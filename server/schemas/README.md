# JSON Schemas

本目录是 **API / 流水线数据契约的权威来源**（single source of truth）。

| 文件 | Schema ID | 说明 |
|------|-----------|------|
| `ocr-session.v1.schema.json` | `home-tutor.ocr-session.v1` | OCR 会话过程记录（**events-only**，单文件导出格式） |
| `session-meta.v1.schema.json` | `home-tutor.session-meta.v1` | 瘦身会话头（生产存储） |
| `session-timeline-index.v1.schema.json` | `home-tutor.session-timeline-index.v1` | 讲解页底栏时间轴索引 |
| `question-package.v1.schema.json` | `home-tutor.question-package.v1` | 按题物化包，供讲解与 LLM |
| `tutor-content.v1.schema.json` | `home-tutor.tutor-content.v1` | 按题讲解文案（v1 mock） |

设计说明见：`docs/product-design/ocr-session-schema-v1.md`

实现时：

- Python 侧用 Pydantic 模型与这些 schema 对齐（`home_tutor.models`）
- 写入 DB / 调用 LLM 前做校验
- 客户端通过 API 消费 JSON，TypeScript 类型可从 schema 生成（可选）
