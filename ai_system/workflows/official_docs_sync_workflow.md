---
project_version: "0.9.0"
language: "zh"
last_updated: "2026-09-22"
compatible_project_version: ">= 0.5.0"
category: "ai_workflow"
status: active
tags: [official-docs, mirror, drift-detection, sync, registry]
purpose: "官方文档镜像（Claude Code / DeepSeek API / DeepSeek Harness）三源漂移探测与更新——台账驱动 + 确定性探测 + 人工闸门"
description: "台账（official_docs/index.md §一/§三）驱动，check_official_docs.py --probe 产漂移清单，四分支处置（diff 采纳 / 重构件重新抓取 / 新页准入 C1–C4 / 消失页归档），人工确认后落镜像并同步视图。只做镜像同步，不做采纳决策。"
changelog: "ods-1.0: 初始版本——三源异构探测（raw_md / html_ssr / github_md）+ 台账真源改造 + 重构页清单处置分支 + 准入门槛判定。基于 2026-09-12 三源全量漂移实测（claude_code 13/14 页 DRIFT；DeepSeek changelog 增 2026-09-10 V4.1-Flash；DSH v0.1→v0.1.5-rc.2）。ods-1.1: `html_ssr` 比对口径由 title/desc/锚指纹改为**正文区文本逐行比对**——2026-09-21 实测原指纹对正文变更零灵敏度（DeepSeek 源 11/23 页假 IDENTICAL，含模型退役/定价/effort 语义）。; ods-1.2: Phase 5 终验第 2 行去 `--all` 误用（工作台账 #264）——原命令只扫 references/ 下 `_extracted_text.md`，对本工作流产物零覆盖（FAIL 0 不是覆盖证据）。改为校验**本工作流产出的漂移报告**（positional 支持文件/目录）；并明写**不要**对 `ai_system/official_docs/` 整树跑本检查——镜像正文是上游文本的忠实复制，而该检查器为转录产物设计，其 brace_balance/image_refs/table_columns 会误报（实测该树 4 文件 FAIL/6 error，修它们等于改上游文本）；镜像一致性由第 1 行 `--check-frontmatter` 负责。"
related:
  - official_docs_sync_workflow.md
  - ../../ai_system/validation/check_official_docs.py
  - ../../ai_system/official_docs/index.md
execution_mode: normal
---

# official_docs_sync_workflow — 官方文档镜像漂移探测与更新

> **作用**：把 `ai_system/official_docs/` 的三个上游镜像从「散文规则 + 人工记忆」改为**可执行的按需流程**。
> **定位**：**只做镜像同步，不做采纳决策**。上游变更「要不要影响项目设计」属 `documentation_update_workflow` / 方案流程，不在本工作流。

## 与既有设施的分工（先读，避免误用）

| 设施 | 对象 | 与本工作流的关系 |
|------|------|------|
| **本工作流** | **上游官方文档** → 本地镜像 | 漂移探测与镜像刷新 |
| `documentation_update_workflow.md` | **本项目源码** → 本项目文档 | 方向相反、真源不同，不合并 |
| `full_project_sync_workflow.md` | 全项目文档漂移 | 其扫描不覆盖上游镜像 |
| `check_official_docs.py` | 本工作流的确定性内核 | 离线闸门 + `--probe` + `--sync-frontmatter` |
| `journal_index_audit_workflow` | Journal 索引 | Phase 5 产报告时按其规则登记 |

---

## 前置条件

| 依赖 | 用途 | 条件 |
|------|------|------|
| `ai_system/official_docs/index.md` | 台账真源（§一 清单 + §3.2 探测方式 + §3.3 检查台账 + §3.4 重构页清单） | 存在且可解析 |
| `ai_system/validation/check_official_docs.py` | 离线闸门 + 在线探测 | 存在；`--check-frontmatter` 全绿 |
| 网络可达 | `--probe` | `code.claude.com` / `api-docs.deepseek.com` / `api.github.com` / `cdn.jsdelivr.net` 至少其一 |

