"""Security-service risk classification and claim-envelope tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_runtime import security_service

ROOT = Path(__file__).resolve().parents[1]
ROOT_POLICY = ROOT / "agents" / "project" / "SECURITY-SERVICE-POLICY.json"
TEMPLATE_POLICY = (
    ROOT
    / "src"
    / "agent_runtime"
    / "templates"
    / "project"
    / "agents"
    / "project"
    / "SECURITY-SERVICE-POLICY.json"
)


def _write_config(root: Path, *, risk_paths: tuple[str, ...] = ()) -> None:
    lines = [
        "schema: agent-runtime-config/v2",
        "project: security-test",
        "profiles:",
        "  - security-service",
        "sync:",
        "  mode: check-diff-apply",
        "  allow_silent_overwrite: false",
    ]
    if risk_paths:
        lines.extend(["host:", "  risk_paths:"])
        lines.extend(f"    - {path}" for path in risk_paths)
    (root / "agent_runtime.yml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_policy(root: Path) -> Path:
    path = root / "agents" / "project" / "SECURITY-SERVICE-POLICY.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(ROOT_POLICY.read_text(encoding="utf-8"), encoding="utf-8")
    return path


def _write_unit(
    root: Path,
    *,
    targets: tuple[str, ...],
    risk_tier: str = "low",
    security_sensitive: bool = False,
    approval_required: bool = False,
    triggers: tuple[str, ...] = (),
    sections: tuple[str, ...] = (),
) -> Path:
    path = root / "agents" / "lead_engineer" / "tasks" / "units" / "TASK-1" / "UNIT-TASK-1-001.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "unit_id: UNIT-TASK-1-001",
        "task_id: TASK-1",
        f"risk_tier: {risk_tier}",
        f"security_sensitive: {str(security_sensitive).lower()}",
        f"approval_required: {str(approval_required).lower()}",
        "escalation_triggers:",
    ]
    lines.extend(f"  - {trigger}" for trigger in triggers)
    lines.append("target_files:")
    lines.extend(f"  - {target}" for target in targets)
    lines.extend(["---", "", "# Unit", ""])
    for section in sections:
        lines.extend([f"## {section}", "", "Bounded test contract.", ""])
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def test_root_template_and_package_policy_are_exact_mirrors() -> None:
    root_payload = json.loads(ROOT_POLICY.read_text(encoding="utf-8"))
    template_payload = json.loads(TEMPLATE_POLICY.read_text(encoding="utf-8"))
    assert root_payload == template_payload == security_service.MANAGED_POLICY


def test_each_risk_class_maps_to_the_registered_contract(tmp_path) -> None:
    _write_config(tmp_path, risk_paths=("services/payment",))
    policy = _write_policy(tmp_path)
    unit = _write_unit(
        tmp_path,
        targets=(
            ".env.production",
            ".env.example",
            "src/auth/session.py",
            "db/migrations/001_add_user.py",
            "services/payment/client.py",
        ),
    )

    report = security_service.analyze_unit(
        tmp_path,
        unit,
        policy_path=policy,
    )

    by_class = {item.risk_class for item in report.classifications}
    assert by_class == {
        "secrets",
        "auth",
        "migration",
        "production_external_effect",
    }
    assert all(item.path != ".env.example" for item in report.classifications)
    requirements = {
        (finding.risk_class, finding.requirement) for finding in report.findings
    }
    assert ("secrets", "approval_required") in requirements
    assert ("secrets", "security_sensitive") in requirements
    assert ("auth", "escalation_trigger:data_integrity") in requirements
    assert ("migration", "section:Rollback") in requirements
    assert (
        "production_external_effect",
        "section:External Effect Boundary",
    ) in requirements
    assert report.status == "block"


def test_fully_declared_cross_risk_unit_passes(tmp_path) -> None:
    _write_config(tmp_path, risk_paths=("services/payment",))
    policy = _write_policy(tmp_path)
    unit = _write_unit(
        tmp_path,
        targets=(
            ".env.production",
            "src/auth/session.py",
            "db/migrations/001_add_user.py",
            "services/payment/client.py",
        ),
        risk_tier="high",
        security_sensitive=True,
        approval_required=True,
        triggers=("security", "data_integrity", "external_effect"),
        sections=("Security Controls", "Rollback", "External Effect Boundary"),
    )

    report = security_service.analyze_unit(
        tmp_path,
        unit,
        policy_path=policy,
    )

    assert report.status == "pass"
    assert report.findings == ()
    assert len(report.classifications) == 4


def test_classifier_never_reads_target_contents(
    tmp_path, monkeypatch
) -> None:
    _write_config(tmp_path)
    policy = _write_policy(tmp_path)
    unit = _write_unit(
        tmp_path,
        targets=("src/auth/session.py",),
        risk_tier="high",
        security_sensitive=True,
        triggers=("security", "data_integrity"),
        sections=("Security Controls",),
    )
    target = tmp_path / "src" / "auth" / "session.py"
    target.parent.mkdir(parents=True)
    target.write_text("PRODUCTION_SECRET=must-not-be-read\n", encoding="utf-8")
    original = Path.read_text

    def guarded_read(path: Path, *args, **kwargs):
        if path.resolve() == target.resolve():
            raise AssertionError("risk classifier opened target contents")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded_read)
    report = security_service.analyze_unit(
        tmp_path,
        unit,
        policy_path=policy,
    )
    serialized = json.dumps(report.to_dict())
    assert report.status == "pass"
    assert "must-not-be-read" not in serialized
    assert "PRODUCTION_SECRET" not in serialized


def test_policy_drift_fails_closed(tmp_path) -> None:
    _write_config(tmp_path)
    policy = _write_policy(tmp_path)
    payload = json.loads(policy.read_text(encoding="utf-8"))
    payload["risk_classes"]["secrets"]["required"]["approval_required"] = False
    policy.write_text(json.dumps(payload), encoding="utf-8")
    unit = _write_unit(tmp_path, targets=("README.md",))

    with pytest.raises(security_service.SecurityPolicyError, match="drift"):
        security_service.analyze_unit(
            tmp_path,
            unit,
            policy_path=policy,
        )


def test_active_claim_recheck_uses_claim_target_snapshot(tmp_path) -> None:
    _write_config(tmp_path)
    policy = _write_policy(tmp_path)
    unit = _write_unit(
        tmp_path,
        targets=("README.md",),
        risk_tier="high",
        security_sensitive=True,
        approval_required=True,
        triggers=("security",),
        sections=("Security Controls",),
    )
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    claim_dir.mkdir(parents=True)
    (claim_dir / "CLAIM-1.json").write_text(
        json.dumps(
            {
                "status": "claimed",
                "unit_spec": unit.relative_to(tmp_path).as_posix(),
                "target_files": [".env.production"],
            }
        ),
        encoding="utf-8",
    )

    reports = security_service.analyze_active_claims(
        tmp_path,
        policy_path=policy,
    )

    assert len(reports) == 1
    assert reports[0].status == "pass"
    assert reports[0].classifications[0].path == ".env.production"


def test_current_registered_unit_passes_managed_gate() -> None:
    unit = (
        ROOT
        / "agents"
        / "lead_engineer"
        / "tasks"
        / "units"
        / "TASK-AR-647"
        / "UNIT-TASK-AR-647-001.md"
    )
    report = security_service.analyze_unit(
        ROOT,
        unit,
        policy_path=ROOT_POLICY,
    )
    assert report.status == "pass"


def test_data_integrity_is_valid_in_root_and_template_unit_schemas() -> None:
    for path in (
        ROOT / "schemas" / "task-unit.schema.json",
        ROOT
        / "src"
        / "agent_runtime"
        / "templates"
        / "project"
        / "schemas"
        / "task-unit.schema.json",
    ):
        schema = json.loads(path.read_text(encoding="utf-8"))
        enum = schema["properties"]["escalation_triggers"]["items"]["enum"]
        assert "data_integrity" in enum
