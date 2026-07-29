"""Managed claim-time risk classification for the security-service profile."""
from __future__ import annotations

import fnmatch
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .config import load_config

POLICY_SCHEMA = "agent-runtime-security-service-policy/v1"
RISK_CLASSES = (
    "secrets",
    "auth",
    "migration",
    "production_external_effect",
)
ACTIVE_CLAIM_STATUSES = frozenset(
    {"assigned", "claimed", "in_progress", "review", "waiting_review", "working"}
)

MANAGED_POLICY: dict[str, Any] = {
    "schema": POLICY_SCHEMA,
    "risk_classes": {
        "secrets": {
            "patterns": [
                ".env",
                ".env.*",
                "**/.env",
                "**/.env.*",
                "**/secrets/**",
                "**/credentials/**",
                "**/vault/**",
                "**/*.pem",
                "**/*.key",
                "**/credentials.json",
            ],
            "exclude": [
                ".env.example",
                "**/.env.example",
                "**/*.example",
            ],
            "required": {
                "risk_tier": ["high", "critical"],
                "security_sensitive": True,
                "approval_required": True,
                "escalation_triggers": ["security"],
                "sections": ["Security Controls"],
            },
        },
        "auth": {
            "patterns": [
                "auth/**",
                "**/auth/**",
                "**/oauth/**",
                "**/authentication/**",
                "**/authorization/**",
                "**/rbac/**",
                "auth.py",
                "**/auth.py",
                "**/authentication.py",
                "**/authorization.py",
                "**/permissions.py",
            ],
            "exclude": [],
            "required": {
                "risk_tier": ["high", "critical"],
                "security_sensitive": True,
                "approval_required": False,
                "escalation_triggers": ["security", "data_integrity"],
                "sections": ["Security Controls"],
            },
        },
        "migration": {
            "patterns": [
                "migrations/**",
                "**/migrations/**",
                "migration/**",
                "**/migration/**",
                "**/migration*.py",
                "**/migrate*.py",
                "db/migrate/**",
                "**/db/migrate/**",
            ],
            "exclude": [],
            "required": {
                "risk_tier": ["high", "critical"],
                "security_sensitive": False,
                "approval_required": False,
                "escalation_triggers": ["data_integrity", "external_effect"],
                "sections": ["Rollback"],
            },
        },
        "production_external_effect": {
            "patterns": [
                "deploy/**",
                "**/deploy/**",
                "deployment/**",
                "**/deployment/**",
                "infra/production/**",
                "**/infra/production/**",
                "ops/production/**",
                "**/ops/production/**",
                "scripts/deploy*.py",
                ".github/workflows/deploy*.yml",
                ".github/workflows/deploy*.yaml",
            ],
            "exclude": [],
            "required": {
                "risk_tier": ["high", "critical"],
                "security_sensitive": False,
                "approval_required": True,
                "escalation_triggers": ["external_effect"],
                "sections": ["External Effect Boundary"],
            },
        },
    },
}

__all__ = [
    "MANAGED_POLICY",
    "POLICY_SCHEMA",
    "RiskClassification",
    "SecurityFinding",
    "SecurityPolicyError",
    "SecurityReport",
    "analyze_active_claims",
    "analyze_unit",
    "classify_targets",
    "load_managed_policy",
]


class SecurityPolicyError(ValueError):
    """The managed policy or unit envelope is malformed."""


@dataclass(frozen=True)
class RiskClassification:
    path: str
    risk_class: str
    reason: str


@dataclass(frozen=True)
class SecurityFinding:
    path: str
    risk_class: str
    requirement: str
    detail: str


@dataclass(frozen=True)
class SecurityReport:
    status: str
    unit_spec: str
    classifications: tuple[RiskClassification, ...] = ()
    findings: tuple[SecurityFinding, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "unit_spec": self.unit_spec,
            "classifications": [asdict(item) for item in self.classifications],
            "findings": [asdict(item) for item in self.findings],
        }


def managed_policy_path() -> Path:
    return (
        Path(__file__).resolve().parent
        / "templates"
        / "project"
        / "agents"
        / "project"
        / "SECURITY-SERVICE-POLICY.json"
    )


