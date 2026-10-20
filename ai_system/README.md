# ai_system/ — AI 自律系统

> **定位**：本项目的 AI 工程治理系统。管理 AI 助手的工作流定义、上下文恢复、提示模板、规约文件与校验闸门。
> **受众**：AI 助手（主要）、项目维护者（次要）
> **最后更新**：2026-10-05

---

## 与项目其他部分的关系

```
nomos/
├── ai_system/        ← 本目录：AI 工程治理
├── project/          项目级活文档（准则 + 索引）
├── proposals/        方案落地区
├── coordination/     多会话协调
└── <空壳目录>        见根 README
```

- `ai_system/` **管辖** AI 工作流、上下文恢复、提示、规约、闸门
- `ai_system/` **不管辖** 业务代码、文档正文、方案内容

## 目录结构

| 子目录 / 文件 | 内容 | 真值 |
|--------|------|------|
| `workflows/` | AI 工作流定义（治理、审计、同步、维护） | `ls ai_system/workflows/*.md` |
| `context/` | AI 跨会话上下文恢复模板 | `ls ai_system/context/*.md` |
| `rules/` | 编码 / 调试规约 | `ls ai_system/rules/*.md` |
| `prompts/` | AI 提示模板 | `ls ai_system/prompts/*.md` |
| `scripts/` | 辅助脚本（`researchers/` 开发侧本地 + `reusable/`） | `ls ai_system/scripts/*/` |
| `official_docs/` | 上游文档链接清单（镜像不随发布件分发） | `ai_system/official_docs/index.md` |
| `validation/` | 校验闸门脚本 | `ls ai_system/validation/*.py` |
| `index.md` | 入口索引 | — |
| `version_registry.md` | 版本策略与注册表 | — |

## 三层设施（别混）

| 层 | 位置 | 性质 |
|---|---|---|
| **工作流定义** | `ai_system/workflows/*.md` | 规程：步骤、闸门、判据 |
| **Skill** | `.claude/skills/*/SKILL.md` | 入口：把工作流包成可调用命令 |
| **动态工作流** | `.claude/workflows/*.js` | 执行：确定性的多 agent 编排 |

**闸门**（`ai_system/validation/*.py`）是唯一机械判据，挂在 `.pre-commit-config.yaml` 与
`.github/workflows/ci.yml` 两处。文档描述与脚本冲突时，**以脚本为准**。

## 入口

- **索引**：[index.md](index.md) — 全部子模块导航
- **工作流注册表**：[workflows/workflow_index.md](workflows/workflow_index.md)
- **项目状态**：[context/_templates/project_state_template.md](context/_templates/project_state_template.md) — 新会话上下文恢复模板
- **版本信息**：[version_registry.md](version_registry.md)
