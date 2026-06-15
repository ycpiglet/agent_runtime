"""Multi-host distributed claim safety (TASK-AR-554, product-maturity-uplift).

claim_lease.py guarantees race-safe *local* ownership (file locks), but multiple HOSTS
sharing the repo via git cannot see each other's file locks. This gate detects the
cross-host hazard: the same resource (task_id/unit_id) actively claimed by two different
hosts. A claim carries a host identity (`host`/`host_id`, else derived from `callsite_id`);
the gate flags/blocks conflicting cross-host active claims so a second host does not
silently double-claim. Read-only detection; stdlib-only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAIMS = ROOT / "agents" / "runtime" / "task_claims"
ACTIVE = {"claimed", "in_progress", "review", "assigned", "working"}


def claim_host(claim: dict) -> str:
    for key in ("host", "host_id", "hostname"):
        if claim.get(key):
            return str(claim[key])
    # derive from callsite_id like "host:pane:..." or "machine-a/term1"
    cs = str(claim.get("callsite_id", "") or "")
    for sep in (":", "/", "@"):
        if sep in cs:
            return cs.split(sep, 1)[0]
    return cs or "unknown"


def _resource(claim: dict) -> str:
    return str(claim.get("unit_id") or claim.get("task_id") or claim.get("claim_id") or "?")


def detect_conflicts(claims: list[dict]) -> list[dict]:
    by_resource: dict[str, list[dict]] = {}
    for c in claims:
        if str(c.get("status", "")).lower() in ACTIVE:
            by_resource.setdefault(_resource(c), []).append(c)
    conflicts = []
    for resource, group in by_resource.items():
        hosts = {claim_host(c) for c in group if claim_host(c) not in ("", "unknown")}
        if len(hosts) >= 2:
            conflicts.append({"resource": resource, "hosts": sorted(hosts),
                              "claims": [c.get("claim_id") for c in group]})
    return conflicts


def load_claims(claims_dir: Path = CLAIMS) -> list[dict]:
    out = []
    if claims_dir.exists():
        for p in sorted(claims_dir.glob("CLAIM-*.json")):
            try:
                out.append(json.loads(p.read_text(encoding="utf-8", errors="replace")))
            except Exception:
                continue
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Detect cross-host active-claim conflicts.")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--enforce", action="store_true")
    a = ap.parse_args(argv)
    conflicts = detect_conflicts(load_claims())
    for c in conflicts:
        print(f"multi-host: CONFLICT resource={c['resource']} hosts={c['hosts']} claims={c['claims']}")
    level = "block" if a.enforce else "watch"
    print(f"multi-host-claim-gate: {level} conflicts={len(conflicts)}")
    return 1 if (a.enforce and conflicts) else 0


if __name__ == "__main__":
    raise SystemExit(main())
