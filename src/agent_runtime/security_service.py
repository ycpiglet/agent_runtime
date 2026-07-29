"""Managed claim-time risk classification for the security-service profile."""
from __future__ import annotations

import fnmatch
import json
import os
import re
import stat
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
_TASK_IDENTIFIER = re.compile(r"^TASK-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
_UNIT_FRONTMATTER_KEY = re.compile(r"^[a-z][a-z0-9_]*$")
_RAW_HTML_TAG_START = re.compile(
    r"^ {0,3}<(?P<tag>script|pre|style|textarea)(?=[\t >]|$)",
    re.IGNORECASE,
)
_GENERIC_HTML_TAG_START = re.compile(
    r"^ {0,3}</?[A-Za-z][A-Za-z0-9-]*(?=[\t />]|$)"
)
UNIT_DOCUMENT_MAX_BYTES = 256 * 1024

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
    config_path = root / "agent_runtime.yml"
    try:
        mode = config_path.lstat().st_mode
    except FileNotFoundError:
        return ()
    except OSError:
        raise SecurityPolicyError(
            "host risk-path configuration is unavailable or malformed"
        ) from None
    if (
        stat.S_ISLNK(mode)
        or not stat.S_ISREG(mode)
        or mode & (stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH) == 0
    ):
        raise SecurityPolicyError(
            "host risk-path configuration is unavailable or malformed"
        )
    try:
        return tuple(load_config(root).risk_paths)
    except Exception:
        raise SecurityPolicyError(
            "host risk-path configuration is unavailable or malformed"
        ) from None


def _target_sequence(value: object, field: str) -> tuple[object, ...]:
    if isinstance(value, (str, bytes, Mapping)) or not isinstance(value, Iterable):
        raise SecurityPolicyError(
            f"{field} must be a list of repository-relative paths"
        )
    return tuple(value)


def classify_targets(
    root: str | Path,
    target_files: Iterable[object],
    *,
    policy_path: str | Path | None = None,
) -> tuple[RiskClassification, ...]:
    """Classify path names only; file contents are never opened."""

    resolved_root = Path(root).resolve()
    policy = load_managed_policy(policy_path)
    targets = _target_sequence(target_files, "target_files")
    classifications: list[RiskClassification] = []
    seen: set[tuple[str, str]] = set()
    host_paths = _host_risk_paths(resolved_root)
    for raw_path in targets:
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


def _single_quoted_scalar(value: str) -> str:
    if len(value) < 2 or not value.endswith("'"):
        raise SecurityPolicyError(
            "unit specification contains an unterminated quoted scalar"
        )
    body = value[1:-1]
    decoded: list[str] = []
    index = 0
    while index < len(body):
        if body[index] != "'":
            decoded.append(body[index])
            index += 1
            continue
        if index + 1 >= len(body) or body[index + 1] != "'":
            raise SecurityPolicyError(
                "unit specification contains malformed quoted scalar"
            )
        decoded.append("'")
        index += 2
    return "".join(decoded)


def _parse_scalar(value: str) -> object:
    normalized = value.strip()
    if (
        not normalized
        or normalized != value
        or any(ord(character) < 32 for character in normalized)
    ):
        raise SecurityPolicyError(
            "unit specification contains an unsupported scalar"
        )
    if normalized.startswith('"'):
        try:
            decoded = json.loads(normalized)
        except (json.JSONDecodeError, UnicodeError) as exc:
            raise SecurityPolicyError(
                "unit specification contains malformed quoted scalar"
            ) from exc
        if not isinstance(decoded, str):
            raise SecurityPolicyError(
                "unit specification quoted scalar must be text"
            )
        return decoded
    if normalized.startswith("'"):
        return _single_quoted_scalar(normalized)
    if normalized.endswith(("'", '"')):
        raise SecurityPolicyError(
            "unit specification contains an unmatched quote"
        )
    if (
        normalized[0] in {"!", "&", "*", "|", ">", "{", "}", "[", "]"}
        or re.search(r"(?:^|\s)[!&*](?=\S)", normalized)
        or re.search(r"\s#", normalized)
    ):
        raise SecurityPolicyError(
            "unit specification contains unsupported YAML scalar syntax"
        )
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    return normalized


def _inline_list(value: str) -> list[object]:
    if not value.startswith("[") or not value.endswith("]"):
        raise SecurityPolicyError(
            "unit specification contains malformed inline list"
        )
    body = value[1:-1]
    if not body.strip():
        return []
    items = body.split(",")
    if any(not item.strip() for item in items):
        raise SecurityPolicyError(
            "unit specification contains malformed inline list"
        )
    return [_parse_scalar(item.strip()) for item in items]


def _markdown_sections(lines: list[str]) -> set[str]:
    sections: set[str] = set()
    fence_character: str | None = None
    fence_length = 0
    html_terminator: str | None = None
    html_until_blank = False
    for raw_line in lines:
        if fence_character is not None:
            closing = re.match(
                rf"^ {{0,3}}({re.escape(fence_character)}"
                rf"{{{fence_length},}})\s*$",
                raw_line,
            )
            if closing is not None:
                fence_character = None
                fence_length = 0
            continue

        if html_terminator is not None:
            if html_terminator.casefold() in raw_line.casefold():
                html_terminator = None
            # CommonMark consumes the entire physical line that closes an
            # HTML block. Never reinterpret text after the terminator as a
            # Markdown heading.
            continue
        if html_until_blank:
            if not raw_line.strip():
                html_until_blank = False
            continue

        fence = re.match(r"^ {0,3}(`{3,}|~{3,}).*$", raw_line)
        if fence is not None:
            marker = fence.group(1)
            fence_character = marker[0]
            fence_length = len(marker)
            continue

        stripped = raw_line.lstrip(" ")
        indent = len(raw_line) - len(stripped)
        if indent <= 3:
            if stripped.startswith("<!--"):
                if "-->" not in stripped[4:]:
                    html_terminator = "-->"
                continue
            if stripped.startswith("<![CDATA["):
                if "]]>" not in stripped[len("<![CDATA[") :]:
                    html_terminator = "]]>"
                continue
            if stripped.startswith("<?"):
                if "?>" not in stripped[2:]:
                    html_terminator = "?>"
                continue
            if re.match(r"^<![A-Z]", stripped):
                if ">" not in stripped[2:]:
                    html_terminator = ">"
                continue

            raw_tag = _RAW_HTML_TAG_START.match(raw_line)
            if raw_tag is not None:
                closing_tag = f"</{raw_tag.group('tag')}>"
                if (
                    closing_tag.casefold()
                    not in raw_line[raw_tag.end() :].casefold()
                ):
                    html_terminator = closing_tag
                continue

            # CommonMark block-tag and complete-tag blocks consume through
            # the next blank line. Treat every tag-shaped line at block
            # indentation this way: false negatives are safe at a claim
            # authorization boundary, while a false section is not.
            if _GENERIC_HTML_TAG_START.match(raw_line) is not None:
                html_until_blank = True
                continue

        # Inline or malformed comment syntax cannot make a security heading
        # more trustworthy. Skip the line and retain an unclosed comment
        # state conservatively.
        comment_start = raw_line.find("<!--")
        if comment_start >= 0:
            if "-->" not in raw_line[comment_start + 4 :]:
                html_terminator = "-->"
            continue

        heading = re.match(r"^##\s+(.+?)\s*$", raw_line)
        if heading is not None:
            sections.add(heading.group(1).strip().casefold())
    return sections


def _unit_document(text: str) -> tuple[dict[str, object], set[str]]:
    if "\x00" in text or "\t" in text:
        raise SecurityPolicyError(
            "unit specification contains unsupported characters"
        )
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise SecurityPolicyError("unit specification has no frontmatter")
    try:
        end = next(index for index in range(1, len(lines)) if lines[index] == "---")
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
            raise SecurityPolicyError(
                "unit specification contains unsupported frontmatter structure"
            )
        key, raw = line.split(":", 1)
        if _UNIT_FRONTMATTER_KEY.fullmatch(key) is None:
            raise SecurityPolicyError(
                "unit specification contains malformed frontmatter key"
            )
        if key in metadata:
            raise SecurityPolicyError(
                "unit specification frontmatter contains duplicate fields"
            )
        if raw:
            if not raw.startswith(" ") or not raw[1:]:
                raise SecurityPolicyError(
                    "unit specification contains malformed frontmatter scalar"
                )
            value = raw[1:]
            metadata[key] = (
                _inline_list(value)
                if value.startswith("[")
                else _parse_scalar(value)
            )
            current_list = None
        else:
            metadata[key] = []
            current_list = key
    sections = _markdown_sections(lines[end + 1 :])
    return metadata, sections


def _stat_signature(value: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _bounded_repository_text(
    root: Path,
    relative: PurePosixPath,
    field: str,
) -> tuple[Path, str]:
    current = root
    components: list[tuple[Path, tuple[int, int, int, int, int, int]]] = []
    try:
        root_stat = root.lstat()
        if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
            raise SecurityPolicyError(
                f"{field} is unavailable or not canonical"
            )
        components.append((root, _stat_signature(root_stat)))
        for index, part in enumerate(relative.parts):
            current = current / part
            item_stat = current.lstat()
            final = index == len(relative.parts) - 1
            if (
                stat.S_ISLNK(item_stat.st_mode)
                or (final and not stat.S_ISREG(item_stat.st_mode))
                or (not final and not stat.S_ISDIR(item_stat.st_mode))
            ):
                raise SecurityPolicyError(
                    f"{field} is unavailable or not canonical"
                )
            if final and (
                item_stat.st_size > UNIT_DOCUMENT_MAX_BYTES
                or item_stat.st_mode
                & (stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
                == 0
            ):
                raise SecurityPolicyError(
                    f"{field} is unavailable or outside the managed bound"
                )
            components.append((current, _stat_signature(item_stat)))

        flags = os.O_RDONLY
        flags |= getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        flags |= getattr(os, "O_NONBLOCK", 0)
        descriptor = os.open(current, flags)
        try:
            with os.fdopen(descriptor, "rb") as handle:
                opened_before = os.fstat(handle.fileno())
                payload = handle.read(UNIT_DOCUMENT_MAX_BYTES + 1)
                opened_after = os.fstat(handle.fileno())
        except Exception:
            try:
                os.close(descriptor)
            except OSError:
                pass
            raise

        if (
            not stat.S_ISREG(opened_before.st_mode)
            or _stat_signature(opened_before) != _stat_signature(opened_after)
            or _stat_signature(opened_before) != components[-1][1]
            or len(payload) > UNIT_DOCUMENT_MAX_BYTES
        ):
            raise SecurityPolicyError(
                f"{field} changed while it was read"
            )
        for path, before_signature in components:
            if _stat_signature(path.lstat()) != before_signature:
                raise SecurityPolicyError(
                    f"{field} changed while it was read"
                )
    except SecurityPolicyError:
        raise
    except (OSError, UnicodeError) as exc:
        raise SecurityPolicyError(
            f"{field} is unavailable or not canonical"
        ) from exc
    try:
        return current, payload.decode("utf-8")
    except UnicodeError as exc:
        raise SecurityPolicyError(
            f"{field} is unavailable or malformed"
        ) from exc


def _regular_repository_path(
    root: Path,
    relative: PurePosixPath,
    field: str,
) -> Path:
    current = root
    for index, part in enumerate(relative.parts):
        current = current / part
        try:
            mode = current.lstat().st_mode
        except OSError as exc:
            raise SecurityPolicyError(
                f"{field} is unavailable or not canonical"
            ) from exc
        if stat.S_ISLNK(mode):
            raise SecurityPolicyError(
                f"{field} is unavailable or not canonical"
            )
        final = index == len(relative.parts) - 1
        if final and not stat.S_ISREG(mode):
            raise SecurityPolicyError(
                f"{field} is unavailable or not canonical"
            )
        if not final and not stat.S_ISDIR(mode):
            raise SecurityPolicyError(
                f"{field} is unavailable or not canonical"
            )
    return current


def _canonical_unit_document(
    root: Path,
    unit_spec: str | Path,
    *,
    task_id: str | None,
    unit_id: str | None,
) -> tuple[Path, str, dict[str, object], set[str], str, str]:
    if not isinstance(unit_spec, (str, Path)):
        raise SecurityPolicyError(
            "unit specification must be a canonical repository-relative path"
        )
    raw = str(unit_spec)
    relative = PurePosixPath(raw)
    if (
        not raw
        or raw != raw.strip()
        or "\\" in raw
        or raw.startswith("/")
        or relative.as_posix() != raw
        or any(part in {"", ".", ".."} for part in relative.parts)
        or len(relative.parts) != 6
        or relative.parts[:4]
        != ("agents", "lead_engineer", "tasks", "units")
    ):
        raise SecurityPolicyError(
            "unit specification must be a canonical repository-relative path"
        )

    path_task_id = relative.parts[4]
    filename = relative.parts[5]
    path_unit_id = filename.removesuffix(".md")
    if (
        not filename.endswith(".md")
        or _TASK_IDENTIFIER.fullmatch(path_task_id) is None
        or re.fullmatch(
            rf"UNIT-{re.escape(path_task_id)}-[0-9]{{3}}",
            path_unit_id,
        )
        is None
    ):
        raise SecurityPolicyError(
            "unit specification must be a canonical repository-relative path"
        )
    canonical = (
        f"agents/lead_engineer/tasks/units/{path_task_id}/"
        f"{path_unit_id}.md"
    )
    if raw != canonical:
        raise SecurityPolicyError(
            "unit specification must be a canonical repository-relative path"
        )
    if task_id is not None and task_id != path_task_id:
        raise SecurityPolicyError(
            "unit specification does not match the requested task identity"
        )
    if unit_id is not None and unit_id != path_unit_id:
        raise SecurityPolicyError(
            "unit specification does not match the requested unit identity"
        )

    task_relative = PurePosixPath(
        "agents",
        "lead_engineer",
        "tasks",
        f"{path_task_id}.md",
    )
    _regular_repository_path(root, task_relative, "task specification")
    spec, unit_text = _bounded_repository_text(
        root,
        relative,
        "unit specification",
    )
    metadata, sections = _unit_document(unit_text)
    if (
        metadata.get("task_id") != path_task_id
        or metadata.get("unit_id") != path_unit_id
    ):
        raise SecurityPolicyError(
            "unit frontmatter identity does not match its canonical path"
        )
    return (
        spec,
        canonical,
        metadata,
        sections,
        path_task_id,
        path_unit_id,
    )


def _list_value(metadata: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = metadata.get(key, ())
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return tuple(value)
    return ()


def _requirement_findings(
    classification: RiskClassification,
    metadata: Mapping[str, object],
    sections: set[str],
    required: Mapping[str, object],
) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []

    allowed_tiers = tuple(str(item) for item in required["risk_tier"])
    risk_tier = metadata.get("risk_tier")
    if (
        not isinstance(risk_tier, str)
        or risk_tier not in allowed_tiers
    ):
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
    task_id: str | None = None,
    unit_id: str | None = None,
    target_files: Iterable[object] | None = None,
    policy_path: str | Path | None = None,
) -> SecurityReport:
    resolved_root = Path(root).resolve()
    (
        _spec,
        canonical_spec,
        metadata,
        sections,
        _path_task_id,
        _path_unit_id,
    ) = _canonical_unit_document(
        resolved_root,
        unit_spec,
        task_id=task_id,
        unit_id=unit_id,
    )
    registered_value = metadata.get("target_files")
    if not isinstance(registered_value, list):
        raise SecurityPolicyError(
            "unit target_files must be a list of repository-relative paths"
        )
    registered_targets = _target_sequence(
        registered_value,
        "unit target_files",
    )
    snapshot_targets = (
        _target_sequence(target_files, "claim target_files")
        if target_files is not None
        else ()
    )
    normalized_targets: list[str] = []
    seen_targets: set[str] = set()
    for raw_target in (*registered_targets, *snapshot_targets):
        normalized_target = _safe_target(raw_target)
        if normalized_target not in seen_targets:
            normalized_targets.append(normalized_target)
            seen_targets.add(normalized_target)
    targets = tuple(normalized_targets)
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
        unit_spec=canonical_spec,
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
            raise SecurityPolicyError(
                "claim record is unavailable or malformed"
            ) from None
        if not isinstance(claim, dict):
            raise SecurityPolicyError("claim record is unavailable or malformed")
        if (
            str(claim.get("status") or "").strip().lower()
            not in ACTIVE_CLAIM_STATUSES
        ):
            continue
        unit_value = claim.get("unit_spec")
        if (
            not isinstance(unit_value, str)
            or not unit_value
            or unit_value != unit_value.strip()
        ):
            raise SecurityPolicyError(
                "active claim must reference a registered unit specification"
            )
        unit_spec = unit_value
        task_id = claim.get("task_id")
        unit_id = claim.get("unit_id")
        if (
            not isinstance(task_id, str)
            or not task_id
            or task_id != task_id.strip()
        ):
            raise SecurityPolicyError(
                "active claim must reference a registered task identity"
            )
        if (
            not isinstance(unit_id, str)
            or not unit_id
            or unit_id != unit_id.strip()
        ):
            raise SecurityPolicyError(
                "active claim must reference a registered unit identity"
            )
        snapshot = claim.get("target_files")
        if not isinstance(snapshot, list):
            raise SecurityPolicyError(
                "active claim target_files must be a list of repository-relative paths"
            )
        reports.append(
            analyze_unit(
                resolved_root,
                unit_spec,
                task_id=task_id,
                unit_id=unit_id,
                target_files=snapshot,
                policy_path=policy_path,
            )
        )
    return tuple(reports)
