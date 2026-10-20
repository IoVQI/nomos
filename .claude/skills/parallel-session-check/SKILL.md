---
name: parallel-session-check
description: 判断一个任务该不该拆成并行会话——对宽泛/广域任务做分解与写域图，输出三态（建议并行 N 路 + 预填会话分解方案 / 不必并行 / 先澄清）。Use when 用户给出的任务宽泛到可能拆成多条互不依赖的工作流（接单后的第一步评估）、或用户问该不该开并行会话 / 要不要把任务拆成多个会话 / 多开几个窗口值不值 / should I split this into parallel sessions / is this worth parallelizing。
allowed-tools: Read, Grep, Glob, Edit, Bash(python *)
---

# parallel-session-check — 并行会话启动建议（入口层）

## 用途

回答「**该不该开并行会话**」；判「该」时**按执行载体分路产出**（丙档 = 预填提示词；甲/乙档 = 直接派单）。它是触发器层的**入口**，
不新增判据，也不执行并行。

## 单点真源

| 内容 | 真源 |
|---|---|
| 判据 / 三态输出 / 拓扑推导 / 预填产物 | `ai_system/workflows/parallel_session_launch_workflow.md` |
| 执行协议（写入域声明 / 铁律） | `coordination/claims/README.md` |
| 串行分支（交接） | `coordination/handoff/README.md` |
| 预填目标模板 | `coordination/_aux_session_prompt_template.md` |

本 Skill **不复制任何判据**——只做入口与工具预授权。改判据改工作流，不改本文件（防第二真源）。

## 何时调用

✅ **调用**：

- 用户给出**宽泛 / 广域**指令（「把 X 领域推进一下」「项目里有点乱」），可能拆成 ≥2 条独立工作流
- 用户**显式问**「该不该开并行 / 要不要拆会话 / 多开窗口值不值」
- 会话结束仍有**可分派**的剩余工作（`chain_orchestration_workflow.md` Phase 0d-8）
- 主线即将**卡在慢 I/O**（MinerU 转录 / CI / 长 solver 扫描 / 批量下载）

❌ **不调用**（命中即静默跳过，不解释）：

- 单条工作流，拆不出 ≥2 条候选 → 会话内子代理即可
- 纯只读任务（调研 / 审计不落盘）
- 已用任务卡把写入域天然隔开（一人一篇 / 一人一个模型）

> 🔴 **反噪音条款**：本入口若对每条任务都跑，会变噪音 → 被忽略 → 孤儿化（工作流 Phase 3 已列此失败模式，
> 并引 `update_chain_tracking.py` 孤儿化为实证）。「**不必并行**」与「**先澄清**」是**一等输出**，不是失败；
> 但**不许为了显得有用而硬凑候选**。

## 执行流程

1. **读真源**：按 `parallel_session_launch_workflow.md` Phase 0–5 执行。
2. **Phase 0 输入契约**三字段齐备：请求原文（不改写）/ 用户可用窗口数 / 是否已有对等会话。
   🔴 窗口数**未知按 1 处理**——不可假设用户能开多窗口（真源同该工作流，本文件不复述该规则）。
   `ListAgents` 只答「谁在线」，**不答「在做什么」**。
3. **Phase 1 分解** → **Phase 2 判据** `可并行 = C2 ∧ (C3 ∨ C4)` 且 C1 成立 → **Phase 3 三态**。
4. **A 态** → Phase 4 拓扑推导 → Phase 5 按模板产出**每候选一份**预填提示词（四要素无空，P5-G1）。
5. **留痕（强制，三态均记）**：在 `coordination/_aux_session_prompt_template.md` §使用记录追加一行
   （日期现场取钟 / slug / 任务 / 结果 = 三态之一）。
   🔴 该表是工作流 §6.1 退役判据的**唯一证据源**；只记 A 态会让「零运行」与「恒 B 态」在证据面上同形不可分辨。
   ⚠️ 该文件是共享产物——写前用 `ListAgents` 查对等会话；被占用则把这一行记进自己的 claim 待办。
6. **时间戳**一律现场取钟：`python ai_system/validation/beijing_time.py --fmt header|filename`。

## 边界（不做的事）

- ❌ 不执行并行——那是被拉起的**辅助会话**的事（协议见 `_parallel/README.md`）
- ❌ 不写 `coordination/claims/`——claim 由被拉起的会话自己在开工第一步写（先写后查）
- ❌ 不做交接——那是 `_handoff/` 的职能
- ❌ 不复制判据表 / 三态表 / 拓扑表 / 时长下限

## 落盘

A 态产出形态**按载体分路**（判据与分路表以 `ai_system/workflows/parallel_session_launch_workflow.md` §2.3 / Phase 5 为准，本文件不复述）：

- **丙档（独立会话）**：只在对话中产出预填提示词（用户核对后自行粘贴），不写文件。
- **甲/乙档（子代理 / teammates）**：**直接派单**（`Agent`），不产提示词——派单前写死四要素与写域清单。

唯一落盘写入 = §使用记录一行（两路均须留痕）。B / C 态不产生任何文件。

## 退役判据

见工作流 §6.1——含「**零运行**」分支（三态留痕口径下，无新增行即无受众 ⇒ 与「连续 3 次未采纳」同等构成撤回信号）；
撤回动作同时包含**注销本 Skill 入口**。
