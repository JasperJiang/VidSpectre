from datetime import datetime
from app import db

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    media_type = db.Column(db.String(20), nullable=False)  # 'movie' or 'tv'
    media_name = db.Column(db.String(200), nullable=False)
    media_id = db.Column(db.String(100))  # Source-specific ID
    source_plugin = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default="active")  # active, paused
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Latest update info
    latest_episode = db.Column(db.String(50))
    latest_update_time = db.Column(db.DateTime)

    # User's watching progress (for TV series)
    current_episode = db.Column(db.String(50), nullable=True)  # e.g., "S01E05" or "5"

    # Search keywords for filtering downloads
    search_keywords = db.Column(db.String(500), nullable=True)  # e.g., "2160p, HDR, 无删减"

    # 爬取周期 (cron表达式, None表示使用全局默认值)
    interval_cron = db.Column(db.String(50))

    def to_dict(self):
        return {
            "id": self.id,
            "media_type": self.media_type,
            "media_name": self.media_name,
            "media_id": self.media_id,
            "source_plugin": self.source_plugin,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "latest_episode": self.latest_episode,
            "latest_update_time": self.latest_update_time.isoformat() if self.latest_update_time else None,
            "current_episode": self.current_episode,
            "search_keywords": self.search_keywords,
            "interval_cron": self.interval_cron,
        }