---
name: proposal-gen
description: >
  Generate a proposal (可执行方案) following the 7-dimension proposal-audit model
  (D1 路径 → D7 复用度) as generation-time gates. Entry parses a natural-language
  requirement/background/constraints into an input contract, then runs P0 (fact collection,
  delegated to the proposal-gen-collect.js dynamic workflow) → P1 (9-section skeleton with
  per-section audit self-checks) → P2 (pre-write evidence gate + atomic self-registration) →
  P3 (post-write lightweight self-audit). Mirrors Skill: proposal-audit on the generation side
  ("生成即审计"). Use when the user asks to 写方案/生成方案/设计方案/帮我写个方案, or says
  "generate proposal"/"proposal generation"/"write a proposal"/"draft proposal", or describes a
  requirement/background and expects a proposal produced per this workflow.
argument-hint: "<背景/需求/要求描述> [site: G_newdir|literature_ingestion|chain_tier_b|general]"
allowed-tools: Bash(git *) Bash(python *) Read(*) Glob(*) Grep(*)
---

# proposal-gen — 生成侧提示词 Skill

生成可执行方案的**生成时门禁**。把 `proposal_audit_workflow.md` (wf-1.2) 的 7 维审计模型倒置为生成期自检，目标是「生成即审计、事后审计零发现」。

**单点真源**：D1–D7 审计规则 + 附录 A 失败模式库（含 A.6 41 模式分类表 + A.7 覆盖度矩阵）一律以 `ai_system/workflows/proposal_audit_workflow.md` 为准，本 Skill 不整篇复制。

---

## 入口编排 — 需求解析 → 输入契约映射

用户以自然语言描述 **需求/背景/要求** 时，先执行本步（这是显式调用「描述需求即生成」的主路径）：

0. **立项闸门**（2026-09-12 起）：先过 [`project/standards/06 改进与维护宗旨`](../../../project/standards/06_改进与维护宗旨.md)
   §1 准入四问（证据 / 归宿 / 成本 / 手段）+ §3 自律设施预算（默认拒绝·实证解锁）。
   未过闸门 → **先向用户呈现闸门结论**（哪一问未过、为何），由用户裁定是否继续；
   用户坚持继续时，在方案 §1 如实标注闸门结论与用户裁定。

1. **解析输入契约** `{ topic, background, requirements, constraints, site, related_files[] }`：
   - `topic`（主题）/ `background`（背景：为什么做）/ `requirements`（需求：做什么）/ `constraints`（要求：不做什么、复用约束）——从用户描述逐项提取，缺失项允许为空但须标注
   - `site`（生成站点）：显式指定 → 直接使用；未指定 → 按需求特征推断：文献目录架构 → `G_newdir`，入库缺口 → `literature_ingestion`，链模板修改/创建/废弃/缺口 → `chain_tier_b`，其余 → `general`
2. **推断 `related_files[]`**：从需求关键词推断候选待编辑/待引用文件（例：「工作流注册表与磁盘不一致」→ `ai_system/workflows/workflow_index.md` + `ai_system/validation/check_workflows.py`），用 Glob/Grep 验证路径存在；**推断不出或不确定 → 一次追问**（列候选让用户确认，禁止凭感觉猜路径）
3. **路由到 P0**：将 `{ topic, related_files[], site }` 作为 `proposal-gen-collect.js` 输入参数传入；`background/requirements/constraints` 作为 P1 撰写的上下文约束
4. **缺省行为**：即使未显式声明「按 proposal-gen 生成」，只要请求符合方案生成特征（描述需求+背景要求产出方案），同样进入本映射（description 触发词兜底捕获）

---

## 编排流程

**严格串行**：P0 → P1 → P2 → P3。任何阶段未通过不得进入下一阶段。

### P0 前置数据采集（pre_write，D1/D2/D4/D5/D7）

**委托 `proposal-gen-collect.js`**（`.claude/workflows/proposal-gen-collect.js`）：

1. 调用 `Workflow({ name: 'proposal-gen-collect', args: { topic, related_files, site } })`（后台运行）
2. 接收其返回的结构化事实清单：`PATH / COUNT / EDIT / REG / BLAST / CHAIN / REUSE`
3. **判断部分**由你完成（collect.js 只做确定性采集）：
   - 决策性计数核验后**重推排除/延后结论**（值错了，由它支撑的结论必须重写——FM-08）
   - 区分「工件类型名」与「字面路径」（FM-02）
   - 其余采集值（值+真源成对）**直接引用，禁止重算或写「已核验」空话**

