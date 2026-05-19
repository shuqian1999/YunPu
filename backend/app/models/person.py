from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    nickname = Column(String(50))
    gender = Column(Integer)
    birth_date = Column(Date)
    death_date = Column(Date)
    country = Column(String(50))
    hometown = Column(String(100))
    residence = Column(String(100))
    custom_fields = Column(JSON)
    is_me = Column(Boolean, default=False, index=True)
    avatar_url = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    events = relationship("Event", back_populates="person")
    reminders = relationship("Reminder", back_populates="person")