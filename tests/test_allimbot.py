"""Strict native-event and clean-profile tests for optional Allimbot."""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from agent_runtime import allimbot
from agent_runtime.template_profiles import selected_paths

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = ROOT / "src" / "agent_runtime" / "templates" / "project"
TEMPLATE_CLIENT = TEMPLATE_ROOT / "scripts" / "allimbot.py"
RECIPE = TEMPLATE_ROOT / ".allimbot.json"
SYNTHETIC_OPENAI_TOKEN = "-".join(
    ("sk", "proj", "SYNTHETIC", "CREDENTIAL", "123")
)
SYNTHETIC_GITHUB_TOKEN = "_".join(
    ("github", "pat", "SYNTHETIC", "CREDENTIAL")
)
EVENT_UUID = "123e4567-e89b-12d3-a456-426614174000"
SESSION_UUID = "123e4567-e89b-12d3-a456-426614174001"
TURN_UUID = "123e4567-e89b-12d3-a456-426614174002"
DEDUPE_SHA256 = "a" * 64


def _load_template_client():
    spec = importlib.util.spec_from_file_location(
        "template_allimbot_under_test", TEMPLATE_CLIENT
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Policy:
    def __init__(self, severity: str, allowlist: list[str]):
        self.severity = severity
        self.sensitive = False
        self.data_allowlist = tuple(allowlist)


class _Integration:
    spec = allimbot.PROJECT_SPEC
    project = allimbot.PROJECT_NAME
    source = allimbot.PROJECT_SOURCE
    events = {
        event_type: _Policy(policy["severity"], policy["data_allowlist"])
        for event_type, policy in allimbot.MANAGED_RECIPE["events"].items()
    }


def _fake_integrations(
    calls: list[tuple],
    *,
    constructor_error: bool = False,
    emit_error: bool = False,
    event_id: str = EVENT_UUID,
):
    class ProjectIntegration:
        @classmethod
        def load(cls, path):
            calls.append(("load", Path(path)))
            return _Integration()

    class ProjectEmitter:
        def __init__(self, integration):
            calls.append(("construct", integration))
            if constructor_error:
                raise RuntimeError("credential secret must not escape")

        def emit(self, event_type, summary, **kwargs):
            calls.append(("emit", event_type, summary, kwargs))
            if emit_error:
                raise OSError("spool path secret must not escape")
            return event_id

    return SimpleNamespace(
        ProjectIntegration=ProjectIntegration,
        ProjectEmitter=ProjectEmitter,
    )


def _valid_event() -> tuple[str, dict[str, object]]:
    return (
        "task.state.changed",
        {
            "task_id": "agent-runtime",
            "from_state": "review",
            "to_state": "completed",
            "owner_role": "runtime",
        },
    )


def test_managed_recipe_is_exact_current_allimbot_contract() -> None:
    assert json.loads(RECIPE.read_text(encoding="utf-8")) == allimbot.MANAGED_RECIPE
    assert {
        event: tuple(policy["data_allowlist"])
        for event, policy in allimbot.MANAGED_RECIPE["events"].items()
    } == {
        "attention.required": (
            "task_id",
            "attention_kind",
            "owner_role",
            "state",
        ),
        "task.state.changed": (
            "task_id",
            "from_state",
            "to_state",
            "owner_role",
        ),
        "release.gate.failed": ("gate", "release", "finding_count"),
        "turn.completed": ("task_id", "result_state", "duration_seconds"),
    }


def test_emit_validates_then_uses_project_emitter_without_flush(monkeypatch) -> None:
    calls: list[tuple] = []
    monkeypatch.setattr(
        allimbot.importlib,
        "import_module",
        lambda name: _fake_integrations(calls),
    )
    event_type, data = _valid_event()

    result = allimbot.emit_event(event_type, data)

    assert result.to_dict() == {
        "status": "spooled",
        "event_id": EVENT_UUID,
        "reason": None,
    }
    assert calls[0] == ("load", RECIPE.resolve())
    emitted = calls[-1]
    assert emitted[0:2] == ("emit", event_type)
    assert emitted[2] == (
        "Task agent-runtime: review -> completed (owner=runtime)"
    )
    assert emitted[3]["body"] == ""
    assert emitted[3]["data"] == data
    source = Path(allimbot.__file__).read_text(encoding="utf-8")
    assert ".flush(" not in source
    assert ".run_worker(" not in source


@pytest.mark.parametrize(
    ("event_type", "data"),
    [
        ("unknown.event", {}),
        (
            "attention.required",
            {
                "task_id": "TASK-1",
                "attention_kind": "review",
                "owner_role": "owner",
                "state": "blocked",
                "prompt": "secret",
            },
        ),
        (
            "release.gate.failed",
            {"gate": "release", "release": "v1", "finding_count": -1},
        ),
        (
            "turn.completed",
            {
                "task_id": "TASK-1",
                "result_state": "done\nsecret",
                "duration_seconds": 1,
            },
        ),
    ],
)
def test_policy_rejects_before_optional_import(
    monkeypatch, event_type: str, data: dict[str, object]
) -> None:
    def unexpected_import(_name):
        raise AssertionError("optional dependency must not be imported")

    monkeypatch.setattr(allimbot.importlib, "import_module", unexpected_import)
    with pytest.raises(allimbot.EventPolicyError) as raised:
        allimbot.emit_event(event_type, data)
    assert "secret" not in str(raised.value)


@pytest.mark.parametrize(
    ("event_type", "data", "correlations"),
    [
        (
            "task.state.changed",
            {
                "task_id": SYNTHETIC_OPENAI_TOKEN,
                "from_state": "review",
                "to_state": "completed",
                "owner_role": "runtime",
            },
            {},
        ),
        (
            "task.state.changed",
            {
                "task_id": "TASK-1",
                "from_state": "review",
                "to_state": "https://events.invalid/destination",
                "owner_role": "runtime",
            },
            {},
        ),
        (
            "task.state.changed",
            {
                "task_id": "TASK-1",
                "from_state": "provider-slack",
                "to_state": "completed",
                "owner_role": "runtime",
            },
            {},
        ),
        (
            "attention.required",
            {
                "task_id": "TASK-1",
                "attention_kind": "prompt-secret",
                "owner_role": "owner",
                "state": "blocked",
            },
            {},
        ),
        (
            "release.gate.failed",
            {
                "gate": "exception-secret",
                "release": "v1.0.0",
                "finding_count": 1,
            },
            {},
        ),
        (
            "turn.completed",
            {
                "task_id": "TASK-1",
                "result_state": "completed",
                "duration_seconds": 1,
            },
            {"dedupe_key": SYNTHETIC_GITHUB_TOKEN},
        ),
    ],
)
def test_sensitive_or_unmanaged_values_never_reach_optional_import(
    monkeypatch,
    event_type: str,
    data: dict[str, object],
    correlations: dict[str, str],
) -> None:
    def unexpected_import(_name):
        raise AssertionError("rejected values must not reach emitter construction")

    monkeypatch.setattr(allimbot.importlib, "import_module", unexpected_import)
    with pytest.raises(allimbot.EventPolicyError):
        allimbot.emit_event(event_type, data, **correlations)


@pytest.mark.parametrize(
    ("event_type", "data", "correlations"),
    [
        (
            "turn.completed",
            {
                "task_id": "127.0.0.1",
                "result_state": "completed",
                "duration_seconds": 1,
            },
            {},
        ),
        (
            "turn.completed",
            {
                "task_id": "events.invalid",
                "result_state": "completed",
                "duration_seconds": 1,
            },
            {},
        ),
        (
            "release.gate.failed",
            {"gate": "discord", "release": "v1.0.0", "finding_count": 1},
            {},
        ),
        (
            "release.gate.failed",
            {
                "gate": "ignorepreviousinstructions",
                "release": "v1.0.0",
                "finding_count": 1,
            },
            {},
        ),
        (
            "release.gate.failed",
            {
                "gate": "databaseconnectionfailed",
                "release": "v1.0.0",
                "finding_count": 1,
            },
            {},
        ),
        (
            "attention.required",
            {
                "task_id": "agent-runtime",
                "attention_kind": "governance-block",
                "owner_role": "discord",
                "state": "blocked",
            },
            {},
        ),
        (
            "turn.completed",
            {
                "task_id": "agent-runtime",
                "result_state": "completed",
                "duration_seconds": 1,
            },
            {"session_id": "events.invalid"},
        ),
        (
            "turn.completed",
            {
                "task_id": "agent-runtime",
                "result_state": "completed",
                "duration_seconds": 1,
            },
            {"turn_id": "discord"},
        ),
        (
            "turn.completed",
            {
                "task_id": "agent-runtime",
                "result_state": "completed",
                "duration_seconds": 1,
            },
            {"dedupe_key": "ignorepreviousinstructions"},
        ),
    ],
)
def test_arbitrary_display_safe_values_never_reach_optional_import(
    monkeypatch,
    event_type: str,
    data: dict[str, object],
    correlations: dict[str, str],
) -> None:
    def unexpected_import(_name):
        raise AssertionError("unregistered values must not reach emitter construction")

    monkeypatch.setattr(allimbot.importlib, "import_module", unexpected_import)
    with pytest.raises(allimbot.EventPolicyError):
        allimbot.emit_event(event_type, data, **correlations)


def test_registered_task_and_owner_role_are_resolved_from_runtime_ssot(
    tmp_path,
    monkeypatch,
) -> None:
    (tmp_path / ".allimbot.json").write_text(
        RECIPE.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    task = (
        tmp_path
        / "agents"
        / "lead_engineer"
        / "tasks"
        / "TASK-AR-647.md"
    )
    task.parent.mkdir(parents=True)
    task.write_text("---\nwork_id: TASK-AR-647\n---\n", encoding="utf-8")
    registry = tmp_path / "agents" / "project" / "ORG-MODEL.yml"
    registry.parent.mkdir(parents=True)
    registry.write_text(
        "schema: agent-runtime-org-model/v1\n"
        "roles:\n"
        "  - id: lead-engineer\n"
        "    tier: planner\n",
        encoding="utf-8",
    )
    calls: list[tuple] = []
    monkeypatch.setattr(
        allimbot.importlib,
        "import_module",
        lambda _name: _fake_integrations(calls),
    )

    result = allimbot.emit_event(
        "task.state.changed",
        {
            "task_id": "TASK-AR-647",
            "from_state": "review",
            "to_state": "completed",
            "owner_role": "lead-engineer",
        },
        root=tmp_path,
        session_id=SESSION_UUID,
        turn_id=TURN_UUID,
        dedupe_key=DEDUPE_SHA256,
    )

    assert result.spooled
    emitted = calls[-1]
    assert emitted[3]["session_id"] == SESSION_UUID
    assert emitted[3]["turn_id"] == TURN_UUID
    assert emitted[3]["dedupe_key"] == DEDUPE_SHA256


def test_managed_gate_and_semantic_release_are_accepted(monkeypatch) -> None:
    calls: list[tuple] = []
    monkeypatch.setattr(
        allimbot.importlib,
        "import_module",
        lambda _name: _fake_integrations(calls),
    )

    result = allimbot.emit_event(
        "release.gate.failed",
        {
            "gate": "owner-governance",
            "release": "v1.2.3-rc.4",
            "finding_count": 2,
        },
    )

    assert result.spooled


def test_recipe_drift_fails_closed_before_optional_import(
    tmp_path, monkeypatch
) -> None:
    recipe = json.loads(RECIPE.read_text(encoding="utf-8"))
    recipe["events"]["task.state.changed"]["data_allowlist"].append("body")
    path = tmp_path / ".allimbot.json"
    path.write_text(json.dumps(recipe), encoding="utf-8")
    imported = False

    def unexpected_import(_name):
        nonlocal imported
        imported = True
        raise AssertionError

    monkeypatch.setattr(allimbot.importlib, "import_module", unexpected_import)
    with pytest.raises(allimbot.EventPolicyError, match="drift"):
        allimbot.emit_event(*_valid_event(), recipe_path=path)
    assert imported is False


def test_composed_summary_bound_fails_closed_before_optional_import(
    monkeypatch,
) -> None:
    def unexpected_import(_name):
        raise AssertionError("summary policy must run before optional import")

    monkeypatch.setattr(allimbot.importlib, "import_module", unexpected_import)
    monkeypatch.setattr(allimbot, "_summary", lambda *_args: "A" * 301)
    with pytest.raises(allimbot.EventPolicyError, match="summary"):
        allimbot.emit_event(*_valid_event())


def test_missing_profile_and_dependency_are_bounded_unavailable(
    tmp_path, monkeypatch
) -> None:
    event_type, data = _valid_event()
    assert allimbot.emit_event(event_type, data, root=tmp_path).to_dict() == {
        "status": "unavailable",
        "event_id": None,
        "reason": "profile_not_selected",
    }

    def missing(_name):
        raise ModuleNotFoundError("not installed", name="allimbot")

    monkeypatch.setattr(allimbot.importlib, "import_module", missing)
    result = allimbot.emit_event(event_type, data)
    assert result.status == "unavailable"
    assert result.reason == "dependency_missing"


@pytest.mark.parametrize(
    ("constructor_error", "emit_error", "reason"),
    [
        (True, False, "configuration_unavailable"),
        (False, True, "spool_unavailable"),
    ],
)
def test_optional_configuration_and_spool_errors_never_leak(
    monkeypatch, constructor_error: bool, emit_error: bool, reason: str
) -> None:
    calls: list[tuple] = []
    monkeypatch.setattr(
        allimbot.importlib,
        "import_module",
        lambda _name: _fake_integrations(
            calls,
            constructor_error=constructor_error,
            emit_error=emit_error,
        ),
    )
    result = allimbot.emit_event(*_valid_event())
    serialized = json.dumps(result.to_dict())
    assert result.reason == reason
    assert "secret" not in serialized
    assert "credential" not in serialized


@pytest.mark.parametrize(
    "event_id",
    [
        SYNTHETIC_OPENAI_TOKEN,
        "discord",
        "ignorepreviousinstructions",
        "123E4567-E89B-12D3-A456-426614174000",
    ],
)
def test_non_uuid_dependency_event_id_is_never_returned(
    monkeypatch,
    event_id: str,
) -> None:
    calls: list[tuple] = []
    monkeypatch.setattr(
        allimbot.importlib,
        "import_module",
        lambda _name: _fake_integrations(
            calls,
            event_id=event_id,
        ),
    )

    result = allimbot.emit_event(*_valid_event())

    assert result.to_dict() == {
        "status": "unavailable",
        "event_id": None,
        "reason": "invalid_event_id",
    }
    assert "credential" not in json.dumps(result.to_dict()).casefold()


def test_legacy_notify_discards_every_supplied_string(monkeypatch) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    def fake_emit(event_type, data, **_kwargs):
        calls.append((event_type, dict(data)))
        return allimbot.EmitResult(status="unavailable", reason="dependency_missing")

    monkeypatch.setattr(allimbot, "emit_event", fake_emit)
    assert (
        allimbot.notify(
            "prompt-secret",
            title="title-secret",
            provider="provider-secret",
        )
        is False
    )
    serialized = json.dumps(calls)
    assert calls == [
        (
            "attention.required",
            {
                "task_id": "agent-runtime",
                "attention_kind": "legacy-notification",
                "owner_role": "owner",
                "state": "attention",
            },
        )
    ]
    assert "secret" not in serialized


def test_decorator_preserves_result_and_original_exception_without_text(
    monkeypatch,
) -> None:
    calls: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(
        allimbot,
        "emit_event",
        lambda event_type, data, **_kwargs: calls.append(
            (event_type, dict(data))
        )
        or allimbot.EmitResult(status="unavailable", reason="dependency_missing"),
    )

    @allimbot.notify_on_complete(title="ignored-secret")
    def succeed():
        return 42

    @allimbot.notify_on_complete()
    def fail():
        raise ValueError("exception-secret")

    assert succeed() == 42
    with pytest.raises(ValueError, match="exception-secret"):
        fail()
    serialized = json.dumps(calls)
    assert [item[1]["to_state"] for item in calls] == ["completed", "failed"]
    assert "exception-secret" not in serialized
    assert "ignored-secret" not in serialized


def test_decorator_event_failure_never_replaces_host_result_or_exception(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        allimbot,
        "emit_event",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            allimbot.EventPolicyError("managed recipe drift")
        ),
    )

    @allimbot.notify_on_complete()
    def succeed():
        return "host-result"

    @allimbot.notify_on_complete()
    def fail():
        raise RuntimeError("original-host-error")

    assert succeed() == "host-result"
    with pytest.raises(RuntimeError, match="original-host-error"):
        fail()


def test_template_wrapper_uses_stdin_and_never_forwards_legacy_text(
    monkeypatch,
) -> None:
    client = _load_template_client()
    captured: list[tuple[list[str], str]] = []

    def fake_run(command, **kwargs):
        captured.append((command, kwargs["input"]))
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(
                {"status": "spooled", "event_id": "evt-1", "reason": None}
            ),
            stderr="",
        )

    monkeypatch.setattr(client.subprocess, "run", fake_run)
    assert client.notify("message-secret", title="title-secret") is True
    command, raw = captured[0]
    assert command[1:3] == ["-m", "agent_runtime.allimbot"]
    assert "--stdin" in command and "--json" in command
    assert "secret" not in raw
    assert json.loads(raw)["event_type"] == "attention.required"


