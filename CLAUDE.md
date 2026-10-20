# CLAUDE.md — Nomos 项目约定

本文件在每次会话启动时自动加载。所有新生成的文件必须遵循此处约定。

> **Nomos 是什么**：一套**长期人机协作的治理骨架**——把「工作流定义」「校验闸门」「跨会话上下文」「方案审批」
> 当作一等基础设施，而不是事后补的文档。它不含任何具体研究内容，见 §一。
>
> 🔴 **维护本文件前先读** [《CLAUDE.md 维护纪律》](project/standards/05_CLAUDE.md维护纪律.md)（准入 / 退场 / 对账）。

---

## 一、仓库结构

```
nomos/
├── CLAUDE.md            ★ 本文件（每次会话自动加载）
├── README.md               面向新人的入口
├── .claude/                Claude Code 设施
│   ├── commands/           斜杠命令（会话收尾闭环）
│   ├── skills/             Skill 定义（各领域操作入口）
│   ├── workflows/          JS 动态工作流（确定性多 agent 编排）
│   └── settings.json       权限 allow / deny
├── .github/workflows/      CI
├── ai_system/              AI 工程治理系统
│   ├── index.md            导航入口
│   ├── workflows/          工作流定义 + 注册表 + 使用手册
│   ├── context/            跨会话上下文恢复模板
│   ├── rules/              编码 / 调试规约
│   ├── prompts/            提示模板
│   ├── scripts/            辅助脚本（含 reusable/）
│   ├── official_docs/      上游文档链接清单（镜像不随发布件分发）
│   └── validation/         校验闸门脚本
├── project/                项目级活文档 + 有意留置的空壳目录（见 §二）
│   ├── index.md
│   ├── standards/          科研工作准则 01–10（判断层，不配脚本）
│   ├── ops/                运维知识（服务器 / 远控 / 网络；文档用占位符，真值不入库）
│   └── <空壳目录>           参考文献 / 知识库 / 程序库 / 会议记录，供你放入材料
├── proposals/              方案（提案）落地区 + 审计报告
├── coordination/           多会话协调（并行声明 + 串行交接）
├── records/                可选工作台账（备忘录 / 报告 / 会话摘要）
└── sandbox/                沙箱（实验 / 草稿 / 外部组件导入，见其 README.md）
```

### 有意留置的空目录

`project/references/`、`project/derivation_kb/`、`project/data_kb/`、`project/domain_kb/`、`project/lab/`、`project/meeting_notes/`、`project/research/`
**是有意留空的**——它们保留路径约定，供你放入自己的材料。每个目录内有一份 `README.md` 说明用途。
真值表见 [README.md](README.md) 的「有意留置的空目录」一节。

---

## 二、计数描述退役原则

文档中的**纯描述型计数**（「N 个文件」「N 篇论文」）退役——它们不驱动行为、不参与校验，
却随每次增删漂移，且无机制保证正确。需要规模信息时**现场取实盘**，不在文档里写死。

**判定三问**（三问皆否 → 退役）：

| # | 问题 | 否 | 是 |
|:---:|------|------|------|
| 1 | 该数字驱动什么吗（触发流程 / 构成阈值）？ | 倾向退役 | 保留 |
| 2 | 它参与自动校验吗（有脚本拿它对账）？ | 倾向退役 | 保留 |
| 3 | 删掉它，读者失去的是「规则」还是仅「规模感」？ | 规模感 → 退役 | 规则 → 保留 |

- **保留**：校验断言（**不列举**——真值 = 各校验脚本自身的活跃闸门声明）、规则阈值（「≥5 文件重命名需确认」）、历史冻结文本（`*_history.md` 等）
- **退役写法**：改为真值指针，例：`workflows/  # 工作流定义 + 注册表 + 使用手册（真值：ls ai_system/workflows/*.md）`
- **退役写法②（树注记）**：目录树/索引里的**内联规模计数**（`← 11 个核心模块`）用**「名目保留、计数去除」**——去掉数字、留下名目与列举。
  🔴 **格式契约里的列数保留**（`15 列` 保留；退役的是 `4 行头` 一类偶然量）。

---

## 三、提案（方案）体系

`proposals/` 是**方案唯一落地区**。凡需要「先设计、后执行」的变更，方案正文都写在这里。

| 设施 | 位置 |
|------|------|
| 方案正文 | `proposals/YYYY/MM/DD/YYYY-MM-DD_<描述>_方案.md`（三级日期路径，文件名日期须与父目录一致） |
| 人读索引 | `proposals/index.md` |
| 机器目录 | `proposals/_catalog.md`（被 `Skill: proposal-gen` / `proposal-audit` 与 JS 工作流消费） |
| 审计报告 | `proposals/_audit/` |

