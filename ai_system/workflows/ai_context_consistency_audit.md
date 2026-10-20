---
project_version: "0.9.0"
language: "zh"
last_updated: "2026-08-31"
compatible_project_version: ">= 0.1.0"
category: "ai_workflow"
tags: [ai-context, audit, fix-propagation, link-integrity]
purpose: "交叉审计全部 ai_context 文件的冲突与漂移，并统一化修复，确保长期自洽。按需运行（原 14/21 天定时间隔提醒已退役，改用户/链触发时运行）。"
changelog: "wf-1.3: 改为按需运行——移除 14/21 天定时间隔提醒（间隔本身不能防 drift，2026-08-31 P2 计数设施瘦身）；wf-1.2: 交叉审计全部 ai_context 文件，检测冲突漂移并统一化修复（2026-06-12）；wf-1.1: 新增 Phase 2.5 + Phase 3.5（2026-05-25）；wf-1.0: 初始版本（2026-05-23）"
---

# AI Context Consistency Audit Workflow

## 工作流目标

本工作流用于：

对：

context/

中的所有 AI 上下文文件，

进行：

全局一致性审计（Global Consistency Audit）。

目标：

确保：

* AI上下文层内部自洽
* 与当前源码一致
* 与当前架构一致
* 与当前EOS流程一致
* 与当前validation体系一致
* 与当前notebook体系一致

特别适用于：

* 长上下文生成后
* 使用 /compact 后
* 多阶段文档生成后
* 大型重构后
* 跨会话恢复后
* 模型架构变化后

注意：求解器与外部副本的边界应写进架构快照；本工作流只审计上下文文件与源码的一致性，不假设某个具体目录存在。

---

# Phase 1：恢复工程上下文

现在，请不要更新任何 ai_context 文件。

请先对整个：

context/

进行一次：

“全局一致性审计（Global Consistency Audit）”。

项目路径：
./ai_system

请重点检查：

* project_state.md
* refactor_history.md
* documentation_rules.md
* architecture_snapshot.md
* eos_pipeline.md
* notebook_registry.md
* validation_registry.md
* module_index.md
* cross_reference_map.md
* pytov_migration_analysis.md

同时结合：

* 当前源码
* 当前README
* 当前architecture
* 当前physics_notes
* 当前validation_checklist
* 当前notebook

重点检查：

1. 文件之间是否存在冲突
2. 文件之间是否存在命名不一致
3. EOS流程是否一致
4. notebook描述是否一致
5. validation描述是否一致
6. 模块状态是否一致
7. 已废弃模块是否一致
8. 架构描述是否一致
9. .dat 输出接口合约是否一致（求解器已内化至 `solver/`，其接口合约在本审计范围内）
10. 术语是否统一
11. **链接完整性**：对每个 `[display_text](target)` Markdown 链接，验证 target 指向的文件存在于磁盘或锚点有效。断裂链接（显示文本已更新但 target 指向旧路径）列为 **严重冲突**

请特别注意：

这些文件是在：

* 长上下文
* 多阶段生成
* 使用 /compact
* 多轮恢复上下文

的情况下生成的。

因此请重点检查：

* 上下文漂移
* 术语漂移
* 架构漂移
* EOS漂移
* notebook漂移
* validation漂移
* 接口合约漂移（.dat 输出格式）
* 链接目标漂移（显示文本已更新但链接目标仍指向旧路径——常见于目录 rename 后）

暂时不要修改文件。

---

# Phase 2：输出一致性审计报告

现在，请输出：

# ai_context一致性审计报告

请分类列出：

## 严重冲突

例如：

* EOS流程冲突
* 当前主模型冲突
* notebook用途冲突
* validation入口冲突
* **断裂的 Markdown 链接**（显示文本与链接目标不一致，或目标文件不存在）

## 中等冲突

例如：

* 命名不一致
* 模块状态不一致
* validation状态不一致
* 已废弃模块状态不一致

## 轻微冲突

例如：

* 术语不统一
* 表述风格漂移
* 重复描述

对于每个问题：

请说明：

1. 冲突来源
2. 涉及文件
3. 当前源码真实情况
4. 建议保留的版本
5. 建议修改方案

最后：

请评估：

整个 ai_context 当前的：

* 自洽程度
* 可信程度
* 可恢复程度
* 长期维护风险

暂时不要修改文件。

---

# Phase 2.5：修复传播影响分析

在输出审计报告后、执行修复前，对每个需要修复的漂移项：

1. 确定"源事实"——源码中的实际状态
2. 生成受影响文件的完整列表，方法：
   - 提取漂移项的关键词（如 `hbarc`、`equilibrium.py:39`、`sound_speed_squared 重复`）
   - 在 `context/` 全目录执行 grep
   - 列出所有包含该关键词的文件及行号
3. 对每个命中项判断：是"需要修复的声明"还是"已正确的声明"
4. 将完整的传播列表写入审计报告，作为 Phase 3 的修复范围清单

此步骤确保每个修复项都有明确的修复范围——在 Phase 3 执行修复时不会遗漏任何文件中的并行声明。

---

# Phase 3：执行统一化修复

现在，请基于：

刚刚生成的：

“ai_context一致性审计报告”

对整个：

context/

进行一次：

“全局统一化修复”。

要求：

1. 不要重写整个文件
2. 仅修复冲突部分
3. 保持长期稳定性
4. 保持与源码一致
5. 保持与当前架构一致
6. 统一EOS术语
7. 统一notebook描述
8. 统一validation描述
9. 统一模块状态
10. 统一命名规范

请特别修复：

* /compact 导致的上下文漂移
* 长对话导致的术语漂移
* 多阶段生成导致的架构漂移

对于每个修复：

请输出：

# 修复原因

# 修复前冲突

# 修复后内容

# 与源码对应关系

最后：

请输出：

# 最终 ai_context 一致性状态

# 当前剩余风险

# 当前仍需人工确认部分

---

# Phase 3.5：跨文件传播验证

在所有修复执行完毕后，执行以下验证步骤：

1. 对每个已修复的漂移项，用修复后的"正确表述"作为 grep 关键词
   - 例：修复某常量局部定义 → grep 该常量的统一导入处
   - 确认所有应包含该正确表述的文件均已反映修复
2. 用漂移项的"旧表述"再次 grep
   - 例：grep `局部 hbarc\|equilibrium.py:39\|hbarc.*局部定义`
   - 确认剩余的命中项均为 strikethrough（`~~...~~`）或 checkbox `[x]`（已勾选完成）
3. 如发现未修复的活跃声明 → 回到 Phase 3 补充修复
4. 重复直到 Phase 3.5 通过（零活跃旧表述命中），**但有界循环，至多 3 轮**：
   - **迭代上限**：Phase 3 ↔ Phase 3.5 往返 ≥3 轮仍未清零 → 强制退出本轮循环，剩余未修复项转入审计报告「当前仍需人工确认部分」
   - **良性残留豁免**：若本轮未产生任何新修复（已达稳定态，grep 命中集与上一轮相同）→ 即使仍有残留也立即退出，残留项同样转入「当前仍需人工确认部分」

将最终验证结果（grep 旧表述的剩余命中列表及状态判断）记录到审计报告末尾。

---

# 使用原则

本工作流：

不是：

“普通文档更新流程”。

而是：

“AI工程认知一致性修复流程”。

重点目标：

不是：

增加内容，

而是：

确保：

整个 AI Context 系统：

长期稳定、自洽、可恢复、可维护。

---

# 禁止事项

禁止：

* 直接整文件重写
* 忽略源码真实状态
* 忽略 model 当前实现
* 忽略 notebook 当前状态
* 忽略 validation 当前状态
* 忽略 refactor_history
* 在不同文件中使用不同命名
* 在不同文件中保留冲突架构

---

# 长期维护建议

建议：

每次大型更新后：

执行一次：

AI Context Consistency Audit。

尤其在以下情况之后：

* EOS架构重构
* notebook迁移
* validation体系变化
* 模块命名变化
* 使用 /compact
* 长上下文恢复
* 多阶段生成
