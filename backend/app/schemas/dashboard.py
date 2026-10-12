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


class TodayBirthday(BaseModel):
    person_id: int
    name: str
    avatar_url: Optional[str] = None
    date: str                 # 今年生日对应的公历日期
    days_until: int
    is_lunar: bool = False


class TodayReminder(BaseModel):
    id: int
    title: str
    person_id: Optional[int] = None
    person_name: Optional[str] = None
    display_date: Optional[str] = None
    days_until: int
    event_type: Optional[str] = None
    event_type_color: Optional[str] = None
    repeat_type: Optional[str] = "once"


class StaleContact(BaseModel):
    person_id: int
    name: str
    avatar_url: Optional[str] = None
    last_contact_at: Optional[str] = None
    days_since: Optional[int] = None
    never_contacted: bool = False


class DashboardToday(BaseModel):
    birthdays: list[TodayBirthday] = []
    reminders: list[TodayReminder] = []
    stale_contacts: list[StaleContact] = []