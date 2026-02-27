"""
LifeOS 内置插件：Google Calendar
同步会议记录和日历事件
"""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from core.models import ContextEvent, EventType
from core.plugin_base import SourcePlugin

CREDENTIALS_DIR = Path.home() / ".lifeos" / "credentials"
CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
TOKEN_FILE = CREDENTIALS_DIR / "google_calendar_token.json"

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


class GoogleCalendarPlugin(SourcePlugin):

    @property
    def name(self) -> str:
        return "google_calendar"

    @property
    def display_name(self) -> str:
        return "Google Calendar"

    @property
    def description(self) -> str:
        return "同步 Google Calendar 中的会议和事件记录"

    @property
    def icon(self) -> str:
        return "📅"

    @property
    def category(self) -> str:
        return "calendar"

    @property
    def config_schema(self) -> dict:
        return {
            "credentials_json": {
                "type": "textarea",
                "label": "OAuth 凭证 JSON",
                "description": (
                    "1. 前往 Google Cloud Console → APIs & Services → Credentials\n"
                    "2. 创建 OAuth 2.0 Client ID（桌面应用类型）\n"
                    "3. 下载 JSON 并粘贴到这里"
                ),
                "required": True,
                "secret": True,
            },
            "calendar_id": {
                "type": "string",
                "label": "日历 ID（可选）",
                "description": "留空使用主日历，或填写具体日历 ID",
                "required": False,
                "default": "primary",
            },
        }

    async def setup(self, config: dict) -> None:
        creds_json = config.get("credentials_json", "")
        self.calendar_id = config.get("calendar_id", "primary")

        # 保存凭证
        creds_file = CREDENTIALS_DIR / "google_credentials.json"
        creds_file.write_text(creds_json)

        self.service = self._build_service(creds_file)

    def _build_service(self, creds_file: Path):
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        import googleapiclient.discovery as discovery

        creds = None
        if TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                from google.auth.transport.requests import Request
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(creds_file), SCOPES)
                creds = flow.run_local_server(port=0)
            TOKEN_FILE.write_text(creds.to_json())

        return discovery.build("calendar", "v3", credentials=creds)

    async def health_check(self) -> dict:
        try:
            result = self.service.calendarList().list(maxResults=1).execute()
            return {"status": "ok", "message": "Google Calendar 连接正常"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def fetch_events(self, since: datetime) -> list[ContextEvent]:
        events = []
        try:
            since_str = since.replace(tzinfo=timezone.utc).isoformat()
            now_str = datetime.now(timezone.utc).isoformat()

            result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=since_str,
                timeMax=now_str,
                maxResults=100,
                singleEvents=True,
                orderBy="startTime",
            ).execute()

            for item in result.get("items", []):
                parsed = self._parse_calendar_event(item)
                if parsed:
                    events.append(parsed)

        except Exception as e:
            print(f"[GoogleCalendarPlugin] 获取事件失败: {e}")

        return events

    def _parse_calendar_event(self, item: dict) -> ContextEvent | None:
        try:
            title = item.get("summary", "（无标题）")
            description = item.get("description", "")[:500]
            attendees = [
                a.get("email", "") for a in item.get("attendees", [])
                if not a.get("self", False)
            ]

            start = item.get("start", {})
            start_str = start.get("dateTime") or start.get("date", "")
            if not start_str:
                return None

            try:
                if "T" in start_str:
                    ts = datetime.fromisoformat(start_str.replace("Z", "+00:00")).replace(tzinfo=None)
                else:
                    ts = datetime.strptime(start_str, "%Y-%m-%d")
            except Exception:
                return None

            content_parts = [f"会议：{title}"]
            if attendees:
                content_parts.append(f"参与者：{', '.join(attendees[:5])}")
            if description:
                content_parts.append(f"描述：{description}")

            return ContextEvent(
                id=f"gcal_{item['id']}",
                source="google_calendar",
                event_type=EventType.MEETING_ATTENDED,
                title=title,
                content="\n".join(content_parts),
                timestamp=ts,
                entities=attendees[:10],
                metadata={
                    "attendees": attendees,
                    "location": item.get("location", ""),
                    "html_link": item.get("htmlLink", ""),
                },
            )
        except Exception as e:
            print(f"[GoogleCalendarPlugin] 解析事件失败: {e}")
            return None
