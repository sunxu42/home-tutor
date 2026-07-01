# Home Tutor

家庭辅导应用 — 浏览器客户端 + Python 服务端。

## 架构概览

```
home-tutor/
├── client/          # React + Vite + shadcn/ui（浏览器客户端）
└── server/          # Python + FastAPI + uv（数据分析 & LLM 服务）
```

### 数据模型

会话由两层存储协作：

| 层 | 存储 | 用途 |
|----|------|------|
| 索引 | SQLite `data/home_tutor.db` | 首页列表：科目、时间、正确率 |
| 内容 | 文件系统 `SESSION_FIXTURES_ROOT` | 讲解回顾：题目包、tutor 文案、时间轴 |

服务启动时会将 fixture 目录（`score48` … `score96` 共 10 条数学会话）自动种子化到 SQLite，保证首页可点击进入回顾页。

重新生成全部 mock 数据：

```bash
cd server
uv run python tests/fixtures/regenerate_all_fixtures.py
uv run python scripts/sync_fixture_sessions.py
```

### 通讯方式

| 协议 | 状态 | 用途 |
|------|------|------|
| HTTP | **已接入** | 会话列表、讲解回顾 API |
| WebSocket | 占位 | 实时事件推送（`api/websocket/`，待接入） |
| WebRTC | 占位 | 低延迟数据通道（`api/webrtc/`，待接入） |

开发环境下，Vite 将 `/api` 和 `/ws` 代理到 `http://localhost:8000`。

## 快速开始

### 服务端

```bash
cd server
uv sync
uv run dev
```

服务默认运行在 http://localhost:8000

### 客户端

```bash
cd client
npm install
npm run dev
```

前端默认运行在 http://localhost:5173

## 环境变量

**服务端**（见 `server/.env.example`）：

- `SESSION_FIXTURES_ROOT` — 讲解数据目录，默认 `tests/fixtures/sessions`
- `DATA_DIR` — SQLite 目录，默认 `data`

**客户端**（见 `client/.env.example`）：

- `VITE_API_BASE` — API 前缀，默认 `/api`

## 技术栈

**客户端**: React 19, TypeScript, Vite, Tailwind CSS, shadcn/ui

**服务端**: Python 3.12+, FastAPI, uvicorn, SQLAlchemy, pydantic-settings
