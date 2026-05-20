from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.person import Person
from app.models.event import Event
from app.models.reminder import Reminder
from app.schemas.dashboard import DashboardStats, DashboardEvent, DashboardReminder

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
    events = db.query(Event).order_by(Event.event_date.desc()).limit(limit).all()
    
    result = []
    for event in events:
        person_name = None
        if event.person:
            if event.person.nickname:
                person_name = event.person.nickname
            elif event.person.last_name or event.person.first_name:
                person_name = f"{event.person.last_name or ''}{event.person.first_name or ''}"
        
        result.append({
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "event_date": event.event_date.isoformat(),
            "location": event.location,
            "event_type": event.event_type.name if event.event_type else None,
            "event_type_color": event.event_type.color if event.event_type else None,
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
            if reminder.person.nickname:
                person_name = reminder.person.nickname
            elif reminder.person.last_name or reminder.person.first_name:
                person_name = f"{reminder.person.last_name or ''}{reminder.person.first_name or ''}"
        
        result.append({
            "id": reminder.id,
            "title": reminder.title,
            "remind_date": reminder.remind_date.isoformat(),
            "is_lunar": reminder.is_lunar,
            "person_id": reminder.person_id,
            "person_name": person_name
        })
    
    return result