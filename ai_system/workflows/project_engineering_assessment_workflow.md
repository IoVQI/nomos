---
project_version: "0.9.0"
language: "en"
last_updated: "2026-09-12"
compatible_project_version: ">= 0.4.0"
category: "ai_workflow"
tags: [assessment, audit]
purpose: "审计研究项目的工程架构、工作流与可维护性，生成评估报告与重构建议；只读审计，唯一例外是 Step 13 条件性写入备忘录台账（records/notes/，治理基础设施）"
changelog: "wf-1.3: Step 13 rewired to ledger model（2026-09-10 台账重置对齐：手插表行 / 详情文件 / P3 储备池旧模型 → 台账条目 + render/check）+ 接入 06 §1 准入闸门。; wf-1.2: Step 13 added — extract critical/high recommendations to records/index.md memo table (唯一例外于只读原则). wf-1.1: Step 7 scientific capability list updated to reflect Phase 4 implementations (tidal, rotation, Maxwell, eos_parametric, eos_rmf); project context refreshed with current module inventory."
---

# Project Engineering Assessment Workflow

## Goal

Perform a comprehensive engineering-scale assessment of a research project.

This workflow evaluates:

* project architecture
* AI workflow systems
* ai_context systems
* notebook infrastructure
* scientific engineering pipelines
* workflow governance
* long-term maintainability
* future-proof capability

The workflow is audit-oriented.

It does not directly modify the project — with one exception: Step 13 may conditionally write to the memo ledger (`records/notes/`) and its generated index view (governance infrastructure).

---

# Supported Project Types

Especially suitable for:

* notebook-heavy projects
* model/solver research projects
* AI-assisted scientific engineering
* workflow-governed projects
* benchmark-driven projects
* multi-pipeline research systems

---

# User Inputs

* project_root
* output_directory
* output_language
* assessment_mode

---

# Input Definitions

## project_root

Root directory of the project to assess.

Example:

./lab

---

## output_directory

Directory where the assessment report will be saved.

Example:

./Journal

---

## output_language

Supported:

* Chinese
* English

---

## assessment_mode

Supported:

* overview
* standard
* full

---

# Assessment Modes

## overview

Generate:

* high-level architecture review
* workflow summary
* major risks
* short recommendations

Best for:

* quick project review
* onboarding
* architecture snapshot

---

## standard

Generate:

* architecture assessment
* workflow assessment
* notebook infrastructure assessment
* maintainability analysis
* technical debt analysis

Recommended default mode.

---

## full

Generate:

* full workflow governance analysis
* ai_context system analysis
* interoperability analysis
* scalability analysis
* future-proof analysis
* orchestration analysis
* scientific engineering maturity analysis

> **Mode 路由**：`overview` 执行浅层步骤（架构/工作流摘要/主要风险/短建议）；`standard`（默认）执行架构 + 工作流 + notebook + 可维护性 + 技术债全步骤；`full` 在 standard 基础上追加治理/AI 上下文/互操作/可扩展/前瞻分析。执行者按所选 mode 决定 Steps 1-13 的执行范围——浅层模式跳过深层分析步骤。

Best for:

* architecture audit
* governance review
* long-term engineering planning

---

# Step 1 — Analyze Project Structure

Analyze:

* directory structure
* module organization
* notebook organization
* docs organization
* workflow organization
* configuration systems
* validation systems

Determine:

* architectural clarity
* module boundaries
* scalability
* coupling risks

Generate:

# Project Architecture Assessment

---

# Step 2 — Analyze AI Context System

Analyze:

