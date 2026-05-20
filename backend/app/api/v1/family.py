from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict

from app.core.database import get_db
from app.models.family_member import FamilyMember
from app.models.family_relation import FamilyRelation
from app.models.family_calculated_relation import FamilyCalculatedRelation
from app.models.person import Person

router = APIRouter(prefix="/family", tags=["家谱"])


@router.get("/tree")
def get_family_tree(
    db: Session = Depends(get_db)
):
    family_members = db.query(FamilyMember).all()
    
    relations = db.query(FamilyRelation).all()
    
    nodes = []
    edges = []
    
    for member in family_members:
        person = db.query(Person).filter(Person.id == member.person_id).first()
        if person:
            nodes.append({
                "id": member.id,
                "person_id": person.id,
                "name": person.nickname or f"{person.last_name}{person.first_name}",
                "gender": person.gender,
                "birth_date": person.birth_date.isoformat() if person.birth_date else None,
                "death_date": person.death_date.isoformat() if person.death_date else None,
                "is_me": person.is_me
            })
    
    for relation in relations:
        edges.append({
            "id": relation.id,
            "source": relation.parent_id,
            "target": relation.child_id,
            "parent_type": relation.parent_type,
            "relation_nature": relation.relation_nature
        })
    
    return {
        "nodes": nodes,
        "edges": edges
    }


@router.get("/relations")
def get_calculated_relations(
    db: Session = Depends(get_db)
):
    relations = db.query(FamilyCalculatedRelation).all()
    
    return [
        {
            "person_id": relation.person_id,
            "relation_name": relation.relation_name,
            "relation_level": relation.relation_level,
            "is_blood": relation.is_blood
        }
        for relation in relations
    ]


@router.get("/relations-to-me")
def get_relations_to_me(
    db: Session = Depends(get_db)
):
    me_person = db.query(Person).filter(
        Person.is_me == True
    ).first()
    
    if not me_person:
        return []
    
    me_member = db.query(FamilyMember).filter(
        FamilyMember.person_id == me_person.id
    ).first()
    
    if not me_member:
        return []
    
    relations = db.query(FamilyCalculatedRelation).all()
    
    return [
        {
            "person_id": relation.person_id,
            "relation_name": relation.relation_name,
            "relation_level": relation.relation_level,
            "is_blood": relation.is_blood
        }
        for relation in relations
    ]


@router.post("/recalculate")
def recalculate_relations(
    db: Session = Depends(get_db)
):
    from app.services.family_service import FamilyService
    
    service = FamilyService(db)
    service.recalculate_all_relations()
    
    return {"message": "关系重新计算成功"}


@router.post("/member")
def add_family_member(
    person_id: int,
    db: Session = Depends(get_db)
):
    from app.services.family_service import FamilyService
    
    service = FamilyService(db)
    member = service.add_family_member(person_id)
    
    return {"id": member.id, "person_id": member.person_id}


@router.post("/relation")
def add_family_relation(
    parent_person_id: int,
    child_person_id: int,
    parent_type: str,
    relation_nature: str = "qin",
    db: Session = Depends(get_db)
):
    from app.services.family_service import FamilyService
    
    service = FamilyService(db)
    
    parent_member = service.add_family_member(parent_person_id)
    child_member = service.add_family_member(child_person_id)
    
    relation = service.add_family_relation(
        parent_member.id,
        child_member.id,
        parent_type,
        relation_nature
    )
    
    service.recalculate_all_relations()
    
    return {"id": relation.id, "message": "关系添加成功"}