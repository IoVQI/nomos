---
project_version: "0.9.0"
language: "zh"
last_updated: "2026-09-14"
compatible_project_version: ">= 0.7.0"
category: "ai_workflow"
tags: [workflow, proposal-audit, quality-gate, pre-execution-review]
purpose: "审计 Journal 方案，在人工审阅前执行 7 维自审计，标注错误并生成结构化报告"
changelog: "2026-09-14 (文件级版本号已退役，改日期标记): 声明面一致性机械化——新建 verify_proposal_declarations.py（FM-30/31/33 集合断言）并接入 P2 G3b + proposal-audit Phase 1.5；修正 D2 数据源指向的已退役键（§3a + §3b 双表，同族，memo #187 的审计侧对应）；修复 findings_by_dimension 恒零（实盘复现）；D7 去硬编码计数（49 + §8b 邻表 3 处）→真值指针。; wf-1.4: 附录 A.6 的 FM-12/13/14 计数键退役对齐（2026-09-12，方案 2026-09-12_退役total_entries手工计数族方案）——三条仍写「bump catalog 计数」的失败模式改为仅写行 + `last_updated`，补完 memo #187 只清 proposal-gen 的遗漏。; wf-1.3: Read phase I2/I3 作用域隔离——报文件名不读正文 + 排除同日期兄弟方案 + 身份锚定，修复交叉污染假阳性（2026-08-13）。; 2026-08-05: 附录 A.6/A.7 持久化——41 失败模式分类表（FM-01~FM-41，含根因 + 生成期护栏）+ 生成侧护栏覆盖度矩阵（40/41 FULLY + FM-22 补丁）；引用性增补，无规则变更; wf-1.2: 广度轴落地——D6/D7 消费 transitive_refs + chain_impacts（I2/I3 Read 阶段数据不再被丢弃）+ Phase 1 新增 §1c 影响面探索步骤；wf-1.1: 规则内联（D1-D7 常量化，消除 7× 冗余文件读取）+ 双轴模型（I1/I2/I3 影响广度轴）；wf-1.0: 初始版本——7 维审计模型（D1 路径→D7 复用度），4 级审计深度（L1–L4），Skill 入口 + 动态工作流管线混合架构"
related:
  - workflow_index.md
  - chain_template_audit_workflow.md
  - workflow_alignment_audit.md
  - journal_index_audit_workflow.md
  - .claude/skills/proposal-gen/SKILL.md  # 生成侧镜像
---

# proposal_audit_workflow — 方案审计

## Goal

在 Journal 方案被人工审阅前，AI 先执行 7 维结构化自审计，标注路径/计数/索引/逻辑/注册/破坏性/复用度问题，生成结构化审计报告。减少人工重复核查 AI 低级错误的时间。

## Audience

AI 助手

## Trigger

用户显式触发，触发短语：

- 「审计这个方案」「audit this proposal」
- 「方案审计」「proposal audit」
- 「check the proposal」「check proposal quality」

**可选参数**：
- `proposal_path` — 方案文件路径（默认：当前会话中最近生成的方案）
- `--depth l1|l2|l3|l4` — 审计深度（默认 L2）
- `--impact i1|i2|i3` — 影响广度（默认 i2）

> **生成侧镜像**：方案生成统一走 `Skill: proposal-gen`（P0–P3 生成时门禁）；P3 全部 PASS 时通常无需再跑完整审计（shift-left 成功），P3 FAIL 时移交本工作流兜底。

## Modes

| 深度 | 审计维度 | 参考工作流深度 | Agent 数 |
|:---:|------|------|:---:|
| **L1** | D1–D4 | 仅读方案本身 | 6 |
| **L2**（默认） | D1–D7 | 读方案 + grep 被引用工作流 frontmatter | 9 |
| **L3** | D1–D7 | L2 + 读被引用链模板 + 上下游工作流 §1/§2 | 9 |
| **L4** | D1–D7 | L3 + 完整阅读被引用工作流全文 | 9 |

> L3/L4 与 L2 的 agent 数相同，差异在 Phase 1 (Read) 读入上下文的深度。

### 影响广度（🆕 wf-1.1）

| 广度 | 名称 | 探索范围 | Agent 增量 | 适用场景 |
|:---:|------|------|:---:|------|
| **I1** | 显式引用 | 方案 `modified_files[]` + `related[]` 中列出的文件 | 0（当前行为） | 小范围修改（1-3 文件） |
| **I2** | 传递引用 | I1 + 对每个 modified file 执行 `grep -rl` 发现所有传递引用者 | +1 | **默认**（基础设施文件修改时） |
| **I3** | 全 blast radius | I2 + 链模板触发域交叉 + `version_registry` 消费者 + Journal 引用 | +2 | 架构级方案 |

> `--impact` 参数可选，默认 `i2`。`--impact i1` 完全等价于升级前行为。

## Prerequisites

- 方案文件存在于 `proposals/` 下
- 方案 `status: "待确认"`（已执行方案的审计由 `chain_template_audit_workflow` 负责）
- `.claude/workflows/proposal-audit-check.js` 存在（动态工作流管线）
- `.claude/workflows/proposal-audit-fix.js` 存在（自动修复管线）

## Outputs

- `ai_system/audit/proposals/{YYYY-MM-DD}/{proposal_stem}_audit.md` — 人类可读审计报告
- `ai_system/audit/proposals/{YYYY-MM-DD}/{proposal_stem}_audit.json` — 结构化 Findings（供自动修复消费）

---

## Phase 1: Read — 读取方案与上下文

### 1a. 解析参数

1. 确定 `proposal_path`（用户指定 → 最近会话产物 → 询问用户）
2. 确定 `depth`（用户指定 → 默认 L2）
3. 确定 `impact`（用户指定 → 默认 i2）
4. 读取方案全文，提取：
   - frontmatter（`related`、`status`、`tags`、`series`）
   - 所有文件路径引用（Markdown 链接 + 代码块路径 + frontmatter 路径）
   - 所有数值声明（计数、版本号、文件数）
   - 所有索引设施引用（workflow_index、catalog、registry）
   - 逻辑链（步骤依赖、闸门条件、假设）

### 1b. 读取上下文（按 depth）

| depth | 读取内容 |
|:---:|------|
| L1 | 无额外读取 |
| L2 | grep 方案 `related` 中引用的工作流 frontmatter（`last_updated`、状态） |
| L3 | L2 + 读取被引用链模板 §1/§2 + 上下游工作流 §1/§2 |
| L4 | L3 + 完整阅读被引用工作流全文 |

### 1c. 探索影响面（按 impact，🆕 wf-1.1）

| impact | 探索内容 |
|:---:|------|
| I1 | 无额外探索——仅使用方案显式声明的 `modified_files` + `related` |
| I2（默认） | I1 + 对每个 `modified_files` 中的文件执行 `grep -rl "<filename>" ai_system/workflows/ ai_system/context/ records/` → 记录传递引用者为 `transitive_refs[{source_file, discovered_refs[]}]`。🆕 作用域隔离：仅记录命中文件名+计数（不读正文），records/ 结果排除本方案同日期目录的兄弟方案+自身 |
| I3 | I2 + 检查 `chain_template_catalog.md` 中每条链模板的触发域是否被命中 → 记录为 `chain_impacts[]`；检查 `version_registry.md` §2 中受影响设施的消费者 |

### 1d. 退出条件

- [ ] 方案全文已读取
- [ ] 所有路径引用已提取为清单
- [ ] 所有数值声明已提取为清单
- [ ] 所有索引设施引用已提取为清单
- [ ] 逻辑链步骤依赖已绘制
- [ ] 按 depth 的上下文已读取
- [ ] 按 impact 的影响面已探索（transitive_refs / chain_impacts）

### 1e. 失败处理

- 方案文件不存在 → 🔴 阻断，报告「文件不存在」
- frontmatter 解析失败 → 🔴 阻断，报告 YAML 语法错误位置
- depth=L3/L4 但被引用文件不存在 → 降级为 L2 + 标注缺失文件
- impact=I2/I3 但 grep 返回空 → 降级为 I1 + 标注「传递引用扫描未发现命中」（不阻断）
- impact=I3 但 chain_template_catalog.md 不存在 → 降级为 I2 + 标注缺失文件

---

## Phase 2: D1 — 路径存在性审计

### 2a. 审计规则

对 Phase 1 提取的**每一个**文件路径引用：

- [ ] 路径指向的文件/目录存在（区分大小写，Win 不敏感但 Git 敏感）
- [ ] 相对路径基于正确的基准目录
- [ ] 路径中的文件名拼写与实际完全一致
- [ ] 不存在指向已废弃目录的旧架构路径

### 2b. 路径验证方法

