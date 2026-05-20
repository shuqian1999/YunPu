from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class SpouseRelation(Base):
    """
    配偶关系表
    
    用于记录两人之间的配偶关系
    创建关系时，会同时创建正向和反向两条记录：
    - 正向：person_a 是 person_b 的 丈夫/妻子/男朋友/女朋友
    - 反向：person_b 是 person_a 的 妻子/丈夫/女朋友/男朋友
    """
    __tablename__ = "spouse_relations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    person_a_id = Column(Integer, ForeignKey("persons.id"), nullable=False, index=True)
    person_b_id = Column(Integer, ForeignKey("persons.id"), nullable=False, index=True)
    relation = Column(Integer, nullable=False)  # 0:丈夫, 1:妻子, 2:姨太太, 3:男朋友, 4:女朋友
    relation_nature = Column(Integer, default=0)  # 0:现任, 1:前任

    person_a = relationship("Person", foreign_keys=[person_a_id])
    person_b = relationship("Person", foreign_keys=[person_b_id])

    def to_dict(self):
        return {
            "id": self.id,
            "person_a_id": self.person_a_id,
            "person_b_id": self.person_b_id,
            "relation": self.relation,
            "relation_nature": self.relation_nature
        }
