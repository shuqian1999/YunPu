from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from app.models.reminder import Reminder
from app.models.event import Event
from app.services.lunar_service import LunarService


def process_due_reminders(db):
    """
    每日定时任务：
    1. 找出当天到期的提醒
    2. 如果开启了 trans_event，为其创建对应事件
    3. 如果是周期性提醒，自动将日期推进到下一个周期，并保持启用
    4. 一次性提醒（once）处理后禁用
    """
    today = date.today()
    converted_count = 0
    advanced_count = 0

    # 找出当天到期且已启用的提醒
    due_reminders = db.query(Reminder).filter(
        Reminder.remind_date == today,
        Reminder.enabled == True
    ).all()

    for reminder in due_reminders:
        # 1. 转换为事件
        if reminder.trans_event:
            event = Event(
                person_id=reminder.person_id,
                event_type_id=reminder.event_type_id,
                title=reminder.title,
                description=reminder.description,
                event_date=reminder.remind_date,
                is_lunar=reminder.is_lunar,
                location=reminder.location,
            )
            db.add(event)
            converted_count += 1

        # 2. 推进到下一个周期
        if reminder.repeat_type != "once":
            # 周期性提醒：自动推进日期，保持启用，继续生效
            next_date = _calculate_next_date(reminder.remind_date, reminder.is_lunar, reminder.repeat_type)
            reminder.remind_date = next_date
            advanced_count += 1
        else:
            # 一次性提醒：处理完后禁用
            reminder.enabled = False

        db.commit()

    return {
        "converted": converted_count,
        "advanced": advanced_count,
        "total_processed": len(due_reminders)
    }


def _calculate_next_date(current: date, is_lunar: bool, repeat_type: str) -> date:
    """计算下一个周期的日期"""
    if repeat_type == "yearly":
        if is_lunar:
            return LunarService.get_next_lunar_year_date(current)
        else:
            return current + relativedelta(years=1)
    elif repeat_type == "monthly":
        return current + relativedelta(months=1)
    elif repeat_type == "weekly":
        return current + timedelta(weeks=1)
    else:
        return current
