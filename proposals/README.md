# proposals/ — 提案落地区

本目录是 Nomos 的**方案（提案）唯一落地区**。凡需要「先设计、后执行」的变更，方案正文都写在这里。

## 什么该进这里

| 进 | 不进 |
|---|---|
| 改变目录结构 / 新增顶层目录的架构增量方案 | 一次性的小修小补 |
| 涉及不可逆操作（大规模重命名、删除、迁移）的方案 | 已有既定工作流覆盖的例行操作 |
| 引入新设施 / 退役旧设施 | 纯文档错别字修正 |
| 需要人工审批后才能执行的变更 | 已由工作流自动闭环的变更 |

判定拿不准时，看 `ai_system/workflows/G_newdir_workflow.md` 与 `ai_system/workflows/proposal_audit_workflow.md`。

## 目录组织

```
proposals/
├── README.md          ← 本文件
├── index.md           ← 提案总索引（人读）
├── _catalog.md        ← 提案目录（机器读，被 proposal-gen 消费）
├── _audit/            ← 提案审计报告输出（由 proposal-audit 写入）
└── YYYY/MM/DD/        ← 逐份提案（文件名：YYYY-MM-DD_<描述>_方案.md）
```

**日期路径深度固定为三级** `YYYY/MM/DD/`，文件名前缀日期必须与父目录名一致。

## 生命周期

```
proposal-gen 生成  →  状态：待确认
      ↓
proposal-audit 审计（写入 _audit/，产出 AUTO_FIX / SEMI / MANUAL 分级发现）
      ↓
人工审批  →  执行  →  状态：已执行
```

- 生成走 `Skill: proposal-gen`，审计走 `Skill: proposal-audit`，二者构成「生成即审计」闭环。
- **未经审批不得执行**任何方案中的变更。
- 新方案登记后，必须同步更新 `index.md` 与 `_catalog.md`。
