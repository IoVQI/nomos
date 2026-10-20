---
project_version: "0.9.0"
language: "zh"
last_updated: "2026-09-10"
compatible_project_version: ">= 0.1.0"
category: "ai_workflow"
tags: [documentation, update, session-report, standalone-document, journal-index, body-metadata, version-registry, auto-sync]
purpose: "检测源码变更后的文档漂移，最小化增量更新文档并同步 AI 上下文。"
changelog: "wf-1.11: +Phase 3c 工作流版本-注册表自动同步 — git diff 检测 workflow_version bump → 自动更新 ai_system/version_registry.md §2（旧版本行递减 + 新版本行递增/新建 + check_workflows.py G4 验证闭环）。消除「版本 bump 后忘记同步 registry → CI G4 FAIL」的反复 human-error。; wf-1.10: 交叉引用更新指向 workflow_index.md §2。; wf-1.9: Phase 3 §3b body metadata 同步。; wf-1.8: Phase 1/2 records/index.md 扩展。; older: §3a 文档版本号递增。"
---

# Incremental Documentation Update Workflow

Goal:

Perform minimal, change-driven documentation updates
after source-code or architecture changes.

Principles:

- incremental update only
- modify affected files only
- modify affected sections only
- preserve structure and naming
- avoid full documentation rewrite
- preserve documentation consistency
- preserve AI context consistency

---

# PHASE 1 — Change Impact Scan

Analyze ONLY changed parts of the project:

- added/removed/renamed modules
- changed APIs
- changed workflows
- changed notebooks
- architecture changes
- dependency changes
- records/index.md (if records/ reports were added/modified in this change set —
  flag as `[Journal: may need index update]`, delegate to `journal_index_audit_workflow`
  for archive table consistency; do NOT edit archive tables directly)

Generate:

# Change Impact Report

Include ONLY:

- changed source files
- affected docs
- affected ai_context files
- affected workflows
- affected notebooks

Additionally, for EVERY document in `lab/docs/` and `project/lab/`:

### Standalone Document Drift Detection

All documents are **standalone** — they have no bilingual pair. Drift detection uses
**content-vs-project-state consistency check**.

**Trigger**: For every document in `lab/docs/` and `project/lab/`.

**Operations**:

1. Read the document's frontmatter:
   - Extract `last_updated` date
   - If `last_updated` is today or newer than the most recent relevant project
     change → skip (no drift expected)
   - Otherwise → proceed to content check

2. **Content Section Inventory**: Extract all major sections from the document
   (heading hierarchy, key claims, module counts, version references,
   capability tables, file listings).

3. **Cross-reference against authoritative sources**:
   - `context/project_state.md` — module counts, architecture layers,
     capability status, notebook inventory, technical debt
   - `context/architecture_snapshot.md` — directory tree, module list
   - `context/module_index.md` — module descriptions
   - `ai_system/version_registry.md` — version history, component versions
   - `context/refactor_history.md` — refactor entries (R14–Rxx)
   - Source code directory listings — actual file counts per directory

4. **Drift classification**:
   - `Critical` — module count mismatch (e.g., doc says 8 modules, actual is 9),
     missing entire refactor milestone (R17/R18 not documented), capability table
     stale (feature implemented but listed as "planned")
   - `High` — stale version references, outdated file listings (missing new
     modules in appendix), missing new glossary terms
   - `Medium` — minor description staleness, missing minor subsections
   - `Low` — typographical issues, formatting inconsistencies

5. **Special handling for `technical_white_paper.md`**:
   This document is the most comprehensive project reference — it synthesizes
   content from all other documentation. Key drift vectors include:
   - §1.3 (current capabilities table) — cross-check against `project_state.md`
     §8.x module tables
   - §3 (engineering architecture) — cross-check against `architecture_snapshot.md`
     §1 directory tree and layer structure
   - §4 (model implementations) — cross-check against `project_state.md` §3-4
   - §5 (data pipeline) — cross-check against `project_state.md` §5-6
   - §6 (validation) — cross-check against `project_state.md` §12
   - §7 (refactor history) — cross-check against `ai_system/version_registry.md` §5
     for missing R-events
   - §8 (future plans) — cross-check completed items against current state
   - Appendix A (file listings) — cross-check against actual directory contents
   - Appendix B (glossary) — cross-check for missing new terms introduced
     in recent refactors

