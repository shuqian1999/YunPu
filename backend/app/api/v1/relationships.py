"""通用关系图谱：全局 3D 链接图 + 个人中心网络（Ego Network）"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.relationship_service import RelationshipService

router = APIRouter(prefix="/relationships", tags=["关系图谱"])

VALID_EDGE_TYPES = {"family", "spouse", "social", "group", "tag"}
DEFAULT_EDGE_TYPES = ["family", "spouse", "social", "group"]


@router.get("/graph")
def get_relationship_graph(
    types: str = Query(
        default="family,spouse,social,group",
        description="边类型，逗号分隔：family/spouse/social/group/tag"
    ),
    importance_min: int = Query(default=0, ge=0, le=5),
    alive_only: bool = Query(default=False),
    keyword: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """全局关系图数据：nodes + edges（仅直接关系边）"""
    edge_types = [t.strip() for t in types.split(",") if t.strip() in VALID_EDGE_TYPES]
    if not edge_types:
        edge_types = list(DEFAULT_EDGE_TYPES)
    service = RelationshipService(db)
    return service.get_graph(
        edge_types=edge_types,
        importance_min=importance_min,
        alive_only=alive_only,
        keyword=keyword
    )


@router.get("/ego/{person_id}")
def get_ego_network(
    person_id: int,
    db: Session = Depends(get_db)
):
    """以指定人物为中心的一级关系网络（按长辈/配偶/晚辈/同组/同标签分类）"""
    service = RelationshipService(db)
    return service.get_ego_network(person_id)
