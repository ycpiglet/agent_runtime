#!/usr/bin/env python3
"""Legacy wrapper for agent_runtime_migration_inventory.py."""

from __future__ import annotations

from scripts.agent_runtime_migration_inventory import *  # noqa: F401,F403
from scripts.agent_runtime_migration_inventory import main


if __name__ == "__main__":
    raise SystemExit(main())
