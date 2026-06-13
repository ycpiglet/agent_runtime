"""Focused tests for TASK-AR-365 external notification routing.

NO REAL NETWORK: every sender test uses a dry-run or an injected fake transport.
No webhook / email is ever fired. Secrets are asserted to NEVER reach served
ui_state. Subscription CRUD is asserted proposal-only.
"""

import json
import re
from pathlib import Path

from agent_runtime import notify_routing
from agent_runtime import ui_commands
from agent_runtime import ui_console
from agent_runtime import ui_state


# ----- severity -> routing-window mapping ------------------------------------


def test_severity_routing_immediate_aggregate_digest():
    # block / approval-pending -> immediate
    assert notify_routing.classify_severity({"event": "task.blocked"}) == notify_routing.SEVERITY_IMMEDIATE
    assert notify_routing.classify_severity({"event": "approval_pending"}) == notify_routing.SEVERITY_IMMEDIATE
    assert notify_routing.classify_severity({"event": "build.failed"}) == notify_routing.SEVERITY_IMMEDIATE
    assert notify_routing.classify_severity({"event": "x", "error": True}) == notify_routing.SEVERITY_IMMEDIATE
    # watch -> aggregate
    assert notify_routing.classify_severity({"event": "drift.watch"}) == notify_routing.SEVERITY_AGGREGATE
    assert notify_routing.classify_severity({"event": "task.warning"}) == notify_routing.SEVERITY_AGGREGATE
    # pass / completed -> digest
    assert notify_routing.classify_severity({"event": "task.completed"}) == notify_routing.SEVERITY_DIGEST
    assert notify_routing.classify_severity({"event": "gate.passed"}) == notify_routing.SEVERITY_DIGEST
    # unknown -> digest (least intrusive; can never escalate to immediate)
    assert notify_routing.classify_severity({"event": "random.noise"}) == notify_routing.SEVERITY_DIGEST
    # explicit severity wins
    assert notify_routing.classify_severity({"event": "task.completed", "severity": "immediate"}) == notify_routing.SEVERITY_IMMEDIATE
    # plain string accepted
    assert notify_routing.classify_severity("task.blocked") == notify_routing.SEVERITY_IMMEDIATE


def test_routing_window_minutes_map_to_immediate_aggregate_digest():
    assert notify_routing.routing_window_minutes(notify_routing.SEVERITY_IMMEDIATE) == 0
    assert notify_routing.routing_window_minutes(notify_routing.SEVERITY_AGGREGATE, aggregate_minutes=5) == 5
    assert notify_routing.routing_window_minutes(notify_routing.SEVERITY_AGGREGATE, aggregate_minutes=15) == 15
    # invalid aggregate window falls back to the default 5
    assert notify_routing.routing_window_minutes(notify_routing.SEVERITY_AGGREGATE, aggregate_minutes=7) == 5
    assert notify_routing.routing_window_minutes(notify_routing.SEVERITY_DIGEST) == notify_routing.DIGEST_WINDOW_MINUTES


# ----- channel recipe payload shaping ----------------------------------------


def test_discord_recipe_shapes_content_and_embed():
    payload = notify_routing.build_discord_payload({"event": "task.blocked", "task_id": "TASK-AR-1", "role": "owner", "detail": "stuck"})
    assert "[immediate]" in payload["content"]
    assert "TASK-AR-1" in payload["content"]
    embed = payload["embeds"][0]
    fields = {field["name"]: field["value"] for field in embed["fields"]}
    assert fields["Task"] == "TASK-AR-1"
    assert fields["Severity"] == "immediate"


def test_telegram_recipe_shapes_text_and_optional_chat_id():
    no_chat = notify_routing.build_telegram_payload({"event": "task.completed", "task_id": "TASK-AR-2"})
    assert "chat_id" not in no_chat  # chat id only set when an opted-in runner passes it
    assert no_chat["disable_notification"] is True  # non-immediate quiets the ping
    with_chat = notify_routing.build_telegram_payload({"event": "task.blocked"}, chat_id="123")
    assert with_chat["chat_id"] == "123"
    assert with_chat["disable_notification"] is False  # immediate is loud