**输出契约**：每事实 `值 = <核验值>，真源 = <绝对路径 + 位置>`；未完成任一采集块不得进入 P1。

### P1 方案撰写（during_write，D1–D7）

按下方《P1 方案撰写提示词》9 节骨架撰写，**以 collect.js 事实清单为闭集输入**（禁止新增清单外计数/路径/设施）。

### P2 落盘前自检门（pre_write，D1–D7）

按下方《P2 落盘前自检门》6 组门禁 G1–G6 逐项写出核验值；FAIL 回退 P1。

### P3 落盘后轻量自审（post_write，D1/D2/D3/D5）

按下方《P3 落盘后轻量自审》从磁盘最终位置重审；AUTO_FIX 当场修；CRITICAL 移交 `/proposal-audit`。

---

## P1 方案撰写提示词 — 标准骨架与逐节自检

### 角色与总则

你是方案撰写者。P0 事实清单已就绪。以下每一节都必须叠加《证据纪律》：

- **证据纪律（叠加到每一节，不只写在开头）**：本节每一个路径、数值、版本号、编辑锚点都必须来自 P0 事实清单并标注来源。拿不准某细节是否为真，就删掉或标注「待确认」，不要靠语感补——**写薄不算错，编细节是硬伤**。
- **闭集输入**：P0 事实清单是唯一合法输入集，撰写中禁止新增清单外的计数/路径/设施/文献（不得出现事实清单里没提过的新文件）。
- **跨节可追溯**：后文的每一个声明（计数、影响、回滚）必须能在前文或清单里找到依据。

### 九节骨架（落盘时严格对齐此标题结构）

frontmatter+元信息表 → §1 背景与动机 → §2 变更总览 → §3 详细步骤与编辑点 → §4 索引影响与自注册清单 → §5 链模板影响声明 → §6 风险与逐文件回滚 → §7 复用与选型说明 → §8 终验

### frontmatter + 元信息表（守 D2）

frontmatter 必须含 proposal_audit Phase 1a 可提取的字段：`date`、`status: 待确认`、`category`、`tags`、`related`（本方案涉及的所有文件绝对路径，逐一来自 P0）、`sources`。元信息表内：
- 所有版本号从 P0 **逐字复制**（`0.3.0` 就写 `0.3.0`，不得写 `0.3`；FM-18）
- 「预估工作量」形如 `~N 行，M 个文件`——**此数暂不填，留到 §2 完成后回填**（防跨节漂移 FM-21）
- 「schema 版本升级 / template_version 变更」声明**不得先行填写**，待 §3 完成 additive vs structural 归类后再定（防 FM-28）

### §1 背景与动机（守 D2）

自检：本节每个计数/规模描述必须带 `真源 = ...` 标注，来自 P0 COUNT 清单。禁止「约 50 篇」「十个文件」这类无法定位真源的记忆值。若某数支撑「本方案不做 X」的排除决策，必须写出「该数经核验（真源），排除/延后理由成立」。按状态计数时枚举状态类别并声明含哪些：`GO 2 篇 + CONDITIONAL GO 2 篇`，不得归并（FM-19）。

### §2 变更总览（守 D2）

本节是**跨节计数的唯一真源**，写作顺序：
1. 先写完 §3 的完整编辑表；
2. 从编辑表**实际行数**统计「修改/新建文件数」「合计行数」；
3. 回填本节总览数字与元信息表「预估工作量」；
4. 自检三项：
   - 编辑表行数 == §2 声明文件数 == 元信息表文件数（FM-21）
   - 类别计数 == 下方实际枚举的行数（FM-11：「四类问题」却列 5 行）
   - 分项之和 == 声明的总数（FM-09）
5. 若声明某节/某文件「不改动」，逐项复核 §3 编辑表里确实没有该文件（FM-30；🔴 **已由 G3b 断言 A3 机械核验**，此处只处理脚本覆盖不到的口径问题：「不改动的文件」下列了 2 个实际要改版本号的文件——声明只读、实际读写）。

### §3 详细步骤与编辑点（守 D4）

每步格式：`步骤 N：<动词> <目标文件绝对路径>`；编辑给出 `target_file` + 逐字 `old_string`→`new_string`（围栏代码块），每条前附「因为」理由。

**硬规则**：
1. **编辑锚点必须来自真实文件**。禁止凭记忆或「应有结构」写 old_string（FM-20：对实际是 YAML frontmatter 的文件写「在 Metadata 表格末追加一行」——表格不存在）
2. **按 target_file 分组、同文件编辑合并**，同文件多条 old_string 各自唯一
3. **编辑归类 additive vs structural**：新增可选字段/子节 = additive；替换列结构/改 schema = structural。structural 必须 bump 对应版本号 + 写明下游迁移/祖父规则（FM-28：4→6 列替换错判为「新增可选字段不破坏兼容性」）
4. **依赖声明前先 grep 证耦合**：无引用则标 `[]`（并行）或「组织性依赖」（FM-23）
5. **拓扑排序**：步骤图不得逆序（FM-29）
6. **边界案例**：新增判定逻辑须完整写出 `passed = ...` 表达式 + 缺失字段/异常边界行为（FM-25）
7. **图/表节点粒度 = 编辑操作粒度**：不得把 2a+2b 两次独立编辑合并为一个节点（FM-24）
8. **语义相近字段先查重**：引入新字段/枚举前 grep 已有同值集字段（FM-26：evidence_coverage vs evidence_level）
9. **声明链模板影响（守 D5）**：对被修改每个文件，依据 P0 CHAIN 清单写正向声明：「文件 X 被链 N 的 <参考点> 消费；本变更影响 = <明确描述>；缺失字段默认行为 = <明确描述>」。**禁止用「不影响」式风险免责句替代**（FM-32）
10. **跨层一致性**：复合工作流修改（MD + Skill + JS 同改）时互验三层注册引用——README 表版本号 == 对应 MD frontmatter 版本号、JS `meta.name` == Skill 委托名、新建 JS 必须引用其实现的领域 MD（FM-38）；发现漂移 → 以 MD frontmatter 为准修正
11. **§3 须自带执行指针（🆕 2026-09-14，消费点接线）**：§3 标题下写一句
    「本方案编辑点可用 `ai_system/scripts/reusable/apply_proposal_edits.py <本方案路径>` 落地
    （逐条断言命中唯一；失配即中止且不写盘；按目标文件原行尾回写）」
    —— **执行会话读的是方案本身，不是本文件**；生成侧不写明，执行侧就不知道执行器存在
    （同族实证：`update_chain_tracking.py` 孤儿化——设施无消费者等于不存在）。
12. **🔴 步骤 ID 只能用 `A`–`F` 与数字** —— `verify_proposal_anchors.py` 的判据是
    `^####\s+步骤\s+([A-F0-9]+)\s*[：:]`。写 `步骤 N1：` / `步骤 W1：`（**`N`/`W` 不在字符集内**）
    会**一个步骤头都解析不到**，全部锚点整齐落 `NO_TARGET` —— 而报错指向的文件**真实存在**，
    人易先怀疑路径而非 ID。🆕 2026-10-05：同日三份方案各踩一次（`N1`–`N8`、`W1`–`W12`）后立此条。
    📌 教训写进方案 §9 **不等于**会照做；**钉进规则才算**。
13. **🔴 标题行必须同时能解析出「含 `/` 且带白名单扩展名」的反引号路径** —— 否则该步的编辑块
    同样落 `NO_TARGET`。两个已实证的坑：① 把文件名**缩写**成 `` `project/standards/06` ``（丢扩展名）
    ⇒ 解析不出；② 本骨架的白名单里**没有 dotfile 形式**，`` `./.gitignore` `` 两个正则都不匹配
    ⇒ 改 dotfile 的步骤须写成**无 `old_string` 块的手工步骤**（先例：`sandbox` 方案的 S0、
    `迁入运维知识ops` 方案的 E2）。

### §4 索引影响与自注册清单（守 D3）

列出本方案触碰的**每一个**索引设施及其更新项（workflow_index §1/§2、chain_template_catalog、`.claude/skills/README.md`、`.claude/workflows/README.md`、`version_registry.md`、被改文件 changelog）。改计数时搜索该值**全部出现处**（FM-17）。

**自注册（本方案自身）**：写入后**同批**完成——① 追加行到 `proposals/_catalog.md` §2 表顶；② 更新其 frontmatter `last_updated` = 本方案日期；③ 追加到 `proposals/index.md` proposals 段（满足保留条件时）。**同一批操作完成**（FM-12/13/14）。

