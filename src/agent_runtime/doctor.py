from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import config as _config
from . import lock as _lock
from . import sync as _sync


@dataclass(frozen=True)
class DoctorFinding:
    severity: str
    area: str
    path: str
    kind: str
    detail: str


@dataclass(frozen=True)
class DoctorPlan:
    root: Path
    findings: tuple[DoctorFinding, ...]
    config_loaded: bool = False

    @property
    def blocker_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity == "blocker")

    @property
    def warning_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity == "warning")

    @property
    def info_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity == "info")


REQUIRED_TEMPLATE_FILES = (
    "scripts/agent_orchestrator.py",
    "scripts/agent_worker.py",
    "scripts/auto_runner.py",
    "scripts/auto_dispatch.py",
    "scripts/check_messages.py",
    "scripts/continuity_contract_gate.py",
    "scripts/message_queue.py",
    "scripts/orchestrator_safety_gate.py",
    "scripts/parallel_worktree_gate.py",
    "scripts/pipeline.py",
    "scripts/response_contract_gate.py",
    "scripts/stop_hook_owner_governance.py",
    "scripts/task_claim_dispatcher.py",
    "agents/project/NEXT-SESSION-POINTER.yml",
    "schemas/task.schema.json",
)

REQUIRED_DOC_FILES = (
    "agents/independent_auditor/AUDIT-GATE.md",
    "agents/independent_auditor/SAFETY-GATE.md",
    "agents/qa/TEST-STRATEGY.md",
)

STOP_FILES = (
    ".auto-runner-stop",
    ".orchestrator-stop",
    "agents/runtime/STOP_LOOP",
)

SCRIPT_HELP = (
    ("agent_orchestrator.py", ("--help",)),
    ("agent_worker.py", ("--help",)),
    ("auto_runner.py", ("--help",)),
    ("auto_dispatch.py", ("--help",)),
    ("check_messages.py", ("--help",)),
    ("continuity_contract_gate.py", ("--help",)),
    ("response_contract_gate.py", ("--help",)),
    ("task_claim_dispatcher.py", ("--help",)),
)

PROVIDER_MODULES = (
    "providers.codex",
    "providers.claude",
    "providers.claude_agent",
    "providers.openai",
)

OPTIONAL_DEPENDENCY_EXTRAS = {
    "providers.codex": {"requests", "dotenv"},
    "providers.claude": {"anthropic", "dotenv"},
    "providers.claude_agent": {"anthropic", "dotenv"},
}

SCRIPT_HELP_TIMEOUT_SECONDS = 12
REPAIR_ACTION_PREFIX = "[doctor][repair]"


def _safe_unlink(path: Path) -> bool:
    try:
        path.unlink()
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False


def _safe_mkdir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def _rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _findings_append(findings: list[DoctorFinding], severity: str, *, area: str, path: str, kind: str, detail: str) -> None:
    findings.append(DoctorFinding(severity=severity, area=area, path=path, kind=kind, detail=detail))


def _with_sys_path(path: Path, action: Callable[[None], object]) -> object:
    paths = sys.path
    sys.path.insert(0, str(path))
    try:
        return action()
    finally:
        if str(path) in sys.path:
            sys.path.remove(str(path))


def _module_import_check(root: Path, module_name: str) -> tuple[bool, str | None]:
    try:
        def _import() -> None:
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
            else:
                importlib.import_module(module_name)
        _with_sys_path(root / "scripts", _import)
        return True, None
    except ModuleNotFoundError as exc:
        missing = exc.name or "<missing>"
        return False, f"missing dependency or module: {missing}"
    except Exception as exc:
        return False, str(exc)


def _run_subcommand(root: Path, script_name: str, args: tuple[str, ...], timeout: int | float = SCRIPT_HELP_TIMEOUT_SECONDS) -> tuple[int, str]:
    script = root / "scripts" / script_name
    if not script.exists():
        return 2, f"missing script: {script_name}"

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str((root / "scripts").resolve()) + (os.pathsep + existing_pythonpath if existing_pythonpath else "")
    process = subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(root),
        env=env,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    return process.returncode, (process.stdout or "") + (process.stderr or "")


