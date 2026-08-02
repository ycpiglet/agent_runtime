from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.parallel_worktree_gate import ClaimRecord, _continuity_findings, check_root


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "parallel_worktree_gate.py"
TRANSACTION_ENV = "AGENT_RUNTIME_CLAIM_COMMIT_TRANSACTION"
TRANSACTION_SCHEMA = "agent-runtime-claim-commit-transaction/v2"
AR655_LIVENESS_NOW = datetime(2026, 8, 3, 0, 0, tzinfo=timezone.utc)
AR655_FIXTURE_EXPIRY = "2099-01-01T00:00:00+00:00"


def _run_gate(
    root: Path,
    *,
    env: dict[str, str] | None = None,
    now: str | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(SCRIPT), "--root", str(root), "--check"]
    if now is not None:
        command.extend(("--now", now))
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


def _write_claim(root: Path, name: str, **overrides: object) -> Path:
    claim_dir = root / "agents" / "runtime" / "task_claims"
    claim_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": name,
        "task_id": "TASK-AR-246",
        "task_set_id": "TASKSET-AR-PANE-PROGRESS",
        "agent_role": "lead-engineer",
        "team_id": "agent-runtime-core",
        "agent_instance_id": "lead-engineer-A",
        "display_name": "lead_engineer@design-01",
        "callsite_id": "terminal-1",
        "pane_id": "terminal-1",
        "status": "working",
        "phase": "implement",
        "progress_pct": 10,
        "status_text": "Implementing task claim support",
        "worktree_path": ".worktrees/TASK-AR-246",
        "branch": "codex/task-ar-246-parallel-runtime",
        "claimed_at": "2026-06-10T12:00:00+09:00",
        "last_heartbeat": "2026-06-10T12:05:00+09:00",
        # Existing gate fixtures represent healthy status-active authority.
        # Complete copies avoid silently relying on legacy missing deadlines.
        "expires_at": AR655_FIXTURE_EXPIRY,
        "lease": {"expires_at": AR655_FIXTURE_EXPIRY},
        "handoff_path": "STATUS.md",
        "log_path": "reviews/REVIEW-2026-06-10-agent-runtime-parallel-session-protocol.md",
    }
    payload.update(overrides)
    worktree_value = str(payload.get("worktree_path") or "")
    if worktree_value and worktree_value != "." and not overrides.get("skip_worktree_marker"):
        worktree = root / worktree_value
        worktree.mkdir(parents=True, exist_ok=True)
        (worktree / ".git").write_text("gitdir: ../../.git/worktrees/test\n", encoding="utf-8")
    path = claim_dir / f"{name}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _active_claim(root: Path) -> ClaimRecord:
    return ClaimRecord(path=root / "claim.json", payload={"status": "claimed"})


def _write_status(root: Path, relative_path: str, text: str) -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


POINTER_AGENT_FIELDS = (
    "claim_id",
    "agent_role",
    "team_id",
    "agent_instance_id",
    "display_name",
    "callsite_id",
    "pane_id",
    "task_id",
    "unit_id",
    "task_set_id",
    "status",
    "phase",
    "progress_pct",
    "step_index",
    "step_total",
    "status_text",
    "worktree_path",
    "branch",
    "claim_path",
    "handoff_path",
    "log_path",
    "last_heartbeat",
)


def _portable_claim(root: Path, claim_id: str = "CLAIM-PORTABLE-1") -> ClaimRecord:
    claim_dir = root / "agents/runtime/task_claims"
    claim_dir.mkdir(parents=True, exist_ok=True)
    handoff = f"agents/runtime/task_claims/{claim_id}.handoff.md"
    log_path = f"agents/runtime/task_claims/{claim_id}.log.md"
    (root / handoff).write_text("# Handoff\n\nContinue the unit.\n", encoding="utf-8")
    (root / log_path).write_text("# Log\n\nClaim created.\n", encoding="utf-8")
    payload: dict[str, object] = {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": claim_id,
        "task_id": "TASK-AR-648",
        "unit_id": "UNIT-TASK-AR-648-008",
        "task_set_id": "TASKSET-AR-PORTABLE-CONTINUITY",
        "agent_role": "lead-engineer",
        "team_id": "agent-runtime-core",
        "agent_instance_id": "lead-engineer-portable-1",
        "display_name": "lead_engineer@portable-01",
        "callsite_id": "codex:portable:01",
        "pane_id": "codex:portable:01",
        "status": "claimed",
        "phase": "red-baseline",
        "progress_pct": 10,
        "step_index": 1,
        "step_total": 8,
        "status_text": "Reproducing the fresh core continuity journey",
        "worktree_path": ".worktrees/TASK-AR-648",
        "branch": "codex/task-ar-648-portable-continuity",
        "claimed_at": "2026-07-30T00:00:00+09:00",
        "last_heartbeat": "2026-07-30T00:05:00+09:00",
        "expires_at": AR655_FIXTURE_EXPIRY,
        "lease": {"expires_at": AR655_FIXTURE_EXPIRY},
        "handoff_path": handoff,
        "log_path": log_path,
    }
    path = claim_dir / f"{claim_id}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return ClaimRecord(path=path, payload=payload)


def _pointer_scalar(value: object) -> str:
    if value is None:
        return "null"
    return json.dumps(str(value), ensure_ascii=False)


