from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.core.database import get_db
from app.models.tag import Tag, PersonTag
from app.schemas.tag import TagCreate, TagUpdate, TagWithCount
from app.services.tag_service import auto_color

router = APIRouter(prefix="/tags", tags=["标签"])


@router.get("", response_model=List[TagWithCount])
def list_tags(db: Session = Depends(get_db)):
    rows = (
        db.query(Tag, func.count(PersonTag.id))
        .outerjoin(PersonTag, PersonTag.tag_id == Tag.id)
        .group_by(Tag.id)
        .order_by(Tag.created_at.asc())
        .all()
    )
    return [
        {
            "id": tag.id,
            "name": tag.name,
            "color": tag.color,
            "person_count": count
        }
        for tag, count in rows
    ]


@router.post("", response_model=TagWithCount, status_code=status.HTTP_201_CREATED)
def create_tag(payload: TagCreate, db: Session = Depends(get_db)):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="标签名称不能为空")

    existing = db.query(Tag).filter(Tag.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="标签已存在")

    tag = Tag(name=name, color=payload.color or auto_color(name))
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return {"id": tag.id, "name": tag.name, "color": tag.color, "person_count": 0}


@router.put("/{tag_id}", response_model=TagWithCount)
def update_tag(tag_id: int, payload: TagUpdate, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"]:
        new_name = data["name"].strip()
        dup = db.query(Tag).filter(Tag.name == new_name, Tag.id != tag_id).first()
        if dup:
            raise HTTPException(status_code=400, detail="标签名称已存在")
        tag.name = new_name
    if "color" in data and data["color"]:
        tag.color = data["color"]

    db.commit()
    db.refresh(tag)
    count = db.query(func.count(PersonTag.id)).filter(
        PersonTag.tag_id == tag_id
    ).scalar() or 0
    return {"id": tag.id, "name": tag.name, "color": tag.color, "person_count": count}


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    db.delete(tag)
    db.commit()
