---
name: workflow-authoring
description: 基于用途构想创建新工作流——生成工作流规范、委托 workflow_creation_workflow 创建注册、委托 proposal-gen 生成创建方案。Use when the user asks to 创建工作流/设计工作流/基于用途构想生成工作流规范, or says "create a workflow for X" / "design a workflow" / "author a workflow".
allowed-tools: Read Glob Grep Bash(git status *) Bash(python ai_system/validation/check_workflows.py *)
---

基于 `${CLAUDE_PROJECT_DIR}` 的用途构想，按 `ai_system/workflows/workflow_authoring_workflow.md` 执行完整撰写流程：

## 流程

1. **Phase 0 输入解析** — 从用途构想提取 `{名称, 所属层, 一句话职责, Skill/动态工作流选型, 关联链模板}`
2. **Phase 1 规范生成** — 生成工作流规范正文，参考官方文档镜像（`ai_system/official_docs/claude_code/skills.md` + `workflows.md`）+ `chain_template_catalog.md` §3 P1-P9 + 既有同类工作流
3. **Phase 2 委托创建** — 委托 `workflow_creation_workflow.md` 落盘 + 注册
4. **Phase 3 委托方案生成** — 委托 `proposal-gen` Skill 生成创建方案
5. **Phase 4 终验** — `python ai_system/validation/check_workflows.py --quiet` exit 0

## 关键约束

- **架构选型显式判定**：仅 MD / MD+Skill / MD+JS（参考三层体系）
- **编排而非重复**：不内联「创建/注册」和「方案生成」，一律委托既有设施
- **严格模式**：每 Phase 满足退出条件才进入下一 Phase；连续 3 次失败 → 阻断并写入 `proposals/` 请求用户介入
