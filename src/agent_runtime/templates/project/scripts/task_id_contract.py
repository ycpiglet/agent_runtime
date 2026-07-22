"""Shared grammar for canonical task identifiers.

The runtime supports legacy numeric ``TASK-N`` IDs, numeric ``TASK-AR-N``
IDs, and collision-safe ``TASK-AR-YYYYMMDD-HHMMSS-XXXXXXXX`` IDs.  The
timestamp suffix is hexadecimal and case-insensitive; callers must preserve
the original identifier rather than normalizing or rekeying it.
"""

from __future__ import annotations

import re


TASK_ID_PATTERN = (
    r"(?:TASK-\d+|TASK-AR-(?:\d{8}-\d{6}-[0-9A-Fa-f]{8}|\d+))"
)
TASK_ID_VALUE_RE = re.compile(rf"^{TASK_ID_PATTERN}$")
TASK_ID_TOKEN_RE = re.compile(
    rf"(?<![A-Za-z0-9_-])({TASK_ID_PATTERN})(?![A-Za-z0-9_-])"
)
TIMESTAMP_SLUG_RE = re.compile(r"^\d{8}-\d{6}$")
HEX_SUFFIX_RE = re.compile(r"^[0-9A-Fa-f]{8}$")


def is_canonical_task_id(value: str) -> bool:
    """Return whether *value* is a complete supported task identifier."""
    return bool(TASK_ID_VALUE_RE.fullmatch(value.strip()))


def build_timestamp_task_id(timestamp_slug: str, hex_suffix: str) -> str:
    """Build a collision-safe task ID while preserving suffix case."""
    timestamp = timestamp_slug.strip()
    suffix = hex_suffix.strip()
    if not TIMESTAMP_SLUG_RE.fullmatch(timestamp):
        raise ValueError(f"invalid task timestamp slug: {timestamp_slug!r}")
    if not HEX_SUFFIX_RE.fullmatch(suffix):
        raise ValueError(f"invalid task hex suffix: {hex_suffix!r}")
    return f"TASK-AR-{timestamp}-{suffix}"
