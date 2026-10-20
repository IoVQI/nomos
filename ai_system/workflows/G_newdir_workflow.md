---
project_version: "0.9.0"
language: "zh"
last_updated: "2026-08-17"
compatible_project_version: ">= 0.4.0"
category: "ai_workflow"
tags: [references, ingestion, gate, directory-structure, taxonomy, G_newdir]
purpose: "安全管控文献入库时的架构变更：检测目录缺口→生成增量提案→用户审批后方可新建目录，杜绝静默建目录"
changelog: "2026-08-05: G_newdir.3 接线 Skill: proposal-gen（P0-P3 生成时门禁）+ 原子双注册（_catalog.md + records/index.md）+ skip-if-present 守卫；wf-1.1: 当前版本——文献入库架构缺口检测→增量提案→用户审批门禁（2026-07-15）；wf-1.0: 初始版本（2026-06-12）"
related:
  - reference_index_maintenance_workflow.md
  - literature_verification_gates.md
  - literature_ingestion_workflow.md
---

# G_newdir — 文献入库架构缺口检测与增量更新门禁

> **位置**：Stage D（放置元信息获取）→ **G_newdir（本门禁）** → Stage E（最终放置）→ Stage F（验证）→ Stage G（会话收尾）
> **设计原则**：Fail-Safe — 宁可停止入库等待用户审批，不可静默创建目录结构

---

## 1. 门禁位置

```
Stage A (inbox) → Stage A2 (元信息核验) → Stage B (deep read) → Stage C (human judgment)
→ Stage D (placement metadata) → G_newdir (本门禁) → Stage E (final placement)
→ Stage F (validation) → Stage G (session wrap-up)
```

G_newdir 是 Stage D 与 Stage E 之间的**强制性门禁**。论文通过放置元信息获取（Stage D）后，在放置到 `references/` 目录树（Stage E）之前，必须经过此门禁判断是否需要架构变更提案。

---

## 2. 触发条件

### 2.1 触发（需提案）

以下任一条件满足时，G_newdir **阻断**，需生成架构增量提案：

| 触发条件 | 判定标准 | 示例 |
|---------|---------|------|
| **T1: 叶子目录不存在** | 条目属于已知子域，但该子域下无匹配的变体子目录 | 条目属于某模型，但 `variants/` 下无对应子目录 |
| **T2: 中间层级缺失** | 条目主题在研究维度上无对应子域目录 | 条目关于某主题，但 `hybrid/` 下无对应子域 |
| **T3: 跨域条目** | 条目同时属于 ≥2 个研究维度，现有分类无法单一映射 | 条目同时涉及两个研究维度 |
| **T4: 新方法论** | 条目提出全新方法，不匹配现有方法分类下任何子类 | 全新的方法，不匹配 `methods/` 下任何子目录 |
| **T5: 新数据来源** | 条目使用新数据来源，`observations/` 下无对应目录 | 新数据产品，`observations/` 下无对应子目录 |

### 2.2 免触发（直接 Stage E）

| 免触发条件 | 判定标准 | 示例 |
|-----------|---------|------|
| 条目恰好属于已有叶子目录 | 目标 `Author_Year/` 的父目录已存在，仅需新建叶子 | 新条目 → 直接放入 `variants/` 下新建 `{NewAuthor_Year}/` |
| 仅创建 `Author_Year/` 叶子 | 现有目录下新增一条目，不需要新建任何中间目录 | `series/sly/` 下新增一条目 |
| 条目被驳回 | Stage C2b 直接进入 `_rejected/`，不涉及架构变更 | — |

### 2.3 边界情况

| 情况 | 处理方式 |
|------|---------|
| 仅新增 `Author_Year/` 叶子 | **免触发**，直接 Stage E |
| 新增 1 级中间目录 + 1 个叶子 | **触发**，需提案（T1） |
| 新增 2+ 级中间目录 | **触发**，需提案（T2） |
| 批量入库涉及 N 个缺口 | 合并为 1 份提案（见 §3.2 合并规则） |
| 论文放入 `_rejected/` | 不涉及架构变更，无需提案 |
| 论文从 `_decommissioned/` 重新激活 | 若原目录已删除 → 触发；否则免触发 |
| `_inbox/` 待处理区论文 | G_newdir 仅在确定入库后触发，不影响 inbox 暂存 |

---

## 3. 门禁流程

```
G_newdir
  │
  ├─ 不触发 → 直接进入 Stage E（最终放置）
  │
  └─ 触发 → 执行以下子步骤：
        │
        ├─ G_newdir.1  定位缺口
        │    ├─ 确定论文的研究维度（domain）
        │    ├─ 在 references/ 目录树中定位最接近的现有节点
        │    └─ 生成「现有架构中的缺口诊断」
        │
        ├─ G_newdir.2  设计方案
        │    ├─ 提议新增的目录路径（1 到 N 级）
        │    ├─ 画 affected subtree 的前后对比
        │    ├─ 列举受影响索引文件
        │    └─ 若为批量入库，合并多个缺口为统一方案
        │
        ├─ G_newdir.3  生成提案文档
        │    ├─ 写入 proposals/YYYY/MM/DD/YYYY-MM-DD_{描述}_架构增量方案.md
        │    ├─ 状态 = 待确认
        │    └─ 在 records/index.md 注册
        │
        ├─ G_newdir.4  等待用户确认
        │    └─ 用户确认前不得创建目录或移动文件
        │
        └─ G_newdir.5  执行 + 归档
             ├─ 按方案创建目录结构
             ├─ 继续 Stage E（放置文件）
             ├─ 方案状态更新为 已执行
             └─ 终验 check_references.py
```

