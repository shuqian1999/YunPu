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
    is_lunar_birth = Column(Boolean, default=False)
    death_date = Column(Date)
    is_lunar_death = Column(Boolean, default=False)
    country = Column(String(50))
    hometown = Column(String(100))
    residence = Column(String(100))
    # 联系人扩展字段
    phone = Column(String(50))
    email = Column(String(100))
    wechat = Column(String(50))
    address = Column(String(200))
    company = Column(String(100))
    occupation = Column(String(100))
    website = Column(String(200))
    custom_fields = Column(JSON)
    is_me = Column(Boolean, default=False, index=True)
    # 是否关注（星标/爱心）：用于筛选重点维护的联系人，如仪表盘「久未联系」
    is_favorite = Column(Boolean, default=False, index=True)
    avatar_url = Column(String(255))
    # 亲密度/重要程度：1-5，默认 3
    importance = Column(Integer, default=3)
    # 最近联系时间，由互动记录自动维护
    last_contact_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    events = relationship("Event", back_populates="person")
    reminders = relationship("Reminder", back_populates="person")
    contact_records = relationship(
        "ContactRecord", back_populates="person", cascade="all, delete-orphan"
    )
    # 标签多对多（只读视图，写入通过 person_tags 关联表管理）
    tags = relationship("Tag", secondary="person_tags", viewonly=True)

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "nickname": self.nickname,
            "gender": self.gender,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "is_lunar_birth": self.is_lunar_birth,
            "death_date": self.death_date.isoformat() if self.death_date else None,
            "is_lunar_death": self.is_lunar_death,
            "country": self.country,
            "hometown": self.hometown,
            "residence": self.residence,
            "phone": self.phone,
            "email": self.email,
            "wechat": self.wechat,
            "address": self.address,
            "company": self.company,
            "occupation": self.occupation,
            "website": self.website,
            "custom_fields": self.custom_fields,
            "is_me": self.is_me,
            "is_favorite": bool(self.is_favorite),
            "avatar_url": self.avatar_url,
            "importance": self.importance if self.importance is not None else 3,
            "tags": [tag.to_dict() for tag in sorted(self.tags, key=lambda t: t.id)],
            "last_contact_at": self.last_contact_at.isoformat() if self.last_contact_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }