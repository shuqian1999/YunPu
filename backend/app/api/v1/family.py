from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Dict, Optional

from app.core.database import get_db
from app.services.family_service import FamilyService
from app.models.enums.relation_enums import (
    FamilyRelationType, RelationNature,
    SpouseRelationType, SpouseRelationNature,
    NATURE_LABELS, SPOUSE_ROLE_LABELS,
)

router = APIRouter(prefix="/family", tags=["家谱"])


@router.get("/relations/to-me")
def get_relations_to_me(
    db: Session = Depends(get_db)
):
    """获取所有与"我"的亲属关系"""
    service = FamilyService(db)
    return service.get_relations_to_me()


@router.get("/relations/grouped")
def get_relations_grouped(
    db: Session = Depends(get_db)
):
    """
    按代差分组返回与"我"相关的所有人物
    用于"按代差列表展示"视图
    """
    service = FamilyService(db)
    return service.get_relations_grouped_by_generation()


@router.get("/relations/between")
def get_relation_between(
    person_a_id: int,
    person_b_id: int,
    db: Session = Depends(get_db)
):
    """计算两人之间的关系"""
    service = FamilyService(db)
    result = service.calculate_relation_between(person_a_id, person_b_id)
    if result:
        return result
    return {"relation_name": "无关系", "level": -1, "is_blood": False}


@router.post("/relation/family")
def create_family_relation(
    person_a_id: int,
    person_b_id: int,
    relation: int,
    relation_nature: int = 0,
    db: Session = Depends(get_db)
):
    """
    创建家庭关系（父母子女）
    
    Args:
        person_a_id: 人物A的ID
        person_b_id: 人物B的ID
        relation: 关系类型 (0:父, 1:母, 2:子, 3:女)
        relation_nature: 关系性质 (0:亲, 1:继, 2:养, 3:义, 4:干)
    """
    service = FamilyService(db)
    try:
        forward, reverse = service.create_family_relation(
            person_a_id, person_b_id, relation, relation_nature
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "message": "关系创建成功",
        "forward": forward.to_dict(),
        "reverse": reverse.to_dict()
    }


@router.post("/relation/spouse")
def create_spouse_relation(
    person_a_id: int,
    person_b_id: int,
    relation: int,
    relation_nature: int = 0,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    创建配偶关系段
    Args:
        person_a_id: 人物A的ID
        person_b_id: 人物B的ID
        relation: 关系类型 (0:丈夫, 1:妻子, 2:姨太太；男女朋友请用社会关系)
        relation_nature: 关系性质 (0:现任, 1:前任)
        start_date: 关系开始日期（如结婚日），可选
        end_date: 关系结束日期（如离婚日），仅前任可填
    """
    service = FamilyService(db)
    try:
        forward, reverse = service.create_spouse_relation(
            person_a_id, person_b_id, relation, relation_nature,
            start_date=start_date, end_date=end_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "message": "关系创建成功",
        "forward": forward.to_dict(),
        "reverse": reverse.to_dict()
    }


@router.delete("/relation/family")
def delete_family_relation(
    person_a_id: int,
    person_b_id: int,
    db: Session = Depends(get_db)
):
    """删除家庭关系"""
    service = FamilyService(db)
    service.delete_family_relation(person_a_id, person_b_id)
    return {"message": "关系删除成功"}


@router.delete("/relation/spouse")
def delete_spouse_relation(
    person_a_id: Optional[int] = None,
    person_b_id: Optional[int] = None,
    relation_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """删除配偶关系段（多段时需传 relation_id 指定具体段）"""
    service = FamilyService(db)
    try:
        service.delete_spouse_relation(
            person_a_id=person_a_id,
            person_b_id=person_b_id,
            relation_id=relation_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"message": "关系删除成功"}


@router.get("/enums")
def get_relation_enums(
    db: Session = Depends(get_db)
):
    """获取关系枚举值"""
    return {
        "family_relation_types": [
            {"value": r.value, "name": r.name, "label": _family_short_label(r.value)}
            for r in FamilyRelationType
        ],
        "relation_natures": [
            {"value": r.value, "name": r.name,
             "label": f"{NATURE_LABELS[r.value]}（{_nature_suffix(r.value)}）"}
            for r in RelationNature
        ],
        "spouse_relation_types": [
            {"value": r.value, "name": r.name, "label": SPOUSE_ROLE_LABELS[r.value]}
            for r in SpouseRelationType
        ],
        "spouse_relation_natures": [
            {"value": r.value, "name": r.name, "label": get_spouse_relation_nature_label(r.value)}
            for r in SpouseRelationNature
        ]
    }


def _family_short_label(value: int) -> str:
    """枚举接口的短称谓（父/母/子/女）"""
    return {0: "父", 1: "母", 2: "子", 3: "女"}.get(value, "未知")


def _nature_suffix(value: int) -> str:
    return {0: "血亲", 1: "继亲", 2: "收养", 3: "结义", 4: "干亲"}.get(value, "未知")


def get_spouse_relation_nature_label(value: int) -> str:
    labels = {0: "现任", 1: "前任"}
    return labels.get(value, "未知")
