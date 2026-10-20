---
project_version: "0.9.0"
language: "zh"
last_updated: "2026-08-17"
compatible_project_version: ">= 0.5.0"
category: "ai_workflow"
tags: [sandbox, external, third-party, repository, ingestion, clone, reference]
purpose: "统一编排三方仓库入库全流程：必要性评估 + 元信息强制 + 索引同步"
changelog: "wf-1.0 (2026-08-13): 修复 W1/W2/W3（import os 缺失、audit 路径）+ 新增 purpose 字段（wf-5.16）；wf-1.0: 初始版本——三方仓库入库：联网/本地双模式 + 必要性评估 + 元信息强制 + 索引同步（2026-07-08）"
related:
  - notebook_update_workflow.md (⚠️ 已废弃 2026-07-15)
  - full_ai_context_update.md
execution_mode: strict  # strict | normal
# strict 模式下：每个 Phase 必须在上一 Phase 所有退出条件满足后才能进入
# 闸门判定必须基于实际命令输出（禁止"推断"通过）
# 连续 3 次同一 Phase 失败 → 🔴 阻断，写入 proposals/ 请求用户介入
completion_marker: "🔴 CHAIN_COMPLETE"
max_retry_per_phase: 3
---

# 三方仓库入库工作流

> 🔴 **本工作流为原项目导入件，路径尚未适配本骨架（标记于 2026-10-05）**：正文中的
> `sandbox/external/cloned/`、`_references/references.md`、`SANDBOX_CONTEXT.md`、`lab/`、
> `records/` 等路径在本仓库均**不存在**。本骨架沙箱的实际目录约定见
> [`sandbox/external/README.md`](../../sandbox/external/README.md)；在完成路径适配前，
> 本文件**不构成**该目录的操作规程。全量适配另立方案（见 `proposals/2026/10/05/`）。

## 工作流目标

统一编排三方仓库入库全流程：从「拿到仓库 URL」到「完成 clone + 元信息填写 + 索引同步」。

**核心原则**：
- **必要性前置**：clone 前必须评估是否已有等价内部实现或重复仓库
- **元信息强制**：每个 clone 仓库必须有 `_source.md`，记录来源、用途、与 lab 关系
- **索引同步**：`_references/references.md` 和 `SANDBOX_CONTEXT.md` 必须同步更新
- **隔离优先**：三方仓库仅作参考，不直接集成到 lab 主代码路径

---

## 适用场景

- 从 GitHub / GitLab 等平台 clone 三方仓库到 `sandbox/external/cloned/`
- 将已存在的本地三方目录纳入管理（补建元信息）
- 将 `_references/references.md` 中的 URL-only 记录升级为已 clone 状态

## 不适用场景

- 文献（论文）入库 → `literature_ingestion_workflow`
- 会议报告入库 → `meeting_note_ingestion_workflow`
- lab 内部模块开发 → `eos_update_workflow` / `architecture_update_workflow`
- Notebook 管理 → ~~`notebook_update_workflow`~~（已废弃，2026-07-15）

---

## 前置条件

| 依赖 | 用途 | 条件 |
|------|------|------|
| Git | clone 仓库 | `git --version` 可用 |
| 网络（联网模式） | 访问远程仓库 | GitHub/GitLab 可达 |
| `sandbox/external/` 目录结构 | 存放 clone 仓库 | 目录已存在 |

---

## 工作流步骤

### Phase 0: 输入解析与模式判定

#### 0.1 解析用户输入

```python
import os, re

def parse_input(user_input):
    """解析用户输入，判定模式和仓库标识。"""
    user_input = user_input.strip()

    # GitHub URL 模式
    m = re.match(r'https?://github\.com/([^/]+/[^/\s]+?)(?:\.git)?(?:\s|$)', user_input)
    if m:
        return {'mode': 'online', 'source': 'github', 'id': m.group(1)}

    # GitLab URL 模式
    m = re.match(r'https?://gitlab\.com/([^/]+/[^/\s]+?)(?:\.git)?(?:\s|$)', user_input)
    if m:
        return {'mode': 'online', 'source': 'gitlab', 'id': m.group(1)}

    # 通用 .git URL
    m = re.match(r'(https?://\S+\.git)(?:\s|$)', user_input)
    if m:
        return {'mode': 'online', 'source': 'generic', 'id': m.group(1)}

    # 本地路径模式（已在 cloned/ 下）
    if os.path.isdir(user_input):
        return {'mode': 'local', 'source': 'local_path', 'id': user_input}

    # 仓库名模式（假设 GitHub）
    m = re.match(r'([a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+)$', user_input)
    if m:
        return {'mode': 'online', 'source': 'github_guess', 'id': m.group(1)}

    return {'mode': 'unknown', 'source': None, 'id': user_input}
```

