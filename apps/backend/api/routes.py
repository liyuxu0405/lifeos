"""
LifeOS API 路由
所有前端可调用的接口，已适配 DeepSeek，修复导入报错
"""
from __future__ import annotations
import uuid
import asyncio
import os
from datetime import date, datetime
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# --- 核心组件导入：全部使用绝对导入（基于 backend 根目录） ---
from agents.daily_brief import DailyBriefAgent
from agents.insight_agent import InsightAgent
from core.database import Database
from core.ingestion import IngestionPipeline
from core.llm_client import get_llm_client
from core.plugin_registry import PluginRegistry
from core.retrieval import ContextRetriever

router = APIRouter()

# ─────────────────────────────────────────────
# 系统状态 & 健康检查
# ─────────────────────────────────────────────

@router.get("/status")
async def get_status():
    """让前端知道 DeepSeek 是否已就绪"""
    client = get_llm_client()
    return {
        "llm_provider": client.openai_model if client.openai_key else "Ollama",
        "has_openai_key": bool(client.openai_key),
        "status": "ready"
    }

@router.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}

# ─────────────────────────────────────────────
# Daily Brief (今日简报)
# ─────────────────────────────────────────────

@router.get("/brief/today")
async def get_today_brief(force: bool = False):
    agent = DailyBriefAgent()
    brief = await agent.generate(force=force)
    return brief.to_dict()

@router.get("/brief/{date_str}")
async def get_brief_by_date(date_str: str):
    db = Database.get()
    brief = db.get_daily_brief(date_str)
    if not brief:
        raise HTTPException(status_code=404, detail="该日期暂无简报")
    return brief

# ─────────────────────────────────────────────
# 上下文检索与时间轴
# ─────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    days_filter: Optional[int] = None
    source_filter: Optional[str] = None

@router.post("/search")
async def search_context(req: SearchRequest):
    retriever = ContextRetriever()
    results = await retriever.retrieve(
        req.query,
        limit=req.limit,
        days_filter=req.days_filter,
        source_filter=req.source_filter,
    )
    for r in results:
        r.pop("vector", None)
    return {"results": results, "total": len(results)}

@router.get("/timeline")
async def get_timeline(days: int = 7, limit: int = 100):
    db = Database.get()
    events = db.get_recent_events(days=days, limit=limit)
    for e in events:
        e.pop("vector", None)
    return {"events": events, "total": len(events)}

# ─────────────────────────────────────────────
# Chat (DeepSeek 驱动的对话)
# ─────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    use_context: bool = True

CHAT_SYSTEM = """你是用户的个人 AI 助理 LifeOS。
你可以访问用户的个人上下文记录（笔记、代码、日历等）。
使用中文简洁、直接地回答问题。"""

@router.post("/chat")
async def chat(req: ChatRequest):
    db = Database.get()
    llm = get_llm_client()
    retriever = ContextRetriever()

    context_str = ""
    if req.use_context:
        context_str = await retriever.get_context_for_agent(req.message, days=30)

    history = db.get_chat_history(limit=10)
    messages = [{"role": h["role"], "content": h["content"]} for h in history]

    user_content = req.message
    if context_str and context_str != "暂无相关上下文记录。":
        user_content = f"我的问题：{req.message}\n\n相关上下文：\n{context_str}"

    messages.append({"role": "user", "content": user_content})

    response = await llm.chat(
        messages=messages,
        system=CHAT_SYSTEM,
        temperature=0.7,
    )

    db.save_chat_message(str(uuid.uuid4()), "user", req.message)
    db.save_chat_message(str(uuid.uuid4()), "assistant", response)

    return {"response": response, "context_used": bool(context_str)}

# ─────────────────────────────────────────────
# Insights (洞察)
# ─────────────────────────────────────────────

@router.get("/insights")
async def get_insights():
    db = Database.get()
    return {"insights": db.get_active_insights()}

@router.post("/insights/analyze")
async def run_analysis():
    agent = InsightAgent()
    insights = await agent.analyze()
    return {"new_insights": len(insights), "insights": [i.to_dict() for i in insights]}

@router.post("/insights/{insight_id}/dismiss")
async def dismiss_insight(insight_id: str):
    db = Database.get()
    db.dismiss_insight(insight_id)
    return {"success": True}

# ─────────────────────────────────────────────
# 插件管理 (Plugins)
# ─────────────────────────────────────────────

@router.get("/plugins")
async def list_plugins():
    registry = PluginRegistry.get()
    return {"plugins": registry.list_plugins()}

class PluginEnableRequest(BaseModel):
    config: dict = {}

@router.post("/plugins/{plugin_name}/enable")
async def enable_plugin(plugin_name: str, req: PluginEnableRequest):
    registry = PluginRegistry.get()
    result = await registry.enable_plugin(plugin_name, req.config)
    if result["success"]:
        pipeline = IngestionPipeline.get()
        asyncio.create_task(pipeline.sync_plugin_now(plugin_name))
    return result

@router.post("/plugins/{plugin_name}/disable")
async def disable_plugin(plugin_name: str):
    registry = PluginRegistry.get()
    await registry.disable_plugin(plugin_name)
    return {"success": True}

@router.post("/plugins/{plugin_name}/sync")
async def sync_plugin(plugin_name: str):
    pipeline = IngestionPipeline.get()
    result = await pipeline.sync_plugin_now(plugin_name)
    return result

# ─────────────────────────────────────────────
# 设置 (Settings)
# ─────────────────────────────────────────────

class SettingsRequest(BaseModel):
    ollama_url: Optional[str] = None
    chat_model: Optional[str] = None
    embedding_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

@router.post("/settings")
async def update_settings(req: SettingsRequest):
    env_file = Path.home() / ".lifeos" / ".env"
    env_file.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    if req.ollama_url:
        os.environ["OLLAMA_URL"] = req.ollama_url
        lines.append(f"OLLAMA_URL={req.ollama_url}")
    if req.chat_model:
        os.environ["CHAT_MODEL"] = req.chat_model
        lines.append(f"CHAT_MODEL={req.chat_model}")
    if req.embedding_model:
        os.environ["EMBEDDING_MODEL"] = req.embedding_model
        lines.append(f"EMBEDDING_MODEL={req.embedding_model}")
    if req.openai_api_key:
        os.environ["OPENAI_API_KEY"] = req.openai_api_key
        lines.append(f"OPENAI_API_KEY={req.openai_api_key}")
    if req.anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = req.anthropic_api_key
        lines.append(f"ANTHROPIC_API_KEY={req.anthropic_api_key}")

    if lines:
        env_file.write_text("\n".join(lines) + "\n")

    import core.llm_client as llm_module
    llm_module._llm_client = None

    llm = get_llm_client()
    provider = await llm.get_available_provider()
    return {"success": True, "active_provider": provider}

@router.get("/settings")
async def get_settings():
    return {
        "ollama_url": os.getenv("OLLAMA_URL", "http://localhost:11434"),
        "chat_model": os.getenv("CHAT_MODEL", "deepseek-chat"),
        "embedding_model": os.getenv("EMBEDDING_MODEL", "nomic-embed-text"),
        "has_openai_key": bool(os.getenv("OPENAI_API_KEY")),
        "has_anthropic_key": bool(os.getenv("ANTHROPIC_API_KEY")),
    }