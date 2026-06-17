"""
农历日期工具服务

使用 lunar-python 库进行农历和公历日期的互转
"""
from datetime import date, datetime
from typing import Optional, Dict

try:
    from lunar_python import Solar, Lunar
    LUNAR_AVAILABLE = True
except ImportError:
    LUNAR_AVAILABLE = False
    print("警告: lunar-python 库未安装，农历功能不可用。请运行: pip install lunar-python")


class LunarService:
    """农历日期服务"""

    @staticmethod
    def is_available() -> bool:
        """检查农历库是否可用"""
        return LUNAR_AVAILABLE

    @staticmethod
    def solar_to_lunar(solar_date: date) -> Optional[Dict]:
        """
        公历日期转农历

        Args:
            solar_date: 公历日期

        Returns:
            {
                "year": 农历年,
                "month": 农历月,
                "day": 农历日,
                "year_zh": "二零二三",
                "month_zh": "正月",
                "day_zh": "十五",
                "display": "二零二三年正月十五",
                "is_leap_month": 是否闰月
            }
        """
        if not LUNAR_AVAILABLE or not solar_date:
            return None

        try:
            solar = Solar.fromYmd(solar_date.year, solar_date.month, solar_date.day)
            lunar = solar.getLunar()

            return {
                "year": lunar.getYear(),
                "month": lunar.getMonth(),
                "day": lunar.getDay(),
                "year_zh": lunar.getYearInChinese(),
                "month_zh": lunar.getMonthInChinese(),
                "day_zh": lunar.getDayInChinese(),
                "display": f"{lunar.getYearInChinese()}年{lunar.getMonthInChinese()}{lunar.getDayInChinese()}",
                "is_leap_month": lunar.getMonth() < 0,
                "zodiac": lunar.getYearShengXiao(),  # 生肖
                "gan_zhi": lunar.getYearInGanZhi()  # 干支
            }
        except Exception as e:
            print(f"公历转农历失败: {e}")
            return None

    @staticmethod
    def lunar_to_solar(year: int, month: int, day: int, is_leap_month: bool = False) -> Optional[date]:
        """
        农历日期转公历

        Args:
            year: 农历年
            month: 农历月
            day: 农历日
            is_leap_month: 是否闰月

        Returns:
            公历日期
        """
        if not LUNAR_AVAILABLE:
            return None

        try:
            if is_leap_month:
                month = -month

            lunar = Lunar.fromYmd(year, month, day)
            solar = lunar.getSolar()

            return date(solar.getYear(), solar.getMonth(), solar.getDay())
        except Exception as e:
            print(f"农历转公历失败: {e}")
            return None

    @staticmethod
    def parse_lunar_string(lunar_str: str) -> Optional[Dict]:
        """
        解析农历字符串

        支持格式:
        - "1990-05-15" (标准格式)
        - "1990年5月15日" (中文格式)
        - "一九九零年五月十五" (农历中文)

        Returns:
            {"year": 1990, "month": 5, "day": 15, "is_leap_month": False}
        """
        if not lunar_str:
            return None

        import re

        # 尝试解析标准格式
        match = re.match(r'^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$', lunar_str.strip())
        if match:
            return {
                "year": int(match.group(1)),
                "month": int(match.group(2)),
                "day": int(match.group(3)),
                "is_leap_month": False
            }

        # 尝试解析中文格式 "1990年5月15日"
        match = re.match(r'^(\d{4})年(\d{1,2})月(\d{1,2})日?$', lunar_str.strip())
        if match:
            return {
                "year": int(match.group(1)),
                "month": int(match.group(2)),
                "day": int(match.group(3)),
                "is_leap_month": False
            }

        return None

    @staticmethod
    def get_next_lunar_birthday(lunar_year: int, lunar_month: int, lunar_day: int,
                                 is_leap: bool = False) -> Optional[date]:
        """
        获取下一个农历生日对应的公历日期

        Args:
            lunar_year: 农历出生年（用于闰月判断）
            lunar_month: 农历月
            lunar_day: 农历日
            is_leap: 是否闰月

        Returns:
            下一个公历日期
        """
        if not LUNAR_AVAILABLE:
            return None

        try:
            today = date.today()
            current_year = today.year

            # 今年的农历生日
            this_year_solar = LunarService.lunar_to_solar(
                current_year, lunar_month, lunar_day, is_leap
            )

            if this_year_solar and this_year_solar >= today:
                return this_year_solar

            # 今年的已过，返回明年
            return LunarService.lunar_to_solar(
                current_year + 1, lunar_month, lunar_day, is_leap
            )
        except Exception as e:
            print(f"获取下一个农历生日失败: {e}")
            return None

    @staticmethod
    def get_solar_display_date(stored_date: date, is_lunar: bool) -> str:
        """
        获取用于显示的公历日期字符串

        设计理念：数据库统一存储"按某种历法记录的日期"。
        - is_lunar=False：stored_date 直接是公历日期，原样返回
        - is_lunar=True：stored_date 实际是农历日期（如 "1999-01-26" 表示"农历1999年正月二十六"），
          需要转换为对应的公历日期用于显示

        Args:
            stored_date: 数据库中存储的日期
            is_lunar: 是否按农历记录

        Returns:
            公历日期字符串 "YYYY-MM-DD"
        """
        if not stored_date:
            return None

        if not is_lunar:
            return stored_date.isoformat()

        # 是农历日期，需要转公历
        if not LUNAR_AVAILABLE:
            # 库不可用时，原样返回
            return stored_date.isoformat()

        try:
            # 解析存储的"农历日期"字符串
            parsed = LunarService.parse_lunar_string(stored_date.isoformat())
            if not parsed:
                return stored_date.isoformat()

            solar = LunarService.lunar_to_solar(
                parsed["year"],
                parsed["month"],
                parsed["day"],
                parsed.get("is_leap_month", False)
            )
            if solar:
                return solar.isoformat()
            return stored_date.isoformat()
        except Exception as e:
            print(f"农历转公历失败: {e}")
            return stored_date.isoformat()

    @staticmethod
    def normalize_lunar_to_solar(stored_date: date, is_lunar: bool) -> Optional[date]:
        """
        将存储的日期规范化为公历 date 对象

        Args:
            stored_date: 数据库中存储的日期
            is_lunar: 是否按农历记录

        Returns:
            规范化后的公历 date 对象
        """
        if not stored_date:
            return None

        if not is_lunar:
            return stored_date

        if not LUNAR_AVAILABLE:
            return stored_date

        try:
            parsed = LunarService.parse_lunar_string(stored_date.isoformat())
            if not parsed:
                return stored_date
            return LunarService.lunar_to_solar(
                parsed["year"],
                parsed["month"],
                parsed["day"],
                parsed.get("is_leap_month", False)
            )
        except Exception as e:
            print(f"农历转公历失败: {e}")
            return stored_date

    @staticmethod
    def get_age_from_lunar(lunar_year: int, lunar_month: int, lunar_day: int,
                            is_leap: bool = False,
                            end_date: Optional[date] = None) -> Optional[int]:
        """
        根据农历生日计算年龄

        Args:
            lunar_year: 农历出生年
            lunar_month: 农历月
            lunar_day: 农历日
            is_leap: 是否闰月
            end_date: 结束日期，默认为今天

        Returns:
            年龄
        """
        if not LUNAR_AVAILABLE:
            return None

        try:
            if end_date is None:
                end_date = date.today()

            # 获取结束日期前最近的公历生日
            solar_birth = LunarService.lunar_to_solar(
                lunar_year, lunar_month, lunar_day, is_leap
            )

            if not solar_birth:
                return None

            # 根据结束日期的公历生日计算年龄
            current_solar = LunarService.lunar_to_solar(
                end_date.year, lunar_month, lunar_day, is_leap
            )

            if current_solar and current_solar > end_date:
                # 今年的生日还没到
                return end_date.year - solar_birth.year - 1
            else:
                return end_date.year - solar_birth.year
        except Exception as e:
            print(f"计算农历年龄失败: {e}")
            return None