#### 0.2 提取仓库名

```python
def extract_repo_name(parsed):
    """从解析结果提取仓库名（用于目录命名）。"""
    if parsed['mode'] == 'online':
        # owner/repo → repo
        return parsed['id'].split('/')[-1].replace('.git', '')
    elif parsed['mode'] == 'local':
        return os.path.basename(os.path.normpath(parsed['id']))
    return parsed['id']
```

### 0.3 退出条件（🔴 必须全部满足方可进入 Phase 1）

- [ ] 输入已解析，mode / source / id 已确定
- [ ] 仓库名已提取（extract_repo_name）
- [ ] 若 URL 无法解析 → 已请求用户手动提供仓库名和 URL

### 0.4 失败处理（🔴 不得跳过）

- URL 格式无法解析 → 🔴 阻断，提示用户手动提供仓库名和 URL
- 模式判定为 unknown → 🔴 阻断，请求用户明确（联网/本地）
- 正则解析崩溃 → 重试 1 次（消耗 max_retry_per_phase）；仍失败 → 🔴 阻断

---

### Phase 1: 必要性评估

#### 1.1 检查重复

```
sandbox/external/cloned/{repo_name}/ 已存在?
  ├─ 是 → 标记 already_exists, 询问用户是更新元信息还是跳过
  └─ 否 → 继续 1.2
```

#### 1.2 检查等价内部实现

```
lab/ 下是否存在功能等价的内部实现?
  ├─ 是 → 警告用户, 记录等价模块路径, 用户确认是否继续 clone
  └─ 否 → 继续 1.3
```

#### 1.3 检查 URL-only 记录升级

```
_references/references.md 中是否有该仓库的 URL-only 记录?
  ├─ 是 → 标记 upgrade_from_url_only, clone 后将行状态更新为 "已 clone"
  └─ 否 → 继续 Phase 2
```

#### 1.4 评估结论

| 结论 | 后续动作 |
|------|---------|
| `proceed` | 进入 Phase 2 |
| `already_exists` | 跳至 Phase 3（补建/更新 `_source.md`） |
| `duplicate` | 终止，通知用户 |
| `upgrade_from_url_only` | 进入 Phase 2，clone 后升级记录 |

### 1.5 退出条件（🔴 必须全部满足方可进入 Phase 2）

- [ ] 1.1 重复检查已完成（`cloned/{repo_name}/` 已存在 → 标记 already_exists）
- [ ] 1.2 等价内部实现检查已完成（lab/ 下功能等价模块 → 已警告用户）
- [ ] 1.3 URL-only 记录升级检查已完成（references.md 有记录 → 标记 upgrade_from_url_only）
- [ ] 评估结论已确定（proceed / already_exists / duplicate / upgrade_from_url_only）

### 1.6 失败处理（🔴 不得跳过）

- 等价内部实现已存在 → ⚠️ 警告但不阻断，用户确认后继续
- 判定为 duplicate → 终止并通知用户（非阻断——用户决策）
- 目录检查崩溃 → 重试 1 次（消耗 max_retry_per_phase）；仍失败 → 🔴 阻断
- 不得以「印象中没 clone 过」为由跳过 `cloned/` 实际检查

---

### Phase 2: Clone 与隔离

#### 2.1 Clone（联网模式）

```bash
cd sandbox/external/cloned/
git clone {repo_url} {repo_name}
cd {repo_name}
git log -1 --format="%H %ai"  # 记录 HEAD commit
```

#### 2.2 确认本地目录（本地模式）

```bash
cd sandbox/external/cloned/{repo_name}/
git log -1 --format="%H %ai"  # 记录 HEAD commit
git remote -v                   # 记录远程 URL
```

#### 2.3 配置隔离

检查并配置 Nomos 根 `.gitignore`（用于隔离 clone 仓库）：

```
# 常见需忽略的条目（根据仓库语言调整）
__pycache__/
*.pyc
.venv/
venv/
node_modules/
build/
dist/
*.o
*.so
*.dylib
.DS_Store
```

> **注意**：不修改三方仓库自身的 `.gitignore`（保持上游原样）。
> 如需忽略 clone 仓库本身，应在 Nomos 根 `.gitignore` 中配置 `sandbox/external/cloned/{repo_name}/`。

#### 2.4 记录关键信息

