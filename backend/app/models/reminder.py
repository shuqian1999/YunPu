from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=True)
    event_type_id = Column(Integer, ForeignKey("event_types.id"), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    remind_date = Column(Date, nullable=False, index=True)
    is_lunar = Column(Boolean, default=False)
    repeat_type = Column(String(20), default="once")  # once, yearly, monthly, weekly
    enabled = Column(Boolean, default=True)
    location = Column(String(200), nullable=True)
    remind_advance_days = Column(Integer, default=0)   # 提前几天提醒，0 = 当天
    trans_event = Column(Boolean, default=False)        # 到期后是否自动转换为事件
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    person = relationship("Person", back_populates="reminders")
    event_type = relationship("EventType")

    def to_dict(self):
        return {
            "id": self.id,
            "person_id": self.person_id,
            "event_type_id": self.event_type_id,
            "title": self.title,
            "description": self.description,
            "remind_date": self.remind_date.isoformat() if self.remind_date else None,
            "is_lunar": self.is_lunar,
            "repeat_type": self.repeat_type,
            "enabled": self.enabled,
            "location": self.location,
            "remind_advance_days": self.remind_advance_days,
            "trans_event": self.trans_event,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
