"""Project-wide canonical timestamp source.

Use this script for new human-facing timestamps instead of shell-specific date
commands. The output is stable across Windows, macOS, and Linux.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys


def _to_iso_with_colon_offset(value: dt.datetime) -> str:
    text = value.strftime("%Y-%m-%dT%H:%M:%S%z")
    if len(text) >= 5 and text[-5] in "+-":
        text = text[:-2] + ":" + text[-2:]
    return text


def local_iso() -> str:
    return _to_iso_with_colon_offset(dt.datetime.now(dt.timezone.utc).astimezone())


def utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def date_only() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().strftime("%Y-%m-%d")


def epoch_seconds() -> str:
    return str(int(dt.datetime.now(dt.timezone.utc).timestamp()))


def value(*, utc: bool = False, date: bool = False, epoch: bool = False) -> str:
    if utc:
        return utc_iso()
    if date:
        return date_only()
    if epoch:
        return epoch_seconds()
    return local_iso()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Project-wide canonical timestamp source")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--utc", action="store_true", help="UTC timestamp with Z suffix")
    group.add_argument("--date", action="store_true", help="local date only, YYYY-MM-DD")
    group.add_argument("--epoch", action="store_true", help="Unix epoch seconds")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(value(utc=args.utc, date=args.date, epoch=args.epoch))
    return 0


if __name__ == "__main__":
    sys.exit(main())