def test_email_recipe_shapes_subject_and_body():
    payload = notify_routing.build_email_payload({"event": "task.completed", "task_id": "TASK-AR-3"}, to="owner@example.com")
    assert payload["subject"].startswith("[agent-runtime][digest]")
    assert "TASK-AR-3" in payload["subject"]
    assert payload["to"] == "owner@example.com"
    assert payload["content_type"] == "text/plain"


def test_build_payload_dispatches_and_rejects_unknown_kind():
    assert "content" in notify_routing.build_payload("discord", {"event": "x"})
    try:
        notify_routing.build_payload("sms", {"event": "x"})
    except ValueError as exc:
        assert "unknown channel kind" in str(exc)
    else:
        raise AssertionError("expected ValueError for unknown kind")


# ----- webhook sender: injectable transport, NEVER real network ---------------


def test_webhook_sender_default_is_dormant_and_sends_nothing():
    # A plain sender uses the null transport: no I/O, sends nothing.
    sender = notify_routing.WebhookSender()
    result = sender.send({"kind": "discord", "name": "ops", "webhook_url": "https://example.invalid/hook"}, {"event": "task.blocked"})
    assert result["sent"] is False
    assert result["transport"] == "null"


def test_webhook_sender_uses_injected_fake_transport_and_builds_payload():
    captured = []

    def fake_transport(request):
        # The fake records the request; it NEVER touches the network.
        captured.append(request)
        return {"sent": True, "transport": "fake"}

    sender = notify_routing.WebhookSender(transport=fake_transport)
    out = sender.send(
        {"kind": "discord", "name": "discord-ops", "webhook_url": "https://example.invalid/hook"},
        {"event": "task.blocked", "task_id": "TASK-AR-9"},
    )
    assert out["sent"] is True
    assert len(captured) == 1
    request = captured[0]
    # The payload is correctly shaped for the recipe and carries the destination
    # url from the channel config (the secret is supplied at call time, never
    # stored on the sender).
    assert request["kind"] == "discord"
    assert request["url"] == "https://example.invalid/hook"
    assert "[immediate]" in request["payload"]["content"]
    assert "TASK-AR-9" in request["payload"]["content"]


def test_webhook_sender_dry_run_bypasses_transport_entirely():
    def explode(_request):
        raise AssertionError("dry_run must never call the transport")

    sender = notify_routing.WebhookSender(transport=explode, dry_run=True)
    out = sender.send({"kind": "telegram", "name": "tg"}, {"event": "task.completed"})
    assert out["sent"] is False
    assert out["transport"] == "dry_run"
    assert out["request"]["kind"] == "telegram"


# ----- aggregation-window batching -------------------------------------------


def test_aggregation_buffer_flushes_immediate_and_batches_others():
    buffer = notify_routing.AggregationBuffer(aggregate_minutes=5)
    # immediate is never buffered
    decision = buffer.add({"event": "task.blocked"})
    assert decision["immediate"] is True and decision["buffered"] is False
    # aggregate + digest accumulate
    buffer.add({"event": "task.warning"})
    buffer.add({"event": "task.warning"})
    buffer.add({"event": "task.completed"})
    counts = buffer.pending_counts()
    assert counts[notify_routing.SEVERITY_AGGREGATE] == 2
    assert counts[notify_routing.SEVERITY_DIGEST] == 1

    # before the 5-min window elapses, nothing flushes
    assert buffer.flush_due(notify_routing.SEVERITY_AGGREGATE, now_minutes=3) == []
    assert buffer.pending_counts()[notify_routing.SEVERITY_AGGREGATE] == 2
    # at/after 5 min, the aggregate batch flushes once and clears
    flushed = buffer.flush_due(notify_routing.SEVERITY_AGGREGATE, now_minutes=6)
    assert len(flushed) == 2
    assert buffer.pending_counts()[notify_routing.SEVERITY_AGGREGATE] == 0
    # digest waits a full day
    assert buffer.flush_due(notify_routing.SEVERITY_DIGEST, now_minutes=60) == []
    digest = buffer.flush_due(notify_routing.SEVERITY_DIGEST, now_minutes=notify_routing.DIGEST_WINDOW_MINUTES + 1)
    assert len(digest) == 1


