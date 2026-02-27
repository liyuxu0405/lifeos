<div align="center">
  <h1>🧠 LifeOS</h1>
  <p>
    <a href="README.md">English</a> | <a href="SETUP.md">简体中文</a>
  </p>
# LifeOS 完整安装与配置教程
</div>

## 目录

1. [环境要求](#1-环境要求)
2. [安装 Ollama（本地 AI 引擎）](#2-安装-ollama)
3. [克隆项目 & 安装依赖](#3-克隆项目--安装依赖)
4. [启动后端](#4-启动后端)
5. [启动前端（开发模式）](#5-启动前端开发模式)
6. [首次配置](#6-首次配置)
7. [配置插件](#7-配置插件)
8. [打包为桌面应用（生产版本）](#8-打包为桌面应用)
9. [常见问题排查](#9-常见问题排查)

---

## 1. 环境要求

| 软件 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 后端智能引擎 |
| Node.js | 20+ | 前端构建 |
| Rust | 1.77+ | Tauri 桌面应用编译 |
| Ollama | 最新版 | 本地 AI 模型运行 |

**检查现有环境：**
```bash
python --version    # >= 3.11
node --version      # >= 20
rustc --version     # >= 1.77
```

---

## 2. 安装 Ollama

Ollama 让你在本地运行 AI 模型，数据完全不离机。

### macOS / Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Windows
从 [ollama.com/download](https://ollama.com/download) 下载安装包。

### 拉取必要模型

```bash
# 对话模型（选一个，取决于你的显存/内存）
ollama pull llama3.1:8b      # 推荐：8GB+ 内存，效果好
ollama pull qwen2.5:7b       # 备选：中文理解更好
ollama pull llama3.2:3b      # 轻量：4GB 内存可用，效果一般

# Embedding 模型（必须，影响搜索质量）
ollama pull nomic-embed-text  # 768 维，本地最佳
```

**验证 Ollama 正常运行：**
```bash
ollama run llama3.1:8b "你好，简单介绍一下你自己"
# 看到正常回复就说明 OK
```

---

## 3. 克隆项目 & 安装依赖

```bash
# 克隆仓库
git clone https://github.com/lifeos-app/lifeos.git
cd lifeos

# ─── 安装 Python 后端依赖 ───
cd apps/backend

# 推荐使用虚拟环境
python -m venv .venv
source .venv/bin/activate     # macOS/Linux
# .venv\Scripts\activate      # Windows

pip install -r requirements.txt

# ─── 安装前端依赖 ───
cd ../desktop
npm install
```

### 安装 Rust（如果未安装）
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# 验证
rustc --version
cargo --version
```

### 安装 Tauri CLI
```bash
cd apps/desktop
npm install  # tauri CLI 已包含在 devDependencies
```

---

## 4. 启动后端

```bash
cd apps/backend
source .venv/bin/activate   # 激活虚拟环境

# 复制环境变量模板
cp .env.example .env

# 编辑 .env（可选，也可以在 App UI 里配置）
# nano .env  或  code .env

# 启动后端服务
python main.py
```

你应该看到类似输出：
```
[LifeOS] 后端启动中...
[LifeOS] 数据库已就绪
[Registry] 已加载插件: markdown_files
[Registry] 已加载插件: github
[Registry] 已加载插件: google_calendar
[LifeOS] 插件系统已就绪，3 个插件可用
[LifeOS] 数据摄入调度器已启动
[LifeOS] ✅ 后端启动完成
INFO:     Uvicorn running on http://127.0.0.1:52700
```

**验证后端正常：**
```bash
curl http://localhost:52700/health
# 应返回：{"status":"ok","version":"0.1.0"}
```

---

## 5. 启动前端（开发模式）

**新开一个终端窗口：**

```bash
cd apps/desktop
npm run tauri dev
```

第一次运行会编译 Rust 代码，需要 2-5 分钟。之后热重载很快。

你会看到 LifeOS 窗口弹出，如果后端已启动，几秒后界面会加载完成。

---

## 6. 首次配置

打开 App 后，点击左侧导航栏最底部的 **⚙️ 设置** 图标：

### 配置 LLM（Ollama 本地，推荐）

| 字段 | 值 |
|------|-----|
| Ollama 地址 | `http://localhost:11434`（默认） |
| 对话模型 | `llama3.1:8b`（或你拉取的模型名） |
| Embedding 模型 | `nomic-embed-text` |

点击 **保存设置**，右上角会显示当前使用的 LLM 提供商。

### 配置 LLM（OpenAI，备选）

如果不想用本地 Ollama，可以填写 OpenAI API Key：

1. 前往 [platform.openai.com/api-keys](https://platform.openai.com/api-keys) 获取 Key
2. 在设置页粘贴 API Key
3. 保存即可，系统会自动检测并切换到 OpenAI

### 配置 LLM（Anthropic Claude，备选）

1. 前往 [console.anthropic.com](https://console.anthropic.com) 获取 API Key
2. 在设置页填写 Anthropic API Key

---

## 7. 配置插件

点击左侧 **🔌 插件** 图标：

### 插件 1：Markdown 文件（最简单）

1. 点击 **Markdown / Obsidian** 的 **连接** 按钮
2. 填写你的 Markdown 文件夹路径：
   - macOS 示例：`/Users/你的用户名/Documents/Notes`
   - Obsidian Vault 示例：`/Users/你的用户名/Library/Mobile Documents/iCloud~md~obsidian/Documents/MyVault`
   - Windows 示例：`C:\Users\你的用户名\Documents\Notes`
3. 选择是否包含子文件夹
4. 点击 **保存并连接**

连接成功后会立即开始同步，你会在时间轴中看到你的笔记。

### 插件 2：GitHub

**第一步：获取 Personal Access Token**

1. 登录 GitHub，点击右上角头像 → **Settings**
2. 左侧菜单最底部 → **Developer settings**
3. **Personal access tokens** → **Tokens (classic)**
4. 点击 **Generate new token**
5. 勾选权限：`repo`（全部）、`read:user`
6. 生成并复制 Token（只显示一次！）

**第二步：在 LifeOS 配置**

1. 点击 GitHub 插件的 **连接** 按钮
2. 粘贴 Token
3. 如需只同步特定仓库，填写：`username/repo1, username/repo2`（留空则同步全部）
4. 点击 **保存并连接**

### 插件 3：Google Calendar

**第一步：创建 Google OAuth 凭证**

1. 前往 [Google Cloud Console](https://console.cloud.google.com)
2. 创建新项目（或使用现有项目）
3. 左侧菜单 → **APIs & Services** → **Library**
4. 搜索 **Google Calendar API** → 启用
5. 左侧菜单 → **Credentials** → **Create Credentials** → **OAuth client ID**
6. 应用类型选择 **Desktop app**
7. 下载 JSON 文件，用文本编辑器打开，复制全部内容

**第二步：在 LifeOS 配置**

1. 点击 Google Calendar 插件的 **连接** 按钮
2. 把复制的 JSON 内容粘贴到 **OAuth 凭证 JSON** 框里
3. 点击 **保存并连接**
4. 浏览器会弹出 Google 授权页面，授权后自动返回

---

## 8. 打包为桌面应用

配置完成、开发验证 OK 后，可以打包为正式的桌面应用：

```bash
cd apps/desktop
npm run tauri build
```

构建产物位置：
- **macOS**：`apps/desktop/src-tauri/target/release/bundle/dmg/LifeOS_*.dmg`
- **Windows**：`apps/desktop/src-tauri/target/release/bundle/nsis/LifeOS_*-setup.exe`
- **Linux**：`apps/desktop/src-tauri/target/release/bundle/appimage/lifeos_*.AppImage`

> **注意：** 打包版本需要把 Python 后端一起打包。目前开发模式需要手动启动后端；生产打包的自动化脚本在 `TODO` 中——欢迎提 PR！

---

## 9. 常见问题排查

### 问：后端启动失败，提示 `ModuleNotFoundError`

```bash
# 确保在虚拟环境中
cd apps/backend
source .venv/bin/activate
pip install -r requirements.txt
```

### 问：LanceDB 安装失败

```bash
# 尝试升级 pip 和安装 wheel
pip install --upgrade pip wheel
pip install lancedb==0.8.2
```

### 问：前端显示 "正在启动 LifeOS..." 一直不动

原因：前端找不到后端服务。检查：
1. 后端是否正在运行：`curl http://localhost:52700/health`
2. 端口是否冲突：`lsof -i :52700`（macOS/Linux）

### 问：Ollama 模型不响应

```bash
# 检查 Ollama 是否在运行
curl http://localhost:11434/api/tags

# 如果没有，启动 Ollama
ollama serve

# 检查模型是否已拉取
ollama list
```

### 问：Tauri 编译失败（macOS）

```bash
# 安装 Xcode Command Line Tools
xcode-select --install
```

### 问：Tauri 编译失败（Linux）

```bash
# Ubuntu/Debian
sudo apt-get install -y libwebkit2gtk-4.1-dev \
  build-essential curl wget file libssl-dev libgtk-3-dev \
  libayatana-appindicator3-dev librsvg2-dev
```

### 问：Google Calendar OAuth 打不开浏览器

这通常发生在无桌面环境的服务器上。LifeOS 需要在有浏览器的本地机器上运行。

### 问：同步后时间轴没有数据

1. 检查插件状态是否显示"已连接"
2. 手动触发同步：点击插件旁边的刷新图标
3. 查看后端日志寻找错误信息

---

## 目录结构速查

```
lifeos/
├── apps/
│   ├── backend/          # Python 后端（FastAPI + LangGraph + LanceDB）
│   │   ├── core/         # 核心引擎（数据库、检索、Embedding）
│   │   ├── agents/       # AI Agent（Daily Brief、Insights）
│   │   ├── api/          # FastAPI 路由
│   │   ├── plugins/      # 数据源插件
│   │   │   ├── builtin/  # 官方插件
│   │   │   └── community/# 社区插件（在这里添加你的插件）
│   │   └── main.py       # 后端入口
│   │
│   └── desktop/          # Tauri + React 前端
│       ├── src/           # React 组件
│       │   ├── components/
│       │   ├── hooks/     # API 调用层
│       │   └── stores/    # Zustand 状态管理
│       └── src-tauri/     # Rust 层（系统托盘、通知）
│
└── docs/
    └── PLUGIN_GUIDE.md   # 插件开发指南
```

---

## 数据存储位置

所有数据存储在：

| 系统 | 路径 |
|------|------|
| macOS | `~/.lifeos/data/` |
| Linux | `~/.lifeos/data/` |
| Windows | `C:\Users\用户名\.lifeos\data\` |

- `lifeos.db` — SQLite 数据库（配置、日历、简报历史）
- `vectors/` — LanceDB 向量数据库（所有事件的 Embedding）
- `embedding_cache/` — Embedding 缓存（加速重复处理）
- `credentials/` — OAuth 凭证（加密存储）

**备份建议：** 定期备份 `~/.lifeos/data/` 目录即可保留所有数据。

---

如有问题，欢迎 [提 Issue](https://github.com/lifeos-app/lifeos/issues) 或查看 [Discussions](https://github.com/lifeos-app/lifeos/discussions)。
