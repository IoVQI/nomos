---
project_version: "0.9.0"
language: "zh"
last_updated: "2026-09-10"
compatible_project_version: ">= 0.5.0"
category: "ai_workflow"
tags: [workflow, lifecycle, deprecation, cleanup, cross-reference, index]
purpose: "统一工作流废弃全流程，确保交叉引用零残留与三字段标注标准化。"
changelog: "wf-1.1: per_workflow_audit 三级防线移除——事后防线随 per_workflow_audit 废弃终止，降为两级防线（2026-08-18）。; wf-1.0: 初始版本——工作流废弃标准化：退役工作流的完整清理流程（交叉引用扫描 → 修复计划 → frontmatter 废弃标记 → workflow_index §3 → version_registry 版本桶 → catalog → 引用修复 → check_workflows 验证），消除「废弃信息格式不统一 + 交叉引用未清理」的被动模式（2026-08-06）。"
related:
  - workflow_index.md
  - workflow_creation_workflow.md
  - ai_system/version_registry.md
  - chain_template_catalog.md
execution_mode: strict  # strict | normal
# strict 模式下：每个 Phase 必须在上一 Phase 所有退出条件满足后才能进入
# 闸门判定必须基于实际命令输出（禁止"推断"通过）
# 连续 3 次同一 Phase 失败 → 🔴 阻断，写入 proposals/ 请求用户介入
completion_marker: "🔴 CHAIN_COMPLETE"
max_retry_per_phase: 3
---

# workflow_deprecation_workflow — 工作流废弃标准化

> **作用**: 退役一个工作流的完整清理流程。事前/事中设施——废弃时立即执行，不依赖事后审计补救。

## 工作流目标

统一「工作流废弃」的全部步骤，确保废弃操作干净完整：
交叉引用扫描与修复、被废弃文件 frontmatter 标注、`workflow_index.md` §1 标记 + §3 废弃记录、`version_registry.md` §2 版本桶移动、链模板触发域更新、`check_workflows.py` 验证。

**核心原则**：
- **交叉引用零残留**：废弃前扫描引用，废弃时全部修复或标注迁移目标
- **信息格式统一**：废弃日期 / 废弃原因 / 迁移目标三字段强制
- **与 proposal_audit 两级防线**：
  ```
  事前: 本工作流（废弃时标准化操作）
  事中: proposal_audit（方案审计——检测方案描述的废弃是否合理）
  ```

---

## 适用场景

- 退役 MD 工作流（`ai_system/workflows/*.md`）
- 退役动态工作流 / Skill 入口（关联注册表同步清理）

## 不适用场景

- 新建工作流 → `workflow_creation_workflow.md`
- 工作流版本升级 → 不触发本工作流
- 仅需标记为「已完成」（非废弃，如一次性任务完成）→ 直接更新 workflow_index 状态列

---

## 前置条件

| 依赖 | 用途 | 条件 |
|------|------|------|
| `workflow_index.md` | §1 标记 + §3 废弃记录 | 存在且可写 |
| `version_registry.md` | §2 版本桶移动 | 存在且可写 |
| `check_workflows.py` | 废弃一致性验证（G1–G6） | Python 环境 |
| grep/rg | 交叉引用扫描 | 可用 |

---

## 工作流步骤

### Phase 0: 输入解析

| 字段 | 必填 | 说明 |
|------|:---:|------|
| 待废弃工作流文件路径 | ✅ | `ai_system/workflows/<name>.md` |
| 废弃原因 | ✅ | 一句话原因 |
| 迁移目标 | ❌ | 替代工作流（可选，无替代则标注「无」） |

### 0.3 退出条件（🔴 必须全部满足方可进入 Phase 1）

- [ ] 待废弃文件路径已确定
- [ ] 废弃原因已撰写
- [ ] 迁移目标已判定（有替代 / 无替代）

### 0.4 失败处理（🔴 不得跳过）

- 文件不存在 → 🔴 阻断，确认路径
- 缺废弃原因 → 🔴 阻断，补齐（禁止空原因废弃）

---

### Phase 1: 交叉引用扫描

