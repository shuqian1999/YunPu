from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class FamilyMember(Base):
    __tablename__ = "family_members"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    person_id = Column(Integer, ForeignKey("persons.id"), unique=True)
    
    user = relationship("User", back_populates="family_members")
    person = relationship("Person")
    relations_as_parent = relationship("FamilyRelation", foreign_keys="FamilyRelation.parent_id", back_populates="parent")
    relations_as_child = relationship("FamilyRelation", foreign_keys="FamilyRelation.child_id", back_populates="child")