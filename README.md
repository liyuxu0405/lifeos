<div align="center">
  <h1>🧠 LifeOS</h1>
  <p>
    <a href="README.md">English</a> | <a href="SETUP.md">简体中文</a>
  </p>
    An open-source personal context OS that actively learns your patterns,<br/>
    connects your tools, and surfaces insights you didn't know you needed.
  </p>

  <p>
    <img src="https://img.shields.io/github/stars/lifeos-app/lifeos?style=flat-square&color=purple" alt="Stars" />
    <img src="https://img.shields.io/github/license/lifeos-app/lifeos?style=flat-square" alt="License" />
    <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-blue?style=flat-square" alt="Platform" />
    <img src="https://img.shields.io/badge/privacy-local%20first-green?style=flat-square" alt="Privacy" />
  </p>
</div>

---

## What is LifeOS?

Most "second brain" tools are just prettier file folders. LifeOS is different.

LifeOS is a **local-first personal context operating system**. It silently ingests your digital activity — commits, notes, meetings, tasks — builds a semantic understanding of your life, and proactively surfaces patterns you'd never notice yourself.

The magic moment: *"You mentioned this idea three times across different tools this week. Want to write it up?"*

**It runs 100% locally. Your data never leaves your machine.**

---

## ✨ Features

- **📰 Daily Brief** — Every morning at 8am, a personalized AI summary of your recent context. Not a boring list. Actual insights.

- **🔍 Context Chat** — Ask questions about your own life. "What was I working on last Tuesday?" "Which projects am I currently stuck on?" "What did I discuss with Zhang San this month?"

- **⚡ Proactive Insights** — LifeOS actively detects patterns and nudges you. Repeated thoughts worth writing up. Goal drift worth addressing. No more notification noise — only meaningful signals.

- **📅 Unified Timeline** — Every note, commit, meeting, and task in a single semantic timeline. Filter, search, explore.

- **🔌 Plugin Ecosystem** — Connect any tool. Obsidian, GitHub, Google Calendar built-in. Community plugins for Notion, Linear, Slack, and more.

- **🔒 Privacy First** — Runs with local Ollama. No cloud, no telemetry. Your context stays yours.

---

## 🚀 Quick Start

### Prerequisites

- [Ollama](https://ollama.com) (for local AI, recommended)
- Python 3.11+
- Node.js 20+
- Rust (for building the desktop app)

### 1. Clone & Install

```bash
git clone https://github.com/lifeos-app/lifeos.git
cd lifeos

# Pull the AI models
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

### 2. Start the Backend

```bash
cd apps/backend
pip install -r requirements.txt
python main.py
```

### 3. Start the Frontend (Dev Mode)

```bash
cd apps/desktop
npm install
npm run tauri dev
```

### Or: Download the Pre-built App

👉 **[Download for macOS / Windows / Linux](https://github.com/lifeos-app/lifeos/releases/latest)**

---

## 🔌 Supported Data Sources

| Plugin | Status | What it ingests |
|--------|--------|-----------------|
| 📝 Markdown Files | ✅ Built-in | Local notes, Obsidian vaults |
| 🐙 GitHub | ✅ Built-in | Commits, PRs, Issues |
| 📅 Google Calendar | ✅ Built-in | Meetings, events |
| 🗒️ Notion | 🚧 Community | Pages, databases |
| 📋 Linear | 🚧 Community | Issues, projects |
| 💬 Slack | 🚧 Community | Messages, threads |
| 🌐 Browser History | 🔜 Planned | Visited pages |

**Want to add your favorite tool?** It takes ~80 lines of Python. [See the Plugin Guide →](docs/PLUGIN_GUIDE.md)

---

## 🤖 LLM Support

LifeOS works with any LLM:

| Provider | How to Use |
|----------|-----------|
| Ollama (local) | Recommended. Zero cost, full privacy. |
| OpenAI | Set `OPENAI_API_KEY` in Settings |
| Anthropic | Set `ANTHROPIC_API_KEY` in Settings |

---

## 🏗️ Architecture

```
Tauri (Rust)           React Frontend          Python Backend
─────────────          ──────────────          ──────────────
System tray      ←→    Daily Brief UI   ←→    FastAPI + LangGraph
Notifications          Chat Interface          LanceDB (vectors)
Global hotkey          Timeline View           SQLite (metadata)
Process mgmt           Plugin Manager          APScheduler
```

Full architecture details in [ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 🧩 Building a Plugin

The simplest possible plugin:

```python
class MyPlugin(SourcePlugin):
    @property
    def name(self): return "my_tool"
    
    @property
    def display_name(self): return "My Tool"
    
    @property
    def description(self): return "Syncs data from My Tool"
    
    async def setup(self, config): 
        self.client = MyToolClient(config["api_key"])
    
    async def fetch_events(self, since):
        return [ContextEvent(
            id=f"mytool_{item.id}",
            source="my_tool",
            event_type=EventType.NOTE_CREATED,
            title=item.title,
            content=item.body,
            timestamp=item.created_at,
        ) for item in self.client.get_items(since=since)]
```

[Read the full Plugin Guide →](docs/PLUGIN_GUIDE.md)

---

## 🗺️ Roadmap

- [x] Core ingestion pipeline
- [x] Daily Brief agent
- [x] Proactive insights
- [x] Plugin ecosystem
- [ ] Browser extension (capture reading history)
- [ ] Mobile companion app (iOS/Android)
- [ ] End-to-end encrypted cloud sync
- [ ] Knowledge graph visualization
- [ ] Plugin marketplace

---

## 🤝 Contributing

Contributions are welcome! The easiest way to contribute:

1. **Write a plugin** for your favorite tool — [Plugin Guide](docs/PLUGIN_GUIDE.md)
2. **Improve the agents** — smarter insights, better briefs
3. **Fix bugs** — check the Issues tab
4. **Improve docs** — better is better

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a PR.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
  <p>Built with ❤️ by the open-source community</p>
  <p>
    <a href="https://github.com/lifeos-app/lifeos/discussions">Discussions</a> ·
    <a href="https://github.com/lifeos-app/lifeos/issues">Issues</a> ·
    <a href="docs/PLUGIN_GUIDE.md">Plugin Guide</a>
  </p>
</div>