def load_managed_policy(path: str | Path | None = None) -> dict[str, Any]:
    resolved = Path(path).resolve() if path is not None else managed_policy_path()
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SecurityPolicyError("managed security-service policy is unavailable or malformed") from exc
    if payload != MANAGED_POLICY:
        raise SecurityPolicyError("managed security-service policy drift detected")
    return payload


def _safe_target(value: object) -> str:
    if not isinstance(value, str):
        raise SecurityPolicyError("target path must be a string")
    normalized = value.removeprefix("new:").strip().replace("\\", "/")
    path = PurePosixPath(normalized)
    if (
        not normalized
        or normalized.startswith("/")
        or any(part in {"", ".", ".."} for part in path.parts)
        or path.parts[0] == ".git"
    ):
        raise SecurityPolicyError("target path must be safe and repository-relative")
    return path.as_posix()


def _matches(path: str, pattern: str) -> bool:
    if fnmatch.fnmatchcase(path, pattern):
        return True
    if pattern.startswith("**/"):
        return fnmatch.fnmatchcase(path, pattern[3:])
    return False


def _host_risk_paths(root: Path) -> tuple[str, ...]:
    try:
        return tuple(load_config(root).risk_paths)
    except Exception:
        return ()


def classify_targets(
    root: str | Path,
    target_files: Iterable[object],
    *,
    policy_path: str | Path | None = None,
) -> tuple[RiskClassification, ...]:
    """Classify path names only; file contents are never opened."""

    resolved_root = Path(root).resolve()
    policy = load_managed_policy(policy_path)
    classifications: list[RiskClassification] = []
    seen: set[tuple[str, str]] = set()
    host_paths = _host_risk_paths(resolved_root)
    for raw_path in target_files:
        path = _safe_target(raw_path)
        for risk_class in RISK_CLASSES:
            rule = policy["risk_classes"][risk_class]
            excluded = any(_matches(path, pattern) for pattern in rule["exclude"])
            matched = next(
                (
                    pattern
                    for pattern in rule["patterns"]
                    if _matches(path, pattern)
                ),
                None,
            )
            if matched is not None and not excluded:
                key = (path, risk_class)
                if key not in seen:
                    classifications.append(
                        RiskClassification(path, risk_class, f"managed-pattern:{matched}")
                    )
                    seen.add(key)
        if any(path == risk_path or path.startswith(risk_path.rstrip("/") + "/") for risk_path in host_paths):
            key = (path, "production_external_effect")
            if key not in seen:
                classifications.append(
                    RiskClassification(
                        path,
                        "production_external_effect",
                        "host-risk-path",
                    )
                )
                seen.add(key)
    return tuple(
        sorted(
            classifications,
            key=lambda item: (item.path, item.risk_class, item.reason),
        )
    )


def _parse_scalar(value: str) -> object:
    normalized = value.strip().strip("\"'")
    if normalized.lower() == "true":
        return True
    if normalized.lower() == "false":
        return False
    return normalized


