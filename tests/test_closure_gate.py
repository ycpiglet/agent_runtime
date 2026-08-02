"""Tests for closure_gate — require compound/review/retro for substantial work."""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import closure_gate  # noqa: E402
import compound_record  # noqa: E402
import stop_hook_closure_gate  # noqa: E402

NOW = datetime(2026, 6, 14, 12, 0, 0, tzinfo=timezone(timedelta(hours=9)))
TODAY = "2026-06-14"
_ACCEPTED_WATCH_MAX_BYTES = 256 * 1024
_CLAIM_ONLY_SIGNATURE = compound_record.normalize_signature(
    "claim only repeated failure authority"
)


def _write_direct_runtime(root: Path) -> None:
    (root / "agents" / "runtime").mkdir(parents=True, exist_ok=True)


# --- pure decision logic ---

def test_decide_not_substantial_approves():
    d = closure_gate.decide(10, {"compound": False, "review": False, "retro": False},
                            threshold=80, disabled=False, now_lines=10)
    assert d["decision"] == "approve"
    assert d["reason"] == "not-substantial"


def test_decide_substantial_without_record_blocks():
    d = closure_gate.decide(200, {"compound": False, "review": False, "retro": False},
                            threshold=80, disabled=False, now_lines=200)
    assert d["decision"] == "block"
    assert d["missing"] == ["compound", "review", "retro"]
    assert "200" in d["message"]


@pytest.mark.parametrize("present", ["compound", "review", "retro"])
def test_decide_substantial_with_any_record_approves(present):
    records = {"compound": False, "review": False, "retro": False}
    records[present] = True
    d = closure_gate.decide(200, records, threshold=80, disabled=False, now_lines=200)
    assert d["decision"] == "approve"
    assert d["reason"] == "closure-record-present"


def test_decide_disabled_always_approves():
    d = closure_gate.decide(9999, {"compound": False, "review": False, "retro": False},
                            threshold=80, disabled=True, now_lines=9999)
    assert d["decision"] == "approve"
    assert d["reason"] == "closure-gate-disabled"


def _scribe_evaluation(
    *,
    state="overdue",
    projection="missing",
    blocking=True,
    reasons=None,
    cleanup_status="none",
):
    closure_reasons = (
        list(reasons)
        if reasons is not None
        else (["source-debt-overdue", "projection-not-fresh"] if blocking else [])
    )
    return {
        "state": state,
        "readiness": "blocked" if blocking else "ready",
        "source_debt": {
            "status": state,
            "hot_count": 20 if state == "overdue" else 13,
            "overdue_sources": ["STATUS.md"] if state == "overdue" else [],
        },
        "projection": {
            "path": "agents/project/state/SCRIBE-PROJECTION.json",
            "status": projection,
        },
        "active_coverage": {
            "status": "complete",
            "missing_task_ids": [],
            "missing_claim_ids": [],
        },
        "cleanup_plan": {"status": "available", "candidate_count": 4},
        "cleanup_outcome": {"status": cleanup_status, "valid": cleanup_status != "invalid"},
        "overdue_sources": ["STATUS.md"] if state == "overdue" else [],
        "closure_blocking": blocking,
        "closure_reasons": closure_reasons,
    }


_DUPLICATE_WATCH_FIELDS = (
    "decision",
    "status",
    "reviewed_by",
    "work_id",
)

_DUPLICATE_WATCH_CASES = [
    pytest.param(
        watch_format,
        field,
        order,
        id=f"{watch_format}-{field}-{order}",
    )
    for watch_format in ("markdown", "json")
    for field in _DUPLICATE_WATCH_FIELDS
    for order in ("invalid-then-valid", "valid-then-invalid")
]


def _duplicate_accepted_watch_document(
    *,
    watch_format,
    field,
    order,
    current_work_id,
):
    valid = {
        "status": "accepted",
        "decision": "accepted_watch",
        "reviewed_by": "qa-independent",
        "work_id": current_work_id,
    }
    invalid = {
        "status": "rejected",
        "decision": "rejected",
        "reviewed_by": None,
        "work_id": "UNIT-TASK-AR-999-001",
    }
    duplicate_values = (
        (invalid[field], valid[field])
        if order == "invalid-then-valid"
        else (valid[field], invalid[field])
    )
    pairs = []
    for key in ("status", "decision", "reviewed_by", "work_id"):
        if key == field:
            pairs.extend((key, value) for value in duplicate_values)
        else:
            pairs.append((key, valid[key]))

    if watch_format == "json":
        rows = [
            f"  {json.dumps(key)}: {json.dumps(value)}"
            for key, value in pairs
        ]
        return "{\n" + ",\n".join(rows) + "\n}\n"

    def frontmatter_scalar(value):
        return "null" if value is None else str(value)

    rows = [
        f"{key}: {frontmatter_scalar(value)}\n"
        for key, value in pairs
    ]
    return "---\n" + "".join(rows) + "---\n\n# Duplicate watch authority\n"


_SEMANTIC_WATCH_REVIEWER_FIELDS = (
    "reviewed_by",
    "reviewer",
    "approved_by",
    "accepted_by",
    "verified_by",
)
_SEMANTIC_WATCH_WORK_FIELDS = (
    "work_id",
    "task_id",
    "unit_id",
    "work_ids",
)
_SEMANTIC_WATCH_FIELDS = (
    "decision",
    "status",
    *_SEMANTIC_WATCH_REVIEWER_FIELDS,
    *_SEMANTIC_WATCH_WORK_FIELDS,
)
_SEMANTIC_WATCH_QUOTE_STYLES = (
    "single",
    "double",
    "escaped-double",
)
_SEMANTIC_DUPLICATE_WATCH_CASES = [
    pytest.param(
        field,
        quote_style,
        order,
        value_mode,
        id=f"{field}-{quote_style}-{order}-{value_mode}",
    )
    for field in _SEMANTIC_WATCH_FIELDS
    for quote_style in _SEMANTIC_WATCH_QUOTE_STYLES
    for order in ("quoted-then-plain", "plain-then-quoted")
    for value_mode in ("quoted-invalid", "plain-invalid")
] + [
    pytest.param(
        field,
        quote_style,
        "quoted-then-plain",
        "equal",
        id=f"{field}-{quote_style}-equal",
    )
    for field in _SEMANTIC_WATCH_FIELDS
    for quote_style in _SEMANTIC_WATCH_QUOTE_STYLES
]


def _quoted_watch_key(field, quote_style):
    if quote_style == "single":
        return f"'{field}'"
    if quote_style == "double":
        return json.dumps(field)
    return f'"\\u{ord(field[0]):04x}{field[1:]}"'


def _semantic_watch_value(field, *, current_work_id, valid):
    if field == "decision":
        return "accepted_watch" if valid else "rejected"
    if field == "status":
        return "accepted" if valid else "rejected"
    if field in _SEMANTIC_WATCH_REVIEWER_FIELDS:
        return "qa-independent" if valid else None
    linked_id = (
        "TASK-AR-645"
        if field == "task_id"
        else current_work_id
    )
    if not valid:
        linked_id = (
            "TASK-AR-999"
            if field == "task_id"
            else "UNIT-TASK-AR-999-001"
        )
    return [linked_id] if field == "work_ids" else linked_id


def _render_watch_frontmatter(entries):
    rows = []
    for key, value in entries:
        if isinstance(value, list):
            rows.append(f"{key}:\n")
            rows.extend(f"  - {item}\n" for item in value)
        else:
            scalar = "null" if value is None else str(value)
            rows.append(f"{key}: {scalar}\n")
    return "---\n" + "".join(rows) + "---\n\n# Semantic watch authority\n"


def _semantic_duplicate_accepted_watch_document(
    *,
    field,
    quote_style,
    order,
    value_mode,
    current_work_id,
):
    reviewer_field = (
        field
        if field in _SEMANTIC_WATCH_REVIEWER_FIELDS
        else "reviewed_by"
    )
    work_field = (
        field if field in _SEMANTIC_WATCH_WORK_FIELDS else "work_id"
    )
    base_fields = ("status", "decision", reviewer_field, work_field)
    if value_mode == "quoted-invalid":
        quoted_valid, plain_valid = False, True
    elif value_mode == "plain-invalid":
        quoted_valid, plain_valid = True, False
    else:
        quoted_valid = plain_valid = True
    semantic_pair = [
        (
            _quoted_watch_key(field, quote_style),
            _semantic_watch_value(
                field,
                current_work_id=current_work_id,
                valid=quoted_valid,
            ),
        ),
        (
            field,
            _semantic_watch_value(
                field,
                current_work_id=current_work_id,
                valid=plain_valid,
            ),
        ),
    ]
    if order == "plain-then-quoted":
        semantic_pair.reverse()

    entries = []
    for key in base_fields:
        if key == field:
            entries.extend(semantic_pair)
        else:
            entries.append(
                (
                    key,
                    _semantic_watch_value(
                        key,
                        current_work_id=current_work_id,
                        valid=True,
                    ),
                )
            )
    return _render_watch_frontmatter(entries)


def _quoted_accepted_watch_document(*, quote_style, current_work_id):
    return _render_watch_frontmatter(
        [
            (
                _quoted_watch_key(field, quote_style),
                _semantic_watch_value(
                    field,
                    current_work_id=current_work_id,
                    valid=True,
                ),
            )
            for field in ("status", "decision", "reviewed_by", "work_id")
        ]
    )


_SEMANTIC_SCALAR_INVALID_STYLES = (
    "nested-single-inside-double",
    "nested-double-inside-single",
    "mixed-single-double",
    "mixed-double-single",
)
_SEMANTIC_SCALAR_VALID_STYLES = (
    "single",
    "double",
    "escaped-double",
)
_INDENTED_WATCH_FRAGMENTS = (
    pytest.param(
        "  decision: rejected\n",
        id="space-indented-authority",
    ),
    pytest.param(
        "\tdecision: rejected\n",
        id="tab-indented-authority",
    ),
    pytest.param(
        "summary: accepted\n  rejected\n",
        id="malformed-continuation",
    ),
    pytest.param(
        "  - rejected\n",
        id="orphan-list-item",
    ),
)


def _valid_watch_scalar(field, *, current_work_id):
    value = _semantic_watch_value(
        field,
        current_work_id=current_work_id,
        valid=True,
    )
    if isinstance(value, list):
        return str(value[0])
    return str(value)


def _styled_watch_scalar(value, style):
    if style == "single":
        return f"'{value}'"
    if style == "double":
        return json.dumps(value)
    if style == "escaped-double":
        return f'"\\u{ord(value[0]):04x}{value[1:]}"'
    if style == "nested-single-inside-double":
        return json.dumps(f"'{value}'")
    if style == "nested-double-inside-single":
        return f"'\"{value}\"'"
    if style == "mixed-single-double":
        return f"'{value}\""
    return f"\"{value}'"


def _semantic_scalar_accepted_watch_document(
    *,
    field,
    style,
    current_work_id,
):
    reviewer_field = (
        field
        if field in _SEMANTIC_WATCH_REVIEWER_FIELDS
        else "reviewed_by"
    )
    work_field = (
        field if field in _SEMANTIC_WATCH_WORK_FIELDS else "work_id"
    )
    rows = []
    for key in ("status", "decision", reviewer_field, work_field):
        if key == field:
            scalar = _styled_watch_scalar(
                _valid_watch_scalar(
                    field,
                    current_work_id=current_work_id,
                ),
                style,
            )
            if key == "work_ids":
                rows.extend((f"{key}:\n", f"  - {scalar}\n"))
            else:
                rows.append(f"{key}: {scalar}\n")
            continue
        value = _semantic_watch_value(
            key,
            current_work_id=current_work_id,
            valid=True,
        )
        if isinstance(value, list):
            rows.append(f"{key}:\n")
            rows.extend(f"  - {item}\n" for item in value)
        else:
            rows.append(f"{key}: {value}\n")
    return "---\n" + "".join(rows) + "---\n\n# Semantic scalar authority\n"


def _indented_accepted_watch_document(*, fragment, current_work_id):
    return (
        "---\n"
        f"{fragment}"
        "status: accepted\n"
        "decision: accepted_watch\n"
        "reviewed_by: qa-independent\n"
        f"work_id: {current_work_id}\n"
        "---\n\n# Indented watch authority\n"
    )


