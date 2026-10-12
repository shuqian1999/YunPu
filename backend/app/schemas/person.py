from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import date, datetime
from fastapi import HTTPException, status

from app.schemas.tag import TagResponse


def _validate_name_or_nickname(first_name, last_name, nickname):
    """检查姓名或称呼至少有一个不为空（去除首尾空格后）"""
    has_name = bool((last_name and last_name.strip()) or (first_name and first_name.strip()))
    has_nickname = bool(nickname and nickname.strip())
    if not (has_name or has_nickname):
        raise ValueError("姓名和称呼至少需要填写一个")


class PersonBase(BaseModel):
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    nickname: Optional[str] = Field(None, max_length=50)
    gender: Optional[int] = None
    birth_date: Optional[date] = None
    is_lunar_birth: bool = False
    death_date: Optional[date] = None
    is_lunar_death: bool = False
    country: Optional[str] = Field(None, max_length=50)
    hometown: Optional[str] = Field(None, max_length=100)
    residence: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    wechat: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=200)
    company: Optional[str] = Field(None, max_length=100)
    occupation: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=200)
    custom_fields: Optional[dict] = None
    is_me: bool = False
    is_favorite: bool = False
    importance: Optional[int] = Field(None, ge=1, le=5)


class PersonCreate(PersonBase):
    # 提交时以"标签名称数组"维护人物标签，后端自动按需创建
    tag_names: Optional[List[str]] = None

    @model_validator(mode="after")
    def check_name_or_nickname(self):
        _validate_name_or_nickname(self.first_name, self.last_name, self.nickname)
        return self


class PersonUpdate(PersonBase):
    tag_names: Optional[List[str]] = None

    # 部分更新不强制姓名校验：仅传标签/亲密度等字段时允许省略姓名。
    # 姓名完整性由创建接口（PersonCreate）与前端表单保证。


class PersonResponse(PersonBase):
    id: int
    avatar_url: Optional[str] = None
    importance: int = 3
    tags: List[TagResponse] = []
    last_contact_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True