import asyncio
from typing import List, Optional, Dict
from plugins.interfaces import DataSourcePlugin, MediaType, MediaItem, UpdateInfo
from plugins.sources.btbtla.parser import BtbtlaParser

class BtbtlaPlugin(DataSourcePlugin):
    def __init__(self):
        self.parser = BtbtlaParser()

    @property
    def name(self) -> str:
        return "btbtla"

    @property
    def supported_media_types(self) -> List[MediaType]:
        return [MediaType.MOVIE, MediaType.TV]

    async def search(self, keyword: str) -> List[MediaItem]:
        """Search for media"""
        # Run sync parser in executor to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.parser.search, keyword)

    async def get_updates(self, media_id: str) -> Optional[UpdateInfo]:
        """Get latest update info"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.parser.get_updates, media_id)

    async def get_download_links(self, media_id: str) -> List[Dict]:
        """Get download links"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.parser.get_download_links, media_id)

    async def get_episode_links(self, media_id: str) -> Dict[str, List[Dict]]:
        """Get episode links grouped by episode number"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.parser.get_episode_links, media_id)

def register(registry):
    """Register plugin to registry"""
    registry.register_data_source(BtbtlaPlugin())
