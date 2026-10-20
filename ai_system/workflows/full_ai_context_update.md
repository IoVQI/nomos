---
project_version: "0.9.0"
language: "zh"
last_updated: "2026-08-17"
compatible_project_version: ">= 0.1.0"
category: "ai_workflow"
tags: [ai-context, full-update]
purpose: "全量更新并同步 AI 上下文文件，确保其与当前源码、架构、model 及 validation 体系一致"
changelog: "wf-1.2: 当前版本（2026-06-12 创建，随 ai_system 拆分从 lab/ 迁出）；wf-1.0: 初始版本（多领域代码变更后全量更新全部 AI 上下文文件）"
---

# Full AI Context Update Workflow

## 工作流目标

本工作流用于：

在项目发生代码修改、架构调整、EOS变化、validation变化、notebook变化之后，

对：

context/

中的 AI 上下文文件，

进行：

恢复、分析、更新、同步。

目标：

确保：

* AI上下文层与当前源码一致
* AI上下文层与当前架构一致
* AI上下文层与当前EOS流程一致
* AI上下文层与当前validation体系一致
* AI上下文层与当前notebook体系一致

本工作流：

适用于：

* 大型重构后
* EOS流程变化后（管线、常数、模型、拼接逻辑）
* notebook迁移后
* validation体系变化后
* 长上下文会话之后
* 使用 /compact 后
* 新会话恢复工程状态时
* 缺少对应领域工作流时的单领域变更（使用 Light Mode）

注意：上下文文件应描述当前实际存在的目录；已移除的外部副本不应继续出现在快照中。

### Compound Delegation Rule 约束

本工作流处理 ai_context 的**结构性变更**（目录树重写、全量重建）。
对于描述性增量更新（模块描述完善、章节扩展），必须委托至
`documentation_update_workflow` Phase 4 执行。

详见：`workflow_alignment_audit.md` §Compound Delegation Rule

---

# Phase 1：恢复工程认知

现在，请先不要更新任何文档。

请先恢复整个项目上下文。

项目路径：

./ai_system

请重点阅读：

* context/project_state.md
* context/refactor_history.md
* context/documentation_rules.md
* context/architecture_snapshot.md
* context/eos_pipeline.md
* context/notebook_registry.md
* context/validation_registry.md
* context/module_index.md
* context/cross_reference_map.md
* context/pytov_migration_analysis.md

同时结合：

* 当前源码
* 当前notebook
* 当前README
* 当前architecture
* 当前physics_notes
* 当前validation_checklist

你的目标是：

恢复整个工程的当前状态。

请输出：

# 当前项目状态

# 当前EOS架构

# 当前validation体系

# 当前notebook体系

# 当前模块体系

# 当前可能过期的文档

暂时不要更新文件。

🔴 **gate-1（进入 Phase 2 前）**：确认 Phase 1 已完成——变更文件清单 + 受影响 context 文件已识别完整，无遗漏领域，方可进入 Phase 2。

---

# Phase 2：分析本次变化

现在，请分析：

自 ai_context 最近一次更新之后，

项目发生了哪些变化。

请重点分析：

1. 新增模块
2. 删除模块
3. 命名变化
4. EOS流程变化
5. TOV流程变化
6. notebook变化
7. validation变化
8. 架构变化
9. 配置变化
10. 已废弃实现
11. 文档体系变化（frontmatter规范、文档结构、新增文档文件、版本注册表）
12. 版本化变化（project version、docs version、workflow version、sync status）

请输出：

# 本次代码变化摘要

# 本次架构变化

# 本次EOS变化

# 本次validation变化

# 本次notebook变化

# 本次模块变化

# 本次文档体系变化

然后：

建立：

“代码/文档变化 → ai_context影响”

映射关系。

暂时不要更新文件。

🔴 **gate-2（进入 Phase 3 前）**：确认 Phase 2 已完成——影响映射关系已列出且完整（表格/列表，覆盖全部变更领域），无遗漏，方可在 Phase 3 开始更新文件。

---

# Phase 3：正式更新 ai_context

