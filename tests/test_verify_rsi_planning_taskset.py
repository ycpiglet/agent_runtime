from __future__ import annotations

import importlib.util
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "verify_rsi_planning_taskset.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("verify_rsi_planning_taskset", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_run_sets_local_pythonpath_for_subprocesses(monkeypatch):
    module = _load_module()
    captured = {}

    def fake_run(command, **kwargs):
        captured["env"] = kwargs.get("env")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    result = module.run(["python", "-m", "pytest"])

    assert result["status"] == "passed"
    env = captured["env"]
    assert env is not None
    paths = env["PYTHONPATH"].split(os.pathsep)
    assert paths[:2] == [".", "src"]
