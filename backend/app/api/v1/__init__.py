from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.persons import router as persons_router
from app.api.v1.events import router as events_router
from app.api.v1.reminders import router as reminders_router
from app.api.v1.countries import router as countries_router
from app.api.v1.family import router as family_router
from app.api.v1.event_types import router as event_types_router
from app.api.v1.settings import router as settings_router
from app.api.v1.data import router as data_router
from app.api.v1.groups import router as groups_router
from app.api.v1.search import router as search_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(dashboard_router)
api_router.include_router(persons_router)
api_router.include_router(events_router)
api_router.include_router(reminders_router)
api_router.include_router(countries_router)
api_router.include_router(family_router)
api_router.include_router(event_types_router)
api_router.include_router(settings_router)
api_router.include_router(data_router)
api_router.include_router(groups_router)
api_router.include_router(search_router)