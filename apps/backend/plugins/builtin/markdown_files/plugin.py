"""
LifeOS 内置插件：Markdown 文件夹
支持 Obsidian Vault、任意 Markdown 笔记目录
"""
from __future__ import annotations
import hashlib
import os
from datetime import datetime
from pathlib import Path

from core.models import ContextEvent, EventType
from core.plugin_base import SourcePlugin


class MarkdownFilesPlugin(SourcePlugin):

    @property
    def name(self) -> str:
        return "markdown_files"

    @property
    def display_name(self) -> str:
        return "Markdown / Obsidian"

    @property
    def description(self) -> str:
        return "同步本地 Markdown 文件夹或 Obsidian Vault 中的笔记"

    @property
    def icon(self) -> str:
        return "📝"

    @property
    def category(self) -> str:
        return "notes"

    @property
    def config_schema(self) -> dict:
        return {
            "folder_path": {
                "type": "string",
                "label": "文件夹路径",
                "description": "Markdown 文件所在目录，如 ~/Documents/Notes 或 ~/ObsidianVault",
                "required": True,
                "secret": False,
                "placeholder": "~/Documents/Notes",
            },
            "recursive": {
                "type": "boolean",
                "label": "包含子文件夹",
                "description": "是否递归扫描子文件夹",
                "required": False,
                "default": True,
            },
        }

    async def setup(self, config: dict) -> None:
        raw_path = config.get("folder_path", "")
        self.folder = Path(raw_path).expanduser().resolve()
        self.recursive = config.get("recursive", True)

        if not self.folder.exists():
            raise ValueError(f"文件夹不存在: {self.folder}")
        if not self.folder.is_dir():
            raise ValueError(f"路径不是文件夹: {self.folder}")

    async def health_check(self) -> dict:
        md_files = list(self.folder.glob("**/*.md" if self.recursive else "*.md"))
        return {
            "status": "ok",
            "message": f"发现 {len(md_files)} 个 Markdown 文件",
        }

    async def fetch_events(self, since: datetime) -> list[ContextEvent]:
        events = []
        pattern = "**/*.md" if self.recursive else "*.md"

        for md_file in self.folder.glob(pattern):
            try:
                mtime = datetime.fromtimestamp(md_file.stat().st_mtime)
                if mtime <= since:
                    continue

                content = md_file.read_text(encoding="utf-8", errors="ignore")
                if not content.strip():
                    continue

                # 提取标题
                title = md_file.stem
                for line in content.split("\n")[:5]:
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break

                # 提取标签（Obsidian 风格 #tag）
                tags = [
                    word[1:] for word in content.split()
                    if word.startswith("#") and len(word) > 1 and word[1:].isalnum()
                ]

                # 截断内容（避免过长）
                content_preview = content[:2000].strip()

                # 生成稳定 ID（基于文件路径和内容哈希）
                event_id = hashlib.md5(
                    f"{md_file}:{content[:100]}".encode()
                ).hexdigest()

                # 判断是新建还是更新
                ctime = datetime.fromtimestamp(md_file.stat().st_ctime)
                event_type = (
                    EventType.NOTE_CREATED
                    if abs((ctime - mtime).total_seconds()) < 60
                    else EventType.NOTE_UPDATED
                )

                event = ContextEvent(
                    id=event_id,
                    source="markdown_files",
                    event_type=event_type,
                    title=title,
                    content=content_preview,
                    timestamp=mtime,
                    tags=tags[:10],
                    metadata={
                        "file_path": str(md_file),
                        "file_name": md_file.name,
                        "word_count": len(content.split()),
                    },
                )
                events.append(event)

            except Exception as e:
                print(f"[MarkdownPlugin] 读取文件失败 {md_file}: {e}")

        return events
