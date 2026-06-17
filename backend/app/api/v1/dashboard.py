from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.person import Person
from app.models.event import Event
from app.models.reminder import Reminder
from app.schemas.dashboard import DashboardStats, DashboardEvent, DashboardReminder
from app.services.lunar_service import LunarService

router = APIRouter(prefix="/dashboard", tags=["仪表盘"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db)
):
    person_count = db.query(Person).count()
    event_count = db.query(Event).count()
    reminder_count = db.query(Reminder).count()
    
    return {
        "person_count": person_count,
        "event_count": event_count,
        "reminder_count": reminder_count
    }


@router.get("/events", response_model=list[DashboardEvent])
def get_dashboard_events(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    # 先获取所有事件，按 display_date 排序后取 limit
    # 这样确保农历事件也按实际公历日期排序
    all_events = db.query(Event).all()
    events_with_display = []
    for event in all_events:
        display_date_str = LunarService.get_solar_display_date(event.event_date, event.is_lunar)
        events_with_display.append((event, display_date_str))
    events_with_display.sort(key=lambda x: x[1])
    events = [e for e, _ in events_with_display[:limit]]

    result = []
    for event in events:
        person_name = None
        if event.person:
            if event.person.last_name or event.person.first_name:
                person_name = f"{event.person.last_name or ''}{event.person.first_name or ''}"
            elif event.person.nickname:
                person_name = event.person.nickname

        result.append({
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "event_date": event.event_date.isoformat(),
            "is_lunar": event.is_lunar,
            "display_date": LunarService.get_solar_display_date(event.event_date, event.is_lunar),
            "event_type_id": event.event_type_id,
            "location": event.location,
            "event_type": event.event_type.name if event.event_type else "其他",
            "event_type_color": event.event_type.color if event.event_type else "#c0c4cc",
            "person_id": event.person_id,
            "person_name": person_name
        })

    return result


@router.get("/reminders", response_model=list[DashboardReminder])
def get_dashboard_reminders(
    days: int = 30,
    db: Session = Depends(get_db)
):
    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=days)
    
    reminders = db.query(Reminder).filter(
        Reminder.remind_date >= start_date,
        Reminder.remind_date <= end_date
    ).order_by(Reminder.remind_date.asc()).all()
    
    result = []
    for reminder in reminders:
        person_name = None
        if reminder.person:
            if reminder.person.last_name or reminder.person.first_name:
                person_name = f"{reminder.person.last_name or ''}{reminder.person.first_name or ''}"
            elif reminder.person.nickname:
                person_name = reminder.person.nickname
        
        result.append({
            "id": reminder.id,
            "title": reminder.title,
            "remind_date": reminder.remind_date.isoformat(),
            "is_lunar": reminder.is_lunar,
            "display_date": LunarService.get_solar_display_date(reminder.remind_date, reminder.is_lunar),
            "person_id": reminder.person_id,
            "person_name": person_name
        })
    
    return result