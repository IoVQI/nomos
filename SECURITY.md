# Security Policy / 安全策略

## Supported versions / 支持版本

| Version | Supported |
|---------|:---------:|
| 1.x     | ✅        |
| < 1.0   | ❌        |

## Reporting a vulnerability / 报告漏洞

请**不要**在公开 Issue 中披露敏感信息。请通过 GitHub Security Advisories 私下报告：

- <https://github.com/IoVQI/nomos/security/advisories/new>

Please **do not** open a public issue for sensitive reports. Use GitHub Security Advisories:

- <https://github.com/IoVQI/nomos/security/advisories/new>

我们会在 7 天内确认收到，并在修复后公开致谢（如你同意）。
We aim to acknowledge within 7 days and will credit you after the fix (with your consent).

## Scope / 范围

本仓库是文档与治理骨架，不含运行时服务。重点关注：

- 发布件中意外包含的凭据、令牌、私钥、真实地址或个人信息；
- 校验脚本或 CI 配置中的命令注入、路径穿越；
- 权限配置（`.claude/settings.json`）中过宽的 allow 规则。

This repository is a documentation and governance skeleton with no runtime service. Reports of
interest include leaked credentials or personal data in release artifacts, command injection or
path traversal in validation scripts, and over-broad permission rules.

## Release hygiene / 发布卫生

每次发布都经过：白名单构建 → 敏感信息扫描 → 个人路径扫描 → 闸门 → 人工复核 → 发布后核验。
若你发现已发布内容包含不应公开的信息，请立即通过上述渠道报告。
