from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class SocialRelationType(Base):
    """
    社会关系类型字典（阶段2）

    - 无向类型（朋友/同事等）：reverse_name 为空
    - 有向类型（如老师）：(a,b)="a 是 b 的老师"，reverse_name="学生"
    - is_preset=1 为系统预设：禁止删除，允许改名/改色
    """
    __tablename__ = "social_relation_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20), nullable=False, unique=True, index=True)
    reverse_name = Column(String(20), nullable=True)
    directed = Column(Integer, nullable=False, default=0)  # 0:无向 1:有向
    color = Column(String(10), nullable=False, default="#fa8c16")
    is_preset = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "reverse_name": self.reverse_name,
            "directed": self.directed,
            "color": self.color,
            "is_preset": self.is_preset,
        }


class SocialRelation(Base):
    """
    社会关系实例（阶段2，单行存储）

    - 无向类型：存储前 person_a_id/person_b_id 归一化为 a < b
    - 有向类型：(a,b) 语义 = "a 是 b 的{type.name}"
    - 同两人同类型可有多段（start_date/end_date），end_date 为空表示进行中
    - closeness：关系级亲密度 1-5，可空（手动打分）
    - introducer_id：介绍人，完全可选；介绍人被删除时手动置 NULL
    """
    __tablename__ = "social_relations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    person_a_id = Column(
        Integer, ForeignKey("persons.id"), nullable=False, index=True
    )
    person_b_id = Column(
        Integer, ForeignKey("persons.id"), nullable=False, index=True
    )
    type_id = Column(
        Integer,
        ForeignKey("social_relation_types.id"),
        nullable=False, index=True
    )
    closeness = Column(Integer, nullable=True)  # 1-5，可空
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    introducer_id = Column(
        Integer, ForeignKey("persons.id"), nullable=True, index=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    relation_type = relationship("SocialRelationType", foreign_keys=[type_id])

    def to_dict(self):
        return {
            "id": self.id,
            "person_a_id": self.person_a_id,
            "person_b_id": self.person_b_id,
            "type_id": self.type_id,
            "closeness": self.closeness,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "introducer_id": self.introducer_id,
        }
