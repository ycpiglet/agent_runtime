"""External notification routing -- webhook-first (Discord / Telegram / email).

TASK-AR-365. Export work events (completed / blocked / approval-pending) to the
owner's messenger via a generic webhook sender plus per-channel recipes, with
severity-based routing windows to prevent alert fatigue (LangSmith pattern:
generic webhook + channel recipes + aggregation windows).

SAFETY (read this before touching anything):

- This module talks to EXTERNAL services. It NEVER fires a real webhook/email on
  its own. The real sender is DORMANT until the owner provides secrets in the
  LOCAL gitignored config (``agents/project/notifications.local.json``). The
  default state sends nothing. Tests inject a fake transport; no real network.
- The actual ``WebhookSender`` takes an *injectable transport*. The default
  transport is a no-op that records nothing and performs no I/O. A runtime owner
  who opts in supplies a real transport in a separate local runner. The console
  + ui_state never construct a real-network transport and never read secret
  values into served state.
- Secrets (webhook URLs / bot tokens / SMTP creds) live ONLY in the local config
  file (gitignored). ``load_local_config`` reads it; ``routing_status`` derives a
  SECRET-FREE status (channel name + enabled flag + recipe kind only) for the UI.

Nothing here mutates canonical repo state. Subscription-rule edits arrive as
proposals via ui_commands (proposal-only). This module is pure routing + payload
shaping + an opt-in local dispatch buffer.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

# --- Severity model -----------------------------------------------------------
# Each runtime work-event maps to a severity, and each severity maps to a routing
# window that decides WHEN it is delivered (anti alert-fatigue):
#   immediate  -> block / approval-pending: dispatched as soon as observed.
#   aggregate  -> watch-level: batched into a 5/15-minute window, one rollup msg.
#   digest     -> pass / completed: rolled into a once-a-day digest.
SEVERITY_IMMEDIATE = "immediate"
SEVERITY_AGGREGATE = "aggregate"
SEVERITY_DIGEST = "digest"

ROUTING_WINDOWS = (SEVERITY_IMMEDIATE, SEVERITY_AGGREGATE, SEVERITY_DIGEST)

# Aggregate window choices (minutes). The owner picks 5 or 15 for watch events.
AGGREGATE_WINDOWS_MINUTES = (5, 15)
DEFAULT_AGGREGATE_WINDOW_MINUTES = 5
DIGEST_WINDOW_MINUTES = 24 * 60

# Event-name -> severity. Names are matched case-insensitively as substrings so
# both raw runtime event names (e.g. ``task.blocked``) and synthesized work
# events (e.g. ``approval_pending``) route correctly. Order matters: the first
# matching rule wins, so the most urgent terms are checked first.
_SEVERITY_RULES: tuple[tuple[str, str], ...] = (
    # immediate: anything that needs the owner NOW
    ("blocked", SEVERITY_IMMEDIATE),
    ("block", SEVERITY_IMMEDIATE),
    ("approval_pending", SEVERITY_IMMEDIATE),
    ("approval-pending", SEVERITY_IMMEDIATE),
    ("approval_required", SEVERITY_IMMEDIATE),
    ("approval", SEVERITY_IMMEDIATE),
    ("error", SEVERITY_IMMEDIATE),
    ("failed", SEVERITY_IMMEDIATE),
    ("failure", SEVERITY_IMMEDIATE),
    # aggregate: watch-level signal, batched
    ("watch", SEVERITY_AGGREGATE),
    ("warning", SEVERITY_AGGREGATE),
    ("stale", SEVERITY_AGGREGATE),
    ("drift", SEVERITY_AGGREGATE),
    # digest: routine completions / passes
    ("completed", SEVERITY_DIGEST),
    ("complete", SEVERITY_DIGEST),
    ("done", SEVERITY_DIGEST),
    ("closed", SEVERITY_DIGEST),
    ("passed", SEVERITY_DIGEST),
    ("pass", SEVERITY_DIGEST),
)

# Channel recipe kinds we know how to shape payloads for.
CHANNEL_KINDS = ("discord", "telegram", "email")

# Local config file (gitignored, NEVER committed). The owner authors it from the
# shipped ``.example`` template. Secret values (webhook URLs / tokens / SMTP
# creds) live ONLY here.
LOCAL_CONFIG_REL = "agents/project/notifications.local.json"
EXAMPLE_CONFIG_REL = "agents/project/notifications.local.example.json"

# Keys whose VALUES are secret and must never reach served ui_state.
_SECRET_KEYS = frozenset(
    {
        "webhook_url",
        "url",
        "bot_token",
        "token",
        "chat_id",
        "smtp_host",
        "smtp_user",
        "smtp_password",
        "password",
        "api_key",
        "auth",
        "authorization",
    }
)

ROUTING_SCHEMA = "agent-runtime-notification-routing/v1"


def classify_severity(event: Any) -> str:
    """Map a runtime event (dict or event-name string) to a severity window.

    Honors an explicit ``severity`` field on the event if it already names a known
    routing window; otherwise classifies by the event name. Unknown events fall
    back to the digest window (least intrusive), so an unrecognized event can
    never escalate to an immediate external ping.
    """
    name = ""
    explicit = ""
    if isinstance(event, dict):
        explicit = str(event.get("severity") or "").strip().lower()
        name = str(event.get("event") or event.get("type") or event.get("name") or "").strip().lower()
        if event.get("error"):
            return SEVERITY_IMMEDIATE
    else:
        name = str(event or "").strip().lower()
    if explicit in ROUTING_WINDOWS:
        return explicit
    for token, severity in _SEVERITY_RULES:
        if token in name:
            return severity
    return SEVERITY_DIGEST


def routing_window_minutes(severity: str, *, aggregate_minutes: int = DEFAULT_AGGREGATE_WINDOW_MINUTES) -> int:
    """Window length (minutes) a given severity is batched over before delivery."""
    if severity == SEVERITY_IMMEDIATE:
        return 0
    if severity == SEVERITY_AGGREGATE:
        return aggregate_minutes if aggregate_minutes in AGGREGATE_WINDOWS_MINUTES else DEFAULT_AGGREGATE_WINDOW_MINUTES
    return DIGEST_WINDOW_MINUTES


# --- Channel recipes (payload shaping; NO network) ----------------------------


def _event_summary(event: dict[str, Any]) -> dict[str, str]:
    """Extract a small, display-safe summary from a runtime event."""
    name = str(event.get("event") or event.get("type") or event.get("name") or "event")
    task_id = str(event.get("task_id") or event.get("target") or "")
    actor = str(event.get("role") or event.get("actor") or "")
    detail = str(event.get("detail") or event.get("reason") or event.get("message") or "")
    severity = classify_severity(event)
    title_bits = [name]
    if task_id:
        title_bits.append(task_id)
    return {
        "title": " - ".join(title_bits),
        "name": name,
        "task_id": task_id,
        "actor": actor,
        "detail": detail,
        "severity": severity,
    }


def _digest_body(summary: dict[str, str]) -> str:
    lines = [summary["title"]]
    if summary["actor"]:
        lines.append(f"by {summary['actor']}")
    if summary["detail"]:
        lines.append(summary["detail"])
    lines.append(f"severity: {summary['severity']}")
    return "\n".join(lines)


def build_discord_payload(event: dict[str, Any]) -> dict[str, Any]:
    """Shape a Discord webhook JSON payload (``content`` + a single embed).

    Pure payload shaping -- this NEVER sends. The caller (an opted-in local
    runner) supplies the webhook URL out of band.
    """
    summary = _event_summary(event)
    return {
        "content": f"[{summary['severity']}] {summary['title']}",
        "embeds": [
            {
                "title": summary["title"],
                "description": summary["detail"] or summary["name"],
                "fields": [
                    {"name": "Task", "value": summary["task_id"] or "n/a", "inline": True},
                    {"name": "Actor", "value": summary["actor"] or "n/a", "inline": True},
                    {"name": "Severity", "value": summary["severity"], "inline": True},
                ],
            }
        ],
    }


def build_telegram_payload(event: dict[str, Any], *, chat_id: str | None = None) -> dict[str, Any]:
    """Shape a Telegram ``sendMessage`` payload (``text`` + optional chat id).

    ``chat_id`` is a routing target, not a secret payload field; it is only set
    when an opted-in local runner passes it. Default omits it.
    """
    summary = _event_summary(event)
    text_lines = [f"*[{summary['severity']}]* {summary['title']}"]
    if summary["actor"]:
        text_lines.append(f"by {summary['actor']}")
    if summary["detail"]:
        text_lines.append(summary["detail"])
    payload: dict[str, Any] = {
        "text": "\n".join(text_lines),
        "parse_mode": "Markdown",
        "disable_notification": summary["severity"] != SEVERITY_IMMEDIATE,
    }
    if chat_id:
        payload["chat_id"] = str(chat_id)
    return payload


def build_email_payload(event: dict[str, Any], *, to: str | None = None) -> dict[str, Any]:
    """Shape an email message (subject + plain-text body) for an SMTP recipe."""
    summary = _event_summary(event)
    payload: dict[str, Any] = {
        "subject": f"[agent-runtime][{summary['severity']}] {summary['title']}",
        "body": _digest_body(summary),
        "content_type": "text/plain",
    }
    if to:
        payload["to"] = str(to)
    return payload


_RECIPES: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "discord": build_discord_payload,
    "telegram": build_telegram_payload,
    "email": build_email_payload,
}


def build_payload(kind: str, event: dict[str, Any]) -> dict[str, Any]:
    """Dispatch to the channel recipe for ``kind``. Raises on unknown kinds."""
    recipe = _RECIPES.get(str(kind).strip().lower())
    if recipe is None:
        raise ValueError(f"unknown channel kind: {kind!r} (expected {', '.join(CHANNEL_KINDS)})")
    return recipe(event)


# --- Webhook sender (injectable transport; DORMANT by default) ----------------


def null_transport(request: dict[str, Any]) -> dict[str, Any]:
    """The default DORMANT transport: performs no I/O and sends nothing.

    Returns a status record so callers can confirm the sender ran without ever
    touching the network. The real sender only fires when an opted-in local
    runner injects a network transport.
    """
    return {"sent": False, "transport": "null", "reason": "dormant: no transport injected"}


@dataclass
class WebhookSender:
    """Builds a channel payload and hands it to an INJECTED transport.

    The transport is a callable ``(request) -> result``. The default
    (:func:`null_transport`) is a no-op that never touches the network, so a
    plain ``WebhookSender()`` is safe and dormant. Tests pass a fake transport
    that records the request; the real network transport is supplied only by an
    owner-opted-in local runner.
    """

    transport: Callable[[dict[str, Any]], dict[str, Any]] = null_transport
    dry_run: bool = False

    def build_request(self, channel: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
        """Assemble the transport request WITHOUT performing any I/O.

        The destination ``url`` is taken from the channel config at call time (it
        is a secret and is NOT stored on the sender). The returned request is
        what would be sent; tests assert its shape.
        """
        kind = str(channel.get("kind") or "").strip().lower()
        payload = build_payload(kind, event)
        return {
            "kind": kind,
            "channel": str(channel.get("name") or kind),
            "url": channel.get("webhook_url") or channel.get("url") or "",
            "payload": payload,
        }

    def send(self, channel: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
        """Build the request and hand it to the injected transport.

        In ``dry_run`` mode the transport is bypassed entirely (nothing leaves
        this process) and the built request is returned for inspection.
        """
        request = self.build_request(channel, event)
        if self.dry_run:
            return {"sent": False, "transport": "dry_run", "request": request}
        result = self.transport(request)
        outcome = {"request": request}
        outcome.update(result if isinstance(result, dict) else {"result": result})
        return outcome


# --- Aggregation-window batching ---------------------------------------------


@dataclass
class AggregationBuffer:
    """Buckets events by routing window so non-urgent events are batched.

    - immediate events are returned to flush right away (never buffered).
    - aggregate events accumulate until ``flush_due`` for the aggregate window.
    - digest events accumulate until the daily digest window.

    Time is supplied by the caller (epoch minutes) so this stays pure/testable
    with no wall-clock dependency.
    """

    aggregate_minutes: int = DEFAULT_AGGREGATE_WINDOW_MINUTES
    pending: dict[str, list[dict[str, Any]]] = field(default_factory=lambda: {SEVERITY_AGGREGATE: [], SEVERITY_DIGEST: []})
    last_flush: dict[str, float] = field(default_factory=lambda: {SEVERITY_AGGREGATE: 0.0, SEVERITY_DIGEST: 0.0})

    def add(self, event: dict[str, Any]) -> dict[str, Any]:
        """Record an event. Returns a routing decision for the caller.

        ``{"severity", "immediate": bool}``. Immediate events should be flushed
        at once; aggregate/digest events are held until their window elapses.
        """
        severity = classify_severity(event)
        if severity == SEVERITY_IMMEDIATE:
            return {"severity": severity, "immediate": True, "buffered": False}
        self.pending.setdefault(severity, []).append(event)
        return {"severity": severity, "immediate": False, "buffered": True}

    def flush_due(self, severity: str, now_minutes: float) -> list[dict[str, Any]]:
        """Return + clear buffered events for ``severity`` if its window elapsed.

        Returns an empty list (and keeps the buffer) when the window has not yet
        elapsed, so a caller polling on a tick never double-sends.
        """
        if severity not in self.pending:
            return []
        window = routing_window_minutes(severity, aggregate_minutes=self.aggregate_minutes)
        if now_minutes - self.last_flush.get(severity, 0.0) < window:
            return []
        batch = self.pending.get(severity, [])
        if not batch:
            self.last_flush[severity] = now_minutes
            return []
        self.pending[severity] = []
        self.last_flush[severity] = now_minutes
        return batch

    def pending_counts(self) -> dict[str, int]:
        """How many events are buffered per window (for status display)."""
        return {severity: len(items) for severity, items in self.pending.items()}


# --- Local config (secrets) + secret-free status ------------------------------


def load_local_config(root: Path | str) -> dict[str, Any]:
    """Load the LOCAL (gitignored) notification config, or an empty default.

    Returns the raw config INCLUDING secret values -- only an opted-in local
    runner should call this. ui_state must call :func:`routing_status` instead,
    which strips secrets. When the file is absent the routing is DORMANT (no
    channels), which is the safe default.
    """
    path = Path(root) / LOCAL_CONFIG_REL
    if not path.exists():
        return {"schema": ROUTING_SCHEMA, "channels": [], "present": False}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema": ROUTING_SCHEMA, "channels": [], "present": False, "invalid": True}
    if not isinstance(raw, dict):
        return {"schema": ROUTING_SCHEMA, "channels": [], "present": False, "invalid": True}
    channels = raw.get("channels") if isinstance(raw.get("channels"), list) else []
    raw["channels"] = [channel for channel in channels if isinstance(channel, dict)]
    raw.setdefault("schema", ROUTING_SCHEMA)
    raw["present"] = True
    return raw


def _strip_secrets(channel: dict[str, Any]) -> dict[str, Any]:
    """Project a channel down to SECRET-FREE display fields.

    Only the channel name, recipe kind, enabled flag, severities it subscribes
    to, and the aggregate window survive. Every secret value (URL/token/chat
    id/SMTP creds) is dropped and replaced with a boolean ``configured`` flag so
    the UI can show "secret present" without ever serving the secret itself.
    """
    kind = str(channel.get("kind") or "").strip().lower()
    severities = channel.get("severities")
    if not isinstance(severities, list):
        severities = list(ROUTING_WINDOWS)
    severities = [s for s in severities if s in ROUTING_WINDOWS] or list(ROUTING_WINDOWS)
    configured = any(
        str(channel.get(key) or "").strip()
        for key in _SECRET_KEYS
    )
    aggregate_minutes = channel.get("aggregate_minutes")
    if aggregate_minutes not in AGGREGATE_WINDOWS_MINUTES:
        aggregate_minutes = DEFAULT_AGGREGATE_WINDOW_MINUTES
    return {
        "name": str(channel.get("name") or kind or "channel"),
        "kind": kind if kind in CHANNEL_KINDS else "unknown",
        "enabled": bool(channel.get("enabled", False)),
        "severities": severities,
        "aggregate_minutes": aggregate_minutes,
        "configured": configured,
    }


def routing_status(root: Path | str, now: str | None = None) -> dict[str, Any]:
    """SECRET-FREE routing status for ui_state / the console.

    NEVER returns webhook URLs, tokens, chat ids, or SMTP creds -- only channel
    name, recipe kind, enabled flag, subscribed severities, and a ``configured``
    boolean. Safe to serialize into served state. When no local config is
    present the routing is reported DORMANT (no channels, nothing sends).
    """
    config = load_local_config(root)
    channels = [_strip_secrets(channel) for channel in config.get("channels", [])]
    enabled = [channel for channel in channels if channel["enabled"] and channel["configured"]]
    return {
        "schema": ROUTING_SCHEMA,
        "generated_at": now,
        "source_path": LOCAL_CONFIG_REL,
        "example_path": EXAMPLE_CONFIG_REL,
        "config_present": bool(config.get("present")),
        "dormant": len(enabled) == 0,
        "channel_kinds": list(CHANNEL_KINDS),
        "routing_windows": list(ROUTING_WINDOWS),
        "aggregate_windows_minutes": list(AGGREGATE_WINDOWS_MINUTES),
        "channels": channels,
        "totals": {
            "channels": len(channels),
            "enabled": len(enabled),
            "configured": sum(1 for channel in channels if channel["configured"]),
        },
        "severity_routing": {
            SEVERITY_IMMEDIATE: "block / approval-pending: delivered immediately",
            SEVERITY_AGGREGATE: f"watch: batched over a {DEFAULT_AGGREGATE_WINDOW_MINUTES}/15-min window",
            SEVERITY_DIGEST: "pass / completed: rolled into a daily digest",
        },
        "note": (
            "External routing is DORMANT until the owner authors the local config"
            " (gitignored) and an opt-in local runner injects a network transport."
            " The console only does proposal-only subscription CRUD; it never sends."
        ),
    }
