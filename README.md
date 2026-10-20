# Nomos

**中文** | [English](README.en.md)

**一套长期人机协作的治理骨架** —— 把「工作流定义」「校验闸门」「跨会话上下文」「方案审批」
当作一等基础设施，而不是事后补的文档。

> A discipline layer for long-horizon AI-assisted work.

本仓库**不含任何具体研究内容**。它提供的是**结构、规程与闸门**：你可以把自己的材料填进预留的位置，
或者删掉用不上的部分。

---

## 为什么存在

与 AI 长期协作时，真正致命的不是「某次答错」，而是**约束的缓慢失效**：

- 上次说好的约定，这次没人记得；
- 文档里写的流程，实际没人走；
- 定了校验规则，却没有任何东西**强制执行**它；
- 会话之间没有记忆，交接全靠临场复述，而**复述就是副本，副本会漂移**。

Nomos 的回应是把这些当成工程问题处理：**约定写成文件，文件挂上闸门，闸门进 CI。**
剩下的部分——判断类准则——明确标注为「不配脚本」，不假装机械可验。

---

## 科研辅助：把研究过程变成可复算、可交接的工作流

Nomos **不替代**你的研究工具——它不检索文献、不做数值计算、不生成图表。
它管的是研究过程的**纪律层**：每个阶段该产出什么、证据放在哪里、结论能说到什么程度。

| 研究阶段 | 设施 | 解决什么 |
|---|---|---|
| 选题与立项 | [`project/standards/01`](project/standards/01_研究选题逻辑.md) + `Skill: proposal-gen` | 六阶段选题路线：领域调研 → 复现 → 候选问题 → 系统验证 → 预实验 → 问题陈述；用真实复现淘汰不靠谱方向 |
| 课题推进 | [`project/standards/02`](project/standards/02_课题推进.md) | 8 阶段框架：冻结问题 → 锁定基线 → 最小验证 → 完整实验 → 深度分析 → 同步写作 → 投稿迭代 |
| 文献工作 | `Skill: literature-review` | 四部分综述正文（背景 → 梳理 → 评述 → 参考文献）；A/B/C 证据分级防编造转述；GB/T 7714 引文格式 |
| 复现与绘图 | [`project/standards/03`](project/standards/03_复现绘图规范.md) | 输入契约、计算与绘图分离、标准图集、统一样式、默认展示窗口 |
| 实验执行与记录 | [`project/standards/09`](project/standards/09_实验执行与记录准则.md) + [`coordination/`](coordination/README.md) | 记录六问（真源 / 口径 / 规模 / 耗时 / 产物 / 状态）、计时口径、可复算判据 |
| 分析与叙事 | [`project/standards/04`](project/standards/04_研究故事线.md) | 九节点故事线、证据链、结论边界、负结果的杠杆点 |
| 汇报与展示 | [`project/standards/07`](project/standards/07_科研汇报展示准则.md) | deck / PPT / PDF 的叙事弧、溯源标注、版式保真、派生件一致性 |
| 可信度与边界 | [`project/standards/10`](project/standards/10_研究可信度与边界陈述准则.md) | 自指基准、禁锚定、防掩盖；边界句指名机制而非「存在不确定性」 |
| 方案与变更 | [`proposals/`](proposals/README.md) + `Skill: proposal-audit` | 「先设计、后执行」；7 维审计（路径 / 计数 / 索引 / 逻辑 / 注册 / 破坏性 / 复用度） |
| 跨会话与交接 | [`ai_system/context/`](ai_system/context/README.md) + `coordination/` | 上下文恢复模板；并行写入域声明与串行交接协议 |

一条典型研究主线：

```
选题 → 复现 → 预实验 → 实验记录 → 分析 → 故事线 → 汇报 → 投稿
 01     01      01        09         02      04       07      02
```

**它带来什么**：换机器、换会话、隔几个月回来，仍能回答「这个结论的证据在哪、当时怎么跑的、
哪些条件没验证」。**它不做什么**：不替你判断科学价值，不保证结论正确——那些留在判断层，
由人负责。

---

## 仓库结构

