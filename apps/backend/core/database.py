"""
LifeOS 数据库层
双存储架构：LanceDB（向量）+ SQLite（元数据）
"""
from __future__ import annotations
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
import numpy as np

import lancedb
from lancedb.pydantic import LanceModel, Vector
from pydantic import Field

from core.models import ContextEvent, DailyBrief, Insight, PluginConfig

# 数据存储路径
DATA_DIR = Path.home() / ".lifeos" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

VECTOR_DB_PATH = str(DATA_DIR / "vectors")
SQLITE_PATH = str(DATA_DIR / "lifeos.db")

EMBEDDING_DIM = 768  # nomic-embed-text 维度


# ─────────────────────────────────────────────
# LanceDB Schema
# ─────────────────────────────────────────────

class EventRecord(LanceModel):
    id: str
    source: str
    event_type: str
    content: str
    title: str = ""
    summary: str = ""
    entities: str = "[]"   # JSON 序列化
    tags: str = "[]"
    timestamp: str
    metadata: str = "{}"
    vector: Vector(EMBEDDING_DIM) = Field(default_factory=lambda: [0.0] * EMBEDDING_DIM)


# ─────────────────────────────────────────────
# SQLite 初始化
# ─────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sync_cursors (
    plugin_name TEXT PRIMARY KEY,
    last_sync_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plugin_configs (
    plugin_name TEXT PRIMARY KEY,
    enabled INTEGER NOT NULL DEFAULT 0,
    config_json TEXT NOT NULL DEFAULT '{}',
    last_sync TEXT
);

