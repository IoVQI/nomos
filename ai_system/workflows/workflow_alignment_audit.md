---
project_version: "0.9.0"
language: "en"
last_updated: "2026-09-10"
compatible_project_version: ">= 0.1.0"
category: "ai_workflow"
tags: [workflow, audit, workspace, deprecation-aware]
purpose: "审计工作流体系与项目架构的一致性，检测漂移与覆盖缺口并委托修复"
changelog: "wf-1.7: per_workflow_audit 废弃联动——Step 1a 消费依赖改写为冻结终态/独立漂移检测 + §4 委托目标标注废弃（2026-08-18）。; wf-1.6: 硬编码计数 39→46 (49 total files) + References 层 10→12 active + body text 同步至 2026-07-08. wf-1.5: Light Audit 新增 G4-style version_registry 快速一致性检查 + version_registry 漂移从 MEDIUM 提升为 CRITICAL. wf-1.4: 硬编码计数 26→39 + project/research/ → sandbox/notebooks/project/research/ 路径修正 + Coverage 表刷新至 2026-06-23. wf-1.3: 硬编码计数 20→26 + 委托目标新增 journal_index_audit_workflow. wf-1.2: 废弃/完成感知委托目标 + project/research/ 槽位刷新 + 计数修正 (18→20)."
---

# Workflow Alignment Audit

## Goal

Validate whether AI workflows remain aligned with:

- current project architecture
- ai_context structure
- engineering practices
- execution pipelines
- workspace structure (`project/research/`)

This workflow is an auditor, not an executor.

Do not directly rewrite workflows.

---

## Modes

### Light Audit (quick, low context cost)

- Verify file references in `workflow_index.md` are all valid
- Count registered vs. on-disk workflows (expect 65 workflow definition files + workflow_index.md + workflow_usage_guide.md + chain_template_catalog.md = 68 total)
- Check solver internalization status across workflow files
- Verify all workflow definition files have valid YAML frontmatter with populated `project_version` / `last_updated` / `language` / `purpose` fields
- Check deprecation/completion status consistency between `workflow_index.md` and `version_registry.md`
- **Registration quick check**: `workflow_index.md` §1/§2 注册与磁盘定义文件对账（原 G4-style `workflow_version` vs `version_registry.md` §2 检查已随该设施 2026-08-31 退役移除）
- Report registration gaps only
- Skip full drift analysis and delegation planning
- Runtime: ~1/4 of full audit

**Use**: every 3-5 sessions; after small context drift; as a fast health pulse.

### Full Audit (comprehensive)

- Full 6-step process below (Step 0 through Step 6)
- Includes prior report review, workspace analysis, drift detection, delegation planning, and execution tracking

**Use**: on explicit request; after major structural changes (new modules, new workflow types, workspace reorganization); after 10+ sessions without audit.

---

# Step 0 — Read Prior Audit Reports

## Step 0a — Read Audit Index (Global View)

Before reading individual audit files, read `audit/audit_index.md` §1 (Quick Reference YAML) and §4 (Recommendation Chain Tracker). This provides:

- Last audit date and file pointer
- Active/resolved cross-audit patterns (A–E)
- Recommendation chain status (resolved / partially resolved / blocked)
- ~30 lines — minimal context cost, maximal global view

## Step 0b — Read Prior Audit File

Read the audit file referenced by `audit_index.md` §1 `last_audit_file`. Additionally:

- `audit/*/audit_execution_record.md` (if any beyond the last)
- `audit/documentation_status_*.md`

Extract:

- Prior audit dates and findings
- Previous recommendations and their execution status
- Open/unresolved items from prior reports
- Trends: are the same issues recurring?

Generate:

# Prior Audit Status Summary

Include:
- Last audit date
- Total prior recommendations
- Executed vs. unexecuted counts
- Blocked/open items
- Recurring issues (appeared in ≥2 prior audits)

This provides a governance feedback loop — the audit must track whether its own prior recommendations were acted upon.

---

# Inputs

Read:

