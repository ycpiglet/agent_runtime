"""Tests for scripts/release_execution_gate.py - parametric version checks."""

from __future__ import annotations

from pathlib import Path

from scripts import release_execution_gate as gate


CURRENT_VERSION = "0.3.0"  # matches pyproject.toml version


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_pyproject(tmp: Path, version: str) -> Path:
    p = tmp / "pyproject.toml"
    _write(p, f'[project]\nname = "agent_runtime"\nversion = "{version}"\n')
    return p


def _make_init(tmp: Path, version: str) -> Path:
    p = tmp / "src" / "agent_runtime" / "__init__.py"
    _write(p, f'__version__ = "{version}"\n')
    return p


def _make_template(tmp: Path) -> Path:
    p = tmp / "agents" / "project" / "RELEASE-GATE-TEMPLATE.yml"
    _write(
        p,
        "release_state: ready\n"
        "release_cause: all_hold_routes_closed_with_evidence\n",
    )
    return p


def _make_plan(tmp: Path, *, target_version: str, owner_approval_status: str = "pending_owner_approval") -> Path:
    p = tmp / "agents" / "project" / "release" / "RELEASE-EXECUTION.yml"
    # Include the REQUIRED_READY_EVIDENCE filenames so the missing-evidence
    # finding does not interfere with our version-specific assertions.
    evidence_lines = "\n".join(
        f"  - {ev}"
        for ev in gate.REQUIRED_READY_EVIDENCE
    )
    _write(
        p,
        f"target_version: {target_version}\n"
        f"target_tag: v{target_version}\n"
        f"owner_approval_status: {owner_approval_status}\n"
        f"execution_status: not_started\n"
        f"ready_evidence:\n{evidence_lines}\n",
    )
    return p


def _version_findings(report: dict) -> list[str]:
    """Extract only version-related findings."""
    return [f for f in report["findings"] if "target_version" in f or "target_tag" in f]


def test_pyproject_version_helper_reads_version(tmp_path: Path) -> None:
    pyproject = _make_pyproject(tmp_path, CURRENT_VERSION)
    assert gate._pyproject_version(pyproject) == CURRENT_VERSION


def test_pyproject_version_helper_missing_file(tmp_path: Path) -> None:
    assert gate._pyproject_version(tmp_path / "nonexistent.toml") == ""


def test_matching_version_produces_no_version_findings(tmp_path: Path) -> None:
    """A plan with target_version == pyproject version generates no version findings."""
    pyproject = _make_pyproject(tmp_path, CURRENT_VERSION)
    init = _make_init(tmp_path, CURRENT_VERSION)
    template = _make_template(tmp_path)
    plan = _make_plan(tmp_path, target_version=CURRENT_VERSION)

    report = gate.evaluate(plan, template, pyproject, init)

    version_issues = _version_findings(report)
    assert version_issues == [], f"Unexpected version findings: {version_issues}"


def test_mismatched_version_blocks_with_finding(tmp_path: Path) -> None:
    """A plan with a different target_version generates a mismatch finding."""
    pyproject = _make_pyproject(tmp_path, CURRENT_VERSION)
    init = _make_init(tmp_path, CURRENT_VERSION)
    template = _make_template(tmp_path)
    # Use an old pinned version - this should trigger the mismatch
    plan = _make_plan(tmp_path, target_version="0.1.8")

    report = gate.evaluate(plan, template, pyproject, init)

    assert any("target_version:mismatch-pyproject" in f for f in report["findings"]), (
        f"Expected mismatch finding, got: {report['findings']}"
    )
    assert report["status"] == "block"


def test_target_tag_mismatch_generates_finding(tmp_path: Path) -> None:
    """A tag that doesn't match 'v'+target_version generates a finding."""
    pyproject = _make_pyproject(tmp_path, CURRENT_VERSION)
    init = _make_init(tmp_path, CURRENT_VERSION)
    template = _make_template(tmp_path)
    plan_path = tmp_path / "agents" / "project" / "release" / "RELEASE-EXECUTION.yml"
    evidence_lines = "\n".join(f"  - {ev}" for ev in gate.REQUIRED_READY_EVIDENCE)
    _write(
        plan_path,
        f"target_version: {CURRENT_VERSION}\n"
        f"target_tag: v0.1.8\n"  # intentionally wrong tag
        f"owner_approval_status: pending_owner_approval\n"
        f"execution_status: not_started\n"
        f"ready_evidence:\n{evidence_lines}\n",
    )

    report = gate.evaluate(plan_path, template, pyproject, init)

    assert any("target_tag:not-v-target-version" in f for f in report["findings"]), (
        f"Expected tag mismatch finding, got: {report['findings']}"
    )


