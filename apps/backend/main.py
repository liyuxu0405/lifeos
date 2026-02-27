"""
LifeOS Backend 主入口
"""
from __future__ import annotations
import asyncio
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# --- 🎯 核心暴力加载逻辑（彻底解决读不到 Key 的问题） ---
from dotenv import load_dotenv
# 强制让程序锁定 main.py 同级目录下的 .env 文件
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

print("="*40)
print(f"🔍 [环境诊断] 正在扫描配置文件: {env_path}")
print(f"🔍 [环境诊断] 配置文件是否存在: {env_path.exists()}")
print(f"🔍 [环境诊断] DeepSeek Key 读取状态: {'✅ 成功拿到' if os.getenv('OPENAI_API_KEY') else '❌ 没拿到 (依然为空)'}")
print("="*40)
# --------------------------------------------------------

# 确保 backend 目录在 Python 路径中，解决相对导入报错
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 确保 backend 目录在 Python 路径中
sys.path.insert(0, str(Path(__file__).parent))

from api.routes import router
from core.database import Database
from core.ingestion import IngestionPipeline
from core.plugin_registry import PluginRegistry


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动和关闭时的生命周期管理"""
    print("[LifeOS] 后端启动中...")

    # 初始化数据库
    db = Database.get()
    print("[LifeOS] 数据库已就绪")

    # 初始化插件注册中心
    registry = PluginRegistry.get()
    await registry.restore_enabled_plugins()
    print(f"[LifeOS] 插件系统已就绪，{len(registry.list_plugins())} 个插件可用")

    # 启动摄入调度器
    pipeline = IngestionPipeline.get()
    pipeline.start()
    print("[LifeOS] 数据摄入调度器已启动")

    print("[LifeOS] ✅ 后端启动完成")
    yield

    # 关闭时清理
    pipeline.stop()
    print("[LifeOS] 后端已关闭")


app = FastAPI(
    title="LifeOS Backend",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS - 允许 Tauri 前端调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["tauri://localhost", "http://localhost:1420", "http://127.0.0.1:1420"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


from dotenv import load_dotenv
load_dotenv()
@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("LIFEOS_PORT", "52700"))
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=port,
        reload=False,
        log_level="info",
    )