_NONCANONICAL_LIST_INDENT_STYLES = (
    "tab-only",
    "space-tab",
    "tab-space",
    "inconsistent",
)
_NBSP_AUTHORITY_POSITIONS = (
    "key-before",
    "key-after",
    "value-before",
    "value-after",
)
_NONEXACT_MARKER_STYLES = (
    "tab-open",
    "tab-close",
    "nbsp-open",
    "nbsp-close",
)
_SPLITLINES_SEPARATORS = (
    pytest.param("\v", id="vt"),
    pytest.param("\f", id="ff"),
    pytest.param("\x1c", id="fs"),
    pytest.param("\x1d", id="gs"),
    pytest.param("\x1e", id="rs"),
    pytest.param("\x85", id="nel"),
    pytest.param("\u2028", id="line-separator"),
    pytest.param("\u2029", id="paragraph-separator"),
)
_FRONTMATTER_MARKER_POSITIONS = ("opening", "closing")
_LOSSY_AUTHORITY_STYLES = (
    "decision-padding",
    "status-padding",
    "work-id-padding",
    "work-ids-padding",
    "decision-nfkc",
    "status-nfkc",
    "work-id-nfkc",
    "work-ids-nfkc",
)


def _noncanonical_work_ids_watch_document(*, style, current_work_id):
    if style == "tab-only":
        items = f"\t- {current_work_id}\n"
    elif style == "space-tab":
        items = f" \t- {current_work_id}\n"
    elif style == "tab-space":
        items = f"\t - {current_work_id}\n"
    else:
        items = (
            "  - UNIT-TASK-AR-999-001\n"
            f"   - {current_work_id}\n"
        )
    return (
        "---\n"
        "status: accepted\n"
        "decision: accepted_watch\n"
        "reviewed_by: qa-independent\n"
        "work_ids:\n"
        f"{items}"
        "---\n\n# Noncanonical list indentation\n"
    )


def _nbsp_accepted_watch_document(*, field, position, current_work_id):
    reviewer_field = (
        field
        if field in _SEMANTIC_WATCH_REVIEWER_FIELDS
        else "reviewed_by"
    )
    work_field = (
        field if field in _SEMANTIC_WATCH_WORK_FIELDS else "work_id"
    )
    rows = []
    for key in ("status", "decision", reviewer_field, work_field):
        value = _semantic_watch_value(
            key,
            current_work_id=current_work_id,
            valid=True,
        )
        rendered_key = key
        if key == field and position == "key-before":
            rendered_key = "\u00a0" + key
        elif key == field and position == "key-after":
            rendered_key = key + "\u00a0"

        if isinstance(value, list):
            scalar = str(value[0])
            if key == field and position == "value-before":
                scalar = "\u00a0" + scalar
            elif key == field and position == "value-after":
                scalar += "\u00a0"
            rows.extend((f"{rendered_key}:\n", f"  - {scalar}\n"))
            continue

        scalar = str(value)
        if key == field and position == "value-before":
            scalar = "\u00a0" + scalar
        elif key == field and position == "value-after":
            scalar += "\u00a0"
        rows.append(f"{rendered_key}: {scalar}\n")
    return "---\n" + "".join(rows) + "---\n\n# NBSP authority\n"


def _nonexact_marker_watch_document(*, style, current_work_id):
    opening = "---"
    closing = "---"
    if style == "tab-open":
        opening = "\t---"
    elif style == "tab-close":
        closing = "\t---"
    elif style == "nbsp-open":
        opening = "\u00a0---\u00a0"
    else:
        closing = "\u00a0---\u00a0"
    return (
        f"{opening}\n"
        "status: accepted\n"
        "decision: accepted_watch\n"
        "reviewed_by: qa-independent\n"
        f"work_id: {current_work_id}\n"
        f"{closing}\n"
        "---\n\n# Nonexact marker authority\n"
    )


def _line_boundary_accepted_watch_document(
    *, separator, marker_position, current_work_id
):
    opening_ending = separator if marker_position == "opening" else "\n"
    closing_ending = separator if marker_position == "closing" else "\n"
    return (
        f"---{opening_ending}"
        "status: accepted\n"
        "decision: accepted_watch\n"
        "reviewed_by: qa-independent\n"
        f"work_id: {current_work_id}\n"
        f"---{closing_ending}"
        "# Noncanonical physical line boundary\n"
    )


def _accepted_watch_bytes(*, watch_format, current_work_id, size=None):
    if watch_format == "markdown":
        prefix = (
            "---\n"
            "status: accepted\n"
            "decision: accepted_watch\n"
            "reviewed_by: qa-independent\n"
            f"work_id: {current_work_id}\n"
            "---\n"
            "# Raw accepted-watch size fixture\n"
        ).encode("utf-8")
        if size is None:
            return prefix
        assert len(prefix) <= size
        return prefix + (b"x" * (size - len(prefix)))

    prefix = (
        "{"
        '"status":"accepted",'
        '"decision":"accepted_watch",'
        '"reviewed_by":"qa-independent",'
        f'"work_id":"{current_work_id}",'
        '"padding":"'
    ).encode("utf-8")
    suffix = b'"}'
    if size is None:
        return prefix + suffix
    assert len(prefix) + len(suffix) <= size
    return prefix + (b"x" * (size - len(prefix) - len(suffix))) + suffix


def _fullwidth_ascii(value):
    return "".join(
        chr(ord(character) + 0xFEE0)
        if 0x21 <= ord(character) <= 0x7E
        else character
        for character in value
    )


def _lossy_accepted_watch_document(
    *,
    style,
    watch_format,
    current_work_id,
):
    field, mode = style.rsplit("-", 1)
    field = field.replace("-", "_")
    target_field = "work_id" if field == "work_id" else field
    if field == "work_ids":
        target_field = "work_ids"
    canonical = {
        "decision": "accepted_watch",
        "status": "accepted",
        "work_id": current_work_id,
        "work_ids": current_work_id,
    }[target_field]
    semantic = (
        f" {canonical} "
        if mode == "padding"
        else _fullwidth_ascii(canonical)
    )
    values = {
        "status": "accepted",
        "decision": "accepted_watch",
        "reviewed_by": "qa-independent",
        "work_id": current_work_id,
    }
    if target_field == "work_ids":
        values.pop("work_id")
        values["work_ids"] = [semantic]
    else:
        values[target_field] = semantic

    if watch_format == "json":
        return json.dumps(values, ensure_ascii=False, indent=2) + "\n"

    rows = []
    for key, value in values.items():
        if isinstance(value, list):
            scalar = str(value[0])
            if key == target_field and mode == "padding":
                scalar = f"'{scalar}'"
            rows.extend((f"{key}:\n", f"  - {scalar}\n"))
            continue
        scalar = str(value)
        if key == target_field and mode == "padding":
            scalar = f"'{scalar}'"
        rows.append(f"{key}: {scalar}\n")
    return "---\n" + "".join(rows) + "---\n\n# Lossy authority\n"


def test_substantial_closeout_blocks_for_overdue_missing_projection():
    base = closure_gate.decide(
        200,
        {"compound": False, "review": True, "retro": False},
        threshold=80,
        disabled=False,
        now_lines=200,
    )
    result = closure_gate.apply_scribe_obligation(
        base,
        _scribe_evaluation(),
        substantial_lines=200,
        threshold=80,
        disabled=False,
    )
    assert result["decision"] == "block"
    assert result["reason"] == "scribe-source-debt-overdue"
    assert result["missing"] == ["scribe_source_debt", "scribe_projection"]
    assert "projection is only a bounded view" in result["message"]


def test_mini_closeout_and_due_state_keep_scribe_advisory():
    for lines, evaluation in (
        (20, _scribe_evaluation()),
        (
            200,
            _scribe_evaluation(state="due", projection="missing", blocking=False),
        ),
    ):
        base = closure_gate.decide(
            lines,
            {"compound": False, "review": True, "retro": False},
            threshold=80,
            disabled=False,
            now_lines=lines,
        )
        result = closure_gate.apply_scribe_obligation(
            base,
            evaluation,
            substantial_lines=lines,
            threshold=80,
            disabled=False,
        )
        assert result["decision"] == "approve"


def test_fresh_projection_does_not_satisfy_overdue_source_debt():
    base = closure_gate.decide(
        200,
        {"compound": False, "review": True, "retro": False},
        threshold=80,
        disabled=False,
        now_lines=200,
    )
    result = closure_gate.apply_scribe_obligation(
        base,
        _scribe_evaluation(
            projection="fresh",
            blocking=True,
            reasons=["source-debt-overdue"],
        ),
        substantial_lines=200,
        threshold=80,
        disabled=False,
    )
    assert result["decision"] == "block"
    assert result["missing"] == ["scribe_source_debt"]
    assert result["scribe"]["projection"]["status"] == "fresh"


def test_verified_cleanup_or_owner_decision_satisfies_substantial_scribe_obligation():
    base = closure_gate.decide(
        200,
        {"compound": False, "review": True, "retro": False},
        threshold=80,
        disabled=False,
        now_lines=200,
    )
    for evaluation in (
        _scribe_evaluation(
            state="ok",
            projection="fresh",
            blocking=False,
            cleanup_status="verified_reduction",
        ),
        _scribe_evaluation(
            projection="fresh",
            blocking=False,
            cleanup_status="owner_decision",
        ),
    ):
        result = closure_gate.apply_scribe_obligation(
            dict(base),
            evaluation,
            substantial_lines=200,
            threshold=80,
            disabled=False,
        )
        assert result["decision"] == "approve"


