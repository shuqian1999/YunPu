from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


class EventBase(BaseModel):
    person_id: Optional[int] = None
    event_type_id: Optional[int] = None
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    event_date: date
    location: Optional[str] = Field(None, max_length=200)


class EventCreate(EventBase):
    pass


class EventUpdate(EventBase):
    pass


class EventResponse(EventBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True