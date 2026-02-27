"""
LifeOS Daily Brief Agent
每天早上生成个性化的上下文摘要简报
"""
from __future__ import annotations
from datetime import datetime, date

from core.database import Database
from core.llm_client import get_llm_client
from core.models import DailyBrief
from core.retrieval import ContextRetriever


BRIEF_SYSTEM_PROMPT = """你是用户的个人 AI 助理，负责生成每日情境简报。
你掌握了用户最近的所有活动记录（笔记、代码提交、日历、任务等）。

要求：
- 语气温暖、简洁，像一位了解你的智慧朋友
- 发现跨数据源的关联和模式，这是最有价值的部分
- 对未完成或被遗忘的事项给予温和提醒
- 今日建议要具体可执行，不超过 3 条
- 中文回复，使用 Markdown 格式"""

BRIEF_USER_PROMPT = """今天是 {date}，星期{weekday}。

以下是我最近 7 天的活动记录：
{context}

请生成今日简报，包含以下部分：
1. **早安打招呼**（一句温暖的开场，结合今天日期或近期主题）
2. **近期亮点**（3-5条，你认为最值得关注的活动）
3. **发现的规律**（你注意到的跨来源模式，例如"你这周三次提到XXX"）
4. **今日建议**（基于上下文的 2-3 条具体建议）
5. **一句话总结**（本周主旋律）

请严格按照以上结构输出 Markdown。"""

WEEKDAYS = ["一", "二", "三", "四", "五", "六", "日"]


class DailyBriefAgent:

    def __init__(self):
        self.db = Database.get()
        self.llm = get_llm_client()
        self.retriever = ContextRetriever()

    async def generate(self, force: bool = False) -> DailyBrief:
        """生成今日简报，已存在则直接返回（除非 force=True）"""
        today = date.today().isoformat()

        if not force:
            existing = self.db.get_daily_brief(today)
            if existing:
                return self._from_dict(existing)

        # 获取上下文
        context = self.retriever.get_recent_events_formatted(days=7)

        weekday = WEEKDAYS[datetime.now().weekday()]
        prompt = BRIEF_USER_PROMPT.format(
            date=today,
            weekday=weekday,
            context=context if context else "暂无记录，这是你使用 LifeOS 的第一天！"
        )

        raw_response = await self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            system=BRIEF_SYSTEM_PROMPT,
            temperature=0.8,
            max_tokens=1500,
        )

        brief = self._parse_response(raw_response, today)
        self.db.save_daily_brief(brief)
        return brief

    def _parse_response(self, raw: str, today: str) -> DailyBrief:
        """解析 LLM 响应，提取结构化数据"""
        lines = raw.strip().split("\n")

        highlights = []
        patterns = []
        priorities = []
        greeting = ""
        reflection = ""

        current_section = None
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            if "早安" in stripped or "**早安" in stripped:
                current_section = "greeting"
            elif "亮点" in stripped:
                current_section = "highlights"
            elif "规律" in stripped or "发现" in stripped:
                current_section = "patterns"
            elif "建议" in stripped or "今日" in stripped:
                current_section = "priorities"
            elif "总结" in stripped or "主旋律" in stripped:
                current_section = "reflection"
            elif stripped.startswith(("- ", "* ", "• ")) or (stripped[0].isdigit() and stripped[1] in ".、"):
                content = stripped.lstrip("-*•0123456789.、 ")
                if current_section == "highlights":
                    highlights.append(content)
                elif current_section == "patterns":
                    patterns.append(content)
                elif current_section == "priorities":
                    priorities.append(content)
            elif current_section == "greeting" and stripped and not stripped.startswith("#"):
                greeting = stripped
            elif current_section == "reflection" and stripped and not stripped.startswith("#"):
                reflection = stripped

        # 降级：如果解析失败，把整个响应当作原始内容
        if not greeting:
            greeting = f"早上好！今天是 {today}。"

        return DailyBrief(
            date=today,
            greeting=greeting,
            highlights=highlights or ["暂无亮点记录"],
            patterns=patterns or [],
            priorities=priorities or ["开始使用 LifeOS 记录你的第一天"],
            reflection=reflection or "",
            raw_markdown=raw,
        )

    def _from_dict(self, data: dict) -> DailyBrief:
        return DailyBrief(
            date=data["date"],
            greeting=data["greeting"],
            highlights=data["highlights"],
            patterns=data["patterns"],
            priorities=data["priorities"],
            reflection=data["reflection"],
            raw_markdown=data["raw_markdown"],
            generated_at=datetime.fromisoformat(data["generated_at"]),
        )