# ----- secrets handling: local config + secret-free status --------------------


def _write_local_config(root: Path) -> None:
    (root / "agents" / "project").mkdir(parents=True, exist_ok=True)
    (root / "agents" / "project" / "notifications.local.json").write_text(
        json.dumps(
            {
                "channels": [
                    {
                        "name": "discord-ops",
                        "kind": "discord",
                        "enabled": True,
                        "severities": ["immediate", "aggregate"],
                        "aggregate_minutes": 15,
                        "webhook_url": "https://discord.example.invalid/SECRET-HOOK",
                    },
                    {
                        "name": "tg",
                        "kind": "telegram",
                        "enabled": False,
                        "bot_token": "SECRET-BOT-TOKEN",
                        "chat_id": "SECRET-CHAT",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )


def test_routing_status_strips_secrets(tmp_path):
    _write_local_config(tmp_path)
    status = notify_routing.routing_status(tmp_path, now="2026-06-14T00:00:00+09:00")
    blob = json.dumps(status)
    # NO secret value survives into the status.
    for secret in ("SECRET-HOOK", "SECRET-BOT-TOKEN", "SECRET-CHAT", "discord.example.invalid"):
        assert secret not in blob
    # Only channel name / kind / enabled / configured / severities survive.
    channels = {channel["name"]: channel for channel in status["channels"]}
    assert channels["discord-ops"]["kind"] == "discord"
    assert channels["discord-ops"]["enabled"] is True
    assert channels["discord-ops"]["configured"] is True
    assert "webhook_url" not in channels["discord-ops"]
    assert status["dormant"] is False
    assert status["totals"]["enabled"] == 1


def test_routing_status_is_dormant_when_no_config(tmp_path):
    status = notify_routing.routing_status(tmp_path)
    assert status["config_present"] is False
    assert status["dormant"] is True
    assert status["channels"] == []


def test_served_ui_state_never_contains_secret_values(tmp_path):
    _write_local_config(tmp_path)
    state = ui_state.build_state(tmp_path)
    blob = json.dumps(state)
    for secret in ("SECRET-HOOK", "SECRET-BOT-TOKEN", "SECRET-CHAT"):
        assert secret not in blob
    routing = state["notification_routing"]
    assert routing["schema"] == notify_routing.ROUTING_SCHEMA
    assert any(channel["name"] == "discord-ops" for channel in routing["channels"])


def test_gitignore_covers_local_secret_config(tmp_path):
    gitignore = Path(__file__).resolve().parents[1] / ".gitignore"
    text = gitignore.read_text(encoding="utf-8")
    assert "agents/project/notifications.local.json" in text
    assert "notifications.local.json" in text


def test_example_template_has_placeholders_only_no_real_secrets():
    example = Path(__file__).resolve().parents[1] / "agents" / "project" / "notifications.local.example.json"
    data = json.loads(example.read_text(encoding="utf-8"))
    for channel in data["channels"]:
        # All channels ship disabled, and any secret-bearing field is a placeholder.
        assert channel["enabled"] is False
        for key in ("webhook_url", "bot_token", "chat_id", "smtp_host", "smtp_user", "smtp_password", "to"):
            if key in channel:
                assert "PUT-YOUR" in channel[key]


# ----- subscription CRUD is proposal-only ------------------------------------


def test_subscription_create_is_proposal_only(tmp_path):
    record = ui_commands.submit_command(
        tmp_path,
        {
            "type": "subscription.create",
            "payload": {"actor": "ui", "channel": "discord-ops", "kind": "discord", "severities": ["immediate"], "aggregate_minutes": 5},
        },
    )
    assert record["status"] == "queued"
    result = record["result"]
    assert result["mutation_boundary"] == "proposal_only"
    assert result["dispatch_boundary"] == "opt_in_local_runner"
    proposal_path = tmp_path / result["changed"][0]
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    assert proposal["target_file"] == "agents/project/notifications.local.json"
    assert proposal["rule"]["kind"] == "discord"
    assert proposal["secrets_boundary"] == "local_config_only"
    # The proposal lives under .ui_outbox -- the local config is NOT written.
    assert ".ui_outbox" in result["changed"][0]
    assert not (tmp_path / "agents" / "project" / "notifications.local.json").exists()


def test_subscription_rejects_secret_values(tmp_path):
    record = ui_commands.submit_command(
        tmp_path,
        {
            "type": "subscription.create",
            "payload": {"actor": "ui", "channel": "discord-ops", "kind": "discord", "webhook_url": "https://leak.invalid/hook"},
        },
    )
    assert record["status"] == "failed"
    assert any("secret values are not allowed" in err for err in record["errors"])


def test_subscription_validates_kind_severity_and_window(tmp_path):
    bad_kind = ui_commands.submit_command(tmp_path, {"type": "subscription.create", "payload": {"channel": "c", "kind": "sms"}})
    assert bad_kind["status"] == "failed"
    bad_sev = ui_commands.submit_command(tmp_path, {"type": "subscription.create", "payload": {"channel": "c", "kind": "email", "severities": ["loud"]}})
    assert bad_sev["status"] == "failed"
    bad_window = ui_commands.submit_command(tmp_path, {"type": "subscription.create", "payload": {"channel": "c", "kind": "email", "aggregate_minutes": 7}})
    assert bad_window["status"] == "failed"
    toggle_no_bool = ui_commands.submit_command(tmp_path, {"type": "subscription.toggle", "target": "c", "payload": {}})
    assert toggle_no_bool["status"] == "failed"


def test_subscription_toggle_and_delete_are_proposals(tmp_path):
    toggle = ui_commands.submit_command(tmp_path, {"type": "subscription.toggle", "target": "discord-ops", "payload": {"enabled": True}})
    assert toggle["status"] == "queued"
    assert toggle["result"]["action"] == "toggle"
    delete = ui_commands.submit_command(tmp_path, {"type": "subscription.delete", "target": "discord-ops", "payload": {}})
    assert delete["status"] == "queued"
    assert delete["result"]["action"] == "delete"


def test_subscription_command_types_in_allowlist():
    for command_type in ("subscription.create", "subscription.update", "subscription.delete", "subscription.toggle"):
        assert command_type in ui_commands.COMMAND_TYPES


# ----- console: serves the routing view, tokenized + escaped, secret-free -----


def test_console_serves_notification_routing_view_and_route(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    # Sidebar entry sits in the OPS group and reuses hash routing.
    assert 'data-view="notifications" data-route="ops/notifications"' in html
    assert 'id="view-notifications"' in html
    assert 'id="subscription-form"' in html

    # JS renders + uses the proposal-only command path; fields are escaped.
    assert "renderNotificationRouting" in js
    assert 'type: "subscription.create"' in js
    assert 'type: "subscription.toggle"' in js
    assert 'type: "subscription.delete"' in js
    assert "escapeHtml(channel.name)" in js
    # The render reads the secret-free resource; never references a secret field.
    for secret_field in ("webhook_url", "bot_token", "chat_id", "smtp_password"):
        assert secret_field not in js

    # CSS selectors exist and the API route is wired.
    for selector in [".routing-status", ".routing-dot-immediate", ".routing-token-digest"]:
        assert selector in css
    payload = json.loads(ui_console.build_response("/api/notification-routing", tmp_path).body.decode("utf-8"))
    assert payload["resource"] == "notification_routing"


def test_console_notification_routing_css_uses_tokens_not_raw_color(tmp_path):
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")
    root_start = css.index(":root {")
    root_block = css[root_start : css.index("}", root_start)]
    dark_start = css.index('[data-theme="dark"] {')
    dark_block = css[dark_start : css.index("}", dark_start)]
    body_css = css.replace(root_block, "").replace(dark_block, "")
    hex_pattern = re.compile(r"#[0-9a-fA-F]{3,8}\b")
    rgba_pattern = re.compile(r"rgba?\(")
    routing_lines = [line for line in body_css.splitlines() if ".routing" in line]
    assert routing_lines, "expected routing CSS rules to exist"
    for line in routing_lines:
        assert not hex_pattern.search(line), f"raw hex in routing CSS: {line.strip()}"
        assert not rgba_pattern.search(line), f"raw rgba in routing CSS: {line.strip()}"