```
对每个路径引用：
1. 解析为绝对路径（基准：项目根 .）
2. test -f 或 test -d 验证存在性
3. 若不存在 → 使用 Glob 搜索近似匹配（同一父目录 + 相似文件名）
4. 若 Glob 命中 → 报告「疑似拼写错误：方案写 X，实际为 Y」
5. 若 Glob 无命中 → 报告「路径不存在」
```

### 2c. 已知旧架构路径模式

| 旧路径模式 | 当前正确路径 |
|------|------|
| `<旧目录>/` | `<新目录>/` |
| `lab/docs/` | `project/lab/` |
| `docs/` | 已废弃，按内容映射到 `ai_system/` / `project/` / `records/` |
| `research_ai/` | 已重命名，按内容映射 |

### 2d. 退出条件

- [ ] 所有路径引用已验证
- [ ] 每个 FAIL 已记录：方案路径 + 实际状态（不存在/拼写错误/旧架构）

---

## Phase 3: D2 — 计数一致性审计

### 3a. 审计规则

对 Phase 1 提取的**每一个**数值声明：

- [ ] 「N 个活跃工作流」— 与 `workflow_index.md` §2 注册表**现场数行**比对（frontmatter 无计数键）
- [ ] 「M 层结构」/「总计」— 🔴 已于 2026-08-31 退役为真值指针；若方案声明此类数字，报「引用了已退役的计数设施」
- [ ] 「X 个文件修改」— 变更文件清单行数是否 = X
- [ ] 版本号（wf-x.y, ct-x.y）— 🔴 frontmatter 无该键；**不要求核对**（版本串已冻结为历史注解，见 `version_registry.md:209`）
- [ ] 方案声明了 frontmatter 字段（如 `memo_active_count`）— 🔴 该键已退役；真值 = `python ai_system/validation/check_memos.py` 实盘（🔴「X 个文件修改」的**集合版**见 §8b 机械核验）

### 3b. 验证数据源

| 方案声明的值类型 | 真源 |
|------|------|
| 活跃工作流数 | `workflow_index.md` §2 注册表现场数行 |
| 层计数 | 🔴 已退役为真值指针（2026-08-31）——声明此类数字即报「引用了已退役的计数设施」 |
| 链模板版本号 | 🔴 frontmatter 无 `catalog_version` 键；版本串为冻结历史注解，不要求核对 |
| 项目版本号 | `ai_system/version_registry.md` §1 |
| Journal 计数 | 🔴 frontmatter 计数键已退役；真值 = 现场数 `proposals/_catalog.md` §2 数据行 |
| memo 计数 | 🔴 `memo_active_count` 已退役；真值 = `python ai_system/validation/check_memos.py` 实盘 |
| Skill 数量 | `.claude/skills/` 目录下的 `SKILL.md` 文件数 |
| 动态工作流数量 | `.claude/workflows/` 目录下的 `.js` 文件数 |

### 3c. 退出条件

- [ ] 所有数值声明已验证
- [ ] 每个 MISMATCH 已记录：声称值 + 实际值 + 真源位置

---

## Phase 4: D3 — 索引完整性审计

### 4a. 审计规则

- [ ] 方案若新增工作流文件 → `workflow_index.md` §1/§2 是否声明了对应条目
- [ ] 方案若新增链模板 → `chain_template_catalog.md` 是否声明了对应条目
- [ ] 方案若新增 Skill → `.claude/skills/README.md`「已注册」表是否声明了新增行
- [ ] 方案若新增动态工作流 → `.claude/workflows/README.md`「已注册」表是否声明了新增行
- [ ] 方案若新增 Journal 文件 → `records/index.md` + `proposals/_catalog.md` 是否声明了对应条目
- [ ] 方案自身的注册（本方案在 records/index.md + _catalog.md 中是否有条目）

### 4b. 索引设施清单

| 索引文件 | 管辖范围 | 检查方式 |
|------|------|------|
| `workflow_index.md` §1/§2 | 工作流 .md 文件 | grep 文件名 |
| `chain_template_catalog.md` | 链模板 | grep 链名称 |
| `.claude/skills/README.md` | 项目 Skill | grep Skill 名称 |
| `.claude/workflows/README.md` | 动态工作流 | grep 文件名 |
| `records/index.md` | Journal 文件 | grep 文件名 |
| `proposals/_catalog.md` | Journal 方案 | grep 文件名 |
| `ai_system/version_registry.md` | 版本化设施 | grep 设施名 |

### 4c. 退出条件

