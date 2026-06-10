from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import planning_loop
except ModuleNotFoundError:
    from scripts import planning_loop

ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_trigger(root: Path, *, trigger: str, propose: bool = False, now: str | None = None) -> dict[str, Any]:
    action = "propose" if propose else "scan"
    gate = planning_loop.planning_gate(root, trigger=trigger, action=action)
    if gate["status"] == "block":
        return {"status": "block", "gate": gate, "canonical_mutation_allowed": False}

    scan_payload = planning_loop.scan(root, trigger=trigger, now=now)
    scan_path = root / "agents" / "planning" / "scans" / f"{scan_payload['id']}.json"
    _write_json(scan_path, scan_payload)

    proposal_result: dict[str, Any] | None = None
    if propose:
        proposal_result = planning_loop.create_proposals(root, scan_payload, now=now)

    return {
        "status": "pass" if gate["status"] == "pass" else "watch",
        "gate": gate,
        "scan_path": scan_path.relative_to(root).as_posix(),
        "proposal_result": proposal_result,
        "canonical_mutation_allowed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a gated proposal-only planning trigger")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--trigger", choices=sorted(planning_loop.ALLOWED_TRIGGERS), default="schedule")
    parser.add_argument("--propose", action="store_true")
    parser.add_argument("--now")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    payload = run_trigger(Path(args.root).resolve(), trigger=args.trigger, propose=args.propose, now=args.now)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"status={payload['status']} trigger={args.trigger} canonical_mutation_allowed=false")
    return 0 if payload["status"] != "block" else 1


if __name__ == "__main__":
    raise SystemExit(main())
