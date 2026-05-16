from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.person import Person
from app.models.user import User
from app.schemas.person import PersonCreate, PersonUpdate, PersonResponse

router = APIRouter(prefix="/persons", tags=["人物"])


@router.get("", response_model=List[PersonResponse])
def get_persons(
    skip: int = 0,
    limit: int = 20,
    search: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Person).filter(Person.user_id == current_user.id)
    
    if search:
        query = query.filter(
            (Person.first_name.contains(search)) |
            (Person.last_name.contains(search)) |
            (Person.nickname.contains(search))
        )
    
    persons = query.order_by(Person.created_at.desc()).offset(skip).limit(limit).all()
    return persons


@router.get("/{person_id}", response_model=PersonResponse)
def get_person(
    person_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    person = db.query(Person).filter(
        Person.id == person_id,
        Person.user_id == current_user.id
    ).first()
    
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="人物不存在"
        )
    
    return person


@router.post("", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
def create_person(
    person: PersonCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_person = Person(**person.model_dump(), user_id=current_user.id)
    db.add(db_person)
    db.commit()
    db.refresh(db_person)
    return db_person


@router.put("/{person_id}", response_model=PersonResponse)
def update_person(
    person_id: int,
    person: PersonUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_person = db.query(Person).filter(
        Person.id == person_id,
        Person.user_id == current_user.id
    ).first()
    
    if not db_person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="人物不存在"
        )
    
    for key, value in person.model_dump(exclude_unset=True).items():
        setattr(db_person, key, value)
    
    db.commit()
    db.refresh(db_person)
    return db_person


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_person(
    person_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_person = db.query(Person).filter(
        Person.id == person_id,
        Person.user_id == current_user.id
    ).first()
    
    if not db_person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="人物不存在"
        )
    
    db.delete(db_person)
    db.commit()


@router.get("/{person_id}/events", response_model=List[dict])
def get_person_events(
    person_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.event import Event
    
    events = db.query(Event).filter(
        Event.person_id == person_id,
        Event.user_id == current_user.id
    ).order_by(Event.event_date.desc()).all()
    
    return [
        {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "event_date": event.event_date.isoformat(),
            "location": event.location,
            "event_type": event.event_type.name if event.event_type else None,
            "event_type_color": event.event_type.color if event.event_type else "#409EFF"
        }
        for event in events
    ]


@router.get("/{person_id}/reminders", response_model=List[dict])
def get_person_reminders(
    person_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.reminder import Reminder
    
    reminders = db.query(Reminder).filter(
        Reminder.person_id == person_id,
        Reminder.user_id == current_user.id,
        Reminder.enabled == True
    ).order_by(Reminder.remind_date.asc()).all()
    
    return [
        {
            "id": reminder.id,
            "title": reminder.title,
            "remind_date": reminder.remind_date.isoformat(),
            "is_lunar": reminder.is_lunar
        }
        for reminder in reminders
    ]


@router.get("/{person_id}/relations")
def get_person_relations(
    person_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.family_member import FamilyMember
    from app.models.family_relation import FamilyRelation
    from app.models.person import Person
    
    family_member = db.query(FamilyMember).filter(
        FamilyMember.person_id == person_id,
        FamilyMember.user_id == current_user.id
    ).first()
    
    if not family_member:
        return {"parents": [], "children": []}
    
    parent_relations = db.query(FamilyRelation).filter(
        FamilyRelation.child_id == family_member.id,
        FamilyRelation.user_id == current_user.id
    ).all()
    
    children_relations = db.query(FamilyRelation).filter(
        FamilyRelation.parent_id == family_member.id,
        FamilyRelation.user_id == current_user.id
    ).all()
    
    parents = []
    for pr in parent_relations:
        parent_member = db.query(FamilyMember).filter(FamilyMember.id == pr.parent_id).first()
        if parent_member:
            parent_person = db.query(Person).filter(Person.id == parent_member.person_id).first()
            parents.append({
                "id": parent_member.id,
                "person_id": parent_member.person_id,
                "name": parent_person.nickname or f"{parent_person.last_name}{parent_person.first_name}",
                "parent_type": pr.parent_type,
                "relation_nature": pr.relation_nature
            })
    
    children = []
    for cr in children_relations:
        child_member = db.query(FamilyMember).filter(FamilyMember.id == cr.child_id).first()
        if child_member:
            child_person = db.query(Person).filter(Person.id == child_member.person_id).first()
            children.append({
                "id": child_member.id,
                "person_id": child_member.person_id,
                "name": child_person.nickname or f"{child_person.last_name}{child_person.first_name}",
                "parent_type": cr.parent_type,
                "relation_nature": cr.relation_nature
            })
    
    return {
        "parents": parents,
        "children": children
    }