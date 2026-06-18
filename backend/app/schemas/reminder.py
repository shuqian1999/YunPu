from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date, datetime


class ReminderBase(BaseModel):
    person_id: Optional[int] = None
    event_type_id: Optional[int] = None
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    remind_date: date
    is_lunar: bool = False
    repeat_type: Literal["once", "yearly", "monthly", "weekly"] = "once"
    enabled: bool = True
    location: Optional[str] = Field(None, max_length=200)
    remind_advance_days: int = Field(0, ge=0, le=30)
    trans_event: bool = False  # 到期后自动生成对应事件


class ReminderCreate(ReminderBase):
    pass


class ReminderUpdate(BaseModel):
    person_id: Optional[int] = None
    event_type_id: Optional[int] = None
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    remind_date: Optional[date] = None
    is_lunar: Optional[bool] = None
    repeat_type: Optional[Literal["once", "yearly", "monthly", "weekly"]] = None
    enabled: Optional[bool] = None
    location: Optional[str] = Field(None, max_length=200)
    remind_advance_days: Optional[int] = Field(None, ge=0, le=30)
    trans_event: Optional[bool] = None


class ReminderResponse(ReminderBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