def _extract_frontmatter(path: Path) -> tuple[dict[str, object], str]:
    if not path.exists():
        return {}, "missing"
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        return {}, str(exc)
    if not text.startswith("---"):
        return {}, "missing opening frontmatter"
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, "missing closing frontmatter delimiter"
    body = parts[1]
    out: dict[str, object] = {}
    current_list_key: str | None = None
    for raw in body.splitlines():
        line = raw.rstrip()
        if not line:
            current_list_key = None
            continue
        if line.startswith("  - ") and current_list_key:
            existing = out.setdefault(current_list_key, [])
            if isinstance(existing, list):
                existing.append(line[4:].strip())
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value == "":
            out[key] = []
            current_list_key = key
        else:
            out[key] = value
            current_list_key = None
    return out, ""


def _message_has_reply(inbox_dir: Path, message_id: str) -> bool:
    if not inbox_dir.exists():
        return False
    for path in inbox_dir.glob("*.md"):
        if path.name == ".gitkeep" or not path.is_file():
            continue
        meta, _ = _extract_frontmatter(path)
        if meta.get("in_reply_to") == message_id:
            return True
    return False


def _can_write_dir(path: Path) -> bool:
    if not path.exists():
        return False
    marker = path / ".__doctor_can_write"
    try:
        marker.write_text("ok\n", encoding="utf-8")
    except Exception:
        return False
    try:
        marker.unlink()
    except Exception:
        pass
    return True


def _run_toolrunner_import_checks(root: Path, findings: list[DoctorFinding]) -> None:
    try:
        mod, error = _module_import_check(root, "providers.agent_tools")
        if not mod:
            _findings_append(
                findings,
                "warning",
                area="toolrunner",
                path="scripts/providers/agent_tools.py",
                kind="toolrunner-import-error",
                detail=error or "import failed",
            )
            return

        def _runner_check() -> None:
            from providers import agent_tools

            runner = agent_tools.ToolRunner(root)
            denied_entries = []
            for command in (
                "python -c \"print(1)\"",
                "py -c \"print(1)\"",
                "python -m pip install requests",
                "git commit -am test",
                "python scripts/check_messages.py && python scripts/check_agent_docs.py",
            ):
                before = len(runner.command_audit)
                output = runner.run_command(command)
                new_audit = runner.command_audit[before:]
                matched = [entry for entry in new_audit if entry.startswith(f"blocked|{runner.command_profile}|{command}")]
                if not matched:
                    denied_entries.append(command)
                if not output.startswith("ERROR:"):
                    _findings_append(
                        findings,
                        "warning",
                        area="toolrunner",
                        path="scripts/providers/agent_tools.py",
                        kind="toolrunner-policy-weakened",
                        detail=f"command should be denied but was allowed: {command}",
                    )
            if denied_entries:
                _findings_append(
                    findings,
                    "warning",
                    area="toolrunner",
                    path="scripts/providers/agent_tools.py",
                    kind="toolrunner-audit-missing",
                    detail=f"denied commands missing audit entries: {', '.join(denied_entries)}",
                )

        _with_sys_path(root / "scripts", _runner_check)
    except Exception as exc:
        _findings_append(
            findings,
            "warning",
            area="toolrunner",
            path="scripts/providers/agent_tools.py",
            kind="toolrunner-check-failed",
            detail=f"unable to run toolrunner checks: {exc}",
        )


def _collect_stale_claims(claims_dir: Path, inbox_dir: Path, now: float | None = None) -> list[tuple[Path, dict]]:
    stale: list[tuple[Path, dict]] = []
    now_val = now if now is not None else time.time()
    if not claims_dir.is_dir():
        return stale
    for claim_file in claims_dir.glob("*.claim"):
        payload: dict | None = None
        try:
            raw = claim_file.read_text(encoding="utf-8")
            payload = json.loads(raw)
        except Exception:
            stale.append((claim_file, {}))
            continue
        if not isinstance(payload, dict):
            stale.append((claim_file, {}))
            continue

        try:
            expires_raw = payload.get("expires_at")
            expires_at = float(expires_raw)
        except (TypeError, ValueError):
            stale.append((claim_file, payload))
            continue
        if now_val <= expires_at:
            continue
        message_id = str(payload.get("message_id") or claim_file.stem)
        if not _message_has_reply(inbox_dir, message_id):
            stale.append((claim_file, payload))
    return stale


def _repair_runtime_directories(root: Path, actions: list[str]) -> int:
    repaired = 0
    paths = (
        root / "agents" / "messages",
        root / "agents" / "messages" / "inbox",
        root / "agents" / "runtime",
        root / "agents" / "runtime" / "claims",
        root / "agents" / "runtime" / "events",
        root / "agents" / "messages" / "archive",
        root / "agents" / "messages" / "samples",
    )
    for path in paths:
        if path.exists():
            continue
        if not _safe_mkdir(path):
            continue
        repaired += 1
        actions.append(f"created_dir {_rel(root, path)}")

    # Add stop-file parents expected by runtime stop checks.
    for rel in (".auto-runner-stop", ".orchestrator-stop", "agents/runtime/STOP_LOOP"):
        target = root / rel
        if not target.parent.exists() and _safe_mkdir(target.parent):
            repaired += 1
            actions.append(f"created_dir {_rel(root, target.parent)}")
    return repaired