CREATE TABLE IF NOT EXISTS daily_briefs (
    date TEXT PRIMARY KEY,
    data_json TEXT NOT NULL,
    generated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS insights (
    id TEXT PRIMARY KEY,
    data_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    dismissed INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS chat_history (
    id TEXT PRIMARY KEY,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL
);
"""


class Database:
    _instance: Optional[Database] = None

    def __init__(self):
        # SQLite
        self.sqlite = sqlite3.connect(SQLITE_PATH, check_same_thread=False)
        self.sqlite.row_factory = sqlite3.Row
        self.sqlite.executescript(SCHEMA_SQL)
        self.sqlite.commit()

        # LanceDB
        self.lance_db = lancedb.connect(VECTOR_DB_PATH)
        self._ensure_events_table()

    @classmethod
    def get(cls) -> Database:
        if cls._instance is None:
            cls._instance = Database()
        return cls._instance

    def _ensure_events_table(self):
        try:
            self.events_table = self.lance_db.open_table("events")
        except Exception:
            import pyarrow as pa
            schema = pa.schema([
                pa.field("id", pa.string()),
                pa.field("source", pa.string()),
                pa.field("event_type", pa.string()),
                pa.field("content", pa.string()),
                pa.field("title", pa.string()),
                pa.field("summary", pa.string()),
                pa.field("entities", pa.string()),
                pa.field("tags", pa.string()),
                pa.field("timestamp", pa.string()),
                pa.field("metadata", pa.string()),
                pa.field("vector", pa.list_(pa.float32(), EMBEDDING_DIM)),
            ])
            self.events_table = self.lance_db.create_table("events", schema=schema)

    # ─────────── Events ───────────

    def insert_event(self, event: ContextEvent):
        data = [{
            "id": event.id,
            "source": event.source,
            "event_type": event.event_type.value,
            "content": event.content,
            "title": event.title,
            "summary": event.summary,
            "entities": json.dumps(event.entities, ensure_ascii=False),
            "tags": json.dumps(event.tags, ensure_ascii=False),
            "timestamp": event.timestamp.isoformat(),
            "metadata": json.dumps(event.metadata, ensure_ascii=False),
            "vector": event.embedding if event.embedding else [0.0] * EMBEDDING_DIM,
        }]
        self.events_table.add(data)

    def event_exists(self, event_id: str) -> bool:
        try:
            result = self.events_table.search().where(f"id = '{event_id}'").limit(1).to_list()
            return len(result) > 0
        except Exception:
            return False

    def vector_search(self, query_vector: list[float], limit: int = 20) -> list[dict]:
        try:
            results = (
                self.events_table.search(query_vector)
                .limit(limit)
                .to_list()
            )
            return results
        except Exception:
            return []

    def get_recent_events(self, days: int = 7, limit: int = 100) -> list[dict]:
        from datetime import timedelta
        since = (datetime.now() - timedelta(days=days)).isoformat()
        try:
            results = (
                self.events_table.search()
                .where(f"timestamp >= '{since}'")
                .limit(limit)
                .to_list()
            )
            return sorted(results, key=lambda x: x.get("timestamp", ""), reverse=True)
        except Exception:
            return []

    def get_all_events(self, limit: int = 500) -> list[dict]:
        try:
            return self.events_table.search().limit(limit).to_list()
        except Exception:
            return []

    # ─────────── Sync Cursors ───────────

    def get_last_sync(self, plugin_name: str) -> datetime | None:
        row = self.sqlite.execute(
            "SELECT last_sync_at FROM sync_cursors WHERE plugin_name = ?", (plugin_name,)
        ).fetchone()
        if row:
            return datetime.fromisoformat(row["last_sync_at"])
        return None

    def update_sync_cursor(self, plugin_name: str, ts: datetime):
        self.sqlite.execute(
            "INSERT OR REPLACE INTO sync_cursors (plugin_name, last_sync_at) VALUES (?, ?)",
            (plugin_name, ts.isoformat())
        )
        self.sqlite.commit()

    # ─────────── Plugin Config ───────────

    def get_plugin_config(self, plugin_name: str) -> dict | None:
        row = self.sqlite.execute(
            "SELECT * FROM plugin_configs WHERE plugin_name = ?", (plugin_name,)
        ).fetchone()
        if row:
            return {
                "plugin_name": row["plugin_name"],
                "enabled": bool(row["enabled"]),
                "config": json.loads(row["config_json"]),
                "last_sync": row["last_sync"],
            }
        return None

    def save_plugin_config(self, plugin_name: str, enabled: bool, config: dict):
        self.sqlite.execute(
            """INSERT OR REPLACE INTO plugin_configs (plugin_name, enabled, config_json)
               VALUES (?, ?, ?)""",
            (plugin_name, int(enabled), json.dumps(config, ensure_ascii=False))
        )
        self.sqlite.commit()

    def get_all_plugin_configs(self) -> list[dict]:
        rows = self.sqlite.execute("SELECT * FROM plugin_configs").fetchall()
        return [
            {
                "plugin_name": r["plugin_name"],
                "enabled": bool(r["enabled"]),
                "config": json.loads(r["config_json"]),
                "last_sync": r["last_sync"],
            }
            for r in rows
        ]

    # ─────────── Daily Briefs ───────────

    def save_daily_brief(self, brief: DailyBrief):
        self.sqlite.execute(
            "INSERT OR REPLACE INTO daily_briefs (date, data_json, generated_at) VALUES (?, ?, ?)",
            (brief.date, json.dumps(brief.to_dict(), ensure_ascii=False), brief.generated_at.isoformat())
        )
        self.sqlite.commit()

    def get_daily_brief(self, date: str) -> dict | None:
        row = self.sqlite.execute(
            "SELECT data_json FROM daily_briefs WHERE date = ?", (date,)
        ).fetchone()
        return json.loads(row["data_json"]) if row else None

    # ─────────── Insights ───────────

    def save_insight(self, insight: Insight):
        self.sqlite.execute(
            "INSERT OR REPLACE INTO insights (id, data_json, created_at, dismissed) VALUES (?, ?, ?, ?)",
            (insight.id, json.dumps(insight.to_dict(), ensure_ascii=False),
             insight.created_at.isoformat(), int(insight.dismissed))
        )
        self.sqlite.commit()

    def get_active_insights(self) -> list[dict]:
        rows = self.sqlite.execute(
            "SELECT data_json FROM insights WHERE dismissed = 0 ORDER BY created_at DESC"
        ).fetchall()
        return [json.loads(r["data_json"]) for r in rows]

    def dismiss_insight(self, insight_id: str):
        self.sqlite.execute("UPDATE insights SET dismissed = 1 WHERE id = ?", (insight_id,))
        self.sqlite.commit()

    # ─────────── Chat History ───────────

    def save_chat_message(self, msg_id: str, role: str, content: str):
        self.sqlite.execute(
            "INSERT INTO chat_history (id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (msg_id, role, content, datetime.now().isoformat())
        )
        self.sqlite.commit()

    def get_chat_history(self, limit: int = 50) -> list[dict]:
        rows = self.sqlite.execute(
            "SELECT * FROM chat_history ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in reversed(rows)]
