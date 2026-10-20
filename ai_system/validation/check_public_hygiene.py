#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Public-release hygiene gate.

Fails if the checked tree contains development artifacts, personal data,
credentials, or internal paths that must never ship in a public release.

Run in the public release repository (CI) or against a release candidate:

    python ai_system/validation/check_public_hygiene.py
    python ai_system/validation/check_public_hygiene.py --root <release-candidate>

Exit code 0 = clean, 1 = findings. Stdlib only.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

SELF = Path(__file__).resolve()
SKIP_DIRS = {".git", "__pycache__", "node_modules"}
TEXT_EXT = {
    ".md", ".txt", ".py", ".js", ".json", ".yml", ".yaml", ".toml",
    ".sh", ".ps1", ".bat", ".cfg", ".ini", ".cff", ".xml", ".html",
}

FORBIDDEN_PATHS = [
    ("project/ops/aliyun/", "personal operations runbook"),
    ("project/ops/remote-desktop/", "personal operations runbook"),
    ("ai_system/official_docs/claude_code/", "third-party mirror"),
    ("ai_system/official_docs/deepseek", "third-party mirror"),
    ("ai_system/context/project_state.md", "source-project snapshot"),
    ("ai_system/context/eos_pipeline.md", "source-project snapshot"),
    ("proposals/2026/", "development proposal"),
    ("coordination/handoff/active/2026", "session handoff"),
    ("sandbox/experiments/migrate_ops.py", "migration script"),
    ("/values.md", "secret value table"),
    ("/_local/", "secret value table"),
    (".rdp", "remote desktop credential file"),
]

CONTENT_RULES = [
    ("residual", re.compile(r"<RESIDUAL_[A-Z0-9_]+>")),
    ("windows_user_path", re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s`\"'<>]+")),
    # Real absolute paths have a substantive first segment; `D:/…` and `D:/x/` are examples.
    ("dev_path", re.compile(r"\b(?:D:[\\/]+[^\s\\/`\"'<>…]{2,}|C:[\\/]+Code\b)", re.I)),
    ("cloud_id", re.compile(r"\bi-[a-z0-9]{16,}\b")),
    ("private_key", re.compile(r"-----BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY-----")),
    ("api_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b|\bghp_[A-Za-z0-9]{36}\b")),
]

ALLOWED_IPS = {"0.0.0.0", "127.0.0.1", "255.255.255.255", "255.255.255.0", "8.8.8.8", "1.1.1.1"}
EXAMPLE_NETS = ("192.0.2.", "198.51.100.", "203.0.113.")
IPV4 = re.compile(r"(?<![\d.])((?:\d{1,3}\.){3}\d{1,3})(?![\d.])")


def tracked_files(root: Path) -> list[Path]:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            capture_output=True, check=True, text=True, encoding="utf-8", errors="replace",
        ).stdout
        if out:
            return [root / p for p in out.split("\0") if p]
    except (OSError, subprocess.CalledProcessError):
        pass
    return [p for p in root.rglob("*") if p.is_file()]


def is_text(p: Path) -> bool:
    return p.suffix.lower() in TEXT_EXT or p.name in {".gitignore", ".gitattributes", ".gitkeep"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--max", type=int, default=200)
    args = ap.parse_args()

    root = args.root.resolve()
    findings: list[str] = []

    for p in tracked_files(root):
        if SELF == p.resolve() or any(part in SKIP_DIRS for part in p.parts):
            continue
        rel = p.relative_to(root).as_posix()
        for needle, why in FORBIDDEN_PATHS:
            if needle in rel and rel != "project/ops/README.md":
                findings.append(f"{rel}: forbidden path ({why})")
                break
        if not is_text(p):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for name, rx in CONTENT_RULES:
                if rx.search(line):
                    findings.append(f"{rel}:{lineno}: {name}")
            for m in IPV4.finditer(line):
                ip = m.group(1)
                if ip in ALLOWED_IPS or ip.startswith(EXAMPLE_NETS):
                    continue
                findings.append(f"{rel}:{lineno}: ip {ip}")

    if not findings:
        print(f"[hygiene] clean: {root}")
        return 0

    print(f"[hygiene] {len(findings)} finding(s):")
    for f in findings[: args.max]:
        print("  " + f)
    if len(findings) > args.max:
        print(f"  ... {len(findings) - args.max} more")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
