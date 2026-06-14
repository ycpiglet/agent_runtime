import importlib
import os
import subprocess
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def test_agent_runtime_is_primary_import_and_ralph_automation_is_legacy_alias():
    runtime = importlib.import_module("agent_runtime")
    legacy = importlib.import_module("ralph_automation")

    assert runtime.__version__
    assert legacy.__version__ == runtime.__version__
    assert importlib.import_module("ralph_automation.cli").main is importlib.import_module("agent_runtime.cli").main


def test_pyproject_declares_agent_runtime_distribution_and_one_release_aliases():
    text = (PACKAGE_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'name = "agent_runtime"' in text
    assert 'agent_runtime = "agent_runtime.cli:main"' in text
    assert 'ralph = "agent_runtime.cli:main"' in text
    # TASK-AR-531: package-data is now a multi-line list -- the base glob is
    # retained PLUS the dot-paths the glob alone silently drops (GH #121).
    assert '"templates/project/**/*"' in text
    assert '"templates/project/.githooks/**/*"' in text


def test_legacy_module_cli_executes_for_one_release():
    env = dict(os.environ)
    env["PYTHONPATH"] = str(PACKAGE_ROOT / "src")

    result = subprocess.run(
        [sys.executable, "-m", "ralph_automation.cli", "--version"],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    assert result.stdout.strip()
