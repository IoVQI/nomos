---
project_version: "0.9.0"
language: "en"
last_updated: "2026-09-22"
compatible_project_version: ">= 0.1.0"
category: "ai_workflow"
tags: [github, push, sync, release, ci, git, commits-ahead]
purpose: "安全地将累积的本地变更经闸门检查与 CI 就绪验证后提交并推送至 GitHub"
changelog: "2026-09-22 (#264): 检查表第 7 行的作用域注记——该行**忠实复刻 CI 那一步**（步骤名与命令同步改为 `Verify references transcription markdown (--all = references/ only)`），**不是**「全仓 markdown 闸门」：`--all` 只扫 references/ 下 `_extracted_text.md`。要校验别的树传目录。; 2026-09-14 (文件级版本号已退役，改日期标记): Phase 2 由「3 条 Light 检查」升级为「CI 等价全量预演」（2a 逐条跑 CI fast-tests 的 10 条一致性命令；2d 退出条件与 2e 失败处理同步改为默认阻断 + 显式放行）；边界：不覆盖闸门侧环境等价性（另由 check_references G10 修复，见同批方案）。; wf-2.5: +推送提示阀门 — Trigger 对齐 commits_ahead ≥ 5（替换模糊「约 1 周」时间启发式），与 CLAUDE.md step 6 同一阀门；方案: git 推送提示阀门方案。; wf-2.4: Phase 0d Step 1.5 瞬时失败重试——连接失败（443 timeout/Connection refused/Could not connect）先重试 2 次（间隔 5s）再判定不可达（2026-08-16 实证瞬时 443 抖动，重试即成功）；0g 失败处理同步（重试→切协议→阻断三级）。; wf-2.3: Phase 3d commit convention aligned to CLAUDE.md type(scope): 中文摘要 (≤72 chars) — removed legacy Chinese-colon prefixes (新增:/修复:/ etc.); 3f exit criteria synced (2026-08-06).; wf-2.2: Phase 0e added — non-blocking version eligibility freshness check before push (reminder if >7 days + ≥3 sessions since last check).; wf-2.1: Initial documented version."
execution_mode: strict  # strict | normal
# strict 模式下：每个 Phase 必须在上一 Phase 所有退出条件满足后才能进入
# 闸门判定必须基于实际命令输出（禁止"推断"通过）
# 连续 3 次同一 Phase 失败 → 🔴 阻断，写入 proposals/ 请求用户介入
# 例外：Phase 0 secrets scan 发现命中 → 即时阻断，不适用 max_retry_per_phase
completion_marker: "🔴 CHAIN_COMPLETE"
max_retry_per_phase: 3
---

# GitHub Push Workflow

Prepare accumulated local changes for a safe push to GitHub and execute the push.
Designed for the "update weekly, push when ready" cadence — handles days of
accumulated commits, uncommitted work, and ensures CI-readiness before push.

Remote (dev, private): `origin` → `https://github.com/IoVQI/nomos-dev.git` (HTTPS)
Remote (public release): `https://github.com/IoVQI/nomos.git` — pushed **only** from the release repo
Fallback: `https://github.com/IoVQI/nomos-dev.git` (HTTPS)
Branch: `main`
CI: `.github/workflows/test.yml` (3 jobs: fast-tests → slow-tests + solver-regression)

Trigger:
- User: "push to GitHub", "push", "sync to GitHub", "upload to GitHub"
- ~~commits_ahead ≥ 5（会话结束提示阀门）~~ 🔴 已随 CLAUDE.md「结束时自动提议 commit」step 6 退役（2026-08-31）——未显式要求 push 时不主动询问
- Before sharing results with collaborators

## Push Mode vs Sync Mode

| Mode | User says | What it does |
|------|-----------|--------------|
| **Push only** | "push to GitHub", "push" | Push existing local commits; leave uncommitted changes as-is |
| **Full sync** | "sync to GitHub", "upload to GitHub" | Commit ALL uncommitted changes (with review), then push |

This workflow covers BOTH modes. In push-only mode, Phase 3 (commit) is skipped.
In sync mode, all phases execute.

