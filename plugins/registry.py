from typing import Dict, List, Optional
from plugins.interfaces import DataSourcePlugin, NotifierPlugin

class PluginRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._data_sources: Dict[str, DataSourcePlugin] = {}
            cls._instance._notifiers: Dict[str, NotifierPlugin] = {}
        return cls._instance

    def register_data_source(self, plugin: DataSourcePlugin):
        self._data_sources[plugin.name] = plugin

    def register_notifier(self, plugin: NotifierPlugin):
        self._notifiers[plugin.name] = plugin

    def get_data_source(self, name: str) -> Optional[DataSourcePlugin]:
        return self._data_sources.get(name)

    def get_notifier(self, name: str) -> Optional[NotifierPlugin]:
        return self._notifiers.get(name)

    def list_data_sources(self) -> List[str]:
        return list(self._data_sources.keys())

    def list_notifiers(self) -> List[str]:
        return list(self._notifiers.keys())

registry = PluginRegistry()
