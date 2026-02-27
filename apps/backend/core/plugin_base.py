"""
LifeOS 插件基类
贡献者只需继承此类并实现三个方法即可创建新数据源插件
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from typing import AsyncIterator, Callable
from core.models import ContextEvent


class SourcePlugin(ABC):
    """
    所有数据源插件的基类。
    
    创建新插件示例：
    
        class MyPlugin(SourcePlugin):
            @property
            def name(self) -> str:
                return "my_source"
            
            @property  
            def display_name(self) -> str:
                return "My Data Source"
            
            @property
            def description(self) -> str:
                return "Connects to My Data Source"
            
            @property
            def config_schema(self) -> dict:
                return {
                    "api_key": {"type": "string", "label": "API Key", "secret": True},
                    "folder": {"type": "string", "label": "Folder Path"}
                }
            
            async def setup(self, config: dict) -> None:
                self.api_key = config["api_key"]
            
            async def fetch_events(self, since: datetime) -> list[ContextEvent]:
                # 返回自 since 以来的新事件
                return [...]
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """插件唯一标识符，小写下划线，如 'markdown_files'"""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """在 UI 中显示的名称，如 'Markdown Files'"""

    @property
    @abstractmethod
    def description(self) -> str:
        """插件功能描述"""

    @property
    def icon(self) -> str:
        """插件图标 emoji，默认📦"""
        return "📦"

    @property
    def category(self) -> str:
        """插件分类：notes / code / calendar / communication / browser"""
        return "other"

    @property
    def config_schema(self) -> dict:
        """
        插件配置项 JSON Schema。
        每个字段包含：type, label, description, required, secret(是否加密存储)
        
        示例：
        {
            "token": {
                "type": "string",
                "label": "Personal Access Token",
                "description": "从设置页面生成",
                "required": True,
                "secret": True
            },
            "folder_path": {
                "type": "string", 
                "label": "Vault 路径",
                "required": True,
                "secret": False
            }
        }
        """
        return {}

    @abstractmethod
    async def setup(self, config: dict) -> None:
        """
        初始化插件连接。
        config 包含用户填写的配置项（secret 字段已解密）。
        如果初始化失败，抛出 Exception，框架会向用户展示错误。
        """

    @abstractmethod
    async def fetch_events(self, since: datetime) -> list[ContextEvent]:
        """
        增量拉取自 since 以来的新事件。
        框架负责记录上次同步时间，插件只需实现增量逻辑。
        返回空列表表示无新事件。
        """

    async def watch(self, callback: Callable[[ContextEvent], None]) -> None:
        """
        可选：实现实时监听（如文件系统 inotify）。
        默认不实现，框架会定期轮询 fetch_events。
        callback 在发现新事件时调用。
        """

    async def health_check(self) -> dict:
        """
        可选：健康检查，返回 {"status": "ok"} 或 {"status": "error", "message": "..."}
        """
        return {"status": "ok"}

    async def teardown(self) -> None:
        """可选：清理资源（关闭连接等）"""
