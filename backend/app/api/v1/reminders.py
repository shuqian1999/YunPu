from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.reminder import Reminder
from app.models.event_type import EventType
from app.schemas.reminder import ReminderCreate, ReminderUpdate, ReminderResponse
from app.services.lunar_service import LunarService

router = APIRouter(prefix="/reminders", tags=["提醒"])


def _enrich_reminder(reminder: Reminder) -> dict:
    """将 reminder 转 dict，并补充 display_date / event_type 信息（与 Event 对齐）"""
    data = reminder.to_dict()
    data["display_date"] = LunarService.get_solar_display_date(
        reminder.remind_date, reminder.is_lunar
    )
    if reminder.event_type:
        data["event_type"] = reminder.event_type.name
        data["event_type_color"] = reminder.event_type.color
    else:
        data["event_type"] = "提醒"
        data["event_type_color"] = "#c0c4cc"
    return data


@router.get("", response_model=List[dict])
def get_reminders(
    person_id: int = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    query = db.query(Reminder)

    if person_id:
        query = query.filter(Reminder.person_id == person_id)

    reminders = query.order_by(Reminder.remind_date.asc()).offset(skip).limit(limit).all()
    return [_enrich_reminder(r) for r in reminders]


@router.get("/{reminder_id}", response_model=dict)
def get_reminder(
    reminder_id: int,
    db: Session = Depends(get_db)
):
    reminder = db.query(Reminder).filter(
        Reminder.id == reminder_id
    ).first()

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )

    return _enrich_reminder(reminder)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_reminder(
    reminder: ReminderCreate,
    db: Session = Depends(get_db)
):
    db_reminder = Reminder(**reminder.model_dump())
    db.add(db_reminder)
    db.commit()
    db.refresh(db_reminder)
    return _enrich_reminder(db_reminder)


@router.put("/{reminder_id}")
def update_reminder(
    reminder_id: int,
    reminder: ReminderUpdate,
    db: Session = Depends(get_db)
):
    db_reminder = db.query(Reminder).filter(
        Reminder.id == reminder_id
    ).first()

    if not db_reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )

    for key, value in reminder.model_dump(exclude_unset=True).items():
        setattr(db_reminder, key, value)

    db.commit()
    db.refresh(db_reminder)
    return _enrich_reminder(db_reminder)


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db)
):
    db_reminder = db.query(Reminder).filter(
        Reminder.id == reminder_id
    ).first()

    if not db_reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )

    db.delete(db_reminder)
    db.commit()
