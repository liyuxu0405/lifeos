"""
LifeOS 事件广播
用于向前端推送系统通知
"""
from __future__ import annotations
from core.models import DailyBrief


async def notify_brief_ready(brief: DailyBrief):
    """通知前端 Daily Brief 已就绪（通过系统通知）"""
    # 这里可以通过 WebSocket 或者系统通知推送
    # Tauri 层会监听这个事件并触发系统通知
    print(f"[Events] Daily Brief 已就绪: {brief.date}")
    # TODO: 实现 WebSocket 广播
