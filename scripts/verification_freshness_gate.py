"""Verification evidence freshness gate.

Detects STALE verification evidence: a verification record (schema
``agent-runtime-work-verification/v1``, normally ``reviews/VERIFY-*.json``)
whose tracked inputs moved after the recorded verification. Closeout that
relies on stale evidence must re-verify first.

Freshness input model
---------------------
Evidence records may carry an optional ``freshness`` block written at
verification time (see ``agents/project/evidence/verification/README.md``):

    "freshness": {
      "commit_ref": "<git HEAD commit hash when the commands ran>",
      "source_paths": [
        {"path": "scripts/example.py", "sha256": "<sha256 hex of file bytes>"}
      ]
    }

A record WITH a freshness block is checkable. It is STALE when any tracked
input moved after verification:

- ``source-missing`` (strong): a tracked source path no longer exists.
- ``source-changed`` (strong): the sha256 of a tracked source no longer
  matches the recorded digest.
- ``source-commits-after-verification`` (strong):
  ``git log <commit_ref>..HEAD -- <source paths>`` reports commits touching
  the tracked paths after the recorded commit.
- ``work-item-updated-after-verification`` (strong): the verified work item's
  ``updated_at`` moved past the record's ``verified_at`` while the item is
  still open. Re-running ``work verify`` resets this.
- ``claim-updated-after-verification`` (advisory, watch-only): a task claim
  for the work item was updated after ``verified_at``. Claims mutate during
  normal progress reporting, so this signal never blocks by itself.

A record WITHOUT a freshness block is legacy: it reports a single
``freshness-unknown`` watch finding and never blocks. Unresolvable inputs
(``commit-ref-unresolvable``, ``work-item-missing``, unreadable JSON) also
degrade to watch, never block.

Severity policy (``--check``)
-----------------------------
- block: stale evidence with a strong reason referenced by an OPEN or closing
  work item. ``--check`` exits 1 only on block findings.
- watch: stale evidence on completed/archived items, advisory-only staleness,
  legacy records, and unresolvable inputs. Exit 0.

The record's ``verified_at``, ``verified_by``, and per-command data stay in
the report so reviewers can judge how old the evidence is and who produced it.

JSON report shape (``--json``)
------------------------------
    {
      "schema": "agent-runtime-verification-freshness/v1",
      "root": "<absolute repo root>",
      "generated_at": "<local iso timestamp>",
      "status": "pass" | "fail",
      "counts": {
        "records": N, "fresh": N, "stale": N, "unknown": N,
        "block": N, "watch": N
      },
      "records": [
        {
          "evidence_ref": "reviews/VERIFY-....json",
          "work_id": "TASK-AR-001",
          "work_path": "agents/lead_engineer/tasks/TASK-AR-001.md",
          "work_status": "in_progress",
          "work_open": true,
          "verification_status": "passed",
          "verified_at": "2026-06-13T01:00:00+09:00",
          "verified_by": "codex",
          "freshness": "fresh" | "stale" | "unknown",
          "severity": "ok" | "watch" | "block",
          "reasons": [
            {
              "code": "source-changed",
              "kind": "strong" | "advisory" | "unknown",
              "source": "scripts/example.py",
              "detail": "sha256 mismatch after verification"
            }
          ]
        }
      ]
    }

Work Explorer and ``work stats`` can consume this JSON to surface stale
verification state per work item.

Follow-up (AR-517 / work.py integration)
----------------------------------------
``scripts/work.py verify`` does not write the ``freshness`` block yet. The
follow-up integration note for the work.py owner: populate
``freshness.commit_ref`` from ``git rev-parse HEAD`` and
``freshness.source_paths`` (path + sha256) from the work item's
``target_files``/``inputs`` when writing evidence, and surface this gate's
``--json`` output in ``work stats``. This module stays read-only toward
work.py.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path


REPORT_SCHEMA = "agent-runtime-verification-freshness/v1"
EVIDENCE_SCHEMA = "agent-runtime-work-verification/v1"
TASKS_DIR = Path("agents/lead_engineer/tasks")
UNITS_DIR = Path("agents/lead_engineer/tasks/units")
REVIEWS_DIR = Path("reviews")
CLAIMS_DIR = Path("agents/runtime/task_claims")
CLOSED_STATUSES = {
    "completed",
    "done",
    "released",
    "archived",
    "cancelled",
    "closed",
    "superseded",
    "wontfix",
    "duplicate",
    "moved_to_vault",
}
GIT_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class Reason:
    code: str
    kind: str  # strong | advisory | unknown
    source: str
    detail: str


@dataclass
class WorkItem:
    rel_path: str
    work_id: str
    task_id: str
    status: str
    updated_at: str
    evidence_refs: list[str] = field(default_factory=list)

    @property
    def open(self) -> bool:
        return self.status.strip().lower() not in CLOSED_STATUSES


@dataclass
class RecordResult:
    evidence_ref: str
    work_id: str
    work_path: str
    work_status: str
    work_open: bool
    verification_status: str
    verified_at: str
    verified_by: str
    freshness: str  # fresh | stale | unknown
    severity: str  # ok | watch | block
    reasons: list[Reason] = field(default_factory=list)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _parse_frontmatter(text: str) -> dict[str, object]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict[str, object] = {}
    key: str | None = None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        item = re.match(r"^\s+-\s+(.*?)\s*$", line)
        if item is not None:
            existing = out.get(key) if key is not None else None
            if isinstance(existing, list):
                existing.append(item.group(1).strip().strip("'\""))
            continue
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*?)\s*$", line)
        if match:
            key = match.group(1)
            value = match.group(2).strip().strip("'\"")
            out[key] = [] if value == "" else value
    return out


def _meta_text(meta: dict[str, object], *keys: str) -> str:
    for key in keys:
        value = meta.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _meta_list(meta: dict[str, object], key: str) -> list[str]:
    value = meta.get(key)
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _parse_timestamp(value: str):
    text = (value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        import datetime as dt

        parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    return parsed


def _local_iso() -> str:
    import datetime as dt

    text = dt.datetime.now(dt.timezone.utc).astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
    if len(text) >= 5 and text[-5] in "+-":
        text = text[:-2] + ":" + text[-2:]
    return text


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _load_work_item(root: Path, path: Path) -> WorkItem | None:
    if not path.is_file():
        return None
    meta = _parse_frontmatter(_read_text(path))
    if not meta:
        return None
    work_id = _meta_text(meta, "unit_id", "work_id", "id", "display_id") or path.stem
    return WorkItem(
        rel_path=_rel(root, path),
        work_id=work_id,
        task_id=_meta_text(meta, "task_id", "display_id", "id") or work_id,
        status=_meta_text(meta, "status"),
        updated_at=_meta_text(meta, "updated_at"),
        evidence_refs=_meta_list(meta, "evidence_refs"),
    )


def _scan_work_items(root: Path) -> list[WorkItem]:
    items: list[WorkItem] = []
    tasks_dir = root / TASKS_DIR
    if tasks_dir.is_dir():
        for path in sorted(tasks_dir.glob("TASK-*.md")):
            item = _load_work_item(root, path)
            if item:
                items.append(item)
    units_dir = root / UNITS_DIR
    if units_dir.is_dir():
        for path in sorted(units_dir.glob("**/UNIT-*.md")):
            item = _load_work_item(root, path)
            if item:
                items.append(item)
    return items


def _scan_claims(root: Path) -> list[dict[str, object]]:
    claims_dir = root / CLAIMS_DIR
    claims: list[dict[str, object]] = []
    if not claims_dir.is_dir():
        return claims
    for path in sorted(claims_dir.glob("*.json")):
        try:
            payload = json.loads(_read_text(path))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            claims.append(payload)
    return claims


def _sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _commits_touching(root: Path, commit_ref: str, paths: list[str]) -> list[str] | None:
    """Commits after commit_ref touching paths; None when unresolvable."""
    command = ["git", "-C", str(root), "log", "--format=%H", f"{commit_ref}..HEAD", "--", *paths]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return [line.strip() for line in (completed.stdout or "").splitlines() if line.strip()]


def _source_entries(freshness: dict[str, object]) -> list[dict[str, str]]:
    raw = freshness.get("source_paths")
    entries: list[dict[str, str]] = []
    if not isinstance(raw, list):
        return entries
    for item in raw:
        if isinstance(item, dict) and str(item.get("path") or "").strip():
            entries.append(
                {
                    "path": str(item.get("path")).strip(),
                    "sha256": str(item.get("sha256") or "").strip().lower(),
                }
            )
    return entries


def _evidence_paths(root: Path, items: list[WorkItem]) -> list[str]:
    refs: dict[str, None] = {}
    reviews_dir = root / REVIEWS_DIR
    if reviews_dir.is_dir():
        for path in sorted(reviews_dir.glob("VERIFY-*.json")):
            refs.setdefault(_rel(root, path), None)
    for item in items:
        for ref in item.evidence_refs:
            normalized = ref.replace("\\", "/").strip()
            if not normalized.endswith(".json"):
                continue
            if (root / normalized).is_file():
                refs.setdefault(normalized, None)
    return sorted(refs)


def _is_verification_record(rel_ref: str, payload: dict[str, object]) -> bool:
    if str(payload.get("schema") or "") == EVIDENCE_SCHEMA:
        return True
    return Path(rel_ref).name.startswith("VERIFY-")


def _owners_for(
    rel_ref: str,
    payload: dict[str, object],
    items: list[WorkItem],
    root: Path,
) -> tuple[WorkItem | None, list[WorkItem]]:
    referencing = [item for item in items if rel_ref in item.evidence_refs]
    record_work_id = str(payload.get("work_id") or "").strip()
    primary = next((item for item in referencing if item.work_id == record_work_id), None)
    if primary is None and record_work_id:
        primary = next((item for item in items if item.work_id == record_work_id), None)
        if primary is not None and primary not in referencing:
            referencing.append(primary)
    if primary is None:
        work_path = str(payload.get("work_path") or "").strip().replace("\\", "/")
        if work_path:
            loaded = _load_work_item(root, root / work_path)
            if loaded is not None:
                primary = loaded
                referencing.append(loaded)
    if primary is None and referencing:
        primary = referencing[0]
    return primary, referencing


def _evaluate_freshness(
    root: Path,
    payload: dict[str, object],
    primary: WorkItem | None,
    work_open: bool,
    claims: list[dict[str, object]],
) -> list[Reason]:
    freshness = payload.get("freshness")
    if not isinstance(freshness, dict):
        freshness = {}
    sources = _source_entries(freshness)
    commit_ref = str(freshness.get("commit_ref") or "").strip()
    if not sources and not commit_ref:
        return [
            Reason(
                code="freshness-unknown",
                kind="unknown",
                source="",
                detail="legacy record has no freshness block; staleness cannot be evaluated",
            )
        ]

    reasons: list[Reason] = []
    for entry in sources:
        source_path = root / entry["path"]
        if not source_path.is_file():
            reasons.append(
                Reason(
                    code="source-missing",
                    kind="strong",
                    source=entry["path"],
                    detail="tracked source file no longer exists",
                )
            )
            continue
        recorded = entry["sha256"]
        if not recorded:
            continue
        current = _sha256(source_path)
        if current is None:
            reasons.append(
                Reason(
                    code="source-unreadable",
                    kind="unknown",
                    source=entry["path"],
                    detail="tracked source file could not be hashed",
                )
            )
        elif current != recorded:
            reasons.append(
                Reason(
                    code="source-changed",
                    kind="strong",
                    source=entry["path"],
                    detail=f"sha256 changed after verification (recorded {recorded[:12]}, current {current[:12]})",
                )
            )

    if commit_ref:
        if sources:
            paths = [entry["path"] for entry in sources]
            commits = _commits_touching(root, commit_ref, paths)
            if commits is None:
                reasons.append(
                    Reason(
                        code="commit-ref-unresolvable",
                        kind="unknown",
                        source=commit_ref,
                        detail="recorded commit_ref cannot be resolved against this checkout",
                    )
                )
            elif commits:
                reasons.append(
                    Reason(
                        code="source-commits-after-verification",
                        kind="strong",
                        source=",".join(paths),
                        detail=f"{len(commits)} commit(s) touched tracked sources after {commit_ref[:12]} (latest {commits[0][:12]})",
                    )
                )
        else:
            reasons.append(
                Reason(
                    code="commit-ref-missing-source-paths",
                    kind="unknown",
                    source=commit_ref,
                    detail="commit_ref without source_paths cannot be scoped; record source paths to enable tracking",
                )
            )

    verified_at = _parse_timestamp(str(payload.get("verified_at") or ""))
    if primary is not None and verified_at is not None:
        if work_open:
            updated_at = _parse_timestamp(primary.updated_at)
            if updated_at is not None and updated_at > verified_at:
                reasons.append(
                    Reason(
                        code="work-item-updated-after-verification",
                        kind="strong",
                        source=primary.rel_path,
                        detail=f"work item updated_at {primary.updated_at} is later than verified_at; re-run work verify",
                    )
                )
        for claim in claims:
            claim_task = str(claim.get("task_id") or "").strip()
            claim_unit = str(claim.get("unit_id") or "").strip()
            if primary.work_id not in {claim_task, claim_unit} and primary.task_id != claim_task:
                continue
            claim_updated = _parse_timestamp(str(claim.get("updated_at") or ""))
            if claim_updated is not None and claim_updated > verified_at:
                reasons.append(
                    Reason(
                        code="claim-updated-after-verification",
                        kind="advisory",
                        source=str(claim.get("claim_id") or "claim"),
                        detail="task claim moved after verification; advisory only",
                    )
                )
                break
    return reasons


def analyze(root: Path) -> list[RecordResult]:
    root = root.resolve()
    items = _scan_work_items(root)
    claims = _scan_claims(root)
    results: list[RecordResult] = []
    for rel_ref in _evidence_paths(root, items):
        path = root / rel_ref
        try:
            payload = json.loads(_read_text(path))
        except json.JSONDecodeError:
            payload = None
        if not isinstance(payload, dict):
            results.append(
                RecordResult(
                    evidence_ref=rel_ref,
                    work_id="",
                    work_path="",
                    work_status="missing",
                    work_open=False,
                    verification_status="",
                    verified_at="",
                    verified_by="",
                    freshness="unknown",
                    severity="watch",
                    reasons=[
                        Reason(
                            code="evidence-unreadable",
                            kind="unknown",
                            source=rel_ref,
                            detail="evidence record is not valid JSON",
                        )
                    ],
                )
            )
            continue
        if not _is_verification_record(rel_ref, payload):
            continue
        primary, owners = _owners_for(rel_ref, payload, items, root)
        work_open = any(owner.open for owner in owners) if owners else False
        reasons = _evaluate_freshness(root, payload, primary, work_open, claims)
        if primary is None:
            reasons.append(
                Reason(
                    code="work-item-missing",
                    kind="unknown",
                    source=str(payload.get("work_path") or ""),
                    detail="referenced work item record was not found",
                )
            )
        has_strong = any(reason.kind == "strong" for reason in reasons)
        has_advisory = any(reason.kind == "advisory" for reason in reasons)
        if has_strong or has_advisory:
            freshness = "stale"
        elif reasons:
            freshness = "unknown"
        else:
            freshness = "fresh"
        if has_strong and work_open:
            severity = "block"
        elif reasons:
            severity = "watch"
        else:
            severity = "ok"
        results.append(
            RecordResult(
                evidence_ref=rel_ref,
                work_id=str(payload.get("work_id") or (primary.work_id if primary else "")),
                work_path=(primary.rel_path if primary else str(payload.get("work_path") or "")),
                work_status=(primary.status if primary else "missing"),
                work_open=work_open,
                verification_status=str(payload.get("status") or ""),
                verified_at=str(payload.get("verified_at") or ""),
                verified_by=str(payload.get("verified_by") or ""),
                freshness=freshness,
                severity=severity,
                reasons=reasons,
            )
        )
    return results


def build_report(root: Path, results: list[RecordResult]) -> dict[str, object]:
    severity_counts = Counter(result.severity for result in results)
    freshness_counts = Counter(result.freshness for result in results)
    block = severity_counts.get("block", 0)
    return {
        "schema": REPORT_SCHEMA,
        "root": str(root.resolve()),
        "generated_at": _local_iso(),
        "status": "fail" if block else "pass",
        "counts": {
            "records": len(results),
            "fresh": freshness_counts.get("fresh", 0),
            "stale": freshness_counts.get("stale", 0),
            "unknown": freshness_counts.get("unknown", 0),
            "block": block,
            "watch": severity_counts.get("watch", 0),
        },
        "records": [
            {
                "evidence_ref": result.evidence_ref,
                "work_id": result.work_id,
                "work_path": result.work_path,
                "work_status": result.work_status,
                "work_open": result.work_open,
                "verification_status": result.verification_status,
                "verified_at": result.verified_at,
                "verified_by": result.verified_by,
                "freshness": result.freshness,
                "severity": result.severity,
                "reasons": [
                    {
                        "code": reason.code,
                        "kind": reason.kind,
                        "source": reason.source,
                        "detail": reason.detail,
                    }
                    for reason in result.reasons
                ],
            }
            for result in results
        ],
    }


def render(root: Path, results: list[RecordResult]) -> str:
    report = build_report(root, results)
    counts = report["counts"]
    findings = sum(1 for result in results for _ in result.reasons)
    lines = [
        f"verification-freshness-gate: {'fail' if counts['block'] else 'pass'}",
        f"root={report['root']}",
        f"records={counts['records']}",
        f"fresh={counts['fresh']}",
        f"stale={counts['stale']}",
        f"unknown={counts['unknown']}",
        f"findings={findings}",
        f"block={counts['block']}",
        f"watch={counts['watch']}",
    ]
    for result in results:
        if result.severity == "ok":
            continue
        for reason in result.reasons:
            lines.append(
                f"- {result.severity} {reason.code} {result.evidence_ref}"
                f" work={result.work_id or '-'} status={result.work_status or '-'}"
                f" source={reason.source or '-'}: {reason.detail}"
            )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verification evidence freshness gate")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--check", action="store_true", help="Exit nonzero on block findings")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit machine-readable JSON report")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    results = analyze(args.root)
    if args.as_json:
        print(json.dumps(build_report(args.root, results), ensure_ascii=True, indent=2))
    else:
        print(render(args.root, results))
    if args.check and any(result.severity == "block" for result in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
