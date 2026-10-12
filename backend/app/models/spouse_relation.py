from sqlalchemy import Column, Integer, ForeignKey, Date, Index, text
from sqlalchemy.orm import relationship
from app.models.base import Base


class SpouseRelation(Base):
    """
    配偶关系表（段内仍写正反向双行；阶段1 起支持多段时间线）

    - 一段配偶关系写两行：(a,b,X) 与 (b,a,反向X)，两行日期/性质相同
    - 同一对人可存在多段（结婚-离婚-复婚），用 start_date/end_date 区分
    - 仅"现任段"（relation_nature=0）受部分唯一索引约束：每方向一对人至多一条
    """
    __tablename__ = "spouse_relations"
    __table_args__ = (
        Index(
            "uq_spouse_current_pair",
            "person_a_id", "person_b_id",
            unique=True,
            sqlite_where=text("relation_nature = 0"),
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    person_a_id = Column(Integer, ForeignKey("persons.id"), nullable=False, index=True)
    person_b_id = Column(Integer, ForeignKey("persons.id"), nullable=False, index=True)
    relation = Column(Integer, nullable=False)  # 0:丈夫, 1:妻子, 2:姨太太（3/4 原男女朋友已迁至社会关系）
    relation_nature = Column(Integer, default=0)  # 0:现任, 1:前任
    start_date = Column(Date, nullable=True)  # 关系开始日期（如结婚日）
    end_date = Column(Date, nullable=True)    # 关系结束日期（如离婚日）；现任段必须为空

    person_a = relationship("Person", foreign_keys=[person_a_id])
    person_b = relationship("Person", foreign_keys=[person_b_id])

    def to_dict(self):
        return {
            "id": self.id,
            "person_a_id": self.person_a_id,
            "person_b_id": self.person_b_id,
            "relation": self.relation,
            "relation_nature": self.relation_nature,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
        }
