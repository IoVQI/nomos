---
project_version: "0.9.0"
language: "zh"
last_updated: "2026-09-10"
compatible_project_version: ">= 0.5.0"
category: "ai_workflow"
tags: [workflow, lifecycle, authoring, design, specification, proposal, meta]
purpose: "统一「新建工作流」设计前端：用途构想→规范→委托创建/方案生成，杜绝即席起草"
changelog: "wf-1.1: Phase 1 frontmatter 模板引用加 purpose 字段（同步 workflow_creation wf-1.1，G1 强制字段 4→5）（2026-08-13）。; wf-1.0: 初始版本——工作流撰写标准化：用途构想→工作流规范→委托创建(workflow_creation_workflow)→委托方案生成(proposal-gen Skill)→终验，填补「构想→规范」前端设计空白（2026-08-13）"
related:
  - workflow_index.md
  - workflow_creation_workflow.md
  - workflow_deprecation_workflow.md
  - ai_system/version_registry.md
  - chain_template_catalog.md
  - .claude/skills/README.md
  - .claude/workflows/README.md
execution_mode: strict  # strict | normal
# strict 模式下：每个 Phase 必须在上一 Phase 所有退出条件满足后才能进入
# 闸门判定必须基于实际命令输出（禁止"推断"通过）
# 连续 3 次同一 Phase 失败 → 🔴 阻断，写入 proposals/ 请求用户介入
completion_marker: "🔴 CHAIN_COMPLETE"
max_retry_per_phase: 3
---

# workflow_authoring_workflow — 工作流撰写标准化

> **作用**: 从一条自然语言的「用途构想」到一份结构化「工作流规范」，再到「新工作流创建方案」的**前端设计**流程。是 `workflow_creation_workflow`（注册落盘）的**上游**，与 `workflow_deprecation_workflow`（废弃）共同构成工作流全生命周期。

## 工作流目标

统一「新建工作流」的**设计阶段**，把「用途构想 → 工作流规范 → 委托创建 → 委托方案」标准化，确保：
- **规范质量可控**：frontmatter 字段统一、Phase 结构对齐、闸门完整
- **注册无遗漏**：委托 `workflow_creation_workflow` 承担机械落盘/注册
- **产物可审计**：委托 `proposal-gen` 生成创建方案

**核心原则**：
- **编排而非重复**：本工作流不内联「创建/注册」和「方案生成」，而是委托既有设施
- **规范先行**：先产出结构化规范，再落盘——杜绝「边写边想」的即席质量
- **三层选型**：按 `.claude/skills/README.md` 三层体系（MD/Skill/JS）显式判定新工作流的架构形态
- **与 creation / proposal_audit 的三级防线**：
  ```
  设计: 本工作流（构想 → 规范）
  创建: workflow_creation_workflow（规范 → 落盘 + 注册）
  事中: proposal_audit（方案审计——检测方案描述的创建是否合理）
  ```

---

## 适用场景

- 用户以自然语言提出「创建一个 X 工作流」「基于用途构想设计工作流」「需要一个 Y 的标准化流程」
- 现有工作流无法覆盖的新领域/新职责，需要从零设计规范

## 不适用场景

- 工作流已充分指定（名称/所属层/职责已定），仅需注册落盘 → 直接走 `workflow_creation_workflow.md`
- 工作流废弃/退役 → `workflow_deprecation_workflow.md`
- 工作流版本升级（语义变更）→ 各文件 self-contained frontmatter 版本，不触发本工作流

---

## 前置条件

| 依赖 | 用途 | 条件 |
|------|------|------|
| `workflow_creation_workflow.md` | Phase 2 委托创建/注册 | 存在（wf-1.0） |
| `proposal-gen` Skill | Phase 3 委托方案生成 | 存在（`.claude/skills/proposal-gen/`） |
| `ai_system/official_docs/claude_code/skills.md` + `workflows.md` | Phase 1 Skill/JS 选型判据 | 存在 |
| `chain_template_catalog.md` | Phase 1 P1-P9 设计原则参考 | 存在 |
| `check_workflows.py` | Phase 4 终验（G1–G6） | Python 环境 |

