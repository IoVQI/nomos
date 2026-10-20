---
name: github-push
description: >
  Run git commit + push with pre-flight safety checks. Combines what was previously
  github-push-check + github-push-execute into a single streamlined flow.
  Triggers on "push", "commit and push", "推送", "提交并推送".
argument-hint: "[commit message]"
allowed-tools: Bash(git *) Bash(grep *) Bash(find *)
---

## GitHub Push — 安全提交并推送

执行 git commit + push，前置安全闸门 + 变更清单 + 用户确认。

### 执行流程

#### Step 1: 安全闸门（直接 bash，禁止 agent 包装）

```
cd ${CLAUDE_PROJECT_DIR}

echo "[1a] secrets 扫描（仅扫将被推送的已跟踪文件）"
# 1a. Secrets scan（权威安全闸门：ai_system/workflows/github_push_workflow.md Phase 0a——本 Skill 为薄封装，扫描范围须与之一致）
# 作用域收窄：只扫将被 push 的已跟踪文件（committed-ahead + staged）；不扫未跟踪（untracked 不入 push，避免拖入并行会话/临时大件导致 grep 挂起）
{ git diff --name-only origin/main..HEAD 2>/dev/null; git diff --cached --name-only 2>/dev/null; } \
  | grep --binary-files=without-match -n -E \
  '(password|secret|token|api_key|API_KEY|credentials)\s*=\s*["\'"'"'"][A-Za-z0-9_-]{8,}' 2>/dev/null || true

echo "[1b] 大文件扫描 (>10MB)"
# 1b. Large file scan（作用域与 1a 一致：只扫 committed-ahead + staged；权威定义见
#      github_push_workflow.md Phase 0b——改动本步须同批改那里，防两处漂移）
# 🔴 2026-09-15 实证：原 `find . -type f -size +10M` 全库遍历，Git Bash 下 120s 未返回（被移入后台），
# 且未跟踪文件不进 push。改为只扫将推送的文件：既快，又贴合语义。
{ git diff --name-only -z origin/main..HEAD 2>/dev/null; git diff --cached --name-only -z 2>/dev/null; } \
  | while IFS= read -r -d '' f; do
      [ -f "$f" ] || continue
      sz=$(wc -c < "$f" 2>/dev/null || echo 0)
      [ "$sz" -gt 10485760 ] && echo "  $((sz/1048576))MB  $f"
    done
echo "  (以上为命中；空 = 无 >10MB 文件)"

echo "[1c] Git config"
# 1c. Git config
git config user.name && git config user.email

echo "[1d] Remote 可达性（timeout 25 防挂死，重试 2 次）"
# 1d. Remote reachable（瞬时失败先重试 2 次——github_push_workflow.md Phase 0d Step 1.5；timeout 避免网络抖动时 ls-remote 无界挂起）
git remote -v
for i in 1 2; do timeout 25 git ls-remote --heads origin 2>&1 && break || echo "(尝试 $i 失败/超时)"; sleep 5; done
```

**阻断规则**：
- Secrets found → 🔴 立即停止，展示命中文件
- Git config 缺失 → 🔴 立即停止
- Remote unreachable（重试 2 次后仍失败）→ 🔴 立即停止
- Large files >10MB → ⚠️ 警告但继续

#### Step 1.5: CI 等价预演（🔴 2026-09-14 起必跑）

**为什么在 Skill 里而不是只在 workflow 里**：本 Skill 是 `push` 的实际执行路径，此前**完全不执行
`github_push_workflow.md` 的 Phase 2**；只改 workflow 不会让本步真正跑起来。

逐条执行 CI fast-tests 的 **10 条一致性命令**（命令表见
`ai_system/workflows/github_push_workflow.md` §2a），**收集全部退出码**（不因首条失败中断）。

- 全部为 0 → 进入 Step 2
- 任一非 0 → 🔴 **默认阻断**：列出失败命令与关键输出；仅当用户**显式放行**才继续，并写明放行理由
- ⚠️ **边界**：本步读的是本地工作树，**抓不到「闸门读开发机磁盘」类不等价**（见 Phase 2 标题下边界注记）

#### Step 2: 变更清单

```
git status --porcelain
git diff --stat
git log origin/main..HEAD --oneline 2>/dev/null || echo "(no commits ahead of origin)"
```

将变更按类别分组展示（Source / Docs / AI_Context / Workflows / Config / Proposals / Coordination）。

#### Step 3: 生成 Commit Message + 用户确认

基于 `git diff --stat` 实际变更自动生成 commit message（遵循 `type(scope): 中文摘要` 格式，见 CLAUDE.md）。

