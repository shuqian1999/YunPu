import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def check_all_reminders():
    """检查所有用户的提醒并生成通知"""
    from app.core.database import SessionLocal
    from app.models.user import User
    from app.services.reminder_service import ReminderService

    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            try:
                service = ReminderService(db)
                notifications = service.check_reminders(user.id)
                if notifications:
                    logger.info(f"为用户 {user.id} 生成了 {len(notifications)} 条通知")
            except Exception as e:
                logger.error(f"检查用户 {user.id} 的提醒时出错: {e}")
    finally:
        db.close()


def start_scheduler():
    """启动定时任务调度器"""
    # 每天凌晨0点执行提醒检查
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
    """停止定时任务调度器"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("定时任务调度器已停止")
