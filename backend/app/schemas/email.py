from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime


class EmailConfigBase(BaseModel):
    smtp_host: Optional[str] = None
    smtp_port: int = 465
    use_ssl: bool = True
    username: Optional[str] = None
    password: Optional[str] = None
    receivers: Optional[str] = None
    send_time: str = "08:00"
    enabled: bool = False
    advance_days: int = Field(7, ge=0, le=30)
    reminder_types: List[str] = Field(default_factory=list)
    include_events: bool = True
    include_reminders: bool = True


class EmailConfigUpdate(BaseModel):
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    use_ssl: Optional[bool] = None
    username: Optional[str] = None
    password: Optional[str] = None
    receivers: Optional[str] = None
    send_time: Optional[str] = None
    enabled: Optional[bool] = None
    advance_days: Optional[int] = Field(None, ge=0, le=30)
    reminder_types: Optional[List[str]] = None
    include_events: Optional[bool] = None
    include_reminders: Optional[bool] = None


class EmailConfigResponse(BaseModel):
    id: int
    smtp_host: Optional[str] = None
    smtp_port: int
    use_ssl: bool
    username: Optional[str] = None
    receivers: Optional[str] = None
    send_time: str
    enabled: bool
    advance_days: int
    reminder_types: List[str] = Field(default_factory=list)
    include_events: bool
    include_reminders: bool
    password: Optional[str] = None
    password_set: bool = False
    updated_at: Optional[str] = None
    created_at: Optional[str] = None


class EmailTestRequest(BaseModel):
    receiver: Optional[str] = None  # 自定义测试接收邮箱，默认用配置中的


class EmailSendNowRequest(BaseModel):
    days: Optional[int] = None
    types: Optional[List[str]] = None
    include_events: Optional[bool] = None
    include_reminders: Optional[bool] = None


class EmailTemplateBase(BaseModel):
    name: str
    event_type: Optional[str] = None
    event_type_id: Optional[int] = None
    subject: str
    content: str
    is_default: bool = False
    is_html: bool = True


class EmailTemplateCreate(EmailTemplateBase):
    pass


class EmailTemplateUpdate(BaseModel):
    name: Optional[str] = None
    event_type: Optional[str] = None
    event_type_id: Optional[int] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    is_default: Optional[bool] = None
    is_html: Optional[bool] = None


class EmailTemplateResponse(EmailTemplateBase):
    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class EmailLogResponse(BaseModel):
    id: int
    subject: Optional[str] = None
    receivers: Optional[str] = None
    content_preview: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    related_count: int
    created_at: Optional[str] = None
