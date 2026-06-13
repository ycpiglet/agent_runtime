from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "verification_freshness_gate.py"
TEMPLATE_SCRIPT = (
    REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "verification_freshness_gate.py"
)

VERIFIED_AT = "2026-06-13T01:00:00+09:00"
BEFORE_VERIFY = "2026-06-13T00:30:00+09:00"
AFTER_VERIFY = "2026-06-13T02:00:00+09:00"


def _write_task(
    root: Path,
    work_id: str,
    *,
    status: str,
    updated_at: str,
    evidence_refs: list[str],
) -> str:
    tasks_dir = root / "agents" / "lead_engineer" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    refs = "\n".join(f"  - {ref}" for ref in evidence_refs)
    path = tasks_dir / f"{work_id}.md"
    path.write_text(
        "---\n"
        f"id: {work_id}\n"
        f"work_id: {work_id}\n"
        "kind: task\n"
        f"status: {status}\n"
        f"updated_at: {updated_at}\n"
        "evidence_refs:\n"
        f"{refs}\n"
        "---\n"
        f"# {work_id}\n",
        encoding="utf-8",
    )
    return f"agents/lead_engineer/tasks/{work_id}.md"


def _write_evidence(
    root: Path,
    name: str,
    *,
    work_id: str,
    work_path: str,
    freshness: dict | None = None,
    verified_at: str = VERIFIED_AT,
) -> str:
    reviews = root / "reviews"
    reviews.mkdir(parents=True, exist_ok=True)
    payload: dict = {
        "schema": "agent-runtime-work-verification/v1",
        "id": name,
        "work_id": work_id,
        "work_path": work_path,
        "kind": "task",
        "status": "passed",
        "signal": "pass",
        "verified_at": verified_at,
        "verified_by": "tester",
        "command_count": 0,
        "commands": [],
    }
    if freshness is not None:
        payload["freshness"] = freshness
    (reviews / f"{name}.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return f"reviews/{name}.json"


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_gate(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _report(result: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(result.stdout)


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_fresh_record_passes_until_tracked_input_moves(tmp_path: Path) -> None:
    source = tmp_path / "scripts" / "example.py"
    source.parent.mkdir(parents=True)
    source.write_text("print('v1')\n", encoding="utf-8")
    work_path = _write_task(
        tmp_path,
        "TASK-T-001",
        status="in_progress",
        updated_at=VERIFIED_AT,
        evidence_refs=["reviews/VERIFY-fresh.json"],
    )
    _write_evidence(
        tmp_path,
        "VERIFY-fresh",
        work_id="TASK-T-001",
        work_path=work_path,
        freshness={"source_paths": [{"path": "scripts/example.py", "sha256": _sha256(source)}]},
    )

    result = _run_gate(tmp_path, "--check", "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    report = _report(result)
    assert report["schema"] == "agent-runtime-verification-freshness/v1"
    assert report["status"] == "pass"
    assert report["counts"]["fresh"] == 1
    assert report["counts"]["stale"] == 0
    record = report["records"][0]
    assert record["freshness"] == "fresh"
    assert record["severity"] == "ok"
    assert record["reasons"] == []


def test_evidence_goes_stale_after_referenced_source_changes(tmp_path: Path) -> None:
    source = tmp_path / "scripts" / "example.py"
    source.parent.mkdir(parents=True)
    source.write_text("print('v1')\n", encoding="utf-8")
    work_path = _write_task(
        tmp_path,
        "TASK-T-002",
        status="in_progress",
        updated_at=VERIFIED_AT,
        evidence_refs=["reviews/VERIFY-stale.json"],
    )
    _write_evidence(
        tmp_path,
        "VERIFY-stale",
        work_id="TASK-T-002",
        work_path=work_path,
        freshness={"source_paths": [{"path": "scripts/example.py", "sha256": _sha256(source)}]},
    )
    source.write_text("print('v2 changed after verification')\n", encoding="utf-8")

    result = _run_gate(tmp_path, "--check", "--json")

    assert result.returncode == 1, result.stdout + result.stderr
    report = _report(result)
    assert report["status"] == "fail"
    assert report["counts"]["block"] == 1
    record = report["records"][0]
    assert record["freshness"] == "stale"
    assert record["severity"] == "block"
    assert record["evidence_ref"] == "reviews/VERIFY-stale.json"
    assert record["work_id"] == "TASK-T-002"
    codes = {reason["code"] for reason in record["reasons"]}
    assert "source-changed" in codes
    sources = {reason["source"] for reason in record["reasons"]}
    assert "scripts/example.py" in sources


def test_missing_tracked_source_blocks_open_task(tmp_path: Path) -> None:
    source = tmp_path / "scripts" / "example.py"
    source.parent.mkdir(parents=True)
    source.write_text("print('v1')\n", encoding="utf-8")
    work_path = _write_task(
        tmp_path,
        "TASK-T-003",
        status="in_progress",
        updated_at=VERIFIED_AT,
        evidence_refs=["reviews/VERIFY-missing.json"],
    )
    _write_evidence(
        tmp_path,
        "VERIFY-missing",
        work_id="TASK-T-003",
        work_path=work_path,
        freshness={"source_paths": [{"path": "scripts/example.py", "sha256": _sha256(source)}]},
    )
    source.unlink()

    result = _run_gate(tmp_path, "--check", "--json")

    assert result.returncode == 1, result.stdout + result.stderr
    record = _report(result)["records"][0]
    assert record["severity"] == "block"
    assert any(reason["code"] == "source-missing" for reason in record["reasons"])


def test_stale_evidence_on_completed_task_is_watch_only(tmp_path: Path) -> None:
    source = tmp_path / "scripts" / "example.py"
    source.parent.mkdir(parents=True)
    source.write_text("print('v1')\n", encoding="utf-8")
    work_path = _write_task(
        tmp_path,
        "TASK-T-004",
        status="completed",
        updated_at=AFTER_VERIFY,
        evidence_refs=["reviews/VERIFY-closed.json"],
    )
    _write_evidence(
        tmp_path,
        "VERIFY-closed",
        work_id="TASK-T-004",
        work_path=work_path,
        freshness={"source_paths": [{"path": "scripts/example.py", "sha256": _sha256(source)}]},
    )
    source.write_text("print('v2 changed after closeout')\n", encoding="utf-8")

    result = _run_gate(tmp_path, "--check", "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    report = _report(result)
    assert report["status"] == "pass"
    record = report["records"][0]
    assert record["freshness"] == "stale"
    assert record["severity"] == "watch"
    assert record["work_open"] is False


def test_legacy_record_without_freshness_block_is_watch_only(tmp_path: Path) -> None:
    work_path = _write_task(
        tmp_path,
        "TASK-T-005",
        status="in_progress",
        updated_at=VERIFIED_AT,
        evidence_refs=["reviews/VERIFY-legacy.json"],
    )
    _write_evidence(
        tmp_path,
        "VERIFY-legacy",
        work_id="TASK-T-005",
        work_path=work_path,
        freshness=None,
    )

    result = _run_gate(tmp_path, "--check", "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    report = _report(result)
    assert report["counts"]["unknown"] == 1
    record = report["records"][0]
    assert record["freshness"] == "unknown"
    assert record["severity"] == "watch"
    assert [reason["code"] for reason in record["reasons"]] == ["freshness-unknown"]


def test_work_item_updated_after_verification_blocks_open_task(tmp_path: Path) -> None:
    source = tmp_path / "scripts" / "example.py"
    source.parent.mkdir(parents=True)
    source.write_text("print('v1')\n", encoding="utf-8")
    work_path = _write_task(
        tmp_path,
        "TASK-T-006",
        status="in_progress",
        updated_at=AFTER_VERIFY,
        evidence_refs=["reviews/VERIFY-moved.json"],
    )
    _write_evidence(
        tmp_path,
        "VERIFY-moved",
        work_id="TASK-T-006",
        work_path=work_path,
        freshness={"source_paths": [{"path": "scripts/example.py", "sha256": _sha256(source)}]},
    )

    result = _run_gate(tmp_path, "--check", "--json")

    assert result.returncode == 1, result.stdout + result.stderr
    record = _report(result)["records"][0]
    assert record["freshness"] == "stale"
    assert record["severity"] == "block"
    assert any(reason["code"] == "work-item-updated-after-verification" for reason in record["reasons"])


def test_commits_touching_tracked_sources_after_commit_ref_mark_stale(tmp_path: Path) -> None:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test")
    source = tmp_path / "scripts" / "example.py"
    source.parent.mkdir(parents=True)
    source.write_text("print('v1')\n", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "baseline")
    commit_ref = subprocess.run(
        ["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.strip()

    work_path = _write_task(
        tmp_path,
        "TASK-T-007",
        status="in_progress",
        updated_at=VERIFIED_AT,
        evidence_refs=["reviews/VERIFY-commit.json"],
    )
    _write_evidence(
        tmp_path,
        "VERIFY-commit",
        work_id="TASK-T-007",
        work_path=work_path,
        freshness={
            "commit_ref": commit_ref,
            "source_paths": [{"path": "scripts/example.py", "sha256": ""}],
        },
    )

    fresh = _run_gate(tmp_path, "--check", "--json")
    assert fresh.returncode == 0, fresh.stdout + fresh.stderr
    assert _report(fresh)["records"][0]["freshness"] == "fresh"

    source.write_text("print('v2')\n", encoding="utf-8")
    _git(tmp_path, "add", "scripts/example.py")
    _git(tmp_path, "commit", "-m", "touch tracked source")

    stale = _run_gate(tmp_path, "--check", "--json")
    assert stale.returncode == 1, stale.stdout + stale.stderr
    record = _report(stale)["records"][0]
    assert record["freshness"] == "stale"
    assert record["severity"] == "block"
    assert any(reason["code"] == "source-commits-after-verification" for reason in record["reasons"])


def test_unresolvable_commit_ref_degrades_to_watch(tmp_path: Path) -> None:
    source = tmp_path / "scripts" / "example.py"
    source.parent.mkdir(parents=True)
    source.write_text("print('v1')\n", encoding="utf-8")
    work_path = _write_task(
        tmp_path,
        "TASK-T-008",
        status="in_progress",
        updated_at=VERIFIED_AT,
        evidence_refs=["reviews/VERIFY-noref.json"],
    )
    _write_evidence(
        tmp_path,
        "VERIFY-noref",
        work_id="TASK-T-008",
        work_path=work_path,
        freshness={
            "commit_ref": "0" * 40,
            "source_paths": [{"path": "scripts/example.py", "sha256": _sha256(source)}],
        },
    )

    result = _run_gate(tmp_path, "--check", "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    record = _report(result)["records"][0]
    assert record["severity"] == "watch"
    assert any(reason["code"] == "commit-ref-unresolvable" for reason in record["reasons"])


def test_claim_update_after_verification_is_advisory_watch_only(tmp_path: Path) -> None:
    source = tmp_path / "scripts" / "example.py"
    source.parent.mkdir(parents=True)
    source.write_text("print('v1')\n", encoding="utf-8")
    work_path = _write_task(
        tmp_path,
        "TASK-T-009",
        status="in_progress",
        updated_at=VERIFIED_AT,
        evidence_refs=["reviews/VERIFY-claim.json"],
    )
    _write_evidence(
        tmp_path,
        "VERIFY-claim",
        work_id="TASK-T-009",
        work_path=work_path,
        freshness={"source_paths": [{"path": "scripts/example.py", "sha256": _sha256(source)}]},
    )
    claims_dir = tmp_path / "agents" / "runtime" / "task_claims"
    claims_dir.mkdir(parents=True)
    (claims_dir / "CLAIM-test.json").write_text(
        json.dumps(
            {
                "claim_id": "CLAIM-test",
                "task_id": "TASK-T-009",
                "unit_id": "",
                "updated_at": AFTER_VERIFY,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = _run_gate(tmp_path, "--check", "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    record = _report(result)["records"][0]
    assert record["freshness"] == "stale"
    assert record["severity"] == "watch"
    assert any(reason["code"] == "claim-updated-after-verification" for reason in record["reasons"])


def test_gate_passes_on_repo_without_evidence(tmp_path: Path) -> None:
    result = _run_gate(tmp_path, "--check")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "verification-freshness-gate: pass" in result.stdout


def test_template_mirror_matches_canonical_script() -> None:
    canonical = SCRIPT.read_text(encoding="utf-8")
    mirror = TEMPLATE_SCRIPT.read_text(encoding="utf-8")

    assert canonical == mirror