```
nomos/
├── CLAUDE.md            ★ AI 会话约定（每次会话自动加载）—— 也是最好的一份总览
├── README.md              本文件
├── README.en.md           英文版
├── VERSION                版本号单一真源
├── CHANGELOG.md           变更日志
├── .claude/               Claude Code 设施
│   ├── commands/          斜杠命令（会话收尾闭环）
│   ├── skills/            Skill 定义：把工作流包装成可调用入口
│   ├── workflows/         JS 动态工作流：确定性的多 agent 编排
│   └── settings.json      权限 allow / deny（含硬阻断不可逆 git 操作）
├── .github/workflows/     CI
├── ai_system/             AI 工程治理系统
│   ├── index.md           导航入口
│   ├── workflows/         工作流定义 + 注册表 + 使用手册
│   ├── context/           跨会话上下文恢复模板
│   ├── rules/             编码 / 调试规约
│   ├── prompts/           提示模板
│   ├── scripts/           可复用辅助脚本
│   ├── official_docs/     上游文档链接清单（镜像不随发布件分发）
│   └── validation/        校验闸门脚本
├── project/               项目级活文档 + 有意留置的空壳目录（见下）
│   ├── index.md
│   ├── standards/         科研工作准则 01–10（选题 / 推进 / 复现 / 故事线 / 汇报 / 可信度；判断层，不配脚本）
│   ├── ops/               运维知识（服务器 / 远控 / 网络；文档用占位符，真值不入库）
│   └── <空壳目录>          参考文献 / 知识库 / 程序库 / 会议记录，供你放入材料
├── proposals/             方案（提案）落地区 + 审计报告
├── coordination/          多会话协调（并行声明 + 串行交接）
├── records/               可选工作台账（备忘录 / 报告 / 会话摘要）
└── sandbox/               沙箱（实验 / 草稿 / 外部组件导入，见其 README.md）
```

---

## 快速开始

```bash
# 1) 装上 git 钩子（校验闸门会在提交时自动跑）
pip install pre-commit pyyaml
pre-commit install

# 2) 手动跑一遍全部闸门
pre-commit run --all-files

# 3) 单独验证工作流注册表
python ai_system/validation/check_workflows.py --quiet
```

**从哪读起**：
1. 本文件（你在读）
2. [`CLAUDE.md`](CLAUDE.md) —— 完整约定总览，也是 AI 会话的自动加载文件
3. [`ai_system/index.md`](ai_system/index.md) —— 治理系统的导航入口
4. [`project/standards/index.md`](project/standards/index.md) —— 判断层准则（选题 / 推进 / 汇报 / 可信度）
5. [`coordination/claims/README.md`](coordination/claims/README.md) —— 多会话协调铁律（**动手改共享文件前必读**）

---

## 有意留置的空目录

以下目录**是有意留空的**——保留路径约定，供你放入自己的材料。
每个目录内有一份 `README.md` 说明用途；不需要就直接删掉整个目录。

| 目录 | 原本承载 |
|------|---------|
| [`project/references/`](project/references/README.md) | 文献库（论文 PDF 与元数据 .md 成对存放） |
| [`project/derivation_kb/`](project/derivation_kb/README.md) | 公式推导知识库（推导文档 + 验证记录） |
| [`project/data_kb/`](project/data_kb/README.md) | 结构化数据知识库（模型注册表 / 基准值 / 观测约束） |
| [`project/domain_kb/`](project/domain_kb/README.md) | 领域概念知识库（术语 / 概念 / 研究方向） |
| [`project/lab/`](project/lab/README.md) | 物理程序库（数值代码 + 人类文档） |
| [`project/meeting_notes/`](project/meeting_notes/README.md) | 会议与报告笔记 |
| [`project/research/`](project/research/README.md) | 科研工作台账（主线 / 分支 / 课题） |

> 这些名字（`derivation_kb`、`lab` 等）来自本骨架的原始项目。它们只是**占位名**——
> 换成你自己领域的名字完全可以，只要同步更新引用。

---

## AI 系统怎么运作：三层

| 层 | 位置 | 性质 | 何时用 |
|---|---|---|---|
| **工作流定义** | `ai_system/workflows/*.md` | 规程：步骤、闸门、判据 | 你要弄清「一件事该怎么做」 |
| **Skill** | `.claude/skills/*/SKILL.md` | 入口：声明 allowed-tools，把工作流包成可调用命令 | 你（或 AI）要**发起**一次操作 |
| **动态工作流** | `.claude/workflows/*.js` | 执行：确定性的多 agent 编排（fan-out / 校验 / 汇总） | 任务需要并行铺开再收敛 |

**闸门**（`ai_system/validation/*.py`）是唯一机械判据，挂在两处：
`.pre-commit-config.yaml`（本地，提交时跑）与 `.github/workflows/ci.yml`（远端，干净克隆上跑）。
文档描述与脚本冲突时，**以脚本为准**。

---

## 多会话协调

会话之间没有共享记忆，**落盘信息是唯一媒介**。

| 目录 | 场景 |
|------|------|
| [`coordination/claims/`](coordination/claims/README.md) | **并行**：开工第一步写 `claims/<slug>.md` 声明写入域 |
| [`coordination/handoff/`](coordination/handoff/README.md) | **串行**：交接提示词，写给人看、粘给下个会话 |

核心只有一条：**每个文件在任何时刻只有一个写者。**

---

## 来源声明

本骨架由作者早期的一个研究项目提炼而来：**只取治理设施与基础架构，不带任何历史、数据、
文献或第三方内容**。公开仓库的 Git 历史是**发布台账**（每次发布一个提交），不是开发历史。

空目录中保留的路径名沿用自原项目，仅为占位。

## 许可

[MIT](LICENSE)