**生成即审计闭环**：所有方案统一走 `Skill: proposal-gen`（生成时 P0–P3 门禁），
与 `Skill: proposal-audit` 形成闭环。方案状态 `待确认` 期间**不得执行**。

**自注册**：写入方案后**同一批操作**完成——追加行到 `_catalog.md` §二表顶 + 更新其 `last_updated`
+ 追加到 `index.md`。**skip-if-present 守卫**：注册前 grep 文件名，已存在则跳过。
🔴 **不维护任何计数键**（`total_entries` 等已退役）——真值 = 表行实盘。

完整规范见 [ai_system/workflows/G_newdir_workflow.md](ai_system/workflows/G_newdir_workflow.md)
与 [ai_system/workflows/proposal_audit_workflow.md](ai_system/workflows/proposal_audit_workflow.md)。

---

## 四、工作流体系

工作流定义位于 `ai_system/workflows/`，入口索引为 [workflow_index.md](ai_system/workflows/workflow_index.md)，
使用手册为 [workflow_usage_guide.md](ai_system/workflows/workflow_usage_guide.md)。

三层结构（别混）：

| 层 | 位置 | 性质 |
|---|---|---|
| **工作流定义** | `ai_system/workflows/*.md` | 规程：步骤、闸门、判据。**人/AI 读的说明书** |
| **Skill** | `.claude/skills/*/SKILL.md` | 入口：把工作流包装成可调用的斜杠命令，声明 allowed-tools |
| **动态工作流** | `.claude/workflows/*.js` | 执行：确定性的多 agent 编排（fan-out / 校验 / 汇总） |

关键工作流：

- `workflow_creation_workflow.md` / `workflow_authoring_workflow.md` — 新建与编写工作流
- `workflow_deprecation_workflow.md` — 工作流退役
- `proposal_audit_workflow.md` — 方案 7 维审计
- `documentation_update_workflow.md` — 文档增量同步
- `parallel_session_launch_workflow.md` — 判「该不该并行 / 该不该交接」

> 🔴 新增/修改工作流后必须运行 `python ai_system/validation/check_workflows.py`。

---

## 五、会话协调

多个会话同时或先后在同一仓库工作时，靠 [`coordination/`](coordination/README.md) 协调。
**会话之间没有共享记忆，落盘信息是唯一媒介。**

| 目录 | 场景 |
|------|------|
| `coordination/claims/` | **并行协调**——开工第一步写 `claims/<slug>.md` 声明写入域 |
| `coordination/handoff/` | **串行交接**——用户提到「交接 / 上个会话 / 接着做」时先读 `handoff/active/` |

🔴 **核心纪律：每个文件任何时刻只有一个写者。**
要改的路径已被他会话声明 → **停止并上报用户**，不自行合并。

**共享索引由主会话单写收口**（`ai_system/index.md`、`project/index.md`、`proposals/index.md`、
`ai_system/official_docs/index.md`、各 `README.md` 注册表）。无主会话时会话只读，
把待登记项写进自己 claim 的「待办」。

完整铁律见 [coordination/claims/README.md](coordination/claims/README.md) §3——**动手改共享文件前必读**。

---

## 六、时间戳对齐规则（北京时间，强制）

所有由 AI 写入文件的时间戳必须对齐**真实北京时间（UTC+08:00, China Standard Time）**，
小时-分钟精度为最低要求（文件名保留秒 `HHMMSS` 以保证唯一性）。

**规范时钟源**：写任何时间戳前，先运行：

```bash
python ai_system/validation/beijing_time.py --fmt iso       # 2026-08-16T16:23:51
python ai_system/validation/beijing_time.py --fmt filename  # 20260816_162351
python ai_system/validation/beijing_time.py --fmt header    # 2026-08-16 16:23
python ai_system/validation/beijing_time.py --fmt date      # 2026-08-16
python ai_system/validation/beijing_time.py --fmt hhmm      # 1623
```

**禁止**：

1. **臆造/猜测/凭记忆回填**时间戳（实证：文件声称 13:30 但 mtime 12:32）。
2. **依赖 `TZ=Asia/Shanghai date`**——部分 Git Bash 环境不解析 tzdata，静默返回 UTC；
   POSIX `TZ=UTC+8` 符号相反，同样错误。**唯一可靠来源是 Python**（`zoneinfo('Asia/Shanghai')`
   或 `timezone(timedelta(hours=8))`）。
3. **手写追踪 YAML**——须通过脚本创建与更新，禁止按模板手填 `started_at`。