---

## Phase 0 — 前置与可达性

1. 跑离线闸门：`python ai_system/validation/check_official_docs.py --check-frontmatter --quiet`
   - **必须 exit 0**。台账自身不一致时探测无意义 → 🔴 阻断，先修台账。
2. 探测四域可达性（`curl -s -o /dev/null -w "%{http_code}" --max-time 10`）：
   `code.claude.com` / `api-docs.deepseek.com` / `api.github.com` / `cdn.jsdelivr.net`。
   - **任一不可达 → 记录降级声明**（该源本轮跳过），不阻断其余源。
   - 🔴 `raw.githubusercontent.com` 本网络不可达，**不要重试**——DSH 走 GitHub API。

**退出条件**：离线闸门 exit 0 且可达性探测有结论（可达清单 + 降级清单）。

---

## Phase 1 — 探测

```
python ai_system/validation/check_official_docs.py --probe --json
```

- adapter 由 `index.md` §3.2 决定（`raw_md` / `html_ssr` / `github_md`），**脚本内不硬编码**。
- 每页超时默认 20 s（`--timeout N` 可调）。不可达页面判 `PROBE_FAILED`，**不 FAIL**。
- 判决：`IDENTICAL` / `MINOR` / `DRIFT` / `MISSING_UPSTREAM` / `PROBE_FAILED` / `NON_MIRROR`。

**产出**：漂移清单（逐页 verdict + added/removed + similarity）。
**退出条件**：所有可达源完成探测；不可达源已在 Phase 0 登记降级。

---

## Phase 2 — 分类处置（四分支）

逐条判定，**四个分支的处置逻辑不同，不可混用**：

### 2a `confidence: full` 且 verdict = `DRIFT` → 差异评估（人工闸门）

- 展示该页 added/removed 摘要（前 30 行 diff 上下文）。
- 由用户裁决：**采纳上游 / 保留本地 / 记入待议**。三条出路都要显式选择。
- ❌ **不自动覆盖**——与 `index.md` §3.1「变更处理 = 人工确认后更新」一致。

### 2b 文件在 §3.4 重构页清单（`confidence: partial`）→ 重新抓取

- **不做 diff**。这批从来不是逐字镜像（2026-07-29/07-30 网络阻断期降级为 WebSearch 结构化提取）。
- 重新抓取 → 写入 → `confidence` 升 `full`、`fetch_method` 更新为实际方式 → **从 §3.4 移出**。
- 抓取后跑 `--sync-frontmatter` 让视图跟上。

### 2c 上游新页面 → 准入判定（C1–C4）

新页面来源：`llms.txt` 页面清单增量（CC）/ `docs/subsystems/` 子树增量（DSH）/ 侧边栏链接增量（DeepSeek）。

逐条写出命中的判据（须 **≥2 项**，判据定义见 `index.md` §四）：

| # | 判据 | 命中 |
|:---:|------|:---:|
| C1 | 已有 ≥1 个项目文件实质性引用该文档 | ☐ |
| C2 | 预期在 ≥2 个工作流/方案中作为设计参考 | ☐ |
| C3 | 用户显式请求纳入 | ☐ |
| C4 | 文档描述的功能在项目中已被实际使用 | ☐ |

- 通过 → 列候选清单 **待用户确认**；**未确认不得入库**。
- ❌ 不得直接创建 `official_docs/` 下的新子目录层级——架构增量须先走 `G_newdir` 同精神的提案流程。

### 2d verdict = `MISSING_UPSTREAM` → 归档

- `status` 转 `archived`（§一 该行），**不删文件**（保留可回滚 + 历史证据）。
- 备注列记明归档日期与原因。

**退出条件**：漂移清单每一条都有归属分支 + 处置决定。

---

## Phase 3 — 落镜像（人工确认后）

