---
project_version: "0.9.0"
language: "zh"
last_updated: "2026-09-10"
compatible_project_version: ">= 0.5.0"
category: "ai_workflow"
tags: [workflow, lifecycle, creation, registration, governance, index]
purpose: "统一新建工作流的标准化注册流程，确保一次注册完整、消除创建遗漏"
changelog: "wf-1.1: Phase 1 frontmatter 模板加 purpose 字段（G1 强制字段 4→5 扩展）（2026-08-13）。; wf-1.0: 初始版本——工作流创建标准化：从零创建新工作流 .md 文件的注册流程（frontmatter 模板 → workflow_index 注册 → version_registry 版本桶 → 动态/Skill 注册 → 链模板触发域评估 → check_workflows 验证），消除「创建→事后审计补救」的被动模式（2026-08-06）。"
related:
  - workflow_index.md
  - workflow_deprecation_workflow.md
  - ai_system/version_registry.md
  - chain_template_catalog.md
  - .claude/workflows/README.md
  - .claude/skills/README.md
execution_mode: strict  # strict | normal
# strict 模式下：每个 Phase 必须在上一 Phase 所有退出条件满足后才能进入
# 闸门判定必须基于实际命令输出（禁止"推断"通过）
# 连续 3 次同一 Phase 失败 → 🔴 阻断，写入 proposals/ 请求用户介入
completion_marker: "🔴 CHAIN_COMPLETE"
max_retry_per_phase: 3
---

# workflow_creation_workflow — 工作流创建标准化

> **作用**: 从零创建新工作流 `.md` 文件时的标准化注册流程。事前设施——创建时立即执行，不依赖事后审计补救。

## 工作流目标

统一「新建工作流」的全部注册步骤，确保新工作流一次性注册完整：
frontmatter 模板、`workflow_index.md` §1/§2/changelog、`version_registry.md` §2 版本桶、动态工作流/Skill 注册（如适用）、链模板触发域评估、`check_workflows.py` 验证。

**核心原则**：
- **一次到位**：注册遗漏（版本号滞后、计数漂移、引用断裂）从「事后审计发现」变为「创建时避免」
- **模板驱动**：frontmatter 字段由模板生成，杜绝字段不统一
- **与 proposal_audit 两级防线**：
  ```
  事前: 本工作流（创建时标准化操作）
  事中: proposal_audit（方案审计——检测方案描述的创建是否合理）
  ```

---

## 适用场景

- 新建 MD 工作流（`ai_system/workflows/*.md`）
- 新建动态工作流（`.claude/workflows/*.js`，P4 分支）
- 新建 Skill 入口（`.claude/skills/<name>/SKILL.md`，P5 分支）

## 不适用场景

- 工作流废弃/退役 → `workflow_deprecation_workflow.md`
- 工作流版本升级（语义变更）→ 不触发本工作流（各文件 self-contained frontmatter 版本）
- 已有工作流的文档修复 → `documentation_update_workflow` 漂移检测管线

---

## 前置条件

| 依赖 | 用途 | 条件 |
|------|------|------|
| `workflow_index.md` | 注册 §1 全景树 + §2 注册表 | 存在且可写 |
| `version_registry.md` | §2 版本桶更新 | 存在且可写 |
| `check_workflows.py` | 注册完整性验证（G1–G6） | Python 环境 |
| `chain_template_catalog.md` | 链模板触发域评估 | 存在（若需评估） |

---

## 工作流步骤

### Phase 0: 输入解析

收集以下输入（用户提供或从上下文推断）：

| 字段 | 必填 | 说明 |
|------|:---:|------|
| 工作流名称 | ✅ | 文件名（`<name>_workflow.md` 或 `<name>.md`） |
| 所属层 | ✅ | 全局层 / 领域层 / References 专项层 / 元层 |
| 一句话职责 | ✅ | 注册表 §2 的「一句话职责」列 |
| 是否动态工作流 | ✅ | `.js` 脚本 → P4 分支 |
| 是否 Skill | ✅ | `SKILL.md` → P5 分支 |
| 关联链模板 | ❌ | 若链模板触发域 → P6 |

### 0.3 退出条件（🔴 必须全部满足方可进入 Phase 1）

- [ ] 工作流名称已确定（含目标文件路径）
- [ ] 所属层已确定（全局/领域/References/元层）
- [ ] 一句话职责已撰写
- [ ] 是否动态工作流 / 是否 Skill 已判定
- [ ] 关联链模板已评估（有/无）

### 0.4 失败处理（🔴 不得跳过）