def _repair_stale_claims(
    root: Path,
    claims_dir: Path,
    inbox_dir: Path,
    actions: list[str],
) -> int:
    repaired = 0
    stale_claims = _collect_stale_claims(claims_dir, inbox_dir)
    if not stale_claims:
        return 0
    for claim_file, payload in stale_claims:
        message_id = str(payload.get("message_id") or claim_file.stem)
        if _safe_unlink(claim_file):
            repaired += 1
            if payload:
                actions.append(f"removed_stale_claim {_rel(root, claim_file)} for message_id={message_id}")
            else:
                actions.append(f"removed_invalid_claim {_rel(root, claim_file)} for message_id={message_id}")
    return repaired


def apply_doctor_repairs(root: Path, plan: DoctorPlan) -> tuple[DoctorPlan, list[str]]:
    """Apply safe, idempotent repair operations and return updated plan + action log."""
    actions: list[str] = []

    root = root.resolve()
    claims_dir = root / "agents" / "runtime" / "claims"
    inbox_dir = root / "agents" / "messages" / "inbox"
    _repair_runtime_directories(root, actions)
    _repair_stale_claims(root, claims_dir, inbox_dir, actions)

    updated_plan, _ = build_doctor_plan(root)
    return updated_plan, actions


def _run_sync_check(root: Path, findings: list[DoctorFinding]) -> None:
    try:
        plan = _sync.build_sync_plan(root)
    except Exception as exc:
        _findings_append(
            findings,
            "warning",
            area="sync",
            path="scripts/",
            kind="sync-check-failed",
            detail=f"unable to run sync plan: {exc}",
        )
        return

    if plan.conflicts:
        _findings_append(
            findings,
            "warning",
            area="sync",
            path="agents/messages",
            kind="sync-conflict",
            detail=f"{len(plan.conflicts)} file(s) diverged from managed template and are blocked",
        )


def _run_lock_check(root: Path, findings: list[DoctorFinding], cfg_ok: bool) -> None:
    if not cfg_ok:
        return
    try:
        lp = _lock.build_lock_plan(root)
    except Exception as exc:
        _findings_append(
            findings,
            "warning",
            area="lock",
            path="agent_runtime.lock.json",
            kind="lock-check-failed",
            detail=f"unable to evaluate lock: {exc}",
        )
        return

    for f in lp.findings:
        if f.kind in {"missing-lock-file", "lock-out-of-date", "malformed-lock-file"}:
            _findings_append(
                findings,
                "blocker",
                area="lock",
                path=f.path,
                kind=f.kind,
                detail=f.detail,
            )
        else:
            _findings_append(
                findings,
                "warning",
                area="lock",
                path=f.path,
                kind=f.kind,
                detail=f.detail,
            )


