from pydantic import BaseModel


class GroupCreate(BaseModel):
    name: str
    color: str = "#409EFF"
    description: str | None = None


class GroupUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
    description: str | None = None


class GroupResponse(BaseModel):
    id: int
    name: str
    color: str
    description: str | None
    created_at: str
    updated_at: str | None

    class Config:
        orm_mode = True