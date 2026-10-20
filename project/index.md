---
date: "2026-10-05"
---

# project/ — 项目级活文档

> 存放跨会话持续维护的项目级活文档（判断层准则与索引）。

## 子目录

| 目录 | 描述 |
|------|------|
| [standards/](standards/) | 工作准则（序号编目）— 选题方法 / 课题推进 / 复现绘图规范 / 研究故事线 / 改进与维护宗旨 / 汇报展示 / 工作流认知 / 实验记录 / 可信度与边界陈述 |
| [ops/](ops/) | 运维知识 — 服务器 / 远程桌面 / 网络的自建设施 runbook。文档内**一律占位符**，真值在 `ops/_local/`（不入库） |
| [references/](references/) | 文献库 — **有意留置的空目录**，见其 `README.md` |
| [derivation_kb/](derivation_kb/) | 公式推导知识库 — **有意留置的空目录**，见其 `README.md` |
| [data_kb/](data_kb/) | 结构化数据知识库 — **有意留置的空目录**，见其 `README.md` |
| [domain_kb/](domain_kb/) | 领域概念知识库 — **有意留置的空目录**，见其 `README.md` |
| [lab/](lab/) | 物理程序库 — **有意留置的空目录**，见其 `README.md` |
| [meeting_notes/](meeting_notes/) | 会议与报告笔记 — **有意留置的空目录**，见其 `README.md` |
| [research/](research/) | 科研工作台账 — **有意留置的空目录**，见其 `README.md` |

## 准则的性质

`standards/` 下是**判断层文件**——它们表述「怎么想」「怎么权衡」，**不配脚本、不进 CI**。
不要试图把它们变成可执行闸门：能机械判定的东西已经放进 `ai_system/validation/`，
放不进去的正说明它依赖人的判断。