> 🔴 **不 bump 任何计数键**（2026-08-31 退役，实际不存在）：`_catalog.md` frontmatter 的 `total_entries` / `latest_entry`、
> `proposals/index.md` frontmatter 的 `catalog_proposals_entries`。照旧规程执行会去找**不存在的键**（要么空转、要么把已退役的计数设施误加回来）。
> 真值 = 表行实盘（现场数 §2 数据行），见方案 `proposals/` 中的历史方案（原项目）。

### §5 链模板影响声明（守 D5）

见 §3 规则 9。另：若本方案不落任何链触发域，显式写「本方案变更未命中 chain_template_catalog 任何触发域（依据 P0 CHAIN 清单）」作为正向声明。

### §6 风险与逐文件回滚（守 D6）

- 为**每个**被修改/新建文件列一行回滚命令：`git checkout -- <绝对路径>`（新建为 `rm <绝对路径>`），并给出「用户拒绝方案」时的整体恢复路径——**回滚段必须与文件清单等长**（FM-33）
- **废弃操作细化**：链模板/Skill/JS 废弃时——编号**保留为 deprecated**（非物理删除，除非有迁移方案）；受影响索引 active/deprecated 计数同步；运行中/已编排链引用检查（blast radius 覆盖）；catalog/README 版本号 bump；每废弃项标记 🔴 + 恢复路径或确认闸门
- **不可逆操作显式标记**：删除 / `git mv` / 废弃操作标记 🔴 + 恢复路径或确认闸门（FM-35）
- **structural 变更附加 dry-run 步骤**：先渲染一个新版产物验证再批量迁移（FM-34）

### §7 复用与选型说明（守 D7）

- 从 P0 REUSE 清单逐项说明：拟新建设施为何不被已有验证脚本/Skill/动态工作流覆盖；被覆盖则改为委托（FM-36/37/41）
- 架构选型符合 P0/P1/P2 标准并给归类理由（FM-39）：纯管线加固 `.md`（P0 strict）/ 线性动态管线 `.js`（P1）/ 高频 Skill `SKILL.md`（P2）
- 新建动态工作流 `.js` 必须引用其实现的领域工作流 `.md`（FM-38）

### §8 终验（守 D2/D3）

列出终验命令与预期退出码（真实路径来自 P0）：`python ai_system/validation/check_workflows.py`、`python ai_system/validation/verify_md_syntax.py`、`node --check` 等。凡方案触碰引用库/索引/工作流治理，终验段不得为空。新增的任何 checklist 项必须能在 §3 找到对应 old_string→new_string。

### 定稿要求

全部 9 节完成且各自自检通过后，进入 P2 落盘前自检门。

---

## P2 落盘前自检门 — 逐项证据核验 + 原子自注册

方案正文全部定稿，**尚未调用 Write/Edit 落盘**。此刻进入硬性门禁，逐项通过后才允许写文件。

对下列每一项，**必须写出具体核验值**，禁止写「已验证」「OK」这类空泛结论。任何一项 FAIL 即回到 P1 修复，不得落盘。

### G1 路径（D1）
- [ ] 方案中每个相对链接都从 `proposals/YYYY/MM/DD/` 的实际位置解析——上溯级数须数准（`..`→YYYY/MM、`../..`→YYYY、`../../..`→`proposals/`、`../../../..`→仓库根）。**写出每个相对链接的解析结果**，并确认目标文件真实存在。
- [ ] 每个绝对路径经 Glob/test 存在；不存在处已标出修正值。
- [ ] 无指向不存在目录的旧架构路径（如早期 sandbox 下的 `_parallel/`、`_handoff/`、`_scripts/`）。🔴 **裸 `sandbox/` 不是旧路径**——它是本骨架的顶层目录。
- [ ] 本方案文件自身路径符合 `YYYY/MM/DD` 深度，文件名前缀 DD == 父目录名。

### G2 计数（D2）
- [ ] 每一个数值旁写出 {核验值, 真源}。例：`ai_system/workflows/ 下 *.md = 20 个（Glob 计数，真源 = 该目录实盘）`，而非「约 10 个」。
- [ ] 决策性计数已重推结论（P0 B 块）。
- [ ] §2 总览数 == §3 编辑表行数 == 元信息表数。
- [ ] 版本号逐字等于 frontmatter（`0.3.0` 不是 `0.3`）。

