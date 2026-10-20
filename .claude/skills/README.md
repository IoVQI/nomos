# .claude/skills/ — 项目 Skill

> Claude Code Skills（`SKILL.md` 指令文件），通过 `/skill-name` 或 AI 自动匹配调用。
> 与 `ai_system/workflows/`（MD 规程文档）和 `.claude/workflows/`（JS 动态工作流）互补。

## 已注册

| Skill | 调用方式 | 封装对象 | 核心价值 |
|------|---------|------|------|
| `proposal-gen` | `/proposal-gen <topic>` 或自动匹配 | `proposal_audit_workflow.md`（生成侧镜像） | P0 真源采集 → P1 骨架撰写 → P2 落盘门禁 + 原子自注册 → P3 轻量自审；**生成即审计** |
| `proposal-audit` | `/proposal-audit <path> [--depth l1-l4]` 或自动匹配 | `proposal_audit_workflow.md` | 7 维审计模型（D1 路径 → D7 复用度），委托两个 `proposal-audit-*.js` 动态工作流 |
| `audit-journal` | `/audit-journal <目标索引> [full\|lite]` 或自动匹配 | 各索引的注册约定 | **索引 ↔ 磁盘**一致性审计。🔴 已覆盖的索引优先跑其机械闸门，本 Skill 只补脚本管不到的那部分 |
| `parallel-session-check` | `/parallel-session-check` 或自动匹配 | `parallel_session_launch_workflow.md` | 判「该不该并行」→ 三态输出 + 拓扑推导 + 按载体分路产出；`allowed-tools` 含 Edit，唯一用途是写 §使用记录留痕行 |
| `workflow-authoring` | `/workflow-authoring <用途构想>` 或自动匹配 | `workflow_authoring_workflow.md` | 用途构想 → 规范 → 委托创建 → 委托方案；**前端设计空白填补** |
| `workflow-explain` | `/workflow-explain <工作流名>` 或自动匹配 | `project/standards/08_工作流认知准则.md`（**准则**，非工作流） | 只读问答：按问题集讲懂单个工作流；`allowed-tools: Read, Grep, Glob` 锁死写权限；答案带 `文件:行号` 锚点 |
| `literature-review` | `/literature-review <主题>` 或自动匹配 | 本 SKILL.md 自持 | A/B/C 证据分级综述写作：**从清单到正文**那一段；内置 GB/T 7714 引文格式要点 |
| `github-push` | `/github-push` 或自动匹配 | `github_push_workflow.md` | commit + push 预检（secrets scan / 大文件 / git config / remote 可达性） |

## 三层体系的关系

```
ai_system/workflows/         ← 领域知识层（MD）
  定义「做什么」——Phase、闸门、约束、边界条件

.claude/workflows/           ← 确定性编排层（JS）
  定义「怎么编排」——agent 并发、pipeline/parallel、Schema 约束

.claude/skills/              ← 入口 + 工具授权层（SKILL.md）
  定义「怎么调用」——参数化入口、allowed-tools 预授权、description 自动发现
```

| 层 | 执行者 | 确定性 | 适用场景 |
|------|:---:|:---:|------|
| MD 工作流 | AI 手动执行 | 低（依赖 AI 解释） | 复杂多分支流程 |
| JS 动态工作流 | Workflow Runtime | 高（代码级） | 线性管线、大批量并行、需可恢复 |
| Skill 入口 | AI 自动匹配 + 手动 `/` | 中（固化工具选择） | 高频调用、多工具漂移、参数化 |

## 与 MD/JS 的协作模式

```
用户: "写个方案"
  │
  ▼
description 匹配 → Skill 加载
  │
  ├─ allowed-tools 预授权 → 锁定可用工具（消除工具漂移）
  ├─ Skill 指令路由 → 读 MD 工作流 → 执行详细 Phase 步骤
  └─ 需要确定性编排 → 调 .claude/workflows/*.js
```

Skill **不替代** MD 和 JS——它是入口层。MD 定义完整步骤，JS 提供确定性编排，Skill 提供参数化入口 + 工具预授权。

## 新增 Skill

1. 确认目标工作流适用 Skill 封装（高频调用 + 工具漂移 + 参数化收益）
2. 在本目录创建 `<skill-name>/SKILL.md`
3. 更新本 README 的已注册表

## 不纳入范围

- 个人 Skill（`~/.claude/skills/`）——跨项目可用，不由本仓库管理
- JS 动态工作流（`.claude/workflows/`）——由该目录的 README 管理
- MD 工作流（`ai_system/workflows/`）——由 `workflow_index.md` 管理
