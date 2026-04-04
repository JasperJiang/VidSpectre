"""Task manager for tracking fetch-all task status"""
import uuid
from datetime import datetime
from typing import Optional

class FetchTask:
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.status = "running"  # running, completed, failed
        self.total = 0
        self.completed = 0
        self.failed = 0
        self.started_at = datetime.utcnow()
        self.finished_at: Optional[datetime] = None
        self.results = []  # list of {subscription_id, name, status, latest_episode, error}

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "status": self.status,
            "total": self.total,
            "completed": self.completed,
            "failed": self.failed,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "results": self.results
        }

class TaskManager:
    _tasks: dict[str, FetchTask] = {}

    @classmethod
    def create_task(cls) -> str:
        task_id = datetime.utcnow().strftime("%Y%m%d-") + uuid.uuid4().hex[:8]
        cls._tasks[task_id] = FetchTask(task_id)
        return task_id

    @classmethod
    def get_task(cls, task_id: str) -> Optional[FetchTask]:
        return cls._tasks.get(task_id)

    @classmethod
    def delete_task(cls, task_id: str):
        if task_id in cls._tasks:
            del cls._tasks[task_id]
