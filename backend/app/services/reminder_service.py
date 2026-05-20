from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import List
from app.models.reminder import Reminder
from app.models.notification import Notification
from app.models.person import Person
from app.utils.lunar import LunarConverter


class ReminderService:
    def __init__(self, db: Session):
        self.db = db

    def check_reminders(self) -> List[Notification]:
        today = date.today()
        reminders = self.db.query(Reminder).filter(
            Reminder.enabled == True
        ).all()

        notifications = []

        for reminder in reminders:
            remind_date = self._calculate_remind_date(reminder, today)
            if remind_date == today:
                notification = self._create_notification(reminder)
                self.db.add(notification)
                notifications.append(notification)

                if reminder.repeat_type == "once":
                    reminder.enabled = False

        if notifications:
            self.db.commit()

        return notifications

    def _calculate_remind_date(self, reminder: Reminder, today: date) -> date:
        base_date = reminder.remind_date

        if reminder.is_lunar and LunarConverter.is_lunar_date_available():
            return self._calculate_lunar_remind_date(base_date, today)

        repeat_type = getattr(reminder, 'repeat_type', 'once')
        if repeat_type == "once":
            return base_date
        elif repeat_type == "yearly":
            return date(today.year, base_date.month, base_date.day)
        elif repeat_type == "monthly":
            day = min(base_date.day, 28)
            return date(today.year, today.month, day)
        elif repeat_type == "weekly":
            weekday = base_date.weekday()
            days_ahead = weekday - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return today + timedelta(days=days_ahead)

        return base_date

    def _calculate_lunar_remind_date(self, base_date: date, today: date) -> date:
        lunar_year, lunar_month, lunar_day, is_leap = LunarConverter.solar_to_lunar(base_date)

        solar_date = LunarConverter.lunar_to_solar(today.year, lunar_month, lunar_day, is_leap)

        if solar_date is None:
            return base_date

        if solar_date < today:
            solar_date = LunarConverter.lunar_to_solar(today.year + 1, lunar_month, lunar_day, is_leap)

        return solar_date if solar_date else base_date

    def _create_notification(self, reminder: Reminder) -> Notification:
        content = self._generate_reminder_content(reminder)

        return Notification(
            type="reminder",
            title=reminder.title,
            content=content,
            related_id=reminder.id
        )

    def _generate_reminder_content(self, reminder: Reminder) -> str:
        content_parts = []

        if reminder.person_id:
            person = self.db.query(Person).filter(
                Person.id == reminder.person_id
            ).first()
            if person:
                name = person.nickname or f"{person.first_name or ''}{person.last_name or ''}".strip()
                if name:
                    content_parts.append(f"人物：{name}")

        if reminder.is_lunar:
            content_parts.append("农历")

        repeat_type = getattr(reminder, 'repeat_type', 'once')
        if repeat_type != "once":
            repeat_map = {
                "yearly": "每年",
                "monthly": "每月",
                "weekly": "每周"
            }
            repeat_text = repeat_map.get(repeat_type, "")
            if repeat_text:
                content_parts.append(repeat_text)

        return "，".join(content_parts) if content_parts else "提醒"