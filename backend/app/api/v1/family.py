from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.family_member import FamilyMember
from app.models.family_relation import FamilyRelation
from app.models.family_calculated_relation import FamilyCalculatedRelation
from app.models.person import Person

router = APIRouter(prefix="/family", tags=["家谱"])


@router.get("/tree")
def get_family_tree(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    family_members = db.query(FamilyMember).filter(
        FamilyMember.user_id == current_user.id
    ).all()
    
    relations = db.query(FamilyRelation).filter(
        FamilyRelation.user_id == current_user.id
    ).all()
    
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    relations = db.query(FamilyCalculatedRelation).filter(
        FamilyCalculatedRelation.user_id == current_user.id
    ).all()
    
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.services.family_service import FamilyService
    
    service = FamilyService(db)
    service.recalculate_all_relations(current_user.id)
    
    return {"message": "关系重新计算成功"}


@router.post("/member")
def add_family_member(
    person_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.services.family_service import FamilyService
    
    service = FamilyService(db)
    member = service.add_family_member(current_user.id, person_id)
    
    return {"id": member.id, "person_id": member.person_id}


@router.post("/relation")
def add_family_relation(
    parent_person_id: int,
    child_person_id: int,
    parent_type: str,  # father, mother
    relation_nature: str = "qin",  # qin, ji, yi
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.services.family_service import FamilyService
    
    service = FamilyService(db)
    
    parent_member = service.add_family_member(current_user.id, parent_person_id)
    child_member = service.add_family_member(current_user.id, child_person_id)
    
    relation = service.add_family_relation(
        current_user.id,
        parent_member.id,
        child_member.id,
        parent_type,
        relation_nature
    )
    
    service.recalculate_all_relations(current_user.id)
    
    return {"id": relation.id, "message": "关系添加成功"}