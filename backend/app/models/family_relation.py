from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class FamilyRelation(Base):
    __tablename__ = "family_relations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    parent_id = Column(Integer, ForeignKey("family_members.id"))
    child_id = Column(Integer, ForeignKey("family_members.id"))
    parent_type = Column(String(20), nullable=False)
    relation_nature = Column(String(20), default="qin")

    user = relationship("User", back_populates="family_relations")
    parent = relationship("FamilyMember", foreign_keys=[parent_id], back_populates="relations_as_parent")
    child = relationship("FamilyMember", foreign_keys=[child_id], back_populates="relations_as_child")

    def to_dict(self):
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "child_id": self.child_id,
            "parent_type": self.parent_type,
            "relation_nature": self.relation_nature
        }