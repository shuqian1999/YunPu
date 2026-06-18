"""邮件发送服务"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
from datetime import date, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.email import EmailConfig, EmailTemplate, EmailLog
from app.models.reminder import Reminder
from app.models.person import Person
from app.utils.lunar import LunarConverter

logger = logging.getLogger(__name__)


# 模板可用的变量（针对 Reminder 字段）
TEMPLATE_VARIABLES = [
    ("{{title}}", "提醒标题"),
    ("{{name}}", "人物姓名"),
    ("{{nickname}}", "人物称呼"),
    ("{{date}}", "提醒日期（公历）"),
    ("{{days_until}}", "距离天数"),
    ("{{event_type}}", "提醒类型（生日/纪念日等）"),
    ("{{event_type_color}}", "提醒类型颜色"),
    ("{{description}}", "提醒描述"),
    ("{{location}}", "提醒地点"),
    ("{{repeat_type}}", "周期类型（不重复/每年/每月/每周）"),
    ("{{is_lunar}}", "是否农历"),
    ("{{lunar_date}}", "农历日期"),
    ("{{advance_days}}", "提前提醒天数"),
    ("{{trans_event}}", "是否到期转事件"),
]


class EmailService:
    def __init__(self, db: Session):
        self.db = db

    # ---------- 配置 ----------
    def get_config(self) -> Optional[EmailConfig]:
        return self.db.query(EmailConfig).order_by(EmailConfig.id.asc()).first()

    def get_or_create_config(self) -> EmailConfig:
        config = self.get_config()
        if not config:
            config = EmailConfig()
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
        return config

    def update_config(self, data: dict) -> EmailConfig:
        config = self.get_or_create_config()
        for key, value in data.items():
            if value is None:
                continue
            if key == "reminder_types" and isinstance(value, list):
                value = ",".join(value)
            setattr(config, key, value)
        self.db.commit()
        self.db.refresh(config)
        return config

    # ---------- 模板 ----------
    def get_default_template(self) -> Optional[EmailTemplate]:
        return self.db.query(EmailTemplate).filter(
            EmailTemplate.is_default == True
        ).first()

    def get_template_for_type(self, event_type: str) -> Optional[EmailTemplate]:
        """根据提醒类型获取模板，优先匹配专用模板，其次默认模板"""
        if not event_type:
            return self.get_default_template()
        template = self.db.query(EmailTemplate).filter(
            EmailTemplate.event_type == event_type
        ).first()
        if template:
            return template
        return self.get_default_template()

    def list_templates(self) -> List[EmailTemplate]:
        return self.db.query(EmailTemplate).order_by(EmailTemplate.id.asc()).all()

    def get_template(self, template_id: int) -> Optional[EmailTemplate]:
        return self.db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()

    def create_template(self, data: dict) -> EmailTemplate:
        if data.get("is_default"):
            self._clear_default()
        template = EmailTemplate(**data)
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def update_template(self, template_id: int, data: dict) -> Optional[EmailTemplate]:
        template = self.get_template(template_id)
        if not template:
            return None
        if data.get("is_default"):
            self._clear_default()
        for key, value in data.items():
            if value is None:
                continue
            setattr(template, key, value)
        self.db.commit()
        self.db.refresh(template)
        return template

    def delete_template(self, template_id: int) -> bool:
        template = self.get_template(template_id)
        if not template:
            return False
        self.db.delete(template)
        self.db.commit()
        return True

    def _clear_default(self):
        self.db.query(EmailTemplate).filter(EmailTemplate.is_default == True).update(
            {"is_default": False}
        )

    # ---------- 模板渲染 ----------
    def render_template(self, template: str, variables: dict) -> str:
        """替换模板中的变量"""
        result = template
        for key, value in variables.items():
            placeholder = "{{" + key + "}}"
            result = result.replace(placeholder, str(value if value is not None else ""))
        return result

    def build_reminder_variables(self, reminder: Reminder, person: Optional[Person],
                                 days_until: int) -> dict:
        """构建 Reminder 的模板变量（包含所有对齐字段）"""
        remind_date = reminder.remind_date
        is_lunar = bool(getattr(reminder, "is_lunar", False))
        lunar_text = LunarConverter.get_lunar_string(remind_date) if is_lunar else ""

        name = ""
        nickname = ""
        if person:
            nickname = person.nickname or ""
            last = person.last_name or ""
            first = person.first_name or ""
            name = (last + first) or nickname

        # 周期类型中文标签
        repeat_type_map = {
            "once": "不重复",
            "yearly": "每年",
            "monthly": "每月",
            "weekly": "每周",
        }
        repeat_type_label = repeat_type_map.get(reminder.repeat_type or "once", "")

        # 事件类型
        et_name = ""
        et_color = "#c0c4cc"
        if reminder.event_type:
            et_name = reminder.event_type.name
            et_color = reminder.event_type.color or "#c0c4cc"

        return {
            "title": reminder.title or "",
            "name": name,
            "nickname": nickname,
            "date": remind_date.strftime("%Y年%m月%d日") if remind_date else "",
            "days_until": days_until,
            "event_type": et_name,
            "event_type_color": et_color,
            "description": reminder.description or "",
            "location": reminder.location or "",
            "repeat_type": repeat_type_label,
            "is_lunar": "是" if is_lunar else "否",
            "lunar_date": lunar_text,
            "advance_days": reminder.remind_advance_days or 0,
            "trans_event": "是" if getattr(reminder, "trans_event", False) else "否",
        }

    # ---------- 数据收集 ----------
    def get_upcoming_reminders(self, days: int, types: List[str]) -> List[dict]:
        """获取指定天数内的未来提醒

        Returns:
            reminders_data 列表，每项包含 reminder/person/actual_date/days_until
        """
        today = date.today()
        end_date = today + timedelta(days=days)
        type_set = set(t.strip() for t in (types or []) if t.strip())

        reminders = self.db.query(Reminder).filter(Reminder.enabled == True).all()
        reminders_data = []

        for reminder in reminders:
            actual_date = self._calculate_reminder_actual_date(reminder, today)
            if actual_date is None:
                continue
            if not (today <= actual_date <= end_date):
                continue

            # 类型过滤：reminder 的 event_type 必须匹配
            et_name = reminder.event_type.name if reminder.event_type else ""
            if type_set and et_name and et_name not in type_set:
                continue
            # 如果 reminder 没有类型但 type_set 也不空，仍跳过
            if type_set and not et_name:
                continue

            days_until = (actual_date - today).days
            person = None
            if reminder.person_id:
                person = self.db.query(Person).filter(
                    Person.id == reminder.person_id
                ).first()
            reminders_data.append({
                "reminder": reminder,
                "person": person,
                "actual_date": actual_date,
                "days_until": days_until,
            })

        reminders_data.sort(key=lambda x: x["actual_date"])
        return reminders_data

    def _calculate_reminder_actual_date(self, reminder: Reminder, today: date) -> Optional[date]:
        """计算提醒实际触发的公历日期"""
        base = reminder.remind_date
        is_lunar = bool(getattr(reminder, "is_lunar", False))
        repeat_type = getattr(reminder, "repeat_type", "once")

        if is_lunar and LunarConverter.is_lunar_date_available():
            try:
                _, lm, ld, is_leap = LunarConverter.solar_to_lunar(base)
                solar = LunarConverter.lunar_to_solar(today.year, lm, ld, is_leap)
                if solar is None:
                    return None
                if solar < today:
                    solar = LunarConverter.lunar_to_solar(today.year + 1, lm, ld, is_leap)
                return solar
            except Exception:
                return base

        if repeat_type == "once":
            return base if base >= today else None
        elif repeat_type == "yearly":
            try:
                return date(today.year, base.month, base.day)
            except ValueError:
                # 2月29日特殊处理
                return date(today.year, 2, 28)
        elif repeat_type == "monthly":
            day = min(base.day, 28)
            return date(today.year, today.month, day)
        elif repeat_type == "weekly":
            weekday = base.weekday()
            days_ahead = weekday - today.weekday()
            if days_ahead < 0:
                days_ahead += 7
            return today + timedelta(days=days_ahead)
        return None

    # ---------- 邮件内容生成 ----------
    def build_email_content(self, reminders_data: List[dict]) -> Tuple[str, str]:
        """根据默认/分类型模板生成邮件主题和正文

        Returns:
            (subject, html_content)
        """
        default_template = self.get_default_template()
        if not default_template:
            return self._build_default_email(reminders_data)

        subject = default_template.subject
        items_html = []

        for rd in reminders_data:
            reminder = rd["reminder"]
            et_name = reminder.event_type.name if reminder.event_type else ""
            template = self.get_template_for_type(et_name) or default_template
            variables = self.build_reminder_variables(
                reminder, rd.get("person"), rd["days_until"]
            )
            subject_rendered = self.render_template(template.subject, variables)
            content_rendered = self.render_template(template.content, variables)

            # 彩色左边条
            et_color = reminder.event_type.color if reminder.event_type else "#c0c4cc"
            items_html.append(f"""
                <div style="margin-bottom: 16px; padding: 12px; border-left: 3px solid {et_color}; background: #f7f8fa; border-radius: 4px;">
                    {content_rendered}
                </div>
            """)
            # 使用第一个提醒的主题作为邮件主题
            if rd == reminders_data[0]:
                subject = subject_rendered

        full_html = f"""
        <html>
        <body style="font-family: 'Microsoft YaHei', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #303133; border-bottom: 2px solid #409EFF; padding-bottom: 10px;">📅 提醒通知</h2>
            <p style="color: #909399;">您有 {len(reminders_data)} 项需要关注的事务：</p>
            {''.join(items_html)}
            <hr style="margin-top: 30px; border: none; border-top: 1px solid #ebeef5;"/>
            <p style="color: #909399; font-size: 12px; text-align: center;">本邮件由 云谱 自动发送</p>
        </body>
        </html>
        """
        return subject, full_html

    def _build_default_email(self, reminders_data: List[dict]) -> Tuple[str, str]:
        """内置默认邮件（无模板时使用）"""
        subject = f"📅 您有 {len(reminders_data)} 项提醒"
        rows = []
        for rd in reminders_data:
            reminder = rd["reminder"]
            et_name = reminder.event_type.name if reminder.event_type else "提醒"
            et_color = reminder.event_type.color if reminder.event_type else "#c0c4cc"
            person_name = ""
            if rd.get("person"):
                p = rd["person"]
                person_name = p.nickname or f"{p.last_name or ''}{p.first_name or ''}"

            date_text = rd["actual_date"].strftime("%Y年%m月%d日")
            lunar_tag = ""
            if getattr(reminder, "is_lunar", False):
                lunar_tag = '<span style="background:#e6a23c;color:#fff;padding:1px 6px;border-radius:3px;font-size:11px;margin-left:4px;">农历</span>'

            repeat_tag = ""
            repeat_type = getattr(reminder, "repeat_type", "once")
            if repeat_type and repeat_type != "once":
                repeat_map = {"yearly": "每年", "monthly": "每月", "weekly": "每周"}
                label = repeat_map.get(repeat_type, "")
                if label:
                    repeat_tag = f'<span style="background:#909399;color:#fff;padding:1px 6px;border-radius:3px;font-size:11px;margin-left:4px;">{label}</span>'

            description_html = ""
            if reminder.description:
                description_html = f'<div style="color:#909399;font-size:12px;margin-top:4px;">{reminder.description}</div>'

            location_html = ""
            if reminder.location:
                location_html = f'<div style="color:#909399;font-size:12px;">📍 {reminder.location}</div>'

            rows.append(f"""
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #ebeef5;">
                        <span style="background:{et_color};color:#fff;padding:2px 8px;border-radius:3px;font-size:12px;">{et_name}</span>
                    </td>
                    <td style="padding: 8px; border-bottom: 1px solid #ebeef5;">
                        <strong>{reminder.title}</strong>
                        {f'<div style="color:#909399;font-size:12px;">{person_name}</div>' if person_name else ''}
                        {description_html}
                        {location_html}
                    </td>
                    <td style="padding: 8px; border-bottom: 1px solid #ebeef5;">
                        {date_text}{lunar_tag}{repeat_tag}
                    </td>
                    <td style="padding: 8px; border-bottom: 1px solid #ebeef5; color: #f56c6c;">
                        {rd['days_until']} 天后
                    </td>
                </tr>
            """)
        body = f"""
        <html>
        <body style="font-family: 'Microsoft YaHei', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #303133; border-bottom: 2px solid #409EFF; padding-bottom: 10px;">📅 云谱提醒</h2>
            <p>您有 {len(reminders_data)} 项需要关注：</p>
            <table style="width:100%; border-collapse: collapse; margin: 16px 0;">
                <thead>
                    <tr style="background: #f5f7fa;">
                        <th style="padding: 10px; text-align: left;">类型</th>
                        <th style="padding: 10px; text-align: left;">事项</th>
                        <th style="padding: 10px; text-align: left;">日期</th>
                        <th style="padding: 10px; text-align: left;">距今</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
            <p style="color: #909399; font-size: 12px; text-align: center;">本邮件由 云谱 自动发送</p>
        </body>
        </html>
        """
        return subject, body

    # ---------- 发送 ----------
    def send_email(self, subject: str, content: str,
                   receivers: List[str], is_html: bool = True,
                   preview: Optional[str] = None) -> Tuple[bool, str, int]:
        """发送邮件"""
        config = self.get_config()
        if not config or not config.smtp_host or not config.username or not config.password:
            return False, "邮件配置不完整", 0

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = Header(subject, "utf-8")
            msg["From"] = formataddr(["云谱", config.username])
            msg["To"] = ", ".join(receivers)

            if is_html:
                msg.attach(MIMEText(content, "html", "utf-8"))
            else:
                msg.attach(MIMEText(content, "plain", "utf-8"))

            if config.use_ssl:
                server = smtplib.SMTP_SSL(config.smtp_host, config.smtp_port, timeout=15)
            else:
                server = smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=15)
                server.starttls()

            server.login(config.username, config.password)
            server.sendmail(config.username, receivers, msg.as_string())
            server.quit()

            preview_text = preview or content[:200] if content else ""
            log = EmailLog(
                subject=subject,
                receivers=",".join(receivers),
                content_preview=preview_text,
                status="success",
                related_count=0,
            )
            self.db.add(log)
            self.db.commit()
            return True, "", 0
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            log = EmailLog(
                subject=subject,
                receivers=",".join(receivers),
                content_preview=(preview or content or "")[:200],
                status="failed",
                error_message=str(e),
            )
            self.db.add(log)
            self.db.commit()
            return False, str(e), 0

    def send_reminder_email(self, days: Optional[int] = None,
                            types: Optional[List[str]] = None
                            ) -> Tuple[bool, str]:
        """发送提醒邮件（用于定时任务或手动触发）"""
        config = self.get_config()
        if not config or not config.enabled:
            return False, "邮件通知未启用"
        if not config.receivers:
            return False, "未配置接收邮箱"

        days = days if days is not None else config.advance_days
        types = types if types is not None else config.reminder_types

        reminders_data = self.get_upcoming_reminders(days, types)

        if not reminders_data:
            return True, "指定范围内没有需要提醒的事项"

        subject, body = self.build_email_content(reminders_data)
        receivers = [r.strip() for r in config.receivers.split(",") if r.strip()]

        preview = f"{len(reminders_data)} 个提醒"
        success, error, _ = self.send_email(subject, body, receivers, preview=preview)
        if success:
            return True, f"已发送 {len(reminders_data)} 项提醒"
        return False, error

    def test_connection(self) -> Tuple[bool, str]:
        """测试 SMTP 连接"""
        config = self.get_config()
        if not config or not config.smtp_host or not config.username or not config.password:
            return False, "邮件配置不完整，请先填写 SMTP 信息"

        try:
            if config.use_ssl:
                server = smtplib.SMTP_SSL(config.smtp_host, config.smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=10)
                server.starttls()
            server.login(config.username, config.password)
            server.quit()
            return True, "SMTP 连接测试成功"
        except Exception as e:
            return False, f"连接失败: {str(e)}"

    def test_send(self, receiver: Optional[str] = None) -> Tuple[bool, str]:
        """发送测试邮件"""
        config = self.get_config()
        if not config:
            return False, "请先配置邮件信息"

        receiver = receiver or config.receivers
        if not receiver:
            return False, "请指定接收邮箱"

        subject = "🧪 云谱邮件通知测试"
        body = f"""
        <html>
        <body style="font-family: 'Microsoft YaHei', Arial, sans-serif; padding: 20px;">
            <h2 style="color: #67c23a;">✅ 邮件通知配置成功</h2>
            <p>这是一封来自 <strong>云谱</strong> 的测试邮件。</p>
            <p>如果您收到了这封邮件，说明您的邮件通知功能已配置成功。</p>
            <hr/>
            <p style="color: #909399; font-size: 12px;">发送时间：{date.today()}</p>
        </body>
        </html>
        """
        receivers = [r.strip() for r in receiver.split(",") if r.strip()]
        success, error, _ = self.send_email(subject, body, receivers)
        if success:
            return True, "测试邮件已发送"
        return False, error

    # ---------- 日志 ----------
    def list_logs(self, limit: int = 50) -> List[EmailLog]:
        return self.db.query(EmailLog).order_by(EmailLog.created_at.desc()).limit(limit).all()

    def clear_logs(self) -> int:
        count = self.db.query(EmailLog).delete()
        self.db.commit()
        return count
