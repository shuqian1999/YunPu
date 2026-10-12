from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.person import Person

router = APIRouter(prefix="/search", tags=["搜索"])


@router.get("/persons")
async def search_persons(
    query: str = Query(..., description="搜索关键词"),
    group_id: Optional[int] = Query(None, description="分组ID"),
    tag_id: Optional[int] = Query(None, description="标签ID"),
    gender: Optional[int] = Query(None, description="性别"),
    is_alive: Optional[bool] = Query(None, description="是否在世"),
    db: Session = Depends(get_db)
):
    persons_query = db.query(Person)
    
    if query:
        search_filter = (
            Person.first_name.contains(query) |
            Person.last_name.contains(query) |
            Person.nickname.contains(query)
        )
        persons_query = persons_query.filter(search_filter)
    
    if group_id:
        from app.models.person_group import PersonGroupMember
        persons_query = persons_query.join(
            PersonGroupMember,
            Person.id == PersonGroupMember.person_id
        ).filter(PersonGroupMember.group_id == group_id)

    if tag_id:
        from app.models.tag import PersonTag
        persons_query = persons_query.join(
            PersonTag,
            Person.id == PersonTag.person_id
        ).filter(PersonTag.tag_id == tag_id)
    
    if gender is not None:
        if gender == 0:
            # 0 表示"未知"，查询性别为空的
            persons_query = persons_query.filter(Person.gender.is_(None))
        else:
            persons_query = persons_query.filter(Person.gender == gender)
    
    if is_alive is not None:
        if is_alive:
            persons_query = persons_query.filter(Person.death_date.is_(None))
        else:
            persons_query = persons_query.filter(Person.death_date.isnot(None))
    
    persons = persons_query.order_by(Person.created_at.desc()).limit(50).all()

    # 去重（join 多对多关联时同一人物可能出现多次）
    unique_persons = list({person.id: person for person in persons}.values())

    return [person.to_dict() for person in unique_persons]