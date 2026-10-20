# .claude/workflows/ — 动态工作流

> Claude Code Dynamic Workflows（JS 运行时），通过 `Workflow({ name: "..." })` 或
> `Skill: <name>` 调用。与 `ai_system/workflows/`（MD 规程文档）互补。

## 已注册

| 文件 | 调用方式 | 参数 | 对应 MD / 入口 |
|------|---------|------|------|
| `proposal-audit-check.js` | `/proposal-audit-check` 或 `Workflow` | `{ proposalPath, depth? }` | `proposal_audit_workflow.md`（Skill `proposal-audit`） |
| `proposal-audit-fix.js` | `/proposal-audit-fix` 或 `Workflow` | `{ auditReportPath, proposalPath? }` | `proposal_audit_workflow.md`（Skill `proposal-audit`） |
| `proposal-gen-collect.js` | `Skill: proposal-gen` 或 `Workflow` | `{ topic, related_files?, site? }` | `Skill: proposal-gen` 的 P0 采集阶段 |

## 与 MD 工作流的关系

- MD 工作流（`ai_system/workflows/`）定义**做什么**（Phase、闸门、约束、边界条件）
- JS 动态工作流（本目录）定义**怎么编排**（agent 并发、pipeline/parallel、Schema 约束、程序化输出）
- 两者成对存在：MD 是设计文档，JS 是执行引擎
- 若仅有 MD 无 JS → 工作流由 AI 手动执行（逐 Phase 读取指令）

## 设计纪律（踩过的坑）

- 🔴 **不要硬编码项目路径**。`Workflow` 运行时**没有文件系统访问**——需要写文件时，把写入这件事
  **交给 agent 去做**（agent 有工具）。脚本里出现的路径只能作为**提示文本**传给 agent。
- 🔴 脚本是**纯 JavaScript**，不是 TypeScript——类型注解会解析失败。
- 🔴 脚本里**不能用** `Date.now()` / `Math.random()` / `new Date()`（会破坏 resume 缓存）。
  时间戳通过 `args` 传入，或在工作流返回后再盖。
- 🔴 `.gitattributes` 里 `*.js text eol=lf` 是**必须**的：CRLF 会让权限层对脚本报「控制字符」而拒绝调用。

## 新增动态工作流

1. 在 `ai_system/workflows/` 中编写 MD 工作流（Phase、闸门、约束）
2. 在本目录创建 JS 文件，实现编排逻辑
3. `meta` 中声明 `cost` profile：`{ agents: {min,max}, mandatory, gate?, notes }`——**成本提示**，
   供用户放行判断参考（不驱动自动拦截）
4. 更新本 README 的已注册表

## 不纳入范围

- `ai_system/workflows/` 下的 MD 工作流（由 `workflow_index.md` 管理）
- `.claude/` 下的其他配置文件（`settings.json` 等）