---

## 工作流步骤

### Phase 0: 输入解析

从「用途构想」提取输入契约：

| 字段 | 必填 | 说明 |
|------|:---:|------|
| 工作流名称 | ✅ | 文件名（`<name>_workflow.md` 或 `<name>.md`） |
| 所属层 | ✅ | 全局层 / 领域层 / References 专项层 / 元层 |
| 一句话职责 | ✅ | workflow_index §2 注册表的「一句话职责」列 |
| 关联领域 | ❌ | 新工作流服务的领域（references / derivation_kb / data_kb 等） |
| 是否需要 Skill 入口 | ✅ | 高频自然语言触发 → 是（P2 选型） |
| 是否需要动态工作流 | ✅ | 线性管线/大批量并行 → 是（P1 选型） |
| 关联链模板 | ❌ | 若属链模板触发域 |

### 0.4 退出条件（🔴 必须全部满足方可进入 Phase 1）

- [ ] 工作流名称已确定（含目标文件路径）
- [ ] 所属层已确定
- [ ] 一句话职责已撰写
- [ ] Skill / 动态工作流 选型已判定

### 0.5 失败处理（🔴 不得跳过）

- 用途构想信息不足（缺名称/所属层/职责）→ 🔴 阻断，向用户补齐
- 目标文件已存在 → 🔴 阻断，提示走版本升级而非创建

---

### Phase 1: 规范生成

生成新工作流的规范正文（frontmatter + 正文 Phase 结构）。**参考素材**（强制查阅）：

1. **frontmatter 模板** → `workflow_creation_workflow.md` Phase 1（`project_version` / `language` / `last_updated` / `compatible_project_version` / `category` / `purpose` / `tags` / `changelog` / `related`）
2. **Skill 选型判据** → `ai_system/official_docs/claude_code/skills.md`（何时建 Skill：重复粘贴指令/checklist/多步流程）+ `.claude/skills/README.md`（三层体系）
3. **动态工作流选型判据** → `ai_system/official_docs/claude_code/workflows.md`（何时用 workflow：多 agent 编排/可重跑脚本）+ `.claude/workflows/README.md`
4. **正文设计原则** → `chain_template_catalog.md` §3 P1-P9（信噪比 / 增量 / 不重叠 / 粒度 / QA 闸门 / 闭环 / 收尾）
5. **既有同类工作流归属** → `workflow_index.md` §1 七层结构

**输出「架构选型结论」**：

| 结论 | 含义 | 后续 |
|------|------|------|
| 仅 MD | 纯治理/推理流程 | Phase 2 仅落盘 MD |
| MD + Skill | 高频自然语言触发 | Phase 2 追加 Skill 注册 |
| MD + JS | 线性确定性管线 | Phase 2 追加动态工作流注册 |

### 1.4 退出条件（🔴 必须全部满足方可进入 Phase 2）

- [ ] frontmatter 已按模板生成（强制字段非空：`project_version` / `last_updated` / `language` / `purpose`）
- [ ] 正文 Phase 结构完整（目标 / 适用场景 / 步骤 / 退出条件 / 失败处理）
- [ ] 架构选型结论已定（仅 MD / MD+Skill / MD+JS）
- [ ] 元层/操作型已按 P0 加固约定决定是否添加 `execution_mode: strict` 块

### 1.5 失败处理（🔴 不得跳过）

- 规范结构不完整（缺退出条件/失败处理）→ 重试补齐（消耗 max_retry_per_phase）
- 架构选型不确定 → 参考 official_docs 判据 + 既有同类工作流，仍不确定则 🔴 阻断向用户确认

---

### Phase 2: 委托创建（workflow_creation_workflow）

委托 `workflow_creation_workflow.md` 执行落盘 + 注册，传入 Phase 1 产出的规范：

