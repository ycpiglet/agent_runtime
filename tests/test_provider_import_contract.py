from __future__ import annotations

import builtins
import importlib
import sys
from pathlib import Path

import pytest


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "src/agent_runtime/templates/project/scripts"


def _import_missing_modules(monkeypatch, missing):
    original_import = builtins.__import__

    def _shim(name, globals=None, locals=None, fromlist=(), level=0):
        if name in missing:
            raise ModuleNotFoundError(f"No module named '{name}'")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _shim)


def _load_provider_package():
    removed = [name for name in sys.modules if name == "providers" or name.startswith("providers.")]
    for name in removed:
        del sys.modules[name]
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        return importlib.import_module("providers")
    finally:
        sys.path.pop(0)


def test_get_provider_dummy_works_without_optional_dependencies(monkeypatch):
    _import_missing_modules(
        monkeypatch,
        {
            "requests",
            "anthropic",
            "dotenv",
            "dotenv_values",
            "watchdog",
            "python_dotenv",
        },
    )
    providers = _load_provider_package()
    provider = providers.get_provider("dummy")
    assert provider.name == "dummy"


def test_get_provider_codex_prompts_install_hint_when_requests_missing(monkeypatch):
    monkeypatch.setenv("DISPATCH_ENABLE_LIVE", "1")
    _import_missing_modules(monkeypatch, {"requests"})
    providers = _load_provider_package()
    with pytest.raises(Exception) as exc:
        providers.get_provider("codex")
    assert "requests" in str(exc.value).lower()
    assert "agent_runtime[codex]" in str(exc.value) or "extra" in str(exc.value).lower()


def test_unknown_provider_raises_system_exit():
    providers = _load_provider_package()
    with pytest.raises(SystemExit):
        providers.get_provider("does-not-exist")