- [ ] 方案声明的每个新建设施均已检查索引注册情况
- [ ] 每个 GAP 已记录：设施 + 缺失的索引位置

---

## Phase 5: D4 — 逻辑自洽性审计

### 5a. 审计规则

- [ ] 步骤间的依赖关系是否可行
- [ ] 闸门/阻断条件是否逻辑一致
- [ ] 方案摘要与具体步骤是否一致（「不改动」段与 §3 目标集的交叠**已机械化**：FM-30 由 `verify_proposal_declarations.py` 断言 A3 核验；D4 只需判断语义层的摘要-步骤一致性）
- [ ] 前提条件（Prerequisites）在方案执行环境中是否真实满足
- [ ] 方案中的假设是否与 CLAUDE.md / 其他工作流的硬约束冲突

### 5b. 常见逻辑断裂模式

| 模式 | 检测方式 |
|------|------|
| 步骤依赖倒置 | 提取所有步骤编号 + 引用关系 → 拓扑排序 → 检测环/逆序 |
| 闸门自相矛盾 | 提取所有「阻断」「重试」「跳过」关键词 → 比对同一条件的不同描述 |
| READ/WRITE 冲突 | 提取摘要中的「只读」「不修改」声明 → 检查步骤中是否有 Edit/Write/rm |
| 前提不满足 | 提取 Prerequisites 节 → 逐项验证文件/工具/环境是否存在 |
| 与 CLAUDE.md 冲突 | 提取方案的约束声明 → 比对 CLAUDE.md 的硬约束 |

### 5c. 退出条件

- [ ] 步骤依赖图已绘制且无逆序/环
- [ ] 闸门条件无自相矛盾
- [ ] 摘要与实际步骤一致
- [ ] 前提条件全部可满足

---

## Phase 6: D5 — 注册完备性审计（仅 L2+）

### 6a. 审计规则

- [ ] 新增工作流：`workflow_index.md` §1 全景树 + §2 注册表行 + §4 维护触发器评估
- [ ] 新增 Skill：名称唯一性 + description 触发词覆盖 + `.claude/skills/README.md`
- [ ] 新增动态工作流：`meta.name` 唯一 + `meta.phases` 完整 + `.claude/workflows/README.md`
- [ ] 跨层影响评估：新设施属于七层中的哪层 + 是否需要更新该层计数 + `version_registry.md`

### 6b. 退出条件

- [ ] 每个新建设施的注册完备性已验证
- [ ] 跨层影响已评估

---

## Phase 7: D6 — 破坏性评估审计（仅 L2+）

### 7a. 审计规则

- [ ] 变更影响面分析：修改的文件被哪些其他工作流/链模板引用
- [ ] 是否存在不可逆操作且无回滚方案
- [ ] 新增/修改的前端约定是否与现有文件冲突
- [ ] 若方案包含代码/脚本变更，是否建议先在 `sandbox/` 中测试

### 7b. 影响面查询

```
对每个被修改的现有文件：
1. grep -r "filename" ai_system/workflows/ — 被哪些工作流引用
2. grep -r "filename" ai_system/context/ — 被哪些上下文文件引用
3. grep -r "filename" records/ — 被哪些方案/报告引用
```

> 🆕 作用域隔离（wf-1.3）：本 grep 仅用于**爆炸半径计数**——只记录命中文件名 + 计数，**禁止读取命中文件正文**；第 3 路（records/）结果须**排除本方案同日期目录 `proposals/YYYY/MM/DD/` 下的其他兄弟方案 + 本方案自身**，避免交叉污染。

### 7c. 退出条件

- [ ] 每个被修改文件的影响面已分析
- [ ] 每个不可逆操作已标记 + 回滚方案已评估

---

## Phase 8: D7 — 已有设施复用度审计（仅 L2+）

### 8a. 审计规则

- [ ] **重复造轮子检测**：每个新建设施 vs 已有设施清单
- [ ] **委托充分性**：新建 Skill → 委托到已有工作流 .md？新建动态工作流 → 引用 .md？
- [ ] **链模板感知**：变更是否落入已有链模板触发域？是否声明了不入链理由？
- [ ] **基础设施复用**：是否利用了已有验证脚本？
- [ ] **模式一致性**：架构选择是否符合 P0/P1/P2 分类标准？
- [ ] **冗余声明检测**：是否声称「新建」了已存在的设施？

### 8b. 已有设施比对清单

