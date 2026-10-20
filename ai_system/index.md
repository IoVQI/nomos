# ai_system/index.md — AI 自律系统入口索引

> **作用**：AI 工程治理系统的统一导航入口。一个文件定位全部子模块。
> **受众**：AI 助手、项目维护者
> **最后更新**：2026-10-05

---

## 一、目录总览

```
ai_system/
├── index.md                  ★ 本文件
├── README.md                    系统总说明
├── version_registry.md          版本策略与注册表
├── workflows/                   AI 工作流定义 + 注册表 + 使用手册（真值：ls ai_system/workflows/*.md）
├── context/                     AI 上下文恢复模板（真值：ls ai_system/context/*.md）
├── rules/                       编码 / 调试规约（真值：ls ai_system/rules/*.md）
├── prompts/                     AI 提示模板（真值：ls ai_system/prompts/*.md）
├── scripts/                     辅助脚本
│   ├── researchers/             研究辅助脚本（开发侧本地，不随发布件分发）
│   └── reusable/                可复用机械核验脚本（方案族消费）
├── official_docs/               上游文档链接清单（镜像不随发布件分发）
└── validation/                  校验闸门脚本
```

## 二、工作流 (workflows/)

| 入口 | 说明 |
|------|------|
| [workflow_index.md](workflows/workflow_index.md) | **工作流注册表** — 全部 AI 工作流的存在状态 |
| [workflow_usage_guide.md](workflows/workflow_usage_guide.md) | **使用手册** — 层级关系、决策树、调用顺序 |

### 常用工作流

| 工作流 | 说明 |
|--------|------|
| [full_ai_context_update.md](workflows/full_ai_context_update.md) | AI 上下文全量更新 |
| [documentation_update_workflow.md](workflows/documentation_update_workflow.md) | 文档增量更新 |
| [ai_context_consistency_audit.md](workflows/ai_context_consistency_audit.md) | AI 上下文一致性审计 |
| [proposal_audit_workflow.md](workflows/proposal_audit_workflow.md) | 方案 7 维审计 |
| [G_newdir_workflow.md](workflows/G_newdir_workflow.md) | 新增顶层目录的架构门禁 |
| [parallel_session_launch_workflow.md](workflows/parallel_session_launch_workflow.md) | 判「该不该并行 / 该不该交接」 |
| [github_push_workflow.md](workflows/github_push_workflow.md) | 提交与推送的安全闸门 |

> 完整列表见 [workflow_index.md](workflows/workflow_index.md)。

## 三、上下文恢复 (context/)

| 文件 | 说明 |
|------|------|
| [_templates/project_state_template.md](context/_templates/project_state_template.md) | **新会话入口** — 项目状态快照模板 |
| [_templates/architecture_snapshot_template.md](context/_templates/architecture_snapshot_template.md) | 架构快照模板 |

> 复制模板到 `context/` 下填写。具体项目的上下文快照属于开发侧本地内容，不随发布件分发。
> 写法约定见 [context/README.md](context/README.md)。

## 四、提示模板 (prompts/) 与规约 (rules/)

| 文件 | 说明 |
|------|------|
| [prompts/debug_prompt.md](prompts/debug_prompt.md) | 调试提示模板 |
| [rules/coding_rules.md](rules/coding_rules.md) | 编码规约 |
| [rules/debug_rules.md](rules/debug_rules.md) | 调试规约 |

## 五、闸门 (validation/)

| 脚本 | 说明 |
|------|------|
| [check_workflows.py](validation/check_workflows.py) | 工作流注册表与磁盘的一致性（G1/G2/G5/G6/G7） |
| [verify_md_syntax.py](validation/verify_md_syntax.py) | Markdown 围栏配平 / 表格列数 / 数学配对 |
| [check_claude_md.py](validation/check_claude_md.py) | CLAUDE.md 链接与结构对账（**按需**，不进 pre-commit/CI） |
| [beijing_time.py](validation/beijing_time.py) | 规范时钟源（北京时间）与一致性自检 |
| [check_memory.py](validation/check_memory.py) | 跨会话记忆查询工具（非闸门） |

## 六、辅助脚本 (scripts/)

| 目录 | 说明 |
|------|------|
| `scripts/researchers/` | 学术元信息抓取（arXiv / INSPIRE / Semantic Scholar） |
| `scripts/reusable/` | 方案族的机械核验脚本（声明面集合 / 锚点唯一性 / 编辑落地） |

## 七、版本信息

[version_registry.md](version_registry.md) — 版本策略与注册表。
