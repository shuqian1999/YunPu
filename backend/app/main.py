from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import engine, SessionLocal, init_db, run_lightweight_migrations
from app.models.base import Base
from app.models.user import User
from app.models.person import Person
from app.models.event import Event
from app.models.reminder import Reminder
from app.models.contact_record import ContactRecord
from app.models.tag import Tag, PersonTag
from app.models.event_type import EventType
from app.models.notification import Notification
from app.models.person_group import PersonGroup, PersonGroupMember
from app.models.email import EmailConfig, EmailTemplate, EmailLog
from app.models.social_relation import SocialRelationType, SocialRelation
from app.core.security import hash_password

# 确保上传目录存在
os.makedirs(settings.upload_dir, exist_ok=True)

app = FastAPI(
  title=settings.app_name,
  openapi_url=f"/api/v1/openapi.json"
)

app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:3000", "http://localhost:5173"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
  Base.metadata.create_all(bind=engine)
  # 为已存在的表补充新增列（联系人字段、最近联系时间等）
  run_lightweight_migrations()

  # 启动定时任务调度器
  try:
    from app.tasks.scheduler import start_scheduler, reschedule_email_job
    start_scheduler()
    # 如果用户已配置发送时间，应用该时间
    db = SessionLocal()
    try:
      config = db.query(EmailConfig).first()
      if config and config.send_time:
        reschedule_email_job(config.send_time)
    finally:
      db.close()
  except ImportError:
    print("注意: 定时任务功能不可用，请安装 apscheduler: pip install apscheduler")
  
  db = SessionLocal()
  try:
    existing_user = db.query(User).filter(User.username == settings.default_username).first()
    if not existing_user:
      user = User(
        username=settings.default_username,
        password_hash=hash_password(settings.default_password)
      )
      db.add(user)
      db.commit()
      db.refresh(user)
      
      person = Person(
        nickname="我",
        is_me=True
      )
      db.add(person)
      db.commit()
      
      print(f"初始用户创建成功：{settings.default_username}")
    
    # 初始化默认事件类型
    default_event_types = [
      {"name": "生日", "color": "#67c23a", "icon": "Calendar"},
      {"name": "纪念日", "color": "#e6a23c", "icon": "Star"},
      {"name": "聚会", "color": "#409eff", "icon": "ChatLineRound"},
      {"name": "旅行", "color": "#909399", "icon": "Location"},
      {"name": "工作", "color": "#f56c6c", "icon": "Briefcase"},
      {"name": "学习", "color": "#9b59b6", "icon": "Reading"},
      {"name": "健康", "color": "#1abc9c", "icon": "FirstAidKit"},
      {"name": "其他", "color": "#c0c4cc", "icon": "More"}
    ]
    
    for et_data in default_event_types:
      existing_et = db.query(EventType).filter(EventType.name == et_data["name"]).first()
      if not existing_et:
        et = EventType(**et_data)
        db.add(et)

    db.commit()
    print("事件类型初始化完成")

    # 初始化默认邮件配置
    existing_email_config = db.query(EmailConfig).first()
    if not existing_email_config:
      email_config = EmailConfig(
        smtp_host="",
        smtp_port=465,
        use_ssl=True,
        username="",
        password="",
        receivers="",
        send_time="08:00",
        enabled=False,
        advance_days=7,
        reminder_types="生日,纪念日"
      )
      db.add(email_config)
      db.commit()
      print("邮件配置初始化完成")

    # 初始化默认邮件模板
    existing_default_tpl = db.query(EmailTemplate).filter(
      EmailTemplate.is_default == True
    ).first()
    if not existing_default_tpl:
      default_template = EmailTemplate(
        name="默认通用模板",
        event_type=None,
        subject="【云谱】{{title}} - 还有 {{days_until}} 天",
        content="""<div style="font-family: 'Microsoft YaHei', Arial, sans-serif;">
  <p style="font-size: 16px; color: #303133; margin: 0 0 8px 0;">
    📌 <strong>{{title}}</strong>
    <span style="background: {{event_type_color}}; color: #fff; padding: 1px 8px; border-radius: 3px; font-size: 12px; margin-left: 8px;">{{event_type}}</span>
  </p>
  <p style="color: #606266; margin: 4px 0;">
    人物：{{nickname}} {{name}}
  </p>
  <p style="color: #606266; margin: 4px 0;">
    📅 日期：{{date}}
    <span style="background: #e6a23c; color: #fff; padding: 1px 6px; border-radius: 3px; font-size: 11px; margin-left: 4px;">{{repeat_type}}</span>
    <span style="background: #909399; color: #fff; padding: 1px 6px; border-radius: 3px; font-size: 11px; margin-left: 4px;">{{is_lunar}}</span>
  </p>
  <p style="color: #f56c6c; margin: 4px 0;">
    ⏰ 还有 <strong>{{days_until}}</strong> 天
  </p>
  {{#if description}}
  <p style="color: #909399; margin-top: 8px; padding: 8px; background: #f5f7fa; border-radius: 4px; font-size: 13px;">
    {{description}}
  </p>
  {{/if}}
  {{#if location}}
  <p style="color: #909399; font-size: 13px; margin: 4px 0;">
    📍 {{location}}
  </p>
  {{/if}}
</div>""",
        is_default=True,
        is_html=True
      )
      db.add(default_template)
      db.commit()
      print("默认邮件模板初始化完成")
  finally:
    db.close()

app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
app.include_router(api_router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "service": "yunpu-backend"}