- `context/architecture_snapshot.md`
- `context/module_index.md`
- `context/project_state.md`
- `context/notebook_registry.md`
- `context/validation_registry.md`
- `context/eos_pipeline.md`
- `context/refactor_history.md`
- `context/documentation_rules.md`
- `workflows/workflow_index.md`
- `version_registry.md`
- `project/research/README.md`
- `project/research/*/README.md` (per-experiment workspace docs)
- `project/research/*/dev_notes.md` (per-experiment dev notes, if present)

Analyze:

- `workflows/*`
- `project/research/` directory structure (all experiment slots)

Compare workflow assumptions against the actual project.

---

# Step 1 — Analyze Workflows

## 1a — Workflow Analysis（消费逐项审计索引）

> 🆕 (2026-08-18): `per_workflow_audit_workflow` 已废弃。本工作流的逐项内容审计依赖随之下线；Step 1a 改为读取冻结的 `ai_system/audit/workflows/index.md` 历史终态（若有），或直接执行自身漂移检测。

1. 读取 `ai_system/audit/workflows/index.md`，提取：
   - 所有工作流的健康状态（healthy / attention / stale / broken）
   - 每个工作流的发现计数（CRITICAL / WARNING / INFO）
   - 上次全量审计日期
2. 识别高风险工作流（health=stale/broken 或 findings_critical ≥ 3）
3. 将高风险工作流作为 Step 2 漂移检测的重点关注对象

> 逐项深度内容审计已随 `per_workflow_audit_workflow` 废弃而终止；本工作流独立执行自身漂移检测（无上游审计依赖）。

## 1b — Workspace Structure Analysis

Analyze `project/research/`:

- List all experiment slots (e.g. `model/`, `solver/`, `benchmark/`, `parameter_scan/`, `integrated/`, `_archive/`, `_shared/`)
- Check per-experiment `README.md` and `dev_notes.md` existence
- Identify workspace directories lacking corresponding workflows
- Verify notebook workflows cover all active experiment slots
- Identify `project/research/` slots not referenced in any ai_context file

Generate:

# Workflow Capability Report

# Workspace Coverage Report

---

# Step 2 — Detect Workflow Drift

Detect:

- structural drift
- pipeline drift
- obsolete assumptions
- invalid references
- missing workflow coverage
- execution-order inconsistencies
- frontmatter drift: missing frontmatter, stale `last_updated`, mismatched `language` tags（原 `workflow_version` ↔ `version_registry.md` §2 一致性检查已随该设施 2026-08-31 退役移除）
- **workspace-to-workflow coverage gaps** (project/research/ slots not covered by any workflow)
- **new project/research/ slots** not registered in notebook_registry.md
- **ai_context gaps** for workspace content (README/dev_notes not reflected in project_state.md)
- **deprecation/completion status accuracy**: verify that workflows marked as deprecated or completed in `workflow_index.md` are also marked consistently in `version_registry.md` §2, and that their former delegation targets have been updated to point to their replacements

Classify:

- critical
- medium
- minor

Generate:

# Workflow Drift Report

---

# Step 3 — Generate Refactor Plan

For each workflow classify:

- keep
- minor update
- major refactor
- obsolete

Then specify:

- required updates
- required removals
- required delegation targets
- required new workflows

Generate:

# Workflow Refactor Plan

---

# Step 4 — Generate Delegation Plan

Do not directly modify workflows.

Delegate required changes to:

- **architecture workflows** → `architecture_update_workflow.md`
- **documentation workflows** → `documentation_update_workflow.md`（⚠️ `documentation_refactor_workflow.md` 已于 2026-07-21 废弃）
- **documentation generation workflows** → `workflow_documentation_generation.md` (⚠️ 已废弃 2026-06-02)
- **notebook workflows** → 手动维护 `project/research/` README（⚠️ `notebook_update_workflow.md` 已于 2026-07-15 废弃）
- **notebook analysis workflows** → `notebook_workflow_lite.md`（⚠️ `notebook_workflow_full.md` 已于 2026-07-15 废弃）
- **notebook migration workflows** → `notebook_migration_workflow.md`
- **validation workflows** → `validation_update_workflow.md`
- **ai_context synchronization workflows** → `ai_context_consistency_audit.md`; ~~`ai_context_consistency_reconciliation.md`~~ (deprecated → audit); ~~`ai_context_delta_synchronization.md`~~ (deprecated → doc_update)
- **portability workflows** → audit the current tree; do not rely on a historical refactor plan.
- **workspace management workflows** → migration and coverage workflows that exist in the current registry.
- **model domain workflows** → `eos_update_workflow.md`
- **session management workflows** → 会话收尾改走 `/闭环本会话`
- **release engineering workflows** → `github_push_workflow.md`
- **project assessment workflows** → `project_engineering_assessment_workflow.md`
- **journal maintenance workflows** → `journal_index_audit_workflow.md`
- **meta-workflow maintenance** → `workflow_index.md` update + user-confirmed self-modification
- **per-workflow audit workflows** → `per_workflow_audit_workflow.md` ⚠️ 已废弃（2026-08-18，不再产出卡片）

