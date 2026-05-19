from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import uuid

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
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
            if parent_person:
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
            if child_person:
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


@router.get("/{person_id}/detail")
def get_person_detail(
    person_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取人物详情（包含亲属关系）"""
    from app.models.family_member import FamilyMember
    from app.models.family_relation import FamilyRelation
    from app.models.person import Person
    from sqlalchemy import or_
    
    person = db.query(Person).filter(
        Person.id == person_id,
        Person.user_id == current_user.id
    ).first()
    
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="人物不存在"
        )
    
    family_member = db.query(FamilyMember).filter(
        FamilyMember.person_id == person_id,
        FamilyMember.user_id == current_user.id
    ).first()
    
    family = {
        "parents": [],
        "spouses": [],
        "children": []
    }

    if family_member:
        parent_relations = db.query(FamilyRelation).filter(
            FamilyRelation.child_id == family_member.id,
            FamilyRelation.user_id == current_user.id
        ).all()
        
        for relation in parent_relations:
            parent_member = db.query(FamilyMember).filter(FamilyMember.id == relation.parent_id).first()
            if parent_member:
                parent_person = db.query(Person).filter(Person.id == parent_member.person_id).first()
                if parent_person:
                    family["parents"].append({
                        "id": parent_member.id,
                        "person_id": parent_member.person_id,
                        "name": parent_person.nickname or f"{parent_person.last_name}{parent_person.first_name}",
                        "parent_type": relation.parent_type,
                        "relation_nature": relation.relation_nature
                    })
        
        spouse_relations = db.query(FamilyRelation).filter(
            (
                (FamilyRelation.parent_id == family_member.id) | 
                (FamilyRelation.child_id == family_member.id)
            ),
            FamilyRelation.parent_type == "spouse",
            FamilyRelation.user_id == current_user.id
        ).all()
        
        for relation in spouse_relations:
            spouse_member_id = relation.child_id if relation.parent_id == family_member.id else relation.parent_id
            spouse_member = db.query(FamilyMember).filter(FamilyMember.id == spouse_member_id).first()
            if spouse_member:
                spouse_person = db.query(Person).filter(Person.id == spouse_member.person_id).first()
                if spouse_person:
                    family["spouses"].append({
                        "id": spouse_member.id,
                        "person_id": spouse_member.person_id,
                        "name": spouse_person.nickname or f"{spouse_person.last_name}{spouse_person.first_name}",
                        "relation_nature": relation.relation_nature
                    })
        
        children_relations = db.query(FamilyRelation).filter(
            FamilyRelation.parent_id == family_member.id,
            FamilyRelation.parent_type != "spouse",
            FamilyRelation.user_id == current_user.id
        ).all()
        
        for relation in children_relations:
            child_member = db.query(FamilyMember).filter(FamilyMember.id == relation.child_id).first()
            if child_member:
                child_person = db.query(Person).filter(Person.id == child_member.person_id).first()
                if child_person:
                    family["children"].append({
                        "id": child_member.id,
                        "person_id": child_member.person_id,
                        "name": child_person.nickname or f"{child_person.last_name}{child_person.first_name}",
                        "parent_type": relation.parent_type,
                        "relation_nature": relation.relation_nature
                    })
    
    return {
        "id": person.id,
        "first_name": person.first_name,
        "last_name": person.last_name,
        "nickname": person.nickname,
        "gender": person.gender,
        "birth_date": person.birth_date.isoformat() if person.birth_date else None,
        "death_date": person.death_date.isoformat() if person.death_date else None,
        "country": person.country,
        "hometown": person.hometown,
        "residence": person.residence,
        "custom_fields": person.custom_fields,
        "is_me": person.is_me,
        "avatar_url": person.avatar_url,
        "family": family
    }


@router.put("/{person_id}/family")
def update_person_family(
    person_id: int,
    family_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新人物的家族关系"""
    from app.models.family_member import FamilyMember
    from app.models.family_relation import FamilyRelation
    from sqlalchemy import or_
    
    family_member = db.query(FamilyMember).filter(
        FamilyMember.person_id == person_id,
        FamilyMember.user_id == current_user.id
    ).first()
    
    if not family_member:
        family_member = FamilyMember(user_id=current_user.id, person_id=person_id)
        db.add(family_member)
        db.flush()
    
    db.query(FamilyRelation).filter(
        or_(
            FamilyRelation.parent_id == family_member.id,
            FamilyRelation.child_id == family_member.id
        ),
        FamilyRelation.user_id == current_user.id
    ).delete()
    
    if family_data.get("parents"):
        for parent in family_data["parents"]:
            parent_member = db.query(FamilyMember).filter(
                FamilyMember.person_id == parent["id"],
                FamilyMember.user_id == current_user.id
            ).first()
            if not parent_member:
                parent_member = FamilyMember(user_id=current_user.id, person_id=parent["id"])
                db.add(parent_member)
                db.flush()
            if parent_member:
                relation = FamilyRelation(
                    user_id=current_user.id,
                    parent_id=parent_member.id,
                    child_id=family_member.id,
                    parent_type=parent.get("parent_type", "father"),
                    relation_nature=parent.get("relation_nature", "qin")
                )
                db.add(relation)
    
    if family_data.get("spouses"):
        for spouse in family_data["spouses"]:
            spouse_member = db.query(FamilyMember).filter(
                FamilyMember.person_id == spouse["id"],
                FamilyMember.user_id == current_user.id
            ).first()
            if not spouse_member:
                spouse_member = FamilyMember(user_id=current_user.id, person_id=spouse["id"])
                db.add(spouse_member)
                db.flush()
            if spouse_member:
                relation = FamilyRelation(
                    user_id=current_user.id,
                    parent_id=family_member.id,
                    child_id=spouse_member.id,
                    parent_type="spouse",
                    relation_nature=spouse.get("relation_nature", "qin")
                )
                db.add(relation)
    
    if family_data.get("children"):
        for child in family_data["children"]:
            child_member = db.query(FamilyMember).filter(
                FamilyMember.person_id == child["id"],
                FamilyMember.user_id == current_user.id
            ).first()
            if not child_member:
                child_member = FamilyMember(user_id=current_user.id, person_id=child["id"])
                db.add(child_member)
                db.flush()
            if child_member:
                relation = FamilyRelation(
                    user_id=current_user.id,
                    parent_id=family_member.id,
                    child_id=child_member.id,
                    parent_type=child.get("parent_type", "father"),
                    relation_nature=child.get("relation_nature", "qin")
                )
                db.add(relation)
    
    db.commit()
    
    invalidate_relation_cache(db, current_user.id)
    
    return {"message": "关系更新成功"}


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
    from app.models.family_member import FamilyMember
    from app.models.family_relation import FamilyRelation
    from app.models.family_calculated_relation import FamilyCalculatedRelation
    from sqlalchemy import or_
    
    db_person = db.query(Person).filter(
        Person.id == person_id,
        Person.user_id == current_user.id
    ).first()
    
    if not db_person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="人物不存在"
        )
    
    family_member = db.query(FamilyMember).filter(
        FamilyMember.person_id == person_id,
        FamilyMember.user_id == current_user.id
    ).first()
    
    if family_member:
        db.query(FamilyRelation).filter(
            or_(
                FamilyRelation.parent_id == family_member.id,
                FamilyRelation.child_id == family_member.id
            ),
            FamilyRelation.user_id == current_user.id
        ).delete()
        
        db.query(FamilyCalculatedRelation).filter(
            FamilyCalculatedRelation.user_id == current_user.id
        ).delete()
        
        db.delete(family_member)
    
    db.delete(db_person)
    db.commit()


