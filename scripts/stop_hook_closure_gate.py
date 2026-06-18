"""Stop hook: block closure when substantial work lacks compound/review/retro.

Emits Stop-hook JSON for every path; non-blocking paths use the empty Codex
Stop output object. Best-effort: any failure approves without blocking. Honors
AGENT_RUNTIME_CLOSURE_GATE_DISABLE via closure_gate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import stop_hook_session_scope


def _emit_stop_payload(payload: dict[str, object]) -> None:
    if payload.get("decision") == "block":
        result: dict[str, object] = {
            "decision": "block",
            "reason": payload.get("reason", "closure gate blocked stop"),
        }
        system_message = payload.get("systemMessage")
        if system_message:
            result["systemMessage"] = system_message
        print(json.dumps(result, ensure_ascii=False))
        return
    print("{}")


def main(argv: list[str] | None = None) -> int:
    try:
        scope = stop_hook_session_scope.assess(stop_hook_session_scope.read_hook_input(), root=Path.cwd())
        if scope.get("bypass"):
            _emit_stop_payload({"decision": "approve", "reason": str(scope.get("reason") or "scope bypass")})
            return 0
        import closure_gate

        result = closure_gate.assess(Path.cwd())
        payload = {
            "decision": result["decision"],
            "reason": result["reason"],
            "systemMessage": result["message"] if result["decision"] == "block" else "",
        }
    except Exception:  # noqa: BLE001 - never block a stop on a gate error
        _emit_stop_payload({"decision": "approve", "reason": "closure gate best-effort error bypass"})
        return 0
    _emit_stop_payload(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