* context/*
* context synchronization
* context scalability
* workflow integration
* stale context risks
* duplicated context risks

Determine:

* ai_context maturity
* synchronization stability
* Claude Code compatibility

Generate:

# AI Context System Assessment

---

# Step 3 — Analyze Workflow System

Analyze:

* workflows/*
* workflow taxonomy
* workflow governance
* workflow interoperability
* delegation structures
* orchestration stability
* workflow drift resistance

Determine:

* workflow maturity
* governance quality
* scalability risks
* obsolete workflows

Generate:

# Workflow System Assessment

---

# Step 4 — Analyze Notebook Infrastructure

Analyze:

* notebook organization
* portability
* reproducibility
* validation integration
* output isolation
* cache management
* benchmark integration

Check:

* hardcoded paths
* notebook pollution risks
* notebook coupling
* reproducibility risks

Generate:

# Notebook Infrastructure Assessment

---

# Step 5 — Analyze Documentation System

Analyze:

* lab/docs/
* workflow documentation
* documentation completeness
* documentation maintainability

Check:

* stale documentation
* missing workflow coverage

Generate:

# Documentation System Assessment

---

# Step 6 — Analyze Engineering Maintainability

Analyze:

* modularity
* naming consistency
* configuration isolation
* dependency management
* reproducibility
* validation strategy
* testability

Check:

* technical debt
* hidden coupling
* fragile pipelines

Generate:

# Engineering Maintainability Assessment

---

# Step 7 — Analyze Scientific Engineering Capability

Analyze support for:

* model pipelines (common + model-A + MIT + parametric + model-B)
* solver pipelines (core + tidal + rotation + adaptive stepping)
* model-C models
* interpolation systems (EOSInterpolator)
* benchmark systems (literature model batch M-R)
* validation pipelines (tests/)
* 派生观测量（如特征频率、响应系数）
* 参数扫描与批量生产
* 多阶段/多相模型
* 参数化模型族

Determine whether the project is suitable for future expansion into:

* 更高维参数空间
* 与其他求解器的耦合
* parameter scans (large-scale model parameter space exploration)
* large-scale benchmark suites
* AI-assisted scientific workflows
* gravitational wave data analysis pipelines

Generate:

# Scientific Workflow Assessment

---

# Step 8 — Analyze AI Engineering Maturity

Evaluate whether the project supports:

* AI-native engineering
* workflow governance
* context engineering
* workflow orchestration
* AI-assisted maintenance
* scalable AI workflows

Classify project maturity:

* basic
* intermediate
* advanced
* AI-native engineering

Generate:

# AI Engineering Maturity Assessment

---

# Step 9 — Analyze Future-Proof Capability

Analyze:

* scalability
* workflow scalability
* notebook scalability
* benchmark scalability
* scientific extensibility
* governance extensibility

Determine:

* most stable systems
* most fragile systems
* drift-prone systems
* future refactor risks

Generate:

# Future-Proof Analysis

---

# Step 10 — Generate Risk Report

Classify risks into:

* critical
* medium
* minor

Analyze:

* architecture risks
* workflow risks
* notebook risks
* ai_context risks
* scalability risks

Generate:

# Technical Debt & Risk Report

---

# Step 11 — Generate Recommendations

Generate:

* architecture recommendations
* workflow governance recommendations
* notebook infrastructure recommendations
* maintainability recommendations
* future-proof recommendations

Do not modify the project.

Recommendations only.

Generate:

# Refactor Recommendations

---

# Step 12 — Generate Final Assessment

Summarize:

* overall project maturity
* strongest engineering aspects
* weakest engineering aspects
* governance maturity
* future scalability
* highest-priority improvement areas

Generate:

# Final Overall Assessment

---

# Step 13 — Update Memo Ledger (Optional)

**Trigger**: When the assessment report contains actionable recommendations
(Step 11 — Refactor Recommendations) classified as critical or high-priority.

**Purpose**: Ensure high-priority engineering recommendations are tracked
in the memo ledger (`records/notes/`) for follow-up. This is the ONLY
exception to the "do not modify project" rule — the modification target is the
memo ledger + its generated index view (governance infrastructure), not the
assessed project.

**Operations**:

1. Read the generated assessment report, focusing on:
   - Step 11 (Refactor Recommendations) — critical and high-priority items
   - Step 10 (Technical Debt & Risk Report) — critical risks

2. For each critical/high item, extract:
   - A concise one-line description (≤80 chars if possible)
   - The recommendation category as context

3. 读台账真源 `records/notes/`（**不是** `records/index.md` 的表——后者自 2026-09-10 起是生成视图，禁止手改）。

4. For each extracted item:
   - 去重：Check if a semantically similar entry already exists（在**台账**中比较 descriptions，not exact string match）。判定方法：共享 ≥3 个关键词且主题相同 → 视为重复（阈值供参考，执行时按语义判断）。
   - If a duplicate is found → skip (do not create redundant entries).
   - **准入闸门（2026-09-12 起）**：过 [`project/standards/06 改进与维护宗旨`](../../project/standards/06_改进与维护宗旨.md) §1 四问（证据/归宿/成本/手段）；未过闸门 → 不建条目，在评估报告中记录原因。
   - If new → 创建台账条目 `records/notes/memo_<id>.md`：
     - `<id>` = 当前台账最大编号 + 1；🔴 **创建后永久不变、不复用**
     - frontmatter 按 `records/notes/README.md` schema：`id` / `ledger: work` / `title` / `status: active` / `priority` / `writable_by: ai` / `created` / `updated` / `source`；正文含 `## 事项` 段
     - `title` = concise description
     - `source` = `project_engineering_assessment`
     - `priority` = **术语映射统一**：critical → P1、high-priority/medium → P2、minor → P3（P3 亦可建条目：`priority: P3` 渲染时自动落「💤 低优先级储备」段）
     - `estimate` = estimated effort from recommendation (or `待评估` if not specified)
   - 写入后**同批**：`python ai_system/validation/render_memos.py --write` + `python ai_system/validation/check_memos.py --quiet`（期望 0 FAIL）

5. **Constraints**:
   - Maximum 5 new memo items per assessment run (avoid flooding the ledger).
   - Prefer items with concrete, actionable scope over vague architectural advice.
   - P3/minor items 可不建条目（非强制）；若建，按上方 P3 规则。
   - Do NOT modify archive tables (proposals/, reports/, assessments/, guides/, lab/).
   - 🔴 **不得手改 `records/index.md` 备忘录表、不得新建「详情文件」**——两者均为 2026-09-10 前台账模型，已废止；条目的唯一文件形态就是台账 `memo_<id>.md`。

6. If no critical/high items exist, skip this step silently.

---

# Output Rules

* audit only
* read-only
* do not modify project
* do not modify workflows
* do not synchronize ai_context
* do not generate releases
* do not rewrite notebooks
* **Exception**: Step 13 may write to the memo ledger (`project_root/records/notes/`)
  + regenerate its index view (governance infrastructure, not the assessed project).
  All other rules remain in force.

Assessment only.

---

# Language Rules

Use:

* Chinese if output_language=Chinese
* English if output_language=English

Maintain:

* engineering documentation style
* scientific engineering perspective
* long-term maintainability focus

---

# Output File Rules

Generate Markdown only.

Automatically generate a suitable filename.

Examples:

* research_project_assessment.md
* project_engineering_review.md
* workflow_governance_assessment.md

Save the generated report into:

output_directory

> ⚠️ **Journal 输出约定**：当 `output_directory` 为 `records/` 路径时，强制遵循 CLAUDE.md 约定——文件名 `YYYY-MM-DD_<描述>.md` + 存放于 `records/reports/YYYY/MM/DD/`（或对应段）+ 在 `records/index.md` 对应段注册条目。非 Journal 路径不适用此约束。

---

# Final Output

Report:

* generated filename
* full save path
* assessment mode used
* workflow statistics
* notebook statistics
* documentation statistics
* identified risk counts