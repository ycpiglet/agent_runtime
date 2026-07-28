#!/usr/bin/env python3
from __future__ import annotations

"""Repository entrypoint for task-linked compound records."""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent_runtime.knowledge_records import *  # noqa: F401,F403,E402
from agent_runtime.knowledge_records import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