1. 按 Phase 2 的裁决写入 / 替换镜像文件。**只改内容，不改目录结构**。
2. 跑 `python ai_system/validation/check_official_docs.py --sync-frontmatter --dry-run` 审一遍，再 `--sync-frontmatter` 落视图。
3. 归档分支（2d）只改 §一 的 `status`，不动文件。

**退出条件**：镜像文件与台账一致（`--check-frontmatter` exit 0）。

---

## Phase 4 — 同步视图

| 项 | 动作 |
|------|------|
| §3.3 检查台账 | 回写本轮 `last_checked` = 今日；`next_check_due` = +30 天；`stale_at` = +90 天 |
| §二 抓取历史 | 追加一行（日期 / 页面 / 方法 / 结果 / 触发原因） |
| §一 受影响行 | 更新 `fetch_date`（2a/2b 采纳的页）与 `status`（2d 归档的页） |
| `{product}/_segment_index.md` | 同步对应条目与「最近更新」 |
| 头部「最后更新」 | 三个 `_segment_index.md` + `index.md` + `README.md` |

> 🔴 日期一律用 `python ai_system/validation/beijing_time.py --fmt date` 现场取，**禁止臆造或回填**。

**退出条件**：台账、视图、段索引三者一致（`--check-frontmatter` exit 0）。

---

## Phase 5 — 终验

| 命令 | 预期 |
|------|------|
| `python ai_system/validation/check_official_docs.py --check-frontmatter` | exit 0 |
| `python lab/validation/verify_md_syntax.py records/reports/YYYY/MM/DD/YYYY-MM-DD_official_docs漂移报告.md` | exit 0 |
| `python ai_system/validation/check_workflows.py --quiet` | exit 0 |

- 🔴 第 2 行**校验本工作流产出的漂移报告**（positional 支持文件与目录）。原写 `--all` 是
  **references/ 专用**，对本工作流产物零覆盖（FAIL 0 不是覆盖证据）——工作台账 #264。
  ⚠️ **不要**改为对 `ai_system/official_docs/` 整树跑本检查：镜像正文是上游文本的**忠实复制**，
  而本检查器为**转录产物**设计，其 `brace_balance` / `image_refs` / `table_columns`
  在上游文档上会误报（2026-09-22 实测该树 4 文件 FAIL / 6 error，而**修它们等于改上游文本**）。
  镜像自身的一致性由第 1 行 `--check-frontmatter` 负责。
- 产出漂移报告至 `records/reports/YYYY/MM/DD/YYYY-MM-DD_official_docs漂移报告.md`，
  按 `journal_index_audit_workflow` 规则登记 `records/index.md`。

---

## 边界（必读）

- **探测可证明漂移存在，不能证明漂移有害。** verdict = `DRIFT` 只是事实陈述；是否影响项目设计属采纳决策，不在本工作流。
- **本工作流不修改 `_analysis/`、`_templates/`、`README.md` 的正文实质**——除 Phase 4 的日期与规则同步。
- **不接 pre-commit / CI 的 `--probe`**：在线探测需网络且慢，只由本工作流按需调用；常驻闸门只有离线的 `--check-frontmatter`。
- **DeepSeek 为 HTML**：不承载 frontmatter，其元信息只在台账；`html_ssr` 探测比的是**正文区文本**（`theme-doc-markdown` 容器，逐行比对）而非整页 HTML——构建噪声不进文本故不误报，但正文区的任何文本变更都会命中，须人工确认归属（2026-09-21 前该 adapter 用 title/desc/锚指纹，对正文变更零灵敏度，已废）。

---

## 触发方式

按需触发。常见入口：

1. §3.3 检查台账的 `next_check_due` 到期（或 `check_official_docs.py` 报 `G_od_5` WARN/FAIL）。
2. 用户要求「检查官方文档有没有更新 / 更新镜像」。
3. 上游发布已知（如新模型发布公告）后主动核。