| 设施类型 | 查询位置 |
|------|------|
| 已有工作流 | `workflow_index.md` §2 注册表（真值 = 现场数行，勿硬编码） |
| 已有 Skill | `.claude/skills/README.md`「已注册」表 + `~/.claude/skills/` |
| 已有动态工作流 | `.claude/workflows/README.md`「已注册」表（真值 = 现场数 `ls .claude/workflows/*.js`） |
| 已有链模板 | `chain_template_catalog.md`（真值 = `grep -c '^#### 链模板'`，含 deprecated） |
| 已有验证脚本 | `check_references.py`、`check_workflows.py`、`check_data_kb.py`、`check_kb.py`、`verify_md_syntax.py`、`cleanup_checkpoints.py`、`sandbox/_scripts/reusable/verify_proposal_anchors.py`（FM-20 锚点唯一性；🔴 工作台账 #305——方案 `status` 为 `已执行`/`已落盘` 时**默认跳过**并 rc=0，故审计**已执行**方案时「锚点预期红」不再是缺陷读数，但 `SKIP ≠ PASS`，须看横幅与 `mode` 字段）、`sandbox/_scripts/reusable/verify_proposal_declarations.py`（FM-30/31/33 声明面集合）、`domain_kb/directions/_meta/check_directions.py`（G_dir_1–5）、`domain_kb/concepts/_meta/check_concepts.py`（G_con_1–2，🆕 2026-10-01） |

### 8c. P0/P1/P2 选型标准速查

| 若方案提议… | 应满足… |
|------|------|
| `.md` 工作流加固 | P0：`execution_mode: strict` + 退出条件（高危工作流）/ 普通工作流可用 P0-lite |
| 动态工作流 `.js` | P1：线性 Phase + 结构化输出 + 固定命令 + ≤15 agents + 无运行时用户交互 |
| Skill `SKILL.md` | P2：高频调用 + 工具漂移 + `allowed-tools` 可锁定 + 参数化收益 |

### 8d. 退出条件

- [ ] 每个新建设施已比对已有设施清单
- [ ] 每个 Skill/动态工作流/工作流选型已验证 P0/P1/P2 标准
- [ ] 冗余声明已标记
- [ ] 未委托/未引用/未声明不入链理由的项已标记

---

## Phase 9: Synthesize — 合成审计报告

### 9a. 合并 Findings

将所有维度的 Findings 合并，按严重度排序：

1. CRITICAL — 必须修复（路径不存在、计数严重偏差、逻辑断裂）
2. WARNING — 建议修复（计数轻微偏差、索引遗漏、复用不足）
3. INFO — 信息提示（可选优化建议）

### 9b. 分类修复建议

| 分类 | 标准 | 示例 |
|------|------|------|
| **AUTO_FIX** | 修复方案确定且可自动化 | 路径拼写修正、计数重新加总、索引行追加 |
| **SEMI** | 需要 AI 理解上下文后修复 | changelog 追加、逻辑链重排、委托声明补充 |
| **MANUAL** | 需要用户决策 | 架构选型调整、闸门语义统一、不可逆操作确认 |

### 9c. 输出

- `_audit.md`：人类可读的审计报告，含逐 Finding 详情 + 修复建议
- `_audit.json`：结构化 Findings 数组，供 `proposal-audit-fix.js` 自动修复管线消费

### 9d. 退出条件

- [ ] `_audit.md` 已写入 `ai_system/audit/proposals/{YYYY-MM-DD}/`
- [ ] `_audit.json` 已写入同一目录
- [ ] 所有 Findings 已分类（AUTO_FIX / SEMI / MANUAL）
- [ ] 🔴 **CHAIN_COMPLETE**

---

## 附录 A：常见错误模式库

### A.1 路径类（D1）

| 模式 | 示例 | 修复 |
|------|------|------|
| 旧架构路径残留 | 指向已废弃目录的引用 | AUTO_FIX |
| 目录层级错误 | `proposals/2026/07/file.md` 缺 `DD/` | AUTO_FIX |
| 文件名拼写 | `literature_ingestion_workflow` → 实际拼写 | SEMI |
| 验证脚本路径错误 | `lab/validation/check_data_kb.py` → `data_kb/_meta/check_data_kb.py` | AUTO_FIX |

### A.2 计数类（D2）

