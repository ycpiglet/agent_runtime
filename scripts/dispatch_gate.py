"""Seam + risk dispatch gate (org-delegation Unit 559, TASK-AR-559).

Per Unit, decide how the Lead may dispatch a Worker:
  - risk decision: auto-dispatch vs Owner-gate, from risk_tier / security_sensitive /
    approval_required / budget_cap / escalation_triggers (mirrors the work-schema +
    the auto-mode classifier philosophy).
  - seam decision: among auto units, run in PARALLEL only when footprints
    (target_files) are disjoint; otherwise SERIALIZE through the Lead. This is the
    research-backed guard against parallel workers editing interdependent code.

Pure planning logic (no side effects); the orchestrator (Unit 560) consumes the plan.
Spec: docs/superpowers/specs/2026-06-14-agent-org-delegation-model-design.md (step 3).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HIGH_RISK_TIERS = {"high", "critical"}
# Escalation triggers that force an Owner gate when present on a unit.
GATE_TRIGGERS = {"security", "data_integrity", "irreversible", "external",
                 "destructive", "prod_data", "secret"}


def risk_mode(meta: dict) -> tuple[str, list[str]]:
    """Return ("auto"|"owner-gate", reasons) for one unit's risk metadata."""
    reasons: list[str] = []
    if str(meta.get("risk_tier", "")).lower() in HIGH_RISK_TIERS:
        reasons.append(f"risk_tier:{meta.get('risk_tier')}")
    if meta.get("security_sensitive"):
        reasons.append("security_sensitive")
    if meta.get("approval_required"):
        reasons.append("approval_required")
    cap = meta.get("budget_cap")
    est = meta.get("est_cost", meta.get("est_tokens"))
    if cap is not None and est is not None and float(est) > float(cap):
        reasons.append("over_budget")
    triggers = {str(t).lower() for t in (meta.get("escalation_triggers") or [])}
    fired = sorted(triggers & GATE_TRIGGERS)
    if fired:
        reasons.append("escalation:" + ",".join(fired))
    return ("owner-gate" if reasons else "auto", reasons)


def _footprint(meta: dict) -> set[str]:
    return {str(x) for x in (meta.get("target_files") or [])}


def plan_dispatch(units: list[tuple[str, dict]], *, max_parallel: int = 4) -> list[dict]:
    """Decide mode + seam for a list of (unit_id, meta).

    auto + footprint disjoint from already-scheduled parallel work + under the
    concurrency cap -> parallel; auto but conflicting/over-cap -> serialize;
    risky -> owner-gate.
    """
    scheduled: set[str] = set()
    parallel = 0
    plan: list[dict] = []
    for uid, meta in units:
        mode, reasons = risk_mode(meta)
        fp = _footprint(meta)
        entry = {"unit_id": uid, "mode": mode, "reasons": reasons, "footprint": sorted(fp)}
        if mode == "auto":
            conflict = bool(fp & scheduled) or parallel >= max_parallel
            entry["seam"] = "serialize" if conflict else "parallel"
            if entry["seam"] == "parallel":
                scheduled |= fp
                parallel += 1
        else:
            entry["seam"] = "owner-gate"
        plan.append(entry)
    return plan


def _front_meta(path: Path) -> dict:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from org_model_gate import parse_frontmatter  # stdlib parser (no PyYAML)
    return parse_frontmatter(path.read_text(encoding="utf-8", errors="replace"))


def _units_from_dir(d: Path) -> list[tuple[str, dict]]:
    out = []
    for p in sorted(d.glob("UNIT-*.md")):
        meta = _front_meta(p)
        out.append((meta.get("unit_id", p.stem), meta))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Plan seam-aware, risk-gated unit dispatch.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--input", help="JSON list of unit metas (each with unit_id)")
    g.add_argument("--units-dir", help="dir of UNIT-*.md files")
    ap.add_argument("--max-parallel", type=int, default=4)
    a = ap.parse_args(argv)
    if a.input:
        metas = json.loads(Path(a.input).read_text(encoding="utf-8"))
        units = [(m["unit_id"], m) for m in metas]
    else:
        units = _units_from_dir(Path(a.units_dir))
    plan = plan_dispatch(units, max_parallel=a.max_parallel)
    summary = {
        "parallel": [e["unit_id"] for e in plan if e.get("seam") == "parallel"],
        "serialize": [e["unit_id"] for e in plan if e.get("seam") == "serialize"],
        "owner_gate": [e["unit_id"] for e in plan if e["mode"] == "owner-gate"],
    }
    print(json.dumps({"plan": plan, "summary": summary}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
