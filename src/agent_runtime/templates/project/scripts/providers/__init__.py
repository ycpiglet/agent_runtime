"""Provider adapter package for agent_worker.py.

A Provider is the backend that generates an agent's reply. TASK-101 broadened
the interface to `run(...) -> ProviderResult`, a `run_stream` hook, and typed
errors (see base.py). DummyProvider runs on the new interface; Claude/Codex/OpenAI
are registered as provider entry points with optional dependencies lazy-loaded on
demand.
"""

from __future__ import annotations

import importlib
import os

from .base import (
    Chunk,
    Provider,
    ProviderAuthError,
    ProviderError,
    ProviderResult,
    ProviderTimeout,
)
from .dummy import DummyProvider
from .openai import OpenAIProvider

PROVIDERS = {
    "dummy": (".dummy", "DummyProvider"),
    "openai": (".openai", "OpenAIProvider"),
    "claude": (".claude", "ClaudeProvider"),
    "claude-agent": (".claude_agent", "ClaudeAgentProvider"),
    "codex": (".codex", "CodexProvider"),
    "codex-agent": (".codex", "CodexAgentProvider"),
}

# Billable providers that make external cost-bearing calls. These are gated behind
# an explicit env opt-in so no entry point (agent_worker, agent_loop, and
# related runners) can spend tokens by accident.
LIVE_PROVIDERS = {"claude", "claude-agent", "codex", "codex-agent"}

# Optional dependency hints shown when a provider module cannot import required
# third-party packages.
PROVIDER_EXTRAS = {
    "claude": ("anthropic", "python-dotenv"),
    "claude-agent": ("anthropic", "python-dotenv"),
    "codex": ("requests", "python-dotenv"),
    "codex-agent": ("requests", "python-dotenv"),
}


def _load_provider(name: str) -> type[Provider]:
    module_name, class_name = PROVIDERS[name]
    try:
        module = importlib.import_module(module_name, package=__package__)
    except ModuleNotFoundError as exc:
        extras = PROVIDER_EXTRAS.get(name)
        if extras:
            missing = exc.name or "optional dependency"
            raise ProviderError(
                f"provider '{name}' requires '{missing}'. "
                f"Install optional deps with `python -m pip install -U 'agent_runtime[{name}]'` "
                f"(or install: {', '.join(extras)})."
            ) from exc
        raise

    provider_cls = getattr(module, class_name, None)
    if provider_cls is None:
        raise ProviderError(f"provider '{name}' is misconfigured: missing class {class_name}")
    return provider_cls


def get_provider(name: str) -> Provider:
    if name not in PROVIDERS:
        known = ", ".join(sorted(PROVIDERS))
        raise SystemExit(f"unknown provider '{name}'. known: {known}")
    if name in LIVE_PROVIDERS and os.environ.get("DISPATCH_ENABLE_LIVE") != "1":
        raise SystemExit(
            f"live provider '{name}' is billable and gated by a guardrail. "
            "Set DISPATCH_ENABLE_LIVE=1 to enable real token spend, or use "
            "'--provider dummy'. This prevents accidental runaway cost — "
            "agent_worker/agent_loop/pipeline default to the safe path."
        )
    return _load_provider(name)()


__all__ = [
    "Provider",
    "ProviderResult",
    "Chunk",
    "ProviderError",
    "ProviderTimeout",
    "ProviderAuthError",
    "DummyProvider",
    "OpenAIProvider",
    "PROVIDERS",
    "get_provider",
]