| 字段 | 来源 |
|------|------|
| clone 日期 | 当前日期 |
| commit hash | `git log -1 --format="%H"` |
| commit 日期 | `git log -1 --format="%ai"` |
| 默认分支 | `git rev-parse --abbrev-ref HEAD` |
| 远程 URL | `git remote get-url origin` |
| 仓库描述 | GitHub API 或 README 首段 |
| 主要语言 | 文件扩展名统计或 GitHub API |
| star 数 | GitHub API（可选） |

### 2.5 退出条件（🔴 必须全部满足方可进入 Phase 3）

- [ ] 仓库已 clone（联网模式 `git clone` 成功）或本地目录已确认（本地模式）
- [ ] HEAD commit 已记录（`git log -1 --format="%H %ai"`）
- [ ] 远程 URL 已记录（本地模式 `git remote -v`）
- [ ] `.gitignore` 隔离已配置（不修改三方仓库自身 `.gitignore`）
- [ ] 关键信息字段已收集（clone 日期 / commit hash+日期 / 默认分支 / 远程 URL / 描述 / 主要语言 / star 数）

### 2.6 失败处理（🔴 不得跳过）

- git clone 失败（网络）→ 重试 3 次，间隔 5s；仍失败 → 🔴 阻断，通知用户检查网络/权限
- git clone 失败（仓库不存在）→ 🔴 阻断，确认 URL 正确性
- 仓库过大（>1GB）→ ⚠️ 警告用户，建议 `--depth 1` 浅 clone（非阻断）

---

### Phase 3: 元信息填写

#### 3a. 创建 `_source.md`

在 `sandbox/external/cloned/{repo_name}/_source.md`：

```markdown
# {repo_name}

- **来源**: {remote_url}
- **clone 日期**: {YYYY-MM-DD}
- **commit**: {full_hash}
- **commit 日期**: {YYYY-MM-DD HH:MM}
- **默认分支**: {branch_name}
- **用途**: {用户填写 — 简述为何需要此仓库}
- **与 lab 的关系**: 独立使用 / 对比验证 / 代码借鉴 / 参考实现
- **状态**: active / archived / abandoned
- **依赖隔离**: 使用独立虚拟环境 / 共享 lab 环境 / 无依赖（纯参考）
- **仓库描述**: {一句话描述，来自 README 或 GitHub}
- **主要语言**: {language}
```

#### 3b. 必填字段验证

```python
def validate_source_md(source_md_path):
    """验证 _source.md 必填字段。"""
    required_fields = [
        '来源', 'clone 日期', 'commit', '用途',
        '与 lab 的关系', '状态', '依赖隔离'
    ]
    with open(source_md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    missing = [f for f in required_fields if f'**{f}**:' not in content]
    return len(missing) == 0, missing
```

### 3c 退出条件（🔴 必须全部满足方可进入 Phase 4）

- [ ] `_source.md` 已创建于 `sandbox/external/cloned/{repo_name}/_source.md`
- [ ] 必填字段全部非空（validate_source_md 返回 missing = []）
- [ ] 必填字段：来源 / clone 日期 / commit / 用途 / 与 lab 的关系 / 状态 / 依赖隔离

### 3d 失败处理（🔴 不得跳过）

- `_source.md` 必填字段缺失 → 🔴 阻断，提示用户补充
- 验证脚本崩溃 → 重试 1 次（消耗 max_retry_per_phase）；仍失败 → 🔴 阻断
- 不得以「字段看起来齐全」为由跳过 validate_source_md 实际校验

---

### Phase 4: 索引同步

#### 4a. 更新 `_references/references.md`

在 `sandbox/external/_references/references.md` 的「已 clone 项目」表格中新增行：

```markdown
| `{repo_name}` | <{remote_url}> | {用途简述} | ★★☆☆☆ | {YYYY-MM-DD} |
```

> 相关程度星级由用户判定（1-5 星）。

若为 URL-only 记录升级，将对应行从「仅 URL 引用」表格移至「已 clone 项目」表格。

#### 4b. 更新 `SANDBOX_CONTEXT.md`

更新 `sandbox/SANDBOX_CONTEXT.md` §外部项目，新增条目：

```markdown
- `external/cloned/{repo_name}/` — {一句话描述}（clone 于 {YYYY-MM-DD}）
```

#### 4c. 更新 `project_state.md`（如涉及）

如果三方仓库与 lab 有直接关联（如对比验证、参考实现），
在 `ai_system/context/project_state.md` 的相关节中记录引用关系。

