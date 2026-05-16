from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class FamilyCalculatedRelation(Base):
    __tablename__ = "family_calculated_relations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    person_id = Column(Integer, ForeignKey("persons.id"))
    relation_name = Column(String(50))
    relation_level = Column(Integer, default=0)
    relation_path = Column(String(200))
    is_blood = Column(Boolean, default=True)

    user = relationship("User", back_populates="calculated_relations")
    person = relationship("Person")