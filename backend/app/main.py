from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import engine, SessionLocal, init_db
from app.models.base import Base
from app.models.user import User
from app.models.person import Person
from app.models.event import Event
from app.models.reminder import Reminder
from app.models.event_type import EventType
from app.models.notification import Notification
from app.models.person_group import PersonGroup, PersonGroupMember
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
  
  # 启动定时任务调度器
  try:
    from app.tasks.scheduler import start_scheduler
    start_scheduler()
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
  finally:
    db.close()

app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
app.include_router(api_router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "service": "yunpu-backend"}
