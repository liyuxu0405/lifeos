"""
LifeOS 插件注册中心
自动发现、注册和管理所有数据源插件
"""
from __future__ import annotations
import importlib
import importlib.util
import inspect
import json
import sys
from pathlib import Path
from typing import Optional

from core.plugin_base import SourcePlugin
from core.database import Database


PLUGINS_DIR = Path(__file__).parent.parent / "plugins"


class PluginRegistry:
    _instance: Optional[PluginRegistry] = None

    def __init__(self):
        self.db = Database.get()
        self._plugins: dict[str, type[SourcePlugin]] = {}
        self._instances: dict[str, SourcePlugin] = {}
        self._scan_plugins()

    @classmethod
    def get(cls) -> PluginRegistry:
        if cls._instance is None:
            cls._instance = PluginRegistry()
        return cls._instance

    def _scan_plugins(self):
        """扫描 plugins/ 目录，自动发现所有插件"""
        for plugin_dir in [PLUGINS_DIR / "builtin", PLUGINS_DIR / "community"]:
            if not plugin_dir.exists():
                continue
            for item in plugin_dir.iterdir():
                if item.is_dir() and (item / "plugin.py").exists():
                    self._load_plugin(item / "plugin.py")

    def _load_plugin(self, plugin_path: Path):
        """动态加载插件模块"""
        try:
            module_name = f"plugin_{plugin_path.parent.name}"
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # 找到继承 SourcePlugin 的类
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, SourcePlugin)
                        and obj is not SourcePlugin
                        and not inspect.isabstract(obj)):
                    instance_preview = obj.__new__(obj)
                    plugin_name = instance_preview.name
                    self._plugins[plugin_name] = obj
                    print(f"[Registry] 已加载插件: {plugin_name}")
        except Exception as e:
            print(f"[Registry] 加载插件失败 {plugin_path}: {e}")

    def list_plugins(self) -> list[dict]:
        """列出所有可用插件及其状态"""
        result = []
        configs = {c["plugin_name"]: c for c in self.db.get_all_plugin_configs()}

        for name, cls in self._plugins.items():
            preview = cls.__new__(cls)
            config_data = configs.get(name, {})
            result.append({
                "name": name,
                "display_name": preview.display_name,
                "description": preview.description,
                "icon": preview.icon,
                "category": preview.category,
                "config_schema": preview.config_schema,
                "enabled": config_data.get("enabled", False),
                "last_sync": config_data.get("last_sync"),
            })

        return sorted(result, key=lambda x: x["display_name"])

    async def enable_plugin(self, plugin_name: str, config: dict) -> dict:
        """启用并初始化插件"""
        if plugin_name not in self._plugins:
            return {"success": False, "error": f"插件 {plugin_name} 不存在"}

        cls = self._plugins[plugin_name]
        instance = cls()

        try:
            await instance.setup(config)
            health = await instance.health_check()
            if health.get("status") != "ok":
                return {"success": False, "error": health.get("message", "健康检查失败")}

            self._instances[plugin_name] = instance
            self.db.save_plugin_config(plugin_name, True, config)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def disable_plugin(self, plugin_name: str):
        """禁用插件"""
        if plugin_name in self._instances:
            await self._instances[plugin_name].teardown()
            del self._instances[plugin_name]
        self.db.save_plugin_config(plugin_name, False, {})

    def get_enabled_instances(self) -> dict[str, SourcePlugin]:
        """返回所有已启用的插件实例"""
        return dict(self._instances)

    async def restore_enabled_plugins(self):
        """应用启动时恢复上次启用的插件"""
        for config in self.db.get_all_plugin_configs():
            if config["enabled"] and config["plugin_name"] in self._plugins:
                result = await self.enable_plugin(
                    config["plugin_name"], config["config"]
                )
                if result["success"]:
                    print(f"[Registry] 已恢复插件: {config['plugin_name']}")
                else:
                    print(f"[Registry] 恢复插件失败 {config['plugin_name']}: {result['error']}")