### 3.1 各子步骤详解

#### G_newdir.1 — 定位缺口

1. **确定论文的研究维度**：从 Stage D 获取的元信息（标题、摘要、分类标签）判定论文属于哪个研究维度
2. **在目录树中定位最近节点**：从 `references/` 根开始逐级比对，找到最深匹配的现有目录
3. **生成缺口诊断**：输出「论文 X 属于维度 Y，最近现有节点为 Z，缺失层级为 [list]」

#### G_newdir.2 — 设计方案

1. **提议新增路径**：从缺口诊断出发，设计需要新建的目录层级
2. **affected subtree 前后对比**：用 ASCII art 画出变更前后的目录子树
3. **列举受影响索引**：需更新的 `_index/*.md` 子模块、`references_index.md`（若涉及新子域导航）

#### G_newdir.3 — 生成提案文档

调用 `Skill: proposal-gen`（P0 真源采集 → P1 骨架撰写 → P2 落盘门禁 → P3 落盘后轻量自审）生成提案，写入 `proposals/YYYY/MM/DD/`，状态设为 `待确认`。
**原子双注册**（同一批操作，禁止先注册一个等另一个）：追加行到 `records/index.md` proposals 段 + 追加行到 `proposals/_catalog.md` §2 表顶（`_catalog.md` frontmatter 计数已于 2026-08-31 退役——只登记行，不计计数，见方案 2026-08-31_废弃工作流版本控制与Journal计数设施方案）。**skip-if-present 守卫**：注册前先 grep 验证本方案行是否已存在，存在则跳过（防二次注册——FM-12/13/14）。

#### G_newdir.4 — 等待用户确认

提案写入后**立即停止**。不得在用户确认前执行任何目录创建或文件移动操作。用户可通过以下方式确认：
- 回复「执行」/「确认」/「同意」
- 修改提案内容后回复「按修改后方案执行」

#### G_newdir.5 — 执行 + 归档

1. 按方案 `mkdir -p` 创建目录，添加 `.gitkeep`
2. 继续 Stage E（放置 PDF + .md）
3. 更新 `references_index.md` 目录树（若涉及）和对应 `_index/*.md` 子模块
4. 运行 `check_references.py` 终验
5. 提案状态更新为 `已执行`

### 3.2 批量入库合并规则

当一次入库涉及多个缺口时，合并为**一份**提案：

1. 在 §1 缺口诊断中为每篇论文单独列出诊断
2. 在 §2 增量方案中合并 affected subtree（同一父目录下的多个缺口合并展示）
3. 在 §4 执行步骤中按依赖顺序排列（先建父目录，再建子目录）

---

## 4. 提案文档最小模板

```markdown
---
date: "YYYY-MM-DD"
category: "proposal"
tags: [references, directory-structure, ingestion, G_newdir]
status: "待确认"
---

# {论文/批次} 文献库架构增量更新方案

## 1. 缺口诊断
- 论文标识（arXiv ID / 标题 / 作者）
- 论文所属研究维度
- 现有架构中最近节点
- 无法直接放置的原因

## 2. 增量方案
- 新增目录路径（从 references/ 根开始）
- affected subtree before/after

## 3. 索引影响
- 需更新的索引文件清单
- 需更新的子模块（_index/*.md）

## 4. 执行步骤
- mkdir 命令列表
- 后续 Stage E 放置说明

## 5. 终验
- check_references.py 预期结果
```

---

## 5. 被引用关系

| 工作流/文档 | 引用方式 |
|------------|---------|
| `CLAUDE.md` references/ 段 | 门禁摘要（5 条规则） |
| `reference_index_maintenance_workflow.md` Phase 0c.3 | 替换旧一句话为 G_newdir 引用 |
| `workflow_index.md` | §2.3（References 专项层注册表） |
| `literature_verification_gates.md` | 闸门体系统览 |
| `literature_ingestion_workflow.md` Phase 2.2 | 集成 G_newdir 门禁（架构缺口时触发） |
| `references/_inbox/README.md` | 步骤 4 人工判定（行37） |

---

## 6. 与其他闸门的关系

| 闸门 | 位置 | 职责 | 与 G_newdir 关系 |
|------|------|------|-----------------|
| G0–G3 | 文献处理管线内 | 内容质量验证 | 无关 — G_newdir 是**架构门禁**，不检查文件内容 |
| `check_references.py` G1–G6 | Stage F | 文件系统一致性 | G_newdir.5 执行后运行 G1–G6 终验 |

G_newdir 是独立于 G0–G3 和 `check_references.py` 的**第三类闸门**：不检查内容质量（G0–G3），不检查文件一致性（G1–G6），而是检查**架构变更是否经用户知情同意**。

> **术语映射**：G_newdir 采用 Stage A–G 模型（本门禁位于 Stage D→E 之间）；编排方 `literature_ingestion_workflow` 采用 Phase 0–5（本门禁集成于其 Phase 2.2）。Stage A–G 与 Phase 0–5 为粗略对应，描述同一管线不同粒度。

---

*工作流版本 wf-1.1，创建于 2026-06-12。*
