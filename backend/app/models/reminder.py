from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=True)
    title = Column(String(200), nullable=False)
    remind_date = Column(Date, nullable=False, index=True)
    is_lunar = Column(Boolean, default=False)
    repeat_type = Column(String(20), default="once")  # once, yearly, monthly, weekly
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    person = relationship("Person", back_populates="reminders")

    def to_dict(self):
        return {
            "id": self.id,
            "person_id": self.person_id,
            "title": self.title,
            "remind_date": self.remind_date.isoformat() if self.remind_date else None,
            "is_lunar": self.is_lunar,
            "repeat_type": self.repeat_type,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }