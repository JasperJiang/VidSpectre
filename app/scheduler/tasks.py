from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from config import Config

scheduler = BackgroundScheduler()

def setup_scheduler(app):
    """Setup scheduler - 按全局 cron 表达式执行"""
    from app.database.models import Subscription
    from app.core.checker import _fetch_and_update_subscription

    def run_all_checks():
        subscriptions = Subscription.query.filter_by(status='active').all()
        for sub in subscriptions:
            _fetch_and_update_subscription(sub)

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

def with_app_context(app, func):
    """Run function with app context"""
    with app.app_context():
        return func()
