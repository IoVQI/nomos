# ai_system/context/ — 跨会话上下文恢复（模板）

> 本目录只随发布件分发**空白模板**，用于让新会话在不依赖聊天历史的情况下恢复项目状态。

## 模板

| 文件 | 用途 |
|------|------|
| [`_templates/project_state_template.md`](_templates/project_state_template.md) | 项目状态快照 |
| [`_templates/architecture_snapshot_template.md`](_templates/architecture_snapshot_template.md) | 架构快照 |

## 用法

1. 复制模板到本目录，按模板填写；
2. 在 `ai_system/index.md` 中登记；
3. 每次架构或状态变化时更新 `last_updated`，不要维护重复的版本副本。

## 原则

- **状态快照，不是会话原文**：不要保存聊天记录或过程日志；
- **真源唯一**：同一事实只写一处，其余位置放指针；
- **不写死规模**：需要计数时现场取实盘；
- **不含敏感值**：地址、凭据、个人信息一律用占位符，真值放在仓库外。
