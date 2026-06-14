"""Stop hook: block closure when substantial work lacks compound/review/retro.

Emits a Stop-hook JSON decision. Best-effort: any failure approves (never blocks a
stop on a gate error). Honors AGENT_RUNTIME_CLOSURE_GATE_DISABLE via closure_gate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    try:
        import closure_gate

        result = closure_gate.assess(Path.cwd())
        payload = {
            "decision": result["decision"],
            "reason": result["reason"],
            "systemMessage": result["message"] if result["decision"] == "block" else "",
        }
    except Exception as exc:  # noqa: BLE001 - never block a stop on a gate error
        payload = {"decision": "approve", "reason": f"closure-gate-error:{exc!r}", "systemMessage": ""}
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