def test_missing_active_coverage_has_its_own_closure_obligation():
    base = closure_gate.decide(
        200,
        {"compound": False, "review": True, "retro": False},
        threshold=80,
        disabled=False,
        now_lines=200,
    )
    evaluation = _scribe_evaluation(
        state="ok",
        projection="fresh",
        blocking=True,
        reasons=["active-coverage-incomplete"],
    )
    evaluation["active_coverage"] = {
        "status": "incomplete",
        "missing_task_ids": ["TASK-ACTIVE"],
        "missing_claim_ids": ["CLAIM-ACTIVE"],
    }

    result = closure_gate.apply_scribe_obligation(
        base,
        evaluation,
        substantial_lines=200,
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "block"
    assert result["reason"] == "scribe-active-coverage-incomplete"
    assert result["missing"] == ["scribe_active_coverage"]


def test_substantial_closeout_blocks_for_configured_source_integrity(
    tmp_path,
    monkeypatch,
):
    _write_direct_runtime(tmp_path)
    source = tmp_path / "state" / "current.json"
    source.parent.mkdir(parents=True)
    source.write_text('{"items":[],"items":[]}\n', encoding="utf-8")
    (tmp_path / "agent_runtime.yml").write_text(
        "schema: agent-runtime-config/v2\n"
        "project: closure-fixture\n"
        "sync:\n"
        "  mode: check-diff-apply\n"
        "  allow_silent_overwrite: false\n"
        "profiles:\n"
        "  - core\n"
        "ownership:\n"
        "  host_owned:\n"
        "    - state/current.json\n"
        "host:\n"
        "  state_adapters:\n"
        "    state: state/current.json\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        closure_gate,
        "count_substantial_lines",
        lambda *args, **kwargs: 200,
    )
    monkeypatch.setattr(
        closure_gate,
        "has_closure_record",
        lambda *args, **kwargs: {
            "compound": False,
            "review": True,
            "retro": False,
        },
    )

    result = closure_gate.assess(tmp_path, threshold=80, disabled=False)

    assert result["decision"] == "block"
    assert result["reason"] == "scribe-source-integrity"
    assert result["missing"] == ["scribe_source_integrity"]
    assert "state/current.json" in result["message"]
    assert "repair" in result["message"].lower()


@pytest.mark.parametrize(
    "raw",
    [
        (
            "schema: agent-runtime-config/v2\n"
            "project: invalid-fixture\n"
            "sync:\n"
            "  mode: check-diff-apply\n"
            "  allow_silent_overwrite: false\n"
            "ownership:\n"
            "  host_owned:\n"
            "    - ../outside.md\n"
        ),
        (
            "schema: agent-runtime-config/v2\n"
            "project: invalid-fixture\n"
            "sync:\n"
            "  mode: check-diff-apply\n"
            "  allow_silent_overwrite: false\n"
            "ownership:\n"
            "  host_owned:\n"
            "    - state/current.md\n"
            "host:\n"
            "  state_adapters:\n"
            "    escaped: ../outside.md\n"
        ),
        (
            "  project: invalid-fixture\n"
            "  sync:\n"
            "    mode: check-diff-apply\n"
            "    allow_silent_overwrite: false\n"
        ),
        (
            "schema: agent-runtime-config/v1\n"
            "project: invalid-fixture\n"
            "sync:\n"
            "  mode: check-diff-apply\n"
            "  allow_silent_overwrite: false\n"
        ),
    ],
    ids=[
        "unsafe-ownership",
        "unsafe-adapter",
        "malformed",
        "schema-invalid",
    ],
)
def test_substantial_closeout_blocks_for_invalid_runtime_config_integrity(
    tmp_path,
    monkeypatch,
    raw,
):
    _write_direct_runtime(tmp_path)
    (tmp_path / "agent_runtime.yml").write_text(raw, encoding="utf-8")
    monkeypatch.setattr(
        closure_gate,
        "count_substantial_lines",
        lambda *args, **kwargs: 200,
    )
    monkeypatch.setattr(
        closure_gate,
        "has_closure_record",
        lambda *args, **kwargs: {
            "compound": False,
            "review": True,
            "retro": False,
        },
    )

    result = closure_gate.assess(tmp_path, threshold=80, disabled=False)

    assert result["decision"] == "block"
    assert result["reason"] == "scribe-source-integrity"
    assert result["missing"] == ["scribe_source_integrity"]
    assert result["scribe"]["unavailable_sources"] == ["agent_runtime.yml"]
    assert "agent_runtime.yml" in result["message"]
    assert "repair" in result["message"].lower()


# --- closure record detection ---

def test_has_closure_record_detects_today(tmp_path):
    _write_direct_runtime(tmp_path)
    (tmp_path / "agents" / "lead_engineer").mkdir(parents=True)
    (tmp_path / "agents" / "lead_engineer" / "compound_log.md").write_text(
        f"## COMPOUND-{TODAY}-001: something\n", encoding="utf-8")
    reviews = tmp_path / "reviews"
    reviews.mkdir()
    (reviews / f"RETRO-{TODAY}-x.md").write_text("retro", encoding="utf-8")
    (reviews / f"REVIEW-{TODAY}-y-closeout.md").write_text("review", encoding="utf-8")
    rec = closure_gate.has_closure_record(tmp_path, now=NOW)
    assert rec == {"compound": True, "review": True, "retro": True}


def test_has_closure_record_ignores_other_days(tmp_path):
    _write_direct_runtime(tmp_path)
    (tmp_path / "agents" / "lead_engineer").mkdir(parents=True)
    (tmp_path / "agents" / "lead_engineer" / "compound_log.md").write_text(
        "## COMPOUND-2026-06-10-001: old\n", encoding="utf-8")
    (tmp_path / "reviews").mkdir()
    (tmp_path / "reviews" / "RETRO-2026-06-10-x.md").write_text("old", encoding="utf-8")
    rec = closure_gate.has_closure_record(tmp_path, now=NOW)
    assert rec == {"compound": False, "review": False, "retro": False}


def _write_active_unit(
    root: Path,
    *,
    review_refs: list[str] | None = None,
    compound_refs: list[str] | None = None,
    signatures: list[str] | None = None,
    triggers: list[str] | None = None,
) -> None:
    unit_id = "UNIT-TASK-AR-645-001"
    unit_path = (
        root
        / "agents"
        / "lead_engineer"
        / "tasks"
        / "units"
        / "TASK-AR-645"
        / f"{unit_id}.md"
    )
    unit_path.parent.mkdir(parents=True, exist_ok=True)

    def block(name: str, values: list[str] | None) -> str:
        if not values:
            return ""
        return name + ":\n" + "".join(f"  - {value}\n" for value in values)

    unit_path.write_text(
        "---\n"
        "schema_version: agent-runtime-work-item/v1\n"
        f"work_id: {unit_id}\n"
        "kind: unit\n"
        "parent_id: TASK-AR-645\n"
        f"unit_id: {unit_id}\n"
        "task_id: TASK-AR-645\n"
        + block("review_refs", review_refs)
        + block("compound_refs", compound_refs)
        + block("defect_signatures", signatures)
        + block("escalation_triggers", triggers)
        + "---\n\n# Active unit\n",
        encoding="utf-8",
    )
    claims = root / "agents" / "runtime" / "task_claims"
    claims.mkdir(parents=True, exist_ok=True)
    (claims / "CLAIM-active.json").write_text(
        json.dumps(
            {
                "schema": "agent-runtime-task-claim/v1",
                "claim_id": "CLAIM-active",
                "status": "claimed",
                "task_id": "TASK-AR-645",
                "unit_id": unit_id,
                "unit_spec": unit_path.relative_to(root).as_posix(),
                "updated_at": "2026-06-14T11:00:00+09:00",
            }
        ),
        encoding="utf-8",
    )


def _write_canonical_active_claim(
    root: Path,
    *,
    claim_id: str = "CLAIM-active",
    task_id: str = "TASK-AR-645",
    unit_id: str = "UNIT-TASK-AR-645-001",
    unit_spec: str | None = None,
    worktree_path: str | None = None,
    defect_signatures: list[str] | None = None,
    escalation_triggers: list[str] | None = None,
    overlay: bool = False,
) -> Path:
    if unit_spec is None:
        unit_spec = (
            "agents/lead_engineer/tasks/units/TASK-AR-645/"
            "UNIT-TASK-AR-645-001.md"
        )
    claim = {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": claim_id,
        "task_id": task_id,
        "unit_id": unit_id,
        "unit_spec": unit_spec,
        "agent_role": "lead-engineer",
        "team_id": "agent-runtime-core",
        "agent_instance_id": f"test-{claim_id.lower()}",
        "display_name": f"lead_engineer@{claim_id.lower()}",
        "callsite_id": f"terminal:{claim_id.lower()}",
        "pane_id": f"terminal:{claim_id.lower()}",
        "mode": "work",
        "status": "claimed",
        "task_set_id": "TASKSET-AR-TEST",
        "active_scope": "TASKSET-AR-TEST",
        "project_id": "PROJECT-AGENT-RUNTIME",
        "model_tier": "worker_standard",
        "wip_slot": 1,
        "stop_condition": "Stop after the declared unit.",
        "phase": "claim-created",
        "progress_pct": 0,
        "step_index": 1,
        "step_total": 2,
        "status_text": "Claim-only repeated-failure fixture",
        "worktree_path": worktree_path or str(root.resolve()),
        "branch": f"test/{claim_id.lower()}",
        "claimed_at": "2026-06-14T11:00:00+09:00",
        "last_heartbeat": "2026-06-14T11:00:00+09:00",
        "updated_at": "2026-06-14T11:00:00+09:00",
        "expires_at": "2099-06-14T11:30:00+09:00",
        "lease": {
            "claimed_at": "2026-06-14T11:00:00+09:00",
            "heartbeat_at": "2026-06-14T11:00:00+09:00",
            "expires_at": "2099-06-14T11:30:00+09:00",
        },
        "handoff_path": f"agents/runtime/task_claims/{claim_id}.handoff.md",
        "log_path": f"agents/runtime/task_claims/{claim_id}.log.md",
        "allow_parallel_task_set": False,
        "tags": [],
        "target_files": [unit_spec] if unit_spec else [],
        "defect_signatures": defect_signatures or [],
        "escalation_triggers": escalation_triggers or [],
    }
    if overlay:
        claim["overlay"] = True
    claims = root / "agents" / "runtime" / "task_claims"
    claims.mkdir(parents=True, exist_ok=True)
    path = claims / f"{claim_id}.json"
    path.write_text(json.dumps(claim, indent=2) + "\n", encoding="utf-8")
    persisted = json.loads(path.read_text(encoding="utf-8"))
    assert persisted["schema"] == "agent-runtime-task-claim/v1"
    assert persisted["claim_id"] == claim_id
    return path


def test_active_claim_store_rejects_windows_name_surrogate_parent_metadata(
    tmp_path,
    monkeypatch,
):
    runtime_dir = tmp_path / "agents" / "runtime"
    runtime_dir.mkdir(parents=True)
    original_lstat = Path.lstat
    runtime_stat = original_lstat(runtime_dir)

    def simulated_windows_lstat(path):
        metadata = original_lstat(path)
        if path == runtime_dir:
            return SimpleNamespace(
                st_mode=runtime_stat.st_mode,
                st_file_attributes=0x0400,
                st_reparse_tag=0xA0000003,
            )
        return metadata

    monkeypatch.setattr(Path, "lstat", simulated_windows_lstat)

    claims, findings = closure_gate._active_claims(tmp_path)

    assert claims == []
    assert findings == ["active-claim-store-integrity-invalid"]


def _write_linked_review(root: Path) -> str:
    review_ref = f"reviews/REVIEW-{TODAY}-claim-only-closeout.md"
    review = root / review_ref
    review.parent.mkdir(parents=True, exist_ok=True)
    review.write_text(
        "---\n"
        "work_id: UNIT-TASK-AR-645-001\n"
        "task_id: TASK-AR-645\n"
        "---\n\n# Generic linked review\n",
        encoding="utf-8",
    )
    return review_ref


def _write_repeat_watch_context(
    root: Path,
    *,
    watch_format: str,
    raw_watch: bytes,
    signature: str,
) -> tuple[str, str]:
    unit_id = "UNIT-TASK-AR-645-001"
    suffix = "json" if watch_format == "json" else "md"
    watch_ref = f"reviews/REVIEW-{TODAY}-raw-watch-stop.{suffix}"
    watch = root / watch_ref
    watch.parent.mkdir(parents=True, exist_ok=True)
    watch.write_bytes(raw_watch)
    record_path, _record = compound_record.create_record(
        root,
        work_ids=[unit_id],
        defect_signatures=[signature],
        title="Bound accepted-watch input",
        summary="Authority-bearing watch input must fail closed within a bound.",
        cause="A malformed or oversized watch escaped bounded validation.",
        prevention="Reject malformed and oversized watch bytes before authority parsing.",
        source_refs=["reviews/source.md"],
        prevention_refs=[watch_ref],
        verification_refs=["reviews/VERIFY-unit.json"],
        created_at="2026-06-14T11:54:00+09:00",
    )
    _write_active_unit(
        root,
        compound_refs=[compound_record.record_ref(root, record_path)],
        signatures=[signature],
    )
    return unit_id, watch_ref


def _set_low_churn_and_neutral_scribe(monkeypatch) -> None:
    monkeypatch.setattr(
        closure_gate, "count_substantial_lines", lambda *args, **kwargs: 10
    )
    monkeypatch.setattr(
        closure_gate.state_projection,
        "evaluate_state",
        lambda _root: _scribe_evaluation(
            state="ok", projection="fresh", blocking=False
        ),
    )


def _run_actual_stop_hook(root: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("AGENT_RUNTIME_CLOSURE_GATE_DISABLE", None)
    env["AGENT_RUNTIME_STOP_SCOPE_DISABLE"] = "1"
    env["AGENT_RUNTIME_CLOSURE_GATE_THRESHOLD"] = "80"
    local_source = str(ROOT / "src")
    env["PYTHONPATH"] = os.pathsep.join(
        value for value in (local_source, env.get("PYTHONPATH", "")) if value
    )
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "stop_hook_closure_gate.py")],
        cwd=root,
        env=env,
        input="{}\n",
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_active_work_rejects_unrelated_same_day_records(tmp_path):
    unrelated_review = f"reviews/REVIEW-{TODAY}-unrelated-closeout.md"
    path = tmp_path / unrelated_review
    path.parent.mkdir(parents=True)
    path.write_text(
        "---\nwork_id: TASK-AR-999\n---\n\n# Unrelated review\n",
        encoding="utf-8",
    )
    (path.parent / f"RETRO-{TODAY}-unrelated.md").write_text(
        "---\nwork_id: TASK-AR-999\n---\n", encoding="utf-8"
    )
    legacy = tmp_path / "agents" / "lead_engineer" / "compound_log.md"
    legacy.parent.mkdir(parents=True)
    legacy.write_text(
        f"## COMPOUND-{TODAY}-999: unrelated\n", encoding="utf-8"
    )
    _write_active_unit(tmp_path, review_refs=[unrelated_review])

    rec = closure_gate.has_closure_record(tmp_path, now=NOW)

    assert rec == {"compound": False, "review": False, "retro": False}


