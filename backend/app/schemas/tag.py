from pydantic import BaseModel, Field
from typing import Optional


class TagBase(BaseModel):
    name: str = Field(..., max_length=30)
    color: str = Field("#409EFF", max_length=10)


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=30)
    color: Optional[str] = Field(None, max_length=10)


class TagResponse(TagBase):
    id: int

    class Config:
        from_attributes = True


class TagWithCount(TagResponse):
    person_count: int = 0
