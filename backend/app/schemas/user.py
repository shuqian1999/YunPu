from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, validator


class UserBase(BaseModel):
    username: str
    email: str  # Remove EmailStr for simplicity
    role: Optional[str] = "user"
    is_active: Optional[bool] = True
    language: Optional[str] = "en"


class UserCreate(UserBase):
    password: str

    @validator('password')
    def password_length(cls, v):
        if len(v) > 72:
            raise ValueError('password cannot be longer than 72 bytes')
        return v


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    language: Optional[str] = None


class UserInDBBase(UserBase):
    id: str
    contact_id: Optional[str] = None
    last_active_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None