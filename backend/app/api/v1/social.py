"""社会关系 API（阶段2）：关系类型管理 + 关系实例 CRUD"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.social import (
    SocialTypeCreate,
    SocialTypeUpdate,
    SocialRelationCreate,
    SocialRelationUpdate,
)
from app.services.social_service import SocialService

router = APIRouter(prefix="/social", tags=["社会关系"])


# ---------------------------------------------------------------------------
# 关系类型
# ---------------------------------------------------------------------------

@router.get("/types")
def list_social_types(db: Session = Depends(get_db)):
    return SocialService(db).list_types()


@router.post("/types", status_code=status.HTTP_201_CREATED)
def create_social_type(payload: SocialTypeCreate, db: Session = Depends(get_db)):
    try:
        return SocialService(db).create_type(
            name=payload.name,
            directed=payload.directed,
            reverse_name=payload.reverse_name,
            color=payload.color,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/types/{type_id}")
def update_social_type(
    type_id: int,
    payload: SocialTypeUpdate,
    db: Session = Depends(get_db)
):
    try:
        return SocialService(db).update_type(
            type_id, payload.model_dump(exclude_unset=True)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/types/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_social_type(type_id: int, db: Session = Depends(get_db)):
    try:
        SocialService(db).delete_type(type_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# 关系实例
# ---------------------------------------------------------------------------

@router.get("/relations")
def list_social_relations(person_id: int, db: Session = Depends(get_db)):
    try:
        return SocialService(db).list_for_person(person_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/relations", status_code=status.HTTP_201_CREATED)
def create_social_relation(
    payload: SocialRelationCreate, db: Session = Depends(get_db)
):
    try:
        return SocialService(db).create_relation(
            person_a_id=payload.person_a_id,
            person_b_id=payload.person_b_id,
            type_id=payload.type_id,
            closeness=payload.closeness,
            start_date=payload.start_date,
            end_date=payload.end_date,
            introducer_id=payload.introducer_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/relations/{relation_id}")
def update_social_relation(
    relation_id: int,
    payload: SocialRelationUpdate,
    db: Session = Depends(get_db)
):
    try:
        return SocialService(db).update_relation(
            relation_id, payload.model_dump(exclude_unset=True)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/relations/{relation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_social_relation(relation_id: int, db: Session = Depends(get_db)):
    try:
        SocialService(db).delete_relation(relation_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
