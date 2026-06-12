"""In-flight overlay: surface branch-side task status divergence against main.

The main board only reads task frontmatter from the current checkout, so work
completed on unmerged agent branches (codex/*, claude/*) is invisible and gets
re-planned (real incident: TASK-AR-370 planned on main, completed on three
codex branches). This script scans agent branches WITHOUT checking them out
(git object access only), compares each changed task file's frontmatter
``status:`` against the same file on the base ref, joins claim state from
``agents/runtime/task_claims/``, and reports per-task divergence records.

Read-only: never mutates the repository or any worktree.
Output is cp949-safe (ASCII only on the human path, ensure_ascii JSON).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "agent-runtime-inflight-overlay/v1"
TASKS_PREFIX = "agents/lead_engineer/tasks"
TASK_FILE_RE = re.compile(r"(TASK-[A-Z]+(?:-[A-Z]+)*-\d+)[^/]*\.md$")
AGENT_BRANCH_PREFIXES = ("codex/", "claude/")
EXCLUDED_BRANCH_PREFIXES = ("archive/",)
CLAIM_DIR = "agents/runtime/task_claims"
ACTIVE_CLAIM_STATUSES = {"assigned", "claimed", "in_progress", "review", "waiting_review", "working"}
STATUS_RE = re.compile(r"^status:\s*(.+?)\s*$", re.MULTILINE)


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _ascii(value: Any) -> str:
    return str(value if value is not None else "").encode("ascii", "replace").decode("ascii")


def run_git(root: Path, *args: str) -> tuple[int, str]:
    """Run a read-only git command; return (returncode, stdout)."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, FileNotFoundError) as exc:
        return 127, str(exc)
    return result.returncode, result.stdout


def frontmatter_status(text: str | None) -> str | None:
    """Extract ``status:`` from the leading YAML frontmatter block."""
    if not text:
        return None
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end_index: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
    if end_index is None:
        return None
    match = STATUS_RE.search("\n".join(lines[1:end_index]))
    if not match:
        return None
    return match.group(1).strip().strip("\"'") or None


def is_agent_branch(name: str) -> bool:
    if name.startswith(EXCLUDED_BRANCH_PREFIXES):
        return False
    return name.startswith(AGENT_BRANCH_PREFIXES)


def resolve_base(root: Path, base: str | None = None) -> str | None:
    candidates = [base] if base else ["origin/main", "main"]
    for candidate in candidates:
        if not candidate:
            continue
        code, _ = run_git(root, "rev-parse", "--verify", "--quiet", f"{candidate}^{{commit}}")
        if code == 0:
            return candidate
    return None


def list_agent_branches(root: Path) -> list[dict[str, str]]:
    """Enumerate local + remote agent branches; local ref wins on name clash."""
    code, out = run_git(root, "remote")
    remotes = {line.strip() for line in out.splitlines() if line.strip()} if code == 0 else set()
    code, out = run_git(root, "for-each-ref", "--format=%(refname:short)", "refs/heads", "refs/remotes")
    if code != 0:
        return []
    by_name: dict[str, dict[str, str]] = {}
    for raw in out.splitlines():
        ref = raw.strip()
        if not ref or ref.endswith("/HEAD"):
            continue
        name = ref
        is_local = True
        head, _, rest = ref.partition("/")
        if head in remotes and rest:
            name = rest
            is_local = False
        if not is_agent_branch(name):
            continue
        existing = by_name.get(name)
        if existing is None or (is_local and existing["kind"] == "remote"):
            by_name[name] = {"name": name, "ref": ref, "kind": "local" if is_local else "remote"}
    return sorted(by_name.values(), key=lambda item: item["name"])


def _task_id_from_path(path: str) -> str | None:
    match = TASK_FILE_RE.search(path.rsplit("/", 1)[-1])
    return match.group(1) if match else None


def _show(root: Path, ref: str, path: str) -> str | None:
    code, out = run_git(root, "show", f"{ref}:{path}")
    return out if code == 0 else None


