"""
LifeOS 混合检索引擎
向量语义检索 + 时间衰减重排 + 实体图增强
"""
from __future__ import annotations
import math
from datetime import datetime
from typing import Optional

from core.database import Database
from core.embedding import get_embedding_service
from core.models import ContextEvent, EventType


class ContextRetriever:

    def __init__(self):
        self.db = Database.get()
        self.embedder = get_embedding_service()

    async def retrieve(
        self,
        query: str,
        limit: int = 10,
        days_filter: Optional[int] = None,
        source_filter: Optional[str] = None,
    ) -> list[dict]:
        """
        混合检索主入口
        1. 向量语义检索（相关性）
        2. 时间衰减重排（近期优先）
        3. 去重合并
        """
        if not query.strip():
            return self.db.get_recent_events(days=7, limit=limit)

        # Step 1: 向量检索
        query_embedding = await self.embedder.embed(query)
        raw_results = self.db.vector_search(query_embedding, limit=min(50, limit * 5))

        if not raw_results:
            return self.db.get_recent_events(days=days_filter or 7, limit=limit)

        # Step 2: 时间衰减重排
        scored = []
        now = datetime.now()
        for r in raw_results:
            semantic_score = 1.0 - (r.get("_distance", 0.5) or 0.5)
            try:
                ts = datetime.fromisoformat(r.get("timestamp", now.isoformat()))
                days_ago = max(0, (now - ts).days)
                # 指数衰减：λ=0.05，7天后权重≈70%，30天后≈22%
                time_weight = math.exp(-0.05 * days_ago)
            except Exception:
                time_weight = 0.5

            final_score = semantic_score * 0.7 + time_weight * 0.3
            scored.append({**r, "_score": final_score})

        # Step 3: 过滤 + 排序
        if days_filter:
            from datetime import timedelta
            cutoff = (now - timedelta(days=days_filter)).isoformat()
            scored = [r for r in scored if r.get("timestamp", "") >= cutoff]

        if source_filter:
            scored = [r for r in scored if r.get("source") == source_filter]

        scored.sort(key=lambda x: x["_score"], reverse=True)

        # 清理内部字段，格式化返回
        results = []
        for r in scored[:limit]:
            r.pop("_distance", None)
            r.pop("vector", None)
            results.append(r)

        return results

    async def get_context_for_agent(self, topic: str, days: int = 7) -> str:
        """
        为 Agent 提供格式化的上下文字符串
        """
        events = await self.retrieve(topic, limit=15, days_filter=days)
        if not events:
            return "暂无相关上下文记录。"

        lines = []
        for e in events:
            ts = e.get("timestamp", "")[:10]
            source = e.get("source", "unknown")
            title = e.get("title") or e.get("content", "")[:50]
            lines.append(f"- [{ts}][{source}] {title}")

        return "\n".join(lines)

    def get_recent_events_formatted(self, days: int = 7) -> str:
        """获取最近事件的文本摘要，用于 Daily Brief"""
        events = self.db.get_recent_events(days=days, limit=50)
        if not events:
            return "最近没有记录到任何活动。"

        import json
        from collections import defaultdict
        by_source = defaultdict(list)
        for e in events:
            source = e.get("source", "unknown")
            title = e.get("title") or e.get("content", "")[:80]
            ts = e.get("timestamp", "")[:10]
            by_source[source].append(f"[{ts}] {title}")

        lines = []
        for source, items in by_source.items():
            lines.append(f"\n**{source}** ({len(items)} 条):")
            lines.extend([f"  {item}" for item in items[:5]])
            if len(items) > 5:
                lines.append(f"  ...还有 {len(items)-5} 条")

        return "\n".join(lines)
