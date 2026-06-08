"""Legacy compatibility alias for :mod:`agent_runtime`.

This package remains for one release so existing host projects can migrate from
``ralph_automation`` imports to ``agent_runtime`` imports without breaking.
"""

from __future__ import annotations

import importlib
import sys

from agent_runtime import __version__

_COMPAT_MODULES = (
    "config",
    "exporter",
    "host_update",
    "inventory",
    "lock",
    "publish_bundle",
    "publish_check",
    "publish_github_execute",
    "publish_github_plan",
    "publish_github_status",
    "publish_tag_smoke",
    "release_preflight",
    "sanitize",
    "sync",
)

for _module_name in _COMPAT_MODULES:
    sys.modules[f"{__name__}.{_module_name}"] = importlib.import_module(f"agent_runtime.{_module_name}")

__all__ = ["__version__"]