def load_claim_index(root: Path) -> dict[str, dict[str, Any]]:
    """Map TASK id -> {claim_status, claim_id} from the working-tree claim dir."""
    index: dict[str, dict[str, Any]] = {}
    claim_dir = root / CLAIM_DIR
    if not claim_dir.is_dir():
        return index
    for path in sorted(claim_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        task_id = str(payload.get("task_id") or "").strip().upper()
        if not task_id:
            continue
        status = str(payload.get("status") or "").strip().lower()
        claim_status = "active" if status in ACTIVE_CLAIM_STATUSES else "released"
        current = index.get(task_id)
        if current is None or (claim_status == "active" and current["claim_status"] != "active"):
            index[task_id] = {"claim_status": claim_status, "claim_id": payload.get("claim_id") or path.stem}
    return index


def _branch_records(
    root: Path,
    base: str,
    branch: dict[str, str],
    claim_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    ref = branch["ref"]
    code, out = run_git(root, "diff", "--name-only", f"{base}...{ref}", "--", f"{TASKS_PREFIX}/")
    if code != 0:
        return []
    changed = [line.strip() for line in out.splitlines() if line.strip()]
    if not changed:
        return []

    records: list[dict[str, Any]] = []
    ahead = None
    last_commit: dict[str, Any] = {}
    for path in changed:
        task_id = _task_id_from_path(path)
        if not task_id:
            continue
        branch_status = frontmatter_status(_show(root, ref, path)) or "absent"
        main_status = frontmatter_status(_show(root, base, path)) or "absent"
        if branch_status == main_status:
            continue
        if ahead is None:
            code, out = run_git(root, "rev-list", "--count", f"{base}..{ref}")
            ahead = int(out.strip()) if code == 0 and out.strip().isdigit() else 0
            code, out = run_git(root, "log", "-1", "--format=%h%x09%cI%x09%s", ref)
            if code == 0 and out.strip():
                commit_hash, _, rest = out.strip().partition("\t")
                commit_date, _, subject = rest.partition("\t")
                last_commit = {"hash": commit_hash, "date": commit_date, "subject": subject}
        claim = claim_index.get(task_id.upper(), {"claim_status": "none", "claim_id": None})
        claimless = claim["claim_status"] == "none"
        records.append(
            {
                "task_id": task_id,
                "path": path,
                "main_status": main_status,
                "branch_status": branch_status,
                "branch": branch["name"],
                "branch_ref": ref,
                "ahead": ahead,
                "last_commit": last_commit,
                "claim_status": claim["claim_status"],
                "claim_id": claim["claim_id"],
                "divergence_flag": True,
                "claimless_flag": claimless,
            }
        )
    return records


def _empty_overlay(root: Path, base: str | None, error: str | None = None) -> dict[str, Any]:
    overlay: dict[str, Any] = {
        "schema": SCHEMA,
        "generated_at": _now_iso(),
        "root": str(root),
        "base": base,
        "branches_scanned": 0,
        "records": [],
        "summary": {
            "divergent_tasks": 0,
            "divergent_records": 0,
            "branches_with_divergence": 0,
            "claimless": 0,
        },
    }
    if error:
        overlay["error"] = error
    return overlay


def build_overlay(root: Path | str, base: str | None = None) -> dict[str, Any]:
    root_path = Path(root).resolve()
    code, _ = run_git(root_path, "rev-parse", "--show-toplevel")
    if code != 0:
        return _empty_overlay(root_path, None, "not a git repository")
    resolved_base = resolve_base(root_path, base)
    if resolved_base is None:
        return _empty_overlay(root_path, base, f"base ref not found: {base or 'origin/main|main'}")

    claim_index = load_claim_index(root_path)
    branches = list_agent_branches(root_path)
    records: list[dict[str, Any]] = []
    for branch in branches:
        records.extend(_branch_records(root_path, resolved_base, branch, claim_index))

    overlay = _empty_overlay(root_path, resolved_base)
    overlay["branches_scanned"] = len(branches)
    overlay["records"] = records
    overlay["summary"] = {
        "divergent_tasks": len({record["task_id"] for record in records}),
        "divergent_records": len(records),
        "branches_with_divergence": len({record["branch"] for record in records}),
        "claimless": len({record["task_id"] for record in records if record["claimless_flag"]}),
    }
    return overlay


def summary_line(overlay: dict[str, Any]) -> str:
    if overlay.get("error"):
        return f"inflight: unavailable ({_ascii(overlay['error'])})"
    summary = overlay.get("summary", {})
    line = (
        f"inflight: {summary.get('divergent_tasks', 0)} tasks diverge "
        f"across {summary.get('branches_with_divergence', 0)} branches"
    )
    claimless = summary.get("claimless", 0)
    if claimless:
        line += f" ({claimless} claimless)"
    return line


def render_table(overlay: dict[str, Any]) -> str:
    records = overlay.get("records", [])
    lines: list[str] = []
    if overlay.get("error"):
        lines.append(f"inflight-overlay: error: {_ascii(overlay['error'])}")
    elif not records:
        lines.append(
            "inflight-overlay: no branch-side task status divergence "
            f"(base={_ascii(overlay.get('base'))}, branches={overlay.get('branches_scanned', 0)})"
        )
    else:
        headers = ["task", "main", "branch_status", "branch", "ahead", "claim", "flags", "last_commit"]
        rows: list[list[str]] = []
        for record in records:
            flags = ["divergence"]
            if record.get("claimless_flag"):
                flags.append("claimless")
            last_commit = record.get("last_commit") or {}
            subject = _ascii(last_commit.get("subject", ""))[:36]
            commit_text = f"{_ascii(last_commit.get('hash', ''))} {subject}".strip()
            rows.append(
                [
                    _ascii(record.get("task_id")),
                    _ascii(record.get("main_status")),
                    _ascii(record.get("branch_status")),
                    _ascii(record.get("branch")),
                    _ascii(record.get("ahead")),
                    _ascii(record.get("claim_status")),
                    ",".join(flags),
                    commit_text,
                ]
            )
        widths = [max(len(headers[i]), *(len(row[i]) for row in rows)) for i in range(len(headers))]
        lines.append("  ".join(header.ljust(widths[i]) for i, header in enumerate(headers)).rstrip())
        for row in rows:
            lines.append("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)).rstrip())
    lines.append(summary_line(overlay))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report unmerged agent-branch task status divergence vs main.")
    parser.add_argument("--root", default=".", help="repository root (default: current directory)")
    parser.add_argument("--base", default=None, help="base ref (default: origin/main, fallback main)")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--summary", action="store_true", help="emit the one-line divergence summary only")
    args = parser.parse_args(argv)

    overlay = build_overlay(Path(args.root), base=args.base)
    if args.json:
        print(json.dumps(overlay, ensure_ascii=True, indent=2))
    elif args.summary:
        print(summary_line(overlay))
    else:
        print(render_table(overlay))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
