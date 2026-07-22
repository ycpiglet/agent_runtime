"""Never-block and lifecycle wiring tests for optional allimbot delivery."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from agent_runtime import allimbot as package_allimbot

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = ROOT / "src" / "agent_runtime" / "templates" / "project"
TEMPLATE_CLIENT = TEMPLATE_ROOT / "scripts" / "allimbot.py"
ALLIMBOT_ENV = (
    "ALLIMBOT_URL",
    "ALLIMBOT_TOKEN",
    "ALLIMBOT_NTFY_TOPIC",
    "ALLIMBOT_PROVIDER",
)


def _load_template_client():
    spec = importlib.util.spec_from_file_location("template_allimbot_under_test", TEMPLATE_CLIENT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(params=["package", "template"])
def client(request):
    return package_allimbot if request.param == "package" else _load_template_client()


class _Response:
    def __init__(self, status: int = 204):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def _clear_config(monkeypatch) -> None:
    for name in ALLIMBOT_ENV:
        monkeypatch.delenv(name, raising=False)


def test_package_and_template_clients_match() -> None:
    package_path = ROOT / "src" / "agent_runtime" / "allimbot.py"
    assert package_path.read_text(encoding="utf-8") == TEMPLATE_CLIENT.read_text(encoding="utf-8")


def test_unconfigured_is_silent_noop_without_network(client, monkeypatch, capsys) -> None:
    _clear_config(monkeypatch)

    def unexpected_request(*_args, **_kwargs):
        raise AssertionError("unconfigured client must not touch the network")

    monkeypatch.setattr(client.urllib.request, "urlopen", unexpected_request)
    assert client.notify("done") is False
    assert client._main(["done"]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_local_dashboard_is_first_and_timeout_is_capped(client, monkeypatch) -> None:
    _clear_config(monkeypatch)
    monkeypatch.setenv("ALLIMBOT_TOKEN", "test-token")
    monkeypatch.setenv("ALLIMBOT_NTFY_TOPIC", "fallback-topic")
    calls: list[tuple[str, dict[str, str], float]] = []

    def fake_urlopen(request, *, timeout):
        calls.append((request.full_url, json.loads(request.data), timeout))
        return _Response()

    monkeypatch.setattr(client.urllib.request, "urlopen", fake_urlopen)
    assert client.notify("TASK-1 complete", provider="ntfy", timeout=99) is True
    assert calls == [
        (
            "http://127.0.0.1:8787/trigger",
            {
                "token": "test-token",
                "message": "TASK-1 complete",
                "title": "agent_runtime",
                "provider": "ntfy",
            },
            3.0,
        )
    ]


def test_dashboard_failure_falls_back_to_ntfy(client, monkeypatch) -> None:
    _clear_config(monkeypatch)
    monkeypatch.setenv("ALLIMBOT_TOKEN", "test-token")
    monkeypatch.setenv("ALLIMBOT_NTFY_TOPIC", "fallback-topic")
    calls: list[tuple[str, dict[str, str], float]] = []

    def fake_urlopen(request, *, timeout):
        payload = json.loads(request.data)
        calls.append((request.full_url, payload, timeout))
        if request.full_url.endswith("/trigger"):
            raise OSError("dashboard unavailable")
        return _Response(200)

    monkeypatch.setattr(client.urllib.request, "urlopen", fake_urlopen)
    assert client.notify("done") is True
    assert [call[0] for call in calls] == [
        "http://127.0.0.1:8787/trigger",
        "https://ntfy.sh",
    ]
    assert calls[1][1] == {
        "topic": "fallback-topic",
        "title": "agent_runtime",
        "message": "done",
    }
    assert [call[2] for call in calls] == [3.0, 3.0]


def test_dashboard_token_is_never_sent_to_a_non_loopback_url(client, monkeypatch) -> None:
    _clear_config(monkeypatch)
    monkeypatch.setenv("ALLIMBOT_TOKEN", "local-only-token")
    monkeypatch.setenv("ALLIMBOT_URL", "https://example.com/collect")
    monkeypatch.setenv("ALLIMBOT_NTFY_TOPIC", "fallback-topic")
    calls: list[str] = []

    def fake_urlopen(request, *, timeout):
        calls.append(request.full_url)
        assert b"local-only-token" not in request.data
        assert timeout == 3.0
        return _Response(200)

    monkeypatch.setattr(client.urllib.request, "urlopen", fake_urlopen)
    assert client.notify("done") is True
    assert calls == ["https://ntfy.sh"]


def test_all_delivery_errors_are_swallowed(client, monkeypatch, capsys) -> None:
    _clear_config(monkeypatch)
    monkeypatch.setenv("ALLIMBOT_TOKEN", "test-token")
    monkeypatch.setenv("ALLIMBOT_NTFY_TOPIC", "fallback-topic")

    def fail(*_args, **_kwargs):
        raise TimeoutError("offline")

    monkeypatch.setattr(client.urllib.request, "urlopen", fail)
    assert client.notify("done") is False
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_decorator_preserves_success_and_original_failure(monkeypatch) -> None:
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(
        package_allimbot,
        "notify",
        lambda message, title="agent_runtime", **_kwargs: calls.append((message, title)) or False,
    )

    @package_allimbot.notify_on_complete(title="daily")
    def succeed():
        return 42

    @package_allimbot.notify_on_complete(title="daily")
    def fail():
        raise ValueError("secret-value-must-not-leave-process")

    assert succeed() == 42
    with pytest.raises(ValueError, match="secret-value-must-not-leave-process"):
        fail()
    assert "completed" in calls[0][0]
    assert "failed" in calls[1][0]
    assert "ValueError" in calls[1][0]
    assert "secret-value" not in calls[1][0]
    assert [title for _, title in calls] == ["daily", "daily"]


def test_template_stop_hook_and_blank_configuration_are_shipped() -> None:
    hooks = json.loads((TEMPLATE_ROOT / ".codex" / "hooks.json").read_text(encoding="utf-8"))
    stop_commands = [
        hook["command"]
        for group in hooks["hooks"]["Stop"]
        for hook in group["hooks"]
    ]
    assert "scripts\\allimbot_stop_hook.cmd" in stop_commands
    wrapper = (TEMPLATE_ROOT / "scripts" / "allimbot_stop_hook.cmd").read_text(encoding="utf-8")
    assert "allimbot.py" in wrapper
    assert "exit /b 0" in wrapper

    example = (TEMPLATE_ROOT / ".env.example").read_text(encoding="utf-8")
    assert "ALLIMBOT_TOKEN=\n" in example
    assert "ALLIMBOT_NTFY_TOPIC=\n" in example
    assert "ALLIMBOT_PROVIDER=\n" in example
    assert "<" not in example

    package_config = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert '"templates/project/.env.example"' in package_config


def test_ci_failure_delivery_is_explicitly_opt_in_and_aggregate() -> None:
    workflow = (ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
    assert "vars.ALLIMBOT_CI_NOTIFY_ENABLED == 'true'" in workflow
    assert "notify_failure:" in workflow
    assert "needs: test" in workflow
    assert "needs.test.result == 'failure'" in workflow
    assert "secrets.ALLIMBOT_NTFY_TOPIC" in workflow
    assert "templates/project/scripts/allimbot.py" in workflow
    assert workflow.count("Send optional allimbot CI failure notification") == 1