**事件时间戳语义**：开始/完成时间在事件发生时**实时快照**；不得用整点/名义值后填。

**并行会话隔离**：每个会话为**自己的**文件实时取钟；禁止复制/推断其他并行会话的时间戳或时间线
（复制他人时间戳同样构成臆造）。

**落盘前自检**（推荐）：`python ai_system/validation/beijing_time.py --check-consistency "<刚写入的时间戳>"`
校验与当前时钟偏差 ≤ 容差（默认 60 分钟），防臆造。

---

## 七、调试纪律（强制）

遇到任何 CI 失败 / check 脚本报错 / 工作流步骤异常时，必须按以下阶段执行：

### 4 阶段门控

| 阶段 | 名称 | 必须完成 | 禁止跳过 |
|:---:|------|------|------|
| 1 | **根因调查** | 读取完整错误输出，定位到具体文件:行号；确认触发条件（哪次变更引入了问题） | 未完成 Phase 1 前，禁止提出任何修复方案 |
| 2 | **模式分析** | 同类问题是否在其他位置也存在？ | 单点修复前检查全局 |
| 3 | **假设与验证** | 单变量修改——一次只改一处；改后立即运行验证命令确认 exit code = 0 | 禁止多变量捆绑修复 |
| 4 | **实施修复** | 全部修复后，运行完整验证命令（非单文件），确认全量通过 | 禁止跳过完整验证 |

### 3 次失败规则

同一问题的修复尝试 ≥3 次均失败时，停止并区分两类：

| 类别 | 判定标准 | 处理方式 |
|------|---------|---------|
| **架构级** | 设计缺陷、系统性不一致、需跨文件重构 | 写入 `proposals/`，标记为「待确认」，转人工决策 |
| **操作级** | 遗漏更新、路径错误、格式问题 | 列出已尝试的方案 + 每次的失败原因，请求用户指导 |

### 红旗信号

出现以下想法时，**立即停止**，返回 Phase 1：

- "先快速修一下，之后再深入调查"
- "试试改 X 看看行不行"
- "跳过验证，我手动检查"
- "应该就是这里的问题，直接改"

### 验证命令不可执行时的处理

当验证命令因环境问题无法完整执行时（如 GBK 崩溃、依赖缺失）：

1. **区分新旧** — 确认哪些 Gate 是预存失败、哪些是本会话引入的。
   若命令在中间崩溃，已输出的 Gate 结果有效，未输出的需单独判定。
2. **手动等价检查** — 对未输出的 Gate，按其检查逻辑手动验证。
3. **已知预存问题可豁免** — 已在 `proposals/` 或 README 中追踪的预存问题，不要求本次修复。
4. **新增 FAIL → 🔴 阻断** — 本会话引入的 FAIL 必须在同一会话中修复，不得以「命令跑不完」为由跳过。

---

## 八、不可逆操作确认原则

以下操作执行前必须经用户显式确认。原则：**回滚成本 > 确认成本 → 必须先确认**。

| 操作 | 确认机制 |
|------|---------|
| 新增顶层目录 / 架构增量 | G_newdir 提案审批（`ai_system/workflows/G_newdir_workflow.md`） |
| 版本号升级（MAJOR/MINOR） | git tag + 人工决策后用户确认等级 |
| 跨目录引用创建 | 引用前确认目标存在且路径有效 |
| 大规模重命名（≥5 文件） | `AskUserQuestion` 显式确认 |
| 删除已入库内容 | `AskUserQuestion` 显式确认 + 先看目标 |

---

## 九、权限模式指引

日常推进使用 **Auto** 模式。项目 tool call 密度高（索引更新、方案生成、多会话协调），
Accept Edits 产生过多确认弹窗，拖慢推进速度。

| 场景 | 推荐模式 | 切换方式 |
|------|:---:|------|
| 日常推进（编辑 / 索引 / 生成） | **Auto** | 默认 |
| 方案设计 / 调研 | Plan | `Shift+Tab` |
| 执行不可逆操作（force push 等） | 临时切 Manual | `Shift+Tab` |

- Auto mode 安全网：classifier 后台审查 + `.claude/settings.json` 中的 deny 规则硬阻断不可逆 git 操作
- 🔴 严禁 `bypassPermissions`

---

## 十、会话边界规则

### 会话末路径

会话收尾走 **`/闭环本会话`**（[.claude/commands/闭环本会话.md](.claude/commands/闭环本会话.md)）：
时钟对齐 → 记忆沉淀 → 提交提议 → clear 就绪结论。

### 结束时自动提议 commit

会话结束前（用户告别 / 超时 / 任务完成自然结束），必须执行：

