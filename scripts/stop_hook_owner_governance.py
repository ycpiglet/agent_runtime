"""Stop hook wrapper for the Owner governance gate.

The governance gate prints human-readable logs. Stop hooks require structured
JSON on stdout, so this wrapper captures gate output and emits a Stop decision.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_MESSAGE_CHARS = 6000


def _clip(text: str) -> str:
    if len(text) <= MAX_MESSAGE_CHARS:
        return text
    return text[:MAX_MESSAGE_CHARS] + "\n...[truncated]"


def _run_gate() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/owner_governance_gate.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def build_payload(result: subprocess.CompletedProcess[str]) -> dict[str, str]:
    output = ((result.stdout or "") + (result.stderr or "")).strip()
    if result.returncode == 0:
        return {
            "decision": "approve",
            "reason": "owner governance gate passed",
            "systemMessage": _clip(output),
        }
    return {
        "decision": "block",
        "reason": f"owner governance gate failed with code {result.returncode}",
        "systemMessage": _clip(output),
    }


def main() -> int:
    payload = build_payload(_run_gate())
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
