"""Launch the Agent Runtime console (UI).

A convenience launcher so the console is started consistently instead of an ad-hoc
`python -c "..."`. It resolves the repo root ABSOLUTELY from this file's location,
so the console always reads THIS repo's tasks regardless of the caller's working
directory -- launching from the wrong root was a "no tasks shown" cause.

    python scripts/run_console.py                # serve this repo at :8765
    python scripts/run_console.py --port 9000
    python scripts/run_console.py --root /other/checkout

The server blocks (serve_forever). For background/auto-start use, see
scripts/console_autostart.py.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch the Agent Runtime console UI")
    parser.add_argument("--host", default="127.0.0.1", help="bind host (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="bind port (default 8765)")
    parser.add_argument(
        "--root",
        default=str(ROOT),
        help="repo root to serve (default: this repo, resolved absolutely)",
    )
    args = parser.parse_args()

    src = ROOT / "src"
    if src.exists() and str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from agent_runtime import ui_console

    root = Path(args.root).resolve()
    print(f"Serving Agent Runtime console for: {root}")
    return ui_console.run_server(root, host=args.host, port=args.port)


if __name__ == "__main__":
    raise SystemExit(main())