### 4d 退出条件（🔴 必须全部满足方可进入 Phase 5）

- [ ] 4a: `_references/references.md`「已 clone 项目」表格已新增行（或 URL-only 行已升级迁移）
- [ ] 4b: `SANDBOX_CONTEXT.md` §外部项目已新增条目
- [ ] 4c: `project_state.md` 已更新（仅当与 lab 直接关联）

### 4e 失败处理（🔴 不得跳过）

- 索引文件写入冲突 → 重试 1 次（消耗 max_retry_per_phase）；仍失败 → 🔴 阻断
- 相关程度星级缺失 → 询问用户判定（非阻断）
- 不得以「索引看起来已更新」为由跳过 `SANDBOX_CONTEXT.md` 实际更新

---

### Phase 5: 终验与收尾

#### 5.1 终验清单

| 检查项 | 判定 |
|--------|------|
| `_source.md` 存在 | ✅ |
| `_source.md` 必填字段非空 | ✅ |
| `_references/references.md` 表格行已添加 | ✅ |
| `SANDBOX_CONTEXT.md` §外部项目已更新 | ✅ |
| clone 目录存在且非空 | ✅ |

#### 5.2 收尾选项

```
入库完成:
  ├─ 单个仓库 → 记录到会话日志, 结束
  ├─ 批量入库 → 生成入库汇总报告
  └─ 用户要求收尾 → /闭环本会话
```

#### 5.3 批量入库汇总报告

```markdown
## 三方仓库入库汇总报告

**日期**: YYYY-MM-DD
**总计**: N 个仓库

| # | 仓库名 | 来源 | 模式 | _source.md | 索引同步 | 状态 |
|:-:|--------|------|:---:|:---:|:---:|------|
| 1 | RepoA | github.com/... | online | ✅ | ✅ | 完成 |
| 2 | RepoB | local | local | ✅ | ✅ | 完成 |

**统计**:
- 成功: X 个
- 跳过（已存在）: Y 个
- 失败: Z 个
```

### 5.4 退出条件（🔴 工作流终点）

- [ ] `_source.md` 存在且必填字段非空
- [ ] `_references/references.md` 表格行已添加
- [ ] `SANDBOX_CONTEXT.md` §外部项目已更新
- [ ] clone 目录存在且非空
- [ ] 批量入库 → 入库汇总报告已生成

### 5.5 失败处理（🔴 不得跳过）

- 终验发现缺失项 → 回到对应 Phase 补充
- 汇总报告写入失败 → 重试 1 次（消耗 max_retry_per_phase）；仍失败 → 🔴 阻断

🔴 CHAIN_COMPLETE

---

## 故障处理

| 故障 | 阶段 | 处理 |
|------|:---:|------|
| git clone 失败（网络） | Phase 2 | 重试 3 次, 间隔 5s; 失败 → 通知用户检查网络/权限 |
| git clone 失败（仓库不存在） | Phase 2 | 确认 URL 正确性; 通知用户 |
| 仓库过大（>1GB） | Phase 2 | 警告用户, 建议 `--depth 1` 浅 clone |
| `_source.md` 必填字段缺失 | Phase 3 | 阻断, 提示用户补充 |
| 等价内部实现已存在 | Phase 1 | 警告但不阻断, 用户确认后继续 |
| URL 格式无法解析 | Phase 0 | 提示用户手动提供仓库名和 URL |

---

## 与下游工作流的衔接

```
third_party_repo_ingestion_workflow (本工作流)
    │
    ├─ 产出 → sandbox/external/cloned/{repo_name}/_source.md
    ├─ 产出 → sandbox/external/_references/references.md 更新
    ├─ 产出 → sandbox/SANDBOX_CONTEXT.md 更新
    │
    ├─ 可选 → /闭环本会话 (会话收尾)
    └─ 上游: 用户提供仓库 URL 或本地路径
```

---

## 维护说明

### 新增支持的 Git 托管平台

在 Phase 0 的 `parse_input()` 中新增 URL 正则匹配分支。

### 模板字段扩展

在 Phase 3a 的 `_source.md` 模板中新增字段，同步更新 Phase 3b 的 `validate_source_md()`。

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| wf-1.0 | 2026-07-08 | 初始版本：联网/本地双模式 + 必要性评估 + 元信息强制 + 索引同步 |

---

*关联工作流：`notebook_update_workflow.md`（三方项目范围声明，⚠️ 已废弃 2026-07-15）、[full_ai_context_update.md](full_ai_context_update.md)（外部副本一致性检查）*
