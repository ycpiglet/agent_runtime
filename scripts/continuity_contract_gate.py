"""Validate live-work continuity and self-improvement documentation contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

try:
    from agent_runtime import config as runtime_config
except ImportError:  # pragma: no cover - exercised only by a broken deployment
    runtime_config = None


ROOT_DOCS = (
    "README.md",
)

# Each entry lists candidate locations for one logical protocol doc, in priority
# order: the consumer-project root first, then the Agent Runtime source-repo
# template path. A doc counts as present if it exists in ANY candidate location,
# so the gate passes both in the source repo (template paths exist) and in a
# generated consumer project (root docs exist, the template tree is absent).
PROTOCOL_DOCS = (
    ("AGENTS.md", "src/agent_runtime/templates/project/AGENTS.md"),
    ("CLAUDE.md", "src/agent_runtime/templates/project/CLAUDE.md"),
)

POINTER_PATHS = (
    "agents/project/NEXT-SESSION-POINTER.yml",
    "src/agent_runtime/templates/project/agents/project/NEXT-SESSION-POINTER.yml",
)

SOURCE_REPO_MARKERS = (
    "pyproject.toml",
    "src/agent_runtime/config.py",
    "src/agent_runtime/templates/project/scripts/continuity_contract_gate.py",
)
CONSUMER_CONFIG_PATH = "agent_runtime.yml"
CONSUMER_LOCK_PATH = "agent_runtime.lock.json"
MANAGED_CONTRACT_PATHS = (
    "AGENT_RUNTIME.md",
    "scripts/continuity_contract_gate.py",
)
CONSUMER_PROTOCOL_PATHS = (
    "AGENTS.md",
    "CLAUDE.md",
)
CONSUMER_POINTER_PATH = "agents/project/NEXT-SESSION-POINTER.yml"
OWNERSHIP_MODES = {"managed", "seed_once", "host_owned", "generated"}

REQUIRED_POINTER_FIELDS = (
    "schema:",
    "updated_at:",
    "current_state:",
    "active_work:",
    "resume:",
    "roles:",
    "pointers:",
    "rules:",
    "verification:",
    "task_set_id:",
    "step_index:",
    "step_total:",
    "status_text:",
)


@dataclass(frozen=True)
class ContinuityFinding:
    path: str
    kind: str
    detail: str


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def _has(pattern: str, text: str) -> bool:
    return re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL) is not None


def _canonical_digest(path: Path) -> str:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        canonical = raw
    else:
        canonical = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def _normal_lock_path(value: object) -> str:
    if not isinstance(value, str):
        return ""
    value = value.strip()
    if (
        not value
        or value.startswith(("/", "~"))
        or "\\" in value
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        return ""
    return value


def _config_ownership(config: object, path: str) -> str:
    for mode in ("managed", "seed_once", "host_owned", "generated"):
        for candidate in config.ownership_for(mode):
            if path == candidate or path.startswith(candidate.rstrip("/") + "/"):
                return mode
    assert runtime_config is not None
    return runtime_config.default_ownership(path)


def _consumer_contract(
    root: Path,
    findings: list[ContinuityFinding],
) -> dict[str, str] | None:
    """Return lock-proven ownership for a generated consumer, else fail closed."""
    start = len(findings)
    config_path = root / CONSUMER_CONFIG_PATH
    lock_path = root / CONSUMER_LOCK_PATH

    config = None
    if runtime_config is None:
        findings.append(
            ContinuityFinding(
                "scripts/agent_runtime/config.py",
                "continuity:consumer-config-loader-missing",
                "generated consumer mode requires the packaged bounded config loader",
            )
        )
    elif not config_path.is_file():
        findings.append(
            ContinuityFinding(
                CONSUMER_CONFIG_PATH,
                "continuity:consumer-config-missing",
                "generated consumer mode requires agent-runtime-config/v2",
            )
        )
    else:
        try:
            config = runtime_config.load_config(root)
        except (OSError, ValueError) as exc:
            findings.append(
                ContinuityFinding(
                    CONSUMER_CONFIG_PATH,
                    "continuity:consumer-config-invalid",
                    f"generated consumer config is invalid: {exc}",
                )
            )
        else:
            if config.source_schema != runtime_config.V2_SCHEMA:
                findings.append(
                    ContinuityFinding(
                        CONSUMER_CONFIG_PATH,
                        "continuity:consumer-config-schema-unsupported",
                        "generated consumer mode requires schema agent-runtime-config/v2",
                    )
                )

    lock: dict[str, object] | None = None
    if not lock_path.is_file():
        findings.append(
            ContinuityFinding(
                CONSUMER_LOCK_PATH,
                "continuity:consumer-lock-missing",
                "generated consumer mode requires agent-runtime-lock/v2",
            )
        )
    else:
        try:
            payload = json.loads(lock_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            findings.append(
                ContinuityFinding(
                    CONSUMER_LOCK_PATH,
                    "continuity:consumer-lock-invalid",
                    f"generated consumer lock is invalid: {exc}",
                )
            )
        else:
            if not isinstance(payload, dict):
                findings.append(
                    ContinuityFinding(
                        CONSUMER_LOCK_PATH,
                        "continuity:consumer-lock-invalid",
                        "generated consumer lock must contain a JSON object",
                    )
                )
            else:
                lock = payload
                if lock.get("schema") != "agent-runtime-lock/v2":
                    findings.append(
                        ContinuityFinding(
                            CONSUMER_LOCK_PATH,
                            "continuity:consumer-lock-schema-unsupported",
                            "generated consumer mode requires schema agent-runtime-lock/v2",
                        )
                    )

    if config is None or lock is None:
        return None

    if lock.get("project") != config.project:
        findings.append(
            ContinuityFinding(
                CONSUMER_LOCK_PATH,
                "continuity:consumer-project-mismatch",
                "config and lock project identifiers must agree",
            )
        )

    lock_upstream = lock.get("upstream")
    if not isinstance(lock_upstream, dict):
        findings.append(
            ContinuityFinding(
                CONSUMER_LOCK_PATH,
                "continuity:consumer-lock-invalid",
                "lock upstream must be a mapping",
            )
        )
        lock_upstream = {}
    config_upstream = {
        "package": config.upstream_package,
        "remote_url": config.upstream_remote_url,
        "ref": config.upstream_ref,
    }
    for field, configured in config_upstream.items():
        if lock_upstream.get(field) != configured:
            findings.append(
                ContinuityFinding(
                    CONSUMER_LOCK_PATH,
                    f"continuity:consumer-upstream-mismatch:{field}",
                    f"config and lock upstream.{field} must agree",
                )
            )

    installed = lock.get("installed")
    if not isinstance(installed, dict):
        findings.append(
            ContinuityFinding(
                CONSUMER_LOCK_PATH,
                "continuity:consumer-lock-invalid",
                "lock installed must be a mapping",
            )
        )
        return None
    ownership_raw = installed.get("ownership")
    managed_raw = installed.get("managed_files")
    if not isinstance(ownership_raw, dict) or not isinstance(managed_raw, dict):
        findings.append(
            ContinuityFinding(
                CONSUMER_LOCK_PATH,
                "continuity:consumer-lock-invalid",
                "lock installed.ownership and installed.managed_files must be mappings",
            )
        )
        return None

    ownership: dict[str, str] = {}
    for raw_path, raw_mode in ownership_raw.items():
        path = _normal_lock_path(raw_path)
        if not path or raw_mode not in OWNERSHIP_MODES:
            findings.append(
                ContinuityFinding(
                    CONSUMER_LOCK_PATH,
                    "continuity:consumer-lock-invalid",
                    f"lock contains invalid ownership entry: {raw_path!r}={raw_mode!r}",
                )
            )
            continue
        ownership[path] = str(raw_mode)
        expected = _config_ownership(config, path)
        if raw_mode != expected:
            findings.append(
                ContinuityFinding(
                    CONSUMER_LOCK_PATH,
                    f"continuity:consumer-ownership-mismatch:{path}",
                    f"config resolves {path} as {expected}, lock records {raw_mode}",
                )
            )

    for path in (*CONSUMER_PROTOCOL_PATHS, CONSUMER_POINTER_PATH):
        if path not in ownership:
            findings.append(
                ContinuityFinding(
                    CONSUMER_LOCK_PATH,
                    f"continuity:consumer-ownership-missing:{path}",
                    f"lock must prove ownership for {path}",
                )
            )

    for path in MANAGED_CONTRACT_PATHS:
        if _config_ownership(config, path) != "managed" or ownership.get(path) != "managed":
            findings.append(
                ContinuityFinding(
                    path,
                    f"continuity:consumer-managed-contract-ownership:{path}",
                    f"{path} must be managed in both config and lock",
                )
            )
            continue
        expected_digest = managed_raw.get(path)
        if not isinstance(expected_digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", expected_digest):
            findings.append(
                ContinuityFinding(
                    CONSUMER_LOCK_PATH,
                    f"continuity:consumer-managed-contract-digest-invalid:{path}",
                    f"lock must contain a canonical sha256 digest for {path}",
                )
            )
            continue
        target = root / path
        if not target.is_file():
            findings.append(
                ContinuityFinding(
                    path,
                    f"continuity:consumer-managed-contract-missing:{path}",
                    f"lock-proven managed contract {path} is missing",
                )
            )
            continue
        if _canonical_digest(target) != expected_digest:
            findings.append(
                ContinuityFinding(
                    path,
                    f"continuity:consumer-managed-contract-digest-mismatch:{path}",
                    f"installed {path} does not match the lock-proven digest",
                )
            )

    return ownership if len(findings) == start else None


def _check_readme(root: Path, findings: list[ContinuityFinding]) -> None:
    readme = _read(root / "README.md")
    if not readme:
        findings.append(ContinuityFinding("README.md", "continuity:readme-missing", "README.md is required"))
        return

    if not _has(r"^##\s+(한국어|Korean)\b", readme):
        findings.append(
            ContinuityFinding(
                "README.md",
                "continuity:readme-korean-section-missing",
                "README must expose a Korean entry section",
            )
        )
    if not _has(r"^##\s+English\b", readme):
        findings.append(
            ContinuityFinding(
                "README.md",
                "continuity:readme-english-section-missing",
                "README must expose an English entry section",
            )
        )

    required_tokens = (
        "AGENTS.md",
        "CLAUDE.md",
        "NEXT-SESSION-POINTER.yml",
        "agents/project/",
    )
    for token in required_tokens:
        if token not in readme:
            findings.append(
                ContinuityFinding(
                    "README.md",
                    f"continuity:readme-pointer-token-missing:{token}",
                    f"README must point developers and agents to {token}",
                )
            )


def _check_pointer(root: Path, findings: list[ContinuityFinding]) -> None:
    existing = [rel for rel in POINTER_PATHS if (root / rel).exists()]
    if not existing:
        findings.append(
            ContinuityFinding(
                "agents/project/NEXT-SESSION-POINTER.yml",
                "continuity:pointer-missing",
                "at least one live-work pointer must exist",
            )
        )
        return

    for rel in existing:
        text = _read(root / rel)
        for field in REQUIRED_POINTER_FIELDS:
            if field not in text:
                findings.append(
                    ContinuityFinding(
                        rel,
                        f"continuity:pointer-field-missing:{field.rstrip(':')}",
                        f"pointer file must include {field}",
                    )
                )
        if "agent-runtime-next-session-pointer/v1" not in text:
            findings.append(
                ContinuityFinding(
                    rel,
                    "continuity:pointer-schema-missing",
                    "pointer file must declare schema agent-runtime-next-session-pointer/v1",
                )
            )


def _check_rule_text(
    text: str,
    label: str,
    findings: list[ContinuityFinding],
) -> None:
    if not text:
        return
    rule_checks = (
        (
            "continuity:pointer-rule-missing",
            r"NEXT-SESSION-POINTER\.yml",
            "protocol docs must require live work pointer maintenance",
        ),
        (
            "continuity:live-work-rule-missing",
            r"(active_work|live\s+work|실시간.*작업|pane_id|progress_pct)",
            "protocol docs must track active agent/team/pane state and progress",
        ),
        (
            "continuity:measured-improvement-rule-missing",
            r"(Evaluate\s*->\s*Propose\s*->\s*Verify\s*->\s*Merge|평가\s*->\s*제안\s*->\s*검증\s*->\s*병합)",
            "protocol docs must define the measured improvement loop",
        ),
        (
            "continuity:repeated-request-api-rule-missing",
            r"(Repeated Request API|반복\s*요청.*API|function/API|함수/API)",
            "protocol docs must promote repeated requests into functions, APIs, scripts, or gates",
        ),
        (
            "continuity:compound-auto-capture-rule-missing",
            r"(Compound.*(automatic|auto|mandatory|forced|자동|강제|필수)|반복.*Compound)",
            "protocol docs must force repeated criticism or mistakes into Compound capture",
        ),
        (
            "continuity:golden-set-rule-missing",
            r"(golden\s*set|goldset|오답|실패\s*사례|edge\s*case)",
            "protocol docs must preserve fixed eval cases, failures, and edge cases",
        ),
        (
            "continuity:owner-merge-rule-missing",
            r"Owner",
            "protocol docs must reserve final criteria and merge authority for Owner",
        ),
    )

    for kind, pattern, detail in rule_checks:
        if not _has(pattern, text):
            findings.append(ContinuityFinding(label, kind, detail))


def _check_protocol_docs(
    root: Path,
    findings: list[ContinuityFinding],
    *,
    excluded: frozenset[str] = frozenset(),
) -> None:
    docs: list[tuple[str, str]] = []
    for candidates in PROTOCOL_DOCS:
        if candidates[0] in excluded:
            continue
        present = [(rel, _read(root / rel)) for rel in candidates if (root / rel).exists()]
        if not any(text for _, text in present):
            findings.append(
                ContinuityFinding(
                    candidates[0],
                    "continuity:protocol-doc-missing",
                    f"protocol doc is required in one of: {', '.join(candidates)}",
                )
            )
            continue
        docs.extend((rel, text) for rel, text in present if text)

    combined = "\n".join(text for _, text in docs)
    _check_rule_text(combined, "AGENTS.md/CLAUDE.md", findings)


def analyze(root: Path) -> list[ContinuityFinding]:
    findings: list[ContinuityFinding] = []
    root = root.resolve()
    source_repo = all((root / marker).is_file() for marker in SOURCE_REPO_MARKERS)
    ownership = None if source_repo else _consumer_contract(root, findings)

    if source_repo or ownership is None:
        _check_readme(root, findings)
        _check_pointer(root, findings)
        _check_protocol_docs(root, findings)
    else:
        readme_ownership = ownership.get("README.md")
        if readme_ownership is not None and readme_ownership != "host_owned":
            _check_readme(root, findings)
        _check_pointer(root, findings)
        excluded = frozenset(
            path
            for path in CONSUMER_PROTOCOL_PATHS
            if ownership.get(path) == "host_owned"
        )
        _check_protocol_docs(root, findings, excluded=excluded)
        _check_rule_text(_read(root / "AGENT_RUNTIME.md"), "AGENT_RUNTIME.md", findings)
    return findings


def render(root: Path, findings: list[ContinuityFinding]) -> str:
    status = "pass" if not findings else "fail"
    lines = [
        f"continuity-contract-gate: {status}",
        f"root={root.resolve()}",
        f"findings={len(findings)}",
    ]
    for finding in findings:
        lines.append(f"- {finding.kind} {finding.path}: {finding.detail}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate session continuity and self-improvement contracts")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--check", action="store_true", help="Fail when findings exist")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    findings = analyze(args.root)
    print(render(args.root, findings))
    if args.check and findings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
