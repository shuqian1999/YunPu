from pydantic import BaseModel


class SystemSettingsResponse(BaseModel):
    person_count: int
    event_count: int
    reminder_count: int
    database_size: str
