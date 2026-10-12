from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta

from app.core.database import get_db
from app.models.person import Person
from app.models.event import Event
from app.models.reminder import Reminder
from app.schemas.dashboard import (
    DashboardStats,
    DashboardEvent,
    DashboardReminder,
    DashboardToday,
)
from app.services.lunar_service import LunarService

router = APIRouter(prefix="/dashboard", tags=["仪表盘"])

# 今日关注的时间窗口与阈值
BIRTHDAY_WINDOW_DAYS = 14
REMINDER_WINDOW_DAYS = 14
STALE_CONTACT_DAYS = 30
STALE_CONTACT_LIMIT = 6


def _person_name(person: Person) -> str:
    if person.last_name or person.first_name:
        return f"{person.last_name or ''}{person.first_name or ''}"
    return person.nickname or f"人物{person.id}"


def _next_solar_birthday(birth: date, today: date):
    """计算公历生日的下一次日期（处理 2 月 29 日）。"""
    try:
        candidate = date(today.year, birth.month, birth.day)
    except ValueError:
        candidate = date(today.year, 3, 1)
    if candidate < today:
        try:
            candidate = date(today.year + 1, birth.month, birth.day)
        except ValueError:
            candidate = date(today.year + 1, 3, 1)
    return candidate


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
        Reminder.enabled == True,
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
            "description": reminder.description,
            "remind_date": reminder.remind_date.isoformat(),
            "is_lunar": reminder.is_lunar,
            "display_date": LunarService.get_solar_display_date(reminder.remind_date, reminder.is_lunar),
            "event_type_id": reminder.event_type_id,
            "event_type": reminder.event_type.name if reminder.event_type else "提醒",
            "event_type_color": reminder.event_type.color if reminder.event_type else "#c0c4cc",
            "repeat_type": reminder.repeat_type,
            "remind_advance_days": reminder.remind_advance_days,
            "trans_event": reminder.trans_event,
            "person_id": reminder.person_id,
            "person_name": person_name
        })

    return result


@router.get("/today", response_model=DashboardToday)
def get_dashboard_today(
    db: Session = Depends(get_db)
):
    """今日关注：近期生日、近期提醒、久未联系的人。"""
    today = datetime.now().date()
    reminder_end = today + timedelta(days=REMINDER_WINDOW_DAYS)

    # 1) 近期生日（仅在世人物）
    birthdays = []
    for person in db.query(Person).filter(Person.birth_date.isnot(None)).all():
        if person.death_date:
            continue

        birth = person.birth_date
        if person.is_lunar_birth:
            next_date = LunarService.get_next_lunar_birthday(
                birth.year, birth.month, birth.day, False
            )
        else:
            next_date = _next_solar_birthday(birth, today)

        if not next_date:
            continue

        days_until = (next_date - today).days
        if 0 <= days_until <= BIRTHDAY_WINDOW_DAYS:
            birthdays.append({
                "person_id": person.id,
                "name": _person_name(person),
                "avatar_url": person.avatar_url,
                "date": next_date.isoformat(),
                "days_until": days_until,
                "is_lunar": bool(person.is_lunar_birth)
            })

    birthdays.sort(key=lambda x: x["days_until"])

    # 2) 近期提醒（按规范化后的公历日期计算倒计时）
    upcoming_reminders = []
    reminders = db.query(Reminder).filter(
        Reminder.enabled == True,
        Reminder.remind_date >= today - timedelta(days=1),
        Reminder.remind_date <= reminder_end
    ).order_by(Reminder.remind_date.asc()).all()

    for reminder in reminders:
        solar_date = LunarService.normalize_lunar_to_solar(
            reminder.remind_date, reminder.is_lunar
        )
        if not solar_date:
            solar_date = reminder.remind_date
        days_until = (solar_date - today).days
        if days_until < 0:
            continue

        upcoming_reminders.append({
            "id": reminder.id,
            "title": reminder.title,
            "person_id": reminder.person_id,
            "person_name": _person_name(reminder.person) if reminder.person else None,
            "display_date": solar_date.isoformat(),
            "days_until": days_until,
            "event_type": reminder.event_type.name if reminder.event_type else "提醒",
            "event_type_color": reminder.event_type.color if reminder.event_type else "#c0c4cc",
            "repeat_type": reminder.repeat_type
        })

    upcoming_reminders.sort(key=lambda x: x["days_until"])
    upcoming_reminders = upcoming_reminders[:5]

    # 3) 久未联系（仅关注的人；排除本人与已故人物）
    stale_cutoff = datetime.combine(
        today - timedelta(days=STALE_CONTACT_DAYS), datetime.min.time()
    )
    candidates = db.query(Person).filter(
        Person.is_favorite == True,  # noqa: E712
        Person.is_me == False,  # noqa: E712
        Person.death_date.is_(None)
    ).all()

    dated_stale = []
    never_contacted = []
    for person in candidates:
        if person.last_contact_at is None:
            never_contacted.append(person)
        elif person.last_contact_at < stale_cutoff:
            dated_stale.append(person)

    dated_stale.sort(key=lambda p: p.last_contact_at)

    stale_contacts = []
    for person in dated_stale:
        last_date = person.last_contact_at.date() if hasattr(
            person.last_contact_at, "date"
        ) else person.last_contact_at
        stale_contacts.append({
            "person_id": person.id,
            "name": _person_name(person),
            "avatar_url": person.avatar_url,
            "last_contact_at": person.last_contact_at.isoformat() if person.last_contact_at else None,
            "days_since": (today - last_date).days,
            "never_contacted": False
        })

    # 从未记录过联系的人排在后面补充
    for person in never_contacted:
        if len(stale_contacts) >= STALE_CONTACT_LIMIT:
            break
        stale_contacts.append({
            "person_id": person.id,
            "name": _person_name(person),
            "avatar_url": person.avatar_url,
            "last_contact_at": None,
            "days_since": None,
            "never_contacted": True
        })

    stale_contacts = stale_contacts[:STALE_CONTACT_LIMIT]

    return {
        "birthdays": birthdays,
        "reminders": upcoming_reminders,
        "stale_contacts": stale_contacts
    }