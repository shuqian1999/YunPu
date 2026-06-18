from pydantic import BaseModel
from typing import Optional


class DashboardStats(BaseModel):
    person_count: int
    event_count: int
    reminder_count: int


class DashboardEvent(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    event_date: str
    is_lunar: bool = False
    display_date: Optional[str] = None
    event_type_id: Optional[int] = None
    location: Optional[str] = None
    event_type: Optional[str] = None
    event_type_color: Optional[str] = None
    person_id: Optional[int] = None
    person_name: Optional[str] = None


class DashboardReminder(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    remind_date: str
    is_lunar: bool = False
    display_date: Optional[str] = None
    event_type_id: Optional[int] = None
    event_type: Optional[str] = None
    event_type_color: Optional[str] = None
    repeat_type: Optional[str] = "once"
    remind_advance_days: Optional[int] = 0
    trans_event: Optional[bool] = False
    person_id: Optional[int] = None
    person_name: Optional[str] = None