def build_doctor_plan(root: Path) -> tuple[DoctorPlan, list[DoctorFinding]]:
    findings: list[DoctorFinding] = []
    root = root.resolve()

    for rel in REQUIRED_TEMPLATE_FILES:
        target = root / rel
        if not target.exists():
            _findings_append(
                findings,
                "blocker",
                area="template",
                path=rel,
                kind="missing-required-file",
                detail="required template artifact is missing",
            )

    for rel in REQUIRED_DOC_FILES:
        target = root / rel
        if not target.exists():
            _findings_append(
                findings,
                "warning",
                area="docs",
                path=rel,
                kind="missing-governance-doc",
                detail="required governance doc missing (non-fatal)",
            )

    for rel in STOP_FILES:
        target = root / rel
        parent = target.parent
        if not parent.exists():
            _findings_append(
                findings,
                "warning",
                area="stop-files",
                path=rel,
                kind="stop-parent-missing",
                detail="parent path for stop-file control is missing",
            )
        elif not _can_write_dir(parent):
            _findings_append(
                findings,
                "warning",
                area="stop-files",
                path=rel,
                kind="stop-parent-not-writable",
                detail="stop file parent is not writable",
            )

    inbox_dir = root / "agents" / "messages" / "inbox"
    runtime_dir = root / "agents" / "runtime"
    claims_dir = runtime_dir / "claims"
    events_dir = runtime_dir / "events"
    for path in (inbox_dir.parent, inbox_dir, runtime_dir, claims_dir, events_dir):
        if not path.exists():
            _findings_append(
                findings,
                "warning",
                area="runtime",
                path=str(path),
                kind="missing-runtime-dir",
                detail="runtime directory missing",
            )
            continue
        if not _can_write_dir(path):
            _findings_append(
                findings,
                "warning",
                area="runtime",
                path=str(path),
                kind="runtime-dir-not-writable",
                detail="directory exists but not writable by current process",
            )

    stale_claims = 0
    now = time.time()
    if claims_dir.is_dir():
        for claim_file in claims_dir.glob("*.claim"):
            try:
                raw = claim_file.read_text(encoding="utf-8")
                payload = json.loads(raw)
            except Exception:
                _findings_append(
                    findings,
                    "warning",
                    area="runtime",
                    path=_rel(root, claim_file),
                    kind="stale-claim-parse-error",
                    detail="claim file is malformed JSON",
                )
                continue

            if not isinstance(payload, dict):
                _findings_append(
                    findings,
                    "warning",
                    area="runtime",
                    path=_rel(root, claim_file),
                    kind="stale-claim-invalid",
                    detail="claim payload is not an object",
                )
                continue

            expires = payload.get("expires_at")
            try:
                expires_at = float(expires)
            except (TypeError, ValueError):
                continue
            if now <= expires_at:
                continue

            message_id = str(payload.get("message_id") or claim_file.stem)
            reply_exists = _message_has_reply(inbox_dir, message_id)
            stale_claims += 1
            if not reply_exists:
                _findings_append(
                    findings,
                    "warning",
                    area="runtime",
                    path=_rel(root, claim_file),
                    kind="stale-claim-without-reply",
                    detail=(
                        f"claim is stale since {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expires_at))} "
                        "and no in-reply message was found"
                    ),
                )

    if stale_claims == 0:
        _findings_append(
            findings,
            "info",
            area="runtime",
            path="agents/runtime/claims",
            kind="stale-claim-none",
            detail="no stale claim files currently detected",
        )

    cfg_ok = True
    try:
        cfg = _config.load_config(root)
        _findings_append(
            findings,
            "info",
            area="config",
            path="agent_runtime.yml",
            kind="config-loaded",
            detail=f"project={cfg.project} sync_mode={cfg.sync_mode}",
        )
    except Exception as exc:
        cfg_ok = False
        _findings_append(
            findings,
            "blocker",
            area="config",
            path="agent_runtime.yml",
            kind="config-invalid",
            detail=str(exc),
        )

    _run_lock_check(root, findings, cfg_ok)
    _run_sync_check(root, findings)

    for script, args in SCRIPT_HELP:
        script_path = root / "scripts" / script
        if not script_path.exists():
            continue
        rc, output = _run_subcommand(root, script, args)
        if rc != 0:
            _findings_append(
                findings,
                "blocker",
                area="template-scripts",
                path=f"scripts/{script}",
                kind="script-help-failed",
                detail=f"{script} --help failed with rc={rc}: {output[:200]!r}",
            )

    for rel in (
        "scripts/pipeline.py",
        "scripts/orchestrator_safety_gate.py",
        "schemas/task.schema.json",
    ):
        if (root / rel).exists():
            continue
        _findings_append(
            findings,
            "blocker",
            area="template",
            path=rel,
            kind="missing-required-file",
            detail="required runtime dependency missing",
        )

    for module_name in PROVIDER_MODULES:
        ok, detail = _module_import_check(root, module_name)
        if ok:
            if module_name == "providers.openai":
                continue
            continue
        severity = "warning"
        if module_name in OPTIONAL_DEPENDENCY_EXTRAS:
            missing = set((detail or "").split()) if detail else set()
            if missing.intersection(OPTIONAL_DEPENDENCY_EXTRAS[module_name]):
                detail = f"{detail} (optional dependency, non-blocking for dummy provider path)"
                severity = "warning"
        _findings_append(
            findings,
            severity,
            area="provider-imports",
            path=module_name.replace(".", "/") + ".py",
            kind="provider-import-failed",
            detail=detail or "import failed",
        )

    _run_toolrunner_import_checks(root, findings)

    return DoctorPlan(root=root, findings=tuple(findings), config_loaded=cfg_ok), findings


