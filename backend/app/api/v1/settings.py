from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.schemas.settings import SystemSettingsResponse
from app.core.security import get_current_user, verify_password, hash_password

router = APIRouter(prefix="/settings", tags=["设置"])


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )
    
    current_user.password_hash = hash_password(new_password)
    db.commit()
    
    return {"message": "密码修改成功"}


@router.get("/system", response_model=SystemSettingsResponse)
async def get_system_settings(
    db: Session = Depends(get_db)
):
    from app.models.person import Person
    from app.models.event import Event
    from app.models.reminder import Reminder
    
    person_count = db.query(Person).count()
    event_count = db.query(Event).count()
    reminder_count = db.query(Reminder).count()
    
    return {
        "person_count": person_count,
        "event_count": event_count,
        "reminder_count": reminder_count,
        "database_size": get_database_size(db)
    }


def get_database_size(db: Session) -> str:
    import os
    database_path = db.bind.url.database
    if os.path.exists(database_path):
        size = os.path.getsize(database_path)
        return f"{size / 1024 / 1024:.2f} MB"
    return "0 MB"