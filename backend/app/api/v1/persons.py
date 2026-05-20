from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import uuid

from app.core.database import get_db
from app.models.person import Person
from app.schemas.person import PersonCreate, PersonUpdate, PersonResponse
from app.services.family_service import FamilyService

router = APIRouter(prefix="/persons", tags=["人物"])


@router.get("", response_model=List[PersonResponse])
def get_persons(
    skip: int = 0,
    limit: int = 20,
    search: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Person)
    
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
    db: Session = Depends(get_db)
):
    db_person = Person(**person.model_dump())
    db.add(db_person)
    db.commit()
    db.refresh(db_person)
    return db_person


@router.get("/{person_id}/events", response_model=List[dict])
def get_person_events(
    person_id: int,
    db: Session = Depends(get_db)
):
    from app.models.event import Event
    
    events = db.query(Event).filter(
        Event.person_id == person_id
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
    db: Session = Depends(get_db)
):
    from app.models.reminder import Reminder
    
    reminders = db.query(Reminder).filter(
        Reminder.person_id == person_id
    ).order_by(Reminder.remind_date.asc()).all()
    
    return [
        {
            "id": reminder.id,
            "title": reminder.title,
            "remind_date": reminder.remind_date.isoformat(),
            "is_lunar": reminder.is_lunar,
            "enabled": reminder.enabled
        }
        for reminder in reminders
    ]


@router.get("/{person_id}/relations")
def get_person_relations(
    person_id: int,
    db: Session = Depends(get_db)
):
    """获取人物的所有关系"""
    service = FamilyService(db)
    
    relations = []
    
    # 获取作为 person_a 的关系
    from app.models.family_relation import FamilyRelation
    from app.models.spouse_relation import SpouseRelation
    
    family_as_a = db.query(FamilyRelation).filter(
        FamilyRelation.person_a_id == person_id
    ).all()
    
    for rel in family_as_a:
        person_b = db.query(Person).filter(Person.id == rel.person_b_id).first()
        if person_b:
            relations.append({
                "person_id": person_b.id,
                "name": person_b.nickname or f"{person_b.last_name or ''}{person_b.first_name or ''}",
                "relation_name": service._get_relation_name(rel.relation, rel.relation_nature, "from_a"),
                "relation_type": rel.relation,
                "relation_nature": rel.relation_nature
            })
    
    spouse_as_a = db.query(SpouseRelation).filter(
        SpouseRelation.person_a_id == person_id
    ).all()
    
    for rel in spouse_as_a:
        person_b = db.query(Person).filter(Person.id == rel.person_b_id).first()
        if person_b:
            relations.append({
                "person_id": person_b.id,
                "name": person_b.nickname or f"{person_b.last_name or ''}{person_b.first_name or ''}",
                "relation_name": service._get_spouse_relation_name(rel.relation, "from_a"),
                "relation_type": f"spouse_{rel.relation}",
                "relation_nature": rel.relation_nature
            })
    
    return relations


@router.get("/{person_id}/detail")
def get_person_detail(
    person_id: int,
    db: Session = Depends(get_db)
):
    """获取人物详情（包含关系）"""
    service = FamilyService(db)
    
    person = db.query(Person).filter(Person.id == person_id).first()
    
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="人物不存在"
        )
    
    # 获取与"我"的关系
    me = db.query(Person).filter(Person.is_me == True).first()
    relation_to_me = None
    if me and me.id != person_id:
        relation_to_me = service.calculate_relation_between(person_id, me.id)
    
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
        "relation_to_me": relation_to_me
    }


@router.get("/{person_id}", response_model=PersonResponse)
def get_person(
    person_id: int,
    db: Session = Depends(get_db)
):
    person = db.query(Person).filter(Person.id == person_id).first()
    
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
    db: Session = Depends(get_db)
):
    db_person = db.query(Person).filter(Person.id == person_id).first()
    
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
    db: Session = Depends(get_db)
):
    from app.models.person_group import PersonGroupMember
    from app.models.family_relation import FamilyRelation
    from app.models.spouse_relation import SpouseRelation
    
    db_person = db.query(Person).filter(Person.id == person_id).first()
    
    if not db_person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="人物不存在"
        )
    
    # 删除人物在分组中的关联记录
    db.query(PersonGroupMember).filter(
        PersonGroupMember.person_id == person_id
    ).delete()
    
    # 删除相关的家庭关系
    db.query(FamilyRelation).filter(
        (FamilyRelation.person_a_id == person_id) | (FamilyRelation.person_b_id == person_id)
    ).delete(synchronize_session=False)
    
    # 删除相关的配偶关系
    db.query(SpouseRelation).filter(
        (SpouseRelation.person_a_id == person_id) | (SpouseRelation.person_b_id == person_id)
    ).delete(synchronize_session=False)
    
    db.delete(db_person)
    db.commit()


@router.post("/{person_id}/avatar")
async def upload_person_avatar(
    person_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    from app.core.config import settings
    
    person = db.query(Person).filter(Person.id == person_id).first()
    
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
    db: Session = Depends(get_db)
):
    person = db.query(Person).filter(Person.id == person_id).first()
    
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
