# project/ops/ — 运维知识（模式示例）

> **这是发布件中的模式示例，不含任何真实 runbook、地址或凭据。**

## 为什么要用占位符

运维文档最容易泄密：真实 IP、主机名、账户、Token 往往直接写在命令示例里。
本目录的做法是：

1. **文档一律写成 `<PLACEHOLDER>`**；
2. **真值集中在仓库外**（或一个被 `.gitignore` 排除的 `_local/values.md`）；
3. 换机、换 IP、换凭据时**只改真值表**，文档不动。

| 占位符示例 | 指代 |
|---|---|
| `<RELAY_PUBLIC_IP>` | 中转服务器公网地址 |
| `<GAME_HOST_PUBLIC_IP>` | 游戏服务器公网地址 |
| `<WORKSTATION_TAILSCALE_IP>` | 工位机 Tailscale 地址 |
| `<FRP_TOKEN>` | frp 两端共享的认证串 |

## 目录建议

```text
project/ops/
├── README.md        ← 本文件
├── index.md         ← 占位符词表与入口（可选）
└── _local/          ← 真值表（必须被 .gitignore 排除）
    └── values.md
```

`.gitignore` 中的对应条目：

```gitignore
project/ops/_local/*
!project/ops/_local/README.md
```

## 纪律

- 真实值**只**写在 `_local/`，绝不复制到 issue、聊天记录或提交信息。
- 发布前扫描 `<RESIDUAL_*>` 一类兜底占位符；它们说明迁移尚未完成。
- 本目录的示例不构成任何运行建议；请按自己的环境重写。