**Constraints**:

- This is a **content staleness check**, not a bilingual parity check.
- If a document's `last_updated` is before the most recent
  `ai_system/version_registry.md` entry, it is likely stale.
- The drift report for standalone documents should enumerate **which specific
  sections** are stale, with the authoritative source for the correct value.

### Derived Document Staleness Check — REMOVED (2026-07-20)

> **已移除**：`workflow_reference_manual.md` (EN+ZH) 已于 2026-07-20 删除。
> `workflow_index.md` 是工作流信息的充分查阅入口，不再需要派生参考手册。
> 此 staleness check 无剩余目标，已移除。

### Directory Tree Syntax Validation

For every document (EN, ZH, or standalone) that contains an ASCII directory tree
(lines containing `├──`, `└──`, `│`), validate tree well-formedness:

1. **Connector correctness**:
   - `├──` (tee) = "there are more siblings after this entry"
   - `└──` (corner) = "this is the last sibling at this level"
   - After a `└──` at depth D, no further `├──` or `└──` entries may
     appear at the same depth D
   - `│` (vertical continuation) must continue through all entries at depth D
     until the `└──` entry at that depth

2. **Indentation consistency**:
   - All entries at the same depth must use the same indentation width
     (typically 4 spaces per level)
   - A `└──` entry's children must be indented one level deeper than
     the `└──` marker

3. **Common bug pattern** — new entry inserted after the last entry:
   ```
   │   └── eos_parametric/          ← declares "I am last"
   │       ├── src/
   │       └── tests/
   │   ├── eos_rmf/                 ← ERROR: sibling after └──
   ```
   The executor must flag this and fix the connectors: change the former
   last-entry to `├──`, and ensure only the true last entry uses `└──`.

4. **Drift classification**:
   - Flag tree syntax errors as `Critical` — they produce a directory structure
     that cannot exist on disk (a last-child cannot have successors).
   - Fix alongside any other Phase 3 edits to the same file.

Do NOT scan unrelated documentation.

STOP after completion.

---

# PHASE 1a — Session Report Consumption (Optional)

**Trigger**: When `records/reports/` contains session reports
(`category: session_report`) dated after the last `documentation_update_workflow`
execution recorded in `ai_system/version_registry.md`.版本目录以 `ai_system/version_registry.md` 当前版本为准——勿硬编码 v0.1.0。

**Purpose**: Session reports capture operational context — what was done,
what broke, what was left unfinished — that the filesystem scan (Phase 1)
cannot detect. Consuming them prevents repeats of known mistakes and
surfaces undocumented residual risks.

**Operations**:

1. List `records/reports/` and filter by:
   - `category: session_report` in frontmatter
   - `date` > last `documentation_update_workflow` entry in `ai_system/version_registry.md`

2. For each matching report, extract:

   **A. Residual Risk Targets** (from `§3.X 剩余风险` or `§3.3 剩余风险`):
   - Files listed as "未触及" (untouched) → add to Phase 2 update plan with
     notation `[Journal-derived: residual risk]`
   - These are files that the previous session intentionally skipped but
     that may still need updates

   **B. Known Pitfalls** (from `§2 遇到的问题与解决方法`):
   - Extract the specific technical traps (e.g., "tree connector conflict",
     "section renumbering cascade") → add as `⚠️ Pitfall` annotations to
     the relevant Phase 3 execution steps
   - This prevents the same mistakes from being repeated in the current session

   **C. Suggested Follow-ups** (from `§5 后续建议`):
   - Extract actionable items → append to Phase 2 plan as optional P3 items
   - Mark as `[Journal-suggested]` with lower priority than Phase 1 detected items

3. Merge Journal-derived items into the Phase 2 plan:
   - `[Journal-derived: residual risk]` items inherit the priority of their
     parent document section
   - `[Journal-suggested]` items default to P3, upgradeable if they match
     Phase 1 detected changes