def _write_portable_pointer(
    root: Path,
    records: list[ClaimRecord],
    *,
    updated_at: str = "2026-07-30T00:05:00+09:00",
    claim_refs: list[str] | None = None,
    omit_agent_field: str = "",
    agent_overrides: dict[str, object] | None = None,
    duplicate_agent: bool = False,
    next_actions: tuple[str, ...] = ("Run the portable continuity gate.",),
) -> Path:
    refs = claim_refs
    if refs is None:
        refs = [record.path.relative_to(root).as_posix() for record in records]
    agents: list[dict[str, object]] = []
    for record in records:
        agent = {
            field: (
                record.path.relative_to(root).as_posix()
                if field == "claim_path"
                else record.payload.get(field)
            )
            for field in POINTER_AGENT_FIELDS
            if field != omit_agent_field
        }
        if agent_overrides:
            agent.update(agent_overrides)
        agents.append(agent)
    if duplicate_agent and agents:
        agents.append(dict(agents[0]))

    primary = records[0].payload if records else {}
    lines = [
        "schema: agent-runtime-next-session-pointer/v1",
        f"updated_at: {_pointer_scalar(updated_at)}",
        "updated_by: portable-continuity-test",
        "current_state:",
        f"  status: {'active' if records else 'idle'}",
        f"  task_set_id: {_pointer_scalar(primary.get('task_set_id'))}",
        "active_work:",
    ]
    if agents:
        lines.append("  current_agents:")
        for agent in agents:
            for index, (field, value) in enumerate(agent.items()):
                prefix = "    - " if index == 0 else "      "
                lines.append(f"{prefix}{field}: {_pointer_scalar(value)}")
    else:
        lines.append("  current_agents: []")
    lines.extend(
        [
            "  current_teams: []",
            "resume:",
            f"  active_task: {_pointer_scalar(primary.get('task_id'))}",
            f"  active_task_set: {_pointer_scalar(primary.get('task_set_id'))}",
        ]
    )
    if next_actions:
        lines.append("  next_actions:")
        lines.extend(f"    - {_pointer_scalar(action)}" for action in next_actions)
    else:
        lines.append("  next_actions: []")
    lines.append("pointers:")
    if refs:
        lines.append("  active_claims:")
        lines.extend(f"    - {_pointer_scalar(ref)}" for ref in refs)
    else:
        lines.append("  active_claims: []")
    path = root / "agents/project/NEXT-SESSION-POINTER.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _set_ar655_record_deadlines(
    record: ClaimRecord,
    *,
    top: object,
    nested: object,
) -> None:
    if top is None:
        record.payload.pop("expires_at", None)
    else:
        record.payload["expires_at"] = top
    if nested is None:
        record.payload.pop("lease", None)
    else:
        record.payload["lease"] = {"expires_at": nested}
    record.path.write_text(
        json.dumps(record.payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def test_ar655_parallel_expired_claim_blocks_with_exact_pointer(tmp_path: Path) -> None:
    record = _portable_claim(tmp_path)
    expired = (AR655_LIVENESS_NOW - timedelta(seconds=601)).isoformat()
    _set_ar655_record_deadlines(record, top=expired, nested=expired)
    _write_portable_pointer(tmp_path, [record])

    findings = check_root(
        tmp_path,
        now=AR655_LIVENESS_NOW,
        grace_seconds=600,
    )

    assert any(
        "task-claim:liveness-expired:CLAIM-PORTABLE-1" in finding.message
        for finding in findings
    )


def test_ar655_parallel_cli_uses_explicit_aware_now_for_liveness(tmp_path: Path) -> None:
    record = _portable_claim(tmp_path)
    expired = (AR655_LIVENESS_NOW - timedelta(seconds=601)).isoformat()
    _set_ar655_record_deadlines(record, top=expired, nested=expired)
    _write_portable_pointer(tmp_path, [record])

    result = _run_gate(tmp_path, now=AR655_LIVENESS_NOW.isoformat())

    assert result.returncode == 1, result.stderr or result.stdout
    assert "task-claim:liveness-expired:CLAIM-PORTABLE-1" in result.stdout


@pytest.mark.parametrize("now", ("not-a-timestamp", "2026-08-03T00:00:00"))
def test_ar655_parallel_cli_refuses_malformed_or_naive_now_without_traceback(
    tmp_path: Path,
    now: str,
) -> None:
    result = _run_gate(tmp_path, now=now)
    output = (result.stdout or "") + (result.stderr or "")

    assert result.returncode != 0
    assert "invalid --now" in output
    assert "timezone-aware" in output
    assert "unrecognized arguments" not in output
    assert "Traceback" not in output


def test_ar655_parallel_expired_claim_blocks_even_when_status_handoff_passes(
    tmp_path: Path,
) -> None:
    _write_status(tmp_path, "STATUS.md", "# STATUS\n\n## Handoff Checklist\n")
    expired = (AR655_LIVENESS_NOW - timedelta(seconds=601)).isoformat()
    _write_claim(
        tmp_path,
        "CLAIM-AR655-STATUS-EXPIRED",
        expires_at=expired,
        lease={"expires_at": expired},
    )

    findings = check_root(
        tmp_path,
        now=AR655_LIVENESS_NOW,
        grace_seconds=600,
    )

    assert any(
        "task-claim:liveness-expired:CLAIM-AR655-STATUS-EXPIRED"
        in finding.message
        for finding in findings
    )


def test_ar655_parallel_expired_claim_does_not_cover_dirty_task_worktree(
    tmp_path: Path,
) -> None:
    repo = _init_git_repo(tmp_path)
    worktree = _add_task_worktree(
        repo,
        name="TASK-AR-900",
        branch="claude/task-ar-900-demo",
    )
    (worktree / "wip.txt").write_text("uncommitted work\n", encoding="utf-8")
    expired = (AR655_LIVENESS_NOW - timedelta(seconds=601)).isoformat()
    _write_claim(
        repo,
        "CLAIM-AR655-DIRTY-EXPIRED",
        task_id="TASK-AR-900",
        worktree_path=".worktrees/TASK-AR-900",
        branch="claude/task-ar-900-demo",
        skip_worktree_marker=True,
        expires_at=expired,
        lease={"expires_at": expired},
        persistence={"mode": "working_tree", "scm_commit_authorized": False},
    )

    findings = check_root(
        repo,
        now=AR655_LIVENESS_NOW,
        grace_seconds=600,
    )

    assert any(
        "worktree:missing-claim-dirty" in finding.message
        for finding in findings
    )


def test_ar655_parallel_indeterminate_claim_blocks_but_retains_dirty_worktree_authority(
    tmp_path: Path,
) -> None:
    repo = _init_git_repo(tmp_path)
    worktree = _add_task_worktree(
        repo,
        name="TASK-AR-900",
        branch="claude/task-ar-900-demo",
    )
    (worktree / "wip.txt").write_text(
        "conservatively authorized uncommitted work\n",
        encoding="utf-8",
    )
    _write_claim(
        repo,
        "CLAIM-AR655-DIRTY-INDETERMINATE",
        task_id="TASK-AR-900",
        worktree_path=".worktrees/TASK-AR-900",
        branch="claude/task-ar-900-demo",
        skip_worktree_marker=True,
        expires_at=AR655_FIXTURE_EXPIRY,
        lease=None,
        persistence={"mode": "working_tree", "scm_commit_authorized": False},
    )

    findings = check_root(
        repo,
        now=AR655_LIVENESS_NOW,
        grace_seconds=600,
    )
    messages = [finding.message for finding in findings]

    assert any(
        "task-claim:liveness-indeterminate:CLAIM-AR655-DIRTY-INDETERMINATE"
        in message
        for message in messages
    )
    assert not any(
        "worktree:missing-claim-dirty" in message
        for message in messages
    )


@pytest.mark.parametrize(
    ("top", "nested", "expect_mismatch"),
    (
        (
            (AR655_LIVENESS_NOW - timedelta(seconds=600)).isoformat(),
            (AR655_LIVENESS_NOW - timedelta(seconds=600)).isoformat(),
            False,
        ),
        (
            (AR655_LIVENESS_NOW - timedelta(seconds=601)).isoformat(),
            (AR655_LIVENESS_NOW + timedelta(seconds=1)).isoformat(),
            True,
        ),
    ),
)
def test_ar655_parallel_within_grace_or_latest_deadline_retains_worktree_authority(
    tmp_path: Path,
    top: str,
    nested: str,
    expect_mismatch: bool,
) -> None:
    repo = _init_git_repo(tmp_path)
    worktree = _add_task_worktree(
        repo,
        name="TASK-AR-900",
        branch="claude/task-ar-900-demo",
    )
    (worktree / "wip.txt").write_text("authorized uncommitted work\n", encoding="utf-8")
    _write_claim(
        repo,
        "CLAIM-AR655-DIRTY-LIVE",
        task_id="TASK-AR-900",
        worktree_path=".worktrees/TASK-AR-900",
        branch="claude/task-ar-900-demo",
        skip_worktree_marker=True,
        expires_at=top,
        lease={"expires_at": nested},
        persistence={"mode": "working_tree", "scm_commit_authorized": False},
    )

    findings = check_root(
        repo,
        now=AR655_LIVENESS_NOW,
        grace_seconds=600,
    )
    messages = [finding.message for finding in findings]

    assert not any("worktree:missing-claim-dirty" in message for message in messages)
    assert not any("task-claim:liveness-expired" in message for message in messages)
    assert any("task-claim:liveness-deadline-mismatch" in message for message in messages) is expect_mismatch


@pytest.mark.parametrize(
    "marker",
    ["Handoff Checklist", "Next Steps", "다음 세션", "다음 단계", "인수인계"],
)
@pytest.mark.parametrize(
    "relative_path",
    ["STATUS.md", "agents/lead_engineer/STATUS.md"],
)
def test_continuity_accepts_status_candidate_resume_markers(
    tmp_path: Path, relative_path: str, marker: str
):
    _write_status(
        tmp_path,
        relative_path,
        f"# STATUS\n\n## {marker}\n",
    )

    assert _continuity_findings(tmp_path, [_active_claim(tmp_path)]) == []


def test_continuity_prefers_root_status_over_valid_host_fallback(tmp_path: Path):
    _write_status(tmp_path, "STATUS.md", "# STATUS\n\n## Current Work\n")
    _write_status(
        tmp_path,
        "agents/lead_engineer/STATUS.md",
        "# STATUS\n\n## 다음 세션\n",
    )

    findings = _continuity_findings(tmp_path, [_active_claim(tmp_path)])

    assert len(findings) == 1
    assert findings[0].startswith("STATUS.md: continuity:status-handoff-missing:")
    assert "agents/lead_engineer/STATUS.md" not in findings[0]


def test_continuity_missing_status_requires_canonical_pointer(tmp_path: Path):
    findings = _continuity_findings(tmp_path, [_active_claim(tmp_path)])

    assert len(findings) == 1
    assert "continuity:pointer-missing" in findings[0]
    assert "agents/project/NEXT-SESSION-POINTER.yml" in findings[0]
    assert "continuity:status-missing" in findings[0]
    assert all(
        candidate in findings[0]
        for candidate in ("STATUS.md", "agents/lead_engineer/STATUS.md")
    )


def test_continuity_accepts_exact_pointer_and_sidecars_without_status(tmp_path: Path):
    record = _portable_claim(tmp_path)
    _write_portable_pointer(tmp_path, [record])

    assert _continuity_findings(tmp_path, [record]) == []


def test_continuity_present_invalid_status_cannot_be_bypassed_by_pointer(tmp_path: Path):
    record = _portable_claim(tmp_path)
    _write_portable_pointer(tmp_path, [record])
    _write_status(tmp_path, "STATUS.md", "# STATUS\n\n## Current Work\n")

    findings = _continuity_findings(tmp_path, [record])

    assert len(findings) == 1
    assert "continuity:status-handoff-missing" in findings[0]


@pytest.mark.parametrize(
    ("case", "reason"),
    [
        ("placeholder", "continuity:pointer-placeholder"),
        ("malformed", "continuity:pointer-malformed"),
        ("schema-invalid", "continuity:pointer-schema-invalid"),
        ("timestamp-invalid", "continuity:pointer-updated-at-invalid"),
        ("stale", "continuity:pointer-stale"),
        ("duplicate-ref", "continuity:pointer-duplicate-active-claim"),
        ("extra-ref", "continuity:pointer-active-claims-mismatch"),
        ("partial-agent", "continuity:pointer-agent-field-missing"),
        ("mismatched-agent", "continuity:pointer-agent-field-mismatch"),
        ("duplicate-agent", "continuity:pointer-duplicate-current-agent"),
        ("resume-mismatch", "continuity:pointer-resume-mismatch"),
        ("missing-next-action", "continuity:pointer-next-actions-missing"),
    ],
)
def test_continuity_pointer_fallback_fails_closed_with_stable_reasons(
    tmp_path: Path,
    case: str,
    reason: str,
):
    record = _portable_claim(tmp_path)
    ref = record.path.relative_to(tmp_path).as_posix()
    if case == "malformed":
        pointer = tmp_path / "agents/project/NEXT-SESSION-POINTER.yml"
        pointer.parent.mkdir(parents=True, exist_ok=True)
        pointer.write_text(
            "schema: agent-runtime-next-session-pointer/v1\n"
            "active_work:\n"
            "  current_agents\n",
            encoding="utf-8",
        )
    else:
        _write_portable_pointer(
            tmp_path,
            [record],
            updated_at=(
                "YYYY-MM-DDTHH:MM:SS+09:00"
                if case == "placeholder"
                else "not-a-timestamp"
                if case == "timestamp-invalid"
                else "2026-07-30T00:04:59+09:00"
                if case == "stale"
                else "2026-07-30T00:05:00+09:00"
            ),
            claim_refs=(
                [ref, ref]
                if case == "duplicate-ref"
                else [ref, "agents/runtime/task_claims/CLAIM-EXTRA.json"]
                if case == "extra-ref"
                else None
            ),
            omit_agent_field="log_path" if case == "partial-agent" else "",
            agent_overrides={"branch": "codex/wrong-branch"}
            if case == "mismatched-agent"
            else None,
            duplicate_agent=case == "duplicate-agent",
            next_actions=() if case == "missing-next-action" else ("Resume the unit.",),
        )
        pointer = tmp_path / "agents/project/NEXT-SESSION-POINTER.yml"
        if case == "schema-invalid":
            pointer.write_text(
                pointer.read_text(encoding="utf-8").replace(
                    "agent-runtime-next-session-pointer/v1",
                    "agent-runtime-next-session-pointer/v999",
                    1,
                ),
                encoding="utf-8",
            )
        if case == "resume-mismatch":
            pointer.write_text(
                pointer.read_text(encoding="utf-8").replace(
                    '  active_task: "TASK-AR-648"',
                    '  active_task: "TASK-AR-WRONG"',
                    1,
                ),
                encoding="utf-8",
            )

    findings = _continuity_findings(tmp_path, [record])

    assert any(reason in finding for finding in findings), findings


def test_continuity_retains_handoff_and_log_sidecar_checks_with_pointer(
    tmp_path: Path,
):
    record = _portable_claim(tmp_path)
    _write_portable_pointer(tmp_path, [record])
    (tmp_path / str(record.payload["handoff_path"])).unlink()
    (tmp_path / str(record.payload["log_path"])).unlink()

    findings = _continuity_findings(tmp_path, [record])

    assert any("task-claim:handoff-path-missing-file" in item for item in findings)
    assert any("task-claim:log-path-missing-file" in item for item in findings)


def test_continuity_rejects_unparseable_claim_heartbeat(tmp_path: Path):
    record = _portable_claim(tmp_path)
    record.payload["last_heartbeat"] = "not-a-timestamp"
    record.path.write_text(
        json.dumps(record.payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _write_portable_pointer(
        tmp_path,
        [record],
        updated_at="2026-07-30T00:05:00+09:00",
    )

    findings = _continuity_findings(tmp_path, [record])

    assert any(
        "continuity:pointer-claim-heartbeat-invalid" in item
        for item in findings
    )


def test_continuity_only_json_reports_effective_pointer_path(tmp_path: Path):
    record = _portable_claim(tmp_path)
    _write_portable_pointer(tmp_path, [record])

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(tmp_path),
            "--continuity-only",
            "--now",
            AR655_LIVENESS_NOW.isoformat(),
            "--json",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "pass"
    assert payload["mode"] == "pointer+sidecars"


def test_continuity_missing_marker_names_selected_host_path(tmp_path: Path):
    _write_status(
        tmp_path,
        "agents/lead_engineer/STATUS.md",
        "# STATUS\n\n## Current Work\n",
    )

    findings = _continuity_findings(tmp_path, [_active_claim(tmp_path)])

    assert len(findings) == 1
    assert findings[0].startswith(
        "agents/lead_engineer/STATUS.md: continuity:status-handoff-missing:"
    )


def test_gate_passes_when_no_parallel_task_claims_exist(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")

    result = _run_gate(tmp_path)

    assert result.returncode == 0
    assert "parallel-worktree-gate: pass" in result.stdout
    assert "findings=0" in result.stdout


def test_gate_passes_fresh_host_without_status_when_no_claims_exist(tmp_path: Path):
    result = _run_gate(tmp_path)

    assert result.returncode == 0
    assert "parallel-worktree-gate: pass" in result.stdout


def test_gate_blocks_duplicate_active_claims_for_one_task(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_claim(tmp_path, "CLAIM-1")
    _write_claim(
        tmp_path,
        "CLAIM-2",
        claim_id="CLAIM-2",
        agent_instance_id="lead-engineer-B",
        callsite_id="terminal-2",
        worktree_path=".worktrees/TASK-AR-246-B",
        branch="codex/task-ar-246-parallel-runtime-b",
    )

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "task-claim:duplicate-active-task:TASK-AR-246" in result.stdout


def test_gate_allows_same_role_with_distinct_instances_and_worktrees(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    review = tmp_path / "reviews" / "REVIEW-2026-06-10-agent-runtime-parallel-session-protocol.md"
    review.parent.mkdir(parents=True, exist_ok=True)
    review.write_text("parallel session handoff log\n", encoding="utf-8")
    _write_claim(tmp_path, "CLAIM-1", task_id="TASK-AR-246")
    _write_claim(
        tmp_path,
        "CLAIM-2",
        claim_id="CLAIM-2",
        task_id="TASK-AR-247",
        task_set_id="TASKSET-AR-QUALITY-LOOP",
        agent_instance_id="lead-engineer-B",
        callsite_id="terminal-2",
        worktree_path=".worktrees/TASK-AR-247",
        branch="codex/task-ar-247-other",
    )

    result = _run_gate(tmp_path)

    assert result.returncode == 0
    assert "findings=0" in result.stdout


def test_gate_blocks_worker_claim_in_main_checkout(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_claim(tmp_path, "CLAIM-1", worktree_path=".")

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "task-claim:main-checkout-worker" in result.stdout


def test_gate_blocks_missing_worktree_for_active_claim(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_claim(tmp_path, "CLAIM-1", skip_worktree_marker=True)

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "task-claim:worktree-path-missing" in result.stdout


def test_gate_blocks_non_git_worktree_for_active_claim(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    worktree = tmp_path / ".worktrees" / "TASK-AR-246"
    worktree.mkdir(parents=True, exist_ok=True)
    _write_claim(tmp_path, "CLAIM-1", skip_worktree_marker=True)

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "task-claim:worktree-not-git-worktree" in result.stdout


def test_gate_blocks_missing_handoff_pointer_for_active_claim(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Current State\n- active\n", encoding="utf-8")
    _write_claim(tmp_path, "CLAIM-1", handoff_path="")

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "task-claim:missing-handoff-path" in result.stdout
    assert "continuity:status-handoff-missing" in result.stdout


def test_gate_blocks_missing_display_name_for_active_claim(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_claim(tmp_path, "CLAIM-1", display_name="")

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "task-claim:missing-display-name" in result.stdout


def test_gate_blocks_duplicate_active_claims_for_one_task_set(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_claim(tmp_path, "CLAIM-1", task_id="TASK-AR-205", worktree_path=".worktrees/TASK-AR-205")
    _write_claim(
        tmp_path,
        "CLAIM-2",
        claim_id="CLAIM-2",
        task_id="TASK-AR-206",
        agent_instance_id="qa-B",
        callsite_id="terminal-2",
        worktree_path=".worktrees/TASK-AR-206",
        branch="codex/task-ar-206-quality-loop",
    )

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "task-claim:duplicate-active-task-set:TASKSET-AR-PANE-PROGRESS" in result.stdout


def test_gate_blocks_missing_taskset_progress_fields_for_active_claim(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_claim(tmp_path, "CLAIM-1", task_set_id="", status_text="")

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "task-claim:missing-task-set-id" in result.stdout
    assert "task-claim:missing-status-text" in result.stdout


def test_gate_allows_only_explicit_overlay_to_omit_worker_checkout_fields(
    tmp_path: Path,
):
    (tmp_path / "STATUS.md").write_text(
        "## Next Steps\n- run the review overlay\n",
        encoding="utf-8",
    )
    _write_claim(
        tmp_path,
        "CLAIM-REVIEW-1",
        task_id="REVIEW-TASK-AR-246-independent-auditor",
        agent_role="independent-auditor",
        agent_instance_id="independent-auditor-CLAIM-REVIEW-1",
        display_name="independent-auditor@review",
        callsite_id="role-routing:closeout:TASK-AR-246:independent-auditor",
        pane_id="overlay:CLAIM-REVIEW-1",
        mode="review",
        overlay=True,
        allow_parallel_task_set=True,
        parent_task_id="TASK-AR-246",
        parent_task_set_id="TASKSET-AR-PANE-PROGRESS",
        worktree_path=None,
        branch=None,
        handoff_path="STATUS.md",
        log_path="STATUS.md",
        persistence={
            "mode": "working_tree",
            "scm_commit_authorized": False,
        },
    )

    result = _run_gate(tmp_path)

    assert result.returncode == 0, result.stdout
    assert "block=0" in result.stdout


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _init_git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "gate-test@example.com")
    _git(repo, "config", "user.name", "Gate Test")
    _git(repo, "config", "commit.gpgsign", "false")
    (repo / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    review = repo / "reviews" / "REVIEW-2026-06-10-agent-runtime-parallel-session-protocol.md"
    review.parent.mkdir(parents=True, exist_ok=True)
    review.write_text("parallel session handoff log\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "init")
    return repo


def _transaction_env(
    repo: Path,
    claim_path: Path,
    *,
    persist_record: bool = True,
    root_value: str | None = None,
    claim_paths: list[str] | None = None,
    owner_pid: int | None = None,
    head: str | None = None,
    marker_overrides: dict[str, object] | None = None,
    artifact_paths: list[Path] | None = None,
) -> tuple[dict[str, str], Path]:
    nonce = "0123456789abcdef0123456789abcdef"
    rel = claim_path.relative_to(repo).as_posix()
    artifact_rels = [
        path.relative_to(repo).as_posix()
        for path in (artifact_paths or [claim_path])
    ]
    current_head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    current_ref = subprocess.run(
        ["git", "-C", str(repo), "symbolic-ref", "-q", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    git_path = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "rev-parse",
            "--git-path",
            "agent-runtime/claim-commit",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    private_dir = Path(git_path)
    if not private_dir.is_absolute():
        private_dir = repo / private_dir
    private_dir = private_dir.resolve()
    private_dir.mkdir(parents=True, exist_ok=True)
    private_dir.chmod(0o700)
    index_path = private_dir / f"{nonce}.index"
    env = dict(os.environ)
    env["GIT_INDEX_FILE"] = str(index_path)
    subprocess.run(
        ["git", "-C", str(repo), "read-tree", current_head],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    index_path.chmod(0o600)
    subprocess.run(
        ["git", "-C", str(repo), "add", "--", *artifact_rels],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    artifacts: list[dict[str, str]] = []
    for artifact_rel in artifact_rels:
        staged = subprocess.run(
            ["git", "-C", str(repo), "ls-files", "--stage", "--", artifact_rel],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        ).stdout.strip()
        mode, oid, _stage, indexed_path = staged.split(None, 3)
        assert indexed_path == artifact_rel
        artifacts.append({"path": artifact_rel, "mode": mode, "oid": oid})
    tree = subprocess.run(
        ["git", "-C", str(repo), "write-tree"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    ).stdout.strip()
    marker = {
        "schema": TRANSACTION_SCHEMA,
        "root": root_value or str(repo.resolve()),
        "claim_paths": claim_paths or [rel],
        "artifacts": artifacts,
        "nonce": nonce,
        "owner_pid": owner_pid if owner_pid is not None else os.getpid(),
        "head": head or current_head,
        "ref": current_ref,
        "index": str(index_path),
        "tree": tree,
    }
    if marker_overrides:
        marker.update(marker_overrides)
    raw = json.dumps(marker, sort_keys=True, separators=(",", ":"))
    record_path = private_dir / f"{nonce}.json"
    if persist_record:
        record_path.write_text(raw + "\n", encoding="utf-8")
        record_path.chmod(0o600)
    env[TRANSACTION_ENV] = raw
    return env, record_path


def _rewrite_transaction_marker(
    env: dict[str, str],
    record_path: Path,
    payload: dict[str, object],
) -> dict[str, str]:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    record_path.write_text(raw + "\n", encoding="utf-8")
    record_path.chmod(0o600)
    updated = dict(env)
    updated[TRANSACTION_ENV] = raw
    return updated


def _add_task_worktree(repo: Path, name: str = "TASK-AR-900", branch: str = "claude/task-ar-900-demo") -> Path:
    path = repo / ".worktrees" / name
    _git(repo, "worktree", "add", "-b", branch, str(path), "main")
    return path


def test_gate_watches_claimless_clean_task_worktree(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    _add_task_worktree(repo)

    result = _run_gate(repo)

    assert result.returncode == 0, result.stdout
    assert "worktree:missing-claim" in result.stdout
    assert "worktree:missing-claim-dirty" not in result.stdout
    assert "worktree:missing-claim-ahead" not in result.stdout
    assert "block=0" in result.stdout
    assert "- watch" in result.stdout


def test_gate_blocks_claimless_dirty_task_worktree(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    worktree = _add_task_worktree(repo)
    (worktree / "wip.txt").write_text("uncommitted work without a claim\n", encoding="utf-8")

    result = _run_gate(repo)

    assert result.returncode == 1
    assert "worktree:missing-claim-dirty" in result.stdout
    assert "- block" in result.stdout


def test_gate_blocks_claimless_ahead_task_worktree(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    worktree = _add_task_worktree(repo)
    (worktree / "done.txt").write_text("committed work without a claim\n", encoding="utf-8")
    _git(worktree, "add", "done.txt")
    _git(worktree, "commit", "-m", "work without claim")

    result = _run_gate(repo)

    assert result.returncode == 1
    assert "worktree:missing-claim-ahead" in result.stdout


def test_gate_passes_claimed_task_worktree(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    _add_task_worktree(repo, name="TASK-AR-900", branch="claude/task-ar-900-demo")
    _write_claim(
        repo,
        "CLAIM-1",
        task_id="TASK-AR-900",
        worktree_path=".worktrees/TASK-AR-900",
        branch="claude/task-ar-900-demo",
        skip_worktree_marker=True,
        persistence={
            "mode": "scm_commit",
            "scm_commit_authorized": True,
        },
    )
    _git(repo, "add", "agents")
    _git(repo, "commit", "-m", "open claim")

    result = _run_gate(repo)

    assert result.returncode == 0, result.stdout
    assert "worktree:missing-claim" not in result.stdout
    assert "findings=0" in result.stdout


def test_gate_blocks_untracked_claim_file(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    _write_claim(repo, "CLAIM-1")

    result = _run_gate(repo)

    assert result.returncode == 1
    assert "task-claim:claim-not-committed" in result.stdout
    assert "2026-06-12" in result.stdout


def test_gate_watches_explicit_working_tree_claim_persistence(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    _write_claim(
        repo,
        "CLAIM-1",
        persistence={
            "mode": "working_tree",
            "scm_commit_authorized": False,
        },
    )

    result = _run_gate(repo)

    assert result.returncode == 0, result.stdout
    assert "task-claim:working-tree-persistence" in result.stdout
    assert "block=0" in result.stdout
    assert "watch=1" in result.stdout


def test_gate_blocks_untracked_claim_after_explicit_scm_commit_authorization(
    tmp_path: Path,
):
    repo = _init_git_repo(tmp_path)
    _write_claim(
        repo,
        "CLAIM-1",
        persistence={
            "mode": "scm_commit",
            "scm_commit_authorized": True,
        },
    )

    result = _run_gate(repo)

    assert result.returncode == 1
    assert "task-claim:authorized-commit-not-persisted" in result.stdout
    assert "block=1" in result.stdout


def test_gate_blocks_staged_only_claim_after_explicit_scm_commit_authorization(
    tmp_path: Path,
):
    repo = _init_git_repo(tmp_path)
    claim_path = _write_claim(
        repo,
        "CLAIM-1",
        persistence={
            "mode": "scm_commit",
            "scm_commit_authorized": True,
        },
    )
    _git(repo, "add", claim_path.relative_to(repo).as_posix())

    result = _run_gate(repo)

    assert result.returncode == 1
    assert "task-claim:authorized-commit-not-persisted" in result.stdout
    assert "block=1" in result.stdout


def test_gate_allows_exact_staged_claim_only_inside_live_commit_transaction(
    tmp_path: Path,
):
    repo = _init_git_repo(tmp_path)
    claim_path = _write_claim(
        repo,
        "CLAIM-1",
        persistence={
            "mode": "scm_commit",
            "scm_commit_authorized": True,
        },
    )
    _git(repo, "add", claim_path.relative_to(repo).as_posix())
    env, _record = _transaction_env(repo, claim_path)

    result = _run_gate(repo, env=env)

    assert result.returncode == 0, result.stdout
    assert "task-claim:authorized-commit-transaction" in result.stdout
    assert "block=0" in result.stdout


def test_gate_rejects_ambient_transaction_marker_without_private_record(
    tmp_path: Path,
):
    repo = _init_git_repo(tmp_path)
    claim_path = _write_claim(
        repo,
        "CLAIM-1",
        persistence={
            "mode": "scm_commit",
            "scm_commit_authorized": True,
        },
    )
    _git(repo, "add", claim_path.relative_to(repo).as_posix())
    env, _record = _transaction_env(repo, claim_path, persist_record=False)

    result = _run_gate(repo, env=env)

    assert result.returncode == 1
    assert "task-claim:authorized-commit-not-persisted" in result.stdout


def test_gate_rejects_malformed_transaction_marker(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    claim_path = _write_claim(
        repo,
        "CLAIM-1",
        persistence={
            "mode": "scm_commit",
            "scm_commit_authorized": True,
        },
    )
    _git(repo, "add", claim_path.relative_to(repo).as_posix())
    env = dict(os.environ)
    env[TRANSACTION_ENV] = "{not-json"

    result = _run_gate(repo, env=env)

    assert result.returncode == 1
    assert "task-claim:authorized-commit-not-persisted" in result.stdout


@pytest.mark.parametrize(
    ("case", "marker_kwargs"),
    [
        ("wrong-root", {"root_value": "/tmp/not-this-repository"}),
        (
            "wrong-path",
            {"claim_paths": ["agents/runtime/task_claims/CLAIM-other.json"]},
        ),
        ("dead-owner", {"owner_pid": 99999999}),
        ("wrong-head", {"head": "0" * 40}),
    ],
)
def test_gate_rejects_mismatched_commit_transaction(
    tmp_path: Path,
    case: str,
    marker_kwargs: dict[str, object],
):
    repo = _init_git_repo(tmp_path)
    claim_path = _write_claim(
        repo,
        "CLAIM-1",
        persistence={
            "mode": "scm_commit",
            "scm_commit_authorized": True,
        },
    )
    _git(repo, "add", claim_path.relative_to(repo).as_posix())
    env, _record = _transaction_env(repo, claim_path, **marker_kwargs)

    result = _run_gate(repo, env=env)

    assert result.returncode == 1, case
    assert "task-claim:authorized-commit-not-persisted" in result.stdout


@pytest.mark.parametrize(
    "case",
    ["wrong-index", "wrong-ref", "wrong-tree", "wrong-blob", "wrong-mode"],
)
def test_gate_rejects_transaction_identity_and_oid_mismatch(
    tmp_path: Path,
    case: str,
):
    repo = _init_git_repo(tmp_path)
    claim_path = _write_claim(
        repo,
        "CLAIM-1",
        persistence={
            "mode": "scm_commit",
            "scm_commit_authorized": True,
        },
    )
    env, record = _transaction_env(repo, claim_path)
    payload = json.loads(env[TRANSACTION_ENV])
    if case == "wrong-index":
        payload["index"] = str(repo / ".git" / "index")
    elif case == "wrong-ref":
        payload["ref"] = "refs/heads/not-current"
    elif case == "wrong-tree":
        payload["tree"] = "0" * 40
    elif case == "wrong-blob":
        payload["artifacts"][0]["oid"] = "0" * 40
    else:
        payload["artifacts"][0]["mode"] = "100755"
    env = _rewrite_transaction_marker(env, record, payload)

    result = _run_gate(repo, env=env)

    assert result.returncode == 1, case
    assert "task-claim:authorized-commit-not-persisted" in result.stdout


@pytest.mark.parametrize("case", ["removed-claim", "extra-path"])
def test_gate_rejects_private_index_tree_mutation(
    tmp_path: Path,
    case: str,
):
    repo = _init_git_repo(tmp_path)
    claim_path = _write_claim(
        repo,
        "CLAIM-1",
        persistence={
            "mode": "scm_commit",
            "scm_commit_authorized": True,
        },
    )
    env, _record = _transaction_env(repo, claim_path)
    if case == "removed-claim":
        command = [
            "git",
            "-C",
            str(repo),
            "update-index",
            "--force-remove",
            "--",
            claim_path.relative_to(repo).as_posix(),
        ]
    else:
        (repo / "STATUS.md").write_text(
            "## Handoff Checklist\n- changed outside the transaction\n",
            encoding="utf-8",
        )
        command = ["git", "-C", str(repo), "add", "--", "STATUS.md"]
    subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    result = _run_gate(repo, env=env)

    assert result.returncode == 1, case
    assert "task-claim:authorized-commit-not-persisted" in result.stdout


def test_gate_rejects_marker_that_omits_changed_sidecar(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    claim_path = _write_claim(
        repo,
        "CLAIM-1",
        persistence={
            "mode": "scm_commit",
            "scm_commit_authorized": True,
        },
    )
    handoff = claim_path.with_name("CLAIM-1.handoff.md")
    log = claim_path.with_name("CLAIM-1.log.md")
    handoff.write_text("# Handoff\n", encoding="utf-8")
    log.write_text("# Log\n", encoding="utf-8")
    env, record = _transaction_env(
        repo,
        claim_path,
        artifact_paths=[claim_path, handoff, log],
    )
    payload = json.loads(env[TRANSACTION_ENV])
    payload["artifacts"] = [
        artifact
        for artifact in payload["artifacts"]
        if artifact["path"] != log.relative_to(repo).as_posix()
    ]
    env = _rewrite_transaction_marker(env, record, payload)

    result = _run_gate(repo, env=env)

    assert result.returncode == 1
    assert "task-claim:authorized-commit-not-persisted" in result.stdout


def test_gate_rejects_transaction_without_private_index_or_with_worktree_mismatch(
    tmp_path: Path,
):
    repo = _init_git_repo(tmp_path)
    claim_path = _write_claim(
        repo,
        "CLAIM-1",
        persistence={
            "mode": "scm_commit",
            "scm_commit_authorized": True,
        },
    )
    env, _record = _transaction_env(repo, claim_path)
    missing_private_index_env = dict(env)
    missing_private_index_env.pop("GIT_INDEX_FILE")
    missing_private_index = _run_gate(repo, env=missing_private_index_env)
    assert missing_private_index.returncode == 1

    payload = json.loads(claim_path.read_text(encoding="utf-8"))
    payload["status_text"] = "changed after private tree was sealed"
    claim_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    mismatched = _run_gate(repo, env=env)
    assert mismatched.returncode == 1
    assert "task-claim:authorized-commit-not-persisted" in mismatched.stdout


def test_transaction_marker_does_not_upgrade_working_tree_persistence(
    tmp_path: Path,
):
    repo = _init_git_repo(tmp_path)
    claim_path = _write_claim(
        repo,
        "CLAIM-1",
        persistence={
            "mode": "working_tree",
            "scm_commit_authorized": False,
        },
    )
    _git(repo, "add", claim_path.relative_to(repo).as_posix())
    env, _record = _transaction_env(repo, claim_path)

    result = _run_gate(repo, env=env)

    assert result.returncode == 0, result.stdout
    assert "task-claim:working-tree-persistence" in result.stdout
    assert "task-claim:authorized-commit-transaction" not in result.stdout


@pytest.mark.parametrize(
    "persistence",
    [
        None,
        {},
        {"mode": "working_tree", "scm_commit_authorized": True},
        {"mode": "scm_commit", "scm_commit_authorized": False},
        {"mode": "unknown", "scm_commit_authorized": False},
    ],
)
def test_gate_blocks_ambiguous_or_inconsistent_untracked_claim_persistence(
    tmp_path: Path,
    persistence: object,
):
    repo = _init_git_repo(tmp_path)
    overrides = {} if persistence is None else {"persistence": persistence}
    _write_claim(repo, "CLAIM-1", **overrides)

    result = _run_gate(repo)

    assert result.returncode == 1
    assert "task-claim:claim-not-committed" in result.stdout


def test_gate_exempts_spike_marker_worktree_with_watch_note(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    worktree = _add_task_worktree(repo)
    (worktree / "SPIKE").write_text("experimental spike worktree\n", encoding="utf-8")
    (worktree / "wip.txt").write_text("spike experiment in flight\n", encoding="utf-8")

    result = _run_gate(repo)

    assert result.returncode == 0, result.stdout
    assert "worktree:spike-exempt" in result.stdout
    assert "worktree:missing-claim" not in result.stdout
    assert "block=0" in result.stdout


def test_gate_exempts_spike_tagged_claim_worktree_with_watch_note(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    worktree = _add_task_worktree(repo, name="TASK-AR-901", branch="claude/task-ar-901-spike")
    (worktree / "wip.txt").write_text("spike experiment in flight\n", encoding="utf-8")
    _write_claim(
        repo,
        "CLAIM-1",
        task_id="TASK-AR-901",
        worktree_path=".worktrees/TASK-AR-901",
        branch="claude/task-ar-901-spike",
        status="released",
        tags=["spike"],
        skip_worktree_marker=True,
    )
    _git(repo, "add", "agents")
    _git(repo, "commit", "-m", "spike claim")

    result = _run_gate(repo)

    assert result.returncode == 0, result.stdout
    assert "worktree:spike-exempt" in result.stdout
    assert "worktree:missing-claim" not in result.stdout


def test_gate_caps_missing_claim_at_watch_when_run_from_linked_worktree(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    worktree = _add_task_worktree(repo)
    (worktree / "wip.txt").write_text("work whose claim may postdate this snapshot\n", encoding="utf-8")

    result = _run_gate(worktree)

    assert result.returncode == 0, result.stdout
    assert "worktree:missing-claim" in result.stdout
    assert "block=0" in result.stdout
    assert "snapshot may predate the claim commit" in result.stdout


def test_gate_resolves_claim_worktree_path_against_primary_checkout(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    _write_claim(
        repo,
        "CLAIM-1",
        task_id="TASK-AR-900",
        worktree_path=".worktrees/TASK-AR-900",
        branch="claude/task-ar-900-demo",
        skip_worktree_marker=True,
    )
    _git(repo, "add", "agents")
    _git(repo, "commit", "-m", "open claim before worktree")
    worktree = _add_task_worktree(repo, name="TASK-AR-900", branch="claude/task-ar-900-demo")

    result = _run_gate(worktree)

    assert result.returncode == 0, result.stdout
    assert "task-claim:worktree-path-missing" not in result.stdout
    assert "findings=0" in result.stdout
