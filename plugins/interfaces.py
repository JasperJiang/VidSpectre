from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from enum import Enum

class MediaType(Enum):
    MOVIE = "movie"
    TV = "tv"

class MediaItem:
    def __init__(self, media_id: str, name: str, media_type: MediaType,
                 cover_url: Optional[str] = None, detail_url: Optional[str] = None):
        self.media_id = media_id
        self.name = name
        self.media_type = media_type
        self.cover_url = cover_url
        self.detail_url = detail_url

    def to_dict(self) -> Dict[str, Any]:
        return {
            "media_id": self.media_id,
            "name": self.name,
            "media_type": self.media_type.value,
            "cover_url": self.cover_url,
            "detail_url": self.detail_url,
        }

class UpdateInfo:
    def __init__(self, media_id: str, latest_episode: str, update_time: Optional[str] = None,
                 download_links: Optional[List[Dict]] = None):
        self.media_id = media_id
        self.latest_episode = latest_episode
        self.update_time = update_time
        self.download_links = download_links or []

class DataSourcePlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name"""
        pass

    @property
    @abstractmethod
    def supported_media_types(self) -> List[MediaType]:
        """Supported media types"""
        pass

    @abstractmethod
    async def search(self, keyword: str) -> List[MediaItem]:
        """Search for media"""
        pass

    @abstractmethod
    async def get_updates(self, media_id: str) -> Optional[UpdateInfo]:
        """Get latest update info for a media"""
        pass

    @abstractmethod
    async def get_download_links(self, media_id: str) -> List[Dict]:
        """Get download links"""
        pass

class NotifierPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name"""
        pass

    @abstractmethod
    async def send(self, title: str, message: str, **kwargs) -> bool:
        """Send notification"""
        pass