Principles:
- NEVER skip hooks (--no-verify, --no-gpg-sign)
- NEVER force push to main
- ALWAYS review what will be pushed before pushing
- ALWAYS check for secrets and large files before pushing
- NEVER amend published commits

---

# PHASE 0 — Safety Gate (Pre-Audit)

Run these checks FIRST. Any failure MUST be resolved before proceeding.

## 0a — Secrets scan

Scan all changed files for common secret patterns:

- `password`, `secret`, `token`, `api_key`, `API_KEY`
- `.env` files (should be in .gitignore)
- `credentials.json`, `service-account.json`
- Hardcoded tokens in source files

Command（含未追踪文件——`git ls-files --others` 覆盖新建凭据文件，防止 secret 穿过闸门）:
```bash
{ git diff --name-only HEAD; git ls-files --others --exclude-standard; } | xargs grep -n -E \
  '["'"'"']?(password|secret|token|api_key|API_KEY|PASSWORD|SECRET|TOKEN|credentials|CREDENTIALS)["'"'"']?\s*[:=]\s*["'"'"']?[A-Za-z0-9_-]{8,}' 2>/dev/null
```

If ANY match: STOP. Report the file and line. Do NOT proceed.
The user must remove secrets before pushing.

## 0b — Large file scan

Check for files > 10 MB that are not in .gitignore:

```bash
# 只扫「将推送的已跟踪对象」（committed-ahead + staged）——与 Phase 0a 同作用域。
# 🔴 2026-09-15 实证：原实现 `find . -type f -size +10M` 是全库遍历，在 Git Bash 下 120s 未返回
# 而被移入后台（它要遍历 external/、worktrees/ 等大目录）；且**未跟踪文件根本不会进 push**，
# 扫它们既慢又与「这个 push 会不会带大文件」的语义无关。
# `-z` + `read -d ''` 是为让**非 ASCII 路径**不被 git 的引号/八进制转义破坏（本仓有中文文件名）。
{ git diff --name-only -z origin/main..HEAD 2>/dev/null; git diff --cached --name-only -z 2>/dev/null; } \
  | while IFS= read -r -d '' f; do
      [ -f "$f" ] || continue
      sz=$(wc -c < "$f" 2>/dev/null || echo 0)
      [ "$sz" -gt 10485760 ] && echo "  $((sz/1048576))MB  $f"
    done
echo "  (以上为命中；空 = 无 >10MB 文件)"
```

If any found: Warn the user. Large files bloat the repo and may exceed GitHub's
100 MB file size limit. Suggest adding to .gitignore or using Git LFS.

## 0c — Git config check

Verify required git config is set:

```bash
git config user.name
git config user.email
```

If empty: STOP. Configure first:
```bash
git config user.name "IoVQI"
git config user.email "<email>"
```

## 0d — Remote & Auth Check

Verify remote URL and connectivity. Test both SSH and HTTPS — network
firewalls may block one but not the other.

```bash
git remote -v
```

**Step 1 — Try current remote:**
```bash
git ls-remote --heads origin 2>&1
```

**Step 1.5 — 瞬时失败重试（🆕 wf-2.4，2026-08-16）:**

> 🔴 连接失败（`Failed to connect ... port 443`、`Connection refused`、`Could not connect`）**先重试 2 次**（间隔 ~5s），
> 确认持续失败才判定「不可达」。2026-08-16 实证：github.com push 瞬时 443 超时，重试即成功——
> 一次性失败 ≠ 阻断，避免误停。

```bash
# 重试：首次失败后等 5s 重试，至多重试 2 次
for i in 1 2; do git ls-remote --heads origin 2>&1 && break; sleep 5; done
```

> 持续失败（重试 2 次后仍失败）→ 进入 Step 2 症状排查（区分 403 凭据 / 防火墙 / DNS 等）。

**Step 2 — If blocked (connection abort / timeout):**

