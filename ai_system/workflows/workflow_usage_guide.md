---
project_version: "0.9.0"
language: "zh"
last_updated: "2026-10-20"
purpose: "工作流使用手册——如何选择、串联与维护工作流。与 workflow_index.md（Registry）配套使用。"
---

# workflow_usage_guide.md — 工作流使用手册

> 注册表见 [workflow_index.md](workflow_index.md)：它回答「存在什么」。
> 本指南回答「如何选择与串联」。
> 想读懂某一个工作流的内部（而非「该调哪个」）→ 用 `Skill: workflow-explain`，
> 问题集与取证纪律见 [`project/standards/08_工作流认知准则.md`](../../project/standards/08_工作流认知准则.md)。

---

## 1. 三个层次

| 层 | 位置 | 回答 | 何时用 |
|---|---|---|---|
| **工作流定义** | `ai_system/workflows/*.md` | 一件事该怎么做 | 你要弄清步骤、闸门与判据 |
| **Skill** | `.claude/skills/*/SKILL.md` | 从哪里发起 | 你要真正执行一次操作 |
| **动态工作流** | `.claude/workflows/*.js` | 如何并行与收敛 | 任务需要 fan-out / 校验 / 汇总 |

**不要混层**：工作流定义是说明书，Skill 是入口，动态工作流是执行器。
三者之间的调用关系写在各工作流的「委托」节，不在本指南复述。

---

## 2. 选择工作流

先问三个问题：

1. **这是常规维护，还是一次性设计？**
   - 常规维护 → 文档 / 架构 / 验证同步类工作流。
   - 一次性设计 → 先走 `proposal-gen` 生成方案，再按方案执行。
2. **会改共享状态吗？**
   - 会（索引、台账、目录结构、远端）→ 走带闸门的工作流；先确认单写者。
   - 不会（只读审计、解释）→ 直接调用对应 Skill 或只读检查。
3. **可逆吗？**
   - 不可逆（删除、重命名、推送、发布）→ 必须先过确认与备份。

### 常见场景

| 场景 | 入口 |
|---|---|
| 文档与源码漂移 | `documentation_update_workflow.md` |
| 架构/模块结构变化 | `architecture_update_workflow.md` |
| 验证函数/基准值变化 | `validation_update_workflow.md` |
| 全量上下文重建 | `full_ai_context_update.md` |
| 上下文互相矛盾 | `ai_context_consistency_audit.md` |
| 新增顶层目录 | `G_newdir_workflow.md` |
| 方案生成与审计 | `Skill: proposal-gen` → `proposal_audit_workflow.md` |
| 新建/修改/废弃工作流 | `workflow_creation_workflow.md` / `workflow_authoring_workflow.md` / `workflow_deprecation_workflow.md` |
| 判断该不该并行 / 交接 | `parallel_session_launch_workflow.md` |
| 提交与推送 | `github_push_workflow.md` |
| 外部仓库入库 | `third_party_repo_ingestion_workflow.md` |
| 官方文档漂移 | `official_docs_sync_workflow.md` |
| 工程架构评估 | `project_engineering_assessment_workflow.md` |
| 工作流体系自审计 | `workflow_alignment_audit.md` |

---

## 3. 串联原则

1. **先生成，后执行**：凡需要「先设计、后执行」的变更，先写方案；方案状态为「待确认」时不得执行。
2. **先审计，后修改**：审计类工作流只读；修改类工作流消费审计结论。
3. **一进一出**：新增设施时写明退役判据；不要只加不减。
4. **单写者**：共享索引/台账同一时刻只有一个写者；并行会话先声明写入域。
5. **闸门即真理**：文档与脚本冲突时以脚本为准；不要用人工逐行比对替代已有闸门。

---

## 4. 驱动链（可选）

如果你的项目需要把多个工作流串成固定流水线，建议在 `records/` 或项目自己的目录中维护
一份「链模板目录」，写明：

- 链名与触发条件；
- 每一步的工作流文件与输入/输出契约；
- 失败时的停止点与人工确认点；
- 链本身的退役判据。

本骨架不预置具体链模板——链是项目特定的，不应伪装成通用设施。

---

## 5. 维护本指南

- 新增/删除工作流时，同步 `workflow_index.md`；本指南只在「选择逻辑」变化时更新。
- 不在这里维护工作流计数、版本号或变更史——真值在 Registry 与 git 历史。
