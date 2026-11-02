"""Deterministic, offline compact owner reports from explicit source facts.

Run ``python -m agent_runtime.owner_brief input.json [-o report.md]``.
Input that cannot fit is rejected, never truncated or silently omitted.
"""

from __future__ import annotations

import argparse
import json
import string
import sys
import unicodedata
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit


STATE_LABELS = {
    "done": "완료",
    "in_progress": "진행 중",
    "blocked": "차단",
    "unknown": "미확인",
    "not_run": "미실행",
}
SIGNAL_RANK = {"pass": 0, "watch": 1, "block": 2}
MAX_FIRST_LAYER = 1200


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name}: nonempty text required")
    if value != value.strip():
        raise ValueError(f"{name}: leading or trailing whitespace is not allowed")
    if any(unicodedata.category(char).startswith("C") or char in "\u2028\u2029" for char in value):
        raise ValueError(f"{name}: control characters or multiple lines are not allowed")
    return value


def escape_markdown(value: str) -> str:
    """Render caller text literally, including HTML and Markdown controls."""
    entities = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}
    return "".join(entities.get(char, "\\" + char if char in string.punctuation else char) for char in value)


def safe_href(value: object) -> str:
    """Allow HTTP(S) and local paths, without active schemes or credentials."""
    href = _text(value, "evidence.href")
    decoded = unquote(href)
    if (
        href != href.strip()
        or "\\" in href
        or any(unicodedata.category(char).startswith("C") for char in decoded)
    ):
        raise ValueError("evidence.href: unsafe path or URL")
    try:
        parsed = urlsplit(href)
        if parsed.scheme:
            if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
                raise ValueError("unsupported URL scheme or missing host")
            if parsed.username is not None or parsed.password is not None:
                raise ValueError("userinfo is not allowed")
            parsed.port  # Reject malformed ports as well as malformed authorities.
        elif parsed.netloc or href.startswith("//"):
            raise ValueError("network-relative URLs are not local paths")
    except ValueError as exc:
        raise ValueError(f"evidence.href: {exc}") from exc
    # Parentheses, angle brackets, quotes and whitespace cannot escape the
    # Markdown destination. Existing percent escapes remain intact.
    return quote(href, safe=":/?#@!$&=+,%~-._")


def _items(value: object, name: str, maximum: int | None = None, minimum: int = 0) -> list:
    if not isinstance(value, list):
        raise ValueError(f"{name}: list required")
    if len(value) < minimum or (maximum is not None and len(value) > maximum):
        raise ValueError(f"{name}: requires {minimum}..{maximum} items; no items were dropped")
    return value


def _fields(value: object, name: str, allowed: set[str]) -> Mapping:
    if not isinstance(value, Mapping) or set(value) - allowed:
        raise ValueError(f"{name}: object with supported fields required")
    return value


def render_owner_brief(source: Mapping[str, object]) -> str:
    """Validate and render compact-v1; source statements remain caller-owned.

    Required: title, summary, statuses, next_actions, limits, evidence.
    Optional: signal (may only increase severity), score + score_source.
    An empty next_actions/evidence list explicitly records no provided items.
    A score is never inferred from state or generated as a confidence estimate.
    """
    source = _fields(source, "report", {
        "title", "summary", "statuses", "next_actions", "limits", "evidence",
        "signal", "score", "score_source",
    })
    title = escape_markdown(_text(source.get("title"), "title"))
    summary = escape_markdown(_text(source.get("summary"), "summary"))
    if len(title) > 70 or len(summary) > 140:
        raise ValueError("title/summary: maximum 70/140 Markdown characters; no text was truncated")

    statuses = []
    state_values = []
    for item in _items(source.get("statuses"), "statuses", 3, 1):
        item = _fields(item, "status", {"label", "state", "detail"})
        state = item.get("state")
        if not isinstance(state, str) or state not in STATE_LABELS:
            raise ValueError("status.state: expected done/in_progress/blocked/unknown/not_run")
        label = escape_markdown(_text(item.get("label"), "status.label"))
        detail = escape_markdown(_text(item.get("detail"), "status.detail"))
        statuses.append(f"- **{STATE_LABELS[state]}** · {label}: {detail}")
        state_values.append(state)

    actions = [escape_markdown(_text(item, "next_action")) for item in _items(source.get("next_actions"), "next_actions", 2)]
    limits = [escape_markdown(_text(item, "limit")) for item in _items(source.get("limits"), "limits", 3, 1)]
    inferred = "block" if "blocked" in state_values else ("watch" if any(state != "done" for state in state_values) else "pass")
    signal = source.get("signal", inferred)
    if not isinstance(signal, str) or signal not in SIGNAL_RANK:
        raise ValueError("signal: expected pass/watch/block")
    signal = max((signal, inferred), key=SIGNAL_RANK.__getitem__)
    metadata = ["---", "report_layout: compact-v1", f"signal: {signal}"]
    if "score" in source:
        score = source["score"]
        if type(score) is not int or not 0 <= score <= 100:
            raise ValueError("score: integer 0..100 required")
        score_source = _text(source.get("score_source"), "score_source")
        metadata.extend((f"score: {score}", f"score_source: {json.dumps(score_source, ensure_ascii=False)}"))
    elif "score_source" in source:
        raise ValueError("score_source: requires an explicit source score")
    metadata.append("---")

    first_layer = "\n".join([
        f"# {title}", "", f"> **{summary}**", "", "## 현재 상태", "",
        *statuses, "", "## 다음 행동", "",
        *[f"- {action}" for action in (actions or ["추가 행동 없음"])], "",
        "## 한도와 미확인", "", *[f"- {limit}" for limit in limits], "",
    ])
    if len(first_layer.strip("\r\n")) > MAX_FIRST_LAYER:
        raise ValueError("first_layer: maximum 1200 Markdown characters; no facts were dropped")

    evidence = []
    for item in _items(source.get("evidence"), "evidence"):
        item = _fields(item, "evidence", {"label", "href", "detail"})
        label = escape_markdown(_text(item.get("label"), "evidence.label"))
        line = f"- [{label}]({safe_href(item.get('href'))})"
        if "detail" in item:
            line += ": " + escape_markdown(_text(item["detail"], "evidence.detail"))
        evidence.append(line)
    return "\n".join(metadata) + "\n\n" + first_layer + "\n## 검증 근거\n\n" + "\n".join(evidence or ["- 제공된 근거 없음"]) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render an offline compact owner report from JSON")
    parser.add_argument("input", nargs="?", default="-", help="JSON file, or - for stdin")
    parser.add_argument("-o", "--output", type=Path, help="Write Markdown locally (default: stdout)")
    args = parser.parse_args(argv)
    try:
        raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
        output = render_owner_brief(json.loads(raw))
        if args.output:
            args.output.write_text(output, encoding="utf-8")
        else:
            sys.stdout.write(output)
    except (ValueError, OSError) as exc:
        print(f"owner-brief: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