| Symptom | Likely cause | Action |
|---------|-------------|--------|
| `kex_exchange_identification: Connection aborted` (SSH) | Firewall blocking port 22 | Try SSH over 443: `ssh -T -p 443 git@ssh.github.com`. If also blocked → switch to HTTPS |
| `403` (HTTPS) | Expired credentials | Switch to SSH, or update PAT token |
| `Connection refused` | Network down | Check VPN/proxy, retry |
| `Could not resolve host` | DNS issue | Check internet connection |

**Step 3 — Switch protocol if needed:**
```bash
# To SSH:
git remote set-url origin git@github.com:IoVQI/nomos-dev.git
# To HTTPS:
git remote set-url origin https://github.com/IoVQI/nomos-dev.git
```

**Step 4 — Verify after switch:**
```bash
git ls-remote --heads origin 2>&1
```

If BOTH protocols fail: STOP. Check network, VPN, or firewall settings.

---

## 0e — Version eligibility freshness check（🔴 已退役 2026-08-31）

> **本节已失效，执行时跳过**：`version_bump_eligibility_workflow` 已于 2026-08-31
> 标记 `status: deprecated`（方案 2026-08-31_废弃工作流版本控制与Journal计数设施方案）；
> 版本升级改由 git tag + 人工决策。以下步骤保留供回滚参考，不再执行。

Check whether a version bump eligibility assessment is overdue. This is
a **non-blocking** reminder — it does not prevent push.

### Step 1 — Find last eligibility check date

Look for the most recent eligibility report in
`records/reports/` (files matching
`*版本升级资格判定报告*`).

If no report found → eligibility has never run. Remind:
`⚠️ 从未执行过版本升级资格检查。建议在下次会话中运行 version_bump_eligibility_workflow。`

### Step 2 — Evaluate freshness

If the most recent report is >7 days old:

Count session reports in `records/sessions/` with
date > last eligibility report date.

If ≥3 sessions since last check:
```
⚠️ 距上次版本升级资格检查已 {N} 天（{M} 个会话）。
建议在 push 完成后运行 version_bump_eligibility_workflow。
当前版本: {current_version}（自 {last_bump_date} 起）
```

If <3 sessions or ≤7 days → no reminder.

### Step 3 — Record for session report

If a reminder was shown, note it for the session report:
`Push 前 eligibility 到期提醒已显示（上次检查: {date}, {N} 天前）`

### Constraints

