import importlib
import pkgutil
from pathlib import Path
from typing import List
from plugins.interfaces import DataSourcePlugin, NotifierPlugin
from plugins.registry import registry

def discover_plugins(plugin_dir: Path) -> List[str]:
    """Discover available plugin directories"""
    plugins = []
    if not plugin_dir.exists():
        return plugins
    for item in plugin_dir.iterdir():
        if item.is_dir() and not item.name.startswith("_"):
            plugins.append(item.name)
    return plugins

def load_plugins(plugin_dir: Path):
    """Load all plugins from plugin directory"""
    plugin_names = discover_plugins(plugin_dir)

    for name in plugin_names:
        try:
            module = importlib.import_module(f"plugins.sources.{name}.plugin")
            if hasattr(module, "register"):
                module.register(registry)
                print(f"Loaded plugin: {name}")
        except Exception as e:
            print(f"Failed to load plugin {name}: {e}")
