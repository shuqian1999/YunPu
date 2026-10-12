from sqlalchemy import Column, Integer, String, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base


class FamilyRelation(Base):
    """
    家庭关系表（阶段1 起为单向边）

    仅记录父母 -> 子女方向的一条边：
    - person_a 是 person_b 的 父亲/母亲（relation 只取 0:父 / 1:母）
    - 儿子/女儿视角由图加载层按子女性别推导，不再存冗余反向行

    历史遗留的 SON(2)/DAUGHTER(3) 反向行由启动迁移统一翻转/清理。
    """
    __tablename__ = "family_relations"
    __table_args__ = (
        UniqueConstraint("person_a_id", "person_b_id", name="uq_family_relations_pair"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    person_a_id = Column(Integer, ForeignKey("persons.id"), nullable=False, index=True)  # 父母
    person_b_id = Column(Integer, ForeignKey("persons.id"), nullable=False, index=True)  # 子女
    relation = Column(Integer, nullable=False)  # 仅 0:父, 1:母
    relation_nature = Column(Integer, default=0)  # 0:亲, 1:继, 2:养, 3:义, 4:干

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