### G3 编辑点与逻辑（D4）
- [ ] 每个 old_string 已对真实文件 Read 确认匹配并逐字引用。
- [ ] 🔴 **机械核验 G3b（声明面集合，2026-09-14 起必跑）**：`python ai_system/scripts/reusable/verify_proposal_declarations.py "<本方案路径>"`
      — 断言 ① §6 回滚表路径集 ⊇ §3 目标集（FM-33）② §2/元信息表声明 ⊇ §3 目标集（FM-21 集合版）③ 「不改动」集 ∩ §3 目标集 = ∅（FM-30）。
      退出码 0 方可落盘；写出汇总值（例：`声明面断言 3 / 3 通过`）。⚠️ **边界**：只覆盖集合包含关系，不覆盖跨节计数 / 步骤引用可达性 / 影响面完备性 / 检查项自反性。
- [ ] 🔴 **机械核验 G3a（锚点唯一性，2026-09-12 起必跑）**：`python ai_system/scripts/reusable/verify_proposal_anchors.py <本方案路径>`
      — 逐条断言每个 `old_string` 在目标文件中**命中恰好 1 次**（非 0 非多），退出码 0 方可落盘。
      写出汇总值（例：`命中唯一 24 / 24`）。该脚本为 FM-20 的机械护栏（§3 骨架须用
      > ℹ️ **生成期本方案 status = `待确认` ⇒ 必走全量核验**。该脚本另有一档「已执行 ⇒ 跳过」
      > （#305）：方案被执行后锚点会被消耗，此后**审计**该方案会得到 `SKIP（已执行）` + rc=0
      > ——那是**跳过、不是通过**，两者不可互读。
      `#### 步骤 X#：…` 标题行 + 围栏 `old_string:`/`new_string:` 格式，路径以反引号写在标题行内）。
      🔴 **围栏三条硬约束（2026-09-29，工作台账 #291 / #298）**——违反任一条**不会报错**，只会让块**少解析**，
      而门禁因此**静默少验**（旧版连 rc 都是 0）：
      1. **围栏行必须独立成行**（不能把开栏与 `old_string:` 写在同一行）——违反 ⇒ **一个块都解析不到**；
         #291 已加守卫：有步骤头而块数为 0 ⇒ 非零退出。
      2. **空 `new_string`（删除类编辑）须在 `new_string:` 后留一个空行**再写闭栏——违反 ⇒ 匹配**越界**，
         把**下一个块的开栏连同其内容一并吞掉**（#298 实证 2 例：`2026-09-18_计数描述退役批次3方案.md`
         与 `2026-09-28_Lackey2006…方案.md`，两处真实锚点从未被验）。
      3. **`old_string`/`new_string` 正文内不得出现独立成行的三反引号**——需要引用代码块时
         **改用更长的外层围栏**（四个反引号；这也是 `verify_md_syntax` 给同一问题的处方）。
- [ ] 🔴 **行尾归一（2026-09-12 实证；2026-09-15 订正前提）**：本仓 `.md` 的 **blob 恒为 LF**
      （`.gitattributes` 钉 `*.md text eol=lf`），但**工作区副本未必是 LF**——`eol=lf` 只在下一次 git 写出
      （checkout/stash/reset）时逐文件生效，存量文件此前保持旧行尾（`git ls-files --eol '*.md'` 2026-09-15 实测：
      `w/crlf` **689** / `w/lf` 2580）。而方案内 `old_string` 通常为 **LF**。
      任何「按 old_string 应用编辑」的动作（人工或脚本）**必须先做 `\r\n → \n` 归一再匹配、回写时还原原行尾**；
      否则**多行锚点必然失配，单行锚点不受影响**——故障呈「部分通过」的迷惑形态（2026-09-12 本次 4 个多行锚点首跑全挂）。
      > ⚠️ **行尾是易失量**（2026-09-15 实证：同一文件 18:46 测为 CRLF、18:48 被一次 pre-commit
      > 的 `checkout` 写成 LF，**两个读数都真**）⇒ 判「是否需要归一」**现场测**，不要引用任何历史读数，
      > 也不要把某次 `w/*` 读数当作跨会话的结项依据。
