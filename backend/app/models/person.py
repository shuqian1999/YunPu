from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, autoincrement=True)
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

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "nickname": self.nickname,
            "gender": self.gender,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "death_date": self.death_date.isoformat() if self.death_date else None,
            "country": self.country,
            "hometown": self.hometown,
            "residence": self.residence,
            "custom_fields": self.custom_fields,
            "is_me": self.is_me,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }