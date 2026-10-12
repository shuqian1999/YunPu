from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


# ---------------------------------------------------------------------------
# 关系类型
# ---------------------------------------------------------------------------

class SocialTypeCreate(BaseModel):
    name: str = Field(..., max_length=20, description="正向/无向称谓")
    reverse_name: Optional[str] = Field(None, max_length=20, description="反向称谓，有向类型必填")
    directed: bool = False
    color: str = Field("#fa8c16", max_length=10)


class SocialTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=20)
    reverse_name: Optional[str] = Field(None, max_length=20)
    directed: Optional[bool] = None
    color: Optional[str] = Field(None, max_length=10)


# ---------------------------------------------------------------------------
# 关系实例
# ---------------------------------------------------------------------------

class SocialRelationBase(BaseModel):
    person_a_id: int = Field(..., description="有向关系中 a 是 b 的{type.name}")
    person_b_id: int
    type_id: int
    # 范围 1-5 由业务层校验（统一返回 400 中文提示）
    closeness: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    introducer_id: Optional[int] = None


class SocialRelationCreate(SocialRelationBase):
    pass


class SocialRelationUpdate(BaseModel):
    person_a_id: Optional[int] = None
    person_b_id: Optional[int] = None
    type_id: Optional[int] = None
    closeness: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    introducer_id: Optional[int] = None
