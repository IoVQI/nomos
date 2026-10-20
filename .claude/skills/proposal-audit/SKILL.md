---
name: proposal-audit
description: >
  Audit a proposal for path errors, count inconsistencies,
  index facility breaks, logic chain gaps, registration gaps,
  destructive changes, and infrastructure reuse before human review.
  Use when the user asks to "audit this proposal", "审计这个方案",
  "check the proposal", "方案审计". Triggers on "audit proposal",
  "审计方案", "proposal audit", "check proposal quality".
argument-hint: "<proposal_path> [--depth l1|l2|l3|l4] [--impact i1|i2|i3]"
allowed-tools: Bash(git *) Bash(python *) Read(*) Glob(*) Grep(*)
---

## 审计方案

对 `$ARGUMENTS` 指定的方案执行 AI 预审计（7 维模型），标注问题后供人工复核。

### 执行规则

1. 读取 `${CLAUDE_PROJECT_DIR}/ai_system/workflows/proposal_audit_workflow.md` 作为详细审计规则参考
2. 解析参数：`$ARGUMENTS` → `proposal_path` + `--depth`（默认 `l2`）
3. 委托动态工作流执行：`/proposal-audit-check proposalPath="<proposal_path>" depth="<depth>"`
4. 🔴 审计报告呈现后，等待用户审阅——**不得自动执行修复**
5. 用户确认修复后 → `/proposal-audit-fix auditReportPath="<audit_dir>/<stem>_audit.json" proposalPath="<proposal_path>"`
6. 🔴 自动修复仅处理 AUTO_FIX 项（路径/计数/索引），SEMI/MANUAL 项保留给用户决策

### 审计深度

| 深度 | 维度 | Agent 数 | 适用场景 |
|:---:|------|:---:|------|
| L1 | D1–D4 | 7 | 快速扫（方案刚写完） |
| L2 | D1–D7 | 9 | **默认**（覆盖全部 7 维） |
| L3 | D1–D7 | 9 | 重要方案（≥5 工作流变更，深度读取被引用工作流 §1/§2） |
| L4 | D1–D7 | 9 | 架构级方案（完整读取被引用工作流全文） |

> L3/L4 与 L2 的 agent 数相同，差异在于 Phase 1 (Read) 读入上下文的深度——更深的上下文使 audit agent 能发现更多跨工作流一致性问题。

### 影响广度（🆕 wf-1.1）

| 广度 | 探索范围 | Agent 增量 | 适用场景 |
|:---:|------|:---:|------|
| **I1** | 仅方案显式列出的 `modified_files[]` + `related[]` | 0（当前行为） | 小范围修改（1-3 文件） |
| **I2** | I1 + 对每个 modified file 执行 grep 发现所有传递引用者（🆕 作用域隔离：报文件名不读正文 + 排除同日期兄弟方案） | +1（Phase 1 扩展） | **默认**（基础设施文件修改时） |
| **I3** | I2 + 链模板触发域交叉检查 + `version_registry` 消费者 + `proposals/` 引用 | +1（Phase 1 扩展 + D6 增强） | 架构级方案 |

> `--impact` 参数可选，默认 `i2`。`--impact i1` 完全等价于升级前行为。`

### 七维模型速查

| 维度 | 检查内容 |
|:---:|------|
| D1 | 所有文件路径引用是否存在 |
| D2 | 所有数值声明是否与真源一致 |
| D3 | 新建设施是否在对应索引中注册 |
| D4 | 步骤依赖/闸门条件/摘要是否自洽 |
| D5 | 新建设施的注册是否完备 |
| D6 | 变更是否可逆/有回滚方案/无冲突 |
| D7 | 是否重复造轮子/充分委托已有设施 |
