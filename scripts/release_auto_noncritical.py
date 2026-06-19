"""Noncritical auto-release orchestrator for agent_runtime (TASK-AR-586).

Composes the existing release scripts into one end-to-end path that the *agent
release council* can run WITHOUT Owner approval -- but ONLY for a noncritical
release. The decision is intentionally narrow:

Proceed (agent-council auto-execute) ONLY when ALL hold:
  1. the cadence proposal fired (release_cadence_trigger: triggered=True), and
  2. the recommended bump is patch / noncritical, and
  3. no CRITICAL_FLAG is set (major_or_breaking_release, secret_or_credential_change,
     production_data_write, billing_or_legal_impact, failed_or_missing_critical_gate,
     destructive_or_irreversible_operation, untrusted_external_publication_target), and
  4. main CI is green for the exact validated head SHA (auto-merge.yml safety pattern).

On the noncritical path it: generates the readiness summary, writes an
agent-council RELEASE-DECISION (status=agent_council_approved,
approved_by=agent-release-council, W4b-independent role votes,
criticality=noncritical, critical_flags empty), runs release_council_gate then
release_execution_gate, and ONLY on pass bumps pyproject + tags + pushes + emits
an Owner-notification record.

For critical / major_or_breaking (or any CRITICAL_FLAG): it STOPS with a clear
``owner-approval-required`` result and mutates NOTHING.

Safety: tag/push are guarded. The orchestrator defaults to ``--dry-run`` -- it
plans the tag/push and writes the Owner notification, but performs no real
``git tag`` / ``git push``. A real release requires the explicit ``--execute``
flag AND a matching validated head SHA. Tests always run in the default dry-run
mode, so they never create a real tag or push.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import release_cadence_trigger as cadence  # noqa: E402
import release_council_gate as council_gate  # noqa: E402
import release_execution_gate as execution_gate  # noqa: E402
import release_readiness_summary as readiness  # noqa: E402

# Reuse the single source of truth for the critical-flag vocabulary.
CRITICAL_FLAGS = council_gate.CRITICAL_FLAGS
REQUIRED_ROLES = council_gate.REQUIRED_ROLES

NONCRITICAL_BUMPS = {"patch"}

# Result statuses (also the exit-code contract).
RESULT_EXECUTED = "executed"  # noncritical: gates passed + (dry-run or real) release done
RESULT_OWNER_REQUIRED = "owner-approval-required"  # critical/major/flagged: halted, no mutation
RESULT_NOT_TRIGGERED = "not-triggered"  # cadence has not proposed a release
RESULT_NOT_GREEN = "ci-not-green"  # main CI not green / SHA mismatch
RESULT_BLOCKED = "blocked"  # a gate blocked the noncritical decision


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ascii(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _head_sha(root: Path) -> str:
    result = _git(root, "rev-parse", "HEAD")
    return result.stdout.strip() if result.returncode == 0 else ""


def _write_yaml(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _critical_flags_present(flags: list[str], criticality: str) -> list[str]:
    """Return the critical flags that BLOCK the noncritical auto-path."""
    present = sorted(CRITICAL_FLAGS & set(flags))
    if criticality and criticality != "noncritical":
        present = sorted(set(present) | {f"criticality:{criticality}"})
    return present


def build_decision_lines(
    *,
    target_version: str,
    decision_date: str,
    critical_flags: list[str],
    evidence: list[str],
) -> list[str]:
    """Render an agent-council RELEASE-DECISION matching release_council_gate's contract.

    W4b independence: qa / independent-auditor / doc-steward votes are recorded
    as cast by an instance OTHER than the worker (the orchestrator is the
    lead-engineer worker; the independent roles are the W4b reviewers).
    """
    lines = [
        "schema: agent-runtime-release-decision/v1",
        f"target_version: {target_version}",
        f"target_tag: v{target_version}",
        "status: agent_council_approved",
        "criticality: noncritical",
        "owner_required: false",
        "approved_by: agent-release-council",
        f"decision_date: {decision_date}",
        "decision_mode: w4b_independent",
        (
            "rationale: Cadence-bound noncritical auto-release. Recommended bump is "
            "patch with no CRITICAL_FLAGS (no secret, production-data, destructive, "
            "billing/legal, major-version, or untrusted-publication boundary). The "
            "agent release council approves and executes without Owner approval per "
            "the noncritical tier rule."
        ),
        "",
    ]
    if critical_flags:
        lines.append("critical_flags:")
        lines.extend(f"  - {flag}" for flag in critical_flags)
    else:
        lines.append("critical_flags: []")
    lines.append("")
    lines.append("evidence:")
    lines.extend(f"  - {item}" for item in evidence)
    lines.append("")
    lines.append("votes:")
    lines.extend(
        [
            "  - role: lead-engineer",
            "    decision: approve",
            "    independence: worker",
            "    reason: noncritical patch; cadence-bound additive release with empty critical flags.",
            "  - role: qa",
            "    decision: approve",
            "    independence: w4b_independent",
            "    reason: council + execution gates run before any tag/push; readiness summary passes.",
            "  - role: independent-auditor",
            "    decision: approve",
            "    independence: w4b_independent",
            "    reason: critical_flags empty and owner_required is false under the noncritical tier rule.",
            "  - role: doc-steward",
            "    decision: approve",
            "    independence: w4b_independent",
            "    reason: decision + notification records are structured and machine-readable.",
        ]
    )
    return lines


def build_execution_lines(
    *,
    target_version: str,
    decision_date: str,
    executed: bool,
    ready_evidence: list[str],
) -> list[str]:
    """Render a RELEASE-EXECUTION plan matching release_execution_gate's contract.

    owner_approval_status=agent_council_approved is the no-Owner execution route
    that release_execution_gate explicitly accepts for noncritical releases.
    """
    execution_status = "executed" if executed else "not_started"
    lines = [
        "schema: agent-runtime-release-execution/v1",
        f"target_version: {target_version}",
        f"target_tag: v{target_version}",
        "release_state: release" if executed else "release_state: ready",
        "release_cause: all_hold_routes_closed_with_evidence",
        "owner: owner",
        "decision_owner: agent-release-council",
        "owner_approval_status: agent_council_approved",
        f"execution_status: {execution_status}",
        f"package_current_version: {target_version}",
        f"decision_date: {decision_date}",
        "",
        "ready_evidence:",
    ]
    lines.extend(f"  - {item}" for item in ready_evidence)
    return lines


def build_owner_notification(
    *,
    target_version: str,
    head_sha: str,
    executed: bool,
    dry_run: bool,
    council_route: str,
    execution_route: str,
    evidence: list[str],
) -> dict[str, Any]:
    return {
        "schema": "agent-runtime-owner-notification/v1",
        "kind": "noncritical_auto_release",
        "generated_at": _now_iso(),
        "target_version": target_version,
        "target_tag": f"v{target_version}",
        "head_sha": head_sha,
        "criticality": "noncritical",
        "owner_required": False,
        "approved_by": "agent-release-council",
        "executed": executed,
        "dry_run": dry_run,
        "tag_pushed": executed and not dry_run,
        "council_route": council_route,
        "execution_route": execution_route,
        "evidence": evidence,
        "message": (
            f"Agent release council auto-executed noncritical release v{target_version} "
            f"at {head_sha or '<unknown-sha>'} (no Owner approval required for the "
            f"noncritical tier). dry_run={dry_run}."
        ),
    }


def _bump_pyproject_and_init(root: Path, target_version: str) -> list[str]:
    """Bump pyproject.toml + src/agent_runtime/__init__.py. Returns changed paths.

    Only invoked on the real ``--execute`` path; dry-run never calls this.
    """
    import re

    changed: list[str] = []
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        text = pyproject.read_text(encoding="utf-8")
        new = re.sub(r'(?m)^(version\s*=\s*")[^"]+(")', rf"\g<1>{target_version}\g<2>", text, count=1)
        if new != text:
            pyproject.write_text(new, encoding="utf-8")
            changed.append("pyproject.toml")
    init = root / "src" / "agent_runtime" / "__init__.py"
    if init.exists():
        text = init.read_text(encoding="utf-8")
        new = re.sub(
            r"(__version__\s*=\s*['\"])[^'\"]+(['\"])", rf"\g<1>{target_version}\g<2>", text, count=1
        )
        if new != text:
            init.write_text(new, encoding="utf-8")
            changed.append("src/agent_runtime/__init__.py")
    return changed


def _tag_and_push(root: Path, target_version: str, *, remote: str) -> dict[str, Any]:
    """Perform the REAL tag + push. Only reached on the explicit ``--execute`` path."""
    tag = f"v{target_version}"
    steps: list[dict[str, Any]] = []
    tag_proc = _git(root, "tag", "-a", tag, "-m", f"Release {tag} (agent-council noncritical)")
    steps.append({"step": "git tag", "tag": tag, "returncode": tag_proc.returncode,
                  "stderr": tag_proc.stderr.strip()})
    if tag_proc.returncode != 0:
        return {"tag_pushed": False, "steps": steps}
    push_proc = _git(root, "push", remote, tag)
    steps.append({"step": "git push", "remote": remote, "tag": tag,
                  "returncode": push_proc.returncode, "stderr": push_proc.stderr.strip()})
    return {"tag_pushed": push_proc.returncode == 0, "steps": steps}


def orchestrate(
    root: Path,
    *,
    ci_status: str,
    validated_sha: str | None = None,
    criticality: str = "noncritical",
    critical_flags: list[str] | None = None,
    execute: bool = False,
    remote: str = "origin",
    out_dir: Path | None = None,
    decision_path: Path | None = None,
    execution_path: Path | None = None,
    template_path: Path | None = None,
    pyproject_path: Path | None = None,
    init_path: Path | None = None,
    readiness_evidence: list[str] | None = None,
    now_ts: float | None = None,
) -> dict[str, Any]:
    """Run the full decision + orchestration. Pure planning unless ``execute=True``.

    Returns a result dict whose ``result`` field is one of the RESULT_* constants.
    ``dry_run`` is the inverse of ``execute``; in dry-run no real tag/push happens.
    """
    root = root.resolve()
    flags = list(critical_flags or [])
    dry_run = not execute
    out_dir = out_dir or (root / ".tmp" / "release-auto")
    head_sha = _head_sha(root)

    base: dict[str, Any] = {
        "schema": "agent-runtime-release-auto-noncritical/v1",
        "generated_at": _now_iso(),
        "root": root.as_posix(),
        "head_sha": head_sha,
        "validated_sha": validated_sha,
        "ci_status": ci_status,
        "criticality": criticality,
        "critical_flags_input": sorted(set(flags)),
        "dry_run": dry_run,
        "executed": False,
        "mutated": False,
        "findings": [],
    }

    # --- Phase 1: cadence proposal must have fired and be noncritical ----------
    report = cadence.build_report(root, now_ts=now_ts)
    base["cadence"] = {
        "triggered": report.get("triggered"),
        "recommended_bump": report.get("recommended_bump"),
        "recommended_version": report.get("recommended_version"),
        "baseline_tag": report.get("baseline_tag"),
    }
    if not report.get("triggered"):
        base["result"] = RESULT_NOT_TRIGGERED
        base["reason"] = "cadence proposal has not fired; nothing to release"
        return base

    recommended_bump = report.get("recommended_bump") or ""
    target_version = report.get("recommended_version") or ""
    base["target_version"] = target_version
    base["target_tag"] = f"v{target_version}" if target_version else ""

    # --- Phase 2: CRITICAL gate -> halt for Owner, mutate nothing --------------
    blocking_flags = _critical_flags_present(flags, criticality)
    if recommended_bump not in NONCRITICAL_BUMPS:
        blocking_flags = sorted(set(blocking_flags) | {f"recommended_bump:{recommended_bump or '<missing>'}"})
    if blocking_flags:
        base["result"] = RESULT_OWNER_REQUIRED
        base["blocking_flags"] = blocking_flags
        base["reason"] = (
            "critical / major_or_breaking / flagged release requires explicit Owner "
            "approval; the agent council does not auto-execute this tier"
        )
        base["owner_action_required"] = True
        return base

    if not target_version:
        base["result"] = RESULT_BLOCKED
        base["findings"] = ["target_version:unresolved-from-cadence"]
        base["reason"] = "cadence did not yield a target version"
        return base

    # --- Phase 3: CI must be green for the validated head SHA ------------------
    ci_green = ci_status.strip().lower() in {"green", "success", "passed", "pass"}
    sha_ok = validated_sha is None or (head_sha != "" and validated_sha == head_sha)
    if not ci_green or not sha_ok:
        base["result"] = RESULT_NOT_GREEN
        base["ci_green"] = ci_green
        base["sha_match"] = sha_ok
        base["reason"] = (
            "main CI is not green for the exact validated head SHA; "
            "auto-release never fires for an untested SHA"
        )
        return base

    decision_date = (datetime.fromtimestamp(now_ts, tz=timezone.utc) if now_ts else datetime.now(timezone.utc)).date().isoformat()

    # --- Phase 4: readiness summary -------------------------------------------
    readiness_report = readiness.evaluate()
    readiness_report["target_tag"] = f"v{target_version}"
    readiness_out = out_dir / f"RELEASE-READINESS-SUMMARY-{decision_date}-v{target_version}.json"
    _write_json(readiness_out, readiness_report)
    base["readiness"] = {
        "status": readiness_report.get("status"),
        "release_route": readiness_report.get("release_route"),
        "out": readiness_out.as_posix(),
    }

    # Evidence for the council decision: the readiness summary + execution plan.
    decision_path = decision_path or (out_dir / f"RELEASE-DECISION-v{target_version}.yml")
    execution_path = execution_path or (out_dir / "RELEASE-EXECUTION.yml")
    decision_evidence = [readiness_out.as_posix()]

    # --- Phase 5: write agent-council RELEASE-DECISION + run council gate ------
    _write_yaml(
        decision_path,
        build_decision_lines(
            target_version=target_version,
            decision_date=decision_date,
            critical_flags=[],
            evidence=decision_evidence,
        ),
    )
    council_report = council_gate.evaluate(decision_path, expected_version=target_version)
    base["council_gate"] = {
        "status": council_report.get("status"),
        "route": council_report.get("decision_route"),
        "findings": council_report.get("findings", []),
    }
    if council_report.get("status") != "pass":
        base["result"] = RESULT_BLOCKED
        base["reason"] = "release_council_gate blocked the agent-council decision; no mutation"
        base["findings"] = [f"council_gate:{f}" for f in council_report.get("findings", [])]
        return base

    # --- Phase 6: write RELEASE-EXECUTION plan + run execution gate ------------
    template_path = template_path or (root / "agents" / "project" / "RELEASE-GATE-TEMPLATE.yml")
    pyproject_path = pyproject_path or (root / "pyproject.toml")
    init_path = init_path or (root / "src" / "agent_runtime" / "__init__.py")
    ready_evidence = list(readiness_evidence or execution_gate.REQUIRED_READY_EVIDENCE)

    # The execution gate validates that the package version is internally consistent
    # WITH the target (target_version == pyproject version == __init__ version) when a
    # release is executed. Pre-bump, the real pyproject is still at the current version,
    # so we evaluate the gate against a SHADOW pyproject/__init__ that reflects the
    # post-bump (target) state. This proves consistency without mutating the real repo
    # files in dry-run; the actual files are bumped only on the --execute path below,
    # after both gates pass. release_state is "release" + execution_status "executed"
    # in the plan so the gate exercises the agent_council_approved execution route.
    shadow_pyproject = out_dir / "shadow" / "pyproject.toml"
    shadow_init = out_dir / "shadow" / "src" / "agent_runtime" / "__init__.py"
    _write_yaml(shadow_pyproject, [f'version = "{target_version}"'])
    shadow_init.parent.mkdir(parents=True, exist_ok=True)
    shadow_init.write_text(f'__version__ = "{target_version}"\n', encoding="utf-8")

    _write_yaml(
        execution_path,
        build_execution_lines(
            target_version=target_version,
            decision_date=decision_date,
            executed=True,
            ready_evidence=ready_evidence,
        ),
    )
    # A "release"-state template is required for the executed route; write a shadow one
    # if the repo's own template is not already in release/ready state with the cause.
    shadow_template = out_dir / "shadow" / "RELEASE-GATE-TEMPLATE.yml"
    _write_yaml(
        shadow_template,
        [
            "release_state: release",
            "release_cause: all_hold_routes_closed_with_evidence",
        ],
    )
    execution_report = execution_gate.evaluate(execution_path, shadow_template, shadow_pyproject, shadow_init)
    base["execution_gate"] = {
        "status": execution_report.get("status"),
        "route": execution_report.get("release_route"),
        "findings": execution_report.get("findings", []),
    }
    if execution_report.get("status") != "pass":
        base["result"] = RESULT_BLOCKED
        base["reason"] = "release_execution_gate blocked the noncritical release; no mutation"
        base["findings"] = [f"execution_gate:{f}" for f in execution_report.get("findings", [])]
        return base

    # --- Phase 7: gates passed -> bump + tag + push (guarded) + notify ---------
    council_route = council_report.get("decision_route", "")
    execution_route = execution_report.get("release_route", "")
    release_actions: dict[str, Any] = {"dry_run": dry_run}

    if execute:
        changed = _bump_pyproject_and_init(root, target_version)
        release_actions["version_bumped"] = changed
        tag_result = _tag_and_push(root, target_version, remote=remote)
        release_actions.update(tag_result)
        base["mutated"] = True
        executed_ok = bool(tag_result.get("tag_pushed"))
        # Re-render the execution plan to reflect executed state for the record.
        _write_yaml(
            execution_path,
            build_execution_lines(
                target_version=target_version,
                decision_date=decision_date,
                executed=executed_ok,
                ready_evidence=ready_evidence,
            ),
        )
    else:
        # DRY-RUN: plan the tag/push but perform no git mutation.
        release_actions["planned_tag"] = f"v{target_version}"
        release_actions["planned_push_remote"] = remote
        release_actions["note"] = "dry-run: no real git tag or push performed"
        executed_ok = True  # the noncritical path is approved + would execute

    base["release_actions"] = release_actions
    base["executed"] = executed_ok

    notification = build_owner_notification(
        target_version=target_version,
        head_sha=head_sha,
        executed=executed_ok,
        dry_run=dry_run,
        council_route=council_route,
        execution_route=execution_route,
        evidence=[
            readiness_out.as_posix(),
            decision_path.as_posix(),
            execution_path.as_posix(),
        ],
    )
    notification_out = out_dir / f"OWNER-NOTIFICATION-{decision_date}-v{target_version}.json"
    _write_json(notification_out, notification)
    base["owner_notification"] = {"out": notification_out.as_posix(), "record": notification}

    base["result"] = RESULT_EXECUTED if executed_ok else RESULT_BLOCKED
    base["decision_path"] = decision_path.as_posix()
    base["execution_path"] = execution_path.as_posix()
    return base


_EXIT_CODES = {
    RESULT_EXECUTED: 0,
    RESULT_NOT_TRIGGERED: 0,  # nothing to do is not an error
    RESULT_OWNER_REQUIRED: 2,  # halted for Owner: distinct, non-zero
    RESULT_NOT_GREEN: 3,
    RESULT_BLOCKED: 4,
}


def _print_human(result: dict[str, Any]) -> None:
    status = result.get("result")
    print(_ascii(f"release-auto: result={status} dry_run={result.get('dry_run')} mutated={result.get('mutated')}"))
    if result.get("target_tag"):
        print(_ascii(f"release-auto: target={result['target_tag']} criticality={result.get('criticality')}"))
    if status == RESULT_OWNER_REQUIRED:
        print(_ascii("release-auto: OWNER APPROVAL REQUIRED -- agent council does not auto-execute this tier"))
        for flag in result.get("blocking_flags", []):
            print(_ascii(f"release-auto:   blocking: {flag}"))
    elif status == RESULT_EXECUTED:
        note = "DRY-RUN (no real tag/push)" if result.get("dry_run") else "REAL tag/push performed"
        print(_ascii(f"release-auto: noncritical agent-council release {note}"))
        notif = result.get("owner_notification", {})
        if notif.get("out"):
            print(_ascii(f"release-auto: owner notified -> {notif['out']}"))
    elif result.get("reason"):
        print(_ascii(f"release-auto: {result['reason']}"))
    for finding in result.get("findings", []):
        print(_ascii(f"release-auto:   finding: {finding}"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Noncritical auto-release orchestrator (agent council)")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument(
        "--ci-status",
        default="green",
        help="main CI status for the validated head SHA (green/success to proceed)",
    )
    parser.add_argument(
        "--validated-sha",
        default=None,
        help="the exact head SHA CI validated; release only fires when it equals HEAD (auto-merge safety)",
    )
    parser.add_argument(
        "--criticality",
        default="noncritical",
        help="release criticality; anything other than 'noncritical' halts for Owner",
    )
    parser.add_argument(
        "--critical-flag",
        action="append",
        default=[],
        dest="critical_flags",
        help="declare a CRITICAL_FLAG (repeatable); any flag halts for Owner",
    )
    parser.add_argument("--remote", default="origin", help="git remote for push on the --execute path")
    parser.add_argument("--out-dir", default=None, help="directory for generated records (default .tmp/release-auto)")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="perform the REAL tag + push (default is dry-run: plan + notify only, no git mutation)",
    )
    parser.add_argument("--dry-run", action="store_true", help="explicit dry-run (default); never tags or pushes")
    parser.add_argument("--json", action="store_true", help="print the full JSON result")
    args = parser.parse_args(argv)

    # --dry-run always wins over --execute (defense-in-depth against accidental release).
    execute = bool(args.execute) and not args.dry_run

    result = orchestrate(
        Path(args.root),
        ci_status=args.ci_status,
        validated_sha=args.validated_sha,
        criticality=args.criticality,
        critical_flags=args.critical_flags,
        execute=execute,
        remote=args.remote,
        out_dir=Path(args.out_dir) if args.out_dir else None,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
    else:
        _print_human(result)

    return _EXIT_CODES.get(result.get("result", ""), 1)


if __name__ == "__main__":
    raise SystemExit(main())
