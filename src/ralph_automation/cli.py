"""Legacy module entrypoint for ``python -m ralph_automation.cli``."""

from __future__ import annotations

from agent_runtime.cli import *  # noqa: F401,F403
from agent_runtime.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
