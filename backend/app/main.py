from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import engine
from app.models.base import Base

app = FastAPI(
    title="Personal CRM API",
    openapi_url=f"/api/v1/openapi.json"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/test")
async def test():
    from app.services.user import UserService
    from app.schemas.user import UserCreate
    from app.core.database import async_session
    async with async_session() as db:
        try:
            user_in = UserCreate(username="testuser", email="test@example.com", password="test123")
            user = await UserService.create(db, user_in)
            return {"user_id": user.id}
        except Exception as e:
            return {"error": str(e)}

app.include_router(api_router, prefix="/api/v1")