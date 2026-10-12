from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


# 允许的互动方式
CONTACT_TYPES = {"meet", "phone", "wechat", "email", "dinner", "gift", "other"}


class ContactRecordBase(BaseModel):
    person_id: int
    contact_type: str = Field("other", max_length=20)
    contact_date: date
    content: Optional[str] = None


class ContactRecordCreate(ContactRecordBase):
    pass


class ContactRecordUpdate(BaseModel):
    person_id: Optional[int] = None
    contact_type: Optional[str] = Field(None, max_length=20)
    contact_date: Optional[date] = None
    content: Optional[str] = None


class ContactRecordResponse(ContactRecordBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