| 模式 | 示例 | 修复 |
|------|------|------|
| 七层计数之和不等于总数 | 各层相加 ≠ 声明的总计 | AUTO_FIX |
| 版本号硬编码 | `总计: 48 active` 但实际 49 | AUTO_FIX |
| 变更文件清单行数 ≠ 声明数 | 「5 个文件」列了 6 个 | AUTO_FIX |
| 问题类别数与表行数不匹配 | 「四类问题」+ 5 行 | AUTO_FIX |

### A.3 索引类（D3）

| 模式 | 示例 | 修复 |
|------|------|------|
| 新工作流未在 §1 全景树 | 注册表有，全景树无 | AUTO_FIX |
| changelog 未追加 | `last_updated` 更新但 changelog 无新条目 | SEMI |
| 层计数字段未更新 | 元层 6→7 但 §1 文本未改 | AUTO_FIX |
| Skills/Workflows README 遗漏 | 新建 Skill 但未更新 `.claude/skills/README.md` | AUTO_FIX |

### A.4 逻辑类（D4）

| 模式 | 示例 | 修复 |
|------|------|------|
| 步骤依赖倒置 | 步骤 3 引用步骤 5 的产物 | SEMI |
| 闸门自相矛盾 | §2「阻断后重试」§4「阻断后立即停止」 | SEMI |
| READ/WRITE 冲突 | 声明「只读」但步骤中有 Edit | MANUAL |
| Pipeline 图遗漏维度 | 标题写「7 维」但图只列 6 维 | AUTO_FIX |

### A.5 复用类（D7）

| 模式 | 示例 | 修复 |
|------|------|------|
| 重复造轮子 | 新建脚本但已有 check 脚本覆盖 | MANUAL |
| 未委托已有 Skill | 新建文献搜索但 academic-search 已覆盖 | AUTO_FIX |
| 未引用已有工作流 .md | 动态工作流 .js 未引用领域知识 .md | SEMI |
| 忽略链模板触发域 | 修改 mineru 工作流但未声明链 5/6/7 影响 | SEMI |
| 选型错误 | 纯管线设计为 .md 但按 P1 应优先 .js | SEMI |
| 声称新建已有设施 | 「新建 workflow_index.md」但已存在 | AUTO_FIX |
| 未利用已有验证脚本 | 手动检查但 check_references.py 已自动化 | AUTO_FIX |
| 与已有 Skill 功能重叠 | 新建 check-paper 但 transcribe/ingest 已覆盖 | MANUAL |

### A.6 失败模式分类表（🆕 2026-08-05）

> 41 个失败模式，源自两份真实审计（2026-07-29 双轴升级 3 条 + 2026-07-31 awesome-literature-review 31 条）+ 附录 A.1–A.5 潜在模式扩展。
> **用途**：① 审计侧按根因聚类发现；② 生成侧（`Skill: proposal-gen`）按「生成期护栏」前置封堵。维度分布：D1:6 / D2:5 / D3:8 / D4:11 / D5:2 / D6:2 / D7:7。

