from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.event_type import EventType
from app.models.user import User

router = APIRouter(prefix="/event-types", tags=["事件类型"])


@router.get("", response_model=List[dict])
def get_event_types(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    event_types = db.query(EventType).all()
    return [
        {
            "id": et.id,
            "name": et.name,
            "color": et.color,
            "icon": et.icon
        }
        for et in event_types
    ]