1. `git status --porcelain` 检查是否有未暂存变更
2. 若无变更 → 不操作，正常结束
3. 若有变更 → 按下表生成 commit message，展示文件清单 + 完整消息，**等待用户确认**
4. 用户确认 → 从 `git status --porcelain` 输出中提取**精确文件列表**，逐文件 `git add <精确路径> ... && git commit`
   - **🔴 禁止 `git add -A`**：精确路径模式防止误吞并行会话或其他窗口的未关联变更
   - 文件列表必须来源于步骤 1 的输出，不可凭记忆推断
   - **提交前复核**：`git diff --cached --name-only` 逐条确认均属本会话改动；
     发现并行会话文件 → `git restore --staged <path>` 撤出后再提交
   - **🔴 并行会话在场时带精确 pathspec 提交**：`git commit -m "..." -- <本次改动的精确路径…>`。
     无路径提交按 **index 整体**落盘，而对端会话的暂存件可能正停在 index 里**等其用户确认**；
     且「提交前复核」与 `git commit` 是**两次独立调用、窗口非原子**⇒ 复核通过也不保证落盘时 index 未变。
     pathspec 提交按「HEAD 树 + **该路径的工作区内容**」重建，index 里其余内容不参与 ⇒ **构造性**关闭该窗口。
     ⚠️ 与下一条并存：`git rm --cached` 类**仍须**不带 pathspec；rename 须**源与目标两条路径都喂**。
   - **🔴 子类豁免——「从索引移除但保留磁盘文件」不得走 pathspec 式提交**：
     凡 `git rm --cached` 类提交，**按 index 整体提交**（`git commit` 不带 `-- <路径>`）。
     机理：pathspec 式按「HEAD 树 + 该路径的工作区内容」重建命名路径，而 `--cached` 只把条目移出索引、
     **文件仍在磁盘** ⇒ 该路径被读作「无变化」，删除被**确定性还原**（非竞态），且原 index 中**已暂存的删除会一并丢失**。
     正确序列：`git rm --cached <paths>` → `git diff --cached --name-status` 复核只含预期条目 → **无 pathspec** 提交。
     此时**唯一有效的处置是串行化**：先确认对端会话已落定再提交，勿依赖复核快照。
   - **提交后核对**：用 `git show --name-status HEAD` 按 `A/D/M` **分类计数**与预期对照，
     **勿只看 `files changed` 总数**——删除被静默还原时总数会偏小，却不构成报警。
5. 用户拒绝 → 跳过，告知文件仍在 working tree 且不受版本保护
6. **推送**：用户本会话显式要求 push → 直接调用 github-push 技能；未显式要求 → 不主动询问

详见 [coordination/claims/README.md](coordination/claims/README.md) §3 铁律 4。

### Commit message 模板

格式：`type(scope): 中文摘要`

| 变更特征 | type | scope 来源 | 示例 |
|---------|------|-----------|------|
| 新增方案 / 报告 / 指南 | `docs` | `proposal` | `docs(proposal): add session-end auto-commit proposal` |
| 索引/元数据同步更新 | `chore` | `index` | `chore(index): sync workflow registry` |
| 修复 CI / 脚本 / 格式问题 | `fix` | 文件名 | `fix(ci): correct check_workflows.py working-directory` |
| 重构（rename / 目录重组） | `refactor` | 目录名 | `refactor(ai_system): relocate validation scripts` |
| 新增工作流 / 自动化流程 | `feat` | `workflow` | `feat(workflow): add reference location audit workflow` |
| 删除 / 退役文件 | `chore` | `decommission` | `chore(decommission): retire obsolete gate` |
| 混合变更（无法单一归类） | `chore` | `sync` | `chore(sync): full-project session sync` |

Subject 要求：中文，≤72 字符；用 `+` 连接多个子操作（≤5 个，超出则概括）；body 中按类别列出文件清单。

### 不纳入自动 commit 的范围

- `.claude/` 下的会话内部文件（由 Claude Code 自行管理，见 `.gitignore`）

---

## 十一、默认工作方式

- **先读后改**：改任何共享文件前，先读 [coordination/claims/README.md](coordination/claims/README.md) §3 铁律。
- **方案先行**：架构级变更先走 `Skill: proposal-gen`，状态 `待确认` 期间不执行。
- **闸门即真理**：`ai_system/validation/` 下的脚本是唯一机械判据；文档描述与脚本冲突时**以脚本为准**。
- **不造第二真源**：信息只在一处定义，其余位置放指针。
- **如实报告**：测试失败就说失败并给出输出；跳过某步就说跳过；完成且验证过就直说完成，不模糊措辞。
