from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import engine, SessionLocal, init_db
from app.models.base import Base
from app.models.user import User
from app.models.person import Person
from app.models.event import Event
from app.models.reminder import Reminder
from app.models.event_type import EventType
from app.core.security import hash_password

app = FastAPI(
    title=settings.app_name,
    openapi_url=f"/api/v1/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.username == settings.default_username).first()
        if not existing_user:
            user = User(
                username=settings.default_username,
                password_hash=hash_password(settings.default_password)
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            person = Person(
                user_id=user.id,
                nickname="我",
                is_me=True
            )
            db.add(person)
            db.commit()
            
            print(f"初始用户创建成功：{settings.default_username}")
    finally:
        db.close()

app.include_router(api_router, prefix="/api/v1")
