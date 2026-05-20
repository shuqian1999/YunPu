from datetime import date
from typing import Tuple, Optional

try:
    from zhdate import ZhDate
    ZH_DATE_AVAILABLE = True
except ImportError:
    ZH_DATE_AVAILABLE = False


class LunarConverter:
    """农历转换工具类"""

    _lunar_days = [
        "初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
        "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
        "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十"
    ]

    @staticmethod
    def solar_to_lunar(solar_date: date) -> Tuple[int, int, int, bool]:
        """公历转农历

        Args:
            solar_date: 公历日期

        Returns:
            Tuple[年, 月, 日, 是否闰月]
        """
        if not ZH_DATE_AVAILABLE:
            return (0, 0, 1, False)

        lunar = ZhDate.from_datetime(solar_date)
        return (lunar.lunar_year, lunar.lunar_month, lunar.lunar_day, lunar.is_leap)

    @staticmethod
    def lunar_to_solar(year: int, month: int, day: int, is_leap: bool = False) -> Optional[date]:
        """农历转公历

        Args:
            year: 农历年
            month: 农历月
            day: 农历日
            is_leap: 是否闰月

        Returns:
            公历日期，如果转换失败返回None
        """
        if not ZH_DATE_AVAILABLE:
            return None

        try:
            lunar = ZhDate(year, month, day, is_leap)
            return lunar.to_datetime().date()
        except Exception:
            return None

    @staticmethod
    def get_lunar_string(solar_date: date) -> str:
        """获取农历日期字符串

        Args:
            solar_date: 公历日期

        Returns:
            农历日期字符串，如 "农历2024年正月初一"
        """
        if not ZH_DATE_AVAILABLE:
            return "农历转换功能不可用"

        year, month, day, is_leap = LunarConverter.solar_to_lunar(solar_date)

        if year == 0:
            return "农历转换功能不可用"

        month_str = f"闰{month}" if is_leap else str(month)
        day_str = LunarConverter._get_lunar_day_string(day)

        return f"农历{year}年{month_str}月{day_str}"

    @staticmethod
    def _get_lunar_day_string(day: int) -> str:
        """获取农历日的字符串表示"""
        if 1 <= day <= 30:
            return LunarConverter._lunar_days[day - 1]
        return str(day)

    @staticmethod
    def is_lunar_date_available() -> bool:
        """检查农历转换功能是否可用"""
        return ZH_DATE_AVAILABLE