| ID | 维度 | 根因 | 生成期护栏（proposal-gen P0–P3 前置封堵） |
|------|:---:|------|------|
| FM-01 | D1 | 未对照真实文件验证 | Resolve every relative link to its absolute target from the proposal file's ACTUAL location (depth of the YYYY/MM/DD path) before writing it. |
| FM-02 | D1 | 未对照真实文件验证 | Distinguish artifact-type names from literal paths — verify existence or annotate the first mention with the real per-paper location. |
| FM-03 | D1 | 未对照真实文件验证 | Check the workflow's 2c legacy-path table and CLAUDE.md directory conventions before writing any path. |
| FM-04 | D1 | 未对照真实文件验证 | Validate any Journal output path against the required depth table (YYYY/MM/DD, DD must match the filename date prefix) before creating the file. |
| FM-05 | D1 | 未对照真实文件验证 | Copy referenced filenames from an ls/Glob result instead of typing them from memory. |
| FM-06 | D1 | 未对照真实文件验证 | Resolve each script/command path against the on-disk location of that script before embedding it in the plan. |
| FM-07 | D2 | 计数凭记忆 | Never state a directory/registry inventory count from memory — run a Glob/wc against the real directory and quote the returned number. |
| FM-08 | D2 | 计数凭记忆 | Any number that supports an exclusion/scope decision must be verified against its source of truth AND have its cost/impact implication re-derived from the corrected value. |
| FM-09 | D2 | 计数凭记忆 | Add the component counts together at generation time and reconcile with the declared total before writing. |
| FM-10 | D2 | 计数凭记忆 | Pull registry counts from the live frontmatter/§ tables of the owning index file at generation time, never from memory. |
| FM-11 | D2 | 计数凭记忆 | Count the rows you actually generate and match the stated category count to that number. |
| FM-12 | D3 | 索引注册遗漏 | Treat index registration as atomic with file creation: append the proposal's own row to BOTH records/index.md and proposals/_catalog.md in the same write, and update _catalog frontmatter `last_updated`. |
| FM-13 | D3 | 索引注册遗漏 | Update the owning index's row and the catalog's row in the same operation; never write one in anticipation of the other. 🔴 计数键已于 2026-08-31 退役（`total_entries`/`latest_entry`/`catalog_proposals_entries` 均不存在）——只写行、不 bump 计数。 |
| FM-14 | D3 | 索引注册遗漏 | When appending a row, update the catalog frontmatter `last_updated` in the same edit. 🔴 `total_entries`/`latest_entry` 已于 2026-08-31 退役——不存在，勿 bump。 |
| FM-15 | D3 | 索引注册遗漏 | For every new facility, list every index that must declare it (workflow_index §1+§2, README registered table, version_registry) and update each in the same session. |
| FM-16 | D3 | 索引注册遗漏 | When touching frontmatter last_updated, write the matching changelog entry in the same edit. |
| FM-17 | D3 | 索引注册遗漏 | Search the target file for ALL occurrences of a count/version before changing any single occurrence. |
| FM-18 | D3 | 声明与内容不一致 | Standardize every version string to the exact frontmatter format of the referenced facility and copy it verbatim everywhere it appears. |
| FM-19 | D3 | 术语/命名冲突 | When counting by status, enumerate the exact status categories (GO vs CONDITIONAL GO vs N/A) and state which ones the count includes. |
| FM-20 | D4 | 未对照真实文件验证 | Read the target file's actual structure and quote the real old_string before writing ANY edit instruction — never write edits from a remembered or assumed structure. |
| FM-21 | D4 | 声明与内容不一致 | After finalizing the per-file edit table, recompute the summary metadata (total lines, file count) from that table and update both in the same pass. |
| FM-22 | D4 | 声明与内容不一致 | When modifying a gated template body, re-read the gate/skip header and reconcile any 'applies to all states' claim with the skip condition, and verify cross-references point to content that exists. |
| FM-23 | D4 | 未对照真实文件验证 | Before declaring a step dependency, grep the two files for mutual references; if none exists, declare [] (parallel) or label it explicitly as an organizational, non-content dependency. |
| FM-24 | D4 | 声明与内容不一致 | Match every diagram node to the exact edit-operation granularity of the execution plan (split nodes per independent Edit) before drawing it. |
| FM-25 | D4 | 未对照真实文件验证 | Fully specify every edit (exact old_string→new_string per line) and trace the boundary cases (missing field, exception) of any new logic before finalizing. |
| FM-26 | D4 | 术语/命名冲突 | Before introducing a new field/enum, grep for existing fields with the same value set and either reuse them or add an explicit cross-reference noting the distinction. |
| FM-27 | D4 | 范围/影响面低估 | Run the full grep blast-radius sweep (ai_system/workflows + ai_system/context + Journal) over every modified file and report the actual hit counts, not a hand-picked subset. |
| FM-28 | D4 | 结构性变更未声明 | Classify each edit as additive vs structural (columns/schema replaced); for any structural change, bump the facility/template version and state the migration/grandfathering rule in the same proposal. |
| FM-29 | D4 | 未对照真实文件验证 | Topologically order the step graph at generation time and verify no step consumes a later step's output. |
| FM-30 | D4 | 声明与内容不一致【🔴 已机械化 2026-09-14：`verify_proposal_declarations.py` 断言 A3——「不改动」声明集 ∩ §3 目标集 = ∅，接入 P2 G3b + proposal-audit Phase 1.5。⚠️ 方案无「不改动」段时 A3 空过，脚本显式提示】 | Re-read every section header against the items beneath it; if an item needs any edit, it belongs in a 'modified/deferred' section, never under 'not modified'. |
| FM-31 | D5 | 声明与内容不一致【🔴 部分机械化 2026-09-14：断言 A2 覆盖「声明面提及的文件 ⊇ §3 目标集」；散文承诺 vs 步骤表这一**语义层**仍由 D5 人工判断】 | Cross-check every operation promised in prose against the execution-plan step table and add a row for each declared operation. |
| FM-32 | D5 | 链影响未声明 | For every modified file, check chain_template_catalog trigger domains and write an explicit per-chain impact declaration (consumed at which reference, missing-field default behavior) rather than a risk disclaimer. |
| FM-33 | D7 | 范围/影响面低估【🔴 部分机械化 2026-09-14：断言 A1——§6 回滚表路径集 ⊇ §3 目标集。实证：2026-08-07 方案 `domain_kb/README.md` 属 §3 目标集而漏出回滚表，撰写者**计数自检**给出假 PASS（13==13，实际 14），由独立审计抓出。⚠️ A1 是「回滚表覆盖 §3」；**§3 目标集本身是否完备仍无人机械核验**】 | After finalizing the file list, enumerate one rollback command (git checkout -- <path>) per modified file and include the full recovery set in the risk section. |
| FM-34 | D6 | 未对照真实文件验证 | For any structural/template change, add an explicit dry-run step (render one artifact from the new template) to the verification plan. |
| FM-35 | D6 | 范围/影响面低估 | Flag any delete/rename/deprecate operation as irreversible and pair it with an explicit revert or confirmation gate in the proposal. |
| FM-36 | D7 | 未对照真实文件验证 | Survey the existing validation-script/facility inventory before proposing any new facility and either reuse or justify divergence. |
| FM-37 | D7 | 未对照真实文件验证 | Check the skills list for an existing covering skill and delegate to it before designing a new one. |
| FM-38 | D7 | 未对照真实文件验证 | Add the corresponding workflow .md reference to any dynamic workflow/.js you create. |
| FM-39 | D7 | 未对照真实文件验证 | Classify each new facility against the P0/P1/P2 criteria (strict gates → P0, linear dynamic pipeline → P1, high-frequency skill → P2) before designing it. |
| FM-40 | D7 | 未对照真实文件验证 | Verify existence of any facility before describing it as being created new. |
| FM-41 | D7 | 未对照真实文件验证 | Before implementing any inline check, survey existing validation scripts and either reuse/extend them or explicitly record why inline is chosen. |

