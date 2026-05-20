from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.notification import Notification

router = APIRouter(prefix="/notifications", tags=["通知"])


@router.get("", response_model=List[dict])
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    notifications = db.query(Notification).order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    
    return [n.to_dict() for n in notifications]


@router.get("/unread-count")
async def get_unread_count(
    db: Session = Depends(get_db)
):
    count = db.query(Notification).filter(
        Notification.is_read == False
    ).count()
    
    return {"count": count}


@router.put("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db)
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知不存在"
        )
    
    notification.is_read = True
    db.commit()
    
    return {"message": "标记成功"}


@router.put("/read-all")
async def mark_all_as_read(
    db: Session = Depends(get_db)
):
    db.query(Notification).filter(
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    
    return {"message": "全部标记成功"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知不存在"
        )
    
    db.delete(notification)
    db.commit()
    
    return {"message": "删除成功"}