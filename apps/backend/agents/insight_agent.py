"""
LifeOS Insight Agent
主动发现用户数字行为中的规律和信号
这是 LifeOS 的"哇时刻"发生器
"""
from __future__ import annotations
import json
from datetime import datetime, timedelta

import numpy as np

from core.database import Database
from core.embedding import get_embedding_service
from core.llm_client import get_llm_client
from core.models import Insight, InsightType


class InsightAgent:

    def __init__(self):
        self.db = Database.get()
        self.llm = get_llm_client()
        self.embedder = get_embedding_service()

    async def analyze(self) -> list[Insight]:
        """运行所有洞察分析器，返回新发现的洞察"""
        insights = []

        # 1. 重复想法检测（最核心的"哇时刻"）
        repeated = await self._detect_repeated_thoughts()
        insights.extend(repeated)

        # 2. 目标偏移检测
        drift = await self._detect_goal_drift()
        insights.extend(drift)

        # 3. 知识盲区检测
        gaps = await self._detect_knowledge_gaps()
        insights.extend(gaps)

        # 保存新洞察
        for insight in insights:
            self.db.save_insight(insight)

        return insights

    async def _detect_repeated_thoughts(self) -> list[Insight]:
        """
        检测用户在不同来源、不同时间表达的相似想法
        语义相似度 > 0.82 且来自不同来源/不同天 = 潜在的重复思考
        """
        events = self.db.get_recent_events(days=14, limit=100)
        if len(events) < 5:
            return []

        # 过滤有 embedding 的事件
        with_vectors = []
        for e in events:
            vec = e.get("vector")
            if vec and len(vec) > 0 and any(v != 0 for v in vec):
                with_vectors.append(e)

        if len(with_vectors) < 3:
            return []

        # 计算成对相似度，找到聚类
        clusters = []
        used = set()

        for i, e1 in enumerate(with_vectors):
            if i in used:
                continue
            cluster = [e1]
            for j, e2 in enumerate(with_vectors[i+1:], i+1):
                if j in used:
                    continue
                v1 = np.array(e1["vector"])
                v2 = np.array(e2["vector"])
                sim = float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8))

                # 相似度高 + 来自不同来源或不同天
                different_source = e1.get("source") != e2.get("source")
                different_day = e1.get("timestamp", "")[:10] != e2.get("timestamp", "")[:10]

                if sim > 0.82 and (different_source or different_day):
                    cluster.append(e2)
                    used.add(j)

            if len(cluster) >= 2:
                clusters.append(cluster)
                used.add(i)

        insights = []
        for cluster in clusters[:3]:  # 最多报告3个聚类
            titles = [e.get("title") or e.get("content", "")[:50] for e in cluster]
            sources = list(set(e.get("source", "unknown") for e in cluster))

            # 用 LLM 提炼主题
            theme = await self._extract_cluster_theme(titles)

            insight = Insight(
                insight_type=InsightType.REPEATED_THOUGHT,
                title=f"你最近多次思考同一个主题",
                description=f"在过去两周，你在 {', '.join(sources)} 中 {len(cluster)} 次提到了相似的想法：**{theme}**",
                evidence=titles[:3],
                suggested_action=f"这个主题反复出现，可能值得整理成一篇文章、一个决策文档，或者深入研究一下。",
                confidence=0.85,
            )
            insights.append(insight)

        return insights

    async def _detect_goal_drift(self) -> list[Insight]:
        """检测本周实际活动与上周计划的偏差"""
        events = self.db.get_recent_events(days=7, limit=50)
        if not events:
            return []

        calendar_events = [e for e in events if "calendar" in e.get("event_type", "")]
        code_events = [e for e in events if "code" in e.get("event_type", "")]
        note_events = [e for e in events if "note" in e.get("event_type", "")]

        # 如果有日历事件（代表计划），但代码/笔记活动很少，可能是目标漂移
        if len(calendar_events) > 3 and len(code_events) + len(note_events) < 2:
            insight = Insight(
                insight_type=InsightType.GOAL_DRIFT,
                title="本周计划与执行可能存在落差",
                description=f"你本周有 {len(calendar_events)} 个日历事项，但记录到的代码/笔记活动较少。",
                evidence=[e.get("title", e.get("content", ""))[:60] for e in calendar_events[:3]],
                suggested_action="花 5 分钟回顾一下本周目标，看看哪些需要调整或重新排期。",
                confidence=0.65,
            )
            return [insight]

        return []

    async def _detect_knowledge_gaps(self) -> list[Insight]:
        """检测用户反复在某领域提问但缺乏系统记录"""
        # 简化版：检测短内容（可能是问题）的聚类
        events = self.db.get_recent_events(days=14, limit=100)
        question_like = [
            e for e in events
            if "?" in e.get("content", "") or "如何" in e.get("content", "")
               or "怎么" in e.get("content", "") or "why" in e.get("content", "").lower()
        ]

        if len(question_like) >= 3:
            topics = [e.get("title") or e.get("content", "")[:40] for e in question_like[:5]]
            insight = Insight(
                insight_type=InsightType.KNOWLEDGE_GAP,
                title=f"你最近提出了 {len(question_like)} 个问题",
                description="发现你近期有一些反复探索的问题，可能值得系统性地整理或学习。",
                evidence=topics[:3],
                suggested_action="考虑创建一个专题笔记或学习计划，把这些问题系统地攻克。",
                confidence=0.6,
            )
            return [insight]

        return []

    async def _extract_cluster_theme(self, texts: list[str]) -> str:
        """用 LLM 提炼文本聚类的核心主题（简短）"""
        prompt = f"""以下是用户在不同时间、不同地方写下的相似内容：

{chr(10).join(f'- {t}' for t in texts[:5])}

请用 5-10 个字概括这些内容的共同主题。只输出主题词，不要解释。"""

        try:
            theme = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=30,
            )
            return theme.strip().strip("。，,.").replace("\n", "")
        except Exception:
            return "某个重要主题"
