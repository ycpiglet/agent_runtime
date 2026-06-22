"""Tests for scripts/role_concentration_gate.py.

TDD-first: these tests are written before the implementation.
All tests use temp directories with synthetic claim JSONs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Allow importing scripts/ directly
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import role_concentration_gate as gate  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_claims_dir(tmp_path: Path) -> Path:
    claims_dir = tmp_path / "agents" / "runtime" / "task_claims"
    claims_dir.mkdir(parents=True)
    return claims_dir


def _write_claim(claims_dir: Path, idx: int, role: str) -> None:
    payload = {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": f"CLAIM-TEST-{idx:04d}",
        "task_id": f"TASK-AR-{idx:04d}",
        "agent_role": role,
        "status": "released",
    }
    (claims_dir / f"CLAIM-TEST-{idx:04d}.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Tests: concentrated set triggers watch finding
# ---------------------------------------------------------------------------


def test_concentrated_set_triggers_watch(tmp_path: Path) -> None:
    """85/112 lead-engineer claims should trigger a watch finding (>0.6 threshold)."""
    claims_dir = _make_claims_dir(tmp_path)
    for i in range(85):
        _write_claim(claims_dir, i, "lead-engineer")
    for i in range(85, 112):
        _write_claim(claims_dir, i, "qa")

    findings = gate.analyze(tmp_path, threshold=0.60)
    watch_codes = [f["code"] for f in findings if f["severity"] == "watch"]
    assert "role-concentration" in watch_codes, (
        "Expected role-concentration watch finding for lead-engineer at 76%"
    )


def test_concentrated_set_exit_zero(tmp_path: Path) -> None:
    """Gate must exit 0 even when watch findings exist (advisory only)."""
    claims_dir = _make_claims_dir(tmp_path)
    for i in range(10):
        _write_claim(claims_dir, i, "lead-engineer")
    rc = gate.main(["--check", "--root", str(tmp_path)])
    assert rc == 0, "Advisory gate must always exit 0"


# ---------------------------------------------------------------------------
# Tests: balanced set is clean
# ---------------------------------------------------------------------------


def test_balanced_set_no_watch(tmp_path: Path) -> None:
    """Evenly distributed roles should produce no role-concentration finding."""
    claims_dir = _make_claims_dir(tmp_path)
    roles = [
        "lead-engineer",
        "reviewer",
        "independent-auditor",
        "qa",
        "council",
        "skeptic",
        "progress-scout",
        "scribe",
    ]
    for i, role in enumerate(roles):
        for j in range(5):
            _write_claim(claims_dir, i * 10 + j, role)

    findings = gate.analyze(tmp_path, threshold=0.60)
    concentration_findings = [
        f for f in findings if f["code"] == "role-concentration"
    ]
    assert not concentration_findings, (
        "Balanced role distribution should not trigger role-concentration finding"
    )


# ---------------------------------------------------------------------------
# Tests: dormant review-role detection
# ---------------------------------------------------------------------------


def test_dormant_review_roles_trigger_watch(tmp_path: Path) -> None:
    """Zero claims for any configured review/verify role should emit a watch finding."""
    claims_dir = _make_claims_dir(tmp_path)
    # Only lead-engineer claims; no reviewer, independent-auditor, etc.
    for i in range(10):
        _write_claim(claims_dir, i, "lead-engineer")

    findings = gate.analyze(
        tmp_path,
        threshold=0.60,
        review_roles={"reviewer", "independent-auditor", "qa"},
    )
    dormant_findings = [f for f in findings if f["code"] == "dormant-review-role"]
    assert dormant_findings, "Expected dormant-review-role findings when no review roles have claims"

    dormant_roles = {f["role"] for f in dormant_findings}
    assert "reviewer" in dormant_roles
    assert "independent-auditor" in dormant_roles
    assert "qa" in dormant_roles


def test_active_review_roles_no_dormant_finding(tmp_path: Path) -> None:
    """When all review roles have at least one claim, no dormant-review-role finding."""
    claims_dir = _make_claims_dir(tmp_path)
    for i in range(5):
        _write_claim(claims_dir, i, "lead-engineer")
    review_roles = {"reviewer", "independent-auditor", "qa"}
    for j, role in enumerate(review_roles):
        _write_claim(claims_dir, 100 + j, role)

    findings = gate.analyze(
        tmp_path,
        threshold=0.60,
        review_roles=review_roles,
    )
    dormant_findings = [f for f in findings if f["code"] == "dormant-review-role"]
    assert not dormant_findings


# ---------------------------------------------------------------------------
# Tests: empty claims dir
# ---------------------------------------------------------------------------


def test_empty_claims_dir_exit_zero(tmp_path: Path) -> None:
    """No claims -> no findings -> exit 0."""
    _make_claims_dir(tmp_path)
    rc = gate.main(["--check", "--root", str(tmp_path)])
    assert rc == 0


def test_missing_claims_dir_exit_zero(tmp_path: Path) -> None:
    """Missing claims dir -> no findings -> exit 0."""
    rc = gate.main(["--check", "--root", str(tmp_path)])
    assert rc == 0


# ---------------------------------------------------------------------------
# Tests: JSON output
# ---------------------------------------------------------------------------


def test_json_output_schema(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """--json output must be valid JSON with expected schema."""
    claims_dir = _make_claims_dir(tmp_path)
    for i in range(5):
        _write_claim(claims_dir, i, "lead-engineer")

    rc = gate.main(["--check", "--json", "--root", str(tmp_path)])
    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert rc == 0
    assert data["schema"] == "agent-runtime-role-concentration/v1"
    assert "status" in data
    assert "counts" in data
    assert "findings" in data


# ---------------------------------------------------------------------------
# Tests: threshold CLI override
# ---------------------------------------------------------------------------


def test_threshold_override(tmp_path: Path) -> None:
    """--threshold 0.5 triggers on 60% concentration that 0.6 would pass."""
    claims_dir = _make_claims_dir(tmp_path)
    for i in range(6):
        _write_claim(claims_dir, i, "lead-engineer")
    for i in range(6, 10):
        _write_claim(claims_dir, i, "qa")

    # 60% lead-engineer: above 0.5 threshold, below 0.6
    findings_strict = gate.analyze(tmp_path, threshold=0.50)
    findings_loose = gate.analyze(tmp_path, threshold=0.60)

    strict_codes = [f["code"] for f in findings_strict if f["severity"] == "watch"]
    loose_codes = [f["code"] for f in findings_loose if f["severity"] == "watch"]

    assert "role-concentration" in strict_codes
    assert "role-concentration" not in loose_codes
