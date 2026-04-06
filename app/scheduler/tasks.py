from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from config import Config

scheduler = BackgroundScheduler()

# 保持 app 引用以便后续更新
_scheduler_app = None

def setup_scheduler(app):
    """Setup scheduler - 按全局 cron 表达式执行"""
    global _scheduler_app
    _scheduler_app = app

    def run_all_checks():
        # 检查定时任务开关
        if not getattr(Config, 'SCHEDULER_ENABLED', True):
            return

        from app.core.checker import _run_all_subscriptions
        _run_all_subscriptions()

    # 解析全局 cron 表达式
    cron_expr = Config.DEFAULT_INTERVAL_CRON
    cron_parts = cron_expr.split()
    if len(cron_parts) == 5:
        trigger = CronTrigger(
            minute=cron_parts[0],
            hour=cron_parts[1],
            day=cron_parts[2],
            month=cron_parts[3],
            day_of_week=cron_parts[4]
        )
        scheduler.add_job(
            func=lambda: with_app_context(app, run_all_checks),
            trigger=trigger,
            id="check_updates",
            name="Check subscription updates",
            replace_existing=True
        )

    if not scheduler.running:
        scheduler.start()

    return scheduler

def reschedule_job():
    """重新调度任务，使用当前的 Config.DEFAULT_INTERVAL_CRON"""
    if not _scheduler_app:
        return

    def run_all_checks():
        # 检查定时任务开关
        if not getattr(Config, 'SCHEDULER_ENABLED', True):
            return

        from app.core.checker import _run_all_subscriptions
        _run_all_subscriptions()

    cron_expr = Config.DEFAULT_INTERVAL_CRON
    cron_parts = cron_expr.split()
    if len(cron_parts) == 5:
        trigger = CronTrigger(
            minute=cron_parts[0],
            hour=cron_parts[1],
            day=cron_parts[2],
            month=cron_parts[3],
            day_of_week=cron_parts[4]
        )
        scheduler.add_job(
            func=lambda: with_app_context(_scheduler_app, run_all_checks),
            trigger=trigger,
            id="check_updates",
            name="Check subscription updates",
            replace_existing=True
        )

def with_app_context(app, func):
    """Run function with app context"""
    with app.app_context():
        return func()
