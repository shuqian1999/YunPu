from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class Tag(Base):
    """人物标签：一个人可有多个标签（区别于分组的多对一归类）"""

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(30), nullable=False, unique=True, index=True)
    color = Column(String(10), nullable=False, default="#409EFF")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    members = relationship("PersonTag", back_populates="tag", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color
        }


class PersonTag(Base):
    """人物-标签 多对多关联"""

    __tablename__ = "person_tags"
    __table_args__ = (
        UniqueConstraint("person_id", "tag_id", name="uq_person_tag"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    person_id = Column(
        Integer, ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tag_id = Column(
        Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tag = relationship("Tag", back_populates="members")