```bash
grep -rl "<wf_filename>" ai_system/workflows/ ai_system/context/ ai_system/audit/ records/ project/ .claude/ 2>/dev/null
```

扫描所有引用被废弃工作流的文件。重点类别：
- `ai_system/workflows/*.md`（related 字段、下游衔接图、委托引用）
- `ai_system/context/*`（AI 上下文）
- `ai_system/audit/*`（审计卡片——按工作流命名，含被废弃工作流引用的审计记录需同步）
- `records/`（提案/报告/备忘录）
- `chain_template_catalog.md`（链模板步骤引用）

> **注**: `ai_system/version_registry.md` 未纳入扫描路径——其版本桶移动由 Phase 5 显式处理，无需在此扫描。

### 1.4 退出条件（🔴 必须全部满足方可进入 Phase 2）

- [ ] 扫描已覆盖 `ai_system/workflows/` + `ai_system/context/` + `ai_system/audit/` + `records/` + `project/` + `.claude/`
- [ ] 引用文件清单已生成（含每处引用的上下文）

### 1.5 失败处理（🔴 不得跳过）

- grep 因权限/路径错误失败 → 重试 1 次；仍失败 → 🔴 阻断

---

### Phase 2: 生成交叉引用修复计划

逐条判定引用处置方式：

| 引用位置 | 处置 |
|------|------|
| `related` frontmatter | 移除被废弃文件引用 |
| 下游衔接图 / 委托引用 | 替换为迁移目标，或移除 |
| `workflow_index.md` §1/§2 | Phase 4 处理 |
| 链模板步骤 | Phase 6 处理 |
| 提案/报告历史引用 | 保留（历史记录），不改写 |

输出修复计划：`{文件路径, 原始引用, 处置动作（替换为X/移除/保留）}`

### 2.4 退出条件（🔴 必须全部满足方可进入 Phase 3）

- [ ] 每条引用已判定处置方式
- [ ] 修复计划已生成（含替换目标或「移除」标注）

### 2.5 失败处理（🔴 不得跳过）

- 引用处置不确定 → 标记 SEMI 待用户确认，不擅自改写历史引用

---

### Phase 3: 更新被废弃工作流 frontmatter

在被废弃文件的 YAML frontmatter 中追加（或修改）：

```yaml
status: "deprecated"
deprecated_date: "<YYYY-MM-DD>"
deprecated_reason: "<废弃原因>"
deprecated_migration: "<迁移目标，无则 N/A>"
```

> **注**: `status` / `deprecated_*` 字段仅为**文档性标注**，G1–G6 不校验（废弃判定由 workflow_index §3 表 + §1/§2 ⚠️ 标记驱动）。被废弃文件仍须保留 `last_updated`（G1 强制约束），不得移除。（原同时要求保留 `workflow_version`——该字段 2026-08-31 已退役，不再存在）

### 3.4 退出条件（🔴 必须全部满足方可进入 Phase 4）

- [ ] frontmatter 已含 `status: deprecated` + 废弃日期 + 原因 + 迁移目标
- [ ] 三字段格式统一（date/reason/migration）

### 3.5 失败处理（🔴 不得跳过）

- frontmatter 无法解析 → 🔴 阻断，人工修复

---

### Phase 4: 更新 workflow_index.md

1. **§1 全景树**：对应条目标记 `⚠️ 已废弃 (YYYY-MM-DD)`
2. **§2 注册表**：状态列改为 `⚠️ 已废弃`
3. **§3 废弃记录**：追加一行 `| <name>.md | YYYY-MM-DD | <迁移目标> |`
4. **七层结构计数**：对应层 active -1 / deprecated +1，总计不变
5. **changelog**：追加 `废弃 <name>.md (YYYY-MM-DD) — <原因>`（🔴 不写 `wf-X.Y:` 版本前缀、不 bump `workflow_version`）
6. **last_updated**：更新为当日

### 4.4 退出条件（🔴 必须全部满足方可进入 Phase 5）

- [ ] §1 已标记 ⚠️ 已废弃
- [ ] §2 状态列已改
- [ ] §3 废弃记录已追加（含日期 + 迁移目标）
- [ ] 层计数已调整（active -1 / deprecated +1）
- [ ] changelog 已追加（日期标记，非版本号）

