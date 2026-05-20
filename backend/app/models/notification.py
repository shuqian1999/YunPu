from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    type = Column(String(50), nullable=False)  # reminder, event, system
    title = Column(String(200), nullable=False)
    content = Column(Text)
    related_id = Column(Integer, nullable=True)  # 关联的提醒或事件ID
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "content": self.content,
            "related_id": self.related_id,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