def test_profile_closure_is_additive_and_core_orchestrator_imports_cleanly(
    tmp_path,
) -> None:
    core_paths = selected_paths(TEMPLATE_ROOT, ("core",))
    security_paths = selected_paths(TEMPLATE_ROOT, ("core", "security-service"))
    names = lambda paths: {
        path.relative_to(TEMPLATE_ROOT).as_posix() for path in paths
    }
    core = names(core_paths)
    security = names(security_paths)
    profile_only = {
        ".allimbot.json",
        "agents/project/SECURITY-SERVICE-POLICY.json",
        "docs/security-service.md",
        "scripts/allimbot.py",
        "scripts/security_service_gate.py",
    }
    assert profile_only.isdisjoint(core)
    assert profile_only <= security
    assert "scripts/allimbot_stop_hook.cmd" not in security

    host = tmp_path / "core-host"
    for source in core_paths:
        relative = source.relative_to(TEMPLATE_ROOT)
        target = host / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    result = subprocess.run(
        [sys.executable, "-S", str(host / "scripts" / "agent_orchestrator.py"), "--help"],
        cwd=host,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode == 0, result.stderr


def test_legacy_delivery_and_ci_bypass_are_removed() -> None:
    source = Path(allimbot.__file__).read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "test.yml").read_text(
        encoding="utf-8"
    )
    example = (TEMPLATE_ROOT / ".env.example").read_text(encoding="utf-8")
    package_config = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    for legacy in (
        "/trigger",
        "ntfy.sh",
        "ALLIMBOT_URL",
        "ALLIMBOT_TOKEN",
        "ALLIMBOT_NTFY_TOPIC",
        "ALLIMBOT_PROVIDER",
    ):
        assert legacy not in source
        assert legacy not in workflow
        assert legacy not in example
    assert "notify_failure:" not in workflow
    assert "ALLIMBOT_ENDPOINT=\n" in example
    assert "ALLIMBOT_PROJECT_TOKEN=\n" in example
    assert "ALLIMBOT_SPOOL_PATH=\n" in example
    assert '"templates/project/.allimbot.json"' in package_config
