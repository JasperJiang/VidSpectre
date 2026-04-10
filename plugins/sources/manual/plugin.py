from typing import List, Dict

from plugins.interfaces import DataSourcePlugin, MediaType


class ManualPlugin(DataSourcePlugin):
    @property
    def name(self) -> str:
        return "manual"

    @property
    def supported_media_types(self) -> List[MediaType]:
        return [MediaType.TV]

    async def search(self, keyword: str) -> List:
        return []

    async def get_updates(self, media_id: str):
        return None

    async def get_download_links(self, media_id: str) -> List[Dict]:
        return []

    async def get_episode_links(self, media_id: str) -> Dict[str, List[Dict]]:
        return {}

    async def get_movie_links(self, media_id: str) -> Dict[str, List[Dict]]:
        return {}


def register(registry):
    registry.register_data_source(ManualPlugin())
