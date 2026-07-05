"""Canonical work-status vocabulary + host-language aliases (issue #121, item 4).

WORK-SCHEMA v1 keeps ``status`` as an English enum and the i18n convention is
EN-schema / KO-UI (RFC-2026-06-23). Hosts writing localized statuses forced
every consumer to grow its own ad-hoc vocabulary: ``DONE_STATUSES`` with a
hard-coded "완료" was copy-pasted across four scripts, and taskset_dispatcher
carried a fifth, *diverged* copy — exactly the "이중 검증 체계" friction the
host reported. This module is the single alias source, per the council verdict
(COUNCIL-2026-06-14, 531: "status l10n P3, alias-additive"):

- ``normalize_status()`` folds any registered alias to its canonical value and
  is otherwise a plain strip/lower — unknown vocab passes through unchanged,
  so adopting it is behavior-preserving for EN statuses.
- The exported ``DONE_STATUSES`` is alias-inclusive, so existing
  ``status.lower() in DONE_STATUSES`` membership sites gain alias coverage
  without changing shape.

Additive only: the schema enum stays English; aliases are accepted on read.
"""

from __future__ import annotations

# Mirror of agents/project/WORK-SCHEMA.yml `status.allowed_values` (pinned by
# tests/test_status_alias.py so the two cannot drift apart).
CANONICAL_STATUSES = (
    "proposed",
    "planned",
    "worker_ready",
    "active",
    "in_progress",
    "blocked",
    "completed",
    "closed",
    "done",
)

# Host-language (KO) aliases -> canonical status. "released" is not in the
# schema enum but is an established runtime value in done-family checks.
STATUS_ALIASES = {
    "제안": "proposed",
    "계획": "planned",
    "계획됨": "planned",
    "준비": "worker_ready",
    "준비됨": "worker_ready",
    "활성": "active",
    "진행": "in_progress",
    "진행중": "in_progress",
    "진행 중": "in_progress",
    "차단": "blocked",
    "차단됨": "blocked",
    "완료": "completed",
    "완료됨": "completed",
    "완결": "done",
    "종결": "closed",
    "종료": "closed",
    "릴리스됨": "released",
    "배포됨": "released",
    "보류": "hold",
    "보류됨": "hold",
}

DONE_CANONICAL = frozenset({"completed", "done", "released"})
# "hold" is not in the schema enum either, but is the established runtime value
# in blocked-family checks (automation_rules_gate carried {"blocked","hold","보류"}).
BLOCKED_CANONICAL = frozenset({"blocked", "hold"})


def normalize_status(value: object) -> str:
    """Alias-aware strip/lower. Unknown vocabulary passes through lowered."""
    text = str(value or "").strip()
    return STATUS_ALIASES.get(text, text.lower())


def _alias_inclusive(canonical: frozenset[str]) -> frozenset[str]:
    return canonical | {
        alias for alias, target in STATUS_ALIASES.items() if target in canonical
    }


# Drop-ins for the legacy per-script sets: canonical family + every alias that
# folds into it (covers the historical {"completed","done","released","완료"}
# and {"blocked","hold","보류"}).
DONE_STATUSES = _alias_inclusive(DONE_CANONICAL)
BLOCKED_STATUSES = _alias_inclusive(BLOCKED_CANONICAL)


def is_done(value: object) -> bool:
    return normalize_status(value) in DONE_CANONICAL
