from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class FamilyMember(Base):
    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), unique=True)

    person = relationship("Person")
    relations_as_parent = relationship("FamilyRelation", foreign_keys="FamilyRelation.parent_id", back_populates="parent")
    relations_as_child = relationship("FamilyRelation", foreign_keys="FamilyRelation.child_id", back_populates="child")

    def to_dict(self):
        return {
            "id": self.id,
            "person_id": self.person_id
        }