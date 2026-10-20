---
project_version: "1.0.0"
language: "zh"
last_updated: "2026-10-05"
category: "ai_workflow"
purpose: "工作流注册表——回答「存在什么」。任何工作流变更必须先更新此注册表。"
tags: [index, governance, registry]
---

# workflow_index.md — AI 工作流注册表

> 📖 **使用手册**：[workflow_usage_guide.md](workflow_usage_guide.md) — 工作流层级关系、调用顺序、决策树。
> 本文件只回答「**存在什么**」，使用手册回答「**如何选择与串联**」。
> **受众**：AI 助手（跨会话恢复 + 工程治理）
> **优先级**：本文件是工作流系统的 Registry——任何工作流变更必须先更新此注册表。

---

## 1. 工作流全景图

```
ai_system/workflows/
│
├── workflow_index.md                          ★ 本文件 —— 注册表
├── workflow_usage_guide.md                    📖 使用手册 —— 层级关系、决策树、调用顺序
│
├── full_ai_context_update.md                  [全局编排] 全量更新 AI 上下文
├── ai_context_consistency_audit.md            [全局审计] 交叉审计上下文冲突与漂移
├── documentation_update_workflow.md           [文档增量] 检测漂移并增量修复
├── project_engineering_assessment_workflow.md [工程评估] 项目工程架构与可维护性审计
├── github_push_workflow.md                    [推送发布] 安全闸门→提交→推送→CI 监控
│
├── architecture_update_workflow.md            [架构专项] 同步架构快照与模块索引
├── validation_update_workflow.md              [验证专项] 同步验证注册表与引用
├── official_docs_sync_workflow.md             [镜像同步] 官方文档三源漂移探测与更新
├── third_party_repo_ingestion_workflow.md     [三方入库] 外部仓库入库全流程（原项目导入件，路径待适配）
│
├── workflow_alignment_audit.md                [体系自审计] 工作流↔架构一致性审计
├── workflow_authoring_workflow.md             [撰写前端] 用途构想→规范
├── workflow_creation_workflow.md              [创建] 新建工作流的标准化注册
├── workflow_deprecation_workflow.md           [废弃] 工作流退役全流程
├── proposal_audit_workflow.md                 [方案审计] 7 维审计模型
├── G_newdir_workflow.md                       [架构门禁] 新增顶层目录的提案审批
└── parallel_session_launch_workflow.md        [并行启动] 判「该不该并行 / 该不该交接」
```

**分层**（层计数不在此维护——真值 = §2 注册表实盘）：

- **全局层** — 跨领域编排、审计、文档同步、推送发布
- **领域层** — 单一领域的专项更新与外部内容入库
- **元层** — 工作流体系自身的治理（创建 / 撰写 / 废弃 / 审计 / 门禁 / 并行决策）

---

## 2. 工作流注册表

> 详细职责、适用场景、触发条件、影响文件 → 见各工作流自身 `.md` 文件的 frontmatter 与正文。
> 如何选择、串联、编排 → 见 [workflow_usage_guide.md](workflow_usage_guide.md)。

### 2.1 全局层

| 文件 | 一句话职责 |
|------|-----------|
| `full_ai_context_update.md` | 全量更新并同步 AI 上下文文件，确保其与当前源码、架构与验证体系一致 |
| `ai_context_consistency_audit.md` | 交叉审计全部 ai_context 文件，检测冲突漂移并统一化修复（按需运行） |
| `documentation_update_workflow.md` | 检测源码变更后的文档漂移，最小化增量更新并同步 AI 上下文 |
| `project_engineering_assessment_workflow.md` | 审计工程架构、工作流与可维护性，生成评估报告与重构建议 |
| `github_push_workflow.md` | 安全地将累积变更经闸门检查与 CI 就绪验证后提交并推送 |

### 2.2 领域层

| 文件 | 一句话职责 |
|------|-----------|
| `architecture_update_workflow.md` | 模块结构 / 导入依赖 / 命名规范变化时，定向更新架构快照与模块索引 |
| `validation_update_workflow.md` | 验证函数 / 测试 / 基准值变更时，定向更新验证注册表与引用 |
| `official_docs_sync_workflow.md` | 官方文档镜像三源漂移探测与更新——台账驱动 + 确定性探测 + 人工闸门 |
| `third_party_repo_ingestion_workflow.md` | 三方仓库入库全流程：必要性评估 + 元信息强制 + 索引同步（原项目导入件，路径待适配本骨架） |

### 2.3 元层

| 文件 | 一句话职责 |
|------|-----------|
| `workflow_alignment_audit.md` | 审计工作流体系与项目架构的一致性，检测漂移与覆盖缺口并委托修复 |
| `workflow_authoring_workflow.md` | 「新建工作流」的设计前端：用途构想→规范→委托创建/方案生成 |
| `workflow_creation_workflow.md` | 新建工作流的标准化注册流程，确保一次注册完整、消除创建遗漏 |
| `workflow_deprecation_workflow.md` | 工作流废弃全流程：交叉引用扫描→修复计划→标记→引用修复→验证 |
| `proposal_audit_workflow.md` | 方案 7 维审计模型（D1 路径→D7 复用度），人工审阅前执行 |
| `G_newdir_workflow.md` | 架构变更门禁：检测目录缺口→生成增量提案→用户审批后方可新建目录 |
| `parallel_session_launch_workflow.md` | 并行会话启动建议（触发器层）：判「该不该并行」并产出预填的会话分解方案 |

---

## 3. 废弃记录

| 工作流 | 废弃日期 | 替代者 |
|--------|:---:|------|
| — | — | — |

---

## 4. 维护触发器

| 触发条件 | 需要更新的注册表内容 | 同步更新 Guide? |
|---------|-------------------|:---:|
| 新增工作流文件 | §1（全景目录树新增条目）+ §2（注册表新增行） | 否 |
| 工作流被废弃 | §1 + §2（标记已废弃）+ §3（新增废弃记录行） | 否 |
| 工作流重命名 | §1 + §2（更新文件名） | 否 |
| 工作流状态变化（已有→已完成） | §1 + §2 + §3 下方「已完成工作流」行 | 否 |
| 新增/调整工作流层级关系 | §1（分层列表） | **是**（Guide §1） |
| 工作流文件自身 frontmatter 更新 | 否（各文件 self-contained） | 否 |
| 新增自动化验证闸门 | 否（`check_workflows.py` 独立于本注册表） | 否 |

**关键原则**：Registry 跟踪「存在什么」，Guide 跟踪「如何使用」。两者更新节奏独立。

> 🔴 修改本文件后必须运行 `python ai_system/validation/check_workflows.py` 验证
> （G5 交叉引用完整性 / G6 废弃一致性）。
