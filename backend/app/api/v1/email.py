"""邮件通知 API"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.email_service import EmailService
from app.schemas.email import (
    EmailConfigResponse,
    EmailConfigUpdate,
    EmailTemplateCreate,
    EmailTemplateUpdate,
    EmailTemplateResponse,
    EmailLogResponse,
    EmailTestRequest,
    EmailSendNowRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/email", tags=["邮件通知"])


# ============= 配置 =============

@router.get("/config", response_model=EmailConfigResponse)
def get_email_config(db: Session = Depends(get_db)):
    """获取邮件配置"""
    service = EmailService(db)
    config = service.get_or_create_config()
    return config.to_dict(hide_password=True)


@router.put("/config", response_model=EmailConfigResponse)
def update_email_config(
    payload: EmailConfigUpdate,
    db: Session = Depends(get_db),
):
    """更新邮件配置"""
    service = EmailService(db)
    data = payload.model_dump(exclude_unset=True)
    config = service.update_config(data)
    # 如果更新了发送时间，重新调度任务
    if "send_time" in data and data["send_time"]:
        try:
            from app.tasks.scheduler import reschedule_email_job
            reschedule_email_job(data["send_time"])
        except Exception as e:
            logger.warning(f"重新调度邮件任务失败: {e}")
    return config.to_dict(hide_password=True)


@router.post("/test-connection")
def test_connection(db: Session = Depends(get_db)):
    """测试 SMTP 连接"""
    service = EmailService(db)
    success, message = service.test_connection()
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    return {"message": message}


@router.post("/test-send")
def test_send(
    payload: EmailTestRequest,
    db: Session = Depends(get_db),
):
    """发送测试邮件"""
    service = EmailService(db)
    success, message = service.test_send(payload.receiver)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    return {"message": message}


@router.post("/send-now")
def send_now(
    payload: EmailSendNowRequest,
    db: Session = Depends(get_db),
):
    """立即发送提醒邮件（使用当前筛选条件）"""
    service = EmailService(db)
    success, message = service.send_reminder_email(
        days=payload.days,
        types=payload.types,
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    return {"message": message}


# ============= 模板 =============

@router.get("/templates", response_model=List[EmailTemplateResponse])
def list_templates(db: Session = Depends(get_db)):
    """获取模板列表"""
    service = EmailService(db)
    return [t.to_dict() for t in service.list_templates()]


@router.get("/templates/{template_id}", response_model=EmailTemplateResponse)
def get_template(template_id: int, db: Session = Depends(get_db)):
    """获取模板详情"""
    service = EmailService(db)
    template = service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模板不存在")
    return template.to_dict()


@router.post("/templates", response_model=EmailTemplateResponse)
def create_template(payload: EmailTemplateCreate, db: Session = Depends(get_db)):
    """创建模板"""
    service = EmailService(db)
    template = service.create_template(payload.model_dump())
    return template.to_dict()


@router.put("/templates/{template_id}", response_model=EmailTemplateResponse)
def update_template(
    template_id: int,
    payload: EmailTemplateUpdate,
    db: Session = Depends(get_db),
):
    """更新模板"""
    service = EmailService(db)
    template = service.update_template(template_id, payload.model_dump(exclude_unset=True))
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模板不存在")
    return template.to_dict()


@router.delete("/templates/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    """删除模板"""
    service = EmailService(db)
    if not service.delete_template(template_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模板不存在")
    return {"message": "删除成功"}


@router.post("/templates/{template_id}/preview")
def preview_template(
    template_id: int,
    db: Session = Depends(get_db),
):
    """使用示例数据预览模板"""
    service = EmailService(db)
    template = service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模板不存在")

    # 示例数据（基于 Reminder 字段）
    sample_data = {
        "title": "妈妈生日",
        "name": "李四",
        "nickname": "妈妈",
        "date": "2026年06月20日",
        "days_until": 3,
        "event_type": "生日",
        "event_type_color": "#67c23a",
        "description": "记得给妈妈准备生日礼物",
        "location": "家里",
        "repeat_type": "每年",
        "is_lunar": "否",
        "lunar_date": "",
        "advance_days": 0,
        "trans_event": "是",
    }

    subject = service.render_template(template.subject, sample_data)
    content = service.render_template(template.content, sample_data)
    return {
        "subject": subject,
        "content": content,
        "is_html": template.is_html,
    }


# ============= 日志 =============

@router.get("/logs", response_model=List[EmailLogResponse])
def list_logs(limit: int = 50, db: Session = Depends(get_db)):
    """获取发送日志"""
    service = EmailService(db)
    return [l.to_dict() for l in service.list_logs(limit=limit)]


@router.delete("/logs")
def clear_logs(db: Session = Depends(get_db)):
    """清空发送日志"""
    service = EmailService(db)
    count = service.clear_logs()
    return {"message": f"已清空 {count} 条日志"}