- 落盘新工作流 `.md` 文件
- 注册 workflow_index §1/§2/七层计数/changelog
- 注册 version_registry §2 版本桶
- 动态工作流注册（若选型含 JS）
- Skill 注册（若选型含 Skill）
- 链模板触发域评估
- check_workflows 验证

### 2.4 退出条件（🔴 必须全部满足方可进入 Phase 3）

- [ ] 新工作流 `.md` 已落盘（内容 == Phase 1 规范）
- [ ] workflow_index / version_registry 注册完成
- [ ] 动态/Skill 注册完成（若适用）
- [ ] 链模板触发域评估已记录（适用/不适用）

### 2.5 失败处理（🔴 不得跳过）

- 委托目标 `workflow_creation_workflow.md` 不可用 → 🔴 阻断，检查文件存在性
- 注册遗漏 → 依赖 check_workflows.py G3/G4 捕获，回到 workflow_creation 修复

---

### Phase 3: 委托方案生成（proposal-gen Skill）

委托 `proposal-gen` Skill 生成「新工作流创建方案」：

- P0 事实采集（proposal-gen-collect.js）
- P1 九节骨架撰写
- P2 落盘门禁 + 原子自注册
- P3 轻量自审

### 3.4 退出条件（🔴 必须全部满足方可进入 Phase 4）

- [ ] 创建方案已落盘（`proposals/YYYY/MM/DD/`）
- [ ] 方案已自注册（`_catalog.md` + `records/index.md`）
- [ ] 方案状态 = 待确认（或已执行，若用户即时批准）

### 3.5 失败处理（🔴 不得跳过）

- `proposal-gen` Skill 不可用 → 🔴 阻断，检查 `.claude/skills/proposal-gen/SKILL.md`
- 方案自审发现 CRITICAL → 移交 `/proposal-audit` 兜底

---

### Phase 4: 终验

```bash
python ai_system/validation/check_workflows.py --quiet
```

必须 exit 0（G1–G6 全部 PASS），尤其：
- G3 索引-磁盘计数匹配（新工作流定义文件数 == 实盘）
- G4 版本注册表一致性（version_registry 版本桶）
- G5 交叉引用完整性

### 4.4 退出条件（🔴 工作流终点）

- [ ] `check_workflows.py --quiet` exit 0
- [ ] G1（frontmatter）/ G3（计数）/ G4（版本桶）/ G5（引用）全部 PASS
- [ ] 无新增 FAIL

### 4.5 失败处理（🔴 不得跳过）

- check_workflows.py FAIL → 🔴 阻断，修复根因后重跑
- 计数漂移 → 运行 `--fix` 或手动修正
- 不得以「输出看起来正常」为由跳过验证

🔴 CHAIN_COMPLETE

---

## 故障处理

| 故障 | 阶段 | 处理 |
|------|:---:|------|
| 用途构想信息不足 | Phase 0 | 🔴 阻断，向用户补齐 |
| 目标文件已存在 | Phase 0 | 🔴 阻断，提示版本升级 |
| 规范结构不完整 | Phase 1 | 重试补齐 |
| 架构选型不确定 | Phase 1 | 查 official_docs + 同类工作流，仍不定 → 🔴 阻断 |
| 委托目标不可用 | Phase 2/3 | 🔴 阻断，检查文件存在性 |
| 注册遗漏 | Phase 2 | check_workflows G3/G4 捕获，回到 workflow_creation 修复 |
| check_workflows FAIL | Phase 4 | 🔴 阻断，修复根因后重跑 |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| wf-1.0 | 2026-08-13 | 初始版本——工作流撰写标准化（P0 输入解析 → P1 规范生成 → P2 委托创建 → P3 委托方案 → P4 终验） |

---

*关联工作流：[workflow_creation_workflow.md](workflow_creation_workflow.md)（创建/注册，Phase 2 委托）、[workflow_deprecation_workflow.md](workflow_deprecation_workflow.md)（废弃）、[proposal_audit_workflow.md](proposal_audit_workflow.md)（方案审计）、[workflow_index.md](workflow_index.md)（注册表）*