**Constraints**:

- Session reports are operational logs, not authoritative — always verify
  disk state before executing any Journal-derived update
- If a session report's `§3` residual risk file no longer exists on disk,
  drop it silently (the risk was resolved in a subsequent session)
- This phase is optional: skip if no new session reports since last execution

---

# PHASE 2 — Incremental Update Plan

Generate:

# Documentation Delta Plan

For EACH affected file:

- sections to update
- obsolete sections
- required new sections
- required link updates
- frontmatter fields to update (`last_updated`)

Include:

- Documentation files
- ai_context updates
- workflow updates

Do NOT rewrite unaffected sections.

**records/index.md affected**:
- If new Journal reports/proposals exist without corresponding index entries,
  delegate to `journal_index_audit_workflow` (Phase 2 — Archive Table Audit).
- Mark as: `[Delegate: journal_index_audit_workflow]`
- Do NOT attempt incremental edits to index.md archive tables directly —
  the audit workflow is the single authority for archive table consistency.
- The memo table (工作备忘录) is updated by project_engineering_assessment_workflow
  — this workflow does NOT write to the memo table.

STOP after completion.

---

# PHASE 3 — Incremental Documentation Update

Update ONLY affected sections.

Requirements:

- preserve structure
- preserve formatting
- preserve naming conventions
- avoid duplicate descriptions
- remove obsolete content
- preserve internal links
- update frontmatter `last_updated` in each modified file

STOP after completion.

### §3a — Document Version Number Increment

After ALL content edits for this run are complete, for EACH file that was
actually modified (not just scanned), increment its version numbers:

1. **Single-document level** (`doc_version`):
   - Read the current `doc_version` frontmatter value (format: `dv-M.m.p`)
   - Increment `p` (PATCH): `dv-M.m.p` → `dv-M.m.(p+1)`
   - If the file doesn't have `doc_version` yet → add `doc_version: "dv-<current_major>.0.0"`
     (aligned to current `document_version` MAJOR) and set `p=0`

2. **System level** (`document_version`):
   - If ≥1 file received a `doc_version` PATCH increment in this run:
     - Read `document_version` from `ai_system/version_registry.md` §2 (e.g., `docs-2.0`)
     - Increment the PATCH digit: `docs-2.0` → `docs-2.1`
     - Update `document_version` in ALL files that were modified in this run
       (NOT all 15 docs — only those touched)
     - Update `ai_system/version_registry.md` §2 `docs (体系)` version and `Last Updated`
   - If only `last_updated` was changed without content changes → skip

3. **Cross-document consistency**:
   - All files modified in the same run share the same `document_version` value
   - The `doc_version.m` of each modified file must equal the new `document_version.m`
   - Example: if `document_version` goes `docs-2.0` → `docs-2.1`, then
     `architecture.md` `dv-2.0.3` → `dv-2.1.4` (m syncs to 2.1, p still increments independently)

4. **Record in execution report**:
   - List each modified file with old → new `doc_version`
   - Record system `document_version` old → new

STOP after completion.

### §3b — Body Metadata Synchronization

After §3a version number increment is complete, for EACH file modified in this run,
synchronize the **human-readable body preamble metadata** with the frontmatter values.

**Why this exists**: Phase 3 frontmatter updates (`last_updated`, `doc_version`) only
touch the YAML header. The body preamble (the `> **最后更新**:` / `> **Version**:` lines
immediately after the title) is separately authored and can drift. This subsection
closes that gap — every frontmatter change that affects a body-visible field MUST be
propagated to the body preamble.

#### §3b.1 — Scan for body metadata lines

For each modified file, read the body preamble (the ~20 lines between the closing `---`
of the frontmatter and the first `---` horizontal rule or `##` section heading).

Identify these patterns (language-dependent):

| Language | Date pattern | Version pattern |
|----------|-------------|----------------|
| ZH (`language: "zh"`) | `> **最后更新**: <date>` or `**日期**: <date>` | `> **版本**: <value>` or `**版本**: <value>` |
| EN (`language: "en"`) | `> **Last updated**: <date>` | `> **Version**: <value>` |

