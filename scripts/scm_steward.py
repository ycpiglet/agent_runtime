"""SCM steward: periodic hygiene loop over branch/worktree/stash/PR/issue/claim debt.

Detects SCM debt before a human notices, reports it in one consolidated view,
and cleans it only through report -> approve -> execute discipline.

Report sections
- worktrees: zombie worktrees / merged branches (delegates to
  scripts/worktree_lifecycle_gate.py, TASK-AR-505) plus unmerged agent-branch
  divergence context from scripts/inflight_overlay.py (TASK-AR-513).
- claims:   stale active claims whose lease expiry is in the past
  (lifecycle gate logic, consumed not reimplemented).
- stashes:  un-reclaimed archive stash refs (refs/heads/archive/stashes/* and
  the origin mirror); refs older than the threshold are flagged with
  recovery guidance.
- github:   open PR aging / lingering drafts, and open issues whose
  TASK-*/BUG-* references are missing from the work registry
  (agents/lead_engineer/tasks/ + BACKLOG.md). gh calls are read-only here.
- views:    generated-view drift via the --check modes of the backlog board,
  work-item classifier, and evidence index generator.

Modes
- report: read-only. One consolidated ASCII report (or --json).
  ALWAYS exits 0 -- reporting is non-blocking by contract.
- clean: requires --approve <section|all>; without approval it only reports
  and changes nothing. Zombie worktree cleanup delegates to the lifecycle
  gate's guarded cleanup (local-only). Every other section PRINTS the exact
  commands it would run. gh mutations execute only behind --execute-gh,
  which is Owner-gated.
- pr-open / pr-close / issue-sync: gh helpers (dry-run by default) for
  task-branch draft PR creation (title = task id, body = claim handoff
  link), closeout PR close/comment, and W3 adjacent-problem intake <-> gh
  issue create/close sync.

Output is ASCII-only so cp949 consoles render it safely.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import inflight_overlay  # noqa: E402  (branch divergence, TASK-AR-513)
import worktree_lifecycle_gate as lifecycle_gate  # noqa: E402  (zombies, TASK-AR-505)

SCHEMA = "agent-runtime-scm-steward/v1"
SECTIONS = ("worktrees", "claims", "stashes", "github", "views")
DEFAULT_PR_AGE_DAYS = 3.0
DEFAULT_STASH_AGE_DAYS = 7.0
ARCHIVE_STASH_PATTERNS = (
    "refs/heads/archive/stashes",
    "refs/remotes/origin/archive/stashes",
)
WORK_REF_RE = re.compile(r"\b(TASK-[A-Z]+(?:-[A-Z]+)*-\d+|BUG-\d+)\b")
TASKS_REL = Path("agents/lead_engineer/tasks")
BACKLOG_REL = Path("BACKLOG.md")
DONE_TASK_STATUSES = {"completed", "done", "released", "closed"}

# (view name, check argv, regenerate argv) -- argv[0] is repo-relative.
VIEW_PROBES: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    (
        "backlog-board",
        ("scripts/backlog_board.py", "--check"),
        ("scripts/backlog_board.py", "--write"),
    ),
    (
        "work-item-classifier",
        ("scripts/work_item_classifier.py", "--check"),
        ("scripts/work_item_classifier.py", "--write"),
    ),
    (
        "evidence-index",
        ("scripts/evidence_index_generator.py", "--check"),
        ("scripts/evidence_index_generator.py", "--write"),
    ),
)

# Injectable command runner: (argv, cwd) -> (returncode, stdout, stderr).
# Tests inject a fake runner so gh sections need no network/subprocess.
CommandRunner = Callable[[list[str], Path], tuple[int, str, str]]


def default_runner(args: list[str], cwd: Path) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as exc:
        return 127, "", str(exc)
    return result.returncode, result.stdout or "", result.stderr or ""


def _git(root: Path, *args: str) -> tuple[int, str, str]:
    return default_runner(["git", "-C", str(root), *args], root)


def _ascii(value: Any) -> str:
    return str(value if value is not None else "").encode("ascii", "replace").decode("ascii")


def _parse_iso(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _age_days(now: datetime, then: datetime | None) -> float | None:
    if then is None:
        return None
    return round((now - then).total_seconds() / 86400.0, 2)


def _finding(severity: str, kind: str, subject: Any, detail: Any) -> dict[str, str]:
    return {
        "severity": severity,
        "kind": kind,
        "subject": _ascii(subject),
        "detail": _ascii(detail),
    }


def _format_command(args: list[str]) -> str:
    parts: list[str] = []
    for arg in args:
        if re.search(r"[\s\"']", arg):
            parts.append('"' + arg.replace('"', '\\"') + '"')
        else:
            parts.append(arg)
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Work registry helpers (issue cross-check)
# ---------------------------------------------------------------------------


def load_registered_ids(root: Path) -> set[str]:
    """Work-item ids known to the repo: task file names + BACKLOG.md text."""
    ids: set[str] = set()
    tasks_dir = root / TASKS_REL
    if tasks_dir.is_dir():
        for path in tasks_dir.glob("*.md"):
            ids.update(match.upper() for match in WORK_REF_RE.findall(path.name))
    backlog = root / BACKLOG_REL
    if backlog.is_file():
        try:
            text = backlog.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        ids.update(match.upper() for match in WORK_REF_RE.findall(text))
    return ids


def load_task_status_index(root: Path) -> dict[str, str]:
    """Map registered task id -> frontmatter status (lowercase)."""
    index: dict[str, str] = {}
    tasks_dir = root / TASKS_REL
    if not tasks_dir.is_dir():
        return index
    for path in sorted(tasks_dir.glob("*.md")):
        match = WORK_REF_RE.search(path.name)
        if not match:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        status = inflight_overlay.frontmatter_status(text) or "unknown"
        index[match.group(1).upper()] = status.strip().lower()
    return index


def _extract_refs(*texts: str) -> list[str]:
    found: set[str] = set()
    for text in texts:
        found.update(match.upper() for match in WORK_REF_RE.findall(text or ""))
    return sorted(found)


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------


def build_worktrees_section(
    root: Path,
    claims: list[dict[str, Any]],
    now: datetime,
    retention_days: float,
    base_ref_arg: str,
) -> dict[str, Any]:
    worktrees = lifecycle_gate.list_worktrees(root)
    base_ref = lifecycle_gate.resolve_base_ref(root, base_ref_arg)
    verdicts = [
        lifecycle_gate.evaluate_worktree(root, worktree, claims, base_ref, retention_days, now)
        for worktree in worktrees
    ]
    zombies = [v for v in verdicts if v.zombie]
    cleanable = [v for v in zombies if v.cleanable]
    exempt = [v for v in zombies if v.exempt_reason]

    findings: list[dict[str, str]] = []
    for verdict in zombies:
        eligible = verdict.eligible_since.isoformat() if verdict.eligible_since else "unknown"
        detail = (
            f"branch={verdict.worktree.branch or 'detached'} "
            f"claim={verdict.claim_id} eligible_since={eligible}"
        )
        if verdict.exempt_reason:
            detail += f" exempt={verdict.exempt_reason}"
        findings.append(_finding("watch", "zombie-worktree", verdict.worktree.rel, detail))

    try:
        overlay = inflight_overlay.build_overlay(root, base=base_ref or None)
        findings.append(
            _finding("info", "inflight", "branches", inflight_overlay.summary_line(overlay))
        )
    except Exception as exc:  # divergence context must never block the report
        findings.append(_finding("info", "inflight", "branches", f"unavailable: {exc}"))

    return {
        "name": "worktrees",
        "status": "attention" if zombies else "ok",
        "base_ref": base_ref,
        "counts": {
            "worktrees": len(worktrees),
            "zombies": len(zombies),
            "cleanable": len(cleanable),
            "exempt": len(exempt),
        },
        "findings": findings,
    }


def build_claims_section(claims: list[dict[str, Any]], now: datetime) -> dict[str, Any]:
    stale_lines = lifecycle_gate.find_stale_claims(claims, now)
    active = sum(
        1
        for claim in claims
        if str(claim.get("status", "")).strip().lower() in lifecycle_gate.ACTIVE_CLAIM_STATUSES
    )
    findings = []
    stale_ids = []
    for line in stale_lines:
        claim_id = line.split(" ", 1)[0].removeprefix("stale-claim:")
        stale_ids.append(claim_id)
        detail = line.partition(" ")[2] or line
        findings.append(_finding("watch", "stale-claim", claim_id, detail))
    return {
        "name": "claims",
        "status": "attention" if stale_lines else "ok",
        "counts": {"total": len(claims), "active": active, "stale": len(stale_lines)},
        "stale_claim_ids": stale_ids,
        "findings": findings,
    }


def build_stashes_section(root: Path, now: datetime, stash_age_days: float) -> dict[str, Any]:
    rc, out, err = _git(
        root,
        "for-each-ref",
        "--format=%(refname)%09%(objectname:short)%09%(committerdate:iso8601-strict)",
        *ARCHIVE_STASH_PATTERNS,
    )
    if rc != 0:
        reason = _ascii((err or out).strip().splitlines()[0] if (err or out).strip() else f"git exited {rc}")
        return {
            "name": "stashes",
            "status": "unavailable",
            "reason": reason,
            "counts": {"refs": 0, "flagged": 0},
            "entries": [],
            "findings": [],
        }

    entries: dict[str, dict[str, Any]] = {}
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        refname, sha, committed_raw = parts
        if refname.startswith("refs/heads/"):
            short, location = refname[len("refs/heads/"):], "local"
        elif refname.startswith("refs/remotes/origin/"):
            short, location = refname[len("refs/remotes/origin/"):], "origin"
        else:
            continue
        age = _age_days(now, _parse_iso(committed_raw))
        entry = entries.setdefault(
            short,
            {"ref": short, "sha": sha, "committed_at": committed_raw, "age_days": age, "locations": []},
        )
        entry["locations"].append(location)
        if location == "local":
            entry.update(sha=sha, committed_at=committed_raw, age_days=age)

    findings: list[dict[str, str]] = []
    flagged = 0
    for entry in sorted(entries.values(), key=lambda item: str(item["ref"])):
        age = entry["age_days"]
        entry["flagged"] = age is not None and age >= stash_age_days
        locations = "+".join(entry["locations"])
        if entry["flagged"]:
            flagged += 1
            findings.append(
                _finding(
                    "watch",
                    "stash-unreclaimed",
                    entry["ref"],
                    f"age_days={age} locations={locations} sha={entry['sha']} "
                    f"recover=git stash apply {entry['sha']} inspect=git show --stat {entry['sha']}",
                )
            )
        else:
            findings.append(
                _finding(
                    "info",
                    "stash-archive",
                    entry["ref"],
                    f"age_days={age} locations={locations} sha={entry['sha']}",
                )
            )

    return {
        "name": "stashes",
        "status": "attention" if flagged else "ok",
        "counts": {"refs": len(entries), "flagged": flagged},
        "threshold_days": stash_age_days,
        "entries": list(sorted(entries.values(), key=lambda item: str(item["ref"]))),
        "findings": findings,
    }


def _gh_json(runner: CommandRunner, root: Path, args: list[str]) -> tuple[list[Any] | None, str]:
    rc, out, err = runner(["gh", *args], root)
    if rc != 0:
        text = (err or out).strip()
        reason = text.splitlines()[0] if text else f"gh exited {rc}"
        return None, _ascii(reason)
    try:
        data = json.loads(out or "[]")
    except json.JSONDecodeError as exc:
        return None, f"gh output not JSON: {exc}"
    return data if isinstance(data, list) else [], ""


def build_github_section(
    root: Path,
    runner: CommandRunner,
    now: datetime,
    pr_age_days: float,
    skip: bool,
) -> dict[str, Any]:
    if skip:
        return {
            "name": "github",
            "status": "skipped",
            "counts": {},
            "prs": [],
            "issues": [],
            "findings": [],
        }

    prs_raw, reason = _gh_json(
        runner,
        root,
        ["pr", "list", "--state", "open", "--json", "number,title,isDraft,createdAt,headRefName", "--limit", "100"],
    )
    if prs_raw is None:
        return {
            "name": "github",
            "status": "unavailable",
            "reason": reason,
            "counts": {},
            "prs": [],
            "issues": [],
            "findings": [],
        }

    findings: list[dict[str, str]] = []
    counts = {
        "open_prs": 0,
        "drafts": 0,
        "aged_prs": 0,
        "open_issues": 0,
        "no_reference": 0,
        "unregistered": 0,
        "completed_refs": 0,
    }

    prs: list[dict[str, Any]] = []
    for raw in prs_raw:
        if not isinstance(raw, dict):
            continue
        number = raw.get("number")
        title = _ascii(raw.get("title"))[:60]
        age = _age_days(now, _parse_iso(str(raw.get("createdAt") or "")))
        is_draft = bool(raw.get("isDraft"))
        flags: list[str] = []
        if is_draft:
            flags.append("draft")
        if age is not None and age >= pr_age_days:
            flags.append("aged")
        record = {
            "number": number,
            "title": title,
            "draft": is_draft,
            "age_days": age,
            "head": _ascii(raw.get("headRefName")),
            "flags": flags,
        }
        prs.append(record)
        counts["open_prs"] += 1
        if is_draft:
            counts["drafts"] += 1
        if "aged" in flags:
            counts["aged_prs"] += 1
        if flags:
            findings.append(
                _finding(
                    "watch",
                    "pr",
                    f"#{number}",
                    f"flags={','.join(flags)} age_days={age} head={record['head']} title={title}",
                )
            )

    issues: list[dict[str, Any]] = []
    issues_raw, issues_reason = _gh_json(
        runner,
        root,
        ["issue", "list", "--state", "open", "--json", "number,title,body,createdAt", "--limit", "200"],
    )
    if issues_raw is None:
        findings.append(_finding("info", "issues-unavailable", "gh", issues_reason))
    else:
        registered = load_registered_ids(root)
        statuses = load_task_status_index(root)
        for raw in issues_raw:
            if not isinstance(raw, dict):
                continue
            number = raw.get("number")
            title = _ascii(raw.get("title"))[:60]
            refs = _extract_refs(str(raw.get("title") or ""), str(raw.get("body") or ""))
            registered_refs = [ref for ref in refs if ref in registered]
            record: dict[str, Any] = {
                "number": number,
                "title": title,
                "refs": refs,
                "registered_refs": registered_refs,
                "flag": "",
            }
            counts["open_issues"] += 1
            if not refs:
                record["flag"] = "issue-no-reference"
                counts["no_reference"] += 1
                findings.append(
                    _finding(
                        "watch",
                        "issue-no-reference",
                        f"#{number}",
                        "no TASK-/BUG- reference; register in BACKLOG.md or "
                        f"agents/lead_engineer/tasks/ title={title}",
                    )
                )
            elif not registered_refs:
                record["flag"] = "issue-unregistered"
                counts["unregistered"] += 1
                findings.append(
                    _finding(
                        "watch",
                        "issue-unregistered",
                        f"#{number}",
                        f"refs={','.join(refs)} not found in agents/lead_engineer/tasks/ "
                        f"or BACKLOG.md; register before work starts title={title}",
                    )
                )
            elif all(statuses.get(ref, "unknown") in DONE_TASK_STATUSES for ref in registered_refs):
                record["flag"] = "issue-completed-refs"
                counts["completed_refs"] += 1
                findings.append(
                    _finding(
                        "watch",
                        "issue-completed-refs",
                        f"#{number}",
                        f"all registered refs done ({','.join(registered_refs)}); "
                        f"candidate for gh issue close title={title}",
                    )
                )
            issues.append(record)

    attention = any(finding["severity"] == "watch" for finding in findings)
    return {
        "name": "github",
        "status": "attention" if attention else "ok",
        "counts": counts,
        "prs": prs,
        "issues": issues,
        "findings": findings,
    }


def build_views_section(root: Path, runner: CommandRunner) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    probes: list[dict[str, Any]] = []
    drift = clean = unavailable = 0
    for name, check_args, fix_args in VIEW_PROBES:
        script = root / check_args[0]
        if not script.is_file():
            unavailable += 1
            findings.append(_finding("info", "view-missing", name, f"{check_args[0]} not found"))
            probes.append({"view": name, "result": "missing"})
            continue
        rc, out, err = runner([sys.executable, str(script), *check_args[1:]], root)
        if rc == 0:
            clean += 1
            probes.append({"view": name, "result": "clean"})
            continue
        if rc == 2:
            # argparse rejects --check: the view has no check mode yet.
            unavailable += 1
            findings.append(
                _finding("info", "view-check-unsupported", name, f"{check_args[0]} has no --check mode yet (rc=2)")
            )
            probes.append({"view": name, "result": "check-unsupported"})
            continue
        drift += 1
        text = (out or err).strip()
        tail = _ascii(text.splitlines()[-1]) if text else ""
        fix = "python " + " ".join(fix_args)
        findings.append(
            _finding("watch", "view-drift", name, f"rc={rc} {tail} regenerate: {fix}".strip())
        )
        probes.append({"view": name, "result": "drift", "rc": rc, "fix": fix})
    return {
        "name": "views",
        "status": "attention" if drift else "ok",
        "counts": {"probes": len(VIEW_PROBES), "drift": drift, "clean": clean, "unavailable": unavailable},
        "probes": probes,
        "findings": findings,
    }


def build_report(
    root: Path | str,
    *,
    runner: CommandRunner | None = None,
    now: datetime | None = None,
    pr_age_days: float = DEFAULT_PR_AGE_DAYS,
    stash_age_days: float = DEFAULT_STASH_AGE_DAYS,
    retention_days: float = lifecycle_gate.DEFAULT_RETENTION_DAYS,
    base_ref: str = "",
    skip_gh: bool = False,
) -> dict[str, Any]:
    runner = runner or default_runner
    now = now or datetime.now(timezone.utc)
    root_path = Path(root).resolve()
    try:
        claims = lifecycle_gate.load_claims(root_path)
    except Exception:
        claims = []

    builders: list[tuple[str, Callable[[], dict[str, Any]]]] = [
        ("worktrees", lambda: build_worktrees_section(root_path, claims, now, retention_days, base_ref)),
        ("claims", lambda: build_claims_section(claims, now)),
        ("stashes", lambda: build_stashes_section(root_path, now, stash_age_days)),
        ("github", lambda: build_github_section(root_path, runner, now, pr_age_days, skip_gh)),
        ("views", lambda: build_views_section(root_path, runner)),
    ]
    sections: dict[str, dict[str, Any]] = {}
    for name, builder in builders:
        try:
            sections[name] = builder()
        except Exception as exc:  # the report must never block (exit-0 invariant)
            sections[name] = {
                "name": name,
                "status": "error",
                "reason": _ascii(exc),
                "counts": {},
                "findings": [_finding("info", "section-error", name, exc)],
            }

    watch = sum(
        1
        for section in sections.values()
        for finding in section.get("findings", [])
        if finding["severity"] == "watch"
    )
    info = sum(
        1
        for section in sections.values()
        for finding in section.get("findings", [])
        if finding["severity"] == "info"
    )
    return {
        "schema": SCHEMA,
        "generated_at": now.isoformat(),
        "root": str(root_path),
        "thresholds": {
            "pr_age_days": pr_age_days,
            "stash_age_days": stash_age_days,
            "retention_days": retention_days,
        },
        "sections": sections,
        "summary": {
            "watch": watch,
            "info": info,
            "sections_attention": sorted(
                name for name, section in sections.items() if section.get("status") == "attention"
            ),
        },
    }


def render_report(report: dict[str, Any]) -> str:
    lines = [
        "scm-steward: report",
        f"root={report['root']}",
        f"generated_at={report['generated_at']}",
    ]
    for name in SECTIONS:
        section = report["sections"].get(name, {})
        header = f"[{name}] status={section.get('status', 'missing')}"
        counts = section.get("counts") or {}
        if counts:
            header += " " + " ".join(f"{key}={value}" for key, value in counts.items())
        if section.get("base_ref"):
            header += f" base_ref={section['base_ref']}"
        if section.get("reason"):
            header += f" reason={_ascii(section['reason'])}"
        lines.append(header)
        for finding in section.get("findings", []):
            lines.append(
                f"- {finding['severity']} {finding['kind']}:{finding['subject']} {finding['detail']}"
            )
    summary = report["summary"]
    lines.append(f"summary: watch={summary['watch']} info={summary['info']}")
    lines.append(
        "note: report is non-blocking (exit 0); cleanup requires clean --approve <section|all>"
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Clean (report -> approve -> execute)
# ---------------------------------------------------------------------------


def _run_commands(
    commands: list[list[str]],
    root: Path,
    runner: CommandRunner,
    execute: bool,
    label: str,
) -> int:
    mode = "execute (Owner-gated --execute-gh)" if execute else "dry-run (print-only)"
    print(f"{label}: {len(commands)} command(s) mode={mode}")
    failures = 0
    for command in commands:
        if not execute:
            print(f"- would-run: {_format_command(command)}")
            continue
        print(f"- run: {_format_command(command)}")
        rc, out, err = runner(command, root)
        print(f"  rc={rc}")
        if rc != 0:
            failures += 1
            text = (err or out).strip()
            if text:
                print(f"  error: {_ascii(text.splitlines()[-1])}")
    return failures


def _clean_worktrees(root: Path, retention_days: float, base_ref_arg: str) -> int:
    now = datetime.now(timezone.utc)
    claims = lifecycle_gate.load_claims(root)
    worktrees = lifecycle_gate.list_worktrees(root)
    base_ref = lifecycle_gate.resolve_base_ref(root, base_ref_arg)
    verdicts = [
        lifecycle_gate.evaluate_worktree(root, worktree, claims, base_ref, retention_days, now)
        for worktree in worktrees
    ]
    actions, failures = lifecycle_gate.clean_zombies(root, verdicts)
    print(f"clean[worktrees]: delegated to worktree_lifecycle_gate actions={len(actions)}")
    for action in actions:
        print(f"- clean {action}")
    if failures:
        print(f"clean[worktrees]: failures={failures}")
    return failures


def _print_claim_guidance(report: dict[str, Any]) -> None:
    section = report["sections"].get("claims", {})
    stale_ids = section.get("stale_claim_ids", [])
    print(f"clean[claims]: print-only stale={len(stale_ids)}")
    for claim_id in stale_ids:
        print(
            f"- manual: review agents/runtime/task_claims/{claim_id}.json; confirm the "
            "instance is gone, then set status=released with released_at"
        )


def _print_stash_commands(report: dict[str, Any]) -> None:
    section = report["sections"].get("stashes", {})
    flagged = [entry for entry in section.get("entries", []) if entry.get("flagged")]
    print(
        f"clean[stashes]: print-only flagged={len(flagged)} -- archive stash refs are "
        "preservation evidence; confirm content is reclaimed before deleting"
    )
    for entry in flagged:
        if "local" in entry.get("locations", []):
            print(f"- would-run: git branch -D {entry['ref']}")
        if "origin" in entry.get("locations", []):
            print(f"- would-run: git push origin --delete {entry['ref']}")


def _github_mutation_commands(report: dict[str, Any]) -> list[list[str]]:
    section = report["sections"].get("github", {})
    commands: list[list[str]] = []
    for pr in section.get("prs", []):
        if "aged" in pr.get("flags", []):
            commands.append(
                [
                    "gh",
                    "pr",
                    "close",
                    str(pr["number"]),
                    "--comment",
                    f"scm-steward: closing stale PR (age {pr['age_days']}d). Reopen if still in flight.",
                ]
            )
    for issue in section.get("issues", []):
        if issue.get("flag") == "issue-completed-refs":
            refs = ",".join(issue.get("registered_refs", []))
            commands.append(
                [
                    "gh",
                    "issue",
                    "close",
                    str(issue["number"]),
                    "--comment",
                    f"scm-steward: linked work item(s) {refs} completed.",
                ]
            )
    return commands


def _clean_github(
    root: Path,
    report: dict[str, Any],
    runner: CommandRunner,
    execute: bool,
) -> int:
    section = report["sections"].get("github", {})
    if section.get("status") in {"unavailable", "skipped", "error"}:
        print(f"clean[github]: section {section.get('status')}; nothing to do")
        return 0
    commands = _github_mutation_commands(report)
    failures = _run_commands(commands, root, runner, execute, "clean[github]")
    for issue in section.get("issues", []):
        if issue.get("flag") in {"issue-unregistered", "issue-no-reference"}:
            refs = ",".join(issue.get("refs", [])) or "none"
            print(
                f"- manual: issue #{issue['number']} needs work-item registration "
                f"(refs={refs}); do not close"
            )
    return failures


def _print_view_commands(report: dict[str, Any]) -> None:
    section = report["sections"].get("views", {})
    drifted = [probe for probe in section.get("probes", []) if probe.get("result") == "drift"]
    print(f"clean[views]: print-only drift={len(drifted)}")
    for probe in drifted:
        print(f"- would-run: {probe['fix']}")


def cmd_clean(args: argparse.Namespace, runner: CommandRunner) -> int:
    root = Path(args.root).resolve()
    report = build_report(
        root,
        runner=runner,
        pr_age_days=args.pr_age_days,
        stash_age_days=args.stash_age_days,
        retention_days=args.retention_days,
        base_ref=args.base_ref,
        skip_gh=args.skip_gh,
    )
    print(render_report(report))
    if not args.approve:
        print("clean: no --approve given; nothing changed (discipline: report -> approve -> execute)")
        return 0
    approved = list(SECTIONS) if args.approve == "all" else [args.approve]
    print(f"clean: approved={','.join(approved)} execute_gh={'on' if args.execute_gh else 'off'}")
    failures = 0
    for section in approved:
        if section == "worktrees":
            failures += _clean_worktrees(root, args.retention_days, args.base_ref)
        elif section == "claims":
            _print_claim_guidance(report)
        elif section == "stashes":
            _print_stash_commands(report)
        elif section == "github":
            failures += _clean_github(root, report, runner, args.execute_gh)
        elif section == "views":
            _print_view_commands(report)
    return 1 if failures else 0


# ---------------------------------------------------------------------------
# gh helpers (dry-run by default; --execute-gh is Owner-gated)
# ---------------------------------------------------------------------------


def cmd_pr_open(args: argparse.Namespace, runner: CommandRunner) -> int:
    root = Path(args.root).resolve()
    task_id = args.task.strip().upper()
    claims = lifecycle_gate.load_claims(root)
    matched = [
        claim for claim in claims if str(claim.get("task_id", "")).strip().upper() == task_id
    ]
    active = [
        claim
        for claim in matched
        if str(claim.get("status", "")).strip().lower() in lifecycle_gate.ACTIVE_CLAIM_STATUSES
    ]
    claim = (active or matched)[-1] if (active or matched) else None

    branch = (args.branch or "").strip()
    if not branch and claim is not None:
        branch = str(claim.get("branch", "")).strip()
    if not branch:
        rc, out, _err = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
        branch = out.strip() if rc == 0 else ""
    if not branch or branch == "HEAD":
        print(f"pr-open: cannot resolve a branch for {task_id}; pass --branch")
        return 1

    claim_id = str(claim.get("claim_id", "")).strip() if claim else ""
    handoff = str(claim.get("handoff_path", "")).strip() if claim else ""
    if not handoff and claim_id:
        handoff = f"agents/runtime/task_claims/{claim_id}.handoff.md"
    body = (
        f"Task: {task_id} | Claim: {claim_id or 'none'} | "
        f"Claim handoff: {handoff or 'n/a (no claim found)'} | "
        "Opened by scm-steward pr-open (draft-first policy; Owner approves ready-for-review)."
    )
    commands = [
        ["git", "push", "-u", "origin", branch],
        [
            "gh",
            "pr",
            "create",
            "--draft",
            "--title",
            task_id,
            "--head",
            branch,
            "--base",
            args.base,
            "--body",
            body,
        ],
    ]
    return 1 if _run_commands(commands, root, runner, args.execute_gh, "pr-open") else 0


def cmd_pr_close(args: argparse.Namespace, runner: CommandRunner) -> int:
    root = Path(args.root).resolve()
    message = args.comment or (
        f"scm-steward: closeout complete for {args.task or 'this task'}; closing PR after integration."
    )
    commands = [
        ["gh", "pr", "comment", str(args.pr), "--body", message],
        ["gh", "pr", "close", str(args.pr)],
    ]
    return 1 if _run_commands(commands, root, runner, args.execute_gh, "pr-close") else 0


def cmd_issue_sync(args: argparse.Namespace, runner: CommandRunner) -> int:
    root = Path(args.root).resolve()
    commands: list[list[str]] = []
    notes: list[str] = []

    if args.intake_title:
        ref = (args.intake_ref or "").strip().upper()
        title = f"[{ref}] {args.intake_title}" if ref else args.intake_title
        body = (
            "W3 adjacent-problem intake via scm-steward issue-sync. "
            f"Work item: {ref or 'UNREGISTERED'}. "
            "Cross-check: agents/lead_engineer/tasks/ + BACKLOG.md."
        )
        commands.append(["gh", "issue", "create", "--title", title, "--body", body])
        if ref and ref not in load_registered_ids(root):
            notes.append(
                f"- manual: {ref} is not registered yet; add it to BACKLOG.md or "
                "agents/lead_engineer/tasks/ so the issue cross-check passes"
            )

    issues_raw, reason = _gh_json(
        runner,
        root,
        ["issue", "list", "--state", "open", "--json", "number,title,body", "--limit", "200"],
    )
    if issues_raw is None:
        print(f"issue-sync: gh unavailable ({reason}); close-direction skipped")
    else:
        registered = load_registered_ids(root)
        statuses = load_task_status_index(root)
        for raw in issues_raw:
            if not isinstance(raw, dict):
                continue
            refs = _extract_refs(str(raw.get("title") or ""), str(raw.get("body") or ""))
            registered_refs = [ref for ref in refs if ref in registered]
            if registered_refs and all(
                statuses.get(ref, "unknown") in DONE_TASK_STATUSES for ref in registered_refs
            ):
                commands.append(
                    [
                        "gh",
                        "issue",
                        "close",
                        str(raw.get("number")),
                        "--comment",
                        f"scm-steward issue-sync: linked work item(s) {','.join(registered_refs)} completed.",
                    ]
                )

    failures = _run_commands(commands, root, runner, args.execute_gh, "issue-sync")
    for note in notes:
        print(note)
    return 1 if failures else 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def cmd_report(args: argparse.Namespace, runner: CommandRunner) -> int:
    report = build_report(
        Path(args.root),
        runner=runner,
        pr_age_days=args.pr_age_days,
        stash_age_days=args.stash_age_days,
        retention_days=args.retention_days,
        base_ref=args.base_ref,
        skip_gh=args.skip_gh,
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=True, indent=2))
    else:
        print(render_report(report))
    return 0  # the report is non-blocking by contract


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="SCM steward hygiene loop (report -> approve -> execute)"
    )
    sub = parser.add_subparsers(dest="command")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")

    thresholds = argparse.ArgumentParser(add_help=False)
    thresholds.add_argument("--pr-age-days", type=float, default=DEFAULT_PR_AGE_DAYS)
    thresholds.add_argument("--stash-age-days", type=float, default=DEFAULT_STASH_AGE_DAYS)
    thresholds.add_argument(
        "--retention-days", type=float, default=lifecycle_gate.DEFAULT_RETENTION_DAYS
    )
    thresholds.add_argument("--base-ref", default="")
    thresholds.add_argument("--skip-gh", action="store_true", help="Skip gh-backed sections")

    report_parser = sub.add_parser(
        "report", parents=[common, thresholds], help="Read-only consolidated report (always exit 0)"
    )
    report_parser.add_argument("--json", action="store_true")

    clean_parser = sub.add_parser(
        "clean",
        parents=[common, thresholds],
        help="Report, then clean approved sections (gh mutations need --execute-gh)",
    )
    clean_parser.add_argument(
        "--approve",
        choices=[*SECTIONS, "all"],
        default="",
        help="Section approved for cleanup; without it nothing changes",
    )
    clean_parser.add_argument(
        "--execute-gh",
        action="store_true",
        help="Owner-gated: actually run gh mutation commands (default prints them)",
    )

    pr_open_parser = sub.add_parser(
        "pr-open", parents=[common], help="Task branch push + draft PR creation (dry-run default)"
    )
    pr_open_parser.add_argument("--task", required=True, help="Task id, becomes the PR title")
    pr_open_parser.add_argument("--branch", default="", help="Branch (default: claim branch or HEAD)")
    pr_open_parser.add_argument("--base", default="main")
    pr_open_parser.add_argument("--execute-gh", action="store_true", help="Owner-gated execution")

    pr_close_parser = sub.add_parser(
        "pr-close", parents=[common], help="Closeout PR comment + close (dry-run default)"
    )
    pr_close_parser.add_argument("--pr", required=True, type=int)
    pr_close_parser.add_argument("--task", default="")
    pr_close_parser.add_argument("--comment", default="")
    pr_close_parser.add_argument("--execute-gh", action="store_true", help="Owner-gated execution")

    issue_sync_parser = sub.add_parser(
        "issue-sync",
        parents=[common],
        help="W3 adjacent-problem intake <-> gh issue create/close sync (dry-run default)",
    )
    issue_sync_parser.add_argument("--intake-title", default="", help="Create an intake issue")
    issue_sync_parser.add_argument("--intake-ref", default="", help="Work item id for the intake issue")
    issue_sync_parser.add_argument("--execute-gh", action="store_true", help="Owner-gated execution")

    return parser


def main(argv: list[str] | None = None, runner: CommandRunner | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    runner = runner or default_runner
    if not getattr(args, "command", None):
        parser.print_help()
        return 2
    if args.command == "report":
        return cmd_report(args, runner)
    if args.command == "clean":
        return cmd_clean(args, runner)
    if args.command == "pr-open":
        return cmd_pr_open(args, runner)
    if args.command == "pr-close":
        return cmd_pr_close(args, runner)
    if args.command == "issue-sync":
        return cmd_issue_sync(args, runner)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
