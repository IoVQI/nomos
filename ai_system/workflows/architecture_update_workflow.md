---
project_version: "0.9.0"
language: "zh"
last_updated: "2026-08-17"
compatible_project_version: ">= 0.1.0"
category: "ai_workflow"
tags: [architecture, update]
purpose: "同步架构变化：定向更新 ai_context 架构快照与模块索引，保持引用一致"
changelog: "wf-1.0: 初始版本——模块结构/导入依赖/命名规范变化时同步架构快照和模块索引（2026-05-27）"
---

# Architecture Update Workflow

## 工作流目标

本工作流用于：

当模块结构、导入依赖、命名规范、或目录布局
发生变化时，

对：

`context/`

中的架构相关 AI 上下文文件，

进行定向增量更新。

目标：

确保：

- `architecture_snapshot.md` 反映当前目录/模块结构
- `module_index.md` 反映当前模块清单和依赖关系
- `project_state.md` §2, §8-10, §13-14 反映当前架构和命名
- 所有 ai_context 文件中的模块引用保持一致

---

## 适用场景

- 新增模块（如新增 `src/<module>/xxx.py`）
- 删除模块
- 重命名模块/函数
- `__init__.py` 导出策略变化
- 目录结构调整（如 `src/<module>/plotting/` 扩展）
- 跨层依赖关系变化
- 命名规范变化
- API 签名变更（函数参数/返回值变化）

## 不适用场景

- 纯 model 物理公式变更 → 用 `eos_update_workflow.md`
- 纯 notebook 变更 → 手动维护 `project/research/` 下对应 README.md（`notebook_update_workflow.md` 已于 2026-07-15 废弃）
- 纯 validation 变更 → 用 `validation_update_workflow.md`
- 大规模跨领域重构 → 用 `full_ai_context_update.md`

---

# Phase 1 — 分析本次架构变化

分析变更内容：

- 新增/删除/重命名了哪些模块
- `__init__.py` 导出策略是否变化
- 目录结构是否变化
- 依赖关系是否变化（如模块 A 不再依赖模块 B）
- 命名规范是否变化
- 公共 API（函数签名）是否变化

输出：

# 架构变化摘要

包括：

- 变更类型（新增/删除/重命名/签名变化/结构变化）
- 影响的文件
- 影响的 ai_context 文件及节号

暂时不要修改文件。

---

# Phase 2 — 定向更新 AI Context

基于变化摘要，更新以下文件：

## 必须更新的文件

| 文件 | 更新内容 | 条件 |
|------|---------|------|
| `architecture_snapshot.md` | 目录结构、模块清单、依赖图 | 结构/模块变化时 |
| `module_index.md` | 模块条目、依赖矩阵、调用链 | 模块变化时 |
| `project_state.md` §2 | 总体架构（三层结构、铁律） | 结构变化时 |
| `project_state.md` §8 | 主要模块表 | 模块变化时 |
| `project_state.md` §9 | 模块职责表 | 职责变化时 |
| `project_state.md` §10 | `__init__.py` 策略 | 导出策略变化时 |
| `project_state.md` §13 | 命名规范（如有新规范或修正） | 命名规范变化时 |
| `project_state.md` §14 | 已废弃模块列表 | 删除模块时 |

## 可选更新的文件

| 文件 | 更新内容 | 条件 |
|------|---------|------|
| `project_state.md` §15 | 重要入口（导入示例） | API 签名变化时 |
| `project_state.md` §17 | 已知技术债务 | 如引入新债务 |
| `refactor_history.md` | 新增 R-N 条目 | 大型架构变化时 |
| `eos_pipeline.md` | 管线中的模块引用 | 管线依赖的模块变化时 |

## 更新要求

1. 不重写整个文件 — 仅更新受影响的节和行
2. 保持模块名、函数名与源码完全一致（复制粘贴验证）
3. `architecture_snapshot.md` 的依赖图必须与实际 import 语句一致
4. `module_index.md` 的依赖矩阵必须更新
5. 已废弃模块移至 `project_state.md` §14，标记废弃日期

---

# Phase 3 — 交叉验证

更新完成后，执行最小化一致性检查：

- 检查 `architecture_snapshot.md` 中的每个模块路径在磁盘上存在
- 检查 `module_index.md` 中的依赖关系与 `__init__.py` 的 import 语句一致
- 检查 `project_state.md` §14 中无已删除但仍标记为 active 的模块
- 检查 `project_state.md` §13 中的命名规范与 §4 函数签名表一致

输出：

# 架构更新验证报告

---

# Phase 4 — 执行 Consistency Audit

最后执行 `ai_context_consistency_audit.md` 作为 QA 闸门。

重点检查：

- 模块名在所有 ai_context 文件中是否一致
- 架构描述在不同文件中是否冲突
- 废弃状态是否统一标记

---

# 工作流原则

本工作流：

- 仅更新受架构变化影响的 ai_context 文件
- 不更新文档（`lab/docs/`）
- 不更新 model 物理描述（委托给 `eos_update_workflow.md`）
- 确保 AI 能从 `module_index.md` 和 `architecture_snapshot.md` 完整恢复工程认知

---

# 禁止事项

禁止：

- 整文件重写
- 忽略源码真实目录结构和 import 语句
- 在不同文件中使用不同的模块名
- 跳过 Phase 4 的 consistency_audit
- 删除模块时仅移除引用而不在 §14 记录废弃
