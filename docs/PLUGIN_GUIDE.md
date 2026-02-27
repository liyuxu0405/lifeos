# LifeOS 插件开发指南

> 30 分钟内创建并运行你的第一个 LifeOS 数据源插件

## 插件是什么？

LifeOS 通过**数据源插件**从外部工具摄入你的数字活动记录。每个插件负责把一种工具的数据转化为标准的 `ContextEvent` 格式，然后 LifeOS 负责后续的 embedding、存储、检索和 AI 分析。

你可以为任何工具写插件：Notion、Linear、Spotify、Twitter、RSS、本地日记……

---

## 快速开始（5 分钟版）

### 第一步：复制模板

```bash
cp -r apps/backend/plugins/builtin/markdown_files \
      apps/backend/plugins/community/my_plugin
```

### 第二步：编辑 `plugin.py`

```python
from datetime import datetime
from core.models import ContextEvent, EventType
from core.plugin_base import SourcePlugin

class MyPlugin(SourcePlugin):
    
    @property
    def name(self) -> str:
        return "my_plugin"          # 唯一标识符，小写下划线
    
    @property
    def display_name(self) -> str:
        return "My Plugin"          # UI 显示名称
    
    @property
    def description(self) -> str:
        return "描述这个插件做什么"
    
    @property
    def icon(self) -> str:
        return "🚀"                 # 随便一个 emoji
    
    @property
    def config_schema(self) -> dict:
        return {
            "api_key": {
                "type": "string",
                "label": "API Key",
                "required": True,
                "secret": True,     # 加密存储
            }
        }
    
    async def setup(self, config: dict) -> None:
        self.api_key = config["api_key"]
        # 在这里初始化你的 API 客户端
        # 如果初始化失败，抛出异常，UI 会显示错误
    
    async def fetch_events(self, since: datetime) -> list[ContextEvent]:
        # 拉取自 since 以来的新数据
        # 框架保证 since 是上次成功同步的时间
        
        events = []
        # ... 你的 API 调用逻辑 ...
        
        events.append(ContextEvent(
            id="my_plugin_unique_id",   # 必须全局唯一且稳定（相同数据每次生成相同 ID）
            source="my_plugin",
            event_type=EventType.NOTE_CREATED,
            title="事件标题",
            content="完整内容，这部分会被向量化",
            timestamp=datetime.now(),
            tags=["标签1", "标签2"],
            entities=["人名", "项目名"],  # 帮助 AI 理解关联
            metadata={"url": "...", "extra": "任意元数据"},
        ))
        
        return events
```

### 第三步：测试

```bash
cd apps/backend
python -c "
import asyncio
from datetime import datetime, timedelta
from plugins.community.my_plugin.plugin import MyPlugin

async def test():
    p = MyPlugin()
    await p.setup({'api_key': 'test'})
    health = await p.health_check()
    print('Health:', health)
    events = await p.fetch_events(datetime.now() - timedelta(days=7))
    print(f'Got {len(events)} events')
    for e in events[:3]:
        print(f'  - {e.title}')

asyncio.run(test())
"
```

### 第四步：启动应用验证

重启 LifeOS 后，你的插件会自动出现在插件管理页面。

---

## EventType 速查表

```python
class EventType(str, Enum):
    NOTE_CREATED = "note.created"        # 新建笔记
    NOTE_UPDATED = "note.updated"        # 更新笔记
    CODE_COMMITTED = "code.committed"    # 代码提交
    CODE_PR_OPENED = "code.pr.opened"    # PR 开启
    CODE_PR_MERGED = "code.pr.merged"    # PR 合并
    CODE_ISSUE_OPENED = "code.issue.opened"
    CODE_ISSUE_CLOSED = "code.issue.closed"
    MEETING_ATTENDED = "calendar.meeting"  # 会议
    TASK_COMPLETED = "task.completed"      # 任务完成
    TASK_CREATED = "task.created"          # 任务创建
    MESSAGE_SENT = "message.sent"          # 消息发送
    WEBPAGE_READ = "browser.read"          # 网页阅读
    CHAT_MESSAGE = "chat.message"          # 聊天记录
```

如果没有合适的类型，用最接近的，或者提 Issue 建议新增。

---

## ContextEvent 字段说明

| 字段 | 类型 | 必须 | 说明 |
|------|------|------|------|
| `id` | `str` | ✅ | 全局唯一 ID。**必须稳定**——同一条数据每次生成的 ID 必须相同，否则会产生重复记录 |
| `source` | `str` | ✅ | 你的插件 `name`，如 `"my_plugin"` |
| `event_type` | `EventType` | ✅ | 事件类型，见上表 |
| `title` | `str` | 推荐 | 短标题，展示在 UI 中 |
| `content` | `str` | ✅ | 完整内容，这部分会被 embedding 向量化，质量决定检索准确率 |
| `timestamp` | `datetime` | ✅ | 事件发生时间，**不是**摄入时间 |
| `tags` | `list[str]` | 可选 | 标签，帮助过滤和分类 |
| `entities` | `list[str]` | 推荐 | 实体（人名、项目名等），帮助 AI 识别关联 |
| `metadata` | `dict` | 可选 | 任意 JSON 元数据，如 URL、ID 等，不参与向量化 |

---

## 生成稳定 ID 的最佳实践

```python
import hashlib

# 方法一：基于外部 ID
event_id = f"my_plugin_{external_id}"

# 方法二：基于内容哈希（当没有外部 ID 时）
event_id = hashlib.md5(f"{source}:{url}:{date}".encode()).hexdigest()

# ❌ 错误做法：使用时间戳或随机数
event_id = str(time.time())  # 每次不同，会产生重复记录
event_id = str(uuid.uuid4())  # 同上
```

---

## 实现实时监听（可选进阶）

对于支持 webhook 或文件系统监听的数据源，可以实现 `watch()` 方法实现实时同步：

```python
async def watch(self, callback) -> None:
    """实时监听文件变化"""
    from watchfiles import awatch
    async for changes in awatch(self.folder):
        for change_type, path in changes:
            if path.endswith(".md"):
                event = await self._parse_file(path)
                if event:
                    await callback(event)
```

---

## 提交你的插件

1. Fork 仓库
2. 在 `apps/backend/plugins/community/你的插件名/` 创建插件
3. 添加 `README.md`（包含配置说明和截图）
4. 提 PR，标题格式：`feat(plugin): add [PluginName] plugin`

**PR 合并标准：**
- 代码通过 CI
- `health_check()` 有意义的错误提示
- ID 稳定性（相同数据生成相同 ID）
- README 包含如何获取 API Key 的说明

---

## 常见问题

**Q: 插件文件放在哪里才能被发现？**
A: `apps/backend/plugins/builtin/` 或 `apps/backend/plugins/community/` 下的任意子目录，只要有 `plugin.py` 文件即可。

**Q: 如何处理 API 限流？**
A: 在 `fetch_events` 里加 `asyncio.sleep()` 控制请求速率，或使用 `tenacity` 库实现重试。

**Q: 如何安全存储 Secret？**
A: 在 `config_schema` 里把字段标记为 `"secret": True`，框架会加密存储（macOS Keychain / Windows Credential Manager）。插件收到的 `config` dict 里的 Secret 字段已经解密，直接使用即可。

**Q: 插件需要额外的 Python 依赖怎么办？**
A: 在插件目录下创建 `requirements.txt`，框架会在启用时自动安装。

---

有问题？欢迎提 Issue 或加入 Discord 社区！
