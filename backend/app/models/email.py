from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Time, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class EmailConfig(Base):
    """邮件通知配置（全局唯一，单条记录）"""
    __tablename__ = "email_config"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # SMTP 配置
    smtp_host = Column(String(200), nullable=True)  # SMTP 服务器地址
    smtp_port = Column(Integer, default=465)         # SMTP 端口
    use_ssl = Column(Boolean, default=True)          # 是否使用 SSL
    username = Column(String(200), nullable=True)    # 发送邮箱账号
    password = Column(String(500), nullable=True)    # 发送邮箱授权码

    # 接收方
    receivers = Column(Text, nullable=True)          # 接收邮箱，多个以逗号分隔

    # 发送设置
    send_time = Column(String(10), default="08:00")  # 每日发送时间 HH:MM
    enabled = Column(Boolean, default=False)         # 是否启用邮件通知

    # 提醒范围
    advance_days = Column(Integer, default=7)        # 提前多少天提醒（0-30）
    reminder_types = Column(Text, nullable=True)     # 启用的提醒类型名称，逗号分隔，如：生日,纪念日
    include_events = Column(Boolean, default=True)   # 是否包含事件
    include_reminders = Column(Boolean, default=True)  # 是否包含提醒

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self, hide_password: bool = False):
        result = {
            "id": self.id,
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
            "use_ssl": self.use_ssl,
            "username": self.username,
            "receivers": self.receivers,
            "send_time": self.send_time,
            "enabled": self.enabled,
            "advance_days": self.advance_days,
            "reminder_types": [t.strip() for t in (self.reminder_types or "").split(",") if t.strip()],
            "include_events": self.include_events,
            "include_reminders": self.include_reminders,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if not hide_password:
            result["password"] = self.password
        else:
            result["password_set"] = bool(self.password)
            result["password"] = None
        return result


class EmailTemplate(Base):
    """邮件模板"""
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)        # 模板名称
    event_type = Column(String(50), nullable=True)    # 关联事件类型（生日/纪念日/聚会等），null 表示通用模板
    event_type_id = Column(Integer, ForeignKey("event_types.id"), nullable=True)  # 关联事件类型ID
    subject = Column(String(200), nullable=False)     # 邮件主题
    content = Column(Text, nullable=False)            # 邮件正文（支持 HTML）
    is_default = Column(Boolean, default=False)       # 是否默认模板
    is_html = Column(Boolean, default=True)            # 是否 HTML 格式
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "event_type": self.event_type,
            "event_type_id": self.event_type_id,
            "subject": self.subject,
            "content": self.content,
            "is_default": self.is_default,
            "is_html": self.is_html,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class EmailLog(Base):
    """邮件发送日志"""
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject = Column(String(500), nullable=True)
    receivers = Column(Text, nullable=True)
    content_preview = Column(Text, nullable=True)     # 正文预览
    status = Column(String(20), nullable=False)        # success / failed
    error_message = Column(Text, nullable=True)
    related_count = Column(Integer, default=0)         # 关联的提醒/事件数量
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "subject": self.subject,
            "receivers": self.receivers,
            "content_preview": self.content_preview,
            "status": self.status,
            "error_message": self.error_message,
            "related_count": self.related_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
