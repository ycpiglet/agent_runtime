#!/usr/bin/env python3
"""Validate sanitized, replayable consumer-pilot evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:
    import pilot_isolation_gate
except ModuleNotFoundError:  # pragma: no cover - supports module-style invocation
    from scripts import pilot_isolation_gate


SCHEMA = "agent-runtime-pilot-evidence/v1"
CONTRACT_SCHEMA = "agent-runtime-pilot-contract/v1"
MIGRATION_SCHEMA = "agent-runtime-migration-pilot-evidence/v1"
MIGRATION_CONTRACT_SCHEMA = "agent-runtime-migration-pilot-contract/v1"
SEAM_LEDGER_SCHEMA = "agent-runtime-migration-seam-ledger/v1"
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTRACT_DIR = ROOT / "tests" / "fixtures" / "pilots" / "contracts"
SHA256_RE = re.compile(r"^(?:sha256:)?[0-9a-f]{64}$")
BARE_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
CLAIM_RE = re.compile(r"^CLAIM-[A-Za-z0-9._-]+$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
TASK_RE = re.compile(r"^TASK-[A-Za-z0-9._-]+$")
UNIT_RE = re.compile(r"^UNIT-TASK-[A-Za-z0-9._-]+$")
CORE_EXTERNAL_EFFECTS = frozenset(
    {
        "publish",
        "deploy",
        "origin_push",
        "host_commit",
        "credential_read",
        "network_delivery",
        "content_mutation",
    }
)
EXPECTED_EXTERNAL_EFFECTS = (
    "publish",
    "deploy",
    "origin_push",
    "host_commit",
    "credential_read",
    "network_delivery",
    "content_mutation",
)
ROUTING_FIELDS = (
    "requested_model_tier",
    "selected_model_tier",
    "resolved_provider_tier",
    "execution_surface",
    "actual_model_status",
    "savings_claim",
)


class ContractRegistryError(ValueError):
    """Raised when a pilot-contract registry is ambiguous or malformed."""


def _finding(code: str, path: str, detail: str) -> dict[str, str]:
    return {"code": code, "path": path, "detail": detail}


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_relative(value: object) -> bool:
    text = str(value or "").strip().replace("\\", "/")
    return bool(
        text
        and not text.startswith("/")
        and not re.match(r"^[A-Za-z]:", text)
        and all(part not in {"", ".", ".."} for part in text.split("/"))
    )


def _valid_sha(value: object) -> bool:
    return bool(SHA256_RE.fullmatch(str(value or "").strip()))


def _semantic_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _absolute_string_paths(value: object, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            findings.extend(_absolute_string_paths(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(_absolute_string_paths(item, f"{path}[{index}]"))
    elif isinstance(value, str):
        text = value.strip().replace("\\", "/")
        if text.startswith("/") or re.match(r"^[A-Za-z]:/", text):
            findings.append(path)
    return findings


def _count(record: dict[str, Any], key: str) -> int | None:
    value = record.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _contract_error(code: str, path: str, detail: str) -> None:
    raise ContractRegistryError(f"{code} {path}: {detail}")


def _contract_int(
    contract: dict[str, Any],
    key: str,
    *,
    minimum: int = 0,
) -> int:
    value = contract.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        _contract_error(
            "invalid-contract-count",
            key,
            f"expected an integer greater than or equal to {minimum}",
        )
    return value


def _validate_execution_contract(
    contract: object,
    source: Path,
) -> dict[str, Any]:
    if not isinstance(contract, dict):
        _contract_error(
            "invalid-contract-root",
            source.name,
            "contract must be a JSON object",
        )
    required_keys = {
        "schema",
        "host",
        "pilot_id",
        "evidence_semantic_sha256",
        "result",
        "baselines",
        "selected_template_files",
        "web_content_incremental_files",
        "content_file_count",
        "post_registration_conflicts",
        "expected_task_count",
        "tasks",
        "findings",
        "verification",
        "required_external_effects",
        "artifact_bindings",
    }
    missing = sorted(required_keys - set(contract))
    unexpected = sorted(set(contract) - required_keys)
    if missing or unexpected:
        detail = []
        if missing:
            detail.append(f"missing={','.join(missing)}")
        if unexpected:
            detail.append(f"unexpected={','.join(unexpected)}")
        _contract_error(
            "invalid-contract-fields",
            source.name,
            "; ".join(detail),
        )
    if contract.get("schema") != CONTRACT_SCHEMA:
        _contract_error(
            "invalid-contract-schema",
            f"{source.name}:schema",
            f"expected {CONTRACT_SCHEMA}",
        )
    for key in ("host", "pilot_id"):
        value = contract.get(key)
        if not isinstance(value, str) or not SLUG_RE.fullmatch(value):
            _contract_error(
                f"invalid-contract-{key.replace('_', '-')}",
                f"{source.name}:{key}",
                "expected a lowercase safe slug",
            )
    if not isinstance(
        contract.get("evidence_semantic_sha256"),
        str,
    ) or not BARE_SHA256_RE.fullmatch(contract["evidence_semantic_sha256"]):
        _contract_error(
            "invalid-contract-semantic-digest",
            f"{source.name}:evidence_semantic_sha256",
            "expected a bare 64-hex SHA-256",
        )
    if contract.get("result") not in {"passed", "blocked"}:
        _contract_error(
            "invalid-contract-result",
            f"{source.name}:result",
            "result must be passed or blocked",
        )

    baselines = contract.get("baselines")
    if not isinstance(baselines, dict) or not {
        "host_commit",
        "runtime_commit",
    }.issubset(baselines):
        _contract_error(
            "invalid-contract-baselines",
            f"{source.name}:baselines",
            "host_commit and runtime_commit are required",
        )
    for key, value in baselines.items():
        if not isinstance(key, str) or not SLUG_RE.fullmatch(key):
            _contract_error(
                "invalid-contract-baseline-name",
                f"{source.name}:baselines",
                "baseline names must be safe slugs",
            )
        if not isinstance(value, str) or not GIT_SHA_RE.fullmatch(value):
            _contract_error(
                "invalid-contract-baseline",
                f"{source.name}:baselines.{key}",
                "expected a full 40-hex git object id",
            )

    selected = _contract_int(contract, "selected_template_files", minimum=1)
    incremental = _contract_int(contract, "web_content_incremental_files")
    if incremental > selected:
        _contract_error(
            "invalid-contract-count",
            f"{source.name}:web_content_incremental_files",
            "incremental files cannot exceed selected files",
        )
    _contract_int(contract, "content_file_count", minimum=1)
    expected_task_count = _contract_int(contract, "expected_task_count", minimum=1)

    conflict_paths = contract.get("post_registration_conflicts")
    if (
        not isinstance(conflict_paths, list)
        or any(
            not isinstance(path, str) or not _safe_relative(path)
            for path in conflict_paths
        )
        or len(set(conflict_paths)) != len(conflict_paths)
    ):
        _contract_error(
            "invalid-contract-conflict-paths",
            f"{source.name}:post_registration_conflicts",
            "paths must be unique safe relative strings",
        )

    tasks = contract.get("tasks")
    if not isinstance(tasks, dict) or len(tasks) != expected_task_count:
        _contract_error(
            "invalid-contract-tasks",
            f"{source.name}:tasks",
            "task map size must equal expected_task_count",
        )
    task_fields = {"unit_id", "claim_id", "task_status", "claim_status"}
    for task_id, task in tasks.items():
        if not isinstance(task_id, str) or not TASK_RE.fullmatch(task_id):
            _contract_error(
                "invalid-contract-task-id",
                f"{source.name}:tasks",
                "task ids must use TASK-* form",
            )
        if not isinstance(task, dict) or set(task) != task_fields:
            _contract_error(
                "invalid-contract-task-fields",
                f"{source.name}:tasks.{task_id}",
                "task contract fields are not exact",
            )
        if not UNIT_RE.fullmatch(str(task.get("unit_id") or "")):
            _contract_error(
                "invalid-contract-unit-id",
                f"{source.name}:tasks.{task_id}.unit_id",
                "unit id must use UNIT-TASK-* form",
            )
        if not CLAIM_RE.fullmatch(str(task.get("claim_id") or "")):
            _contract_error(
                "invalid-contract-claim-id",
                f"{source.name}:tasks.{task_id}.claim_id",
                "claim id must use CLAIM-* form",
            )
        if task.get("task_status") not in {"completed", "blocked"}:
            _contract_error(
                "invalid-contract-task-status",
                f"{source.name}:tasks.{task_id}.task_status",
                "task status must be completed or blocked",
            )
        if task.get("claim_status") not in {"released", "blocked"}:
            _contract_error(
                "invalid-contract-claim-status",
                f"{source.name}:tasks.{task_id}.claim_status",
                "claim status must be released or blocked",
            )

    expected_findings = contract.get("findings")
    if not isinstance(expected_findings, dict):
        _contract_error(
            "invalid-contract-findings",
            f"{source.name}:findings",
            "findings must be a code-to-priority map",
        )
    for code, priority in expected_findings.items():
        if (
            not isinstance(code, str)
            or not code.strip()
            or priority not in {"P0", "P1", "P2"}
        ):
            _contract_error(
                "invalid-contract-finding",
                f"{source.name}:findings",
                "finding codes must be non-empty and priorities P0, P1, or P2",
            )

    verification = contract.get("verification")
    if not isinstance(verification, dict) or not verification:
        _contract_error(
            "invalid-contract-verification",
            f"{source.name}:verification",
            "verification must be a non-empty integer map",
        )
    for key, value in verification.items():
        if (
            not isinstance(key, str)
            or not SLUG_RE.fullmatch(key)
            or not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
        ):
            _contract_error(
                "invalid-contract-verification",
                f"{source.name}:verification.{key}",
                "verification entries must be safe names and nonnegative integers",
            )

    effects = contract.get("required_external_effects")
    if (
        not isinstance(effects, list)
        or any(
            not isinstance(effect, str) or not SLUG_RE.fullmatch(effect)
            for effect in effects
        )
        or len(set(effects)) != len(effects)
        or not CORE_EXTERNAL_EFFECTS.issubset(effects)
    ):
        _contract_error(
            "invalid-contract-required-external-effects",
            f"{source.name}:required_external_effects",
            "unique effects must include every core offline-effect guard",
        )

    bindings = contract.get("artifact_bindings")
    if not isinstance(bindings, list):
        _contract_error(
            "invalid-contract-artifact-bindings",
            f"{source.name}:artifact_bindings",
            "artifact_bindings must be a list",
        )
    seen_binding_paths: set[str] = set()
    binding_fields = {
        "kind",
        "path",
        "semantic_sha256",
        "raw_evidence_sha256",
    }
    for index, binding in enumerate(bindings):
        prefix = f"{source.name}:artifact_bindings[{index}]"
        if not isinstance(binding, dict) or set(binding) != binding_fields:
            _contract_error(
                "invalid-contract-artifact-binding",
                prefix,
                "pilot isolation binding fields are not exact",
            )
        if binding.get("kind") != "pilot_isolation":
            _contract_error(
                "invalid-contract-artifact-kind",
                f"{prefix}.kind",
                "only pilot_isolation is supported",
            )
        path = binding.get("path")
        if (
            not isinstance(path, str)
            or not _safe_relative(path)
            or path in seen_binding_paths
            or not path.startswith("tests/fixtures/pilots/")
        ):
            _contract_error(
                "invalid-contract-artifact-path",
                f"{prefix}.path",
                "artifact paths must be unique, safe, and fixture-scoped",
            )
        seen_binding_paths.add(str(path))
        for digest_key in ("semantic_sha256", "raw_evidence_sha256"):
            digest = binding.get(digest_key)
            if not isinstance(digest, str) or not BARE_SHA256_RE.fullmatch(digest):
                _contract_error(
                    "invalid-contract-artifact-digest",
                    f"{prefix}.{digest_key}",
                    "expected a bare 64-hex SHA-256",
                )
    return contract


def _validate_migration_contract(
    contract: object,
    source: Path,
) -> dict[str, Any]:
    if not isinstance(contract, dict):
        _contract_error(
            "invalid-contract-root",
            source.name,
            "contract must be a JSON object",
        )
    required_keys = {
        "schema",
        "host",
        "pilot_id",
        "evidence_semantic_sha256",
        "result",
        "baselines",
        "source_unmanaged_count",
        "selected_template_files",
        "seam_dispositions",
        "unclassified_count",
        "temporary_conflict_count",
        "additional_reclaimed_conflicts",
        "protected_file_count",
        "protected_paths_sha256",
        "protected_manifest_sha256",
        "findings",
        "verification",
        "required_external_effects",
        "artifact_bindings",
    }
    missing = sorted(required_keys - set(contract))
    unexpected = sorted(set(contract) - required_keys)
    if missing or unexpected:
        detail = []
        if missing:
            detail.append(f"missing={','.join(missing)}")
        if unexpected:
            detail.append(f"unexpected={','.join(unexpected)}")
        _contract_error(
            "invalid-contract-fields",
            source.name,
            "; ".join(detail),
        )
    if contract.get("schema") != MIGRATION_CONTRACT_SCHEMA:
        _contract_error(
            "invalid-contract-schema",
            f"{source.name}:schema",
            f"expected {MIGRATION_CONTRACT_SCHEMA}",
        )
    for key in ("host", "pilot_id"):
        value = contract.get(key)
        if not isinstance(value, str) or not SLUG_RE.fullmatch(value):
            _contract_error(
                f"invalid-contract-{key.replace('_', '-')}",
                f"{source.name}:{key}",
                "expected a lowercase safe slug",
            )
    digest = contract.get("evidence_semantic_sha256")
    if not isinstance(digest, str) or not BARE_SHA256_RE.fullmatch(digest):
        _contract_error(
            "invalid-contract-semantic-digest",
            f"{source.name}:evidence_semantic_sha256",
            "expected a bare 64-hex SHA-256",
        )
    if contract.get("result") not in {"passed", "blocked"}:
        _contract_error(
            "invalid-contract-result",
            f"{source.name}:result",
            "result must be passed or blocked",
        )

    baselines = contract.get("baselines")
    if not isinstance(baselines, dict) or not {
        "host_commit",
        "runtime_commit",
    }.issubset(baselines):
        _contract_error(
            "invalid-contract-baselines",
            f"{source.name}:baselines",
            "host_commit and runtime_commit are required",
        )
    for key, value in baselines.items():
        if not isinstance(key, str) or not SLUG_RE.fullmatch(key):
            _contract_error(
                "invalid-contract-baseline-name",
                f"{source.name}:baselines",
                "baseline names must be safe slugs",
            )
        if not isinstance(value, str) or not GIT_SHA_RE.fullmatch(value):
            _contract_error(
                "invalid-contract-baseline",
                f"{source.name}:baselines.{key}",
                "expected a full 40-hex git object id",
            )

    source_count = _contract_int(
        contract,
        "source_unmanaged_count",
        minimum=1,
    )
    _contract_int(contract, "selected_template_files", minimum=1)
    _contract_int(contract, "protected_file_count", minimum=1)
    for key in ("unclassified_count", "temporary_conflict_count"):
        _contract_int(contract, key)
    for key in ("protected_paths_sha256", "protected_manifest_sha256"):
        value = contract.get(key)
        if not isinstance(value, str) or not BARE_SHA256_RE.fullmatch(value):
            _contract_error(
                "invalid-contract-digest",
                f"{source.name}:{key}",
                "expected a bare 64-hex SHA-256",
            )

    dispositions = contract.get("seam_dispositions")
    expected_dispositions = {
        "managed",
        "seed_once",
        "host_owned",
        "generated",
    }
    if (
        not isinstance(dispositions, dict)
        or set(dispositions) != expected_dispositions
        or any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
            for value in dispositions.values()
        )
        or sum(dispositions.values()) != source_count
    ):
        _contract_error(
            "invalid-contract-seam-dispositions",
            f"{source.name}:seam_dispositions",
            "exact nonnegative dispositions must sum to source_unmanaged_count",
        )

    reclaimed = contract.get("additional_reclaimed_conflicts")
    if (
        not isinstance(reclaimed, list)
        or not reclaimed
        or any(
            not isinstance(path, str) or not _safe_relative(path)
            for path in reclaimed
        )
        or len(set(reclaimed)) != len(reclaimed)
    ):
        _contract_error(
            "invalid-contract-reclaimed-conflicts",
            f"{source.name}:additional_reclaimed_conflicts",
            "paths must be a non-empty unique safe relative list",
        )

    expected_findings = contract.get("findings")
    if not isinstance(expected_findings, dict):
        _contract_error(
            "invalid-contract-findings",
            f"{source.name}:findings",
            "findings must be a code-to-priority map",
        )
    for code, priority in expected_findings.items():
        if (
            not isinstance(code, str)
            or not code.strip()
            or priority not in {"P0", "P1", "P2"}
        ):
            _contract_error(
                "invalid-contract-finding",
                f"{source.name}:findings",
                "finding codes must be non-empty and priorities P0, P1, or P2",
            )

    verification = contract.get("verification")
    if not isinstance(verification, dict) or not verification:
        _contract_error(
            "invalid-contract-verification",
            f"{source.name}:verification",
            "verification must be a non-empty integer map",
        )
    for key, value in verification.items():
        if (
            not isinstance(key, str)
            or not SLUG_RE.fullmatch(key)
            or not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
        ):
            _contract_error(
                "invalid-contract-verification",
                f"{source.name}:verification.{key}",
                "verification entries must be safe names and nonnegative integers",
            )

    effects = contract.get("required_external_effects")
    if (
        not isinstance(effects, list)
        or any(
            not isinstance(effect, str) or not SLUG_RE.fullmatch(effect)
            for effect in effects
        )
        or len(set(effects)) != len(effects)
        or not CORE_EXTERNAL_EFFECTS.issubset(effects)
    ):
        _contract_error(
            "invalid-contract-required-external-effects",
            f"{source.name}:required_external_effects",
            "unique effects must include every core offline-effect guard",
        )

    bindings = contract.get("artifact_bindings")
    if not isinstance(bindings, list) or len(bindings) != 2:
        _contract_error(
            "invalid-contract-artifact-bindings",
            f"{source.name}:artifact_bindings",
            "migration contracts require exactly one isolation and one seam ledger",
        )
    seen_binding_paths: set[str] = set()
    seen_kinds: set[str] = set()
    for index, binding in enumerate(bindings):
        prefix = f"{source.name}:artifact_bindings[{index}]"
        if not isinstance(binding, dict):
            _contract_error(
                "invalid-contract-artifact-binding",
                prefix,
                "artifact binding must be an object",
            )
        kind = binding.get("kind")
        expected_fields = {
            "pilot_isolation": {
                "kind",
                "path",
                "semantic_sha256",
                "raw_evidence_sha256",
            },
            "seam_ledger": {
                "kind",
                "path",
                "semantic_sha256",
            },
        }.get(kind)
        if expected_fields is None or set(binding) != expected_fields:
            _contract_error(
                "invalid-contract-artifact-binding",
                prefix,
                "artifact binding kind or fields are not exact",
            )
        path = binding.get("path")
        if (
            not isinstance(path, str)
            or not _safe_relative(path)
            or path in seen_binding_paths
            or not path.startswith("tests/fixtures/pilots/")
        ):
            _contract_error(
                "invalid-contract-artifact-path",
                f"{prefix}.path",
                "artifact paths must be unique, safe, and fixture-scoped",
            )
        seen_binding_paths.add(path)
        seen_kinds.add(kind)
        for digest_key in expected_fields - {"kind", "path"}:
            value = binding.get(digest_key)
            if not isinstance(value, str) or not BARE_SHA256_RE.fullmatch(value):
                _contract_error(
                    "invalid-contract-artifact-digest",
                    f"{prefix}.{digest_key}",
                    "expected a bare 64-hex SHA-256",
                )
    if seen_kinds != {"pilot_isolation", "seam_ledger"}:
        _contract_error(
            "invalid-contract-artifact-kinds",
            f"{source.name}:artifact_bindings",
            "migration contracts require one isolation and one seam ledger",
        )
    return contract


def _validate_contract(contract: object, source: Path) -> dict[str, Any]:
    schema = contract.get("schema") if isinstance(contract, dict) else None
    if schema == MIGRATION_CONTRACT_SCHEMA:
        return _validate_migration_contract(contract, source)
    return _validate_execution_contract(contract, source)


def load_contract_registry(
    contract_dir: Path = DEFAULT_CONTRACT_DIR,
) -> dict[tuple[str, str], dict[str, Any]]:
    if not contract_dir.is_dir() or contract_dir.is_symlink():
        _contract_error(
            "contract-registry-unavailable",
            str(contract_dir),
            "contract registry must be a real directory",
        )
    paths = sorted(contract_dir.glob("*.json"))
    if not paths:
        _contract_error(
            "contract-registry-empty",
            str(contract_dir),
            "at least one immutable pilot contract is required",
        )
    registry: dict[tuple[str, str], dict[str, Any]] = {}
    pilot_owners: dict[str, str] = {}
    for path in paths:
        if path.is_symlink() or not path.is_file():
            _contract_error(
                "invalid-contract-file",
                path.name,
                "contract must be a regular non-symlink file",
            )
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            _contract_error(
                "invalid-contract-json",
                path.name,
                type(exc).__name__,
            )
        contract = _validate_contract(raw, path)
        key = (contract["host"], contract["pilot_id"])
        if key in registry:
            _contract_error(
                "duplicate-contract",
                path.name,
                f"duplicate host/pilot pair {key[0]}:{key[1]}",
            )
        owner = pilot_owners.get(contract["pilot_id"])
        if owner is not None and owner != contract["host"]:
            _contract_error(
                "cross-host-pilot-reuse",
                path.name,
                f"pilot id already belongs to {owner}",
            )
        pilot_owners[contract["pilot_id"]] = contract["host"]
        registry[key] = contract
    return registry


def _artifact_findings(
    contract: dict[str, Any],
    *,
    artifact_root: Path,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    root = artifact_root.resolve()
    for index, binding in enumerate(contract.get("artifact_bindings", [])):
        prefix = f"contract.artifact_bindings[{index}]"
        relative = Path(binding["path"])
        artifact = (root / relative).resolve()
        if root not in artifact.parents:
            findings.append(
                _finding(
                    "artifact-path-escape",
                    f"{prefix}.path",
                    "artifact binding resolves outside the repository",
                )
            )
            continue
        try:
            payload = json.loads(artifact.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            findings.append(
                _finding(
                    "artifact-unavailable",
                    f"{prefix}.path",
                    f"{type(exc).__name__}: bound artifact could not be loaded",
                )
            )
            continue
        if not isinstance(payload, dict):
            findings.append(
                _finding(
                    "invalid-bound-artifact",
                    f"{prefix}.path",
                    "bound artifact must be a JSON object",
                )
            )
            continue
        absolute_paths = _absolute_string_paths(payload)
        if absolute_paths:
            findings.append(
                _finding(
                    "artifact-absolute-path-leak",
                    f"{prefix}.path",
                    f"bound artifact contains an absolute path at {absolute_paths[0]}",
                )
            )
        if _semantic_sha256(payload) != binding["semantic_sha256"]:
            findings.append(
                _finding(
                    "artifact-semantic-digest-mismatch",
                    f"{prefix}.semantic_sha256",
                    "bound artifact differs from its immutable semantic digest",
                )
            )
        if binding["kind"] == "pilot_isolation":
            if payload.get("schema") != pilot_isolation_gate.PORTABLE_SCHEMA:
                findings.append(
                    _finding(
                        "isolation-artifact-not-portable",
                        f"{prefix}.path",
                        "published isolation evidence must use the v2 sanitized projection",
                    )
                )
                continue
            if payload.get("pilot_id") != contract["pilot_id"]:
                findings.append(
                    _finding(
                        "isolation-pilot-identity-mismatch",
                        f"{prefix}.path",
                        "portable isolation evidence belongs to another pilot",
                    )
                )
            raw_proof = _mapping(payload.get("raw_proof"))
            if (
                raw_proof.get("evidence_sha256")
                != binding["raw_evidence_sha256"]
            ):
                findings.append(
                    _finding(
                        "isolation-raw-binding-mismatch",
                        f"{prefix}.raw_evidence_sha256",
                        "portable evidence does not bind the declared raw proof",
                    )
                )
            isolation = pilot_isolation_gate.analyze(payload, artifact)
            if isolation["block_count"]:
                findings.append(
                    _finding(
                        "isolation-artifact-blocked",
                        f"{prefix}.path",
                        f"portable isolation gate reported {isolation['block_count']} blocker(s)",
                    )
                )
        elif binding["kind"] == "seam_ledger":
            if payload.get("schema") != SEAM_LEDGER_SCHEMA:
                findings.append(
                    _finding(
                        "invalid-seam-ledger-schema",
                        f"{prefix}.path",
                        f"expected {SEAM_LEDGER_SCHEMA}",
                    )
                )
                continue
            ledger_fields = {
                "schema",
                "host",
                "pilot_id",
                "host_commit",
                "runtime_commit",
                "source_unmanaged_count",
                "unclassified_count",
                "temporary_conflict_count",
                "counts",
                "additional_reclaimed_conflicts",
                "entries",
            }
            if set(payload) != ledger_fields:
                findings.append(
                    _finding(
                        "invalid-seam-ledger-fields",
                        f"{prefix}.path",
                        "seam ledger top-level fields must be exact",
                    )
                )
            if (
                payload.get("host") != contract["host"]
                or payload.get("pilot_id") != contract["pilot_id"]
            ):
                findings.append(
                    _finding(
                        "seam-ledger-identity-mismatch",
                        f"{prefix}.path",
                        "seam ledger belongs to another host or pilot",
                    )
                )
            baselines = _mapping(contract.get("baselines"))
            if (
                payload.get("host_commit") != baselines.get("host_commit")
                or payload.get("runtime_commit")
                != baselines.get("runtime_commit")
            ):
                findings.append(
                    _finding(
                        "seam-ledger-baseline-mismatch",
                        f"{prefix}.path",
                        "seam ledger baseline differs from the exact contract",
                    )
                )
            entries = _list(payload.get("entries"))
            seen_paths: set[str] = set()
            observed_counts = {
                "managed": 0,
                "seed_once": 0,
                "host_owned": 0,
                "generated": 0,
            }
            invalid_entry = False
            for entry in entries:
                record = _mapping(entry)
                path = record.get("path")
                disposition = record.get("disposition")
                before = record.get("before")
                after = record.get("after")
                changed = record.get("changed")
                if (
                    set(record)
                    != {
                        "path",
                        "disposition",
                        "before",
                        "after",
                        "changed",
                        "reason",
                    }
                    or not isinstance(path, str)
                    or not _safe_relative(path)
                    or path in seen_paths
                    or disposition not in observed_counts
                    or not _valid_sha(before)
                    or not _valid_sha(after)
                    or not isinstance(changed, bool)
                    or changed != (before != after)
                    or not isinstance(record.get("reason"), str)
                    or not record["reason"].strip()
                ):
                    invalid_entry = True
                    continue
                seen_paths.add(path)
                observed_counts[disposition] += 1
            if invalid_entry:
                findings.append(
                    _finding(
                        "invalid-seam-ledger-entry",
                        f"{prefix}.path",
                        "entries require unique safe paths, exact digests, dispositions, change flags, and reasons",
                    )
                )
            if (
                payload.get("source_unmanaged_count")
                != contract.get("source_unmanaged_count")
                or len(entries) != contract.get("source_unmanaged_count")
                or payload.get("counts") != contract.get("seam_dispositions")
                or observed_counts != contract.get("seam_dispositions")
                or payload.get("unclassified_count")
                != contract.get("unclassified_count")
                or payload.get("temporary_conflict_count")
                != contract.get("temporary_conflict_count")
                or payload.get("additional_reclaimed_conflicts")
                != contract.get("additional_reclaimed_conflicts")
            ):
                findings.append(
                    _finding(
                        "seam-ledger-contract-mismatch",
                        f"{prefix}.path",
                        "ledger counts, entries, or reclaimed conflicts differ from the exact contract",
                    )
                )
    return findings


def _validate_migration_evidence(
    payload: dict[str, Any],
    *,
    expected_host: str | None = None,
    contracts: dict[tuple[str, str], dict[str, Any]] | None = None,
    artifact_root: Path = ROOT,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    payload_host = str(payload.get("host") or "")
    pilot_id = str(payload.get("pilot_id") or "")
    host = expected_host or payload_host
    if payload.get("schema") != MIGRATION_SCHEMA:
        findings.append(
            _finding(
                "invalid-schema",
                "schema",
                f"expected {MIGRATION_SCHEMA}",
            )
        )
    if payload_host != host:
        findings.append(
            _finding("host-contract-mismatch", "host", f"expected {host}")
        )
    if contracts is None:
        try:
            contracts = load_contract_registry()
        except ContractRegistryError as exc:
            findings.append(
                _finding(
                    "contract-registry-invalid",
                    "contracts",
                    str(exc),
                )
            )
            contracts = {}
    known_hosts = {contract_host for contract_host, _ in contracts}
    contract = contracts.get((payload_host, pilot_id))
    if not contract:
        if payload_host not in known_hosts:
            findings.append(
                _finding(
                    "unknown-host-contract",
                    "host",
                    "host has no registered immutable pilot contracts",
                )
            )
        findings.append(
            _finding(
                "unknown-pilot-contract",
                "pilot_id",
                "the exact host/pilot pair is not registered",
            )
        )
        contract = {}
    elif contract.get("schema") != MIGRATION_CONTRACT_SCHEMA:
        findings.append(
            _finding(
                "pilot-kind-contract-mismatch",
                "schema",
                "migration evidence requires a migration contract",
            )
        )
        contract = {}
    if contract and payload.get("result") != contract["result"]:
        findings.append(
            _finding(
                "result-contract-mismatch",
                "result",
                f"expected {contract['result']}",
            )
        )
    if contract and _semantic_sha256(payload) != contract[
        "evidence_semantic_sha256"
    ]:
        findings.append(
            _finding(
                "fixture-semantic-digest-mismatch",
                "$",
                "fixture differs from the pinned semantic evidence contract",
            )
        )
    absolute_paths = _absolute_string_paths(payload)
    if absolute_paths:
        findings.append(
            _finding(
                "absolute-path-leak",
                absolute_paths[0],
                "fixture strings must not contain absolute local paths",
            )
        )

    baselines = _mapping(payload.get("baselines"))
    expected_baselines = _mapping(contract.get("baselines"))
    baseline_keys = set(expected_baselines) or {
        "host_commit",
        "runtime_commit",
    }
    for key in sorted(baseline_keys):
        value = str(baselines.get(key) or "")
        if not GIT_SHA_RE.fullmatch(value):
            findings.append(
                _finding(
                    "invalid-baseline",
                    f"baselines.{key}",
                    "expected a full git object id",
                )
            )
        elif contract and value != expected_baselines[key]:
            findings.append(
                _finding(
                    "baseline-contract-mismatch",
                    f"baselines.{key}",
                    "value differs from the pinned migration contract",
                )
            )

    source = _mapping(payload.get("source_migration"))
    source_count = _count(source, "source_unmanaged_count")
    if source_count != contract.get("source_unmanaged_count"):
        findings.append(
            _finding(
                "source-seam-count-mismatch",
                "source_migration.source_unmanaged_count",
                "source seam count differs from the exact migration contract",
            )
        )
    if not _valid_sha(source.get("source_unmanaged_paths_sha256")):
        findings.append(
            _finding(
                "invalid-source-seam-digest",
                "source_migration.source_unmanaged_paths_sha256",
                "source seam inventory requires a SHA-256 digest",
            )
        )
    if source.get("attempt_2_manifest_reproduced") is not True:
        findings.append(
            _finding(
                "migration-baseline-not-reproduced",
                "source_migration.attempt_2_manifest_reproduced",
                "the prior same-commit inventory must reproduce",
            )
        )
    if (
        not str(source.get("source_runtime_ref") or "").strip()
        or not str(source.get("source_config_schema") or "").strip()
    ):
        findings.append(
            _finding(
                "invalid-source-migration",
                "source_migration",
                "source Runtime ref and config schema are required",
            )
        )

    adoption = _mapping(payload.get("adoption"))
    selected = _count(adoption, "selected_template_files")
    if selected != contract.get("selected_template_files"):
        findings.append(
            _finding(
                "selection-contract-mismatch",
                "adoption.selected_template_files",
                "selection differs from the exact migration contract",
            )
        )
    if adoption.get("target_config_schema") != "agent-runtime-config/v2":
        findings.append(
            _finding(
                "invalid-target-config-schema",
                "adoption.target_config_schema",
                "migration target must use config v2",
            )
        )
    for key in ("profiles", "capabilities"):
        values = adoption.get(key)
        if (
            not isinstance(values, list)
            or not values
            or any(
                not isinstance(value, str) or not SLUG_RE.fullmatch(value)
                for value in values
            )
            or len(set(values)) != len(values)
        ):
            findings.append(
                _finding(
                    f"invalid-{key}",
                    f"adoption.{key}",
                    "values must be a non-empty unique safe slug list",
                )
            )
    for name in ("initial_reconcile", "final_reconcile"):
        reconcile = _mapping(adoption.get(name))
        counts = tuple(
            _count(reconcile, key)
            for key in ("safe_updates", "conflicts", "preserved", "excluded")
        )
        if (
            any(value is None for value in counts)
            or sum(value or 0 for value in counts) != selected
        ):
            findings.append(
                _finding(
                    "reconcile-count-mismatch",
                    f"adoption.{name}",
                    "reconcile counts must be integers summing to the selection",
                )
            )
    initial = _mapping(adoption.get("initial_reconcile"))
    final = _mapping(adoption.get("final_reconcile"))
    if _count(initial, "conflicts") != 0:
        findings.append(
            _finding(
                "initial-conflict",
                "adoption.initial_reconcile.conflicts",
                "safe migration planning must not retain conflicts",
            )
        )
    if _count(final, "safe_updates") != 0 or _count(final, "conflicts") != 0:
        findings.append(
            _finding(
                "unstable-migration",
                "adoption.final_reconcile",
                "final reconcile must settle with zero updates and conflicts",
            )
        )
    ownership = _mapping(adoption.get("ownership_counts"))
    expected_ownership_keys = {
        "managed",
        "seed_once",
        "host_owned",
        "generated",
    }
    if (
        set(ownership) != expected_ownership_keys
        or any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
            for value in ownership.values()
        )
        or sum(ownership.values()) != selected
    ):
        findings.append(
            _finding(
                "ownership-count-mismatch",
                "adoption.ownership_counts",
                "exact ownership counts must sum to selected template files",
            )
        )

    lock = _mapping(adoption.get("lock"))
    if (
        lock.get("schema") != "agent-runtime-lock/v2"
        or lock.get("migration") != "current"
        or _count(lock, "template_files") != selected
        or _count(lock, "finding_count") != 0
        or lock.get("upstream_ref") != baselines.get("runtime_commit")
        or not _valid_sha(lock.get("template_digest"))
    ):
        findings.append(
            _finding(
                "invalid-migration-lock",
                "adoption.lock",
                "lock v2 must bind the exact Runtime and clean template inventory",
            )
        )
    idempotence = _mapping(adoption.get("idempotence"))
    before = _mapping(idempotence.get("before"))
    after = _mapping(idempotence.get("after"))
    expected_idempotence_keys = {
        "status_sha256",
        "tracked_diff_sha256",
        "untracked_paths_sha256",
        "untracked_content_sha256",
        "config_sha256",
        "lock_sha256",
        "hooks_sha256",
        "scribe_projection_sha256",
    }
    if (
        idempotence.get("second_plan_apply_identical") is not True
        or set(before) != expected_idempotence_keys
        or set(after) != expected_idempotence_keys
        or any(not _valid_sha(value) for value in before.values())
        or before != after
    ):
        findings.append(
            _finding(
                "migration-not-idempotent",
                "adoption.idempotence",
                "second plan/apply snapshots must be exact and byte-identical",
            )
        )

    seam = _mapping(payload.get("seam_reduction"))
    dispositions = _mapping(seam.get("dispositions"))
    expected_dispositions = _mapping(contract.get("seam_dispositions"))
    if (
        _count(seam, "source_unmanaged_count") != source_count
        or dispositions != expected_dispositions
        or sum(
            value
            for value in dispositions.values()
            if isinstance(value, int) and not isinstance(value, bool)
        )
        != source_count
    ):
        findings.append(
            _finding(
                "seam-disposition-mismatch",
                "seam_reduction.dispositions",
                "all source seams must have an exact contracted disposition",
            )
        )
    if _count(seam, "unclassified_count") != 0:
        findings.append(
            _finding(
                "unclassified-migration-seam",
                "seam_reduction.unclassified_count",
                "green migration evidence cannot leave an unclassified seam",
            )
        )
    if _count(seam, "temporary_conflict_count") != 0:
        findings.append(
            _finding(
                "temporary-migration-conflict",
                "seam_reduction.temporary_conflict_count",
                "green migration evidence cannot retain a temporary conflict",
            )
        )
    if (
        _count(seam, "unclassified_count")
        != contract.get("unclassified_count")
        or _count(seam, "temporary_conflict_count")
        != contract.get("temporary_conflict_count")
    ):
        findings.append(
            _finding(
                "seam-state-contract-mismatch",
                "seam_reduction",
                "remaining seam state differs from the exact contract",
            )
        )
    managed = dispositions.get("managed")
    changed_count = _count(seam, "changed_source_path_count")
    if (
        not isinstance(managed, int)
        or isinstance(managed, bool)
        or managed < 1
        or changed_count is None
        or changed_count < managed
    ):
        findings.append(
            _finding(
                "no-material-seam-reduction",
                "seam_reduction",
                "at least one real source seam must return to managed Runtime",
            )
        )
    reclaimed = seam.get("additional_reclaimed_conflicts")
    if reclaimed != contract.get("additional_reclaimed_conflicts"):
        findings.append(
            _finding(
                "reclaimed-conflict-contract-mismatch",
                "seam_reduction.additional_reclaimed_conflicts",
                "additional reclaimed paths differ from the exact contract",
            )
        )

    preservation = _mapping(payload.get("preservation"))
    before_manifest = preservation.get("protected_manifest_before")
    after_manifest = preservation.get("protected_manifest_after")
    if (
        _count(preservation, "protected_file_count")
        != contract.get("protected_file_count")
        or preservation.get("protected_paths_sha256")
        != contract.get("protected_paths_sha256")
        or before_manifest != contract.get("protected_manifest_sha256")
        or not _valid_sha(before_manifest)
        or not _valid_sha(after_manifest)
    ):
        findings.append(
            _finding(
                "protected-inventory-contract-mismatch",
                "preservation",
                "protected inventory differs from the exact contract",
            )
        )
    if (
        before_manifest != after_manifest
        or _count(preservation, "protected_change_count") != 0
    ):
        findings.append(
            _finding(
                "protected-product-mutation",
                "preservation",
                "protected product bytes changed during migration",
            )
        )
    for key in (
        "primary_unchanged",
        "control_unchanged",
        "runtime_product_unchanged",
    ):
        if preservation.get(key) is not True:
            findings.append(
                _finding(
                    "isolation-checkout-mutation",
                    f"preservation.{key}",
                    "non-target checkouts must remain unchanged",
                )
            )

    lifecycle = _mapping(payload.get("lifecycle"))
    compound = _mapping(lifecycle.get("compound"))
    if (
        _count(compound, "search_count_before") != 0
        or (_count(compound, "search_count_after") or 0) < 1
        or compound.get("check_status") != "pass"
        or not TASK_RE.fullmatch(str(compound.get("work_id") or ""))
        or not str(compound.get("record_id") or "").startswith("COMPOUND-")
        or not str(compound.get("defect_signature") or "").startswith(
            "defect:"
        )
    ):
        findings.append(
            _finding(
                "compound-migration-proof-missing",
                "lifecycle.compound",
                "migration must write, retrieve, and validate a task-linked record",
            )
        )
    if (
        not _valid_sha(compound.get("legacy_source_before"))
        or compound.get("legacy_source_before")
        != compound.get("legacy_source_after")
    ):
        findings.append(
            _finding(
                "compound-legacy-source-mutation",
                "lifecycle.compound",
                "legacy compound history must remain unchanged",
            )
        )
    scribe = _mapping(lifecycle.get("scribe"))
    if (
        scribe.get("projection_status") != "fresh"
        or scribe.get("readiness") != "ready"
        or scribe.get("closure_blocking") is not False
    ):
        findings.append(
            _finding(
                "scribe-projection-not-fresh",
                "lifecycle.scribe",
                "generated Scribe projection must be fresh and ready",
            )
        )
    if (
        not _valid_sha(scribe.get("source_before"))
        or scribe.get("source_before") != scribe.get("source_after")
    ):
        findings.append(
            _finding(
                "scribe-source-mutation",
                "lifecycle.scribe",
                "configured Scribe source must remain unchanged",
            )
        )
    observed_finding_codes = {
        str(item.get("code") or "")
        for item in _list(payload.get("findings"))
        if isinstance(item, dict)
    }
    if (
        scribe.get("source_overdue") is True
        or scribe.get("active_task_coverage") != "verified"
        or scribe.get("compaction_performed") is not True
    ) and "scribe-source-overdue-active-task-unverified" not in observed_finding_codes:
        findings.append(
            _finding(
                "scribe-gap-not-declared",
                "lifecycle.scribe",
                "overdue, unverified, or uncompacted state must remain an explicit finding",
            )
        )
    hooks = _mapping(lifecycle.get("hooks"))
    if (
        (_count(hooks, "canonical_event_count") or 0) < 5
        or (_count(hooks, "canonical_command_count") or 0) < 6
        or hooks.get("owner_command_preserved") is not True
    ):
        findings.append(
            _finding(
                "lifecycle-hook-contract-missing",
                "lifecycle.hooks",
                "canonical lifecycle events and host authority hook are required",
            )
        )
    if (
        (_count(hooks, "legacy_duplicate_count") or 0) > 0
        and "legacy-hook-command-duplication" not in observed_finding_codes
    ):
        findings.append(
            _finding(
                "legacy-hook-gap-not-declared",
                "lifecycle.hooks.legacy_duplicate_count",
                "preserved duplicate commands must remain an explicit finding",
            )
        )

    continuity = _mapping(payload.get("continuity"))
    if (
        continuity.get("evidence_mode") != "contract-replay-only"
        or _count(continuity, "product_work_dispatch_count") != 0
        or _count(continuity, "product_claim_mutation_count") != 0
    ):
        findings.append(
            _finding(
                "migration-product-work-executed",
                "continuity",
                "migration-only evidence must not invent or dispatch product work",
            )
        )
    if (
        _count(continuity, "parallel_contract_tests_passed")
        != _count(
            _mapping(payload.get("verification")),
            "parallel_worktree_tests_passed",
        )
        or not str(continuity.get("reason") or "").strip()
    ):
        findings.append(
            _finding(
                "continuity-contract-mismatch",
                "continuity",
                "continuity replay count and non-execution reason must be explicit",
            )
        )

    routing = _mapping(payload.get("routing"))
    if (
        routing.get("availability") != "configured_unverified"
        or routing.get("live_probe_performed") is not False
        or routing.get("actual_model_status") != "unverified"
        or routing.get("provider_usage_verified") is not False
    ):
        findings.append(
            _finding(
                "invalid-routing-observation",
                "routing",
                "offline migration cannot claim observed provider execution",
            )
        )
    if routing.get("savings_claim") != "unavailable":
        findings.append(
            _finding(
                "unsupported-savings-claim",
                "routing.savings_claim",
                "token or cost savings require observed provider usage",
            )
        )
    if (
        (_count(routing, "equivalent_tier_warning_count") or 0) > 0
        and "model-tier-execution-equivalence" not in observed_finding_codes
    ):
        findings.append(
            _finding(
                "routing-gap-not-declared",
                "routing.equivalent_tier_warning_count",
                "equivalent execution tiers must remain an explicit finding",
            )
        )

    effects = _mapping(payload.get("external_effects"))
    required_effects = set(_list(contract.get("required_external_effects")))
    for key in sorted(set(effects) | required_effects):
        if _count(effects, key) != 0:
            findings.append(
                _finding(
                    "external-effect-nonzero",
                    f"external_effects.{key}",
                    "offline migration requires the integer zero",
                )
            )

    observed_findings: dict[str, str] = {}
    duplicate_finding_codes: set[str] = set()
    for item in _list(payload.get("findings")):
        record = _mapping(item)
        code = str(record.get("code") or "")
        if code in observed_findings:
            duplicate_finding_codes.add(code)
        observed_findings[code] = str(record.get("priority") or "")
    if duplicate_finding_codes or observed_findings != contract.get(
        "findings",
        {},
    ):
        findings.append(
            _finding(
                "finding-contract-mismatch",
                "findings",
                "codes and priorities must exactly match the migration contract",
            )
        )
    if "P0" in set(observed_findings.values()) and payload.get(
        "result"
    ) != "blocked":
        findings.append(
            _finding(
                "p0-not-blocking",
                "result",
                "a P0 finding must block the migration pilot",
            )
        )

    verification = _mapping(payload.get("verification"))
    for key, expected in _mapping(contract.get("verification")).items():
        if _count(verification, key) != expected:
            findings.append(
                _finding(
                    "verification-contract-mismatch",
                    f"verification.{key}",
                    f"expected integer {expected}",
                )
            )
    rollback = _mapping(payload.get("rollback"))
    if (
        rollback.get("strategy") != "discard-disposable-target"
        or rollback.get("primary_restore_required") is not False
        or rollback.get("control_restore_required") is not False
        or rollback.get("runtime_product_restore_required") is not False
    ):
        findings.append(
            _finding(
                "invalid-migration-rollback",
                "rollback",
                "rollback must discard only the disposable target",
            )
        )
    if contract:
        findings.extend(
            _artifact_findings(
                contract,
                artifact_root=artifact_root,
            )
        )
    return findings


def validate_evidence(
    payload: object,
    *,
    expected_host: str | None = None,
    contracts: dict[tuple[str, str], dict[str, Any]] | None = None,
    artifact_root: Path = ROOT,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not isinstance(payload, dict):
        return [_finding("invalid-root", "$", "evidence must be a JSON object")]
    if payload.get("schema") == MIGRATION_SCHEMA:
        return _validate_migration_evidence(
            payload,
            expected_host=expected_host,
            contracts=contracts,
            artifact_root=artifact_root,
        )
    if payload.get("schema") != SCHEMA:
        findings.append(_finding("invalid-schema", "schema", f"expected {SCHEMA}"))

    payload_host = str(payload.get("host") or "")
    pilot_id = str(payload.get("pilot_id") or "")
    host = expected_host or payload_host
    if payload_host != host:
        findings.append(
            _finding("host-contract-mismatch", "host", f"expected {host}")
        )
    if contracts is None:
        try:
            contracts = load_contract_registry()
        except ContractRegistryError as exc:
            findings.append(
                _finding(
                    "contract-registry-invalid",
                    "contracts",
                    str(exc),
                )
            )
            contracts = {}
    known_hosts = {contract_host for contract_host, _ in contracts}
    contract = contracts.get((payload_host, pilot_id))
    if not contract:
        if payload_host not in known_hosts:
            findings.append(
                _finding(
                    "unknown-host-contract",
                    "host",
                    "host has no registered immutable pilot contracts",
                )
            )
        findings.append(
            _finding(
                "unknown-pilot-contract",
                "pilot_id",
                "the exact host/pilot pair is not registered",
            )
        )
        contract = {}
    if contract and payload.get("result") != contract["result"]:
        findings.append(_finding("result-contract-mismatch", "result", f"expected {contract['result']}"))
    if (
        contract
        and _semantic_sha256(payload)
        != contract["evidence_semantic_sha256"]
    ):
        findings.append(_finding("fixture-semantic-digest-mismatch", "$", "fixture differs from the pinned semantic evidence contract"))
    absolute_paths = _absolute_string_paths(payload)
    if absolute_paths:
        findings.append(_finding("absolute-path-leak", absolute_paths[0], "fixture strings must not contain absolute local paths"))

    baselines = _mapping(payload.get("baselines"))
    expected_baselines = _mapping(contract.get("baselines"))
    baseline_keys = set(expected_baselines) or {"host_commit", "runtime_commit"}
    for key in sorted(baseline_keys):
        value = str(baselines.get(key) or "")
        if not GIT_SHA_RE.fullmatch(value):
            findings.append(_finding("invalid-baseline", f"baselines.{key}", "expected a full git SHA"))
        elif contract and value != expected_baselines[key]:
            findings.append(_finding("baseline-contract-mismatch", f"baselines.{key}", "value differs from pinned pilot contract"))

    adoption = _mapping(payload.get("adoption"))
    selected = _count(adoption, "selected_template_files")
    initial = _mapping(adoption.get("initial_reconcile"))
    immediate = _mapping(adoption.get("immediate_post_apply_reconcile"))
    if selected is None or selected <= 0:
        findings.append(_finding("invalid-selection-count", "adoption.selected_template_files", "must be positive"))
    elif sum(
        value or 0
        for value in (
            _count(initial, "safe_updates"),
            _count(initial, "preserved"),
            _count(initial, "excluded"),
            _count(initial, "conflicts"),
        )
    ) != selected:
        findings.append(_finding("reconcile-count-mismatch", "adoption.initial_reconcile", "counts must equal selected files"))
    if _count(initial, "conflicts") != 0:
        findings.append(_finding("initial-conflict", "adoption.initial_reconcile.conflicts", "initial adoption must have zero conflicts"))
    if _count(immediate, "safe_updates") != 0 or _count(immediate, "conflicts") != 0:
        findings.append(_finding("unstable-apply", "adoption.immediate_post_apply_reconcile", "safe apply must settle with zero updates and conflicts"))
    if contract and adoption.get(
        "web_content_incremental_files"
    ) != contract.get("web_content_incremental_files"):
        findings.append(
            _finding(
                "incremental-selection-contract-mismatch",
                "adoption.web_content_incremental_files",
                "value differs from the pinned pilot contract",
            )
        )
    if contract and selected != contract["selected_template_files"]:
        findings.append(_finding("selection-contract-mismatch", "adoption.selected_template_files", "value differs from pinned pilot contract"))
    post_registration = _mapping(adoption.get("post_work_registration_reconcile"))
    post_conflicts = _list(post_registration.get("conflict_paths"))
    if (
        _count(post_registration, "safe_updates") != 0
        or _count(post_registration, "conflicts") != len(post_conflicts)
        or post_conflicts != contract.get("post_registration_conflicts", [])
    ):
        findings.append(
            _finding(
                "post-registration-reconcile-mismatch",
                "adoption.post_work_registration_reconcile",
                "conflict count and paths must match the pinned pilot observation",
            )
        )

    preservation = _mapping(payload.get("preservation"))
    assets = _list(preservation.get("host_assets"))
    if preservation.get("host_asset_count") != len(assets) or not assets:
        findings.append(_finding("host-asset-count-mismatch", "preservation.host_assets", "declared count must match a non-empty list"))
    seen_paths: set[str] = set()
    for index, item in enumerate(assets):
        record = _mapping(item)
        prefix = f"preservation.host_assets[{index}]"
        path = str(record.get("path") or "")
        if not _safe_relative(path) or path in seen_paths:
            findings.append(_finding("invalid-host-asset-path", f"{prefix}.path", "path must be unique and safe relative"))
        seen_paths.add(path)
        before, after = record.get("before"), record.get("after")
        if not _valid_sha(before) or not _valid_sha(after):
            findings.append(_finding("invalid-host-asset-digest", prefix, "before and after must be SHA-256 values"))
        elif before != after:
            findings.append(_finding("host-asset-overwrite", prefix, f"preserved asset changed: {path}"))
    if preservation.get("unexpected_overwrite_count") != 0:
        findings.append(_finding("unexpected-overwrite", "preservation.unexpected_overwrite_count", "must be zero"))
    content = _mapping(preservation.get("content"))
    if _count(content, "file_count") != contract.get("content_file_count"):
        findings.append(_finding("content-file-count-mismatch", "preservation.content.file_count", "value differs from pinned pilot contract"))
    if not _valid_sha(content.get("before")) or not _valid_sha(content.get("after")):
        findings.append(_finding("invalid-content-digest", "preservation.content", "content manifests must be SHA-256 values"))
    elif content.get("before") != content.get("after"):
        findings.append(_finding("content-mutation", "preservation.content", "src/content manifest changed"))

    bootstrap = _mapping(payload.get("bootstrap"))
    if not CLAIM_RE.fullmatch(str(bootstrap.get("upstream_claim_id") or "")):
        findings.append(_finding("missing-bootstrap-claim", "bootstrap.upstream_claim_id", "bootstrap must map to a persisted upstream claim"))
    for key in ("unmapped_diff_count", "consumer_commit_count", "consumer_push_count"):
        if _count(bootstrap, key) != 0:
            findings.append(_finding("bootstrap-effect-nonzero", f"bootstrap.{key}", "must be the integer zero"))

    expected_task_count = payload.get("expected_task_count")
    tasks = _list(payload.get("tasks"))
    contract_task_count = contract.get("expected_task_count")
    if (
        expected_task_count != len(tasks)
        or (contract and expected_task_count != contract_task_count)
    ):
        findings.append(
            _finding(
                "task-count-mismatch",
                "tasks",
                "task traces must match the pinned pilot contract",
            )
        )
    seen_tasks: set[str] = set()
    for index, item in enumerate(tasks):
        task = _mapping(item)
        prefix = f"tasks[{index}]"
        task_id = str(task.get("task_id") or "")
        if not task_id or task_id in seen_tasks:
            findings.append(_finding("invalid-task-trace", f"{prefix}.task_id", "task id must be present and unique"))
        seen_tasks.add(task_id)
        claim = _mapping(task.get("claim_trace"))
        if not CLAIM_RE.fullmatch(str(claim.get("claim_id") or "")):
            findings.append(_finding("missing-claim-trace", f"{prefix}.claim_trace", "task must carry a canonical claim id"))
        if claim.get("task_id") != task_id or claim.get("unit_id") != task.get("unit_id"):
            findings.append(_finding("claim-identity-mismatch", f"{prefix}.claim_trace", "claim/task/unit identities must agree"))
        if claim.get("status") not in {"blocked", "released"}:
            findings.append(_finding("invalid-claim-status", f"{prefix}.claim_trace.status", "terminal pilot claim must be blocked or released"))
        expected_task = _mapping(_mapping(contract.get("tasks")).get(task_id))
        if not expected_task:
            findings.append(_finding("unexpected-task-trace", prefix, "task is not in the pinned host contract"))
        elif (
            task.get("unit_id") != expected_task.get("unit_id")
            or task.get("status") != expected_task.get("task_status")
            or claim.get("claim_id") != expected_task.get("claim_id")
            or claim.get("status") != expected_task.get("claim_status")
        ):
            findings.append(_finding("task-contract-mismatch", prefix, "task, unit, claim, or terminal status differs from the pinned host contract"))
        outputs = _list(task.get("output_refs"))
        if not outputs or any(not _safe_relative(path) for path in outputs):
            findings.append(_finding("missing-task-output", f"{prefix}.output_refs", "task must have safe bounded output refs"))

        routing = _mapping(task.get("routing"))
        missing_routing = [field for field in ROUTING_FIELDS if field not in routing]
        if missing_routing:
            findings.append(_finding("missing-routing-field", f"{prefix}.routing", ", ".join(missing_routing)))
        observed = routing.get("observed_model")
        verified_usage = routing.get("provider_usage_verified") is True
        if observed not in {None, ""} and (
            routing.get("actual_model_status") != "verified"
            or not str(routing.get("observation_source") or "").strip()
        ):
            findings.append(_finding("false-model-observation", f"{prefix}.routing.observed_model", "observed model requires verified status and an observation source"))
        usage_values = tuple(routing.get(key) for key in ("input_tokens", "output_tokens", "cost"))
        if any(value is not None for value in usage_values) and not verified_usage:
            findings.append(_finding("unverified-provider-usage", f"{prefix}.routing", "tokens or cost require verified provider usage"))
        if verified_usage:
            token_values = tuple(routing.get(key) for key in ("input_tokens", "output_tokens"))
            cost = routing.get("cost")
            if (
                routing.get("actual_model_status") != "verified"
                or not str(observed or "").strip()
                or not str(routing.get("observation_source") or "").strip()
                or any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in token_values)
                or not isinstance(cost, (int, float))
                or isinstance(cost, bool)
                or cost < 0
            ):
                findings.append(_finding("invalid-provider-usage-proof", f"{prefix}.routing", "verified usage requires an observed model, source, nonnegative integer tokens, and nonnegative numeric cost"))
        savings_claim = routing.get("savings_claim")
        if savings_claim != "unavailable" and (
            not verified_usage
            or not str(routing.get("savings_observation_source") or "").strip()
            or not str(routing.get("comparison_baseline") or "").strip()
        ):
            findings.append(_finding("unsupported-savings-claim", f"{prefix}.routing.savings_claim", "savings require verified usage, an observation source, and a comparison baseline"))

    compound = _mapping(payload.get("compound"))
    if compound.get("negative_fixture_matched") is not True:
        findings.append(_finding("compound-negative-missing", "compound.negative_fixture_matched", "intentional negative must reproduce"))
    if (
        not isinstance(compound.get("retrieval_match_count"), int)
        or isinstance(compound.get("retrieval_match_count"), bool)
        or compound.get("retrieval_match_count", 0) < 1
    ):
        findings.append(_finding("compound-retrieval-missing", "compound.retrieval_match_count", "later lookup must retrieve the record"))

    restart = _mapping(payload.get("restart"))
    if restart.get("same_task") is not True or restart.get("same_claim") is not True:
        findings.append(_finding("restart-identity-mismatch", "restart", "second process must resume the same task and claim"))
    writer_pid, reader_pid = restart.get("writer_pid"), restart.get("reader_pid")
    if (
        not isinstance(writer_pid, int)
        or isinstance(writer_pid, bool)
        or not isinstance(reader_pid, int)
        or isinstance(reader_pid, bool)
        or writer_pid == reader_pid
    ):
        findings.append(_finding("restart-process-not-distinct", "restart", "writer and reader processes must be distinct"))

    scribe = _mapping(payload.get("scribe"))
    if scribe.get("projection_status") != "fresh" or scribe.get("readiness") != "ready":
        findings.append(_finding("scribe-projection-not-fresh", "scribe", "projection must be fresh and ready"))
    if scribe.get("backlog_before") != scribe.get("backlog_after") or not _valid_sha(scribe.get("backlog_before")):
        findings.append(_finding("scribe-source-mutation", "scribe", "BACKLOG.md digest must remain unchanged"))

    effects = _mapping(payload.get("external_effects"))
    required_effects = set(
        _list(contract.get("required_external_effects"))
        or EXPECTED_EXTERNAL_EFFECTS
    )
    for key in sorted(set(effects) | required_effects):
        if _count(effects, key) != 0:
            findings.append(_finding("external-effect-nonzero", f"external_effects.{key}", "offline pilot requires the integer zero"))

    observed_findings: dict[str, str] = {}
    duplicate_finding_codes: set[str] = set()
    for item in _list(payload.get("findings")):
        record = _mapping(item)
        code = str(record.get("code") or "")
        if code in observed_findings:
            duplicate_finding_codes.add(code)
        observed_findings[code] = str(record.get("priority") or "")
    if duplicate_finding_codes or observed_findings != contract.get("findings", {}):
        findings.append(_finding("finding-contract-mismatch", "findings", "codes and priorities must exactly match the pinned host contract"))
    priorities = set(observed_findings.values())
    if "P0" in priorities and payload.get("result") != "blocked":
        findings.append(_finding("p0-not-blocking", "result", "a P0 finding must block the pilot"))

    verification = _mapping(payload.get("verification"))
    expected_verification = _mapping(contract.get("verification"))
    for key, expected in expected_verification.items():
        if _count(verification, key) != expected:
            findings.append(_finding("verification-contract-mismatch", f"verification.{key}", f"expected integer {expected}"))
    if contract:
        findings.extend(
            _artifact_findings(
                contract,
                artifact_root=artifact_root,
            )
        )
    return findings


def load_evidence(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("evidence root must be a JSON object")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate sanitized consumer-pilot evidence")
    parser.add_argument("--host", default="bean-wiki", help="Fixture host slug")
    parser.add_argument("--fixture", type=Path, default=None, help="Explicit evidence JSON")
    parser.add_argument(
        "--contract-dir",
        type=Path,
        default=DEFAULT_CONTRACT_DIR,
        help="Directory containing immutable host/pilot contracts",
    )
    parser.add_argument("--check", action="store_true", help="Fail when findings exist")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable result")
    args = parser.parse_args(argv)
    root = ROOT
    path = args.fixture or root / "tests" / "fixtures" / "pilots" / args.host / "evidence.json"
    try:
        fixture_label = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        fixture_label = path.name
    try:
        payload = load_evidence(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        contract_id = None
        findings = [
            _finding(
                "fixture-unavailable",
                fixture_label,
                f"{type(exc).__name__}: fixture could not be loaded",
            )
        ]
    else:
        contract_id = (
            f"{payload.get('host')}:{payload.get('pilot_id')}"
            if payload.get("host") and payload.get("pilot_id")
            else None
        )
        try:
            contracts = load_contract_registry(args.contract_dir)
        except ContractRegistryError as exc:
            findings = [
                _finding(
                    "contract-registry-invalid",
                    "contracts",
                    str(exc),
                )
            ]
        else:
            findings = validate_evidence(
                payload,
                expected_host=args.host,
                contracts=contracts,
                artifact_root=root,
            )
    result = {
        "schema": "agent-runtime-pilot-acceptance-result/v1",
        "host": args.host,
        "contract_id": contract_id,
        "fixture": fixture_label,
        "status": "pass" if not findings else "fail",
        "finding_count": len(findings),
        "findings": findings,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"pilot-acceptance: {result['status']}")
        print(f"host={args.host}")
        print(f"fixture={fixture_label}")
        print(f"findings={len(findings)}")
        for finding in findings:
            print(f"- {finding['code']} {finding['path']}: {finding['detail']}")
    return 1 if args.check and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