### 4.5 失败处理（🔴 不得跳过）

- 废弃记录格式不统一 → 参照既有行（§3 现有 10 条）修复

---

### Phase 5: 更新 version_registry.md §2 版本桶

1. 在对应版本桶行 notes 中，将该文件从 active 列表移到 deprecated 列表
2. 若桶行标注了「X active + Y deprecated」→ 调整为 active -1 / deprecated +1
3. 若 `workflow_index.md` 版本已 bump（Phase 4）→ 同步体系版本 + 桶移动

### 5.4 退出条件（🔴 必须全部满足方可进入 Phase 6）

- [ ] 该文件已从 active 移到 deprecated 计数
- [ ] workflow_index 版本 bump 已同步
- [ ] 无计数漂移

### 5.5 失败处理（🔴 不得跳过）

- 计数漂移 → `check_workflows.py --fix` 或手动修正

---

### Phase 6: 链模板触发域更新（若适用）

> 仅当被废弃工作流属于链模板触发域时执行；否则跳过（N/A）。

- 更新 `chain_template_catalog.md`：引用被废弃工作流的链模板步骤 → 替换为迁移目标或移除
- 若链模板因此废弃 → 按链模板废弃流程处理（见 catalog 维护约定）
- bump catalog 版本 ct-X.Y

### 6.4 退出条件（🔴 必须全部满足方可进入 Phase 7）

- [ ] 链模板引用已处理（替换/移除）或标记 N/A
- [ ] catalog 版本已 bump（若修改）

### 6.5 失败处理（🔴 不得跳过）

- 链模板步骤引用了被废弃工作流但无迁移目标 → 🔴 阻断，需先确定替代方案

---

### Phase 7: 执行交叉引用修复

按 Phase 2 生成的修复计划逐条执行：
- `related` / 下游衔接图 / 委托引用 → 替换为迁移目标或移除
- 历史记录（提案/报告）→ 不改写
- 每处修复后确认无残留引用

### 7.4 退出条件（🔴 必须全部满足方可进入 Phase 8）

- [ ] 全部计划内修复已执行
- [ ] 重新 grep 确认无计划内引用残留
- [ ] 历史引用（保留类）已明确标注不处理

### 7.5 失败处理（🔴 不得跳过）

- 修复后仍有残留引用 → 回到 Phase 2 补充判定

---

### Phase 8: 验证

```bash
python ai_system/validation/check_workflows.py --quiet
```

必须 exit 0（G1–G6 全部 PASS），尤其：
- G3 索引-磁盘计数匹配
- G4 版本注册表一致性
- G6 废弃一致性（§3 标记 ↔ §1/§2 ⚠️ 标记）

### 8.4 退出条件（🔴 工作流终点）

- [ ] `check_workflows.py --quiet` exit 0
- [ ] G3（计数）/ G4（版本桶）/ G6（废弃一致性）全部 PASS
- [ ] 无新增 FAIL

### 8.5 失败处理（🔴 不得跳过）

- check_workflows.py FAIL → 🔴 阻断，修复根因后重跑
- G6 废弃一致性 FAIL → 检查 §1/§2 ⚠️ 标记与 §3 记录是否对齐

🔴 CHAIN_COMPLETE

---

## 故障处理

| 故障 | 阶段 | 处理 |
|------|:---:|------|
| 文件不存在 | Phase 0 | 🔴 阻断，确认路径 |
| 缺废弃原因 | Phase 0 | 🔴 阻断，补齐 |
| frontmatter 无法解析 | Phase 3 | 🔴 阻断，人工修复 |
| 引用处置不确定 | Phase 2 | 标记 SEMI 待用户确认 |
| 链模板无迁移目标 | Phase 6 | 🔴 阻断，先定替代方案 |
| check_workflows FAIL | Phase 8 | 🔴 阻断，修复根因后重跑 |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| wf-1.0 | 2026-08-06 | 初始版本——工作流废弃标准化（P1–P8 清理流程） |

---

*关联工作流：[workflow_creation_workflow.md](workflow_creation_workflow.md)（创建标准化）、[workflow_index.md](workflow_index.md)（注册表 + 废弃记录）*
