from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional

from app.core.database import get_db
from app.services.lunar_service import LunarService

router = APIRouter(prefix="/lunar", tags=["农历"])


@router.get("/convert")
def convert_solar_to_lunar(
    date_str: str,
    db: Session = Depends(get_db)
):
    """
    公历日期转农历

    Args:
        date_str: 公历日期字符串，格式 YYYY-MM-DD
    """
    try:
        solar_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")

    if not LunarService.is_available():
        return {
            "solar_date": date_str,
            "display": "",
            "available": False,
            "message": "农历转换服务不可用，请手动输入农历日期"
        }

    lunar = LunarService.solar_to_lunar(solar_date)
    if not lunar:
        return {
            "solar_date": date_str,
            "display": "",
            "available": True,
            "message": "转换失败"
        }

    return {
        "solar_date": date_str,
        "year": lunar["year"],
        "month": lunar["month"],
        "day": lunar["day"],
        "year_zh": lunar["year_zh"],
        "month_zh": lunar["month_zh"],
        "day_zh": lunar["day_zh"],
        "display": lunar["display"],
        "zodiac": lunar.get("zodiac", ""),
        "gan_zhi": lunar.get("gan_zhi", ""),
        "is_leap_month": lunar.get("is_leap_month", False),
        "available": True
    }


@router.get("/next-birthday")
def get_next_lunar_birthday(
    year: int,
    month: int,
    day: int,
    is_leap: bool = False,
    db: Session = Depends(get_db)
):
    """
    获取下一个农历生日对应的公历日期
    """
    if not LunarService.is_available():
        return {
            "available": False,
            "message": "农历服务不可用"
        }

    next_date = LunarService.get_next_lunar_birthday(year, month, day, is_leap)
    if not next_date:
        return {
            "available": True,
            "message": "获取失败"
        }

    return {
        "available": True,
        "next_solar_date": next_date.isoformat(),
        "days_until": (next_date - date.today()).days
    }
