---
name: audit-journal
description: >
  Audit an index file against disk contents and auto-fix drift. Use when the
  user asks to audit an index, check index/directory consistency, or fix
  registry drift. Triggers on "索引审计", "audit index", "audit journal",
  "index consistency", "索引一致性".
argument-hint: "<目标索引> [full|lite]"
allowed-tools: Bash(git *), Read, Glob, Grep
---

## 索引一致性审计

对指定索引执行「**索引声明 ↔ 磁盘实盘**」的一致性审计并修复漂移。
`$ARGUMENTS` 指定目标索引与模式（默认 `full`）。

### 适用目标

| 索引 | 对账对象 | 已有机械闸门？ |
|------|---------|:---:|
| `ai_system/workflows/workflow_index.md` | `ai_system/workflows/*.md` | ✅ `check_workflows.py` |
| `ai_system/index.md` | `ai_system/` 各子模块 | ❌ 本 Skill 负责 |
| `project/index.md` | `project/` 各子目录 | ❌ 本 Skill 负责 |
| `proposals/index.md` + `proposals/_catalog.md` | `proposals/YYYY/MM/DD/*.md` | ❌ 本 Skill 负责 |
| `coordination/handoff/index.md` | `coordination/handoff/{active,consumed}/` | ❌ 本 Skill 负责 |

> 🔴 **先跑机械闸门，再上人工判断。** 标 ✅ 的索引，其一致性由脚本负责——**不要**用人工逐行比对
> 去复现一个已有闸门的结论。本 Skill 只做两类事：
> ① 没有脚本覆盖的索引；② 脚本报不出的人工判断项（如「链接指对了文件，但语义指向的是另一件事」）。
> 这正是「文档描述与脚本冲突时以脚本为准」的落地方式。

### 执行规则

1. **确定目标**：若 `$ARGUMENTS` 未给目标索引，**列出候选让用户选**——禁止凭感觉猜一个索引去改。
2. **Full**（默认）：① 抽取索引声明的每一条目 → ② 逐条验证磁盘存在（Glob/Read）→
   ③ 反向扫描磁盘，找有无**未登记**项 → ④ 产出漂移清单 → ⑤ 应用修复 → ⑥ 报告
3. **Lite**：只做 ②③ 两步，**只报不改**。
4. 🔴 **改索引前先确认**：Read 目标路径，确认它确实不存在（或确实存在），再动索引。
   共享表的引用字段尤其要**打开目标文件核对它确实是这条目该指向的东西**——
   按「最新那个文件」猜，会把一个显示错误放大成结构化事实
   （见 `coordination/claims/README.md` §3 铁律 3 的实证）。
5. 🔴 每个 Phase 须**满足退出条件**才进入下一 Phase；判定基于实际命令输出，禁止推断。
6. 完成时明确写出：审计了哪个索引 / 发现几处漂移 / 修了几处 / 未修的原因。
