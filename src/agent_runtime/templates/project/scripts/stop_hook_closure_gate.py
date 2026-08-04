"""Stop hook: block closure when substantial work lacks compound/review/retro.

Emits Stop-hook JSON only for block paths. Non-blocking and explicit bypass
paths stay silent. Unexpected gate errors fail closed with a bounded message.
Honors AGENT_RUNTIME_CLOSURE_GATE_DISABLE via closure_gate.
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
    except Exception:  # noqa: BLE001 - emit only a bounded fail-closed result
        _emit_stop_payload(
            {
                "decision": "block",
                "reason": "closure-gate-error",
                "systemMessage": (
                    "Closure validation failed unexpectedly. Repair or explicitly "
                    "bypass the gate before stopping."
                ),
            }
        )
        return 0
    _emit_stop_payload(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
