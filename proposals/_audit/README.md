# proposals/_audit/ — 提案审计报告输出

本目录存放 `Skill: proposal-audit` 与 `.claude/workflows/proposal-audit-check.js` 产出的审计报告。

## 产出物

| 文件 | 由谁写 | 内容 |
|---|---|---|
| `YYYY-MM-DD_<方案名>_audit.json` | `proposal-audit-check.js` | 结构化发现（7 维模型，含 `AUTO_FIX` / `SEMI` / `MANUAL` 分级） |
| `YYYY-MM-DD_<方案名>_audit.md` | `proposal-audit-check.js` | 同上的 Markdown 报告，供人工复核 |

## 组织

按方案日期分子目录：`_audit/YYYY/MM/DD/`。

## 修复

`AUTO_FIX` 级发现由 `.claude/workflows/proposal-audit-fix.js` 自动回改方案正文；
`SEMI` / `MANUAL` 级留给人工决策，不在自动修复范围内。

> 本目录替代了早期项目中被删除的 `ai_system/audit/proposals/`。
