---
document_version: "0.1"
language: "zh"
last_updated: "YYYY-MM-DD"
category: "ai_context"
tags: [architecture, snapshot]
---

# architecture_snapshot.md — 架构快照（模板）

> **作用**：描述系统「由哪些层与模块构成、谁依赖谁」。不描述实现细节。
> **受众**：AI 助手、新维护者。

---

## 1. 分层

| 层 | 职责 | 位置 | 允许依赖 |
|---|---|---|---|
| 接口层 | — | — | — |
| 领域层 | — | — | — |
| 基础设施层 | — | — | — |

## 2. 模块清单

| 模块 | 职责 | 入口 | 对外契约 |
|---|---|---|---|
| — | — | — | — |

## 3. 数据流

```text
<input> → <module> → <artifact> → <consumer>
```

## 4. 跨层约束

- ——
- ——

## 5. 变更记录

| 日期 | 变更 | 影响面 |
|---|---|---|
| YYYY-MM-DD | — | — |

> 🔴 只记录**架构级**变更。文件级改动看 `git log`，不要在这里维护第二份变更史。