#### §3b.2 — Synchronize date

For each identified date line in the body preamble:
- Read the frontmatter `last_updated` value
- If the body date ≠ frontmatter `last_updated` → update body date to match frontmatter
- If no date line exists in the body → add `> **最后更新**: <frontmatter_last_updated>` (ZH)
  or `> **Last updated**: <frontmatter_last_updated>` (EN) in the preamble block

#### §3b.3 — Synchronize version

For each file modified in this run:
- Read the frontmatter `doc_version` value (set/updated in §3a)
- If a version line exists in the body preamble → update it to `dv-X.Y.Z`
- If NO version line exists → add one:
  - ZH: `> **版本**: <doc_version>`
  - EN: `> **Version**: <doc_version>`
  - Place the version line after the date line (or after the last existing preamble metadata line)

#### §3b.4 — Placement conventions

When adding missing lines, follow the existing preamble structure of the file:
- Blockquote-style preamble (`>` lines): add new lines in the same block, after the
  last existing metadata line, before the closing blank line
- Bold-label style preamble (`**Label**: value`): add new lines in the same style,
  after the last existing metadata line
- Maintain one blank line between the preamble block and the `---` horizontal rule

#### §3b.5 — Record in execution report

List each file with body metadata changes:
- `<file>: body date <old> → <new>` (if date was updated)
- `<file>: body version <old> → <new>` (if version was updated or added)
- `<file>: body version line added: dv-X.Y.Z` (if version was missing)

STOP after completion.

### §3c — Workflow Version-Registry Sync (🆕 wf-1.11)

After all other Phase 3 edits are complete, detect workflow version bumps
from `git diff` and automatically sync `ai_system/version_registry.md` §2.

**Why this exists**: CI failures (G4: `ai_system/version_registry.md` mismatch) recur because
the manual registry update step is forgotten after every workflow version bump.
Automatic sync eliminates the human-error gap.

#### §3c.1 — Detect workflow version bumps

Scan `git diff --name-only -- ai_system/workflows/` for modified files.
For each, parse the frontmatter:

```
（🔴 2026-08-31 退役：工作流文件级版本号 `workflow_version` 已废除——不再读 frontmatter 版本、不再检测「版本 bump」，仅按文件是否变更判定是否承接漂移）
```

If `old_version ≠ new_version` → a version bump occurred. Record:
```yaml
bumps:
    old_version: "wf-1.19"
    new_version: "wf-1.20"
    changelog_summary: "<first sentence of changelog>"
```

#### §3c.2 — Update ai_system/version_registry.md §2

For each detected bump, update the §2 table rows:

**Step 1 — Update old version row**:
- Find row matching `— 其中 <old_version> 文件`
- Decrement `文件` count by 1
- If count becomes 0 → set `Last Updated` to `—`, set `Notes` to
  `(<workflow_name> 已升至 <new_version>)`
- If count > 0 → remove `<workflow_name>` from the Notes description,
  update the count

**Step 2 — Update new version row**:
- Find or create row matching `— 其中 <new_version> 文件`
- If row exists:
  - Increment `文件` count by 1
  - Append `<workflow_name> (<old_version>→<new_version>: <changelog_summary>)`
    to the Notes column
  - Update `Last Updated` to today
- If row does NOT exist:
  - Insert new row in version-descending order position:
    ```
    | — 其中 <new_version> 文件 | 1 个 | <today> | <workflow_name> (<old_version>→<new_version>: <changelog_summary>) |
    ```
  - Rows are sorted by version (newer versions first, within same major.minor block)

**Row ordering rule**: New rows are inserted after the last entry with
a higher version number and before the first entry with a lower version number.

#### §3c.3 — Verify with check_workflows.py

After all rows are updated:

```bash
python ai_system/validation/check_workflows.py --quiet
```

Exit code 0 → ✅ sync complete.
Exit code ≠ 0 → 🔴 G4 FAIL → re-read ai_system/version_registry.md, fix the mismatch, re-verify.

