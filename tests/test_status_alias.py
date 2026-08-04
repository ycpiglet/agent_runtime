"""Status vocabulary localization — issue #121 item 4, council verdict
COUNCIL-2026-06-14 (531): "status l10n P3, alias-additive".

The schema enum stays English (RFC-2026-06-23: EN schema, KO UI); hosts may
write localized statuses and every consumer folds them identically through
scripts/status_alias.py instead of five drifting per-script sets.
"""

from __future__ import annotations

import re
from pathlib import Path

from scripts import status_alias

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_SCRIPTS = REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts"


def test_korean_aliases_fold_to_canonical():
    assert status_alias.normalize_status("완료") == "completed"
    assert status_alias.normalize_status(" 진행중 ") == "in_progress"
    assert status_alias.normalize_status("진행 중") == "in_progress"
    assert status_alias.normalize_status("차단됨") == "blocked"
    assert status_alias.normalize_status("보류") == "hold"


def test_english_statuses_pass_through_unchanged():
    for value in ("Completed", "IN_PROGRESS", "blocked", "worker_ready"):
        assert status_alias.normalize_status(value) == value.strip().lower()
    # Unknown vocabulary is not rejected (additive, not strict).
    assert status_alias.normalize_status("weird_custom") == "weird_custom"
    assert status_alias.normalize_status(None) == ""


def test_every_alias_targets_known_vocabulary():
    known = set(status_alias.CANONICAL_STATUSES) | {"released", "hold"}
    for alias, target in status_alias.STATUS_ALIASES.items():
        assert target in known, (alias, target)


def test_canonical_statuses_match_work_schema_enum():
    schema = (REPO_ROOT / "agents" / "project" / "WORK-SCHEMA.yml").read_text(encoding="utf-8")
    match = re.search(
        r"^  status:\n(?:.*\n)*?\s+allowed_values:\s*\[(?P<values>[^\]]+)\]",
        schema,
        flags=re.MULTILINE,
    )
    assert match, "WORK-SCHEMA.yml status.allowed_values not found"
    schema_values = tuple(v.strip() for v in match.group("values").split(","))
    assert schema_values == status_alias.CANONICAL_STATUSES


def test_done_and_blocked_sets_are_alias_inclusive():
    # Superset of every historical per-script literal.
    assert {"completed", "done", "released", "완료"} <= status_alias.DONE_STATUSES
    assert {"blocked", "hold", "보류"} <= status_alias.BLOCKED_STATUSES
    assert status_alias.is_done("완료") is True
    assert status_alias.is_done("blocked") is False


def test_blocked_predicate_matches_exact_compound_tokens():
    for value in ("blocked", "hold", "held", "보류", "blocked/R3", "보류:R3"):
        assert status_alias.is_blocked(value) is True
    for value in ("", "unblocked", "unblocked/R3", "placeholder"):
        assert status_alias.is_blocked(value) is False


def test_consumers_use_the_single_alias_source():
    # The five scripts that carried their own (drifting) vocabulary literals
    # must consume status_alias instead — root and template variants alike.
    consumers = ["backlog_board.py", "automation_rules_gate.py", "state_sync_gate.py", "task_identity.py"]
    for name in consumers:
        for base in (REPO_ROOT / "scripts", TEMPLATE_SCRIPTS):
            text = (base / name).read_text(encoding="utf-8")
            assert "status_alias.DONE_STATUSES" in text, (base / name)
            assert 'DONE_STATUSES = {"completed"' not in text, (base / name)
    for base in (REPO_ROOT / "scripts", TEMPLATE_SCRIPTS):
        text = (base / "taskset_dispatcher.py").read_text(encoding="utf-8")
        assert "status_alias.normalize_status" in text, (base / "taskset_dispatcher.py")


def test_dispatcher_normalize_folds_korean_done():
    import sys

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    try:
        import taskset_dispatcher
    finally:
        sys.path.pop(0)
    assert taskset_dispatcher._normalize_status("완료") == "completed"
    assert taskset_dispatcher._normalize_status(" Done ") == "done"


def test_template_status_alias_matches_root():
    root = (REPO_ROOT / "scripts" / "status_alias.py").read_text(encoding="utf-8")
    template = (TEMPLATE_SCRIPTS / "status_alias.py").read_text(encoding="utf-8")
    assert root == template
