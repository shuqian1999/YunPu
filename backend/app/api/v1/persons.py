from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import uuid

from app.core.database import get_db
from app.models.person import Person
from app.models.event import Event
from app.schemas.person import PersonCreate, PersonUpdate, PersonResponse
from app.services.family_service import FamilyService
from app.services.lunar_service import LunarService
from app.services.tag_service import sync_person_tags

router = APIRouter(prefix="/persons", tags=["人物"])


def _transfer_me(db: Session, exclude_id):
    """把「我」的标记从现有持有者身上收回（保证全库唯一）。
    exclude_id 为即将成为新「我」的人物 id（新人物尚未落库时传 None）。"""
    query = db.query(Person).filter(Person.is_me == True)  # noqa: E712
    if exclude_id is not None:
        query = query.filter(Person.id != exclude_id)
    query.update({Person.is_me: False}, synchronize_session=False)


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
    data = person.model_dump()
    tag_names = data.pop("tag_names", None)

    # is_me 全库唯一：新建时若标记为"我"，原"我"自动让位（转让）
    if data.get("is_me"):
        _transfer_me(db, exclude_id=None)

    db_person = Person(**data)
    if db_person.importance is None:
        db_person.importance = 3

    db.add(db_person)
    db.flush()

    if tag_names is not None:
        sync_person_tags(db, db_person, tag_names)

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
    ).all()

    # 转换为带 display_date 的列表，并按 display_date 排序（确保农历事件也按实际公历日期排序）
    events_with_display = []
    for event in events:
        display_date_str = LunarService.get_solar_display_date(event.event_date, event.is_lunar)
        events_with_display.append((event, display_date_str))

    # 按 display_date 升序排序
    events_with_display.sort(key=lambda x: x[1])

    return [
        {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "event_date": event.event_date.isoformat(),
            "is_lunar": event.is_lunar,
            "display_date": LunarService.get_solar_display_date(event.event_date, event.is_lunar),
            "event_type_id": event.event_type_id,
            "location": event.location,
            "event_type": event.event_type.name if event.event_type else "其他",
            "event_type_color": event.event_type.color if event.event_type else "#c0c4cc"
        }
        for event, _ in events_with_display
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

    result = []
    for r in reminders:
        item = r.to_dict()
        item["display_date"] = LunarService.get_solar_display_date(r.remind_date, r.is_lunar)
        if r.event_type:
            item["event_type"] = r.event_type.name
            item["event_type_color"] = r.event_type.color
        else:
            item["event_type"] = "提醒"
            item["event_type_color"] = "#c0c4cc"
        result.append(item)
    return result


@router.get("/{person_id}/relations")
def get_person_relations(
    person_id: int,
    db: Session = Depends(get_db)
):
    """获取人物的所有直接关系（父母/子女/配偶段，批量内存图构建）"""
    service = FamilyService(db)
    return service.get_direct_relations(person_id)


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
    
    data = person.model_dump(exclude_unset=True)
    tag_names = data.pop("tag_names", None)

    # is_me 唯一锚点保护：允许"转让"（把别人设为我，原"我"自动让位），
    # 但不能直接取消当前唯一的"我"
    if "is_me" in data:
        if data["is_me"]:
            if not db_person.is_me:
                _transfer_me(db, exclude_id=person_id)
            # data 保留 is_me=True，由下方 setattr 写到当前人物
        elif db_person.is_me:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能取消「我」的标记。如需更换视角人物，请直接在目标人物卡上将其设为「我」"
            )

    for key, value in data.items():
        setattr(db_person, key, value)

    if tag_names is not None:
        db.flush()
        sync_person_tags(db, db_person, tag_names)

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
    from app.models.social_relation import SocialRelation
    from app.models.contact_record import ContactRecord
    from app.models.tag import PersonTag
    
    db_person = db.query(Person).filter(Person.id == person_id).first()

    if not db_person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="人物不存在"
        )

    # 「我」是家族称谓的视角锚点，必须全库唯一存在，禁止删除
    if db_person.is_me:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="「我」是家族关系的视角人物，不能删除。如需更换，请先把「我」转让给其他人物卡"
        )

    # 删除人物的交往记录
    db.query(ContactRecord).filter(
        ContactRecord.person_id == person_id
    ).delete(synchronize_session=False)

    # 删除人物的标签关联
    db.query(PersonTag).filter(
        PersonTag.person_id == person_id
    ).delete(synchronize_session=False)

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

    # 阶段2：删除该人作为当事人的社会关系；作为他人关系的介绍人时仅置空
    db.query(SocialRelation).filter(
        (SocialRelation.person_a_id == person_id) | (SocialRelation.person_b_id == person_id)
    ).delete(synchronize_session=False)
    db.query(SocialRelation).filter(
        SocialRelation.introducer_id == person_id
    ).update({SocialRelation.introducer_id: None}, synchronize_session=False)

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
