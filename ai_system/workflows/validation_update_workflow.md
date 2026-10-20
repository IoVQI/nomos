---
project_version: "0.9.0"
language: "zh"
last_updated: "2026-08-17"
compatible_project_version: ">= 0.1.0"
category: "ai_workflow"
tags: [validation, update]
purpose: "定向增量更新验证相关的 AI 上下文文件，确保验证注册表与引用准确反映验证函数、测试与基准值"
changelog: "wf-1.1: 当前版本——验证函数/测试文件/基准值变更时同步验证注册表和引用（2026-07-15）；wf-1.0: 初始版本（2026-05-27）"
---

# Validation Update Workflow

## 工作流目标

本工作流用于：

当验证函数、测试文件、验证结果基准值、
或验证覆盖范围发生变化时，

对：

`context/`

中的 validation 相关 AI 上下文文件，

进行定向增量更新。

目标：

确保：

- `validation_registry.md` 反映当前的验证函数和测试套件
- `project_state.md` §12 反映当前的验证体系和测试覆盖
- AI 能够执行正确的验证流程并解读验证结果

---

## 适用场景

- 新增/修改验证函数（`src/validation.py`）
- 新增/修改测试文件（`projects/*/tests/`）
- 新增/修改项目验证脚本（`projects/*/validation/`）
- 验证结果基准值更新（如 fiducial point 数值变化）
- 验证状态变化（PASS→FAIL→条件通过）
- 测试路径策略变化（`conftest.py` `_find_project_root()` 哨兵自动发现机制）
- 新增 phase 级综合验证（如 `phase6_xxx.py`）
- 回归保护规则更新

## 不适用场景

- 纯 model 物理公式变更（但需重跑验证） → 用 `eos_update_workflow.md`，然后执行本工作流更新验证状态
- 纯模块架构变更 → 用 `architecture_update_workflow.md`
- 大规模跨领域重构 → 用 `full_ai_context_update.md`

---

# Phase 0a — Pre-check (预检查)

在修改任何文件之前，执行以下预检查：

1. **读取目标 ai_context 文件**: 读入本工作流将要修改的每个 ai_context 文件
2. **检查 frontmatter last_updated**: 确认每个文件的 `last_updated` 字段
   - 若 `last_updated` 为今日日期 → 记录 "Pre-updated by [推测来源]"，跳过该文件的重复更新
   - 若 `last_updated` 为较早日期 → 继续执行更新
3. **冲突检测**: 检查 `audit/` 最近审计记录，确认无其他工作流正在修改相同文件

输出:

# Pre-check 结果

| 文件 | last_updated | 操作 |
|------|-------------|------|
| ... | ... | 更新 / 跳过 (已由 X 更新) |

---

# Phase 0b — Delegation Interface (委托接口)

本工作流在治理体系中的位置：

- **可直接修改**: validation_registry, project_state §§12, 16-17
- **必须委托**: 结构性变更 → `full_ai_context_update`；描述性增量 → `documentation_update_workflow` Phase 4
- **委托目标**: `documentation_update_workflow` Phase 4 (增量描述性更新)
- **委托链记录**: `Validation Update Workflow → ai_context 修改委托至 documentation_update_workflow`

遵循 `workflow_alignment_audit.md` 中定义的 **Compound Delegation Rule**：
禁止将结构性变更和描述性变更合并为单个委托。若更新同时涉及两者，
必须拆分为独立子任务分别委托。

---

# Phase 1 — 分析本次 Validation 变化

分析变更内容：

- 新增/修改/删除了哪些验证函数
- 新增/修改/删除了哪些测试文件
- 验证结果基准值是否变化（检查 `phase5_verification.py` 等）
- 验证覆盖范围是否变化（新物理区域 / 新边界条件）
- 回归保护规则是否需要更新

输出：

# Validation 变化摘要

包括：

- 变更的验证函数/测试文件
- 影响的模型（model-A / MIT / model-B / parametric）
- 基准值变化（如有）
- 覆盖范围变化（如有）

暂时不要修改文件。

---

# Phase 2 — 定向更新 AI Context

基于变化摘要，更新以下文件：

## 必须更新的文件

| 文件 | 更新内容 | 条件 |
|------|---------|------|
| `validation_registry.md` | 验证函数表、测试文件表、覆盖矩阵 | 每次 |
| `project_state.md` §12.1 | 验证函数表（4+1） | 验证函数变化时 |
| `project_state.md` §12.2 | 测试文件表（model-A 4 + MIT 5） | 测试文件变化时 |
| `project_state.md` §12.3 | 测试路径策略 | 路径策略变化时 |
| `project_state.md` §12.4 | 回归保护规则 | 规则变化时 |

## 可选更新的文件

| 文件 | 更新内容 | 条件 |
|------|---------|------|
| `project_state.md` §16 | 重要测试列表 | 关键测试变化时 |
| `project_state.md` §17 | 已知技术债务（如重复验证函数 D1） | 如修复或新增债务 |
| `module_index.md` §1.6 | validation 模块索引 | 模块 API 变化时 |
| `refactor_history.md` | 新增 R-N 条目 | 大型验证重构时 |

## 更新要求

1. 验证函数签名必须与 `src/validation.py` 完全一致
2. 测试文件清单必须与磁盘上的实际文件一致
3. 基准值必须与测试文件中的断言值一致
4. 已知重复的验证函数必须保持标记，直到修复
5. 测试路径策略必须反映实际的 `conftest.py` `_find_project_root()` 哨兵自动发现机制——向上扫描含 `pyproject.toml` + `solver/` 的工程根并自动插入 `sys.path`

---

# Phase 3 — 交叉验证

更新完成后，执行最小化一致性检查：

- 检查 `validation_registry.md` 中每个测试文件在磁盘上存在
- 检查 `project_state.md` §12.2 的测试数与实际文件数一致
- 检查 `project_state.md` §17 中的验证相关技术债务条目是否仍准确
- 检查 `phase5_verification.py` 的硬编码路径是否仍被标记为已知问题（P2）

输出：

# Validation 更新验证报告

---

# Phase 4 — 执行 Consistency Audit

最后执行 `ai_context_consistency_audit.md` 作为 QA 闸门。

重点检查：

- 验证函数名在 `validation_registry.md` 和 `project_state.md` §12 之间是否一致
- 验证状态在 `module_index.md` 中是否一致
- 已知债务条目是否在各文件中统一标记

---

# 工作流原则

本工作流：

- 仅更新 AI 上下文中的验证注册信息
- 不修改验证函数或测试文件本身
- 不更新 model 物理描述或架构描述
- 维护验证体系与源码的精确对应

---

# 禁止事项

禁止：

- 整文件重写
- 忽略源码中实际的验证函数签名
- 在不同文件中使用不同的验证函数名
- 遗漏测试文件（必须与磁盘上的文件一一核对）
- 跳过 Phase 4 的 consistency_audit
