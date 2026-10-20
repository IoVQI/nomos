# sandbox/external/ — 外部组件导入区

> 从其他项目扒来的组件在此落一次脚，登记清楚；本地化进 Nomos 后，原件即删。

## 目录约定

| 路径 | 入库 | 内容 |
|------|:---:|------|
| `staging/<repo>/` | ❌ | 克隆件的原始副本。**除其 `README.md` 外整体被根 `.gitignore` 排除** |
| `_registry/<repo>.md` | ✅ | 该组件的元信息：来源 / commit / 用途 / 状态 / **落地路径** |
| `_index.md` | ✅ | 全部组件的索引表 |
| `_registry/_TEMPLATE.md` | ✅ | `_registry/<repo>.md` 的模板 |

## 为什么元信息不在原件里

早期项目把 `_source.md` 放进被 `.gitignore` 忽略的克隆目录内 —— 两者矛盾：
原件不入库，元信息就跟着一起丢。本骨架把元信息移到被忽略树**之外**。

## 为什么必须填「落地路径」

因为原件在本地化完成后**即删**。少了这一栏，日后想知道某段代码从哪来、改了什么，将无据可查。
`_registry/` 里的记录因此是溯源链上唯一的一环。

## 三步生命周期

1. **扒** —— `git clone <url> sandbox/external/staging/<repo>`
2. **登记** —— 从 `_registry/_TEMPLATE.md` 复制出新元信息并填齐；在 `_index.md` 加一行
3. **本地化并清场** —— 把要用的部分提炼进 Nomos 的正式位置 → 该路径写回元信息的「落地路径」
   → 状态改 `localized` → `rm -rf staging/<repo>`

> 🔴 判据：`staging/` 下**只应有**尚未本地化的组件。看到已本地化却还留在那儿的，说明第 3 步没做完。

## 完整流程

每一步的判定条件与失败处理见
[`third_party_repo_ingestion_workflow.md`](../../ai_system/workflows/third_party_repo_ingestion_workflow.md)。
> ⚠️ 该工作流为原项目导入件，**路径尚未适配本骨架**（其正文已标）——
> 本页的目录约定以**本页**为准，流程步骤待该工作流适配后再行引用。
