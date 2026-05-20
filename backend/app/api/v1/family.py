from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict

from app.core.database import get_db
from app.services.family_service import FamilyService
from app.models.enums.relation_enums import (
    FamilyRelationType, RelationNature,
    SpouseRelationType, SpouseRelationNature
)

router = APIRouter(prefix="/family", tags=["家谱"])


@router.get("/tree")
def get_family_tree(
    db: Session = Depends(get_db)
):
    """获取家族树结构"""
    service = FamilyService(db)
    return service.get_family_tree()


@router.get("/relations/to-me")
def get_relations_to_me(
    db: Session = Depends(get_db)
):
    """获取所有与"我"的亲属关系"""
    service = FamilyService(db)
    return service.get_relations_to_me()


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
    forward, reverse = service.create_family_relation(
        person_a_id, person_b_id, relation, relation_nature
    )
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
    db: Session = Depends(get_db)
):
    """
    创建配偶关系
    
    Args:
        person_a_id: 人物A的ID
        person_b_id: 人物B的ID
        relation: 关系类型 (0:丈夫, 1:妻子, 2:姨太太, 3:男朋友, 4:女朋友)
        relation_nature: 关系性质 (0:现任, 1:前任)
    """
    service = FamilyService(db)
    forward, reverse = service.create_spouse_relation(
        person_a_id, person_b_id, relation, relation_nature
    )
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
    person_a_id: int,
    person_b_id: int,
    db: Session = Depends(get_db)
):
    """删除配偶关系"""
    service = FamilyService(db)
    service.delete_spouse_relation(person_a_id, person_b_id)
    return {"message": "关系删除成功"}


@router.get("/enums")
def get_relation_enums(
    db: Session = Depends(get_db)
):
    """获取关系枚举值"""
    return {
        "family_relation_types": [
            {"value": r.value, "name": r.name, "label": get_family_relation_label(r.value)}
            for r in FamilyRelationType
        ],
        "relation_natures": [
            {"value": r.value, "name": r.name, "label": get_relation_nature_label(r.value)}
            for r in RelationNature
        ],
        "spouse_relation_types": [
            {"value": r.value, "name": r.name, "label": get_spouse_relation_label(r.value)}
            for r in SpouseRelationType
        ],
        "spouse_relation_natures": [
            {"value": r.value, "name": r.name, "label": get_spouse_relation_nature_label(r.value)}
            for r in SpouseRelationNature
        ]
    }


def get_family_relation_label(value: int) -> str:
    labels = {0: "父", 1: "母", 2: "子", 3: "女"}
    return labels.get(value, "未知")


def get_relation_nature_label(value: int) -> str:
    labels = {0: "亲（血亲）", 1: "继（继亲）", 2: "养（收养）", 3: "义（结义）", 4: "干（干亲）"}
    return labels.get(value, "未知")


def get_spouse_relation_label(value: int) -> str:
    labels = {0: "丈夫", 1: "妻子", 2: "姨太太/妾", 3: "男朋友", 4: "女朋友"}
    return labels.get(value, "未知")


def get_spouse_relation_nature_label(value: int) -> str:
    labels = {0: "现任", 1: "前任"}
    return labels.get(value, "未知")