- 输入信息不足（缺名称/所属层/职责）→ 🔴 阻断，向用户补齐
- 目标文件已存在 → 🔴 阻断，提示走版本升级而非创建

---

### Phase 1: 生成标准化 frontmatter

按模板生成新工作流的 frontmatter（插入在 YAML 闭合 `---` 之前）：

```yaml
project_version: "<当前项目版本，读 lab/pyproject.toml 或 version_registry.md §1>"
language: "zh"
last_updated: "<当日 YYYY-MM-DD>"
compatible_project_version: ">= 0.5.0"
category: "ai_workflow"
purpose: "<稳定创建目的声明——解决什么问题、扮演什么角色，跨版本升级保持不变>"
tags: [<职责相关标签>]
changelog: "初始版本——<一句话职责>（<当日 YYYY-MM-DD>）"
related:
  - <关联工作流/设施文件>
```

**强制字段**（`check_workflows.py` G1 校验）：`project_version` / `last_updated` / `language` / `purpose` 必须非空。

> 🔴 2026-08-31 起**不再有 `workflow_version` 字段**（文件级版本号退役）——不要生成它，G1 也不校验它。

**执行稳定性加固**（🆕 遵循工作流执行稳定性 P0 方案）：元层/操作型工作流默认添加
`execution_mode: strict` + `completion_marker: "🔴 CHAIN_COMPLETE"` + `max_retry_per_phase: 3` + 逐 Phase 退出条件/失败处理块。

### 1.4 退出条件（🔴 必须全部满足方可进入 Phase 2）

- [ ] frontmatter 已生成：`project_version` / `last_updated` / `language` / `purpose` 非空
- [ ] changelog 已含 wf-1.0 初始条目（含日期）
- [ ] related 已列出关联文件（若适用）
- [ ] 已按 P0 加固约定决定是否添加 execution_mode 块

### 1.5 失败处理（🔴 不得跳过）

- frontmatter 缺强制字段 → 重试补齐（消耗 max_retry_per_phase）
- YAML 语法错误 → 🔴 阻断，人工修复格式

---

### Phase 2: 写入 workflow_index.md 注册

更新 `ai_system/workflows/workflow_index.md`：

1. **§1 全景树**：在对应层级位置新增条目行
   ```
   ├── <name>.md                 [<所属层>] 🆕 (wf-1.0) — <一句话职责>
   ```
2. **§2 注册表**：在对应分层小节（2.1 全局 / 2.2 领域 / 2.3 References / 2.5 元层）新增一行
   ```
   | `<name>.md` | 🆕 | <一句话职责> |
   ```
3. **七层结构计数**：更新对应层 active 计数 + 总计（65→N 定义文件 / 66→N 注册）
4. **changelog**：frontmatter 追加 `初始版本——<职责>（YYYY-MM-DD）`（🔴 不写 `wf-X.Y→wf-X.Y+1` 版本前缀、不 bump `workflow_version`——该字段已退役）
5. **last_updated**：更新为当日

### 2.4 退出条件（🔴 必须全部满足方可进入 Phase 3）

- [ ] §1 全景树已新增条目
- [ ] §2 对应分层小节已新增注册行
- [ ] 七层结构计数已更新（层计数 + 总计）
- [ ] changelog 已追加（日期标记，非版本号）
- [ ] `last_updated` 已更新

### 2.5 失败处理（🔴 不得跳过）

- 层级判定不清 → 参照 §1 七层结构定义 + 既有同类工作流归属
- 计数更新遗漏 → 依赖 Phase 7 check_workflows.py G3 捕获

---

### Phase 3: 更新 version_registry.md §2 版本桶

更新 `ai_system/version_registry.md` §2：

1. 在对应版本桶行（如「— 其中 wf-1.0 文件」）追加新工作流：
   - 计数 +1
   - notes 的 active 列表追加文件名
   - 若无对应版本桶行 → 新增一行
2. 若 `workflow_index.md` 版本已 bump（Phase 2）：
   - 「workflows (体系)」行版本号 + 注释同步
   - 旧版本桶计数 -1 → 新版本桶 +1（workflow_index 自注册移动）

### 3.4 退出条件（🔴 必须全部满足方可进入 Phase 4）

- [ ] 新工作流已计入对应版本桶（计数 + 文件名列表）
- [ ] workflow_index 版本 bump 已同步（若 Phase 2 发生）
- [ ] 无计数漂移（与磁盘实际文件数一致）

### 3.5 失败处理（🔴 不得跳过）

- 计数漂移 → 运行 `python ai_system/validation/check_workflows.py --fix` 自动修正桶计数
- 桶行不存在 → 新增标准格式行

