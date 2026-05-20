import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def check_all_reminders():
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


def start_scheduler():
    scheduler.add_job(
        check_all_reminders,
        CronTrigger(hour=0, minute=0),
        id='check_reminders',
        name='每日提醒检查',
        replace_existing=True
    )

    scheduler.start()
    logger.info("定时任务调度器已启动")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("定时任务调度器已停止")