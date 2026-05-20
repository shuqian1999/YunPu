from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.person import Person
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/search", tags=["搜索"])


@router.get("/persons")
async def search_persons(
    query: str = Query(..., description="搜索关键词"),
    group_id: Optional[int] = Query(None, description="分组ID"),
    gender: Optional[int] = Query(None, description="性别"),
    is_alive: Optional[bool] = Query(None, description="是否在世"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    persons_query = db.query(Person).filter(Person.user_id == current_user.id)
    
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
    
    if gender is not None:
        persons_query = persons_query.filter(Person.gender == gender)
    
    if is_alive is not None:
        if is_alive:
            persons_query = persons_query.filter(Person.death_date.is_(None))
        else:
            persons_query = persons_query.filter(Person.death_date.isnot(None))
    
    persons = persons_query.order_by(Person.created_at.desc()).limit(50).all()
    
    return [
        {
            "id": person.id,
            "first_name": person.first_name,
            "last_name": person.last_name,
            "nickname": person.nickname,
            "gender": person.gender,
            "birth_date": person.birth_date.isoformat() if person.birth_date else None,
            "death_date": person.death_date.isoformat() if person.death_date else None,
            "avatar_url": person.avatar_url,
            "is_me": person.is_me
        }
        for person in persons
    ]