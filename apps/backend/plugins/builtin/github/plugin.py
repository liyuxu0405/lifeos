"""
LifeOS 内置插件：GitHub
同步 commits、PR、Issues、评论
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from core.models import ContextEvent, EventType
from core.plugin_base import SourcePlugin


class GitHubPlugin(SourcePlugin):

    @property
    def name(self) -> str:
        return "github"

    @property
    def display_name(self) -> str:
        return "GitHub"

    @property
    def description(self) -> str:
        return "同步你的 GitHub commits、Pull Requests 和 Issues 活动"

    @property
    def icon(self) -> str:
        return "🐙"

    @property
    def category(self) -> str:
        return "code"

    @property
    def config_schema(self) -> dict:
        return {
            "token": {
                "type": "string",
                "label": "Personal Access Token",
                "description": "在 GitHub Settings → Developer settings → Personal access tokens 生成，需要 repo 和 user 权限",
                "required": True,
                "secret": True,
                "placeholder": "ghp_xxxxxxxxxxxx",
            },
            "include_repos": {
                "type": "string",
                "label": "只同步这些仓库（可选）",
                "description": "逗号分隔的 owner/repo，留空则同步所有仓库",
                "required": False,
                "placeholder": "myname/repo1, myname/repo2",
            },
        }

    async def setup(self, config: dict) -> None:
        self.token = config.get("token", "")
        include = config.get("include_repos", "")
        self.include_repos = (
            [r.strip() for r in include.split(",") if r.strip()]
            if include else []
        )

        # 延迟导入，避免没安装时报错
        from github import Github, GithubException
        self.gh = Github(self.token)
        self.user = self.gh.get_user()

    async def health_check(self) -> dict:
        try:
            login = self.user.login
            return {"status": "ok", "message": f"已连接到账号: {login}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def fetch_events(self, since: datetime) -> list[ContextEvent]:
        events = []
        try:
            # 获取用户的所有活动
            for event in self.user.get_events():
                if event.created_at.replace(tzinfo=None) <= since:
                    break

                parsed = self._parse_github_event(event)
                if parsed:
                    events.append(parsed)

                if len(events) >= 100:
                    break
        except Exception as e:
            print(f"[GitHubPlugin] 获取事件失败: {e}")

        return events

    def _parse_github_event(self, event) -> Optional[ContextEvent]:
        try:
            repo_name = event.repo.name
            ts = event.created_at.replace(tzinfo=None)

            # 过滤仓库
            if self.include_repos and repo_name not in self.include_repos:
                return None

            event_id = f"github_{event.id}"

            if event.type == "PushEvent":
                commits = event.payload.get("commits", [])
                if not commits:
                    return None
                messages = [c.get("message", "").split("\n")[0][:80] for c in commits[:5]]
                content = f"Pushed to {repo_name}:\n" + "\n".join(f"- {m}" for m in messages)
                return ContextEvent(
                    id=event_id,
                    source="github",
                    event_type=EventType.CODE_COMMITTED,
                    title=f"[{repo_name}] {messages[0]}",
                    content=content,
                    timestamp=ts,
                    metadata={"repo": repo_name, "commits": len(commits)},
                )

            elif event.type == "PullRequestEvent":
                pr = event.payload.get("pull_request", {})
                action = event.payload.get("action", "")
                title = pr.get("title", "")
                body = (pr.get("body") or "")[:300]
                return ContextEvent(
                    id=event_id,
                    source="github",
                    event_type=(
                        EventType.CODE_PR_MERGED if action == "closed" and pr.get("merged")
                        else EventType.CODE_PR_OPENED
                    ),
                    title=f"[{repo_name}] PR {action}: {title}",
                    content=f"{title}\n\n{body}",
                    timestamp=ts,
                    metadata={"repo": repo_name, "action": action, "pr_number": pr.get("number")},
                )

            elif event.type == "IssuesEvent":
                issue = event.payload.get("issue", {})
                action = event.payload.get("action", "")
                title = issue.get("title", "")
                body = (issue.get("body") or "")[:300]
                return ContextEvent(
                    id=event_id,
                    source="github",
                    event_type=(
                        EventType.CODE_ISSUE_CLOSED if action == "closed"
                        else EventType.CODE_ISSUE_OPENED
                    ),
                    title=f"[{repo_name}] Issue {action}: {title}",
                    content=f"{title}\n\n{body}",
                    timestamp=ts,
                    metadata={"repo": repo_name, "action": action},
                )

        except Exception as e:
            print(f"[GitHubPlugin] 解析事件失败: {e}")

        return None