def invalidate_relation_cache(db: Session, user_id: int):
    """失效关系缓存"""
    from app.models.family_calculated_relation import FamilyCalculatedRelation
    
    db.query(FamilyCalculatedRelation).filter(
        FamilyCalculatedRelation.user_id == user_id
    ).delete()
    db.commit()


@router.post("/{person_id}/avatar")
async def upload_person_avatar(
    person_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传人物头像"""
    person = db.query(Person).filter(
        Person.id == person_id,
        Person.user_id == current_user.id
    ).first()
    
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="人物不存在"
        )
    
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请上传图片文件"
        )
    
    file_content = await file.read()
    if len(file_content) > settings.max_upload_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="图片大小不能超过 5MB"
        )
    
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的图片格式"
        )
    
    file_name = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(settings.upload_dir, file_name)
    
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    old_avatar_url = person.avatar_url
    person.avatar_url = f"/uploads/{file_name}"
    db.commit()
    
    if old_avatar_url and old_avatar_url.startswith("/uploads/"):
        old_file_path = old_avatar_url[1:]
        if os.path.exists(old_file_path):
            try:
                os.remove(old_file_path)
            except:
                pass
    
    return {"avatar_url": person.avatar_url}


@router.delete("/{person_id}/avatar")
def delete_person_avatar(
    person_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除人物头像"""
    person = db.query(Person).filter(
        Person.id == person_id,
        Person.user_id == current_user.id
    ).first()
    
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="人物不存在"
        )
    
    if not person.avatar_url:
        return {"message": "没有头像可删除"}
    
    old_avatar_url = person.avatar_url
    person.avatar_url = None
    db.commit()
    
    if old_avatar_url and old_avatar_url.startswith("/uploads/"):
        old_file_path = old_avatar_url[1:]
        if os.path.exists(old_file_path):
            try:
                os.remove(old_file_path)
            except:
                pass
    
    return {"message": "头像删除成功"}
