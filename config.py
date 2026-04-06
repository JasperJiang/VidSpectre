import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(exist_ok=True)

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{STORAGE_DIR / 'vidspectre.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Scheduler settings
    SCHEDULER_ENABLED = True  # 定时任务开关，默认开启
    SCHEDULER_INTERVAL_HOURS = 6
    DEFAULT_INTERVAL_CRON = "0 */6 * * *"  # 默认每6小时
    FETCH_RETRY_COUNT = int(os.environ.get("FETCH_RETRY_COUNT", "3"))  # 默认重试3次

    # Plugin settings
    PLUGIN_DIR = BASE_DIR / "plugins" / "sources"
    PLUGIN_DIR.mkdir(parents=True, exist_ok=True)