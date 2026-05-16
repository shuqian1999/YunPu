from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.person import Person
from app.models.event import Event
from app.models.reminder import Reminder
from app.models.user import User
from app.schemas.dashboard import DashboardStats, DashboardEvent, DashboardReminder

router = APIRouter(prefix="/dashboard", tags=["仪表盘"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    person_count = db.query(Person).filter(
        Person.user_id == current_user.id
    ).count()
    
    event_count = db.query(Event).filter(
        Event.user_id == current_user.id
    ).count()
    
    reminder_count = db.query(Reminder).filter(
        Reminder.user_id == current_user.id,
        Reminder.enabled == True
    ).count()
    
    return {
        "person_count": person_count,
        "event_count": event_count,
        "reminder_count": reminder_count
    }


@router.get("/events", response_model=list[DashboardEvent])
def get_dashboard_events(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    events = db.query(Event).filter(
        Event.user_id == current_user.id
    ).order_by(Event.event_date.desc()).limit(limit).all()
    
    result = []
    for event in events:
        result.append({
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "event_date": event.event_date.isoformat(),
            "location": event.location,
            "event_type": event.event_type.name if event.event_type else None,
            "event_type_color": event.event_type.color if event.event_type else None,
            "person_id": event.person_id,
            "person_name": event.person.nickname if event.person else None
        })
    
    return result


@router.get("/reminders", response_model=list[DashboardReminder])
def get_dashboard_reminders(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=days)
    
    reminders = db.query(Reminder).filter(
        Reminder.user_id == current_user.id,
        Reminder.remind_date >= start_date,
        Reminder.remind_date <= end_date,
        Reminder.enabled == True
    ).order_by(Reminder.remind_date.asc()).all()
    
    result = []
    for reminder in reminders:
        result.append({
            "id": reminder.id,
            "title": reminder.title,
            "remind_date": reminder.remind_date.isoformat(),
            "is_lunar": reminder.is_lunar,
            "person_id": reminder.person_id,
            "person_name": reminder.person.nickname if reminder.person else None
        })
    
    return result