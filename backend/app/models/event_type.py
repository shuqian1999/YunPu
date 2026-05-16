from sqlalchemy import Column, Integer, String
from app.models.base import Base


class EventType(Base):
    __tablename__ = "event_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    color = Column(String(20), nullable=False, default="#409EFF")
    icon = Column(String(50), nullable=True)