def test_active_work_accepts_explicit_linked_review_and_compound(tmp_path):
    review_ref = f"reviews/REVIEW-{TODAY}-task-ar-645-closeout.md"
    review = tmp_path / review_ref
    review.parent.mkdir(parents=True)
    review.write_text(
        "---\n"
        "work_id: UNIT-TASK-AR-645-001\n"
        "task_id: TASK-AR-645\n"
        "---\n\n# Linked review\n",
        encoding="utf-8",
    )
    record_path, _record = compound_record.create_record(
        tmp_path,
        work_ids=["UNIT-TASK-AR-645-001"],
        defect_signatures=["same-day unrelated closure"],
        title="Bind closure to work",
        summary="A same-day file was unrelated to the active unit.",
        cause="Closure searched only by date.",
        prevention="Require explicit references linked to the work.",
        source_refs=[review_ref],
        prevention_refs=["scripts/closure_gate.py"],
        verification_refs=["reviews/VERIFY-unit.json"],
        created_at="2026-06-14T11:30:00+09:00",
    )
    compound_ref = compound_record.record_ref(tmp_path, record_path)
    _write_active_unit(
        tmp_path,
        review_refs=[review_ref],
        compound_refs=[compound_ref],
        signatures=["same-day unrelated closure"],
    )

    rec = closure_gate.has_closure_record(tmp_path, now=NOW)

    assert rec == {"compound": True, "review": True, "retro": False}


