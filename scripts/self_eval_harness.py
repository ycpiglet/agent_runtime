"""Cross-version self-eval harness + advisory RSI fitness gate (TASK-AR-530, GH #128).

Objective, version-over-version metrics so platform changes are provably
*improvement*, not unfalsifiable *change*. FIXED (held-out) metrics stay
meaningful across versions; VARIABLE metrics are tied to a version's new
capability. Per the council, the RSI fitness gate is ADVISORY (reports the
N->N+1 delta, NEVER blocks) until a trustworthy baseline + R3 sign-off exist.

  --report   compute + print the current metric snapshot (JSON)
  --write    persist the snapshot to SELF-EVAL-BASELINE.json (the held-out baseline)
  --gate     advisory: compare current vs baseline, report improvement/regression
             per metric; exit 0 ALWAYS (advisory mode, not a blocking gate yet)

Where a fixed metric has no captured substrate yet (WORK-SCHEMA actuals such as
rework_count / first_try_test_pass), it is reported as `null` and excluded from
the fitness delta -- the schema is the spine, the captured values are the muscle.

Host real-usage pipeline (GH #128 request 4): hosts (e.g. autofolio) supply
per-cycle metric snapshots as ``agent-runtime-host-eval/v1`` JSON files under
``agents/host/eval/`` (the host-owned namespace from
docs/host-context-read-location.md). The harness ingests them additively into
the snapshot's ``hosts`` section; absence of the directory is not an error, and
unreadable/foreign files are listed loudly as skipped, never dropped silently.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TASKS = ROOT / "agents" / "lead_engineer" / "tasks"
REVIEWS = ROOT / "reviews"
BASELINE = ROOT / "agents" / "project" / "work-items" / "SELF-EVAL-BASELINE.json"
SCHEMA = "agent-runtime-self-eval/v1"
HOST_SCHEMA = "agent-runtime-host-eval/v1"

# Fixed (held-out) metrics: meaningful regardless of version. Some are computed
# now; the rest are declared so the held-out spine is stable and a later
# WORK-SCHEMA actuals capture fills them in.
FIXED_METRICS = (
    "completed_tasks",
    "open_tasks",
    "verification_coverage_pct",
    "est_tokens_total",
    "est_hours_total",
    # Declared, awaiting WORK-SCHEMA actuals capture (reported null until then):
    "first_try_test_pass_rate",
    "gate_failure_count",
    "rework_count",
    "reopened_count",
    "merge_conflict_count",
    "owner_intervention_count",
)
# "higher is better" direction per computed metric (for the advisory verdict).
HIGHER_IS_BETTER = {
    "completed_tasks": True,
    "verification_coverage_pct": True,
    "open_tasks": False,
    "est_tokens_total": False,
    "est_hours_total": False,
}


def _frontmatter(text: str) -> dict[str, str]:
    meta: dict[str, str] = {}
    if not text.startswith("---"):
        return meta
    block = text.split("---", 2)[1] if text.count("---") >= 2 else ""
    for line in block.splitlines():
        if ":" in line and not line.startswith(" "):
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta


def load_host_snapshots(root: Path = ROOT) -> tuple[list[dict], list[str]]:
    """Read host-supplied eval snapshots from agents/host/eval/ (absence is fine)."""
    hosts: list[dict] = []
    skipped: list[str] = []
    host_dir = root / "agents" / "host" / "eval"
    if not host_dir.is_dir():
        return hosts, skipped
    for path in sorted(host_dir.rglob("*.json")):
        rel = path.relative_to(root).as_posix()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            skipped.append(f"{rel}: unreadable ({exc.__class__.__name__})")
            continue
        if not isinstance(data, dict) or data.get("schema") != HOST_SCHEMA:
            skipped.append(f"{rel}: schema is not {HOST_SCHEMA}")
            continue
        if not data.get("host") or not data.get("cycle"):
            skipped.append(f"{rel}: missing required host/cycle fields")
            continue
        hosts.append(data)
    return hosts, skipped


def compute_snapshot(version: str, root: Path = ROOT) -> dict:
    tasks_dir = root / "agents" / "lead_engineer" / "tasks"
    reviews_dir = root / "reviews"
    completed: list[str] = []
    open_count = 0
    est_tokens = 0
    est_hours = 0.0
    captured: dict[str, int] = {"gate_failure_count": 0, "rework_count": 0, "reopened_count": 0}
    have_actuals = False
    for path in tasks_dir.glob("TASK-*.md"):
        meta = _frontmatter(path.read_text(encoding="utf-8", errors="replace"))
        status = meta.get("status", "").lower()
        try:
            est_tokens += int(meta.get("est_tokens", "0") or 0)
            est_hours += float(meta.get("est_hours", "0") or 0)
        except ValueError:
            pass
        for field in captured:
            if field in meta:
                have_actuals = True
                try:
                    captured[field] += int(meta.get(field, "0") or 0)
                except ValueError:
                    pass
        if status in {"completed", "done", "released"}:
            completed.append(meta.get("id", path.stem))
        elif status not in {"triage", "intake"}:
            open_count += 1
    # Verification coverage: completed tasks that have an independent W4B record.
    w4b_tasks = {
        match.group(0)
        for path in reviews_dir.glob("W4B-*.md")
        for match in [re.search(r"TASK-AR-[0-9]+", path.stem)]
        if match
    }
    verified = sum(1 for tid in completed if tid in w4b_tasks)
    coverage = round(100.0 * verified / len(completed), 1) if completed else 0.0

    fixed = {name: None for name in FIXED_METRICS}
    fixed["completed_tasks"] = len(completed)
    fixed["open_tasks"] = open_count
    fixed["verification_coverage_pct"] = coverage
    fixed["est_tokens_total"] = est_tokens
    fixed["est_hours_total"] = round(est_hours, 1)
    if have_actuals:
        fixed["gate_failure_count"] = captured["gate_failure_count"]
        fixed["rework_count"] = captured["rework_count"]
        fixed["reopened_count"] = captured["reopened_count"]

    hosts, host_skipped = load_host_snapshots(root)
    snapshot = {
        "schema": SCHEMA,
        "version": version,
        "fixed": fixed,
        "variable": {
            # per-version capability metrics (cycle-specific; extend per version):
            "w4b_records": len(list(reviews_dir.glob("W4B-*.md"))),
            "council_deliberations": len(list(reviews_dir.glob("COUNCIL-*.md"))),
        },
        "hosts": hosts,
        "note": "Advisory only. null fixed metrics await WORK-SCHEMA actuals capture.",
    }
    if host_skipped:
        snapshot["host_skipped"] = host_skipped
    return snapshot


def advisory_gate(current: dict, baseline: dict | None) -> list[str]:
    """Report per-metric improvement/regression vs baseline. Never blocks."""
    lines: list[str] = []
    if not baseline:
        lines.append("self-eval: no baseline; run --write to set the held-out baseline")
        return lines
    cur, base = current.get("fixed", {}), baseline.get("fixed", {})
    lines.append(f"self-eval: {baseline.get('version')} -> {current.get('version')} (advisory)")
    for name in FIXED_METRICS:
        c, b = cur.get(name), base.get(name)
        if c is None or b is None:
            continue
        delta = round(c - b, 1)
        if delta == 0:
            verdict = "flat"
        else:
            improved = (delta > 0) == HIGHER_IS_BETTER.get(name, True)
            verdict = "improved" if improved else "REGRESSED"
        lines.append(f"  {name}: {b} -> {c} ({'+' if delta > 0 else ''}{delta}) {verdict}")
    for host in current.get("hosts", []):
        supplied = len(host.get("fixed") or {}) + len(host.get("variable") or {})
        lines.append(
            f"  host[{host.get('host')}] cycle {host.get('cycle')}:"
            f" {supplied} real-usage metrics supplied"
        )
    for reason in current.get("host_skipped", []):
        lines.append(f"  host-eval SKIPPED {reason}")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Cross-version self-eval harness (TASK-AR-530)")
    parser.add_argument("--version", default="current", help="version label for the snapshot")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--write", action="store_true", help="persist snapshot as the held-out baseline")
    parser.add_argument("--gate", action="store_true", help="advisory fitness gate vs baseline (never blocks)")
    args = parser.parse_args()

    snapshot = compute_snapshot(args.version)
    if args.write:
        BASELINE.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
        print(f"wrote={BASELINE}")
        return 0
    if args.gate:
        baseline = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.exists() else None
        for line in advisory_gate(snapshot, baseline):
            print(line)
        return 0  # advisory: never blocks
    # default / --report
    print(json.dumps(snapshot, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