def _unit_document(path: Path) -> tuple[dict[str, object], set[str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise SecurityPolicyError("unit specification is unavailable") from exc
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SecurityPolicyError("unit specification has no frontmatter")
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration as exc:
        raise SecurityPolicyError("unit specification frontmatter is unterminated") from exc

    metadata: dict[str, object] = {}
    current_list: str | None = None
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - ") and current_list is not None:
            value = _parse_scalar(line[4:])
            assert isinstance(metadata[current_list], list)
            metadata[current_list].append(value)
            continue
        if line.startswith(" ") or ":" not in line:
            current_list = None
            continue
        key, raw = line.split(":", 1)
        key = key.strip()
        if raw.strip():
            metadata[key] = _parse_scalar(raw)
            current_list = None
        else:
            metadata[key] = []
            current_list = key
    sections = {
        match.group(1).strip().casefold()
        for line in lines[end + 1 :]
        if (match := re.match(r"^##\s+(.+?)\s*$", line))
    }
    return metadata, sections


def _list_value(metadata: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = metadata.get(key, ())
    if isinstance(value, list):
        return tuple(str(item).strip() for item in value if str(item).strip())
    if isinstance(value, str) and value.strip():
        return (value.strip(),)
    return ()


def _requirement_findings(
    classification: RiskClassification,
    metadata: Mapping[str, object],
    sections: set[str],
    required: Mapping[str, object],
) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []

    allowed_tiers = tuple(str(item) for item in required["risk_tier"])
    if str(metadata.get("risk_tier") or "").strip().lower() not in allowed_tiers:
        findings.append(
            SecurityFinding(
                classification.path,
                classification.risk_class,
                "risk_tier",
                f"risk_tier must be one of {','.join(allowed_tiers)}",
            )
        )
    if required.get("security_sensitive") is True and metadata.get("security_sensitive") is not True:
        findings.append(
            SecurityFinding(
                classification.path,
                classification.risk_class,
                "security_sensitive",
                "security_sensitive must be true",
            )
        )
    if required.get("approval_required") is True and metadata.get("approval_required") is not True:
        findings.append(
            SecurityFinding(
                classification.path,
                classification.risk_class,
                "approval_required",
                "approval_required must be true",
            )
        )

    triggers = set(_list_value(metadata, "escalation_triggers"))
    for trigger in required["escalation_triggers"]:
        if trigger not in triggers:
            findings.append(
                SecurityFinding(
                    classification.path,
                    classification.risk_class,
                    f"escalation_trigger:{trigger}",
                    f"escalation_triggers must include {trigger}",
                )
            )
    for section in required["sections"]:
        if str(section).casefold() not in sections:
            findings.append(
                SecurityFinding(
                    classification.path,
                    classification.risk_class,
                    f"section:{section}",
                    f"unit must include ## {section}",
                )
            )
    return findings


def analyze_unit(
    root: str | Path,
    unit_spec: str | Path,
    *,
    target_files: Iterable[object] | None = None,
    policy_path: str | Path | None = None,
) -> SecurityReport:
    resolved_root = Path(root).resolve()
    spec = Path(unit_spec)
    if not spec.is_absolute():
        spec = resolved_root / spec
    metadata, sections = _unit_document(spec)
    if isinstance(target_files, (str, bytes)):
        raise SecurityPolicyError("target_files must be a list of repository-relative paths")
    targets = (
        tuple(target_files)
        if target_files is not None
        else _list_value(metadata, "target_files")
    )
    classifications = classify_targets(
        resolved_root,
        targets,
        policy_path=policy_path,
    )
    policy = load_managed_policy(policy_path)
    findings: list[SecurityFinding] = []
    for classification in classifications:
        required = policy["risk_classes"][classification.risk_class]["required"]
        findings.extend(
            _requirement_findings(classification, metadata, sections, required)
        )
    return SecurityReport(
        status="pass" if not findings else "block",
        unit_spec=spec.relative_to(resolved_root).as_posix()
        if spec.is_relative_to(resolved_root)
        else str(spec),
        classifications=classifications,
        findings=tuple(findings),
    )


def analyze_active_claims(
    root: str | Path,
    *,
    policy_path: str | Path | None = None,
) -> tuple[SecurityReport, ...]:
    resolved_root = Path(root).resolve()
    claim_dir = resolved_root / "agents" / "runtime" / "task_claims"
    reports: list[SecurityReport] = []
    if not claim_dir.is_dir():
        return ()
    for claim_path in sorted(claim_dir.glob("*.json")):
        try:
            claim = json.loads(claim_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if (
            not isinstance(claim, dict)
            or str(claim.get("status") or "").strip().lower()
            not in ACTIVE_CLAIM_STATUSES
        ):
            continue
        unit_spec = str(claim.get("unit_spec") or "").strip()
        if not unit_spec:
            continue
        reports.append(
            analyze_unit(
                resolved_root,
                unit_spec,
                target_files=claim.get("target_files")
                if isinstance(claim.get("target_files"), list)
                else None,
                policy_path=policy_path,
            )
        )
    return tuple(reports)
