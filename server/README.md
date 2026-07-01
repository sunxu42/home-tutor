# Home Tutor Server

Python 后端服务，负责数据分析与 LLM 内容生成。

## 目录结构

```
server/
├── schemas/                 # JSON Schema 契约（权威来源）
├── src/home_tutor/
│   ├── main.py              # FastAPI 入口
│   ├── core/                # 配置
│   ├── api/
│   │   ├── http/            # REST API
│   │   ├── websocket/       # WebSocket
│   │   └── webrtc/          # WebRTC 信令
│   ├── services/
│   │   ├── analysis/        # 数据分析
│   │   └── llm/             # LLM 内容生成
│   └── models/              # Pydantic 模型（与 schemas/ 对齐）
├── tests/
└── pyproject.toml
```

## 开发

```bash
uv sync
cp .env.example .env
uv run dev
```

## 测试

```bash
uv run pytest
```

## Fixture：拆分 OCR 会话

将 monolithic `ocr-sessions/*.json` 拆为讲解页所需的目录结构：

```bash
cd tests/fixtures
uv run python split_ocr_session_fixture.py --all
```

输出：`tests/fixtures/sessions/score50|score70|score90/`（含 `meta.json`、`events.jsonl`、`packages/`、`tutor/`、`timeline-index.json`）。

讲解回顾 API：

- `GET /api/sessions/{session_id}/tutor-view`
- `GET /api/sessions/{session_id}/questions/{question_id}`