- This check is **non-blocking** — push proceeds regardless.
- If the check itself fails (e.g., can't list report directory),
  log a warning and continue — never block push on eligibility infra failure.
- The reminder is shown once per push, not per commit.

### 0f 退出条件（🔴 必须全部满足方可进入 Phase 1）

- [ ] 0a secrets scan 已执行
  - [ ] 若 0 命中 → ✅ 通过
  - [ ] 若 ≥1 命中 → 🔴 **即时阻断**，报告文件和行号，**不适用 max_retry_per_phase**
- [ ] 0b large file scan 已执行
  - [ ] 若 0 命中 → ✅ 通过
  - [ ] 若 ≥1 命中 → ⚠️ 警告用户，建议 .gitignore/LFS（非阻断，用户确认后继续）
- [ ] 0c git config 已检查（user.name + user.email 非空）
- [ ] 0d remote 可达（SSH 或 HTTPS 至少一个可用）
- [x] ~~0e version eligibility 已检查~~ —— 🔴 0e 已退役（2026-08-31），本项自动满足，无需执行

### 0g 失败处理（🔴 不得跳过）

- secrets scan 发现命中 → 🔴 **立即阻断**，不重试。原因：secrets 不会因重试消失
- git config 缺失 → 🔴 阻断，提示配置命令。用户配置后手动重试（不消耗 max_retry_per_phase）
- remote 不可达 → **先重试 2 次（瞬时抖动排查，Phase 0d Step 1.5）**；持续失败 → 尝试切换协议（SSH↔HTTPS）；均不可达 → 🔴 阻断
- 不得以「看起来没有 secrets」为由跳过实际扫描

---

# PHASE 1 — Change Inventory

Build a complete picture of what will be pushed.

## 1a — Commits ahead of origin

List all local commits not yet on origin/main:

```bash
git log origin/main..HEAD --oneline
```

If this returns nothing, no commits to push — skip to checking uncommitted changes.

## 1b — Uncommitted changes

```bash
git status
git diff --stat
git diff --cached --stat
```

Categorize each changed file:

| Category | Signal | Action |
|----------|--------|--------|
| **Source code** | `*.py` in `lab/` | Ensure tests pass |
| **Docs** | `lab/docs/*.md` | Check docs consistency |
| **AI context** | `context/*.md` | Verify no stale refs |
| **Workflows** | `workflows/*.md` | Update workflow_index.md |
| **Config** | `lab/config/*.py`, `.github/*` | Review carefully |
| **Data** | `data_kb/**` | Check .gitignore coverage |
| **Journal** | `records/**` | OK to commit directly |
| **Sandbox** | `sandbox/**` | Check for output files |
| **Untracked** | `??` in git status | Decide: add or gitignore |

## 1c — Deletion review

Check for staged deletions (`D` in git status):

- Accidental deletions: restore with `git restore --staged <file>`
- Intentional renames: ensure git detected as rename, not delete+add
- Data file deletions: confirm these were moved/relocated, not lost

### 1d 退出条件（🔴 必须全部满足方可进入 Phase 2）

- [ ] 1a: 所有 local commits 已列出（`git log origin/main..HEAD --oneline`）
- [ ] 1b: 所有 changed/untracked 文件已按类别分类
- [ ] 1c: 所有 staged deletions 已审核（无意外删除）
- [ ] Push-only 模式：检查完毕即可进入 Phase 2（跳过 Phase 3 Commit）

### 1e 失败处理（🔴 不得跳过）

- `git log` 或 `git status` 命令失败 → 🔴 阻断，检查 git 仓库状态
- 未分类文件 → 标记为 `Other`，不阻断

---

# PHASE 2 — CI Readiness Check（2026-09-14 起：**CI 等价全量预演**）

> 🔴 **本阶段的判定基准是 CI**：跑一遍 `.github/workflows/test.yml` 的 fast-tests 里那 **10 条一致性命令**，
> 任一条非 0 退出即阻断（见 2e）。改动理由与实证见方案
> `proposals/2026/09/14/2026-09-14_推送前CI等价预演方案.md` §1.4。
>
> ⚠️ **已知边界**：本预演读的是**本地工作树**，故抓不到「闸门读开发机磁盘」这一类不等价
> （例：`check_references.py` 其余 8 处 `os.walk`、G10 内 `os.path.isdir` 的兜底分支）。
> 该类的修法在闸门侧，不在本阶段。

## 2a — CI 等价全量预演（10 条一致性命令）

**做什么**：逐条跑 CI fast-tests 实际执行的一致性命令（**真值 = 下表行数，不在此写死计数**），
**收集退出码**（不因首条失败而中断，以便一次看全部红色项）。`pip install` 与 `pytest` 不计入（非一致性 check）。

🔴 **工作目录**：test.yml 的 fast-tests 设 `defaults.run.working-directory: lab`；下表已把路径折算为**仓库根**下的写法，可在根目录直接跑。

| # | CI 步骤名 | 命令（仓库根下） |
|:--:|------|------|
| 1 | Check references/ consistency | `python lab/validation/check_references.py --skip-g4 --skip-g5 --skip-g7 --quiet` |
| 2 | Check workflows/ consistency | `python ai_system/validation/check_workflows.py --quiet` |
| 3 | Check derivation_kb consistency | `python derivation_kb/_meta/check_kb.py` |
| 4 | Check data_kb consistency | `python data_kb/_meta/check_data_kb.py` |
| 5 | Check lab code compliance | `python lab/validation/check_eos_code.py` |
| 6 | Check domain_kb directions consistency | `python domain_kb/directions/_meta/check_directions.py` |
| 7 | Check domain_kb concepts consistency | `python domain_kb/concepts/_meta/check_concepts.py` |
| 8 | Verify references transcription markdown (--all = references/ only) | `python lab/validation/verify_md_syntax.py --all` |
| 9 | Check sandbox/ layout & git discipline | `python ai_system/validation/check_sandbox_layout.py --quiet` |
| 10 | Check memos/ ledger consistency | `python ai_system/validation/check_memos.py --quiet` |
| 11 | Check official_docs mirror registry | `python ai_system/validation/check_official_docs.py --check-frontmatter --quiet` |

**为什么是这一套**（不是「另加一套检查」）：pre-commit 的钩子**各带 `files:` 条件**，只在本批改动命中该域时才跑；
而 CI 无条件全跑。两者**触发条件不等价** ⇒ 本批没碰的域的既有缺陷本地不可见。
本步用「无条件跑 CI 的确切集合」把这一差异消掉。

**边界**：本步**不能**替代闸门侧的环境等价性修复（见 Phase 2 标题下的边界注记）。

🔴 **第 7 行的作用域**（工作台账 #264）：`verify_md_syntax.py --all` 是 **references/ 专用**
（只扫该树下 `_extracted_text.md`）。此处**忠实复刻 CI 那一步**，**不是**「全仓 markdown 闸门」——
`FAIL 0` 对该命令未覆盖的树不构成覆盖证据。要校验别的树，传目录：
`python lab/validation/verify_md_syntax.py <dir>`（按 `**/*.md` 递归）。

## 2b — Markdown link check (quick)

For any modified .md files, verify internal links don't point to renamed files:

```bash
# Extract markdown links from changed .md files, verify targets exist
git diff --name-only HEAD | grep '\.md$' | while read f; do
  grep -oP '\[.*?\]\(\K[^)]+' "$f" | while read link; do
    # skip external URLs
    [[ "$link" =~ ^https?:// ]] && continue
    target="$(dirname "$f")/${link%%#*}"   # 剥离 #锚点 片段，避免合法锚点链接被误判 BROKEN
    [[ -e "$target" ]] || echo "BROKEN: $f -> $link"
  done
done
```

If broken links found: Fix them before pushing, or document as intentional.

## 2c — AI context consistency (light)

Check that recently modified code has its changes reflected in ai_context:

- If `**/src/*.py` was modified → check `project_state.md` §8 for module descriptions
- If modules were added/removed/renamed → check `module_index.md` for corresponding entries
- If workflow files were created/modified → check `workflow_index.md` is updated

This is a LIGHT check — not a full audit. For deep verification, run
`full_project_sync_workflow` separately.

### 2d 退出条件（🔴 必须全部满足方可进入 Phase 3）

- [ ] 2a: **CI 等价的 10 条一致性命令已逐条执行**，且全部退出码为 0（或失败项已按 2e 处置）
- [ ] 2b: 已修改 .md 文件的内部链接已检查（broken links 已修复或记录）
- [ ] 2c: ai_context 轻量一致性已检查（新增/重命名模块已反映在上下文中）

### 2e 失败处理（🔴 不得跳过）

- **2a 任一命令非 0 退出 → 🔴 默认阻断 push**：列出失败命令与关键输出，要求处置后再推。
  仅当用户**显式放行**（如已知预存失败 / 有意重组）方可继续，并须在会话内写明放行理由。
  ⚠️ 原措辞「警告不阻断」已废止——它正是「本地绿 / CI 红」得以流到 main 的直接原因（§1.2 三次实证）。
- Broken links 发现 → 修复后再进入 Phase 3；无法修复的标记为已知

---

# PHASE 3 — Commit (if needed)

**Skip this phase entirely** in **push-only 模式**（用户请求 "push" 而非 "sync"）——push-only 仅推送已存在的 commits/暂存内容，**绝不创建新 commit**（见 3f 出口 + Phase 3 标题「Commit (if needed)」）。

Only execute if:
- User requested **full sync**（提交 + 推送），且
- `git status` 显示有需提交的 staged/unstaged 变更

## 3a — Determine mode: Bulk or Selective

Count the changed files:

```bash
git status --short | wc -l
```

| File count | Mode | Approach |
|------------|------|----------|
| ≤ 20 files | **Selective** | Categorize each file, present to user, ask which to include (3b) |
| > 20 files | **Bulk** | Summarize by category, present high-level overview, `git add <精确路径>` with user confirmation (3c) |

When in bulk mode: the changeset is too large for per-file review. Show the
user a category-level summary (counts by directory/type) and get a single
approval to commit everything.

When in selective mode: present the categorized list and let the user choose
which files go into this commit.

## 3b — Selective mode: File-level review

Present the user with a categorized list of changed files and ask:

- Which files to include in this commit?
- Any files to leave uncommitted intentionally?
- Is this one commit or multiple?

## 3c — Bulk mode: Category-level summary

For large changesets, present a summary table:

```
BULK SYNC SUMMARY:
  Modified:  N files (src/, docs/, config/, ...)
  New:      N files (records/, src/, ...)
  Deleted:  N files (eos_literature/, ref/, ...)
  Renamed:  N files (validation/ → tests/)
```

Then ask: "Commit everything with a single message and push? (y/n)"

Use `git add <精确路径列表>` (extracted from Phase 1b change inventory) only after explicit user confirmation.
**🔴 Never use `git add -A`** — it would stage uncommitted changes from parallel sessions or other windows.

## 3d — Commit message

Review recent commit message style:

```bash
git log origin/main..HEAD --oneline  # already pushed commits
git log --oneline -5                  # overall style
```

Draft a commit message following CLAUDE.md §Commit message 模板 (single source of truth):
- Format: `type(scope): 中文摘要` — Chinese subject, ≤72 chars
- `type` ∈ {feat, fix, chore, refactor, docs}
- `scope`: 文献领域目录名 / deriv / journal / index / 文件名 / 目录名 / workflow / decommission / sync
- Body lists changed files by category (≤5 sub-operations with `+`, else summarize)
- 🔴 Do NOT use legacy Chinese-colon prefixes (`新增:`, `修复:`, etc.) — superseded by type(scope) per CLAUDE.md

Example format:
```
fix(workflow): 消费 memo #22 — 链12裁决trigger统一 + Tier2.5代码实现

- 修复链 12 类型矛盾：catalog ct-1.9 + chain_orchestration wf-2.13 Rule 3b 续跑建议
- 实现 pdf_sources.py Tier 2.5（_KNOWN_OA_JOURNALS + try_journal_website）
```

## 3e — Create the commit

**Selective mode:**
```bash
git add <specific files>
git commit -m "$(cat <<'EOF'
<commit message>
EOF
)"
```

**Bulk mode (after user confirmation):**
```bash
# 精确路径模式：从 Phase 1 变更清单提取文件列表，禁止 git add -A
git add <file1> <file2> ...  # 仅包含 Phase 1b 分类清单中的文件
git commit -m "$(cat <<'EOF'
chore(sync): 本地 . 完整状态同步至 GitHub

- <category1>: <summary>
- <category2>: <summary>
EOF
)"
```

If the commit fails due to a pre-commit hook:
1. Read the hook error output
2. Fix the issue
3. Stage the fix and create a NEW commit (never use --amend unless the user
   explicitly asks)

### 3f 退出条件（🔴 必须全部满足方可进入 Phase 4）

- [ ] Push-only 模式 → Phase 3 不执行，直接进入 Phase 4
- [ ] Sync 模式：commit 已创建（`git add` + `git commit` 已执行）
- [ ] Commit message 符合 CLAUDE.md 约定（`type(scope): 中文摘要`，subject ≤72 chars）
- [ ] 已确认无 secrets 或大文件被意外 staged

### 3g 失败处理（🔴 不得跳过）

- Pre-commit hook 失败 → 修复问题后重新 commit；不得使用 --no-verify
- Commit message 格式检查 → ⚠️ 提醒但允许继续

---

# PHASE 4 — Push

## 4a — Final confirmation

**CRITICAL**: Always display a push summary and wait for explicit user
confirmation before executing the push. Never skip this step.

Display a push summary to the user:

```
========== PUSH SUMMARY ==========
Branch: main
Remote: <current remote URL>
Commits to push: N
  - <short-hash> <subject>
  - <short-hash> <subject>
Files changed: N  (+X / -Y lines in working copy if sync mode)
New files: [category summary]
Deleted files: [category summary]
CI will run: fast-tests → slow-tests + solver-regression
=================================
Proceed with push? (y/n)
```

Wait for explicit user confirmation before proceeding. If the user says no,
stop — do not push. Let the user decide what to change.

## 4b — Execute push

```bash
git push origin main
```

Never use `--force`. If push is rejected:
- `non-fast-forward`: Remote has commits you don't have. Run `git fetch origin && git log origin/main..HEAD && git log HEAD..origin/main`. Discuss with user whether to pull/rebase.
- `GH006`: Branch protection. Discuss with user.
- Authentication failure: Check credential helper or personal access token.

## 4c — Verify push success

```bash
# Confirm local HEAD matches remote
git log origin/main..HEAD --oneline  # should return nothing
```

### 4d 退出条件（🔴 必须全部满足方可进入 Phase 5）

- [ ] 4a: 推送摘要已展示给用户且已获得显式确认
- [ ] 4b: `git push origin main` 已执行且成功
- [ ] 4c: `git log origin/main..HEAD --oneline` 返回空（确认推送成功）
- [ ] 未使用 `--force`

### 4e 失败处理（🔴 不得跳过）

- Push rejected (non-fast-forward) → `git fetch && git log` 分析差异，与用户讨论 pull/rebase
- Authentication failure → 检查 credential helper / PAT token
- Push 超时 → 重试 1 次（消耗 max_retry_per_phase）；仍失败 → 🔴 阻断

---

# PHASE 5 — Post-Push

## 5a — CI monitoring (optional)

The CI pipeline runs automatically on push to main:
- `fast-tests`: pytest (projects/, excluding phase5_verification.py)
- `slow-tests`: pytest with --run-slow
- `solver-regression`: solver regression + tidal regression + rotation regression + analytic benchmarks + literature benchmarks + inline literature metadata sanity check

To check CI status:
```bash
gh run list --branch main --limit 3
gh run watch <run-id>
```

Report CI status to user. If any job fails:
- Read the failure log (`gh run view <run-id> --log`)
- Identify whether it's a pre-existing issue or caused by this push
- If caused by this push: prepare a fix commit

## 5b — Tag (if significant milestone)

If this push represents a significant milestone (paper version, major feature, release):
```bash
git tag -a v<version> -m "<description>"
git push origin v<version>
```

Don't tag routine weekly syncs — only meaningful checkpoints.

### 5c 退出条件（🔴 必须全部满足方可进入 Phase 6）

- [ ] 5a: CI 状态已报告（若 gh CLI 可用）
- [ ] 5b: 若为里程碑推送 → tag 已创建并推送；否则跳过
- [ ] CI 失败（若有）→ 已确认是预存问题还是本次推送引入

### 5d 失败处理（🔴 不得跳过）

- CI 发现本次推送引入的失败 → 准备 fix commit，不阻断（post-push 阶段）
- `gh` CLI 不可用 → 跳过 CI 监控，不阻断

---

# PHASE 6 — Cleanup & Record

## 6a — Sync ai_context (if needed)

If PHASE 1 changed ai_context files, verify:
- `cross_reference_map.md` counts are consistent with actual disk state
- `project_state.md` §8 directory tree matches reality
- `version_registry.md` document counts are accurate

## 6b — Update workflow_index.md (if needed)

If this session created or modified any workflows:
- The workflow_index.md entry should already be updated (see
  `documentation_update_workflow` Phase 3)
- Verify file count in §1 is correct
- Verify §2 registry table is complete

## 6c — Generate session report (if not already done)

If running at session end, invoke `/闭环本会话` to record the
push operation in the session report.

### 6d 退出条件（🔴 工作流终点）

- [ ] 6a: ai_context 文件已同步（若 Phase 1 有变更）
- [ ] 6b: workflow_index.md 已更新（若 Phase 1 有工作流变更）
- [ ] 6c: 会话报告已生成（若为会话结束时执行）

### 6e 失败处理（🔴 不得跳过）

- ai_context 同步冲突 → 标记待办，不阻断（推送已完成）
- workflow_index.md 计数不一致 → ⚠️ 提醒下次 check_workflows.py 验证（或 documentation_update 漂移检测）

🔴 CHAIN_COMPLETE

---

## Appendix A: Push Decision Flow

```
Start
  │
  ├── Phase 0: Safety Gate
  │     ├── Secrets found? ──→ STOP. Remove secrets.
  │     ├── Large files? ──→ Warn user, suggest .gitignore/LFS.
  │     ├── Git config missing? ──→ Configure.
  │     └── Remote unreachable?
  │           ├── Try alternate protocol (SSH ↔ HTTPS)
  │           ├── Try SSH over 443
  │           └── Both fail? ──→ STOP. Check network/VPN.
  │
  ├── Phase 1: Change Inventory
  │     ├── Review commits ahead of origin
  │     ├── Review uncommitted changes
  │     └── Review deletions
  │
  ├── Phase 2: CI Readiness
  │     ├── Verify CI paths match project structure
  │     ├── Check for broken markdown links
  │     └── Light ai_context consistency check
  │
  ├── Phase 3: Commit (SKIP if push-only mode)
  │     ├── Determine mode: >20 files? → Bulk / ≤20 → Selective
  │     ├── Selective: present categorized files, user picks
  │     ├── Bulk: present category summary, user says yes/no
  │     ├── Draft commit message
  │     └── Commit (never --amend, never --no-verify)
  │
  ├── Phase 4: Push
  │     ├── Display summary → **GET USER CONFIRMATION**
  │     ├── git push origin main
  │     └── Verify success (git log origin/main..HEAD --oneline)
  │
  └── Phase 5-6: Post-Push
        ├── Monitor CI (optional)
        ├── Tag (if milestone)
        └── Sync ai_context / generate session report
```

## Appendix B: Common Failure Modes

| Scenario | Cause | Fix |
|----------|-------|-----|
| SSH: `kex_exchange_identification: Connection aborted` | Firewall blocks port 22 | Switch to HTTPS, or try SSH over port 443 |
| HTTPS: `403` error | Expired PAT / credentials | Switch to SSH, or update PAT token |
| Both protocols blocked | Network firewall (e.g. GFW) | Configure proxy: `git config --global http.proxy http://127.0.0.1:<port>` |
| Push rejected: non-fast-forward | Someone else pushed to main | `git fetch && git pull --rebase origin main` |
| CI fails on fast-tests | Test broken by recent change | Fix test locally, commit, push again |
| CI fails on solver-regression | regression.py path changed | Update CI test.yml path |
| Large file accidentally staged | Forgot to add to .gitignore | `git reset HEAD <file>`, add to .gitignore, recommit |
| Secret committed in history | Accidentally committed .env | `git filter-branch` or `BFG Repo-Cleaner`; rotate the secret immediately |
| Pre-commit hook blocks commit | Hook detects an issue | Fix the issue; do NOT use --no-verify |
| merge conflict during pull | Local and remote diverged | Resolve conflicts, test, commit the merge |

## Appendix C: Project-Specific Notes

- **CI runs on push to main**: The `test.yml` workflow triggers automatically.
  No manual CI trigger needed after push.
- **Data directory reorganization** (2026-07-20, completed): `lab/data/`
  fully deprecated; all data migrated to `data_kb/`. CI does NOT depend on
  these files.
- **phase5_verification.py**: Has hardcoded absolute paths (`./…`).
  It is correctly excluded from CI (`--ignore=`). It will always fail on CI
  by design.
- **solver/validation/**: Contains regression scripts that ARE run in CI.
  Do not rename this directory without updating `test.yml`.
- **Sandbox output**: Large output files (plots, PDFs) should be covered by
  `.gitignore`. Verify when new output directories are created.
- **Journal directory**: Contains session reports and execution reports. These
  are documentation, not code — safe to push.
