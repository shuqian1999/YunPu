from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


class PersonBase(BaseModel):
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    nickname: Optional[str] = Field(None, max_length=50)
    gender: Optional[int] = None
    birth_date: Optional[date] = None
    death_date: Optional[date] = None
    country: Optional[str] = Field(None, max_length=50)
    hometown: Optional[str] = Field(None, max_length=100)
    residence: Optional[str] = Field(None, max_length=100)
    custom_fields: Optional[dict] = None
    is_me: bool = False


class PersonCreate(PersonBase):
    pass


class PersonUpdate(PersonBase):
    pass


class PersonResponse(PersonBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_contact_at: Optional[datetime] = None

    class Config:
        from_attributes = True