This verification step MUST pass before proceeding. Max 2 retry attempts.

#### §3c.4 — Record in execution report

For each synced bump:
```
<workflow_name>: <old_version>→<new_version>
  ai_system/version_registry.md: <old_version> row (N→N-1), <new_version> row (M→M+1)
  check_workflows.py G4: PASS
```

STOP after completion.

---

# PHASE 4 — AI Context Delta Update

This is the ONLY workflow authorized to perform incremental
updates to ai_context files. Full-project sync delegates
ai_context writes here.

## Scope

This phase handles **descriptive** ai_context updates:
- Refining module descriptions
- Adding missing sections
- Updating status fields
- Fixing broken cross-references

It does NOT handle **structural** ai_context registration (new module
entries, new slot creation in registries). Structural updates are
delegated to `full_ai_context_update` when `full_project_sync_workflow`
detects the need.

## 4a — Pre-check: detect pre-updated files

For EACH ai_context file in the Change Impact Report:
- Read the file's frontmatter `last_updated` field.
- If `last_updated` is today's date:
  - Skip this file.
  - Record in the execution report: "Pre-updated by [source workflow]"
  - Do NOT overwrite.
- If `last_updated` is older than today:
  - Proceed to §4b (incremental write).

## 4b — Mutual exclusion check

Before writing to any ai_context file, verify:
- full_project_sync_workflow is not currently executing
- No other workflow holds an ai_context write lock
- (This is a runtime check — the executor must confirm before proceeding.)

### §4b.1 — Compound Delegation Check

Verify the current delegation does not violate the Compound Delegation Rule:
- If the delegation contains both structural and descriptive changes → REJECT, require splitting
- If descriptive-incremental only → PASS, continue to §4c

## 4c — Incremental write

Update ONLY affected ai_context files.

Possible files include:

- context/project_state.md
- context/architecture_snapshot.md
- context/module_index.md
- context/notebook_registry.md
- context/validation_registry.md
- context/eos_pipeline.md
- context/refactor_history.md

Update ONLY changed sections.

Avoid full-file rewrite.

STOP after completion.

## 4d — Version Registry Consistency Check（🔴 已退役 2026-08-31）

工作流**文件级版本号**（`workflow_version`）与 `version_registry.md` §2 分桶行已退役，
原「按版本分桶计数 + 与 §2 对账 + 孤儿行自动修复」步骤随之下线。
工作流一致性由 `check_workflows.py` G1/G2/G5/G6（格式 / last_updated / 交叉引用 / 废弃一致性）兜底，
不再维护任何版本分桶计数。

5. **Report**: List all corrections made to §2 in the execution report.

This check is MANDATORY — do NOT skip even if no AI context files
were modified in this run. Registry drift is a recurring Critical
issue (5 consecutive audits).

---

# PHASE 5 — Consistency Validation

Generate:

# Documentation Consistency Report

Check ONLY impacted areas for:

- broken links
- outdated names
- terminology mismatch
- standalone document vs. project-state consistency
- derived document vs. source-file consistency (derived docs only)
- outdated workflow references
- duplicate descriptions
- frontmatter validity (all docs files have valid YAML frontmatter)
- frontmatter `last_updated` reflects actual changes
- **Body metadata consistency**: For EVERY file modified in this run, verify
  that body preamble metadata matches frontmatter values:
  - Body date line (`> **最后更新**:` / `> **Last updated**:` / `**日期**:`)
    must match frontmatter `last_updated`
  - Body version line (`> **版本**:` / `> **Version**:` / `**版本**:`)
    must match frontmatter `doc_version`
  - If either is missing, flag as `Medium — body metadata missing` and
    add during verification (do not defer)
  - If either is stale, flag as `High — body/frontmatter metadata divergence`
    and update in-place
- **ASCII directory tree well-formedness**: for any document containing tree
  diagrams, validate connector correctness (`├──`/`└──`/`│`) and indentation
  consistency per Phase 1 §Directory Tree Syntax Validation rules

Then generate:

# Final Documentation Delta Summary

STOP after completion.