def render(plan: DoctorPlan) -> str:
    lines = [
        "# Agent Runtime Doctor",
        "",
        f"root={plan.root}",
        f"blockers={plan.blocker_count}",
        f"warnings={plan.warning_count}",
        f"infos={plan.info_count}",
        "",
        "| Severity | Area | Path | Kind | Detail |",
        "|---|---|---|---|---|",
    ]
    for finding in plan.findings:
        lines.append(
            f"| {finding.severity} | {finding.area} | {finding.path} | {finding.kind} | {finding.detail} |"
        )
    if not plan.findings:
        lines.append("| info | doctor | summary | ok | no findings |")
    return "\n".join(lines)


def _finding_json(finding: DoctorFinding) -> dict[str, str]:
    return {
        "severity": finding.severity,
        "area": finding.area,
        "path": finding.path,
        "kind": finding.kind,
        "detail": finding.detail,
    }


def _config_json(root: Path) -> dict[str, object]:
    """Return a useful projection even when configuration validation failed."""
    source_path = root / _config.CONFIG_FILE
    try:
        cfg = _config.load_config(root)
    except Exception:
        source_schema = "unknown"
        try:
            document = _config._parse_document(_config.config_path(root))
            source_schema = str(document.get("schema", _config.V1_SCHEMA))
            source_path = _config.config_path(root)
        except Exception:
            pass
        return {"source_schema": source_schema, "source_path": _rel(root, source_path), "valid": False}
    ownership = {mode: list(paths) for mode, paths in cfg.ownership}
    return {
        "valid": True,
        "source_schema": cfg.source_schema,
        "effective_schema": cfg.effective_schema,
        "source_path": _rel(root, cfg.path),
        "project": cfg.project,
        "upstream": {
            "package": cfg.upstream_package,
            "remote_url": cfg.upstream_remote_url,
            "ref": cfg.upstream_ref,
        },
        "sync": {
            "mode": cfg.sync_mode,
            "allow_silent_overwrite": cfg.allow_silent_overwrite,
            "unmanaged_paths": list(cfg.unmanaged_paths),
        },
        "profiles": list(cfg.profiles),
        "capabilities": list(cfg.capabilities),
        "ownership": ownership,
        "host": {
            "context": {
                "path": cfg.host_context.path,
                "present": cfg.host_context.present,
                "purpose": cfg.host_context.purpose,
                "domain": cfg.host_context.domain,
                "safety_constraints": list(cfg.host_context.safety_constraints),
                "role_mapping": dict(cfg.host_context.role_mapping),
                "read_more": list(cfg.host_context.read_more),
            },
            "role_overlay": cfg.role_overlay,
            "risk_paths": list(cfg.risk_paths),
            "state_adapters": dict(cfg.state_adapters),
        },
    }


def render_json(plan: DoctorPlan, *, actions: list[str] | None = None) -> str:
    findings = sorted(
        (_finding_json(finding) for finding in plan.findings),
        key=lambda item: (item["severity"], item["area"], item["path"], item["kind"], item["detail"]),
    )
    payload: dict[str, object] = {
        "schema": "agent-runtime-doctor/v1",
        "root": str(plan.root),
        "config": _config_json(plan.root),
        "findings": findings,
        "summary": {
            "blockers": plan.blocker_count,
            "warnings": plan.warning_count,
            "infos": plan.info_count,
        },
    }
    if actions is not None:
        payload["repair_actions"] = actions
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)


def run_doctor(root: Path, *, check: bool, repair: bool = False, json_output: bool = False) -> int:
    plan, _ = build_doctor_plan(root)
    if repair:
        updated, actions = apply_doctor_repairs(root, plan)
        if json_output:
            print(render_json(updated, actions=actions))
            return 1 if check and updated.blocker_count else 0
        print(render(updated))
        if actions:
            print(f"{REPAIR_ACTION_PREFIX} performed {len(actions)} actions")
            for action in actions:
                print(f"{REPAIR_ACTION_PREFIX} {action}")
        else:
            print(f"{REPAIR_ACTION_PREFIX} no actions needed")
        if check and updated.blocker_count:
            return 1
        return 0

    print(render_json(plan) if json_output else render(plan))
    if check and plan.blocker_count:
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run host runtime health checks")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Host project root")
    parser.add_argument("--check", action="store_true", help="Fail if blockers exist")
    parser.add_argument("--repair", action="store_true", help="Attempt safe auto-repair actions")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable doctor report")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_doctor(args.root, check=args.check, repair=args.repair, json_output=args.json)


if __name__ == "__main__":
    raise SystemExit(main())