def test_declared_repeat_blocks_review_only_even_below_churn_threshold(
    tmp_path,
    monkeypatch,
):
    review_ref = f"reviews/REVIEW-{TODAY}-repeat-review-only.md"
    review = tmp_path / review_ref
    review.parent.mkdir(parents=True)
    review.write_text(
        "---\n"
        "work_id: UNIT-TASK-AR-645-001\n"
        "task_id: TASK-AR-645\n"
        "---\n\n# Linked review only\n",
        encoding="utf-8",
    )
    _write_active_unit(
        tmp_path,
        review_refs=[review_ref],
        signatures=["review-only repeated failure"],
    )
    monkeypatch.setattr(
        closure_gate, "count_substantial_lines", lambda *args, **kwargs: 10
    )
    monkeypatch.setattr(
        closure_gate.state_projection,
        "evaluate_state",
        lambda _root: _scribe_evaluation(
            state="ok", projection="fresh", blocking=False
        ),
    )

    result = closure_gate.assess(
        tmp_path,
        work_id="UNIT-TASK-AR-645-001",
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "block"
    assert result["reason"] == "repeated-failure-compound-required"
    assert result["repeat_failure"]["required"] is True


@pytest.mark.parametrize("claim_signal", ("repeated_failure", "defect_signature"))
def test_inferred_stop_context_preserves_claim_only_repeat_authority(
    tmp_path,
    monkeypatch,
    claim_signal,
):
    review_ref = _write_linked_review(tmp_path)
    _write_active_unit(tmp_path, review_refs=[review_ref])
    _write_canonical_active_claim(
        tmp_path,
        defect_signatures=(
            [_CLAIM_ONLY_SIGNATURE]
            if claim_signal == "defect_signature"
            else []
        ),
        escalation_triggers=(
            ["repeated_failure"]
            if claim_signal == "repeated_failure"
            else []
        ),
    )
    _set_low_churn_and_neutral_scribe(monkeypatch)

    result = closure_gate.assess(
        tmp_path,
        now=NOW,
        threshold=80,
        disabled=False,
    )

    assert result["substantial_lines"] == 10
    assert result["records"]["review"] is True
    assert result["repeat_failure"]["required"] is True
    assert result["decision"] == "block"
    assert result["reason"] == "repeated-failure-compound-required"
    if claim_signal == "defect_signature":
        assert result["repeat_failure"]["defect_signatures"] == [
            _CLAIM_ONLY_SIGNATURE
        ]
    else:
        assert "repeated_failure" in result["repeat_failure"][
            "escalation_triggers"
        ]


@pytest.mark.parametrize("claim_signal", ("repeated_failure", "defect_signature"))
def test_explicit_stop_context_preserves_matching_claim_only_repeat_authority(
    tmp_path,
    monkeypatch,
    claim_signal,
):
    review_ref = _write_linked_review(tmp_path)
    _write_active_unit(tmp_path, review_refs=[review_ref])
    _write_canonical_active_claim(
        tmp_path,
        defect_signatures=(
            [_CLAIM_ONLY_SIGNATURE]
            if claim_signal == "defect_signature"
            else []
        ),
        escalation_triggers=(
            ["repeated_failure"]
            if claim_signal == "repeated_failure"
            else []
        ),
    )
    _set_low_churn_and_neutral_scribe(monkeypatch)

    result = closure_gate.assess(
        tmp_path,
        work_id="UNIT-TASK-AR-645-001",
        now=NOW,
        threshold=80,
        disabled=False,
    )

    assert result["repeat_failure"]["required"] is True
    assert result["decision"] == "block"
    assert result["reason"] == "repeated-failure-compound-required"


def test_explicit_task_context_uses_task_work_id_when_parent_is_taskset(
    tmp_path,
    monkeypatch,
):
    review_ref = _write_linked_review(tmp_path)
    _write_active_unit(tmp_path, review_refs=[review_ref])
    task_path = (
        tmp_path
        / "agents"
        / "lead_engineer"
        / "tasks"
        / "TASK-AR-645.md"
    )
    task_path.write_text(
        "---\n"
        "schema_version: agent-runtime-work-item/v1\n"
        "id: TASK-AR-645\n"
        "work_id: TASK-AR-645\n"
        "kind: task\n"
        "parent_id: TASKSET-AR-TEST\n"
        "unit_spec: agents/lead_engineer/tasks/units/TASK-AR-645/"
        "UNIT-TASK-AR-645-001.md\n"
        "review_refs:\n"
        f"  - {review_ref}\n"
        "---\n\n# Active task\n",
        encoding="utf-8",
    )
    _write_canonical_active_claim(
        tmp_path,
        defect_signatures=[_CLAIM_ONLY_SIGNATURE],
        escalation_triggers=["repeated_failure"],
    )
    _set_low_churn_and_neutral_scribe(monkeypatch)

    result = closure_gate.assess(
        tmp_path,
        work_id="TASK-AR-645",
        now=NOW,
        threshold=80,
        disabled=False,
    )

    assert result["reason"] == "repeated-failure-compound-required"
    assert result["repeat_failure"]["required"] is True
    assert result["repeat_failure"]["defect_signatures"] == [
        _CLAIM_ONLY_SIGNATURE
    ]


@pytest.mark.parametrize("claim_signal", ("repeated_failure", "defect_signature"))
def test_actual_stop_hook_blocks_claim_only_repeat_below_churn(
    tmp_path,
    claim_signal,
):
    review_ref = _write_linked_review(tmp_path)
    _write_active_unit(tmp_path, review_refs=[review_ref])
    _write_canonical_active_claim(
        tmp_path,
        defect_signatures=(
            [_CLAIM_ONLY_SIGNATURE]
            if claim_signal == "defect_signature"
            else []
        ),
        escalation_triggers=(
            ["repeated_failure"]
            if claim_signal == "repeated_failure"
            else []
        ),
    )

    result = _run_actual_stop_hook(tmp_path)

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["decision"] == "block"
    assert payload["reason"] == "repeated-failure-compound-required"


@pytest.mark.parametrize(
    ("claim_task_id", "claim_unit_id"),
    (
        pytest.param(
            "TASK-AR-999",
            "UNIT-TASK-AR-645-001",
            id="same-unit-wrong-task",
        ),
        pytest.param(
            "TASK-AR-645",
            "UNIT-TASK-AR-999-001",
            id="same-task-wrong-unit",
        ),
        pytest.param(
            "TASK-AR-999",
            "UNIT-TASK-AR-999-001",
            id="both-identities-wrong",
        ),
    ),
)
def test_inferred_stop_rejects_identity_mismatched_claim_without_signal_leak(
    tmp_path,
    monkeypatch,
    claim_task_id,
    claim_unit_id,
):
    review_ref = _write_linked_review(tmp_path)
    _write_active_unit(tmp_path, review_refs=[review_ref])
    _write_canonical_active_claim(
        tmp_path,
        task_id=claim_task_id,
        unit_id=claim_unit_id,
        unit_spec=(
            "agents/lead_engineer/tasks/units/TASK-AR-645/"
            "UNIT-TASK-AR-645-001.md"
        ),
        defect_signatures=[_CLAIM_ONLY_SIGNATURE],
        escalation_triggers=["repeated_failure"],
    )
    _set_low_churn_and_neutral_scribe(monkeypatch)

    result = closure_gate.assess(
        tmp_path,
        now=NOW,
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "block"
    assert result["reason"] == "active-claim-context-invalid"
    assert result["repeat_failure"]["defect_signatures"] == []
    assert "repeated_failure" not in result["repeat_failure"][
        "escalation_triggers"
    ]


def test_explicit_work_ignores_unrelated_active_claim_authority(
    tmp_path,
    monkeypatch,
):
    review_ref = _write_linked_review(tmp_path)
    _write_active_unit(tmp_path, review_refs=[review_ref])
    _write_canonical_active_claim(
        tmp_path,
        task_id="TASK-AR-999",
        unit_id="UNIT-TASK-AR-999-001",
        unit_spec="",
        worktree_path=str((tmp_path / "other-worktree").resolve()),
        defect_signatures=[_CLAIM_ONLY_SIGNATURE],
        escalation_triggers=["repeated_failure"],
    )
    _set_low_churn_and_neutral_scribe(monkeypatch)

    result = closure_gate.assess(
        tmp_path,
        work_id="UNIT-TASK-AR-645-001",
        now=NOW,
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "approve"
    assert result["reason"] == "not-substantial"
    assert result["records"]["review"] is True
    assert result["repeat_failure"]["required"] is False
    assert result["repeat_failure"]["defect_signatures"] == []
    assert "repeated_failure" not in result["repeat_failure"][
        "escalation_triggers"
    ]


@pytest.mark.parametrize(
    ("claim_task_id", "claim_unit_id"),
    (
        pytest.param(
            "TASK-AR-999",
            "UNIT-TASK-AR-645-001",
            id="same-unit-wrong-task",
        ),
        pytest.param(
            "TASK-AR-645",
            "UNIT-TASK-AR-999-001",
            id="same-task-wrong-unit",
        ),
    ),
)
def test_explicit_stop_rejects_partial_claim_identity_without_signal_leak(
    tmp_path,
    monkeypatch,
    claim_task_id,
    claim_unit_id,
):
    review_ref = _write_linked_review(tmp_path)
    _write_active_unit(tmp_path, review_refs=[review_ref])
    _write_canonical_active_claim(
        tmp_path,
        task_id=claim_task_id,
        unit_id=claim_unit_id,
        unit_spec=(
            "agents/lead_engineer/tasks/units/TASK-AR-645/"
            "UNIT-TASK-AR-645-001.md"
        ),
        defect_signatures=[_CLAIM_ONLY_SIGNATURE],
        escalation_triggers=["repeated_failure"],
    )
    _set_low_churn_and_neutral_scribe(monkeypatch)

    result = closure_gate.assess(
        tmp_path,
        work_id="UNIT-TASK-AR-645-001",
        now=NOW,
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "block"
    assert result["reason"] == "active-claim-context-invalid"
    assert result["repeat_failure"]["defect_signatures"] == []
    assert "repeated_failure" not in result["repeat_failure"][
        "escalation_triggers"
    ]


def test_inferred_stop_ignores_review_overlay_beside_valid_worker_claim(
    tmp_path,
    monkeypatch,
):
    review_ref = _write_linked_review(tmp_path)
    _write_active_unit(tmp_path, review_refs=[review_ref])
    worker_signature = compound_record.normalize_signature(
        "valid worker claim beside review overlay"
    )
    overlay_signature = compound_record.normalize_signature(
        "review overlay must not become closure authority"
    )
    _write_canonical_active_claim(
        tmp_path,
        claim_id="CLAIM-active-worker",
        defect_signatures=[worker_signature],
        escalation_triggers=["repeated_failure"],
    )
    _write_canonical_active_claim(
        tmp_path,
        claim_id="CLAIM-review-overlay",
        task_id="REVIEW-TASK-AR-645-independent-auditor",
        unit_id="",
        unit_spec="",
        defect_signatures=[overlay_signature],
        escalation_triggers=["repeated_failure"],
        overlay=True,
    )
    _set_low_churn_and_neutral_scribe(monkeypatch)

    result = closure_gate.assess(
        tmp_path,
        now=NOW,
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "block"
    assert result["reason"] == "repeated-failure-compound-required"
    assert result["reason"] != "active-claim-context-ambiguous"
    assert result["repeat_failure"]["defect_signatures"] == [worker_signature]
    assert overlay_signature not in result["repeat_failure"][
        "defect_signatures"
    ]


@pytest.mark.parametrize(
    "invalid_kind",
    ("schema", "claim-id", "malformed-json", "authority-type"),
)
def test_selected_active_claim_integrity_fails_closed_without_signal_leak(
    tmp_path,
    monkeypatch,
    invalid_kind,
):
    review_ref = _write_linked_review(tmp_path)
    _write_active_unit(tmp_path, review_refs=[review_ref])
    claim_path = _write_canonical_active_claim(
        tmp_path,
        defect_signatures=[_CLAIM_ONLY_SIGNATURE],
        escalation_triggers=["repeated_failure"],
    )
    if invalid_kind == "malformed-json":
        claim_path.write_bytes(b'{"status":"claimed",')
    else:
        payload = json.loads(claim_path.read_text(encoding="utf-8"))
        if invalid_kind == "schema":
            payload["schema"] = "agent-runtime-task-claim/v0"
        elif invalid_kind == "claim-id":
            payload["claim_id"] = "CLAIM-does-not-match-filename"
        else:
            payload["defect_signatures"] = {"not": "a-list"}
        claim_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    _set_low_churn_and_neutral_scribe(monkeypatch)

    result = closure_gate.assess(
        tmp_path,
        now=NOW,
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "block"
    assert result["reason"] == "active-claim-context-invalid"
    assert result["repeat_failure"]["defect_signatures"] == []
    assert "repeated_failure" not in result["repeat_failure"][
        "escalation_triggers"
    ]


def test_explicit_task_rejects_noncanonical_duplicate_unit_spec(
    tmp_path,
    monkeypatch,
):
    task = tmp_path / "agents/lead_engineer/tasks/TASK-AR-645.md"
    task.parent.mkdir(parents=True, exist_ok=True)
    task.write_text(
        "---\n"
        "schema_version: agent-runtime-work-item/v1\n"
        "work_id: TASK-AR-645\n"
        "id: TASK-AR-645\n"
        "kind: task\n"
        "status: in_progress\n"
        "---\n\n# Canonical task\n",
        encoding="utf-8",
    )
    canonical_unit = (
        tmp_path
        / "agents/lead_engineer/tasks/units/TASK-AR-645/"
        "UNIT-TASK-AR-645-001.md"
    )
    canonical_unit.parent.mkdir(parents=True, exist_ok=True)
    canonical_unit.write_text(
        "---\n"
        "schema_version: agent-runtime-work-item/v1\n"
        "work_id: UNIT-TASK-AR-645-001\n"
        "unit_id: UNIT-TASK-AR-645-001\n"
        "task_id: TASK-AR-645\n"
        "kind: unit\n"
        "---\n\n# Canonical unit\n",
        encoding="utf-8",
    )
    duplicate = canonical_unit.with_name("duplicate-self-declared-unit.md")
    duplicate.write_bytes(canonical_unit.read_bytes())
    _write_canonical_active_claim(
        tmp_path,
        unit_spec=duplicate.relative_to(tmp_path).as_posix(),
        defect_signatures=[_CLAIM_ONLY_SIGNATURE],
        escalation_triggers=["repeated_failure"],
    )
    _set_low_churn_and_neutral_scribe(monkeypatch)

    result = closure_gate.assess(
        tmp_path,
        work_id="TASK-AR-645",
        now=NOW,
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "block"
    assert result["reason"] == "active-claim-context-invalid"
    assert result["repeat_failure"]["defect_signatures"] == []


def test_inferred_stop_blocks_ambiguous_claims_without_unioning_authority(
    tmp_path,
    monkeypatch,
):
    review_ref = _write_linked_review(tmp_path)
    _write_active_unit(tmp_path, review_refs=[review_ref])
    first_signature = compound_record.normalize_signature(
        "first ambiguous claim authority"
    )
    second_signature = compound_record.normalize_signature(
        "second ambiguous claim authority"
    )
    _write_canonical_active_claim(
        tmp_path,
        claim_id="CLAIM-active",
        defect_signatures=[first_signature],
        escalation_triggers=["repeated_failure"],
    )
    _write_canonical_active_claim(
        tmp_path,
        claim_id="CLAIM-other",
        defect_signatures=[second_signature],
        escalation_triggers=["repeated_failure"],
    )
    _set_low_churn_and_neutral_scribe(monkeypatch)

    result = closure_gate.assess(
        tmp_path,
        now=NOW,
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "block"
    assert result["reason"] == "active-claim-context-ambiguous"
    assert result["missing"] == ["work_id"]
    assert result["repeat_failure"]["defect_signatures"] == []
    assert "repeated_failure" not in result["repeat_failure"][
        "escalation_triggers"
    ]
    assert result["repeat_failure"]["compound_refs"] == []


def test_inferred_stop_selects_primary_relative_claim_from_linked_worktree(
    tmp_path,
    monkeypatch,
):
    primary = tmp_path / "primary"
    primary.mkdir()
    assert _git(primary, "init").returncode == 0
    assert _git(primary, "config", "user.email", "test@example.invalid").returncode == 0
    assert _git(primary, "config", "user.name", "Test User").returncode == 0
    (primary / "seed.txt").write_text("seed\n", encoding="utf-8")
    assert _git(primary, "add", "seed.txt").returncode == 0
    assert _git(primary, "commit", "-m", "seed").returncode == 0

    local_worktree = primary / ".worktrees" / "TASK-AR-645"
    other_worktree = primary / ".worktrees" / "TASK-AR-999"
    assert _git(
        primary,
        "worktree",
        "add",
        "-b",
        "test/relative-local",
        str(local_worktree),
        "HEAD",
    ).returncode == 0

    # Relative claim paths are protocol-relative to the primary checkout.
    # A shadow path under the linked worktree must never win resolution.
    (local_worktree / ".worktrees" / "TASK-AR-645").mkdir(parents=True)
    (local_worktree / ".worktrees" / "TASK-AR-999").mkdir(parents=True)
    assert _git(
        primary,
        "worktree",
        "add",
        "-b",
        "test/relative-other",
        str(other_worktree),
        "HEAD",
    ).returncode == 0

    review_ref = _write_linked_review(local_worktree)
    _write_active_unit(local_worktree, review_refs=[review_ref])
    local_signature = compound_record.normalize_signature(
        "primary relative linked worktree authority"
    )
    other_signature = compound_record.normalize_signature(
        "other relative linked worktree authority"
    )
    _write_canonical_active_claim(
        local_worktree,
        claim_id="CLAIM-relative-local",
        worktree_path=".worktrees/TASK-AR-645",
        defect_signatures=[local_signature],
        escalation_triggers=["repeated_failure"],
    )
    _write_canonical_active_claim(
        local_worktree,
        claim_id="CLAIM-relative-other",
        task_id="TASK-AR-999",
        unit_id="UNIT-TASK-AR-999-001",
        unit_spec="",
        worktree_path=".worktrees/TASK-AR-999",
        defect_signatures=[other_signature],
        escalation_triggers=["repeated_failure"],
    )
    _set_low_churn_and_neutral_scribe(monkeypatch)
    monkeypatch.chdir(local_worktree)

    result = closure_gate.assess(
        local_worktree,
        now=NOW,
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "block"
    assert result["reason"] == "repeated-failure-compound-required"
    assert result["reason"] != "active-claim-context-ambiguous"
    assert result["repeat_failure"]["defect_signatures"] == [local_signature]
    assert other_signature not in result["repeat_failure"]["defect_signatures"]


def test_declared_repeat_accepts_current_compound_with_supported_prevention(
    tmp_path,
    monkeypatch,
):
    prevention = tmp_path / "scripts" / "closure_gate.py"
    prevention.parent.mkdir(parents=True)
    prevention.write_text("raise SystemExit(0)\n", encoding="utf-8")
    record_path, _record = compound_record.create_record(
        tmp_path,
        work_ids=["UNIT-TASK-AR-645-001", "TASK-AR-645"],
        defect_signatures=["repeat with prevention"],
        title="Prevent the repeated failure",
        summary="The repeated failure now has a durable prevention target.",
        cause="Review-only closure did not preserve the prevention.",
        prevention="Run an executable closure gate.",
        source_refs=["reviews/source.md"],
        prevention_refs=["scripts/closure_gate.py"],
        verification_refs=["reviews/VERIFY-unit.json"],
        created_at="2026-06-14T11:40:00+09:00",
    )
    _write_active_unit(
        tmp_path,
        compound_refs=[compound_record.record_ref(tmp_path, record_path)],
        signatures=["repeat with prevention"],
    )
    monkeypatch.setattr(
        closure_gate, "count_substantial_lines", lambda *args, **kwargs: 10
    )
    monkeypatch.setattr(
        closure_gate.state_projection,
        "evaluate_state",
        lambda _root: _scribe_evaluation(
            state="ok", projection="fresh", blocking=False
        ),
    )

    result = closure_gate.assess(
        tmp_path,
        work_id="UNIT-TASK-AR-645-001",
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "approve"
    assert result["reason"] == "repeated-failure-compound-present"
    assert result["repeat_failure"]["satisfied"] is True


@pytest.mark.parametrize(
    ("watch_metadata", "expected_finding"),
    [
        (
            "decision: accepted_watch\nreviewed_by: []\n",
            "compound:prevention-watch-reviewer-missing",
        ),
        (
            "decision: accepted_watch\nreviewed_by: null\n",
            "compound:prevention-watch-reviewer-missing",
        ),
        (
            "decision: accepted_watch\nreviewed_by: false\n",
            "compound:prevention-watch-reviewer-missing",
        ),
        (
            "decision: accepted_watch\nreviewed_by: TBD\n",
            "compound:prevention-watch-reviewer-missing",
        ),
        (
            "disposition: accepted_watch\nreviewed_by: qa-independent\n",
            "compound:prevention-destination-unsupported",
        ),
        (
            "prevention_status: accepted_watch\nreviewed_by: qa-independent\n",
            "compound:prevention-destination-unsupported",
        ),
        (
            "? decision\n"
            ": rejected\n"
            "decision: accepted_watch\n"
            "reviewed_by: qa-independent\n",
            "compound:prevention-watch-invalid",
        ),
        (
            "!!str decision: rejected\n"
            "decision: accepted_watch\n"
            "reviewed_by: qa-independent\n",
            "compound:prevention-watch-invalid",
        ),
        (
            "<<: *authority\n"
            "decision: accepted_watch\n"
            "reviewed_by: qa-independent\n",
            "compound:prevention-watch-invalid",
        ),
        (
            "\"\\x64ecision\": rejected\n"
            "decision: accepted_watch\n"
            "reviewed_by: qa-independent\n",
            "compound:prevention-watch-invalid",
        ),
        (
            "\"decision: rejected\n"
            "decision: accepted_watch\n"
            "reviewed_by: qa-independent\n",
            "compound:prevention-watch-invalid",
        ),
    ],
    ids=[
        "empty-list-reviewer",
        "null-reviewer",
        "boolean-reviewer",
        "placeholder-reviewer",
        "disposition-alias",
        "prevention-status-alias",
        "explicit-key-syntax",
        "tagged-key-syntax",
        "merge-key-syntax",
        "unsupported-key-escape",
        "unclosed-quoted-key",
    ],
)
def test_stop_gate_rejects_invalid_accepted_watch_metadata(
    tmp_path,
    monkeypatch,
    watch_metadata,
    expected_finding,
):
    unit_id = "UNIT-TASK-AR-645-001"
    signature = "invalid accepted watch authority"
    watch_ref = f"reviews/REVIEW-{TODAY}-invalid-watch-authority.md"
    watch = tmp_path / watch_ref
    watch.parent.mkdir(parents=True, exist_ok=True)
    watch.write_text(
        "---\n"
        "status: accepted\n"
        f"{watch_metadata}"
        f"work_id: {unit_id}\n"
        "---\n\n# Invalid accepted watch authority\n",
        encoding="utf-8",
    )
    record_path, _record = compound_record.create_record(
        tmp_path,
        work_ids=[unit_id],
        defect_signatures=[signature],
        title="Reject invalid accepted watch authority",
        summary="An accepted watch must carry explicit review authority.",
        cause="Untyped frontmatter values were coerced into reviewer identities.",
        prevention="Require an exact decision and a bounded reviewer identity.",
        source_refs=["reviews/source.md"],
        prevention_refs=[watch_ref],
        verification_refs=["reviews/VERIFY-unit.json"],
        created_at="2026-06-14T11:42:00+09:00",
    )
    _write_active_unit(
        tmp_path,
        compound_refs=[compound_record.record_ref(tmp_path, record_path)],
        signatures=[signature],
    )
    monkeypatch.setattr(
        closure_gate, "count_substantial_lines", lambda *args, **kwargs: 10
    )
    monkeypatch.setattr(
        closure_gate.state_projection,
        "evaluate_state",
        lambda _root: _scribe_evaluation(
            state="ok", projection="fresh", blocking=False
        ),
    )

    result = closure_gate.assess(
        tmp_path,
        work_id=unit_id,
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "block"
    assert result["reason"] == "repeated-failure-compound-required"
    assert result["repeat_failure"]["satisfied"] is False
    assert any(
        expected_finding in finding
        for finding in result["repeat_failure"]["findings"]
    )


@pytest.mark.parametrize(
    ("watch_format", "field", "order"),
    _DUPLICATE_WATCH_CASES,
)
def test_stop_gate_rejects_duplicate_accepted_watch_authority(
    tmp_path,
    monkeypatch,
    watch_format,
    field,
    order,
):
    unit_id = "UNIT-TASK-AR-645-001"
    signature = "duplicate accepted watch authority"
    suffix = "json" if watch_format == "json" else "md"
    watch_ref = f"reviews/REVIEW-{TODAY}-duplicate-watch.{suffix}"
    watch = tmp_path / watch_ref
    watch.parent.mkdir(parents=True, exist_ok=True)
    watch.write_text(
        _duplicate_accepted_watch_document(
            watch_format=watch_format,
            field=field,
            order=order,
            current_work_id=unit_id,
        ),
        encoding="utf-8",
    )
    record_path, _record = compound_record.create_record(
        tmp_path,
        work_ids=[unit_id],
        defect_signatures=[signature],
        title="Reject duplicate accepted watch authority",
        summary="An accepted watch must carry one authoritative value per field.",
        cause="Duplicate keys allowed parser-order authority overrides.",
        prevention="Reject duplicate accepted-watch authority keys.",
        source_refs=["reviews/source.md"],
        prevention_refs=[watch_ref],
        verification_refs=["reviews/VERIFY-unit.json"],
        created_at="2026-06-14T11:44:00+09:00",
    )
    _write_active_unit(
        tmp_path,
        compound_refs=[compound_record.record_ref(tmp_path, record_path)],
        signatures=[signature],
    )
    monkeypatch.setattr(
        closure_gate, "count_substantial_lines", lambda *args, **kwargs: 10
    )
    monkeypatch.setattr(
        closure_gate.state_projection,
        "evaluate_state",
        lambda _root: _scribe_evaluation(
            state="ok", projection="fresh", blocking=False
        ),
    )

    result = closure_gate.assess(
        tmp_path,
        work_id=unit_id,
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "block"
    assert result["reason"] == "repeated-failure-compound-required"
    assert result["repeat_failure"]["satisfied"] is False
    assert any(
        f"compound:prevention-watch-invalid:{watch_ref}" in finding
        for finding in result["repeat_failure"]["findings"]
    )


@pytest.mark.parametrize(
    ("field", "quote_style", "order", "value_mode"),
    _SEMANTIC_DUPLICATE_WATCH_CASES,
)
def test_stop_gate_rejects_semantic_duplicate_watch_authority(
    tmp_path,
    monkeypatch,
    field,
    quote_style,
    order,
    value_mode,
):
    unit_id = "UNIT-TASK-AR-645-001"
    signature = "semantic duplicate accepted watch authority"
    watch_ref = f"reviews/REVIEW-{TODAY}-semantic-duplicate-watch.md"
    watch = tmp_path / watch_ref
    watch.parent.mkdir(parents=True, exist_ok=True)
    watch.write_text(
        _semantic_duplicate_accepted_watch_document(
            field=field,
            quote_style=quote_style,
            order=order,
            value_mode=value_mode,
            current_work_id=unit_id,
        ),
        encoding="utf-8",
    )
    record_path, _record = compound_record.create_record(
        tmp_path,
        work_ids=[unit_id],
        defect_signatures=[signature],
        title="Reject semantic duplicate accepted watch authority",
        summary="YAML authority keys need one semantic representation.",
        cause="Raw key spelling diverged from YAML scalar identity.",
        prevention="Canonicalize keys before duplicate detection.",
        source_refs=["reviews/source.md"],
        prevention_refs=[watch_ref],
        verification_refs=["reviews/VERIFY-unit.json"],
        created_at="2026-06-14T11:46:00+09:00",
    )
    _write_active_unit(
        tmp_path,
        compound_refs=[compound_record.record_ref(tmp_path, record_path)],
        signatures=[signature],
    )
    monkeypatch.setattr(
        closure_gate, "count_substantial_lines", lambda *args, **kwargs: 10
    )
    monkeypatch.setattr(
        closure_gate.state_projection,
        "evaluate_state",
        lambda _root: _scribe_evaluation(
            state="ok", projection="fresh", blocking=False
        ),
    )

    result = closure_gate.assess(
        tmp_path,
        work_id=unit_id,
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "block"
    assert result["reason"] == "repeated-failure-compound-required"
    assert result["repeat_failure"]["satisfied"] is False
    assert any(
        f"compound:prevention-watch-invalid:{watch_ref}" in finding
        for finding in result["repeat_failure"]["findings"]
    )


@pytest.mark.parametrize(
    "quote_style",
    _SEMANTIC_WATCH_QUOTE_STYLES,
)
def test_stop_gate_accepts_single_semantic_quoted_watch_keys(
    tmp_path,
    monkeypatch,
    quote_style,
):
    unit_id = "UNIT-TASK-AR-645-001"
    signature = "valid quoted accepted watch authority"
    watch_ref = f"reviews/REVIEW-{TODAY}-valid-quoted-watch.md"
    watch = tmp_path / watch_ref
    watch.parent.mkdir(parents=True, exist_ok=True)
    watch.write_text(
        _quoted_accepted_watch_document(
            quote_style=quote_style,
            current_work_id=unit_id,
        ),
        encoding="utf-8",
    )
    record_path, _record = compound_record.create_record(
        tmp_path,
        work_ids=[unit_id],
        defect_signatures=[signature],
        title="Accept valid quoted watch authority",
        summary="A unique quoted YAML key remains a valid scalar key.",
        cause="Compatibility control for semantic key decoding.",
        prevention="Decode supported scalar key syntax before validation.",
        source_refs=["reviews/source.md"],
        prevention_refs=[watch_ref],
        verification_refs=["reviews/VERIFY-unit.json"],
        created_at="2026-06-14T11:47:00+09:00",
    )
    _write_active_unit(
        tmp_path,
        compound_refs=[compound_record.record_ref(tmp_path, record_path)],
        signatures=[signature],
    )
    monkeypatch.setattr(
        closure_gate, "count_substantial_lines", lambda *args, **kwargs: 10
    )
    monkeypatch.setattr(
        closure_gate.state_projection,
        "evaluate_state",
        lambda _root: _scribe_evaluation(
            state="ok", projection="fresh", blocking=False
        ),
    )

    result = closure_gate.assess(
        tmp_path,
        work_id=unit_id,
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "approve"
    assert result["reason"] == "repeated-failure-compound-present"
    assert result["repeat_failure"]["satisfied"] is True


@pytest.mark.parametrize("field", _SEMANTIC_WATCH_FIELDS)
@pytest.mark.parametrize("style", _SEMANTIC_SCALAR_INVALID_STYLES)
def test_stop_gate_rejects_invalid_semantic_watch_scalars(
    tmp_path,
    monkeypatch,
    field,
    style,
):
    unit_id = "UNIT-TASK-AR-645-001"
    signature = "invalid semantic accepted watch scalar"
    watch_ref = f"reviews/REVIEW-{TODAY}-invalid-semantic-scalar.md"
    watch = tmp_path / watch_ref
    watch.parent.mkdir(parents=True, exist_ok=True)
    watch.write_text(
        _semantic_scalar_accepted_watch_document(
            field=field,
            style=style,
            current_work_id=unit_id,
        ),
        encoding="utf-8",
    )
    record_path, _record = compound_record.create_record(
        tmp_path,
        work_ids=[unit_id],
        defect_signatures=[signature],
        title="Reject invalid semantic watch scalar",
        summary="Authority values need bounded scalar decoding.",
        cause="Quote characters were trimmed instead of decoded.",
        prevention="Decode one supported scalar representation.",
        source_refs=["reviews/source.md"],
        prevention_refs=[watch_ref],
        verification_refs=["reviews/VERIFY-unit.json"],
        created_at="2026-06-14T11:48:00+09:00",
    )
    _write_active_unit(
        tmp_path,
        compound_refs=[compound_record.record_ref(tmp_path, record_path)],
        signatures=[signature],
    )
    monkeypatch.setattr(
        closure_gate, "count_substantial_lines", lambda *args, **kwargs: 10
    )
    monkeypatch.setattr(
        closure_gate.state_projection,
        "evaluate_state",
        lambda _root: _scribe_evaluation(
            state="ok", projection="fresh", blocking=False
        ),
    )

    result = closure_gate.assess(
        tmp_path,
        work_id=unit_id,
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "block"
    assert result["reason"] == "repeated-failure-compound-required"
    assert result["repeat_failure"]["satisfied"] is False
    if style.startswith("mixed-"):
        assert any(
            f"compound:prevention-watch-invalid:{watch_ref}" in finding
            for finding in result["repeat_failure"]["findings"]
        )


@pytest.mark.parametrize("field", _SEMANTIC_WATCH_FIELDS)
@pytest.mark.parametrize("style", _SEMANTIC_SCALAR_VALID_STYLES)
def test_stop_gate_accepts_valid_semantic_watch_scalars(
    tmp_path,
    monkeypatch,
    field,
    style,
):
    unit_id = "UNIT-TASK-AR-645-001"
    signature = "valid semantic accepted watch scalar"
    watch_ref = f"reviews/REVIEW-{TODAY}-valid-semantic-scalar.md"
    watch = tmp_path / watch_ref
    watch.parent.mkdir(parents=True, exist_ok=True)
    watch.write_text(
        _semantic_scalar_accepted_watch_document(
            field=field,
            style=style,
            current_work_id=unit_id,
        ),
        encoding="utf-8",
    )
    record_path, _record = compound_record.create_record(
        tmp_path,
        work_ids=[unit_id],
        defect_signatures=[signature],
        title="Accept valid semantic watch scalar",
        summary="Supported scalar quoting preserves authority values.",
        cause="Compatibility control for bounded scalar decoding.",
        prevention="Decode paired and JSON-compatible quoted scalars.",
        source_refs=["reviews/source.md"],
        prevention_refs=[watch_ref],
        verification_refs=["reviews/VERIFY-unit.json"],
        created_at="2026-06-14T11:49:00+09:00",
    )
    _write_active_unit(
        tmp_path,
        compound_refs=[compound_record.record_ref(tmp_path, record_path)],
        signatures=[signature],
    )
    monkeypatch.setattr(
        closure_gate, "count_substantial_lines", lambda *args, **kwargs: 10
    )
    monkeypatch.setattr(
        closure_gate.state_projection,
        "evaluate_state",
        lambda _root: _scribe_evaluation(
            state="ok", projection="fresh", blocking=False
        ),
    )

    result = closure_gate.assess(
        tmp_path,
        work_id=unit_id,
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "approve"
    assert result["reason"] == "repeated-failure-compound-present"
    assert result["repeat_failure"]["satisfied"] is True


@pytest.mark.parametrize("fragment", _INDENTED_WATCH_FRAGMENTS)
def test_stop_gate_rejects_unexpected_watch_indentation(
    tmp_path,
    monkeypatch,
    fragment,
):
    unit_id = "UNIT-TASK-AR-645-001"
    signature = "unexpected accepted watch indentation"
    watch_ref = f"reviews/REVIEW-{TODAY}-unexpected-indentation.md"
    watch = tmp_path / watch_ref
    watch.parent.mkdir(parents=True, exist_ok=True)
    watch.write_text(
        _indented_accepted_watch_document(
            fragment=fragment,
            current_work_id=unit_id,
        ),
        encoding="utf-8",
    )
    record_path, _record = compound_record.create_record(
        tmp_path,
        work_ids=[unit_id],
        defect_signatures=[signature],
        title="Reject unexpected watch indentation",
        summary="Unsupported indentation must not be silently discarded.",
        cause="Non-list indented content was ignored.",
        prevention="Reject indented content outside an active list.",
        source_refs=["reviews/source.md"],
        prevention_refs=[watch_ref],
        verification_refs=["reviews/VERIFY-unit.json"],
        created_at="2026-06-14T11:50:00+09:00",
    )
    _write_active_unit(
        tmp_path,
        compound_refs=[compound_record.record_ref(tmp_path, record_path)],
        signatures=[signature],
    )
    monkeypatch.setattr(
        closure_gate, "count_substantial_lines", lambda *args, **kwargs: 10
    )
    monkeypatch.setattr(
        closure_gate.state_projection,
        "evaluate_state",
        lambda _root: _scribe_evaluation(
            state="ok", projection="fresh", blocking=False
        ),
    )

    result = closure_gate.assess(
        tmp_path,
        work_id=unit_id,
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "block"
    assert result["reason"] == "repeated-failure-compound-required"
    assert result["repeat_failure"]["satisfied"] is False
    assert any(
        f"compound:prevention-watch-invalid:{watch_ref}" in finding
        for finding in result["repeat_failure"]["findings"]
    )


@pytest.mark.parametrize("style", _NONCANONICAL_LIST_INDENT_STYLES)
def test_stop_gate_rejects_noncanonical_watch_list_indentation(
    tmp_path,
    monkeypatch,
    style,
):
    unit_id = "UNIT-TASK-AR-645-001"
    signature = "noncanonical accepted watch list indentation"
    watch_ref = f"reviews/REVIEW-{TODAY}-noncanonical-list-indent.md"
    watch = tmp_path / watch_ref
    watch.parent.mkdir(parents=True, exist_ok=True)
    watch.write_text(
        _noncanonical_work_ids_watch_document(
            style=style,
            current_work_id=unit_id,
        ),
        encoding="utf-8",
    )
    record_path, _record = compound_record.create_record(
        tmp_path,
        work_ids=[unit_id],
        defect_signatures=[signature],
        title="Reject noncanonical watch list indentation",
        summary="Authority list indentation must use one space-only depth.",
        cause="Broad whitespace trimming erased malformed indentation.",
        prevention="Reject tab-bearing and inconsistent list indentation.",
        source_refs=["reviews/source.md"],
        prevention_refs=[watch_ref],
        verification_refs=["reviews/VERIFY-unit.json"],
        created_at="2026-06-14T11:51:00+09:00",
    )
    _write_active_unit(
        tmp_path,
        compound_refs=[compound_record.record_ref(tmp_path, record_path)],
        signatures=[signature],
    )
    monkeypatch.setattr(
        closure_gate, "count_substantial_lines", lambda *args, **kwargs: 10
    )
    monkeypatch.setattr(
        closure_gate.state_projection,
        "evaluate_state",
        lambda _root: _scribe_evaluation(
            state="ok", projection="fresh", blocking=False
        ),
    )

    result = closure_gate.assess(
        tmp_path,
        work_id=unit_id,
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "block"
    assert result["reason"] == "repeated-failure-compound-required"
    assert result["repeat_failure"]["satisfied"] is False
    assert any(
        f"compound:prevention-watch-invalid:{watch_ref}" in finding
        for finding in result["repeat_failure"]["findings"]
    )


@pytest.mark.parametrize("field", _SEMANTIC_WATCH_FIELDS)
@pytest.mark.parametrize("position", _NBSP_AUTHORITY_POSITIONS)
def test_stop_gate_rejects_nbsp_watch_authority_separation(
    tmp_path,
    monkeypatch,
    field,
    position,
):
    unit_id = "UNIT-TASK-AR-645-001"
    signature = "nbsp accepted watch authority separation"
    watch_ref = f"reviews/REVIEW-{TODAY}-nbsp-authority.md"
    watch = tmp_path / watch_ref
    watch.parent.mkdir(parents=True, exist_ok=True)
    watch.write_text(
        _nbsp_accepted_watch_document(
            field=field,
            position=position,
            current_work_id=unit_id,
        ),
        encoding="utf-8",
    )
    record_path, _record = compound_record.create_record(
        tmp_path,
        work_ids=[unit_id],
        defect_signatures=[signature],
        title="Reject NBSP watch authority separation",
        summary="Only explicit ASCII YAML separation can grant authority.",
        cause="Unicode-wide trimming erased NBSP around authority tokens.",
        prevention="Preserve or reject non-ASCII separation before authority checks.",
        source_refs=["reviews/source.md"],
        prevention_refs=[watch_ref],
        verification_refs=["reviews/VERIFY-unit.json"],
        created_at="2026-06-14T11:52:00+09:00",
    )
    _write_active_unit(
        tmp_path,
        compound_refs=[compound_record.record_ref(tmp_path, record_path)],
        signatures=[signature],
    )
    monkeypatch.setattr(
        closure_gate, "count_substantial_lines", lambda *args, **kwargs: 10
    )
    monkeypatch.setattr(
        closure_gate.state_projection,
        "evaluate_state",
        lambda _root: _scribe_evaluation(
            state="ok", projection="fresh", blocking=False
        ),
    )

    result = closure_gate.assess(
        tmp_path,
        work_id=unit_id,
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "block"
    assert result["reason"] == "repeated-failure-compound-required"
    assert result["repeat_failure"]["satisfied"] is False


@pytest.mark.parametrize("style", _NONEXACT_MARKER_STYLES)
def test_stop_gate_rejects_nonexact_watch_frontmatter_markers(
    tmp_path,
    monkeypatch,
    style,
):
    unit_id = "UNIT-TASK-AR-645-001"
    signature = "nonexact accepted watch frontmatter marker"
    watch_ref = f"reviews/REVIEW-{TODAY}-nonexact-marker.md"
    watch = tmp_path / watch_ref
    watch.parent.mkdir(parents=True, exist_ok=True)
    watch.write_text(
        _nonexact_marker_watch_document(
            style=style,
            current_work_id=unit_id,
        ),
        encoding="utf-8",
    )
    record_path, _record = compound_record.create_record(
        tmp_path,
        work_ids=[unit_id],
        defect_signatures=[signature],
        title="Reject nonexact watch frontmatter marker",
        summary="Authority metadata requires exact frontmatter delimiters.",
        cause="Unicode-wide trimming treated padded delimiters as exact.",
        prevention="Require exact column-zero frontmatter delimiters.",
        source_refs=["reviews/source.md"],
        prevention_refs=[watch_ref],
        verification_refs=["reviews/VERIFY-unit.json"],
        created_at="2026-06-14T11:53:00+09:00",
    )
    _write_active_unit(
        tmp_path,
        compound_refs=[compound_record.record_ref(tmp_path, record_path)],
        signatures=[signature],
    )
    monkeypatch.setattr(
        closure_gate, "count_substantial_lines", lambda *args, **kwargs: 10
    )
    monkeypatch.setattr(
        closure_gate.state_projection,
        "evaluate_state",
        lambda _root: _scribe_evaluation(
            state="ok", projection="fresh", blocking=False
        ),
    )

    result = closure_gate.assess(
        tmp_path,
        work_id=unit_id,
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "block"
    assert result["reason"] == "repeated-failure-compound-required"
    assert result["repeat_failure"]["satisfied"] is False


@pytest.mark.parametrize("separator", _SPLITLINES_SEPARATORS)
@pytest.mark.parametrize("marker_position", _FRONTMATTER_MARKER_POSITIONS)
def test_stop_gate_rejects_splitlines_separator_markers(
    tmp_path,
    monkeypatch,
    separator,
    marker_position,
):
    unit_id = "UNIT-TASK-AR-645-001"
    signature = "splitlines separator accepted watch marker"
    watch_ref = f"reviews/REVIEW-{TODAY}-line-boundary-stop.md"
    watch = tmp_path / watch_ref
    watch.parent.mkdir(parents=True, exist_ok=True)
    watch.write_bytes(
        _line_boundary_accepted_watch_document(
            separator=separator,
            marker_position=marker_position,
            current_work_id=unit_id,
        ).encode("utf-8")
    )
    record_path, _record = compound_record.create_record(
        tmp_path,
        work_ids=[unit_id],
        defect_signatures=[signature],
        title="Reject splitlines separator watch marker",
        summary="Only LF and CRLF may delimit authority-bearing Markdown.",
        cause="Unicode-wide splitting erased a noncanonical line separator.",
        prevention="Reject noncanonical physical line boundaries before parsing.",
        source_refs=["reviews/source.md"],
        prevention_refs=[watch_ref],
        verification_refs=["reviews/VERIFY-unit.json"],
        created_at="2026-06-14T11:54:00+09:00",
    )
    _write_active_unit(
        tmp_path,
        compound_refs=[compound_record.record_ref(tmp_path, record_path)],
        signatures=[signature],
    )
    monkeypatch.setattr(
        closure_gate, "count_substantial_lines", lambda *args, **kwargs: 10
    )
    monkeypatch.setattr(
        closure_gate.state_projection,
        "evaluate_state",
        lambda _root: _scribe_evaluation(
            state="ok", projection="fresh", blocking=False
        ),
    )

    result = closure_gate.assess(
        tmp_path,
        work_id=unit_id,
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "block"
    assert result["reason"] == "repeated-failure-compound-required"
    assert result["repeat_failure"]["satisfied"] is False
    assert any(
        f"compound:prevention-watch-invalid:{watch_ref}" in finding
        for finding in result["repeat_failure"]["findings"]
    )


@pytest.mark.parametrize("watch_format", ("markdown", "json"))
def test_direct_repeat_requirement_bounds_malformed_utf8(
    tmp_path,
    watch_format,
):
    unit_id = "UNIT-TASK-AR-645-001"
    unit_id, watch_ref = _write_repeat_watch_context(
        tmp_path,
        watch_format=watch_format,
        raw_watch=(
            _accepted_watch_bytes(
                watch_format=watch_format,
                current_work_id=unit_id,
            )
            + b"\xff"
        ),
        signature="malformed utf8 accepted watch stop",
    )

    requirement = closure_gate.repeated_failure_requirement(
        tmp_path,
        closure_gate._active_work_contexts(tmp_path, work_id=unit_id),
    )
    result = closure_gate.decide(
        10,
        {"compound": True, "review": False, "retro": False},
        threshold=80,
        disabled=False,
        repeat_failure=requirement,
    )

    assert requirement["required"] is True
    assert requirement["satisfied"] is False
    assert any(
        f"compound:prevention-watch-invalid:{watch_ref}" in finding
        for finding in requirement["findings"]
    )
    assert result["decision"] == "block"
    assert result["reason"] == "repeated-failure-compound-required"


@pytest.mark.parametrize("watch_format", ("markdown", "json"))
def test_actual_stop_hook_blocks_malformed_utf8_watch(
    tmp_path,
    watch_format,
):
    unit_id = "UNIT-TASK-AR-645-001"
    _write_repeat_watch_context(
        tmp_path,
        watch_format=watch_format,
        raw_watch=(
            _accepted_watch_bytes(
                watch_format=watch_format,
                current_work_id=unit_id,
            )
            + b"\xff"
        ),
        signature="malformed utf8 accepted watch actual stop",
    )

    result = _run_actual_stop_hook(tmp_path)

    assert result.returncode == 0
    assert result.stderr == ""
    assert "Traceback" not in result.stdout
    payload = json.loads(result.stdout)
    assert payload["decision"] == "block"
    assert payload["reason"] == "repeated-failure-compound-required"
    assert len(result.stdout) < 4096


@pytest.mark.parametrize("watch_format", ("markdown", "json"))
@pytest.mark.parametrize(
    ("size", "expected_block"),
    (
        pytest.param(_ACCEPTED_WATCH_MAX_BYTES, False, id="exact-boundary"),
        pytest.param(_ACCEPTED_WATCH_MAX_BYTES + 1, True, id="over-boundary"),
    ),
)
def test_actual_stop_hook_enforces_raw_watch_size_bound(
    tmp_path,
    watch_format,
    size,
    expected_block,
):
    unit_id = "UNIT-TASK-AR-645-001"
    _write_repeat_watch_context(
        tmp_path,
        watch_format=watch_format,
        raw_watch=_accepted_watch_bytes(
            watch_format=watch_format,
            current_work_id=unit_id,
            size=size,
        ),
        signature="oversized accepted watch actual stop",
    )

    result = _run_actual_stop_hook(tmp_path)

    assert result.returncode == 0
    assert result.stderr == ""
    if expected_block:
        payload = json.loads(result.stdout)
        assert payload["decision"] == "block"
        assert payload["reason"] == "repeated-failure-compound-required"
    else:
        assert result.stdout == ""


@pytest.mark.parametrize("style", _LOSSY_AUTHORITY_STYLES)
@pytest.mark.parametrize("watch_format", ("markdown", "json"))
def test_stop_gate_rejects_lossy_watch_authority_normalization(
    tmp_path,
    monkeypatch,
    style,
    watch_format,
):
    unit_id = "UNIT-TASK-AR-645-001"
    signature = "lossy accepted watch authority normalization"
    suffix = "json" if watch_format == "json" else "md"
    watch_ref = f"reviews/REVIEW-{TODAY}-lossy-authority.{suffix}"
    watch = tmp_path / watch_ref
    watch.parent.mkdir(parents=True, exist_ok=True)
    watch.write_text(
        _lossy_accepted_watch_document(
            style=style,
            watch_format=watch_format,
            current_work_id=unit_id,
        ),
        encoding="utf-8",
    )
    record_path, _record = compound_record.create_record(
        tmp_path,
        work_ids=[unit_id],
        defect_signatures=[signature],
        title="Reject lossy watch authority normalization",
        summary="Decoded authority must already equal its canonical token.",
        cause="Whitespace and NFKC normalization widened authority semantics.",
        prevention="Compare decoded authority without lossy normalization.",
        source_refs=["reviews/source.md"],
        prevention_refs=[watch_ref],
        verification_refs=["reviews/VERIFY-unit.json"],
        created_at="2026-06-14T11:54:00+09:00",
    )
    _write_active_unit(
        tmp_path,
        compound_refs=[compound_record.record_ref(tmp_path, record_path)],
        signatures=[signature],
    )
    monkeypatch.setattr(
        closure_gate, "count_substantial_lines", lambda *args, **kwargs: 10
    )
    monkeypatch.setattr(
        closure_gate.state_projection,
        "evaluate_state",
        lambda _root: _scribe_evaluation(
            state="ok", projection="fresh", blocking=False
        ),
    )

    result = closure_gate.assess(
        tmp_path,
        work_id=unit_id,
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "block"
    assert result["reason"] == "repeated-failure-compound-required"
    assert result["repeat_failure"]["satisfied"] is False


def test_parent_repeated_failure_signal_is_inherited_by_stop_gate(
    tmp_path,
    monkeypatch,
):
    task = tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-645.md"
    task.parent.mkdir(parents=True, exist_ok=True)
    task.write_text(
        "---\n"
        "schema_version: agent-runtime-work-item/v1\n"
        "work_id: TASK-AR-645\n"
        "id: TASK-AR-645\n"
        "kind: task\n"
        "escalation_triggers:\n"
        "  - repeated_failure\n"
        "---\n\n# Parent task\n",
        encoding="utf-8",
    )
    _write_active_unit(tmp_path)
    monkeypatch.setattr(
        closure_gate, "count_substantial_lines", lambda *args, **kwargs: 10
    )
    monkeypatch.setattr(
        closure_gate.state_projection,
        "evaluate_state",
        lambda _root: _scribe_evaluation(
            state="ok", projection="fresh", blocking=False
        ),
    )

    result = closure_gate.assess(
        tmp_path,
        work_id="UNIT-TASK-AR-645-001",
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "block"
    assert "repeated_failure" in result["repeat_failure"]["escalation_triggers"]


def test_parent_compound_ref_satisfies_inherited_stop_requirement(
    tmp_path,
    monkeypatch,
):
    prevention = tmp_path / "scripts" / "repeat_gate.py"
    prevention.parent.mkdir(parents=True)
    prevention.write_text("raise SystemExit(0)\n", encoding="utf-8")
    record_path, _record = compound_record.create_record(
        tmp_path,
        work_ids=["TASK-AR-645"],
        defect_signatures=["parent repeat with prevention"],
        title="Prevent parent repeat",
        summary="The parent task owns the repeated-failure decision.",
        cause="The unit inherited a task-level repeat signal.",
        prevention="Run the executable repeated-failure gate.",
        source_refs=["reviews/source.md"],
        prevention_refs=["scripts/repeat_gate.py"],
        verification_refs=["reviews/VERIFY-task.json"],
        created_at="2026-06-14T11:45:00+09:00",
    )
    compound_ref = compound_record.record_ref(tmp_path, record_path)
    task = tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-645.md"
    task.parent.mkdir(parents=True, exist_ok=True)
    task.write_text(
        "---\n"
        "schema_version: agent-runtime-work-item/v1\n"
        "work_id: TASK-AR-645\n"
        "id: TASK-AR-645\n"
        "kind: task\n"
        "escalation_triggers:\n"
        "  - repeated_failure\n"
        "compound_refs:\n"
        f"  - {compound_ref}\n"
        "---\n\n# Parent task\n",
        encoding="utf-8",
    )
    _write_active_unit(tmp_path)
    monkeypatch.setattr(
        closure_gate, "count_substantial_lines", lambda *args, **kwargs: 10
    )
    monkeypatch.setattr(
        closure_gate.state_projection,
        "evaluate_state",
        lambda _root: _scribe_evaluation(
            state="ok", projection="fresh", blocking=False
        ),
    )

    result = closure_gate.assess(
        tmp_path,
        work_id="UNIT-TASK-AR-645-001",
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "approve"
    assert result["records"]["compound"] is True
    assert result["repeat_failure"]["valid_compound_refs"] == [compound_ref]


def test_multiple_active_claims_fail_closed_without_explicit_work_id(tmp_path):
    review_ref = f"reviews/REVIEW-{TODAY}-task-ar-645-closeout.md"
    review = tmp_path / review_ref
    review.parent.mkdir(parents=True)
    review.write_text(
        "---\nwork_id: UNIT-TASK-AR-645-001\n---\n\n# Linked review\n",
        encoding="utf-8",
    )
    _write_active_unit(tmp_path, review_refs=[review_ref])
    claims = tmp_path / "agents" / "runtime" / "task_claims"
    (claims / "CLAIM-other.json").write_text(
        json.dumps(
            {
                "schema": "agent-runtime-task-claim/v1",
                "claim_id": "CLAIM-other",
                "status": "claimed",
                "task_id": "TASK-AR-999",
                "unit_id": "UNIT-TASK-AR-999-001",
                "updated_at": "2026-06-14T11:30:00+09:00",
            }
        ),
        encoding="utf-8",
    )

    inferred = closure_gate.has_closure_record(tmp_path, now=NOW)
    explicit = closure_gate.has_closure_record(
        tmp_path, now=NOW, work_id="UNIT-TASK-AR-645-001"
    )

    assert inferred == {"compound": False, "review": False, "retro": False}
    assert explicit == {"compound": False, "review": True, "retro": False}


def _deep_accepted_watch_json(depth: int = 1200) -> bytes:
    return ("[" * depth + "0" + "]" * depth).encode("utf-8")


def test_direct_repeat_requirement_bounds_deep_json_recursion(tmp_path):
    unit_id, watch_ref = _write_repeat_watch_context(
        tmp_path,
        watch_format="json",
        raw_watch=_deep_accepted_watch_json(),
        signature="deep accepted watch JSON recursion direct stop",
    )

    requirement = closure_gate.repeated_failure_requirement(
        tmp_path,
        closure_gate._active_work_contexts(tmp_path, work_id=unit_id),
    )

    assert requirement["required"] is True
    assert requirement["satisfied"] is False
    assert any(
        f"compound:prevention-watch-invalid:{watch_ref}" in finding
        for finding in requirement["findings"]
    )


def test_actual_stop_hook_blocks_deep_json_recursion(tmp_path):
    _write_repeat_watch_context(
        tmp_path,
        watch_format="json",
        raw_watch=_deep_accepted_watch_json(),
        signature="deep accepted watch JSON recursion actual stop",
    )

    result = _run_actual_stop_hook(tmp_path)

    assert result.returncode == 0
    assert result.stderr == ""
    assert "Traceback" not in result.stdout
    payload = json.loads(result.stdout)
    assert payload["decision"] == "block"
    assert payload["reason"] == "repeated-failure-compound-required"


def test_missing_primary_relative_worktree_never_uses_linked_root_shadow(
    tmp_path,
    monkeypatch,
):
    primary = tmp_path / "primary"
    primary.mkdir()
    assert _git(primary, "init").returncode == 0
    assert _git(primary, "config", "user.email", "test@example.invalid").returncode == 0
    assert _git(primary, "config", "user.name", "Test User").returncode == 0
    (primary / "seed.txt").write_text("seed\n", encoding="utf-8")
    assert _git(primary, "add", "seed.txt").returncode == 0
    assert _git(primary, "commit", "-m", "seed").returncode == 0

    local_worktree = primary / ".worktrees" / "TASK-AR-645"
    assert _git(
        primary,
        "worktree",
        "add",
        "-b",
        "test/missing-primary-relative",
        str(local_worktree),
        "HEAD",
    ).returncode == 0
    _write_active_unit(local_worktree)
    _write_canonical_active_claim(
        local_worktree,
        claim_id="CLAIM-shadow-relative",
        worktree_path=".worktrees/TASK-AR-MISSING",
        defect_signatures=[_CLAIM_ONLY_SIGNATURE],
        escalation_triggers=["repeated_failure"],
    )
    shadow = local_worktree / ".worktrees" / "TASK-AR-MISSING"
    shadow.parent.mkdir(parents=True)
    shadow.symlink_to(local_worktree, target_is_directory=True)
    assert not (primary / ".worktrees" / "TASK-AR-MISSING").exists()
    assert shadow.resolve() == local_worktree.resolve()
    monkeypatch.chdir(local_worktree)

    resolution = closure_gate.resolve_active_work_contexts(local_worktree)

    assert resolution["reason"] is None
    assert [context["kind"] for context in resolution["contexts"]] == ["unit"]
    assert all(
        _CLAIM_ONLY_SIGNATURE not in context["defect_signatures"]
        for context in resolution["contexts"]
    )
    assert resolution["selected_claim_ids"] == ["CLAIM-active"]
    assert "CLAIM-shadow-relative" not in resolution["selected_claim_ids"]


# --- substantial line counting via git ---

def _git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


@pytest.fixture
def git_repo(tmp_path):
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "t@e.com")
    _git(tmp_path, "config", "user.name", "T")
    _git(tmp_path, "config", "commit.gpgsign", "false")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "seed.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-m", "seed")
    return tmp_path


@pytest.mark.skipif(__import__("shutil").which("git") is None, reason="git not available")
def test_count_substantial_lines_counts_code_churn(git_repo):
    # a sizeable code commit
    (git_repo / "src" / "feature.py").write_text("\n".join(f"line{i} = {i}" for i in range(120)) + "\n", encoding="utf-8")
    _git(git_repo, "add", "-A")
    _git(git_repo, "commit", "-m", "feat: big")
    n = closure_gate.count_substantial_lines(git_repo, now=NOW, window_hours=24)
    assert n >= 120


@pytest.mark.skipif(__import__("shutil").which("git") is None, reason="git not available")
def test_count_substantial_lines_counts_uncommitted(git_repo):
    (git_repo / "scripts").mkdir()
    (git_repo / "scripts" / "wip.py").write_text("\n".join(f"a{i}=1" for i in range(90)) + "\n", encoding="utf-8")
    n = closure_gate.count_substantial_lines(git_repo, now=NOW, window_hours=24)
    assert n >= 90


# --- stop hook wrapper ---

def test_stop_hook_blocks_substantial_without_record(tmp_path, monkeypatch, capsys):
    _write_direct_runtime(tmp_path)
    monkeypatch.setattr(closure_gate, "count_substantial_lines", lambda *a, **k: 300)
    monkeypatch.setattr(closure_gate, "has_closure_record",
                        lambda *a, **k: {"compound": False, "review": False, "retro": False})
    monkeypatch.setattr(stop_hook_closure_gate.Path, "cwd", staticmethod(lambda: tmp_path))
    rc = stop_hook_closure_gate.main([])
    assert rc == 0
    import json
    out = json.loads(capsys.readouterr().out)
    assert out["decision"] == "block"
    assert out["systemMessage"]


def test_stop_hook_fails_closed_on_unexpected_gate_error(monkeypatch, capsys):
    monkeypatch.setattr(closure_gate, "assess", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    rc = stop_hook_closure_gate.main([])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["decision"] == "block"
    assert payload["reason"] == "closure-gate-error"
    assert payload["systemMessage"] == (
        "Closure validation failed unexpectedly. Repair or explicitly bypass "
        "the gate before stopping."
    )


def test_stop_hook_disabled_env_approves(tmp_path, monkeypatch, capsys):
    _write_direct_runtime(tmp_path)
    monkeypatch.setenv("AGENT_RUNTIME_CLOSURE_GATE_DISABLE", "1")
    monkeypatch.setattr(stop_hook_closure_gate.Path, "cwd", staticmethod(lambda: tmp_path))
    rc = stop_hook_closure_gate.main([])
    assert rc == 0
    assert capsys.readouterr().out == ""
