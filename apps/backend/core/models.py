"""
LifeOS Core Data Models
统一的数据模型，所有插件的共同语言
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

class EventType(str, Enum):
    NOTE_CREATED = "note.created"
    NOTE_UPDATED = "note.updated"
    CODE_COMMITTED = "code.committed"
    CODE_PR_OPENED = "code.pr.opened"
    CODE_PR_MERGED = "code.pr.merged"
    CODE_ISSUE_CREATED = "code.issue.created"
    CODE_ISSUE_OPENED = "code.issue.opened"
    CODE_ISSUE_CLOSED = "code.issue.closed"
    MEETING_ATTENDED = "calendar.meeting"
    TASK_COMPLETED = "task.completed"
    TASK_CREATED = "task.created"
    MESSAGE_SENT = "message.sent"
    WEBPAGE_READ = "browser.read"
    CHAT_MESSAGE = "chat.message"
    CUSTOM = "custom"

@dataclass
class ContextEvent:
    source: str
    event_type: EventType
    content: str
    timestamp: datetime
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    summary: str = ""
    entities: list = field(default_factory=list)
    tags: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    embedding: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "event_type": self.event_type.value,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "entities": self.entities,
            "tags": self.tags,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

class InsightType(str, Enum):
    REPEATED_THOUGHT = "repeated_thought"
    GOAL_DRIFT = "goal_drift"
    KNOWLEDGE_GAP = "knowledge_gap"
    OVERDUE_TASK = "overdue_task"
    RELATIONSHIP_SIGNAL = "relationship_signal"

@dataclass
class Insight:
    insight_type: InsightType
    title: str
    description: str
    evidence: list
    suggested_action: str
    confidence: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    dismissed: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "insight_type": self.insight_type.value if isinstance(self.insight_type, Enum) else self.insight_type,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "suggested_action": self.suggested_action,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "dismissed": self.dismissed,
        }

@dataclass
class DailyBrief:
    date: str
    greeting: str = ""
    highlights: list = field(default_factory=list)
    patterns: list = field(default_factory=list)
    priorities: list = field(default_factory=list)
    reflection: str = ""
    raw_markdown: str = ""
    generated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "greeting": self.greeting,
            "highlights": self.highlights,
            "patterns": self.patterns,
            "priorities": self.priorities,
            "reflection": self.reflection,
            "raw_markdown": self.raw_markdown,
            "generated_at": self.generated_at.isoformat(),
        }

@dataclass
class PluginConfig:
    plugin_name: str
    enabled: bool
    config: dict
    last_sync: str = None