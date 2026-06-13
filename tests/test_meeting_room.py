import importlib.util
import json
from pathlib import Path

from agent_runtime import ui_console, ui_state

_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "meeting_room.py"


def _load_meeting_room_module():
    spec = importlib.util.spec_from_file_location("meeting_room_under_test", _SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


meeting_room = _load_meeting_room_module()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _claim(root: Path, *, claim_id: str, role: str, task_id: str, status: str = "in_progress") -> None:
    payload = {
        "claim_id": claim_id,
        "agent_instance_id": f"{role}-{claim_id}",
        "agent_role": role,
        "status": status,
        "task_id": task_id,
        "task_set_id": "TASKSET-AR-UI-LIVING-CONSOLE",
        "display_name": role.replace("_", " ").title(),
    }
    _write(root / "agents" / "runtime" / "task_claims" / f"{claim_id}.json", json.dumps(payload))


def _task(root: Path, task_id: str, *, status: str = "in_progress") -> None:
    text = "\n".join(
        [
            "---",
            f"id: {task_id}",
            f"title: {task_id} title",
            f"status: {status}",
            "owner: lead-engineer",
            "priority: P1",
            "task_set_id: TASKSET-AR-UI-LIVING-CONSOLE",
            "---",
            "",
            "## Goal",
            "",
            "Do the thing.",
            "",
        ]
    )
    _write(root / "agents" / "lead_engineer" / "tasks" / f"{task_id}-thing.md", text)


# --- scripts/meeting_room.py plan -----------------------------------------


def test_plan_writes_well_formed_meeting_skeleton(tmp_path):
    result = meeting_room.plan(
        tmp_path,
        topic="Living Console Sync",
        participants=["lead_engineer", "planner"],
        meeting_type="review",
        rounds=2,
        task_id="TASK-AR-361",
        now="2026-06-13T10:00:00+09:00",
    )
    assert result["status"] == "recorded"
    assert result["meeting_id"] == "MEETING-2026-06-13-living-console-sync"
    target = tmp_path / result["path"]
    assert target.exists()
    text = target.read_text(encoding="utf-8")

    meta, body = ui_state.parse_frontmatter(text)
    assert meta["type"] == "meeting"
    assert meta["meeting_type"] == "review"
    assert meta["rounds"] == 2
    assert meta["task_id"] == "TASK-AR-361"
    assert meta["participants"] == ["lead_engineer", "planner"]
    assert "## Agenda" in body
    assert "### Round 1" in body and "### Round 2" in body
    assert "### Round 3" not in body
    assert "## Decision" in body


def test_plan_is_deterministic_for_same_inputs(tmp_path):
    other = tmp_path / "other"
    kwargs = dict(
        topic="Repeatable Topic",
        participants=["a", "b"],
        meeting_type="meeting",
        rounds=3,
        now="2026-06-13T10:00:00+09:00",
    )
    first = meeting_room.plan(tmp_path, **kwargs)
    second = meeting_room.plan(other, **kwargs)
    assert (tmp_path / first["path"]).read_text(encoding="utf-8") == (other / second["path"]).read_text(encoding="utf-8")


def test_plan_rejects_too_few_participants(tmp_path):
    result = meeting_room.plan(tmp_path, topic="Solo", participants=["only_one"], rounds=2)
    assert result["status"] == "failed"
    assert any("2 participants" in error for error in result["errors"])
    assert not list((tmp_path / "reviews").glob("MEETING-*.md")) if (tmp_path / "reviews").exists() else True


def test_plan_rejects_non_positive_rounds(tmp_path):
    result = meeting_room.plan(tmp_path, topic="Zero", participants=["a", "b"], rounds=0)
    assert result["status"] == "failed"
    assert any("rounds must be > 0" in error for error in result["errors"])


def test_plan_rejects_invalid_meeting_type(tmp_path):
    result = meeting_room.plan(tmp_path, topic="Bad", participants=["a", "b"], meeting_type="party", rounds=1)
    assert result["status"] == "failed"
    assert any("invalid meeting type" in error for error in result["errors"])


def test_plan_dedupes_participants_case_insensitively(tmp_path):
    result = meeting_room.plan(
        tmp_path,
        topic="Dedupe",
        participants=["Lead", "lead", "Planner", ""],
        rounds=1,
        now="2026-06-13T10:00:00+09:00",
    )
    assert result["status"] == "recorded"
    assert result["participants"] == ["Lead", "Planner"]


def test_plan_refuses_overwrite_without_flag(tmp_path):
    kwargs = dict(topic="Dup", participants=["a", "b"], rounds=1, now="2026-06-13T10:00:00+09:00")
    assert meeting_room.plan(tmp_path, **kwargs)["status"] == "recorded"
    second = meeting_room.plan(tmp_path, **kwargs)
    assert second["status"] == "failed"
    assert any("already exists" in error for error in second["errors"])
    assert meeting_room.plan(tmp_path, overwrite=True, **kwargs)["status"] == "recorded"


def test_plan_cli_json_output(tmp_path, capsys):
    exit_code = meeting_room.main(
        [
            "plan",
            "--root",
            str(tmp_path),
            "--topic",
            "CLI Topic",
            "--participant",
            "lead_engineer",
            "--participant",
            "planner",
            "--rounds",
            "2",
            "--json",
        ]
    )
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "recorded"
    assert payload["schema"] == "agent-runtime-meeting-plan/v1"
    assert (tmp_path / payload["path"]).exists()


def test_plan_output_is_ascii_safe(tmp_path, capsys):
    meeting_room.main(
        [
            "plan",
            "--root",
            str(tmp_path),
            "--topic",
            "ASCII",
            "--participants",
            "a,b",
            "--rounds",
            "1",
        ]
    )
    captured = capsys.readouterr().out
    captured.encode("ascii")  # raises if any non-ascii byte leaked to stdout


# --- meeting_room resource + route ----------------------------------------


def test_meeting_room_resource_shape(tmp_path):
    _task(tmp_path, "TASK-AR-361", status="in_progress")
    _task(tmp_path, "TASK-AR-999", status="completed")
    _claim(tmp_path, claim_id="c1", role="lead_engineer", task_id="TASK-AR-361")
    _claim(tmp_path, claim_id="c2", role="planner", task_id="TASK-AR-361")

    state = ui_state.build_state(tmp_path)
    room = state["meeting_room"]
    assert room["schema"] == "agent-runtime-meeting-room/v1"
    roles = {agent["id"] for agent in room["available_agents"]}
    assert {"lead_engineer", "planner"} <= roles
    topic_ids = {topic["id"] for topic in room["topic_options"]}
    assert "TASK-AR-361" in topic_ids
    assert "TASK-AR-999" not in topic_ids  # completed tasks are not offered
    assert room["constraints"]["min_participants"] == 2
    assert room["command"]["mutation_boundary"] == "proposal_only"
    assert room["meeting_types"] == ["meeting", "seminar", "review"]


def test_meeting_room_dedupes_agent_cards_by_role(tmp_path):
    _claim(tmp_path, claim_id="c1", role="lead_engineer", task_id="TASK-AR-361")
    _claim(tmp_path, claim_id="c2", role="lead_engineer", task_id="TASK-AR-362")
    state = ui_state.build_state(tmp_path)
    cards = [a for a in state["meeting_room"]["available_agents"] if a["id"] == "lead_engineer"]
    assert len(cards) == 1
    assert cards[0]["instances"] == 2


def test_meeting_room_route_returns_200(tmp_path):
    _claim(tmp_path, claim_id="c1", role="lead_engineer", task_id="TASK-AR-361")
    for path in ("/api/meeting_room", "/api/meeting-room"):
        response = ui_console.build_response(path, tmp_path)
        assert response.status == 200
        payload = json.loads(response.body.decode("utf-8"))
        assert payload["resource"] == "meeting_room"
        assert payload["items"]["schema"] == "agent-runtime-meeting-room/v1"


def test_meeting_room_panel_and_dnd_anchors_present(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    # nav + view panel
    assert 'data-view="meeting"' in html
    assert 'id="view-meeting"' in html
    assert 'id="meeting-dropzone"' in html
    assert 'id="meeting-available"' in html
    assert 'id="meeting-config-form"' in html
    # drag/drop + keyboard equivalents
    assert 'draggable="true"' in js
    assert "dragstart" in js and "drop" in js and "dragover" in js
    assert 'event.key === "Enter"' in js  # keyboard add
    assert 'event.key === "Delete"' in js  # keyboard remove
    # proposal-only command path, never direct reviews mutation
    assert "runtime.request_meeting" in js
    assert "scripts/meeting_room.py plan" in js
    # styled drop zone
    assert ".meeting-dropzone" in css