---

### Phase 4: 动态工作流注册（仅当动态工作流）

> 仅当 Phase 0 判定「是否动态工作流 = 是」时执行；否则跳过（N/A）。

在 `.claude/workflows/README.md` 注册新 `.js` 动态工作流：

- 表格新增行（文件 / 调用方式 / 参数 / 对应 MD）
- 确认既有动态工作流（`.claude/workflows/*.js`）不受影响

### 4.4 退出条件（🔴 必须全部满足方可进入 Phase 5）

- [ ] `.claude/workflows/README.md` 已注册（若为动态工作流）
- [ ] 非动态工作流 → 本 Phase 标记 N/A 跳过

### 4.5 失败处理（🔴 不得跳过）

- README 表格格式错乱 → 参照既有行修复

---

### Phase 5: Skill 注册（仅当 Skill 入口）

> 仅当 Phase 0 判定「是否 Skill = 是」时执行；否则跳过（N/A）。

在 `.claude/skills/README.md` 已注册表新增行：

| Skill | 调用方式 | 封装对象 | 核心价值 |

- 确认 `description` 触发词覆盖中英文
- 确认 `allowed-tools` 与实际工具需求匹配
- 确认 `${CLAUDE_PROJECT_DIR}` 引用路径正确

### 5.4 退出条件（🔴 必须全部满足方可进入 Phase 6）

- [ ] `.claude/skills/README.md` 已注册（若为 Skill）
- [ ] SKILL.md 文件存在且 frontmatter 完整
- [ ] 非 Skill → 本 Phase 标记 N/A 跳过

### 5.5 失败处理（🔴 不得跳过）

- description 无触发词 → 补充中英文触发词
- allowed-tools 过宽 → 收窄至实际需要

---

### Phase 6: 链模板触发域评估

评估新工作流是否属于链模板触发域：

1. 检查 `chain_template_catalog.md` 中 10 个活跃链模板的步骤是否应引用新工作流
2. 若是 → 更新 `chain_template_catalog.md`（步骤引用 + 版本 bump）
3. 若否 → 记录「不适用」，不修改 catalog

### 6.4 退出条件（🔴 必须全部满足方可进入 Phase 7）

- [ ] 已评估新工作流与链模板触发域的关系
- [ ] 若属触发域 → catalog 已更新
- [ ] 若不属 → 明确记录「不适用」

### 6.5 失败处理（🔴 不得跳过）

- 不确定是否属于触发域 → 搜索 catalog 中同类工作流的引用模式

---

### Phase 7: 验证

```bash
python ai_system/validation/check_workflows.py --quiet
```

必须 exit 0（G1–G6 全部 PASS），尤其：
- G3 索引-磁盘计数匹配
- G4 版本注册表一致性
- G5 交叉引用完整性

### 7.4 退出条件（🔴 工作流终点）

- [ ] `check_workflows.py --quiet` exit 0
- [ ] G1（frontmatter）/ G3（计数）/ G4（版本桶）/ G5（引用）全部 PASS
- [ ] 无新增 FAIL

### 7.5 失败处理（🔴 不得跳过）

- check_workflows.py FAIL → 🔴 阻断，修复根因后重跑
- 计数漂移 → 运行 `--fix` 或手动修正
- 不得以「输出看起来正常」为由跳过验证

🔴 CHAIN_COMPLETE

---

## 故障处理

| 故障 | 阶段 | 处理 |
|------|:---:|------|
| 输入信息不足 | Phase 0 | 🔴 阻断，向用户补齐 |
| 目标文件已存在 | Phase 0 | 🔴 阻断，提示版本升级 |
| frontmatter 缺字段 | Phase 1 | 重试补齐；YAML 错误 → 🔴 阻断 |
| 层级判定不清 | Phase 2 | 参照 §1 七层结构 + 同类工作流归属 |
| 计数漂移 | Phase 3/7 | `check_workflows.py --fix` 或手动修正 |
| check_workflows FAIL | Phase 7 | 🔴 阻断，修复根因后重跑 |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| wf-1.0 | 2026-08-06 | 初始版本——工作流创建标准化（P1–P7 注册流程） |
| wf-1.1 | 2026-08-13 | Phase 1 frontmatter 模板加 purpose 字段（G1 强制字段 4→5 扩展） |

---

*关联工作流：[workflow_deprecation_workflow.md](workflow_deprecation_workflow.md)（废弃标准化）、[workflow_index.md](workflow_index.md)（注册表）、[proposal_audit_workflow.md](proposal_audit_workflow.md)（事中审计）*
