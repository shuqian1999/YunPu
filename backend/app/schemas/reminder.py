from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


class ReminderBase(BaseModel):
    person_id: Optional[int] = None
    title: str = Field(..., max_length=200)
    remind_date: date
    is_lunar: bool = False
    enabled: bool = True


class ReminderCreate(ReminderBase):
    pass


class ReminderUpdate(ReminderBase):
    pass


class ReminderResponse(ReminderBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True