如果 `$ARGUMENTS` 非空，以用户提供的 message 为准。

**必须**展示以下内容并等待用户确认：
- Commit message
- 变更文件清单（按类别）
- Commits ahead of origin
- 任何警告（large files, broken links 等）

用户确认后才进入 Step 4。

#### Step 4: Commit + Push

```bash
cd ${CLAUDE_PROJECT_DIR}
# 精确路径模式：从 Step 2 变更清单中提取文件列表，禁止 git add -A
git add <file1> <file2> ...   # Step 2 分类清单中的精确路径
git diff --cached --name-status                    # 复核：只含本批预期条目
git commit -m "<message>" -- <file1> <file2> ...   # 🔴 pathspec 形态（见下）
timeout 120 git push origin main   # timeout 防网络抖动挂起
```

> 🔴 **提交须带精确 pathspec（2026-09-29，工作台账 #299）**——无路径 `git commit` 按 **index 整体**落盘，
> 而并行会话的暂存件可能正停在 index 里**等其用户确认** ⇒ 会把它一并卷走。
> **pathspec 形态按「HEAD 树 + 该路径的工作区内容」重建，index 里其余内容不参与** ⇒ **构造性**关闭该窗口。
> 这是**无条件默认**（不取决于是否检测到对端会话）：它相对无路径提交**永不变差**。
> （`CLAUDE.md` 只要求「并行会话在场时」使用；本 Skill 取**更严**的无条件形态——**收紧而非冲突**，故不构成两条真源相左。）
> 🔴 **与 `git rm --cached` 子类的冲突**（文件仍在磁盘 ⇒ pathspec 会把删除读作「无变化」而确定性还原）见下方子类豁免段——
> **该子类必须无 pathspec**，此时改用**串行化**处置。
> 另：**rename 须源与目标两条路径都喂**（`--name-only` 对 rename 只给目标）。

- 如果 nothing to commit → 只执行 push（推送已有 commits）
- 如果 push 被拒绝（non-fast-forward）→ 报告原因，终止

> 🔴 **子类豁免（🆕 2026-09-18）——「从索引移除但保留磁盘文件」不得走 pathspec 式提交**
>
> 若本批含 `git rm --cached` 类条目（摘出跟踪 / 去版本化 / 存量产物不入 git），**不得**用 pathspec 式提交
> （`git commit -- <paths>` 或 `--pathspec-from-file`）。`--cached` 只移出索引、**文件仍在磁盘**，
> 而 pathspec 式按「HEAD 树 + 该路径的**工作区内容**」重建 ⇒ 存在被读作「无变化」，删除被**确定性还原**，
> 且**原 index 中已暂存的删除一并丢失**（2026-09-18 实测：一次静默漏掉 33 个删除，且 `git diff --cached` 归零）。
>
> **正确序列**：`git rm --cached <paths>` → `git diff --cached --name-status` 逐条确认只含预期条目 → **无 pathspec** 的 `git commit`。
>
> 🔴 **但「复核已做过」不构成安全前提**（2026-09-23 证伪，**两度实证**）：复核与 `git commit` 是**两次独立调用、窗口非原子**
> ——实测复核 11 条，落盘 17 条 / 13 条各一次。故本子类（pathspec 被禁用）在**并行会话在场**时的**唯一有效**处置是
> **串行化**：提交前用 `ListAgents` 查对等会话 + `git status --porcelain` 确认对端已**落定**，**勿依赖复核快照**。
> （同源：`CLAUDE.md` §结束时自动提交 · `coordination/claims/README.md` §3 铁律 4。）
>
> **提交后核对**：`git show --name-status HEAD` 按 `A/D/M` **分类计数**与预期对照，**勿只看 `files changed` 总数**
> ——删除被静默还原时该总数偏小却不报警（实测预期 42、报 9）。

#### Step 5: 报告

展示：committed hash, pushed branch, remote URL. CI 自动触发；**Step 1.5 的 CI 等价预演已给出推送前结论**，
故无需在推送后等待 CI（如需事后确认，用 `gh run list --limit 1`，见方案 §1.2 的 run 锚点格式）。

### 禁止事项

- ❌ 禁止使用 `git add -A`（会误吞并行会话/窗口的变更；必须用精确路径）
- ❌ 禁止对含 `git rm --cached` 条目的批次使用 pathspec 式提交（删除会被静默还原；见 Step 4 子类豁免）
- ❌ 禁止将 bash 命令包装为 agent 调用
- ❌ 禁止写入中间文件（.push-report.json 等）用于 IPC
- ❌ 禁止使用 `--force` push
- ❌ 禁止跳过用户确认直接 commit+push