### A.7 生成侧护栏覆盖度矩阵（🆕 2026-08-05）

> proposal-gen 生成时门禁（P0 真源采集 → P1 骨架撰写 → P2 落盘门禁 → P3 轻量自审）对 A.6 的覆盖验证结果：**40/41 FULLY 覆盖**，1 项未覆盖（已定位补丁，见下）。

| 覆盖状态 | 模式 | 说明 |
|:---:|------|------|
| FULLY（机械·集合层） | FM-20 / FM-21（集合版）/ FM-30 / FM-33（集合层） | 确定性脚本断言，不依赖读者注意力：FM-20 → `verify_proposal_anchors.py`（P2 G3a；🔴 工作台账 #305——对 `status` = 已执行/已落盘的方案**默认跳过**并 rc=0，故审计已执行方案时「锚点预期红」已不再是缺陷读数，但 `SKIP ≠ PASS`）、FM-30/33 + FM-21 集合版 → `verify_proposal_declarations.py`（P2 G3b + proposal-audit Phase 1.5）。🔴 **边界**：仅覆盖「声明面之间的集合包含」，**不覆盖**跨节计数 / 步骤引用可达性 / 影响面完备性 / 检查项自反性 / 声明集本身的完备性 |
| FULLY | FM-01~FM-41（除 FM-22） | P0 采集块 / P1 骨架逐节自检 / P2 门禁 G1–G6 / P3 自审 四层封堵 |
| NOT | FM-22 | 门控模板正文与 gate/skip 头适用范围矛盾 + 悬空内部交叉引用——补丁已并入 proposal-gen 设计：P2-G3 增两条（① 改门控模板正文时重读 gate 头调和适用性；② 验证 `§N.N→§M.M` 交叉引用指向存在章节），P1 §3 同步补充「门控模板正文与 gate 头一致性」规则 |

---

## 附录 B：与现有审计工作流的分工边界

| 工作流 | 审计对象 | 触发方式 | 时机 |
|------|------|------|:---:|
| **proposal_audit** 🆕 | 单个 Journal 方案 | 用户显式 | **事前**（方案执行前） |
| `chain_template_audit` | 全部链模板 | 链编排后/定期 | 事后 |
| `workflow_alignment_audit` | 工作流体系聚合 | 定期 | 事后 |
| `journal_index_audit` | records/index.md ↔ 磁盘 | 定期/用户 | 事后 |
