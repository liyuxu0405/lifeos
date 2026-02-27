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
    MEETING_ATTENDED = "calendar.meeting"
    TASK_COMPLETED = "task.completed"
    MESSAGE_SENT = "message.sent"
    WEBPAGE_READ = "browser.read"
    CUSTOM = "custom"

@dataclass
class ContextEvent:
    source: str
    event_type: EventType
    content: str
    timestamp: datetime
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    summary: str = ""
    entities: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    embedding: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "event_type": self.event_type.value,
            "content": self.content,
            "summary": self.summary,
            "entities": self.entities,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    dismissed: bool = False


@dataclass
class DailyBrief:
    date: str
    highlights: list = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
