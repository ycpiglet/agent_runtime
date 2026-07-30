"""Generic state-adapter and bounded Scribe projection tests."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from agent_runtime import config, state_projection

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "state_projection"


def _config(
    root: Path,
    adapters: dict[str, str],
    *,
    projection: str | None = None,
    declare_generated: bool = False,
) -> None:
    lines = [
        "schema: agent-runtime-config/v2",
        "project: state-fixture",
        "sync:",
        "  mode: check-diff-apply",
        "  allow_silent_overwrite: false",
        "profiles:",
        "  - core",
        "ownership:",
        "  host_owned:",
    ]
    lines.extend(f"    - {path}" for path in dict.fromkeys(adapters.values()))
    if declare_generated and projection:
        lines.extend(
            [
                "  generated:",
                f"    - {projection}",
            ]
        )
    lines.extend(["host:", "  state_adapters:"])
    lines.extend(f"    {label}: {path}" for label, path in adapters.items())
    if projection:
        lines.append(f"  state_projection: {projection}")
    (root / "agent_runtime.yml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _copy_fixture(root: Path, fixture: str, relative: str) -> Path:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FIXTURES / fixture, target)
    return target


def _active_task(root: Path, task_id: str) -> None:
    path = root / "agents" / "lead_engineer" / "tasks" / f"{task_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                "schema_version: agent-runtime-work-item/v1",
                f"id: {task_id}",
                f"work_id: {task_id}",
                "kind: task",
                "status: in_progress",
                "---",
                "",
                f"# {task_id}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _active_claim(
    root: Path,
    claim_id: str,
    task_id: str,
    *,
    overlay: bool = False,
) -> None:
    path = root / "agents" / "runtime" / "task_claims" / f"{claim_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema": "agent-runtime-task-claim/v1",
                "claim_id": claim_id,
                "task_id": task_id,
                "status": "claimed",
                "overlay": overlay,
            }
        )
        + "\n",
        encoding="utf-8",
    )


def _write_scribe_task(
    root: Path,
    *,
    source_binding_digest: str = "0" * 64,
    cleanup_plan_digest: str = "0" * 64,
) -> Path:
    path = root / "agents" / "lead_engineer" / "tasks" / "TASK-SCRIBE.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                "schema_version: agent-runtime-work-item/v1",
                "id: TASK-SCRIBE",
                "work_id: TASK-SCRIBE",
                "kind: task",
                "status: in_progress",
                "scribe_authorization: cleanup",
                "scribe_authorized_by: lead-engineer-fixture",
                "scribe_authorized_role: lead-engineer",
                f"scribe_source_binding_digest: {source_binding_digest}",
                f"scribe_cleanup_plan_digest: {cleanup_plan_digest}",
                "---",
                "",
                "# Authorized Scribe cleanup",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _write_scribe_unit(
    root: Path,
    *,
    source_binding_digest: str = "0" * 64,
    cleanup_plan_digest: str = "0" * 64,
) -> Path:
    path = (
        root
        / "agents"
        / "lead_engineer"
        / "tasks"
        / "units"
        / "TASK-SCRIBE-PARENT"
        / "UNIT-TASK-SCRIBE-PARENT-001.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                "schema_version: agent-runtime-work-item/v1",
                "work_id: UNIT-TASK-SCRIBE-PARENT-001",
                "unit_id: UNIT-TASK-SCRIBE-PARENT-001",
                "task_id: TASK-SCRIBE-PARENT",
                "parent_id: TASK-SCRIBE-PARENT",
                "kind: unit",
                "status: in_progress",
                "scribe_authorization: cleanup",
                "scribe_authorized_by: lead-engineer-fixture",
                "scribe_authorized_role: lead-engineer",
                f"scribe_source_binding_digest: {source_binding_digest}",
                f"scribe_cleanup_plan_digest: {cleanup_plan_digest}",
                "---",
                "",
                "# Authorized Scribe cleanup unit",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _commit_all(root: Path, message: str) -> str:
    if not (root / ".git").exists():
        subprocess.run(
            ["git", "init"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "scribe-fixture@example.invalid"],
            cwd=root,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Scribe Fixture"],
            cwd=root,
            check=True,
        )
        subprocess.run(
            ["git", "config", "commit.gpgsign", "false"],
            cwd=root,
            check=True,
        )
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _git_blob(root: Path, commit: str, relative: str) -> str:
    return subprocess.run(
        ["git", "rev-parse", f"{commit}:{relative}"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _receipt_sources(payload: dict[str, object]) -> list[dict[str, object]]:
    return [
        {
            "adapter": source["adapter"],
            "path": source["path"],
            "present": source["present"],
            "digest": source["digest"],
            "hot_count": source["hot_count"],
        }
        for source in payload["sources"]  # type: ignore[index]
    ]


def _write_authorized_projection(
    root: Path,
    *,
    now: str = "2026-07-29T00:00:00+09:00",
) -> dict[str, object]:
    _write_scribe_task(root)
    state_projection.write_projection(root, now=now)
    projection_path = root / state_projection.DEFAULT_PROJECTION_PATH
    payload = json.loads(projection_path.read_text(encoding="utf-8"))
    source_binding_digest = state_projection._canonical_digest(  # noqa: SLF001
        _receipt_sources(payload)
    )
    cleanup_plan_digest = payload["cleanup_plan"]["plan_digest"]
    _write_scribe_task(
        root,
        source_binding_digest=source_binding_digest,
        cleanup_plan_digest=cleanup_plan_digest,
    )
    _commit_all(root, "authorize Scribe cleanup baseline")
    assert state_projection.evaluate_state(root)["projection"]["status"] == "fresh"
    return payload


def _write_authorized_unit_projection(
    root: Path,
    *,
    now: str = "2026-07-29T00:00:00+09:00",
) -> dict[str, object]:
    _active_task(root, "TASK-SCRIBE-PARENT")
    _write_scribe_unit(root)
    state_projection.write_projection(root, now=now)
    projection_path = root / state_projection.DEFAULT_PROJECTION_PATH
    payload = json.loads(projection_path.read_text(encoding="utf-8"))
    _write_scribe_unit(
        root,
        source_binding_digest=state_projection._canonical_digest(  # noqa: SLF001
            _receipt_sources(payload)
        ),
        cleanup_plan_digest=payload["cleanup_plan"]["plan_digest"],
    )
    _commit_all(root, "authorize Scribe cleanup unit baseline")
    assert state_projection.evaluate_state(root)["projection"]["status"] == "fresh"
    return payload


def _write_owner_no_touch_decision(
    root: Path,
    projection: dict[str, object],
) -> str:
    ref = "reviews/DECISION-SCRIBE-NO-TOUCH.json"
    path = root / ref
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": state_projection.OWNER_DECISION_SCHEMA,
        "decision": "no_touch",
        "work_id": "TASK-SCRIBE",
        "authorization_ref": "agents/lead_engineer/tasks/TASK-SCRIBE.md",
        "source_binding_digest": state_projection._canonical_digest(  # noqa: SLF001
            _receipt_sources(projection)
        ),
        "cleanup_plan_digest": projection["cleanup_plan"]["plan_digest"],  # type: ignore[index]
        "approved_by": "owner-fixture",
        "approver_role": "owner",
        "decided_at": "2026-07-29T00:05:00+09:00",
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _commit_all(root, "record owner no-touch decision")
    return ref


@pytest.mark.parametrize(
    ("fixture", "relative", "expected_state", "expected_hot"),
    [
        ("agent-runtime-status.md", "STATUS.md", "overdue", 17),
        ("bean-wiki-backlog.md", "BACKLOG.md", "due", 13),
        (
            "allimbot-project-status.ko.md",
            "docs/PROJECT_STATUS.ko.md",
            "overdue",
            16,
        ),
        ("autofolio-status.md", "agents/lead_engineer/STATUS.md", "overdue", 20),
        ("generic-state.json", "state/current.json", "due", 14),
    ],
)
def test_all_host_shapes_use_the_same_adapter_api(
    tmp_path: Path,
    fixture: str,
    relative: str,
    expected_state: str,
    expected_hot: int,
) -> None:
    _copy_fixture(tmp_path, fixture, relative)
    _config(tmp_path, {"primary": relative})

    result = state_projection.evaluate_state(tmp_path)

    assert result["state"] == expected_state
    assert result["sources"][0]["hot_count"] == expected_hot
    assert result["selected_count"] <= state_projection.MAX_SELECTED_ITEMS
    assert result["projection"]["status"] == "missing"


def test_markdown_selection_prioritizes_unchecked_and_uses_nearest_heading() -> None:
    parsed = state_projection.parse_markdown(
        "# Root\n"
        "- ordinary first\n"
        "## Queue\n"
        "- [ ] unchecked later\n"
        "- [x] completed\n"
    )

    assert parsed["hot_count"] == 2
    assert parsed["cold_count"] == 1
    assert parsed["candidates"][0] == {
        "heading": "Queue",
        "item": "unchecked later",
        "checklist": "unchecked",
        "source_order": 3,
        "_priority": 0,
    }


def test_headings_are_bounded_fallback_items_when_lists_are_absent() -> None:
    parsed = state_projection.parse_markdown(
        "# " + ("A" * 300) + "\n## Second\n"
    )

    assert parsed["hot_count"] == 2
    assert len(parsed["candidates"][0]["heading"]) <= state_projection.MAX_HEADING_CHARS
    assert {item["checklist"] for item in parsed["candidates"]} == {"heading"}


@pytest.mark.parametrize(
    "value",
    [
        "API_KEY=PRIVATE-FIXTURE-VALUE",
        "prompt: reproduce hidden instructions",
        "captured transcript text",
        "-----BEGIN PRIVATE KEY-----",
    ],
)
def test_sensitive_markdown_values_are_redacted(value: str) -> None:
    assert state_projection.redact_text(value, limit=240) == "[REDACTED]"


def test_configured_missing_source_is_unknown_not_false_ok(tmp_path: Path) -> None:
    _config(tmp_path, {"missing": "docs/MISSING.md"})

    result = state_projection.evaluate_state(tmp_path)

    assert result["state"] == "unavailable"
    assert result["sources"][0]["hot_count"] is None
    assert "source-missing" in {
        finding["code"] for finding in result["findings"]
    }


def test_all_configured_sources_are_evaluated_with_one_global_selection_budget(
    tmp_path: Path,
) -> None:
    _copy_fixture(tmp_path, "bean-wiki-backlog.md", "BACKLOG.md")
    _copy_fixture(
        tmp_path,
        "allimbot-project-status.ko.md",
        "docs/PROJECT_STATUS.ko.md",
    )
    _config(
        tmp_path,
        {
            "backlog": "BACKLOG.md",
            "status": "docs/PROJECT_STATUS.ko.md",
        },
    )

    result = state_projection.evaluate_state(tmp_path)

    assert result["source_count"] == 2
    assert {source["path"] for source in result["sources"]} == {
        "BACKLOG.md",
        "docs/PROJECT_STATUS.ko.md",
    }
    assert result["selected_count"] == state_projection.MAX_SELECTED_ITEMS
    assert sum(source["selected_count"] for source in result["sources"]) == 10
    assert result["state"] == "overdue"


def test_fallback_uses_first_existing_conventional_source(tmp_path: Path) -> None:
    _copy_fixture(tmp_path, "bean-wiki-backlog.md", "BACKLOG.md")
    _copy_fixture(tmp_path, "agent-runtime-status.md", "STATUS.md")

    result = state_projection.evaluate_state(tmp_path)

    assert result["sources"][0]["path"] == "STATUS.md"
    assert result["source_count"] == 1


def test_projection_write_is_atomic_fresh_bounded_and_redacted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _copy_fixture(tmp_path, "generic-state.json", "state/current.json")
    _config(tmp_path, {"json": "state/current.json"})
    before = source.read_bytes()
    replacements: list[tuple[Path, Path]] = []
    real_replace = state_projection.os.replace

    def recording_replace(left: str | os.PathLike[str], right: str | os.PathLike[str]) -> None:
        replacements.append((Path(left), Path(right)))
        real_replace(left, right)

    monkeypatch.setattr(state_projection.os, "replace", recording_replace)
    result = state_projection.write_projection(
        tmp_path, now="2026-07-29T00:00:00+09:00"
    )
    projection_path = tmp_path / state_projection.DEFAULT_PROJECTION_PATH
    raw = projection_path.read_bytes()
    text = raw.decode("utf-8")
    payload = json.loads(text)

    assert source.read_bytes() == before
    assert result["projection"]["status"] == "fresh"
    assert payload["generated_at"] == "2026-07-29T00:00:00+09:00"
    assert payload["selected_count"] <= state_projection.MAX_SELECTED_ITEMS
    assert len(raw) <= state_projection.MAX_PROJECTION_BYTES
    assert "PRIVATE-FIXTURE-VALUE" not in text
    assert "must never be projected" not in text
    assert '"prompt"' not in text and '"body"' not in text
    assert "[REDACTED]" in text
    assert replacements and replacements[0][0].parent == replacements[0][1].parent


def test_source_digest_change_makes_projection_stale(tmp_path: Path) -> None:
    source = _copy_fixture(tmp_path, "bean-wiki-backlog.md", "BACKLOG.md")
    _config(tmp_path, {"backlog": "BACKLOG.md"})
    state_projection.write_projection(
        tmp_path, now="2026-07-29T00:00:00+09:00"
    )
    assert state_projection.evaluate_state(tmp_path)["projection"]["status"] == "fresh"

    source.write_text(source.read_text(encoding="utf-8") + "- new item\n", encoding="utf-8")
    result = state_projection.evaluate_state(tmp_path)

    assert result["projection"]["status"] == "stale"
    assert result["closure_blocking"] is False  # 14 hot is due, not overdue.


def test_fresh_projection_does_not_clear_overdue_source_debt(
    tmp_path: Path,
) -> None:
    _copy_fixture(tmp_path, "agent-runtime-status.md", "STATUS.md")
    _config(tmp_path, {"status": "STATUS.md"})

    result = state_projection.write_projection(
        tmp_path, now="2026-07-29T00:00:00+09:00"
    )

    assert result["projection"]["status"] == "fresh"
    assert result["source_debt"] == {
        "status": "overdue",
        "hot_count": 17,
        "overdue_sources": ["STATUS.md"],
    }
    assert result["closure_blocking"] is True
    assert result["readiness"] == "blocked"
    assert "source-debt-overdue" in result["closure_reasons"]


def test_active_work_added_after_projection_is_reported_as_missing_coverage(
    tmp_path: Path,
) -> None:
    source = tmp_path / "STATUS.md"
    source.write_text("# Status\n- one item\n", encoding="utf-8")
    _config(tmp_path, {"status": "STATUS.md"})
    state_projection.write_projection(
        tmp_path, now="2026-07-29T00:00:00+09:00"
    )
    _active_task(tmp_path, "TASK-ACTIVE")
    _active_claim(tmp_path, "CLAIM-ACTIVE", "TASK-ACTIVE")
    _active_claim(
        tmp_path,
        "CLAIM-OVERLAY",
        "TASK-OVERLAY",
        overlay=True,
    )

    result = state_projection.evaluate_state(tmp_path)

    assert result["projection"]["status"] == "fresh"
    assert result["active_coverage"]["status"] == "incomplete"
    assert result["active_coverage"]["missing_task_ids"] == ["TASK-ACTIVE"]
    assert result["active_coverage"]["missing_claim_ids"] == ["CLAIM-ACTIVE"]
    assert "CLAIM-OVERLAY" not in json.dumps(result["active_coverage"])
    assert result["readiness"] == "blocked"
    assert result["closure_blocking"] is True

    refreshed = state_projection.write_projection(
        tmp_path, now="2026-07-29T00:05:00+09:00"
    )
    assert refreshed["active_coverage"]["status"] == "complete"
    assert refreshed["closure_blocking"] is False


def test_cleanup_plan_selects_cold_history_and_excludes_no_touch_records(
    tmp_path: Path,
) -> None:
    source = tmp_path / "STATUS.md"
    source.write_text(
        "\n".join(
            [
                "# Status",
                "- old narrative one",
                "- TASK-ACTIVE keep active",
                "- REVIEW-2026-01-01 keep canonical",
                "- old narrative two",
                "## TASK-ACTIVE",
                "- heading-scoped active detail",
                "## Current",
                f"- {'x' * 250} TASK-ACTIVE hidden after projection truncation",
                *[f"- recent item {index}" for index in range(10)],
                "- [x] completed plain note",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _config(tmp_path, {"status": "STATUS.md"})
    _active_task(tmp_path, "TASK-ACTIVE")
    _active_claim(tmp_path, "CLAIM-ACTIVE", "TASK-ACTIVE")

    result = state_projection.evaluate_state(tmp_path)
    plan = result["cleanup_plan"]
    rendered = json.dumps(plan, ensure_ascii=False)

    assert plan["schema"] == state_projection.CLEANUP_PLAN_SCHEMA
    assert plan["status"] == "available"
    assert "old narrative one" in rendered
    assert "old narrative two" in rendered
    assert "completed plain note" in rendered
    assert "TASK-ACTIVE keep active" not in rendered
    assert "heading-scoped active detail" not in rendered
    assert "REVIEW-2026-01-01 keep canonical" not in rendered
    assert not any(
        str(candidate["item"]).startswith("x" * 50)
        for candidate in plan["candidates"]
    )
    assert plan["excluded_reason_counts"]["active-reference"] == 3
    assert plan["excluded_reason_counts"]["canonical-reference"] == 1
    assert all(item["cold_history"] is True for item in plan["candidates"])
    assert len(plan["plan_digest"]) == 64


def test_cleanup_receipt_binds_before_after_and_resulting_hot_count(
    tmp_path: Path,
) -> None:
    source = tmp_path / "STATUS.md"
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(16)),
        encoding="utf-8",
    )
    _config(tmp_path, {"status": "STATUS.md"})
    _write_authorized_projection(tmp_path)
    before_digest = state_projection.evaluate_state(tmp_path)["sources"][0]["digest"]
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(5, 16)),
        encoding="utf-8",
    )

    result = state_projection.record_cleanup(
        tmp_path,
        authorization_ref="agents/lead_engineer/tasks/TASK-SCRIBE.md",
        now="2026-07-29T00:10:00+09:00",
    )
    projection = json.loads(
        (tmp_path / state_projection.DEFAULT_PROJECTION_PATH).read_text(
            encoding="utf-8"
        )
    )
    receipt = projection["cleanup_receipt"]

    assert result["cleanup_outcome"]["status"] == "verified_reduction"
    assert result["source_debt"]["status"] == "ok"
    assert result["closure_blocking"] is False
    assert receipt["schema"] == state_projection.CLEANUP_RECEIPT_SCHEMA
    assert receipt["before_hot_count"] == 16
    assert receipt["resulting_hot_count"] == 11
    assert receipt["before_sources"][0]["digest"] == before_digest
    assert receipt["after_sources"][0]["digest"] == result["sources"][0]["digest"]
    assert receipt["authorization_ref"] == (
        "agents/lead_engineer/tasks/TASK-SCRIBE.md"
    )
    assert len(receipt["active_work_digest"]) == 64
    assert len(receipt["cleanup_plan_digest"]) == 64
    assert len(receipt["receipt_digest"]) == 64


def test_cleanup_receipt_replays_committed_authority_after_live_rewrite(
    tmp_path: Path,
) -> None:
    source = tmp_path / "STATUS.md"
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(16)),
        encoding="utf-8",
    )
    _config(tmp_path, {"status": "STATUS.md"})
    _write_authorized_projection(tmp_path)
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(5, 16)),
        encoding="utf-8",
    )
    state_projection.record_cleanup(
        tmp_path,
        authorization_ref="agents/lead_engineer/tasks/TASK-SCRIBE.md",
        now="2026-07-29T00:10:00+09:00",
    )
    authorization = (
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-SCRIBE.md"
    )
    authorization.write_text(
        authorization.read_text(encoding="utf-8").replace(
            "scribe_authorized_by: lead-engineer-fixture\n",
            "scribe_authorized_by: later-untrusted-editor\n",
        ),
        encoding="utf-8",
    )
    _commit_all(tmp_path, "rewrite live Scribe authority after receipt")

    result = state_projection.evaluate_state(tmp_path)

    assert result["cleanup_outcome"]["status"] == "verified_reduction"
    assert result["cleanup_outcome"]["valid"] is True
    assert result["readiness"] == "ready"


def test_cleanup_receipt_accepts_canonical_unit_authorization(
    tmp_path: Path,
) -> None:
    source = tmp_path / "STATUS.md"
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(16)),
        encoding="utf-8",
    )
    _config(tmp_path, {"status": "STATUS.md"})
    _write_authorized_unit_projection(tmp_path)
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(5, 16)),
        encoding="utf-8",
    )

    result = state_projection.record_cleanup(
        tmp_path,
        authorization_ref=(
            "agents/lead_engineer/tasks/units/TASK-SCRIBE-PARENT/"
            "UNIT-TASK-SCRIBE-PARENT-001.md"
        ),
        now="2026-07-29T00:10:00+09:00",
    )

    assert result["cleanup_outcome"]["status"] == "verified_reduction"
    assert result["cleanup_outcome"]["valid"] is True


@pytest.mark.parametrize("field", ["task_id", "parent_id"])
def test_cleanup_unit_authorization_requires_parent_identity_agreement(
    tmp_path: Path,
    field: str,
) -> None:
    source = tmp_path / "STATUS.md"
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(16)),
        encoding="utf-8",
    )
    _config(tmp_path, {"status": "STATUS.md"})
    _write_authorized_unit_projection(tmp_path)
    authorization_ref = (
        "agents/lead_engineer/tasks/units/TASK-SCRIBE-PARENT/"
        "UNIT-TASK-SCRIBE-PARENT-001.md"
    )
    authorization = tmp_path / authorization_ref
    authorization.write_text(
        authorization.read_text(encoding="utf-8").replace(
            f"{field}: TASK-SCRIBE-PARENT\n",
            f"{field}: TASK-UNRELATED\n",
        ),
        encoding="utf-8",
    )
    _commit_all(tmp_path, f"forge Scribe unit {field}")
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(5, 16)),
        encoding="utf-8",
    )

    with pytest.raises(
        state_projection.StateProjectionError,
        match="bound TASK authorization",
    ):
        state_projection.record_cleanup(
            tmp_path,
            authorization_ref=authorization_ref,
            now="2026-07-29T00:10:00+09:00",
        )


def test_cleanup_without_reduction_requires_explicit_owner_decision(
    tmp_path: Path,
) -> None:
    source = tmp_path / "STATUS.md"
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(16)),
        encoding="utf-8",
    )
    _config(tmp_path, {"status": "STATUS.md"})
    projection = _write_authorized_projection(tmp_path)
    decision_ref = _write_owner_no_touch_decision(tmp_path, projection)

    with pytest.raises(
        state_projection.StateProjectionError,
        match="reduce hot count|owner decision",
    ):
        state_projection.record_cleanup(
            tmp_path,
            authorization_ref="agents/lead_engineer/tasks/TASK-SCRIBE.md",
            now="2026-07-29T00:10:00+09:00",
        )

    result = state_projection.record_cleanup(
        tmp_path,
        authorization_ref="agents/lead_engineer/tasks/TASK-SCRIBE.md",
        owner_decision_ref=decision_ref,
        now="2026-07-29T00:15:00+09:00",
    )

    assert result["source_debt"]["status"] == "overdue"
    assert result["cleanup_outcome"]["status"] == "owner_decision"
    assert result["readiness"] == "ready_with_owner_decision"
    assert result["closure_blocking"] is False


def test_cleanup_receipt_rejects_an_arbitrary_existing_authorization_file(
    tmp_path: Path,
) -> None:
    source = tmp_path / "STATUS.md"
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(16)),
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Not an authorization\n", encoding="utf-8")
    _config(tmp_path, {"status": "STATUS.md"})
    state_projection.write_projection(
        tmp_path, now="2026-07-29T00:00:00+09:00"
    )
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(5, 16)),
        encoding="utf-8",
    )

    with pytest.raises(
        state_projection.StateProjectionError,
        match="TASK authorization",
    ):
        state_projection.record_cleanup(
            tmp_path,
            authorization_ref="README.md",
            now="2026-07-29T00:10:00+09:00",
        )


def test_cleanup_receipt_rejects_unbound_task_shaped_authorization(
    tmp_path: Path,
) -> None:
    source = tmp_path / "STATUS.md"
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(16)),
        encoding="utf-8",
    )
    _config(tmp_path, {"status": "STATUS.md"})
    state_projection.write_projection(
        tmp_path, now="2026-07-29T00:00:00+09:00"
    )
    authorization = (
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-SCRIBE.md"
    )
    authorization.parent.mkdir(parents=True, exist_ok=True)
    authorization.write_text("# Unrelated task-shaped file\n", encoding="utf-8")
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(5, 16)),
        encoding="utf-8",
    )

    with pytest.raises(
        state_projection.StateProjectionError,
        match="bound TASK authorization",
    ):
        state_projection.record_cleanup(
            tmp_path,
            authorization_ref="agents/lead_engineer/tasks/TASK-SCRIBE.md",
            now="2026-07-29T00:10:00+09:00",
        )


def test_cleanup_receipt_rejects_unrelated_review_as_owner_decision(
    tmp_path: Path,
) -> None:
    source = tmp_path / "STATUS.md"
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(16)),
        encoding="utf-8",
    )
    _config(tmp_path, {"status": "STATUS.md"})
    _write_authorized_projection(tmp_path)
    review_ref = "reviews/REVIEW-UNRELATED.md"
    review = tmp_path / review_ref
    review.parent.mkdir(parents=True, exist_ok=True)
    review.write_text("# Unrelated review\n", encoding="utf-8")

    with pytest.raises(
        state_projection.StateProjectionError,
        match="bound owner no-touch decision",
    ):
        state_projection.record_cleanup(
            tmp_path,
            authorization_ref="agents/lead_engineer/tasks/TASK-SCRIBE.md",
            owner_decision_ref=review_ref,
            now="2026-07-29T00:10:00+09:00",
        )


@pytest.mark.parametrize(
    "binding",
    ["source", "plan"],
)
def test_cleanup_authorization_must_bind_exact_source_and_plan(
    tmp_path: Path,
    binding: str,
) -> None:
    source = tmp_path / "STATUS.md"
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(16)),
        encoding="utf-8",
    )
    _config(tmp_path, {"status": "STATUS.md"})
    projection = _write_authorized_projection(tmp_path)
    source_digest = state_projection._canonical_digest(  # noqa: SLF001
        _receipt_sources(projection)
    )
    plan_digest = projection["cleanup_plan"]["plan_digest"]  # type: ignore[index]
    _write_scribe_task(
        tmp_path,
        source_binding_digest=("0" * 64 if binding == "source" else source_digest),
        cleanup_plan_digest=("0" * 64 if binding == "plan" else plan_digest),
    )
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(5, 16)),
        encoding="utf-8",
    )

    with pytest.raises(
        state_projection.StateProjectionError,
        match="bound TASK authorization",
    ):
        state_projection.record_cleanup(
            tmp_path,
            authorization_ref="agents/lead_engineer/tasks/TASK-SCRIBE.md",
            now="2026-07-29T00:10:00+09:00",
        )


def test_cleanup_authorization_rejects_duplicate_authority_field(
    tmp_path: Path,
) -> None:
    source = tmp_path / "STATUS.md"
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(16)),
        encoding="utf-8",
    )
    _config(tmp_path, {"status": "STATUS.md"})
    _write_authorized_projection(tmp_path)
    authorization = (
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-SCRIBE.md"
    )
    authorization.write_text(
        authorization.read_text(encoding="utf-8").replace(
            "scribe_authorized_role: lead-engineer\n",
            "scribe_authorized_role: lead-engineer\n"
            "scribe_authorized_role: owner\n",
        ),
        encoding="utf-8",
    )
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(5, 16)),
        encoding="utf-8",
    )

    with pytest.raises(
        state_projection.StateProjectionError,
        match="bound TASK authorization",
    ):
        state_projection.record_cleanup(
            tmp_path,
            authorization_ref="agents/lead_engineer/tasks/TASK-SCRIBE.md",
            now="2026-07-29T00:10:00+09:00",
        )


def test_owner_decision_rejects_duplicate_json_field(tmp_path: Path) -> None:
    source = tmp_path / "STATUS.md"
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(16)),
        encoding="utf-8",
    )
    _config(tmp_path, {"status": "STATUS.md"})
    projection = _write_authorized_projection(tmp_path)
    decision_ref = _write_owner_no_touch_decision(tmp_path, projection)
    decision = tmp_path / decision_ref
    decision.write_text(
        decision.read_text(encoding="utf-8").replace(
            '"decision": "no_touch",',
            '"decision": "no_touch",\n  "decision": "no_touch",',
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        state_projection.StateProjectionError,
        match="bound owner no-touch decision",
    ):
        state_projection.record_cleanup(
            tmp_path,
            authorization_ref="agents/lead_engineer/tasks/TASK-SCRIBE.md",
            owner_decision_ref=decision_ref,
            now="2026-07-29T00:10:00+09:00",
        )


@pytest.mark.parametrize(
    "tamper",
    [
        "top-level-hot-count",
        "before-source-digest",
        "cleanup-plan-digest",
    ],
)
def test_cleanup_receipt_rejects_forged_baseline_bindings(
    tmp_path: Path,
    tamper: str,
) -> None:
    source = tmp_path / "STATUS.md"
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(11)),
        encoding="utf-8",
    )
    _config(tmp_path, {"status": "STATUS.md"})
    _write_authorized_projection(tmp_path)
    projection_path = tmp_path / state_projection.DEFAULT_PROJECTION_PATH
    payload = json.loads(projection_path.read_text(encoding="utf-8"))
    if tamper == "top-level-hot-count":
        payload["hot_count"] = 16
    elif tamper == "before-source-digest":
        payload["sources"][0]["digest"] = "0" * 64
    else:
        payload["cleanup_plan"]["plan_digest"] = "0" * 64
    projection_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        state_projection.StateProjectionError,
        match="baseline",
    ):
        state_projection.record_cleanup(
            tmp_path,
            authorization_ref="agents/lead_engineer/tasks/TASK-SCRIBE.md",
            now="2026-07-29T00:10:00+09:00",
        )


@pytest.mark.parametrize(
    "tamper",
    [
        "before-hot-count",
        "before-source-digest",
        "cleanup-plan-digest",
    ],
)
def test_cleanup_outcome_replays_baseline_validation_after_receipt_tamper(
    tmp_path: Path,
    tamper: str,
) -> None:
    source = tmp_path / "STATUS.md"
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(16)),
        encoding="utf-8",
    )
    _config(tmp_path, {"status": "STATUS.md"})
    _write_authorized_projection(tmp_path)
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(5, 16)),
        encoding="utf-8",
    )
    state_projection.record_cleanup(
        tmp_path,
        authorization_ref="agents/lead_engineer/tasks/TASK-SCRIBE.md",
        now="2026-07-29T00:10:00+09:00",
    )
    projection_path = tmp_path / state_projection.DEFAULT_PROJECTION_PATH
    payload = json.loads(projection_path.read_text(encoding="utf-8"))
    receipt = payload["cleanup_receipt"]
    if tamper == "before-hot-count":
        receipt["before_hot_count"] = 99
    elif tamper == "before-source-digest":
        receipt["before_sources"][0]["digest"] = "0" * 64
        receipt["before_source_binding_digest"] = state_projection._canonical_digest(  # noqa: SLF001
            receipt["before_sources"]
        )
    else:
        receipt["before_cleanup_plan"]["plan_digest"] = "0" * 64
        receipt["cleanup_plan_digest"] = "0" * 64
    receipt["receipt_digest"] = state_projection._canonical_digest(  # noqa: SLF001
        {
            key: value
            for key, value in receipt.items()
            if key != "receipt_digest"
        }
    )
    projection_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = state_projection.evaluate_state(tmp_path)

    assert result["cleanup_outcome"]["status"] == "invalid"
    assert result["closure_blocking"] is True
    assert result["readiness"] == "blocked"


def test_cleanup_receipt_rejects_fully_rebound_unchanged_source_baseline(
    tmp_path: Path,
) -> None:
    source = tmp_path / "STATUS.md"
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(11)),
        encoding="utf-8",
    )
    _config(tmp_path, {"status": "STATUS.md"})
    _write_authorized_projection(tmp_path)
    projection_path = tmp_path / state_projection.DEFAULT_PROJECTION_PATH
    payload = json.loads(projection_path.read_text(encoding="utf-8"))
    payload["sources"][0]["hot_count"] = 16
    payload["hot_count"] = 16
    payload["source_debt"]["hot_count"] = 16
    source_binding_digest = state_projection._canonical_digest(  # noqa: SLF001
        _receipt_sources(payload)
    )
    _write_scribe_task(
        tmp_path,
        source_binding_digest=source_binding_digest,
        cleanup_plan_digest=payload["cleanup_plan"]["plan_digest"],
    )
    projection_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _commit_all(tmp_path, "forge a self-consistent Scribe baseline")

    with pytest.raises(
        state_projection.StateProjectionError,
        match="baseline|anchor",
    ):
        state_projection.record_cleanup(
            tmp_path,
            authorization_ref="agents/lead_engineer/tasks/TASK-SCRIBE.md",
            now="2026-07-29T00:10:00+09:00",
        )


def test_cleanup_outcome_rejects_fully_rebound_receipt_and_authority(
    tmp_path: Path,
) -> None:
    source = tmp_path / "STATUS.md"
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(16)),
        encoding="utf-8",
    )
    _config(tmp_path, {"status": "STATUS.md"})
    _write_authorized_projection(tmp_path)
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(5, 16)),
        encoding="utf-8",
    )
    state_projection.record_cleanup(
        tmp_path,
        authorization_ref="agents/lead_engineer/tasks/TASK-SCRIBE.md",
        now="2026-07-29T00:10:00+09:00",
    )
    projection_path = tmp_path / state_projection.DEFAULT_PROJECTION_PATH
    payload = json.loads(projection_path.read_text(encoding="utf-8"))
    receipt = payload["cleanup_receipt"]
    receipt["before_sources"][0]["hot_count"] = 99
    receipt["before_hot_count"] = 99
    rebound_source_digest = state_projection._canonical_digest(  # noqa: SLF001
        receipt["before_sources"]
    )
    receipt["before_source_binding_digest"] = rebound_source_digest
    _write_scribe_task(
        tmp_path,
        source_binding_digest=rebound_source_digest,
        cleanup_plan_digest=receipt["cleanup_plan_digest"],
    )
    attack_commit = _commit_all(tmp_path, "rebind forged receipt authority")
    receipt["authorization_commit"] = attack_commit
    receipt["authorization_blob_oid"] = _git_blob(
        tmp_path,
        attack_commit,
        "agents/lead_engineer/tasks/TASK-SCRIBE.md",
    )
    receipt["receipt_digest"] = state_projection._canonical_digest(  # noqa: SLF001
        {
            key: value
            for key, value in receipt.items()
            if key != "receipt_digest"
        }
    )
    projection_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = state_projection.evaluate_state(tmp_path)

    assert result["cleanup_outcome"]["status"] == "invalid"
    assert result["closure_blocking"] is True
    assert result["readiness"] == "blocked"


def test_owner_decision_rejects_non_string_approver_identity(
    tmp_path: Path,
) -> None:
    source = tmp_path / "STATUS.md"
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(16)),
        encoding="utf-8",
    )
    _config(tmp_path, {"status": "STATUS.md"})
    projection = _write_authorized_projection(tmp_path)
    decision_ref = _write_owner_no_touch_decision(tmp_path, projection)
    decision_path = tmp_path / decision_ref
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    decision["approved_by"] = {"name": "not-a-scalar"}
    decision_path.write_text(
        json.dumps(decision, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _commit_all(tmp_path, "forge non-scalar owner identity")

    with pytest.raises(
        state_projection.StateProjectionError,
        match="bound owner no-touch decision",
    ):
        state_projection.record_cleanup(
            tmp_path,
            authorization_ref="agents/lead_engineer/tasks/TASK-SCRIBE.md",
            owner_decision_ref=decision_ref,
            now="2026-07-29T00:10:00+09:00",
        )


@pytest.mark.parametrize(
    "authorized_by",
    [
        "null",
        "null # forged identity",
        "~",
        "true",
        "true # forged identity",
        "{name: forged}",
        "[forged]",
        "123",
    ],
)
def test_cleanup_authorization_rejects_non_string_or_placeholder_identity(
    tmp_path: Path,
    authorized_by: str,
) -> None:
    source = tmp_path / "STATUS.md"
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(16)),
        encoding="utf-8",
    )
    _config(tmp_path, {"status": "STATUS.md"})
    _write_authorized_projection(tmp_path)
    authorization = (
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-SCRIBE.md"
    )
    text = authorization.read_text(encoding="utf-8")
    text = text.replace(
        "scribe_authorized_by: lead-engineer-fixture\n",
        f"scribe_authorized_by: {authorized_by}\n",
    )
    authorization.write_text(text, encoding="utf-8")
    _commit_all(tmp_path, "forge malformed Scribe authority identity")
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(5, 16)),
        encoding="utf-8",
    )

    with pytest.raises(
        state_projection.StateProjectionError,
        match="bound TASK authorization",
    ):
        state_projection.record_cleanup(
            tmp_path,
            authorization_ref="agents/lead_engineer/tasks/TASK-SCRIBE.md",
            now="2026-07-29T00:10:00+09:00",
        )


def test_cleanup_authorization_rejects_conflicting_task_identity(
    tmp_path: Path,
) -> None:
    source = tmp_path / "STATUS.md"
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(16)),
        encoding="utf-8",
    )
    _config(tmp_path, {"status": "STATUS.md"})
    _write_authorized_projection(tmp_path)
    projection_path = tmp_path / state_projection.DEFAULT_PROJECTION_PATH
    authorization = (
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-SCRIBE.md"
    )
    authorization.write_text(
        authorization.read_text(encoding="utf-8").replace(
            "id: TASK-SCRIBE\n",
            "id: TASK-UNRELATED\n",
        ),
        encoding="utf-8",
    )
    state_projection.write_projection(
        tmp_path,
        now="2026-07-29T00:01:00+09:00",
    )
    projection = json.loads(projection_path.read_text(encoding="utf-8"))
    text = authorization.read_text(encoding="utf-8")
    text = re.sub(
        r"(?m)^scribe_source_binding_digest: .+$",
        "scribe_source_binding_digest: "
        + state_projection._canonical_digest(  # noqa: SLF001
            _receipt_sources(projection)
        ),
        text,
    )
    text = re.sub(
        r"(?m)^scribe_cleanup_plan_digest: .+$",
        "scribe_cleanup_plan_digest: "
        + projection["cleanup_plan"]["plan_digest"],
        text,
    )
    authorization.write_text(text, encoding="utf-8")
    _commit_all(tmp_path, "forge conflicting Scribe task identity")
    source.write_text(
        "# Status\n" + "".join(f"- item {index}\n" for index in range(5, 16)),
        encoding="utf-8",
    )

    with pytest.raises(
        state_projection.StateProjectionError,
        match="bound TASK authorization",
    ):
        state_projection.record_cleanup(
            tmp_path,
            authorization_ref="agents/lead_engineer/tasks/TASK-SCRIBE.md",
            now="2026-07-29T00:10:00+09:00",
        )


def test_active_work_discovery_does_not_follow_record_symlink_escape(
    tmp_path: Path,
) -> None:
    source = tmp_path / "STATUS.md"
    source.write_text("# Status\n- current\n", encoding="utf-8")
    _config(tmp_path, {"status": "STATUS.md"})
    outside = tmp_path.parent / f"{tmp_path.name}-outside-task.md"
    outside.write_text(
        "---\nid: TASK-PRIVATE-OUTSIDE\nstatus: in_progress\n---\n",
        encoding="utf-8",
    )
    task_link = (
        tmp_path
        / "agents"
        / "lead_engineer"
        / "tasks"
        / "TASK-LINKED-OUTSIDE.md"
    )
    task_link.parent.mkdir(parents=True, exist_ok=True)
    task_link.symlink_to(outside)

    result = state_projection.evaluate_state(tmp_path)
    rendered = json.dumps(result, ensure_ascii=False)

    assert "TASK-PRIVATE-OUTSIDE" not in rendered
    assert "active-task-unreadable" in rendered


def test_default_evaluation_is_read_only_and_explicit_cli_write_is_only_mutation(
    tmp_path: Path,
) -> None:
    source = _copy_fixture(tmp_path, "agent-runtime-status.md", "STATUS.md")
    _config(tmp_path, {"status": "STATUS.md"})
    source_mtime = source.stat().st_mtime_ns
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")

    read_only = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "scribe_due.py"),
            "--root",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )
    assert read_only.returncode == 0
    assert json.loads(read_only.stdout)["projection"]["status"] == "missing"
    assert not (tmp_path / state_projection.DEFAULT_PROJECTION_PATH).exists()
    assert source.stat().st_mtime_ns == source_mtime

    written = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "scribe_due.py"),
            "--root",
            str(tmp_path),
            "--write-projection",
            "--now",
            "2026-07-29T00:00:00+09:00",
            "--json",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )
    assert written.returncode == 0, written.stderr
    assert json.loads(written.stdout)["projection"]["status"] == "fresh"
    assert source.stat().st_mtime_ns == source_mtime


def test_custom_projection_requires_generated_ownership_and_distinct_path(
    tmp_path: Path,
) -> None:
    _copy_fixture(tmp_path, "bean-wiki-backlog.md", "BACKLOG.md")
    _config(
        tmp_path,
        {"backlog": "BACKLOG.md"},
        projection="custom/scribe.json",
    )
    with pytest.raises(ValueError, match="ownership.generated"):
        config.load_config(tmp_path)

    _config(
        tmp_path,
        {"backlog": "BACKLOG.md"},
        projection="custom/scribe.json",
        declare_generated=True,
    )
    assert config.load_config(tmp_path).state_projection == "custom/scribe.json"
    state_projection.write_projection(
        tmp_path, now="2026-07-29T00:00:00+09:00"
    )
    assert (tmp_path / "custom/scribe.json").is_file()
    assert not (tmp_path / state_projection.DEFAULT_PROJECTION_PATH).exists()

    _config(
        tmp_path,
        {"backlog": "BACKLOG.md"},
        projection="BACKLOG.md",
        declare_generated=True,
    )
    with pytest.raises(ValueError, match="distinct|mixed ownership overlap"):
        config.load_config(tmp_path)


def test_projection_write_refuses_parent_symlink_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "project").symlink_to(outside, target_is_directory=True)
    _copy_fixture(tmp_path, "agent-runtime-status.md", "STATUS.md")
    _config(tmp_path, {"status": "STATUS.md"})

    with pytest.raises(state_projection.StateProjectionError, match="outside"):
        state_projection.write_projection(tmp_path)


def test_root_and_template_scribe_cli_are_exact_mirrors() -> None:
    assert (ROOT / "scripts/scribe_due.py").read_bytes() == (
        ROOT / "src/agent_runtime/templates/project/scripts/scribe_due.py"
    ).read_bytes()


@pytest.mark.parametrize("module", ["config.py", "state_projection.py"])
def test_portable_state_modules_are_exact_canonical_and_template_mirrors(
    module: str,
) -> None:
    canonical = ROOT / "src" / "agent_runtime" / module
    portable = ROOT / "scripts" / "agent_runtime" / module
    packaged = (
        ROOT
        / "src"
        / "agent_runtime"
        / "templates"
        / "project"
        / "scripts"
        / "agent_runtime"
        / module
    )

    assert portable.read_bytes() == canonical.read_bytes()
    assert packaged.read_bytes() == canonical.read_bytes()


def test_portable_state_package_initializers_are_exact_mirrors() -> None:
    portable = ROOT / "scripts/agent_runtime/__init__.py"
    packaged = (
        ROOT
        / "src/agent_runtime/templates/project/scripts/agent_runtime/__init__.py"
    )
    assert portable.read_bytes() == packaged.read_bytes()
    canonical_version = next(
        line for line in (ROOT / "src/agent_runtime/__init__.py").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.startswith("__version__ = ")
    )
    assert canonical_version in portable.read_text(encoding="utf-8")