def test_no_hardcoded_018_in_evaluation_logic() -> None:
    """Regression guard: the gate source must not contain '0.1.8' in version checks."""
    source = Path(__file__).resolve().parents[1] / "scripts" / "release_execution_gate.py"
    text = source.read_text(encoding="utf-8")
    # The evaluate() function body starts after _package_versions
    # We simply check the whole file has no version equality check on '0.1.8'
    assert '"0.1.8"' not in text, "Hardcoded '0.1.8' string found in release_execution_gate.py"
    assert "'0.1.8'" not in text, "Hardcoded '0.1.8' string found in release_execution_gate.py"
    assert '"v0.1.8"' not in text, "Hardcoded 'v0.1.8' string found in release_execution_gate.py"
    assert "'v0.1.8'" not in text, "Hardcoded 'v0.1.8' string found in release_execution_gate.py"


def test_approval_routes_unchanged_approved(tmp_path: Path) -> None:
    """The approved route (approved + not_started) yields approved_pending_release_execution when no other findings."""
    pyproject = _make_pyproject(tmp_path, CURRENT_VERSION)
    init = _make_init(tmp_path, CURRENT_VERSION)
    template = _make_template(tmp_path)
    # Create the evidence files so evidence findings don't interfere
    for ev_path in gate.REQUIRED_READY_EVIDENCE:
        _write(tmp_path / ev_path, "evidence\n")
    plan_path = tmp_path / "agents" / "project" / "release" / "RELEASE-EXECUTION.yml"
    evidence_lines = "\n".join(f"  - {ev}" for ev in gate.REQUIRED_READY_EVIDENCE)
    _write(
        plan_path,
        f"target_version: {CURRENT_VERSION}\n"
        f"target_tag: v{CURRENT_VERSION}\n"
        f"owner_approval_status: approved\n"
        f"execution_status: not_started\n"
        f"ready_evidence:\n{evidence_lines}\n",
    )

    report = gate.evaluate(plan_path, template, pyproject, init)

    # The version-related findings should be absent; route should be the approved route
    version_issues = _version_findings(report)
    assert version_issues == [], f"Unexpected version findings: {version_issues}"
    if not report["findings"]:
        assert report["release_route"] == "approved_pending_release_execution"


def test_approval_routes_unchanged_agent_council_approved(tmp_path: Path) -> None:
    """The agent_council_approved + executed route yields release_evidence_ready when no other findings."""
    pyproject = _make_pyproject(tmp_path, CURRENT_VERSION)
    init = _make_init(tmp_path, CURRENT_VERSION)
    # Use release state for executed status
    template_path = tmp_path / "agents" / "project" / "RELEASE-GATE-TEMPLATE.yml"
    _write(
        template_path,
        "release_state: release\n"
        "release_cause: all_hold_routes_closed_with_evidence\n",
    )
    for ev_path in gate.REQUIRED_READY_EVIDENCE:
        _write(tmp_path / ev_path, "evidence\n")
    plan_path = tmp_path / "agents" / "project" / "release" / "RELEASE-EXECUTION.yml"
    evidence_lines = "\n".join(f"  - {ev}" for ev in gate.REQUIRED_READY_EVIDENCE)
    _write(
        plan_path,
        f"target_version: {CURRENT_VERSION}\n"
        f"target_tag: v{CURRENT_VERSION}\n"
        f"owner_approval_status: agent_council_approved\n"
        f"execution_status: executed\n"
        f"ready_evidence:\n{evidence_lines}\n",
    )

    report = gate.evaluate(plan_path, template_path, pyproject, init)

    version_issues = _version_findings(report)
    assert version_issues == [], f"Unexpected version findings: {version_issues}"
    if not report["findings"]:
        assert report["release_route"] == "release_evidence_ready"
