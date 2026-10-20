---
name: workflow-explain
description: 读懂一个工作流——针对 ai_system/workflows/ 下的指定工作流，按 project/standards/08 的问题集作答（触发条件/磁盘影响/关系位置/结构可维护性），全程只读并附文件:行号锚点。Use when the user asks 某个工作流是干什么的 / 它跑完会改我哪些文件 / 从哪里入手优化它 / explain a workflow / what does this workflow do。
allowed-tools: Read, Grep, Glob
---

# workflow-explain — 工作流认知辅助

## 用途

回答用户对**某一个** `ai_system/workflows/*.md` 工作流的理解性问题。**只读**：不修改任何文件（除非用户显式要求落盘答案）。

## 单点真源

- **问题集 + 取证纪律**：`project/standards/08_工作流认知准则.md`（§1 问题集 / §2 取证纪律 / §3 生长机制 / §5 退役判据）
- 本 Skill **不复制**问题集——只引用。改问题集改准则，不改本文件。

## 执行流程

1. **定目标**：从用户输入解析目标工作流文件名。歧义（如「那个审计的」）→ 用 Glob 列候选让用户确认，**禁止猜**。
2. **只读取材**（全部只读）：
   - 目标文件本体 `ai_system/workflows/<name>.md`
   - 其在 `workflow_index.md` §2/§3 的登记行
   - 其在 `chain_template_catalog.md` 的链步骤引用（若有）
   - 其**消费者**：`grep -rn "<name>" ai_system/ .claude/ CLAUDE.md`（区分「指令性引用」与「历史注记」）
3. **按 `standards/08 §1` 的问题集作答**，遵守 §2 五条取证纪律：
   - 每个答案带 `文件:行号` 锚点
   - 明确区分「逐字写着 / 推出 / 未记载」
   - 范围限于该工作流 + 其注册/消费点，不外推
   - **不扇出子代理**（单会话内完成）
4. **作答后追问**（`standards/08 §3` 生长循环）：输出一句「读下来你还有哪卡住 / 想追问什么？」
5. **用户提问若属通用问题** → **提议**新增为 `standards/08 §1` 条目（含 source 日期+提问者），**经用户确认后**才写入。
   —— 未经确认不得改准则。
6. **退出**：用户显式说「不用了 / 够了」。

## 落盘（可选，默认不落）

默认只在对话中作答。用户显式要求落盘时才写 `ai_system/workflows/_qa/<slug>.md`，并在文件头记
「源文件最后核对日期 + 源文件 mtime」——失效判据复用 `check_references.py` G7 的「声明日期 vs mtime」**模式**（跨文件泛化：此处比的是**目标工作流的 mtime**），不发明新机制。

> ⚠️ **v0.1 默认不落盘**。启用条件见方案 §7 分期判据。

## 边界（不做的事）

- ❌ 不修改被解释的工作流；不改 `workflow_index.md` / `workflow_usage_guide.md`
- ❌ 不做审计（不产出 finding / 健康度）——那是 `chain_template_audit_workflow` 的职能
- ❌ 不评价工作流好坏（用户要的是「读懂」，不是「打分」）
- ❌ 不跨工作流做体系级综述——那是 `workflow_usage_guide.md` 的职能

## 退役判据

见 `project/standards/08 §5`（三条件）。
