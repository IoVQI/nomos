# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
版本号真源是仓库根目录的 [`VERSION`](VERSION) 文件。

## [Unreleased]

## [1.0.4] - 2026-10-20

### Changed

- 全面通用化发布件：移除原项目研究标识与内部路径，包括 `lab` 项目结构、模型/求解器专名、
  具体案例名与内部台账路径。
- `ai_system/rules/coding_rules.md` 重写为通用科研编码规范（单位、验证、回归、可复现性）。
- `workflow_usage_guide.md` 重写为简洁的通用选择指南。
- 删除已废弃/项目特定的 `session_report_workflow.md` 与 `portability_refactor_workflow.md`，
  同步更新注册表与引用。
- 新增可选 `records/` 台账骨架（备忘录 / 报告 / 会话摘要）。
- 发布历史改为单提交；提交与标签使用 GitHub noreply 身份。

## [1.0.3] - 2026-10-20

### Changed

- 清理 `project/standards/` 中的过程记录：移除非方法性的日期、版本状态、内部路径、
  具体案例名、提交哈希、工作台账编号与变更史。
- `03_复现绘图规范` 文件重命名并去除具体案例名，
  内容改为通用的可复用模式与默认展示窗口。
- 04 / 05 / 06 / 07 / 08 / 09 / 10：把项目特定案例改为通用反例或一般化说明，
  保留全部方法论、判据与检查清单。
- `standards/index.md`：只保留准则表与维护规则，不再维护状态、版本与历史注记。
- 同步更新 README、CLAUDE.md 中对 03 文件名与准则编号的引用。

## [1.0.2] - 2026-10-20

### Changed

- `README.md` / `README.en.md`：新增「科研辅助」章节，按研究阶段映射设施
  （选题、推进、文献、复现绘图、实验记录、故事线、汇报、可信度、方案审计、跨会话交接）。
- 补充一条典型研究主线图（选题 → 复现 → 预实验 → 记录 → 分析 → 故事线 → 汇报 → 投稿）。
- 修正目录树中准则编号为 `01–10`，并标注科研属性。

## [1.0.1] - 2026-10-20

### Fixed

- `check_public_hygiene.py`：移除脚本内硬编码的源项目名；开发路径检测改为通用规则。
- `check_public_hygiene.py`：`git ls-files` 输出按 UTF-8 解码，避免 Windows GBK 环境崩溃。
- `project/standards/01`、`02`：移除来源注释中的内部绝对路径，改为普通说明。
- `RELEASE_NOTES/v1.0.0.md`：修正 LICENSE 相对链接。
- 发布件开始包含 `RELEASE_NOTES/`，便于离线查阅发布说明。

## [1.0.0] - 2026-10-20

### Added

- 首次公开发布：治理骨架（workflows / gates / context / proposal approval）。
- `VERSION`、`CHANGELOG.md`、`RELEASE_NOTES/`、`SECURITY.md`、`CONTRIBUTING.md`。
- 英文 README（`README.en.md`）。
- `ai_system/context/_templates/`：跨会话上下文文件的空白模板。
- GitHub Issue / Pull Request 模板。

### Changed

- 版本真源统一为根目录 `VERSION`；`ai_system/version_registry.md` 改为指针。
- CI 移除失效的 `official_docs` 镜像闸门。
- 发布路径与远端仓库参数化（`IoVQI/nomos` 公开、`IoVQI/nomos-dev` 私有）。

### Removed

- 发布件中不含：开发过程记录、个人运维知识、原项目上下文快照、第三方官方文档镜像。
- 未随发布件分发 `ai_system/scripts/researchers/`（保留目录说明）。

### Security

- 发布流水线新增白名单构建、敏感信息扫描、个人路径扫描与发布后一致性核验。
