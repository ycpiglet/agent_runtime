"""Optional, dependency-free allimbot notification client.

Delivery is deliberately best-effort: missing configuration is a silent no-op,
all exceptions are swallowed, and every network attempt is capped at three
seconds. The local allimbot dashboard is tried before the ntfy fallback.
"""
from __future__ import annotations

import argparse
import functools
import json
import os
import time
import urllib.request
from collections.abc import Callable
from typing import Any

DEFAULT_TIMEOUT = 3.0
DEFAULT_URL = "http://127.0.0.1:8787"
__all__ = ["notify", "notify_on_complete"]


def _bounded_timeout(timeout: float) -> float:
    try:
        return min(DEFAULT_TIMEOUT, max(0.1, float(timeout)))
    except (TypeError, ValueError):
        return DEFAULT_TIMEOUT


def _post_json(url: str, payload: dict[str, str], timeout: float) -> bool:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    with urllib.request.urlopen(request, timeout=_bounded_timeout(timeout)) as response:  # noqa: S310
        return 200 <= response.status < 300


def notify(
    message: str,
    title: str = "agent_runtime",
    provider: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> bool:
    """Send one best-effort notification; never raise or print."""
    try:
        resolved_provider = provider or os.environ.get("ALLIMBOT_PROVIDER", "")
        token = os.environ.get("ALLIMBOT_TOKEN", "")
        topic = os.environ.get("ALLIMBOT_NTFY_TOPIC", "")
        if not token and not topic:
            return False

        if token:
            base = os.environ.get("ALLIMBOT_URL", DEFAULT_URL).rstrip("/")
            try:
                if _post_json(
                    base + "/trigger",
                    {
                        "token": token,
                        "message": str(message),
                        "title": str(title),
                        "provider": resolved_provider,
                    },
                    timeout,
                ):
                    return True
            except Exception:
                pass

        if topic:
            try:
                return _post_json(
                    "https://ntfy.sh",
                    {"topic": topic, "title": str(title), "message": str(message)},
                    timeout,
                )
            except Exception:
                pass
    except Exception:
        pass
    return False


def notify_on_complete(title: str | None = None, provider: str | None = None) -> Callable:
    """Decorate a function with best-effort success/failure notifications."""

    def decorator(function: Callable) -> Callable:
        @functools.wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            started = time.monotonic()
            try:
                result = function(*args, **kwargs)
            except Exception as exc:
                elapsed = time.monotonic() - started
                notify(
                    f"{function.__name__} failed ({elapsed:.0f}s): {exc}",
                    title=title or "agent_runtime task failed",
                    provider=provider,
                )
                raise
            elapsed = time.monotonic() - started
            notify(
                f"{function.__name__} completed ({elapsed:.0f}s)",
                title=title or "agent_runtime task completed",
                provider=provider,
            )
            return result

        return wrapper

    return decorator


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Send an optional allimbot notification")
    parser.add_argument("message")
    parser.add_argument("-t", "--title", default="agent_runtime")
    parser.add_argument("-p", "--provider", default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)
    delivered = notify(args.message, title=args.title, provider=args.provider)
    if args.verbose:
        print("notification delivered" if delivered else "notification not delivered")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