- [ ] 步骤拓扑无逆序；dependency 均有 grep 依据或已标注为组织性。
- [ ] 每次 structural 变更已配版本 bump 步骤 + 迁移/祖父规则。
- [ ] 无「不改动」段含需改动文件的声明（§2-5 复核通过）。
- [ ] **FM-22 补丁**：改被门控模板正文时，已重读 gate/skip 头并调和适用性声明；每个 `§N.N→§M.M` 内部交叉引用已确认指向存在章节。

### G4 注册（D3/D5）
- [ ] 每个新建设施已列出全部索引注册点（§4 清单）。
- [ ] **自注册步骤已就位**：本方案写入后 → `_catalog.md` §2 表顶追加行 + frontmatter `last_updated` 更新 → `proposals/index.md` proposals 段追加。**同一批操作完成**（FM-12/13/14）。**skip-if-present 守卫**：注册前 grep 验证行已存在则跳过。🔴 **不 bump 计数键**（`total_entries`/`latest_entry`/`catalog_proposals_entries` 已于 2026-08-31 退役，不存在）。

### G5 版本升级判定（D5）
- [ ] 若触碰版本化设施，已列版本升级为 §3 显式执行步骤（不是只在 prose 里提一句，FM-31）。
- [ ] 方案中不再有「prose 承诺了但执行表没有」的操作。

### G6 回滚与复用（D6/D7）
- [ ] 每个被改文件有回滚命令（git checkout -- / rm），回滚段与文件清单等长（FM-33）—— 🔴 **集合版已由 G3b 机械核验**；此处只确认口径（自注册文件是否单列）与人工可读性。
- [ ] 每个新建设施有复用/委托声明（§7）。

### 门禁动作

全部 PASS 后按顺序执行：
1. 写入方案文件（`proposals/YYYY/MM/DD/YYYY-MM-DD_{描述}.md`）；
2. **同批**完成自注册（G4）：`_catalog.md` 行 + frontmatter `last_updated` + `proposals/index.md`；
3. 更新 §4 清单中可在本次完成的索引项；不能本次完成的标注为「执行期步骤」。

写文件与自注册是**同一个原子动作序列**，不允许先写文件后忘记注册。

---

## P3 落盘后轻量自审 — 生成侧审计闭环

方案文件 + 自注册已落盘，向用户呈现之前。运行一次「生成侧审计」，目标：低级错误归零；若仍有 CRITICAL，交给 `/proposal-audit` 兜底。

### 自审清单

- **D1 路径**：从**磁盘上最终位置**重新解析方案中每个相对链接（含目录段数）；逐条 Glob 存在性；无旧架构路径；已修正的链接复核一次。
- **D2 计数**：重跑每个计数真源（`workflow_index.md` 实盘、目录 Glob/wc；🔴 `_catalog.md` frontmatter 计数键已于 2026-08-31 退役，改为现场数 §2 数据行），与方案正文一致；§2 总览与 §3 编辑表一致。
- **D3/D5 注册**：确认 `_catalog.md` 含本方案行（grep 文件名）且 frontmatter `last_updated` 已更新；`proposals/index.md` 含条目。🔴 无计数键可对账（`total_entries`/`latest_entry`/`catalog_proposals_entries` 均已退役）——「声明数 == 表内实际行数」这类对账随之作废。
- **变更影响**：对照 P0 BLAST 清单复核影响面声明未被缩水。

### 判定

- 全部 PASS → 呈现方案，说明「生成侧 D1–D7 自检已通过」。
- 发现 AUTO_FIX 级问题（路径/计数/索引行）→ 当场修复后重审。
- 发现 SEMI/MANUAL 级问题或修复后仍有 CRITICAL → 立即运行 `/proposal-audit`（proposal-audit-check 按 L2/I2 审计），按其 Findings 修复或提交用户决策。**不得在自审未过时直接把方案提交人工审阅。**

---

## 参考

- `ai_system/workflows/proposal_audit_workflow.md` (wf-1.2) — D1–D7 审计模型 + 附录 A 失败模式库（A.6 41 模式分类 + A.7 覆盖度矩阵）单点真源
- `.claude/workflows/proposal-gen-collect.js` — P0 采集引擎（本 Skill 委托）
- `.claude/workflows/proposal-audit-check.js` / `proposal-audit-fix.js` — 审计侧管线（P3 FAIL 时兜底）
