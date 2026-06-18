import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def check_all_reminders():
    """生成站内通知（每天 0 点执行）"""
    from app.core.database import SessionLocal
    from app.services.reminder_service import ReminderService

    db = SessionLocal()
    try:
        service = ReminderService(db)
        notifications = service.check_reminders()
        if notifications:
            logger.info(f"生成了 {len(notifications)} 条通知")
    except Exception as e:
        logger.error(f"检查提醒时出错: {e}")
    finally:
        db.close()


async def send_scheduled_email():
    """按用户配置的发送时间发送邮件通知"""
    from app.core.database import SessionLocal
    from app.services.email_service import EmailService

    db = SessionLocal()
    try:
        service = EmailService(db)
        success, message = service.send_reminder_email()
        logger.info(f"定时邮件发送: success={success}, message={message}")
    except Exception as e:
        logger.error(f"发送定时邮件出错: {e}")
    finally:
        db.close()


async def process_due_reminders_job():
    """每日 0:30 处理到期提醒：转换事件、推进周期"""
    from app.core.database import SessionLocal
    from app.services.reminder_service import process_due_reminders

    db = SessionLocal()
    try:
        result = process_due_reminders(db)
        if result["total_processed"] > 0:
            logger.info(
                f"处理到期提醒: 总计 {result['total_processed']} 条，"
                f"转换事件 {result['converted']} 条，推进周期 {result['advanced']} 条"
            )
    except Exception as e:
        logger.error(f"处理到期提醒出错: {e}")
    finally:
        db.close()


def _job_listener(event):
    if event.exception:
        logger.error(f"定时任务执行失败: {event.exception}")
    else:
        logger.info(f"定时任务执行成功: {event.job_id}")


def start_scheduler():
    # 监听器
    scheduler.add_listener(
        _job_listener,
        EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
    )

    # 每日 0 点生成站内通知
    scheduler.add_job(
        check_all_reminders,
        CronTrigger(hour=0, minute=0),
        id='check_reminders',
        name='每日提醒检查',
        replace_existing=True
    )

    # 邮件发送任务：默认每天 08:00 发送
    # 实际发送时间会在执行时根据配置覆盖（这里设一个兜底时间）
    scheduler.add_job(
        send_scheduled_email,
        CronTrigger(hour=8, minute=0),
        id='send_email',
        name='邮件提醒发送',
        replace_existing=True
    )

    # 每日 00:30 处理到期提醒（生成事件/推进周期）
    scheduler.add_job(
        process_due_reminders_job,
        CronTrigger(hour=0, minute=30),
        id='process_due_reminders',
        name='到期提醒处理',
        replace_existing=True
    )

    scheduler.start()
    logger.info("定时任务调度器已启动")


def reschedule_email_job(send_time: str):
    """根据用户的发送时间配置重新调度邮件任务

    Args:
        send_time: HH:MM 格式
    """
    try:
        hour, minute = send_time.split(":")
        hour, minute = int(hour), int(minute)
    except (ValueError, AttributeError):
        hour, minute = 8, 0

    job = scheduler.get_job('send_email')
    if job:
        job.reschedule(trigger=CronTrigger(hour=hour, minute=minute))
        logger.info(f"邮件任务已重新调度: {hour:02d}:{minute:02d}")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("定时任务调度器已停止")
