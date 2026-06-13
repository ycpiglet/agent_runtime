"""Idea Vault revival loop.

Preserve shelved (rejected / deferred) ideas with a revisit date and revival
criteria, periodically re-surface the ones whose `revisit_after` has arrived, and
keep the revival path proposal-only so no task is ever auto-created.

Commands
--------
  list                       Print every registry entry.
  due   [--now YYYY-MM-DD]   Print entries whose revisit_after <= now (read-only,
                             always exit 0).
  revive <id>                Emit a B-mode owner proposal (origin_type
                             idea_vault_revival) into the planning outbox. Never
                             creates a task. Marks the entry status -> revived.
  defer  <id> --until DATE   Push revisit_after to DATE; status -> re-deferred.

The registry single source of truth is the markdown table inside
`agents/project/idea-vault/IDEA-VAULT.md`. Stdout is ASCII-safe (the repo runs on
a cp949 console); Korean content stays in the markdown file, never on stdout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VAULT_PATH = Path("agents") / "project" / "idea-vault" / "IDEA-VAULT.md"

# Registry table columns, in order. The markdown table is the SSoT.
COLUMNS = (
    "id",
    "idea",
    "shelved_at",
    "shelved_reason",
    "origin_ref",
    "revisit_after",
    "revival_criteria",
    "status",
)

# Lifecycle status vocabulary for a vault entry.
#   shelved     -> active, awaiting its revisit_after
#   revived     -> a revival proposal has been emitted (under re-evaluation / A-B)
#   re-deferred -> re-evaluated and pushed out to a new revisit_after
#   adopted     -> promoted into real work (kept for decision history)
#   retired     -> permanently dropped (kept for decision history)
ALLOWED_STATUS = {"shelved", "revived", "re-deferred", "adopted", "retired"}
ACTIVE_STATUS = {"shelved", "re-deferred"}

ID_RE = re.compile(r"^IV-\d{3}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _now_date(value: str | None = None) -> str:
    """Resolve the effective 'today' as an ASCII YYYY-MM-DD string.

    Precedence: explicit --now, then SOURCE_DATE_EPOCH (reproducible builds),
    then the real wall clock.
    """
    if value:
        return _normalize_date(value)
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch and epoch.isdigit():
        return datetime.fromtimestamp(int(epoch), timezone.utc).date().isoformat()
    return date.today().isoformat()


def _normalize_date(value: str) -> str:
    text = str(value).strip()
    # Accept full ISO timestamps too, but the registry stores plain dates.
    parsed = date.fromisoformat(text[:10])
    return parsed.isoformat()


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _split_row(line: str) -> list[str]:
    # `| a | b |` -> ['a', 'b'] ; drop the empty edge cells from the pipes.
    cells = line.split("|")
    if cells and cells[0].strip() == "":
        cells = cells[1:]
    if cells and cells[-1].strip() == "":
        cells = cells[:-1]
    return [c.strip() for c in cells]


def _is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", c) for c in cells)


def parse_entries(text: str) -> list[dict[str, str]]:
    """Parse the registry table into ordered entry dicts.

    Recognizes the entry table by its header row (the first cell is `id`).
    Rows that are not data rows (separators, malformed) are skipped.
    """
    entries: list[dict[str, str]] = []
    in_table = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            in_table = False
            continue
        cells = _split_row(line)
        if not in_table:
            # Look for the header row that begins the entry table.
            if cells and cells[0].lower() == "id" and len(cells) == len(COLUMNS):
                in_table = True
            continue
        if _is_separator(cells):
            continue
        if len(cells) != len(COLUMNS):
            continue
        if not ID_RE.match(cells[0]):
            continue
        entries.append(dict(zip(COLUMNS, cells)))
    return entries


def validate_entries(entries: list[dict[str, str]]) -> list[str]:
    """Return a list of schema violations (empty list == valid registry)."""
    errors: list[str] = []
    seen: set[str] = set()
    for entry in entries:
        eid = entry.get("id", "")
        if not ID_RE.match(eid):
            errors.append(f"bad id: {eid!r}")
            continue
        if eid in seen:
            errors.append(f"duplicate id: {eid}")
        seen.add(eid)
        status = entry.get("status", "")
        if status not in ALLOWED_STATUS:
            errors.append(f"{eid}: bad status {status!r} (allowed: {sorted(ALLOWED_STATUS)})")
        revisit = entry.get("revisit_after", "")
        if not DATE_RE.match(revisit):
            errors.append(f"{eid}: revisit_after not YYYY-MM-DD: {revisit!r}")
        for required in ("idea", "shelved_reason", "revival_criteria"):
            if not entry.get(required):
                errors.append(f"{eid}: empty {required}")
    return errors


def load_registry(root: Path) -> tuple[Path, list[dict[str, str]]]:
    path = root / VAULT_PATH
    entries = parse_entries(_read(path))
    return path, entries


def due_entries(entries: list[dict[str, str]], now: str) -> list[dict[str, str]]:
    """Active entries whose revisit_after has arrived (<= now)."""
    out: list[dict[str, str]] = []
    for entry in entries:
        if entry.get("status") not in ACTIVE_STATUS:
            continue
        revisit = entry.get("revisit_after", "")
        if not DATE_RE.match(revisit):
            continue
        if revisit <= now:
            out.append(entry)
    return out


def _find(entries: list[dict[str, str]], entry_id: str) -> dict[str, str] | None:
    for entry in entries:
        if entry.get("id") == entry_id:
            return entry
    return None


def _stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _rewrite_status(text: str, entry_id: str, *, status: str, revisit_after: str | None = None) -> str:
    """Rewrite the single registry row for `entry_id` in place.

    Only the status and (optionally) revisit_after cells change; all other
    content and formatting is preserved exactly.
    """
    lines = text.splitlines(keepends=True)
    for index, raw in enumerate(lines):
        body = raw.rstrip("\n")
        if not body.strip().startswith("|"):
            continue
        cells = _split_row(body)
        if len(cells) != len(COLUMNS) or cells[0] != entry_id:
            continue
        cells[COLUMNS.index("status")] = status
        if revisit_after is not None:
            cells[COLUMNS.index("revisit_after")] = revisit_after
        newline = "\n" if raw.endswith("\n") else ""
        lines[index] = "| " + " | ".join(cells) + " |" + newline
        return "".join(lines)
    raise KeyError(f"entry not found in registry table: {entry_id}")


def revive_proposal(
    root: Path,
    entry: dict[str, str],
    *,
    now: str,
    outbox: Path | None = None,
) -> dict[str, Any]:
    """Build and persist a proposal-only revival record. Never creates a task."""
    outbox = outbox or (root / "agents" / "planning" / "outbox")
    eid = entry["id"]
    dedupe_key = f"idea_vault_revival:{eid}"
    core = {
        "dedupe_key": dedupe_key,
        "entry_id": eid,
        "revisit_after": entry.get("revisit_after"),
    }
    proposal_id = f"PROP-{_stable_hash(core)[:12].upper()}"
    proposal = {
        "id": proposal_id,
        "mode": "B",
        "status": "proposed",
        "action_type": "idea_vault_revival",
        "proposal_output": "owner_decision",
        "origin_type": "idea_vault_revival",
        "origin_ref": f"{VAULT_PATH.as_posix()}#{eid}",
        "risk_tier": "owner",
        "title": f"Idea Vault revival due: {eid}",
        "created_at": now,
        "updated_at": now,
        "dedupe_key": dedupe_key,
        "entry_id": eid,
        "revisit_after": entry.get("revisit_after"),
        "revival_criteria": entry.get("revival_criteria"),
        "shelved_reason": entry.get("shelved_reason"),
        "source_refs": [{"path": f"{VAULT_PATH.as_posix()}#{eid}", "kind": "idea_vault_entry"}],
        "evidence": [
            {
                "summary": (
                    f"{eid} shelved on {entry.get('shelved_at')} is due for re-evaluation "
                    f"(revisit_after {entry.get('revisit_after')})."
                ),
                "confidence": 0.7,
            }
        ],
        "ab_experiment": {
            "protocol": f"{VAULT_PATH.as_posix()}#ab-experiment-protocol",
            "status": "not_started",
            "one_variable": None,
            "metric": None,
            "period": None,
            "decision": None,
        },
        "owner_boundary": (
            "Owner decision required: re-evaluate against revival_criteria, then adopt "
            "(spawn work via the normal intake) or re-defer. Proposal-only; no task is created."
        ),
        "canonical_mutation_allowed": False,
        "suggested_next_action": (
            "Owner reviews revival_criteria; if adopting, run a one-variable A/B experiment "
            "per the documented protocol before promoting to a task."
        ),
    }
    outbox.mkdir(parents=True, exist_ok=True)
    (outbox / f"{proposal_id}.json").write_text(
        json.dumps(proposal, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return proposal


def _ascii(value: Any) -> str:
    """Render any registry value ASCII-safe for the cp949 console."""
    text = "" if value is None else str(value)
    return text.encode("ascii", "replace").decode("ascii")


def _print_entries(entries: list[dict[str, str]], *, header: str) -> None:
    print(header)
    if not entries:
        print("(none)")
        return
    for entry in entries:
        print(
            f"- {entry['id']} [{entry.get('status')}] revisit_after={entry.get('revisit_after')} "
            f"| {_ascii(entry.get('idea'))}"
        )


def cmd_list(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    _, entries = load_registry(root)
    if args.json:
        print(json.dumps({"status": "pass", "count": len(entries), "entries": entries},
                         ensure_ascii=True, indent=2, sort_keys=True))
    else:
        _print_entries(entries, header=f"idea-vault: {len(entries)} entries")
    return 0


def cmd_due(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    now = _now_date(args.now)
    _, entries = load_registry(root)
    due = due_entries(entries, now)
    if args.json:
        print(json.dumps({"status": "pass", "now": now, "due_count": len(due), "due": due},
                         ensure_ascii=True, indent=2, sort_keys=True))
    else:
        _print_entries(due, header=f"idea-vault due as of {now}: {len(due)} entries")
    return 0  # read-only: always success


def cmd_revive(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    now = _now_date(args.now)
    path, entries = load_registry(root)
    entry = _find(entries, args.id)
    if entry is None:
        print(f"idea-vault: error: unknown id {args.id}")
        return 1
    if entry.get("status") in {"adopted", "retired"}:
        print(f"idea-vault: error: {args.id} is {entry.get('status')}; cannot revive")
        return 1
    outbox = Path(args.outbox).resolve() if args.outbox else None
    proposal = revive_proposal(root, entry, now=now, outbox=outbox)
    new_text = _rewrite_status(_read(path), args.id, status="revived")
    path.write_text(new_text, encoding="utf-8")
    if args.json:
        print(json.dumps({"status": "pass", "proposal_id": proposal["id"],
                          "proposal_output": proposal["proposal_output"], "entry_id": args.id},
                         ensure_ascii=True, indent=2, sort_keys=True))
    else:
        print(f"idea-vault: revived {args.id} -> proposal {proposal['id']} (proposal-only, no task created)")
    return 0


def cmd_defer(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    path, entries = load_registry(root)
    entry = _find(entries, args.id)
    if entry is None:
        print(f"idea-vault: error: unknown id {args.id}")
        return 1
    try:
        until = _normalize_date(args.until)
    except ValueError:
        print(f"idea-vault: error: --until must be YYYY-MM-DD, got {args.until!r}")
        return 1
    new_text = _rewrite_status(_read(path), args.id, status="re-deferred", revisit_after=until)
    path.write_text(new_text, encoding="utf-8")
    if args.json:
        print(json.dumps({"status": "pass", "entry_id": args.id, "revisit_after": until,
                          "new_status": "re-deferred"}, ensure_ascii=True, indent=2, sort_keys=True))
    else:
        print(f"idea-vault: deferred {args.id} -> revisit_after={until} (status re-deferred)")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    _, entries = load_registry(root)
    errors = validate_entries(entries)
    status = "pass" if not errors else "fail"
    if args.json:
        print(json.dumps({"status": status, "count": len(entries), "errors": errors},
                         ensure_ascii=True, indent=2, sort_keys=True))
    else:
        print(f"idea-vault-validate: {status} ({len(entries)} entries)")
        for error in errors:
            print(f"- {error}")
    return 0 if not errors else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Idea Vault revival loop (proposal-only)")
    parser.add_argument("--root", default=str(ROOT))
    sub = parser.add_subparsers(dest="command", required=True)

    list_p = sub.add_parser("list", help="list all registry entries")
    list_p.add_argument("--json", action="store_true")
    list_p.set_defaults(func=cmd_list)

    due_p = sub.add_parser("due", help="list entries whose revisit_after has arrived")
    due_p.add_argument("--now", help="fixture clock as YYYY-MM-DD")
    due_p.add_argument("--json", action="store_true")
    due_p.set_defaults(func=cmd_due)

    revive_p = sub.add_parser("revive", help="emit a proposal-only revival (never a task)")
    revive_p.add_argument("id")
    revive_p.add_argument("--now", help="fixture clock as YYYY-MM-DD")
    revive_p.add_argument("--outbox", help="override planning outbox dir")
    revive_p.add_argument("--json", action="store_true")
    revive_p.set_defaults(func=cmd_revive)

    defer_p = sub.add_parser("defer", help="push revisit_after to a new date")
    defer_p.add_argument("id")
    defer_p.add_argument("--until", required=True, help="new revisit_after YYYY-MM-DD")
    defer_p.add_argument("--json", action="store_true")
    defer_p.set_defaults(func=cmd_defer)

    validate_p = sub.add_parser("validate", help="validate the registry schema")
    validate_p.add_argument("--json", action="store_true")
    validate_p.set_defaults(func=cmd_validate)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