现在，请正式更新：

context/

中的所有上下文文件。

包括：

* project_state.md
* refactor_history.md
* architecture_snapshot.md
* eos_pipeline.md
* notebook_registry.md
* validation_registry.md
* module_index.md
* documentation_rules.md
* cross_reference_map.md（**只读引用**——由 `ai_context_consistency_audit` 维护，本工作流不直接更新）
* pytov_migration_analysis.md（**只读历史记录**——PYTOV 迁移已于 2026-05-13 完成，仅保留作参考，本工作流不直接更新）

要求：

1. 不要整文件重写
2. 仅更新受影响部分
3. 保持长期稳定性
4. 保持与源码一致
5. 保持与当前架构一致
6. 自动修复过期描述
7. 自动标记废弃内容
8. 自动维护术语一致性
9. 自动维护EOS流程一致性
10. 自动维护validation一致性

对于每个文件：

请输出：

# 修改原因

# 修改内容

# 与源码对应关系

# 是否存在待确认部分

最后：

请生成：

# ai_context更新报告

# 当前工程状态变化

# 当前EOS状态变化

# 当前validation状态变化

# 当前notebook状态变化

完成后必须执行 `ai_context_consistency_audit.md`（与 Light Mode L2 一致）——交叉审计全部 ai_context 文件，检测冲突漂移并统一化修复。

---

# Light Mode：单领域变更（定向更新）

当代码变更仅影响 1 个领域，且对应的领域工作流不存在或不确定是否适用时，使用 Light Mode。

Light Mode 仅包含 2 个阶段：

## Phase L1：恢复工程认知（范围：project_state.md + 变更源码）

读入 `project_state.md` + 变更涉及的源码文件。

## Phase L2：定向更新

仅更新受影响的 ai_context 文件节（不更新全部 8 个文件）。

更新范围：

| 变更领域 | 更新的文件 |
|---------|-----------|
| 模型/参数 | `context/project_state.md` 的目标与模型节；`context/architecture_snapshot.md` |
| 模块架构 | `context/project_state.md` 的架构节；`context/architecture_snapshot.md`；`context/module_index.md`（若启用） |
| 计算环境 | `context/project_state.md` 的环境节；`context/notebook_registry.md`（若启用） |
| Validation | `project_state.md` §12; `validation_registry.md`; `module_index.md` §13 |
| 文档体系 | `version_registry.md` §2 docs体系版本; `documentation_rules.md`; `architecture_snapshot.md` §1 docs目录树 |
| 版本化 | `version_registry.md` §2（docs 体系版本，非ai_context 直接更新）; `documentation_rules.md` frontmatter规则 |

要求：

1. 不重写整个文件——仅更新受影响节
2. 保持与其他 ai_context 文件的一致性
3. 完成后必须执行 `ai_context_consistency_audit.md`

**注意**: 如果对应的领域工作流已存在，优先使用领域工作流而非 Light Mode。

---

# 工作流原则

本工作流：

不是：

“普通文档更新流程”。

而是：

“AI工程认知维护流程”。

重点目标：

不是：

增加文档内容，

而是：

确保：

AI能够：

* 长期恢复工程状态
* 理解当前EOS流程
* 理解当前validation体系
* 理解当前notebook生态
* 理解当前模块关系
* 理解当前架构状态

---

# 禁止事项

禁止：

* 直接重写整个 ai_context
* 忽略当前源码状态
* 忽略当前EOS实现
* 忽略validation状态
* 忽略notebook状态
* 忽略refactor_history
* 在不同文件中使用不同命名
* 保留冲突架构
* 保留失效validation
* 保留已废弃实现为 active 状态

---

# 长期维护建议

建议：

每次：

* 大型重构
* EOS流程变化
* notebook迁移
* validation变化
* 使用 /compact
* 长上下文恢复

之后，

执行一次：

Full AI Context Update Workflow。

---

# 最终目标

构建：

长期稳定、

可恢复、

可维护、

跨会话一致、

面向未来AI协作的：

AI工程上下文系统。
