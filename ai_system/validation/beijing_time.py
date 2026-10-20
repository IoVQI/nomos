#!/usr/bin/env python3
"""
Canonical Beijing time — 项目规范时钟源（北京时间 UTC+08:00，无夏令时）。

所有由 AI 手写的时间戳必须通过本脚本实时获取（CLAUDE.md §时间戳对齐规则），
禁止臆造/回填/凭记忆猜测。

本机 Git Bash 的 `TZ=Asia/Shanghai date` 静默返回 UTC（tzdata 不解析），
POSIX `TZ=UTC+8` 符号相反也错——只有 Python 固定偏移/zoneinfo 可靠
（2026-08-16 实测）。

Usage:
  python beijing_time.py [--fmt iso|filename|header|date|hhmm] [--check-consistency TS] [--tolerance N]

  --fmt iso        → 2026-08-16T16:23:51   (累积记录 timestamp / 链 ISO 字段；固定宽度无时区后缀，保字典序)
  --fmt filename   → 20260816_162351       (.session_milestone_<TS>.md / .chain_execution_<TS>.yml / chain_<TS>.yml)
  --fmt header     → 2026-08-16 16:23      (milestone 标题 / 报告标题)
  --fmt date       → 2026-08-16            (YYYY-MM-DD)
  --fmt hhmm       → 1623                  (文件名 HHMM 分量)
  无参数           → 同 --fmt iso

  --check-consistency <TS>   → 校验给定时间戳与当前北京时间偏差（分钟），> 容差退出 1。
                               用于 AI 落盘前自检是否使用了真实时钟（防臆造）。仅适用于
                               WRITE_TIME 时间戳；事件时间戳（如历史 started_at）不适用。
"""
import argparse
import sys
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))  # 北京时间，无夏令时

_PARSERS = ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y%m%d_%H%M%S')


def now():
    return datetime.now(CST)


def main():
    parser = argparse.ArgumentParser(description='Canonical Beijing time (UTC+08:00)')
    parser.add_argument('--fmt', choices=['iso', 'filename', 'header', 'date', 'hhmm'], default='iso')
    parser.add_argument('--check-consistency', metavar='TS', help='WRITE_TIME timestamp to sanity-check against now')
    parser.add_argument('--tolerance', type=int, default=60, help='tolerance minutes for --check-consistency (default 60)')
    args = parser.parse_args()

    if args.check_consistency:
        ts = args.check_consistency.strip()
        parsed = None
        for fmt in _PARSERS:
            try:
                parsed = datetime.strptime(ts, fmt)
                break
            except ValueError:
                continue
        if parsed is None:
            print(f'ERROR: cannot parse timestamp: {ts}')
            sys.exit(1)
        parsed = parsed.replace(tzinfo=CST)
        delta_min = abs((now() - parsed).total_seconds()) / 60.0
        if delta_min > args.tolerance:
            print(f'WARN: timestamp {ts} is {delta_min:.0f} min from now '
                  f'(tolerance {args.tolerance}) — likely fabricated/stale')
            sys.exit(1)
        print(f'OK: timestamp {ts} is {delta_min:.0f} min from now')
        sys.exit(0)

    n = now()
    if args.fmt == 'filename':
        print(n.strftime('%Y%m%d_%H%M%S'))
    elif args.fmt == 'header':
        print(n.strftime('%Y-%m-%d %H:%M'))
    elif args.fmt == 'date':
        print(n.strftime('%Y-%m-%d'))
    elif args.fmt == 'hhmm':
        print(n.strftime('%H%M'))
    else:  # iso
        print(n.strftime('%Y-%m-%dT%H:%M:%S'))  # 固定宽度无时区后缀


if __name__ == '__main__':
    main()
