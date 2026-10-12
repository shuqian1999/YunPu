from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class ContactRecord(Base):
    """交往记录：记录与某位人物的一次互动（见面/电话/微信等）"""

    __tablename__ = "contact_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False, index=True)
    # 互动方式：meet 见面 / phone 电话 / wechat 微信 / email 邮件 / dinner 聚餐 / gift 礼物 / other 其他
    contact_type = Column(String(20), nullable=False, default="other")
    contact_date = Column(Date, nullable=False, index=True)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    person = relationship("Person", back_populates="contact_records")

    def to_dict(self):
        return {
            "id": self.id,
            "person_id": self.person_id,
            "contact_type": self.contact_type,
            "contact_date": self.contact_date.isoformat() if self.contact_date else None,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
