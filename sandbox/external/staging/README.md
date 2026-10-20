# sandbox/external/staging/ — 克隆区

> 第三方组件的**原始副本**存放处。本目录**除本 README 外整体不入库**。

## 为什么它不在版本库里

- 克隆件自带嵌套 `.git`，直接入库会让版本控制语义混乱
- 体积通常远大于项目本体
- 版权属第三方

根 `.gitignore` 用 `sandbox/external/staging/*` + `!.../README.md` 的写法：
前者保留目录本身，后者让这份说明仍受版本控制。

## 用法

```bash
git clone <url> sandbox/external/staging/<repo>
```

随后立刻按 [`../README.md`](../README.md) 的「三步生命周期」登记元信息。
🔴 本地化完成后，本目录下的原件**必须删除** —— 它的溯源已落在 `../_registry/<repo>.md`。