## Compound Delegation Rule

When a task spans both structural and descriptive ai_context changes,
do NOT delegate with "or":

  ❌ "delegate to workflow_A **or** workflow_B"

This creates a race condition: the first workflow to execute will
do the work, and the second will either duplicate effort or silently
skip — losing governance traceability.

Instead, split the task:

  ✅ "P4a (structural) → full_project_sync → full_ai_context_update"
  ✅ "P4b (descriptive) → documentation_update_workflow Phase 4"

Each sub-task has exactly one owner. The audit execution record
must track completion of both sub-tasks independently.

## Self-Repair Delegation

When the audit workflow itself has drift:

1. **Minor fixes** (path typos, count updates, stale references): self-modify with user confirmation, then record the change in the audit execution record.
2. **Structural changes** (new steps, category expansion, mode additions): propose changes to user for approval before modifying.
3. **Index-level changes** (new workflow registration): delegate to `workflow_index.md` maintenance — do not self-modify the index directly.

Self-repair must be traceable. Every self-modification must be logged in the audit execution record with: what changed, why, and user confirmation status.

Generate:

# Workflow Delegation Plan

---

# Step 5 — Final Validation

Validate:

- workflow interoperability
- workflow coverage
- workflow consistency
- ai_context compatibility
- workspace-to-workflow alignment
- prior recommendations execution status

Generate:

# Final Workflow Audit Summary

---

# Step 6 — Record Audit Execution

After completing the audit, record execution metadata in `audit/`:

Generate:

# Audit Execution Record

Include:
- **Audit date** (YYYY-MM-DD)
- **Mode** (light / full)
- **Prior recommendations status**: executed / pending / blocked counts
- **Findings summary**: critical / medium / minor counts with brief descriptions
- **Recommendations list**: numbered IDs (R1, R2, ...) with classification (critical/medium/minor)
- **Governance feedback**: whether prior recommendations were acted upon
- **Self-repair log**: any modifications made to this workflow during the audit

Place in: `audit/YYYY-MM-DD/audit_execution_record.md`

This enables:
- Cross-audit trend analysis
- Governance accountability (are recommendations being followed?)
- Detection of recurring issues

---

# Coverage Verification

When new directories appear in `project/research/`, flag them as:

- **Workflow coverage gap**: no corresponding workflow exists → recommend creating one
- **ai_context coverage gap**: no entry in `notebook_registry.md` or `project_state.md` → recommend registration
- **Governance risk**: ungoverned workspace slots accumulate unmanaged experimental state

Maintain a monitoring table for workspace slots. Fill it from the live tree; do not keep a
dated snapshot in this document.

| Slot | Status | Has Workflow? | Has ai_context Entry? | Risk |
|------|--------|--------------|----------------------|------|
| `<slot>/` | Active / Reserved / Infrastructure | ✅ / Partial / ❌ | ✅ / Partial / ❌ | — |

When any new directory appears under the experiment workspace, re-run coverage verification.

When any new `.md` file appears in `workflows/` that is not registered in `workflow_index.md`,
flag it as a **workflow registration gap** — the audit itself should detect on-disk vs.
registered mismatches.

> Historical audit findings belong in the audit report, not in this workflow definition.
> Keep this section as a template; append findings to the report produced by the run.

---

# Constraints

- do not directly rewrite workflows
- do not duplicate ai_context
- do not store static architecture data
- do not bypass workflow delegation
- do not hardcode project structure
- use ai_context as the single source of truth
- self-repair must be user-confirmed and traceable
- record audit execution for governance feedback
