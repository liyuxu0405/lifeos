"""
LifeOS 数据摄入管道
负责调度插件定期拉取数据、计算 embedding 并存入数据库
"""
from __future__ import annotations
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from core.database import Database
from core.embedding import get_embedding_service
from core.models import ContextEvent
from core.plugin_registry import PluginRegistry


class IngestionPipeline:
    _instance: Optional[IngestionPipeline] = None

    def __init__(self):
        self.db = Database.get()
        self.embedder = get_embedding_service()
        self.registry = PluginRegistry.get()
        self.scheduler = AsyncIOScheduler()
        self._running = False

    @classmethod
    def get(cls) -> IngestionPipeline:
        if cls._instance is None:
            cls._instance = IngestionPipeline()
        return cls._instance

    def start(self):
        """启动摄入调度器"""
        if self._running:
            return

        # 每 15 分钟同步一次所有启用的插件
        self.scheduler.add_job(
            self._sync_all_plugins,
            IntervalTrigger(minutes=15),
            id="sync_plugins",
            replace_existing=True,
        )

        # 每天早上 8:00 触发 Daily Brief 生成
        self.scheduler.add_job(
            self._trigger_daily_brief,
            CronTrigger(hour=8, minute=0),
            id="daily_brief",
            replace_existing=True,
        )

        # 每天晚上 10:00 运行洞察分析
        self.scheduler.add_job(
            self._trigger_insights,
            CronTrigger(hour=22, minute=0),
            id="insights",
            replace_existing=True,
        )

        self.scheduler.start()
        self._running = True
        print("[Ingestion] 调度器已启动")

        # 启动时立即同步一次
        asyncio.create_task(self._sync_all_plugins())

    def stop(self):
        if self._running:
            self.scheduler.shutdown()
            self._running = False

    async def _sync_all_plugins(self):
        """同步所有启用插件的数据"""
        instances = self.registry.get_enabled_instances()
        if not instances:
            return

        print(f"[Ingestion] 开始同步 {len(instances)} 个插件...")
        tasks = [
            self._sync_plugin(name, plugin)
            for name, plugin in instances.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        total = sum(r for r in results if isinstance(r, int))
        print(f"[Ingestion] 同步完成，共摄入 {total} 条新事件")
        return total

    async def sync_plugin_now(self, plugin_name: str) -> dict:
        """手动触发单个插件同步"""
        instances = self.registry.get_enabled_instances()
        if plugin_name not in instances:
            return {"success": False, "error": "插件未启用"}
        count = await self._sync_plugin(plugin_name, instances[plugin_name])
        return {"success": True, "new_events": count}

    async def _sync_plugin(self, plugin_name: str, plugin) -> int:
        """同步单个插件"""
        try:
            last_sync = self.db.get_last_sync(plugin_name)
            since = last_sync or (datetime.now() - timedelta(days=30))

            events = await plugin.fetch_events(since)
            if not events:
                return 0

            # 过滤已存在的事件
            new_events = [e for e in events if not self.db.event_exists(e.id)]
            if not new_events:
                self.db.update_sync_cursor(plugin_name, datetime.now())
                return 0

            # 批量计算 embedding
            texts = [f"{e.title} {e.content}"[:1000] for e in new_events]
            embeddings = await self.embedder.embed_batch(texts)

            # 存入数据库
            for event, embedding in zip(new_events, embeddings):
                event.embedding = embedding
                self.db.insert_event(event)

            self.db.update_sync_cursor(plugin_name, datetime.now())
            print(f"[Ingestion] {plugin_name}: 摄入 {len(new_events)} 条新事件")
            return len(new_events)

        except Exception as e:
            print(f"[Ingestion] {plugin_name} 同步失败: {e}")
            return 0

    async def _trigger_daily_brief(self):
        """触发 Daily Brief 生成"""
        from agents.daily_brief import DailyBriefAgent
        try:
            agent = DailyBriefAgent()
            brief = await agent.generate()
            print(f"[Ingestion] Daily Brief 已生成: {brief.date}")
            # 发送系统通知（通过 FastAPI 事件）
            from api.events import notify_brief_ready
            await notify_brief_ready(brief)
        except Exception as e:
            print(f"[Ingestion] Daily Brief 生成失败: {e}")

    async def _trigger_insights(self):
        """触发洞察分析"""
        from agents.insight_agent import InsightAgent
        try:
            agent = InsightAgent()
            insights = await agent.analyze()
            print(f"[Ingestion] 发现 {len(insights)} 条新洞察")
        except Exception as e:
            print(f"[Ingestion] 洞察分析失败: {e}")
