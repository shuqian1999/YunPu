from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.person_group import PersonGroup, PersonGroupMember
from app.schemas.group import GroupCreate, GroupUpdate, GroupResponse
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/groups", tags=["分组"])


@router.get("", response_model=List[GroupResponse])
async def get_groups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    groups = db.query(PersonGroup).filter(
        PersonGroup.user_id == current_user.id
    ).order_by(PersonGroup.created_at.asc()).all()
    return groups


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group: GroupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_group = PersonGroup(**group.dict(), user_id=current_user.id)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: int,
    group: GroupUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_group = db.query(PersonGroup).filter(
        PersonGroup.id == group_id,
        PersonGroup.user_id == current_user.id
    ).first()
    
    if not db_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分组不存在"
        )
    
    for key, value in group.dict(exclude_unset=True).items():
        setattr(db_group, key, value)
    
    db.commit()
    db.refresh(db_group)
    return db_group


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_group = db.query(PersonGroup).filter(
        PersonGroup.id == group_id,
        PersonGroup.user_id == current_user.id
    ).first()
    
    if not db_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分组不存在"
        )
    
    db.query(PersonGroupMember).filter(
        PersonGroupMember.group_id == group_id
    ).delete()
    
    db.delete(db_group)
    db.commit()


@router.get("/{group_id}/members")
async def get_group_members(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.person import Person
    
    # 先验证分组是否属于当前用户
    db_group = db.query(PersonGroup).filter(
        PersonGroup.id == group_id,
        PersonGroup.user_id == current_user.id
    ).first()
    
    if not db_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分组不存在"
        )
    
    members = db.query(
        PersonGroupMember,
        Person
    ).join(
        Person, Person.id == PersonGroupMember.person_id
    ).filter(
        PersonGroupMember.group_id == group_id
    ).all()
    
    result = []
    for member, person in members:
        result.append({
            "id": member.id,
            "person_id": person.id,
            "person_name": f"{person.last_name}{person.first_name}" if person.last_name or person.first_name else "未知",
            "person_nickname": person.nickname
        })
    
    return result


@router.post("/{group_id}/members/{person_id}")
async def add_person_to_group(
    group_id: int,
    person_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(PersonGroupMember).filter(
        PersonGroupMember.group_id == group_id,
        PersonGroupMember.person_id == person_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="人物已在分组中"
        )
    
    member = PersonGroupMember(group_id=group_id, person_id=person_id)
    db.add(member)
    db.commit()
    
    return {"message": "添加成功"}


@router.delete("/{group_id}/members/{person_id}")
async def remove_person_from_group(
    group_id: int,
    person_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = db.query(PersonGroupMember).filter(
        PersonGroupMember.group_id == group_id,
        PersonGroupMember.person_id == person_id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="人物不在分组中"
        )
    
    db.delete(member)
    db.commit()
    
    return {"message": "移除成功"}


@router.get("/person/{person_id}", response_model=List[GroupResponse])
async def get_person_groups(
    person_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    groups = db.query(PersonGroup).join(
        PersonGroupMember,
        PersonGroup.id == PersonGroupMember.group_id
    ).filter(
        PersonGroupMember.person_id == person_id,
        PersonGroup.user_id == current_user.id
    ).order_by(PersonGroup.created_at.asc()).all()
    
    return groups