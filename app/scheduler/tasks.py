from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from croniter import croniter
from datetime import datetime
from config import Config

scheduler = BackgroundScheduler()

def should_run_now(cron_expr):
    """检查是否应该现在执行"""
    now = datetime.now()
    cron = croniter(cron_expr, now)
    prev_run = cron.get_prev(datetime)
    # 如果最近一次执行在当前小时内，返回True
    return (now - prev_run).total_seconds() < 3600

def setup_scheduler(app):
    """Setup scheduler - 每小时运行一次,动态检查每个订阅是否应该执行"""
    from app.core.checker import run_check_for_subscription

    scheduler.add_job(
        func=lambda: with_app_context(app, run_all_checks),
        trigger=IntervalTrigger(hours=1),
        id="check_updates",
        name="Check subscription updates",
        replace_existing=True
    )

    if not scheduler.running:
        scheduler.start()

    return scheduler

def run_all_checks():
    """检查所有需要更新的订阅"""
    from app.database.models import Subscription
    from app.core.checker import run_check_for_subscription

    subscriptions = Subscription.query.filter_by(status='active').all()
    for sub in subscriptions:
        # 获取实际使用的cron (订阅自定义或全局默认)
        interval = sub.interval_cron or Config.DEFAULT_INTERVAL_CRON
        if should_run_now(interval):
            # 执行爬取检查
            subscription = Subscription.query.get(sub.id)
            from app.core.checker import run_check_for_subscription as check_func
            check_func(sub.id)

def with_app_context(app, func):
    """Run function with app context"""
    with app.app_context():
        return func()