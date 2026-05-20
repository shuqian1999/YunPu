from pydantic import BaseModel, EmailStr


class UserSettingsResponse(BaseModel):
    username: str
    email: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None


class UserSettingsUpdate(BaseModel):
    email: EmailStr | None = None
    display_name: str | None = None
    avatar_url: str | None = None


class SystemSettingsResponse(BaseModel):
    person_count: int
    event_count: int
    reminder_count: int
    database_size: str