#!/usr/bin/env python3
"""Live verification helper for ClaudeProvider sdk backend (TASK-102 인수사항 / #7).

The sdk backend was only mocked in TASK-102. This runs a real single-shot call so
the success path (content extraction, token usage, finish_reason) is verified once
a valid key is present.

Usage:
  1. Put your Anthropic API key in .env or the environment (gitignored — never commit).
  2. python scripts/verify_sdk_backend.py

Reads .env via python-dotenv, forces CLAUDE_PROVIDER_BACKEND=sdk, calls run() with a
tiny prompt, and prints the ProviderResult. Exit 0 on a real reply, 1 otherwise.
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:
    pass  # dotenv optional; env may already be set

os.environ["CLAUDE_PROVIDER_BACKEND"] = "sdk"

from providers import get_provider  # noqa: E402
from providers.base import ProviderAuthError, ProviderError, ProviderResult  # noqa: E402
import eval_harness  # noqa: E402
import model_routing  # noqa: E402


def _dispatch_ceiling(provider) -> int | None:
    for attr in ("per_dispatch_cap", "tokens_per_call"):
        try:
            value = int(getattr(provider, attr, 0) or 0)
        except (TypeError, ValueError):
            continue
        if value > 0:
            return value
    return None


def _record(
    *,
    dispatch_id: str,
    claim_id: str | None,
    route: dict,
    preflight: dict,
    status: str,
    finish_reason: str | None,
    result=None,
    error: str | None = None,
) -> None:
    eval_harness.record_execution_receipt(
        dispatch_id=dispatch_id,
        task_id="verify-sdk",
        claim_id=claim_id,
        role="qa",
        provider=route.get("provider"),
        execution_surface="provider_worker",
        requested_tier=route.get("requested_tier"),
        selected_tier=route.get("selected_tier"),
        resolved_model=route.get("resolved_model"),
        resolved_reasoning_effort=route.get("reasoning_effort"),
        resolved_model_source=route.get("model_source"),
        resolved_reasoning_source=route.get("reasoning_source"),
        observed_provider=getattr(result, "provider", None) if result else None,
        observed_model=getattr(result, "model", None) if result else None,
        observed_reasoning_effort=(
            getattr(result, "reasoning_effort", None) if result else None
        ),
        tokens_in=getattr(result, "tokens_in", None) if result else None,
        tokens_out=getattr(result, "tokens_out", None) if result else None,
        billed_cost=getattr(result, "billed_cost", None) if result else None,
        currency=getattr(result, "currency", None) if result else None,
        source="verify_sdk_backend",
        status=status,
        finish_reason=finish_reason,
        error=error,
        route_status=route.get("route_status"),
        application_status=route.get("application_status"),
        model_changed=route.get("model_changed"),
        route_changed=route.get("route_changed"),
        budget_preflight_result=preflight,
        path=eval_harness.EVAL_LOG,
    )


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("BLOCKED: ANTHROPIC_API_KEY not set. Add it to .env (gitignored) "
              "or the environment, then re-run.")
        return 1

    provider = get_provider("claude")
    tier = model_routing.resolve_subagent_tier("qa")
    route = model_routing.resolve_provider_route(
        "claude-agent",
        tier["selected_tier"],
        requested_tier=tier["requested_tier"],
    )
    for name, value in dict(route.get("provider_env") or {}).items():
        os.environ[name] = value
    if route.get("resolved_model") and hasattr(provider, "model"):
        provider.model = route["resolved_model"]
    print(f"backend={provider.backend} model={provider.model}")
    prompt_role, instruction = "qa", "Reply with exactly: OK"
    dispatch_id = f"verify-sdk-{uuid.uuid4().hex}"
    claim_id = str(os.environ.get("AGENT_RUNTIME_CLAIM_ID") or "").strip() or None
    try:
        preflight = eval_harness.reserve_dispatch_budget(
            path=eval_harness.EVAL_LOG,
            root=ROOT,
            task_id="verify-sdk",
            claim_id=claim_id,
            dispatch_id=dispatch_id,
            dispatch_ceiling=_dispatch_ceiling(provider),
            source="verify_sdk_backend",
        )
    except eval_harness.ReceiptIntegrityError as exc:
        print(f"BLOCKED: receipt ledger or budget authority is untrusted: {exc}")
        return 1
    if not preflight["allowed"]:
        _record(
            dispatch_id=dispatch_id,
            claim_id=claim_id,
            route=route,
            preflight=preflight,
            status="skipped",
            finish_reason="skipped",
            error=str(preflight["reason"]),
        )
        print(f"BLOCKED: {preflight['reason']}")
        return 1
    try:
        eval_harness.record_provider_call_start(
            dispatch_id=dispatch_id,
            task_id="verify-sdk",
            source="verify_sdk_provider_run",
            provider=str(route.get("provider") or ""),
            execution_surface="provider_worker",
            path=eval_harness.EVAL_LOG,
            root=ROOT,
        )
        result: ProviderResult = provider.run(
            prompt_role,
            instruction,
            {
                "task_id": "verify-sdk",
                "claim_id": claim_id,
                "dispatch_id": dispatch_id,
                "budget_preflight": preflight,
                "routing": tier,
                "provider_route": route,
            },
        )
    except ProviderAuthError as exc:
        _record(
            dispatch_id=dispatch_id,
            claim_id=claim_id,
            route=route,
            preflight=preflight,
            status="error",
            finish_reason="error",
            error=f"{type(exc).__name__}: {exc}",
        )
        print(f"AUTH FAIL: {exc}")
        return 1
    except ProviderError as exc:
        _record(
            dispatch_id=dispatch_id,
            claim_id=claim_id,
            route=route,
            preflight=preflight,
            status="error",
            finish_reason="error",
            error=f"{type(exc).__name__}: {exc}",
        )
        print(f"PROVIDER ERROR: {exc}")
        return 1
    except Exception as exc:
        _record(
            dispatch_id=dispatch_id,
            claim_id=claim_id,
            route=route,
            preflight=preflight,
            status="error",
            finish_reason="error",
            error=f"{type(exc).__name__}: {exc}",
        )
        print(f"UNEXPECTED PROVIDER ERROR: {exc}")
        return 1

    _record(
        dispatch_id=dispatch_id,
        claim_id=claim_id,
        route=route,
        preflight=preflight,
        status="completed" if not getattr(result, "error", None) else "error",
        finish_reason=getattr(result, "finish_reason", None),
        result=result,
        error=str(getattr(result, "error", None) or "").strip() or None,
    )

    print("--- live ProviderResult ---")
    print(f"text          : {result.text!r}")
    print(f"tokens_in     : {result.tokens_in}")
    print(f"tokens_out    : {result.tokens_out}")
    print(f"finish_reason : {result.finish_reason}")
    ok = bool(result.text) and result.tokens_out > 0
    print(f"\n{'PASS' if ok else 'INCOMPLETE'}: sdk backend "
          f"{'returned a real reply with usage' if ok else 'reply/usage missing'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
