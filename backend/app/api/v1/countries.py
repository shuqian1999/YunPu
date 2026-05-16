from fastapi import APIRouter
from app.core.countries import COUNTRIES

router = APIRouter(tags=["系统"])


@router.get("/countries")
def get_countries():
    return COUNTRIES