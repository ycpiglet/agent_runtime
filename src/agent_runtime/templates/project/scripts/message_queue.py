"""Message claim/ownership queue for worker claim safety.

The module is intentionally small and dependency-free so both workers and
offline runners can rely on the same semantics:

- atomic lease file created before mutating inbox message
- stale lease recovery (with safety checks)
- owner-scoped mark-as-answered to avoid duplicate replies
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import time
import uuid
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
MESSAGES_INBOX = REPO_ROOT / "agents" / "messages" / "inbox"
RUNTIME_DIR = REPO_ROOT / "agents" / "runtime"
CLAIMS_DIR = RUNTIME_DIR / "claims"
CLAIM_TTL_SECONDS = 30 * 60
MAX_CLAIM_CREATE_ATTEMPTS = 4
CLAIM_CREATE_RETRY_DELAY_SECONDS = 0.01
CLAIM_LOCK_STALE_SECONDS = 30.0


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_window_range(window_value: object) -> tuple[str, str]:
    if not isinstance(window_value, str):
        return "", ""
    split_parts = window_value.split("/")
    if len(split_parts) != 2:
        return "", ""
    start, end = split_parts[0].strip(), split_parts[1].strip()
    if not start or not end:
        return "", ""
    return start, end


def _build_pass39_warning_summary_record(
    warning_code_counts: dict[str, int],
    *,
    total_warnings: int,
    run_id: str,
    event_name: str,
    window_start: str,
    window_end: str,
    schema_version: str = "pass39-warning-summary-v1",
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "warning_code_counts": warning_code_counts,
        "total_warnings": total_warnings,
        "run_id": run_id,
        "event_name": event_name,
        "window_start": window_start,
        "window_end": window_end,
    }


def _evaluate_warning_summary_policy(
    records: list[dict[str, object]],
    *,
    max_warnings_per_context: int,
    code_warning_limits: dict[str, int] | None = None,
) -> tuple[bool, list[str]]:
    if code_warning_limits is None:
        code_warning_limits = {}
    reasons: list[str] = []
    for record in records:
        run_id = str(record.get("run_id", "unknown"))
        event_name = str(record.get("event_name", "unknown"))
        warning_count = _safe_int(record.get("total_warnings", 0))
        warning_code_counts = dict(record.get("warning_code_counts", {}))
        if warning_count > max_warnings_per_context:
            reasons.append(
                f"context(run_id={run_id}, event={event_name}) has "
                f"{warning_count} warnings (max {max_warnings_per_context})"
            )
        for code, limit in code_warning_limits.items():
            current = _safe_int(warning_code_counts.get(code, 0))
            if current > int(limit):
                reasons.append(
                    f"context(run_id={run_id}, event={event_name}) "
                    f"code={code} has {current} warnings (max {int(limit)})"
                )
    return len(reasons) == 0, reasons


def _coalesce_warning_summary_records(
    records: list[dict[str, object]]
) -> list[dict[str, object]]:
    coalesced: dict[tuple[str, str, str, str], dict[str, object]] = {}
    for record in records:
        schema_version = str(record.get("schema_version", "pass39-warning-summary-v1"))
        run_id = str(record.get("run_id", record.get("run", "legacy")))
        event_name = str(record.get("event_name", record.get("event", "legacy")))
        window_start = record.get("window_start", record.get("ts_window_start"))
        window_end = record.get("window_end", record.get("window_end_time"))
        if (window_start in (None, "")) and (window_end in (None, "")):
            window_start, window_end = _parse_window_range(record.get("window"))
        window_start = str(window_start if window_start not in (None, "") else "")
        window_end = str(window_end if window_end not in (None, "") else "")
        key = (run_id, event_name, window_start, window_end)
        if key not in coalesced:
            coalesced[key] = {
                "run_id": run_id,
                "event_name": event_name,
                "window_start": window_start,
                "window_end": window_end,
                "schema_version": schema_version,
                "warning_code_counts": dict(record.get("warning_code_counts", {})),
                "total_warnings": _safe_int(record.get("total_warnings", 0), 0),
            }
            continue

        existing = coalesced[key]
        existing_counts = dict(existing.get("warning_code_counts", {}))
        for code, count in dict(record.get("warning_code_counts", {})).items():
            existing_counts[code] = max(
                _safe_int(existing_counts.get(code, 0), 0),
                _safe_int(count, 0),
            )
        existing["warning_code_counts"] = existing_counts
        existing["total_warnings"] = max(
            _safe_int(existing.get("total_warnings", 0), 0),
            _safe_int(record.get("total_warnings", 0), 0),
        )

        if schema_version != existing["schema_version"]:
            existing_schema_version = str(existing["schema_version"])
            if (
                "legacy" in schema_version
                or "legacy" in existing_schema_version
                or schema_version.endswith("-v0")
                or existing_schema_version.endswith("-v0")
            ):
                existing["schema_version"] = "pass39-warning-summary-legacy"
            else:
                existing["schema_version"] = schema_version

    return list(coalesced.values())


def _append_jsonl_record(path: str, payload: object) -> None:
    output_path = Path(path)
    if not output_path.is_absolute():
        github_workspace = os.getenv("GITHUB_WORKSPACE", "").strip()
        if github_workspace:
            output_path = Path(github_workspace) / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _load_warning_summary_records(path: str) -> list[dict[str, object]]:
    output_path = Path(path)
    if not output_path.is_absolute():
        github_workspace = os.getenv("GITHUB_WORKSPACE", "").strip()
        if github_workspace:
            output_path = Path(github_workspace) / output_path
    if not output_path.exists():
        return []
    if output_path.suffix.lower() == ".jsonl":
        records: list[dict[str, object]] = []
        for raw in output_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line:
                continue
            records.append(json.loads(line))
        return records

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    return [payload] if isinstance(payload, dict) else []


def _parse_warning_code_spec(raw: str) -> tuple[str, int]:
    code, _, count = raw.partition("=")
    if not code or not count:
        raise ValueError("warning specification must be CODE=COUNT")
    return code, int(count)


def _parse_warning_code_threshold_specs(
    specs: list[str],
) -> dict[str, int]:
    thresholds: dict[str, int] = {}
    for raw in specs:
        code, limit = _parse_warning_code_spec(raw)
        thresholds[code] = max(thresholds.get(code, 0), limit)
    return thresholds


def _run_warning_summary_gate(
    *,
    summary_path: str,
    run_id: str,
    event_name: str,
    window_start: str,
    window_end: str,
    warning_codes: list[str],
    max_warnings_per_context: int,
    code_warning_limits: list[str],
    report_path: str,
    dry_run: bool = False,
    schema_version: str = "pass39-warning-summary-v1",
) -> dict[str, object]:
    warning_code_counts: dict[str, int] = {}
    for raw in warning_codes:
        code, count = _parse_warning_code_spec(raw)
        warning_code_counts[code] = max(warning_code_counts.get(code, 0), count)

    total_warnings = sum(_safe_int(value) for value in warning_code_counts.values())
    record = _build_pass39_warning_summary_record(
        warning_code_counts,
        total_warnings=total_warnings,
        run_id=run_id,
        event_name=event_name,
        window_start=window_start,
        window_end=window_end,
        schema_version=schema_version,
    )
    _append_jsonl_record(summary_path, record)

    records = _coalesce_warning_summary_records(_load_warning_summary_records(summary_path))
    parsed_code_limits = _parse_warning_code_threshold_specs(code_warning_limits)
    policy_passed, reasons = _evaluate_warning_summary_policy(
        records,
        max_warnings_per_context=max_warnings_per_context,
        code_warning_limits=parsed_code_limits,
    )
    report = {
        "path": summary_path,
        "record_count": len(records),
        "records": records,
        "max_warnings_per_context": max_warnings_per_context,
        "code_warning_limits": parsed_code_limits,
        "dry_run": dry_run,
        "policy_passed": policy_passed,
        "reasons": reasons,
    }
    if report_path:
        _append_jsonl_record(str(report_path), report)
    return report


def _main_warning_summary_gate(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Message queue warning summary gate")
    parser.add_argument("command", nargs="?", default="")
    parser.add_argument("--summary-path", required=True, help="Path to JSONL warning summary artifact")
    parser.add_argument("--run-id", required=True, help="run_id context")
    parser.add_argument("--event-name", required=True, help="event_name context")
    parser.add_argument("--window-start", required=True, help="window_start context")
    parser.add_argument("--window-end", required=True, help="window_end context")
    parser.add_argument(
        "--warning",
        action="append",
        default=[],
        metavar="CODE=COUNT",
        help="warning code and count pair",
    )
    parser.add_argument(
        "--schema-version",
        default="pass39-warning-summary-v1",
        help="warning summary schema version",
    )
    parser.add_argument(
        "--max-warnings-per-context",
        type=int,
        default=0,
        help="policy threshold for max total warnings in a context",
    )
    parser.add_argument(
        "--code-threshold",
        action="append",
        default=[],
        metavar="CODE=COUNT",
        help="per-code warning threshold",
    )
    parser.add_argument(
        "--report-path",
        default="",
        help="optional path to append JSON report",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="evaluate policy and write report without failing execution",
    )
    args = parser.parse_args(argv)
    if args.command != "warning-summary-gate":
        parser.error("expected command: warning-summary-gate")

    try:
        report = _run_warning_summary_gate(
            summary_path=args.summary_path,
            run_id=args.run_id,
            event_name=args.event_name,
            window_start=args.window_start,
            window_end=args.window_end,
            warning_codes=args.warning,
            max_warnings_per_context=args.max_warnings_per_context,
            code_warning_limits=args.code_threshold,
            report_path=args.report_path,
            dry_run=args.dry_run,
            schema_version=args.schema_version,
        )
    except Exception as exc:
        print(f"PASS-76 warning summary gate failed: {exc}")
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.dry_run:
        return 0
    return 0 if report["policy_passed"] else 1


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] in {"warning-summary-gate", "--help", "-h"}:
        return _main_warning_summary_gate(argv)
    if argv:
        return _main_warning_summary_gate(argv)
    return 0


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter dict, body str)."""
    if not text.startswith("---"):
        return {}, ""
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, ""
    meta: dict[str, object] = {}
    current_list_key: str | None = None
    for raw in parts[1].splitlines():
        line = raw.rstrip()
        if not line:
            current_list_key = None
            continue
        if line.startswith("  - ") and current_list_key:
            existing = meta.setdefault(current_list_key, [])
            if isinstance(existing, list):
                existing.append(line[4:].strip())
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value == "":
            meta[key] = []
            current_list_key = key
        else:
            meta[key] = value
            current_list_key = None
    body = parts[2].lstrip("\n")
    return meta, body


def serialize_frontmatter(meta: dict, body: str) -> str:
    """Round-trip frontmatter in a stable order."""
    keys_in_order = ["id", "from", "to", "task_id", "intent", "type",
                     "status", "ts", "in_reply_to", "evidence", "next"]
    lines = ["---"]
    for k in keys_in_order:
        if k not in meta:
            continue
        v = meta[k]
        if isinstance(v, list):
            if not v:
                lines.append(f"{k}: []")
            else:
                lines.append(f"{k}:")
                for item in v:
                    lines.append(f"  - {item}")
        else:
            if v == "" or v is None:
                lines.append(f"{k}:")
            else:
                lines.append(f"{k}: {v}")
    for k, v in meta.items():
        if k in keys_in_order:
            continue
        if isinstance(v, list):
            if not v:
                lines.append(f"{k}: []")
            else:
                lines.append(f"{k}:")
                for item in v:
                    lines.append(f"  - {item}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines) + body


def _now_epoch() -> float:
    return time.time()


def _msg_id_from_path(path: Path, meta: dict) -> str:
    if isinstance(meta.get("id"), str) and meta["id"].strip():
        return str(meta["id"]).strip()
    stem = path.stem
    if stem.startswith("MSG-"):
        return stem
    return f"MSG-{uuid.uuid4().hex[:14]}"


def _claim_path(message_id: str) -> Path:
    return CLAIMS_DIR / f"{message_id}.claim"


def _claim_lock_path(message_id: str) -> Path:
    return CLAIMS_DIR / f"{message_id}.claim.lock"


def _acquire_claim_file_lock(lock_path: Path) -> bool:
    for attempt in range(MAX_CLAIM_CREATE_ATTEMPTS * 10):
        try:
            lock_path.mkdir()
            return True
        except FileExistsError:
            try:
                age = _now_epoch() - lock_path.stat().st_mtime
                if age > CLAIM_LOCK_STALE_SECONDS:
                    lock_path.rmdir()
                    continue
            except FileNotFoundError:
                continue
            except Exception:
                pass
            if attempt == (MAX_CLAIM_CREATE_ATTEMPTS * 10) - 1:
                return False
            time.sleep(CLAIM_CREATE_RETRY_DELAY_SECONDS)
    return False


def _release_claim_file_lock(lock_path: Path) -> None:
    try:
        lock_path.rmdir()
    except Exception:
        pass


def _worker_identity(role: str | None = None, *, pid: int | None = None,
                    hostname: str | None = None) -> dict[str, object]:
    return {
        "role": (role or "unknown").strip() or "unknown",
        "pid": pid if pid is not None else os.getpid(),
        "hostname": hostname or socket.gethostname(),
    }


def _identity_token(identity: dict[str, object] | None) -> str | None:
    if not isinstance(identity, dict):
        return None
    token = identity.get("token")
    if token is None:
        token = identity.get("claim_token")
    if token is None:
        return None
    return str(token)


def _claim_owner_matches(claim: dict, *, role: str | None, identity: dict | None) -> bool:
    if not isinstance(claim, dict):
        return False
    if role:
        expected_role = claim.get("role")
        if expected_role is not None and str(expected_role) != role:
            return False
    claim_token = claim.get("token")
    if claim_token is not None:
        expected = _identity_token(identity)
        if expected is not None and str(claim_token) != expected:
            return False
    if identity is None:
        return True
    for field in ("pid", "hostname"):
        expected = claim.get(field)
        actual = identity.get(field)
        if expected is None or actual is None:
            continue
        try:
            if field == "pid":
                if int(expected) != int(actual):
                    return False
            else:
                if str(expected) != str(actual):
                    return False
        except Exception:
            if str(expected) != str(actual):
                return False
    return True


def _write_json_atomic(path: Path, payload: dict) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload_text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    return _write_text_atomic(path, payload_text)


def _read_claim(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            return raw
    except Exception:
        # Keep malformed payloads recoverable by allowing one retry path before
        # treating them as stale.
        return {}
    return None


def _write_text_atomic(
    path: Path,
    text: str,
    *,
    attempts: int = MAX_CLAIM_CREATE_ATTEMPTS,
    delay_seconds: float = CLAIM_CREATE_RETRY_DELAY_SECONDS,
) -> bool:
    attempts = int(attempts) if attempts else 1
    if attempts < 1:
        attempts = 1
    delay = float(delay_seconds)
    if delay < 0:
        delay = 0.0

    for attempt in range(attempts):
        tmp = path.with_suffix(path.suffix + f".tmp.{uuid.uuid4().hex[:8]}")
        try:
            tmp.write_text(text, encoding="utf-8")
            os.replace(tmp, path)
            return True
        except Exception:
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass
            if attempt == attempts - 1:
                return False
            time.sleep(delay)
    return False


def _is_stale_claim(claim: dict, now: float | None = None) -> bool:
    if not isinstance(claim, dict):
        return True
    now_val = _now_epoch() if now is None else now
    expires = claim.get("expires_at")
    try:
        expires_at = float(expires)
    except Exception:
        return True
    return expires_at <= now_val


def _claim_token_from_frontmatter(meta: dict | None) -> str | None:
    claim = meta.get("claim") if isinstance(meta, dict) else None
    if not isinstance(claim, dict):
        return None
    token = claim.get("token")
    return str(token) if token else None


def _claim_token_from_file(message_id: str) -> str | None:
    claim = _read_claim(_claim_path(message_id))
    if not isinstance(claim, dict):
        return None
    token = claim.get("token")
    return str(token) if token else None


def _message_reply_paths(message_id: str, inbox_dir: Path | None = None) -> list[Path]:
    inbox = inbox_dir or MESSAGES_INBOX
    if not inbox.is_dir():
        return []
    out: list[Path] = []
    for p in inbox.iterdir():
        if p.suffix != ".md" or p.name.startswith(".") or not p.is_file():
            continue
        try:
            meta, _ = parse_frontmatter(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not meta:
            continue
        if str(meta.get("in_reply_to", "")) == message_id:
            out.append(p)
    return out


def _has_reply(message_id: str, inbox_dir: Path | None = None) -> bool:
    return len(_message_reply_paths(message_id, inbox_dir)) > 0


def has_active_claim(
    path: Path,
    *, 
    role: str | None = None,
    worker_identity: dict | None = None,
) -> bool:
    """Return True when `path` has a non-stale claim owned by this worker context."""
    if not path.exists() or not path.is_file():
        return False
    try:
        meta, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    message_id = _msg_id_from_path(path, meta)
    claim = _read_claim(_claim_path(message_id))
    if claim is not None:
        if _is_stale_claim(claim):
            return False
        claim_path = claim.get("path")
        expected_path = str(path.resolve())
        if claim_path and claim_path not in {str(message_id), expected_path}:
            return False
        return _claim_owner_matches(
            claim,
            role=role,
            identity=worker_identity if isinstance(worker_identity, dict) else _worker_identity(role),
        )
    # If claim file is missing (e.g. crash/restart), trust frontmatter claim
    # metadata only when it still indicates an active lease.
    frontmatter_claim = meta.get("claim")
    if not isinstance(frontmatter_claim, dict):
        return False
    if _is_stale_claim(frontmatter_claim):
        return False
    claim_path = frontmatter_claim.get("path")
    expected_path = str(path.resolve())
    if claim_path and claim_path not in {str(message_id), expected_path}:
        return False
    return _claim_owner_matches(
        frontmatter_claim,
        role=role,
        identity=worker_identity if isinstance(worker_identity, dict) else _worker_identity(role),
    )


def current_claim_token(path: Path) -> str | None:
    """Return token for active claim file, or frontmatter claim when persisted."""
    try:
        meta, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    message_id = _msg_id_from_path(path, meta)
    token = _claim_token_from_file(message_id) or _claim_token_from_frontmatter(meta)
    if token is not None:
        return token
    return None


def _acquire_claim(
    message_id: str,
    role: str,
    *,
    ttl: int = CLAIM_TTL_SECONDS,
    now: float | None = None,
    message_path: str | None = None,
) -> bool:
    """Create an exclusive lease file. Returns True on success."""
    if not role:
        role = "unknown"
    now_val = _now_epoch() if now is None else now
    expiry = now_val + max(1, int(ttl))
    p = _claim_path(message_id)

    if not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)

    marker = {
        "message_id": message_id,
        "role": role,
        "pid": os.getpid(),
        "hostname": socket.gethostname(),
        "token": uuid.uuid4().hex,
        "claimed_at": now_val,
        "expires_at": expiry,
        "path": message_path or str(message_id),
    }
    marker_text = json.dumps(marker, ensure_ascii=False, indent=2, sort_keys=True)

    lock_path = _claim_lock_path(message_id)
    if not _acquire_claim_file_lock(lock_path):
        return False

    try:
        # If an existing lease is stale or malformed, allow takeover. The
        # directory lock keeps stale recovery and fresh creation serialized
        # across both threads and processes.
        claim = _read_claim(p)
        if claim is not None:
            if _is_stale_claim(claim, now=now_val) or claim == {}:
                try:
                    p.unlink(missing_ok=True)
                except Exception:
                    pass
            else:
                return False

        for attempt in range(MAX_CLAIM_CREATE_ATTEMPTS):
            try:
                with open(p, "x", encoding="utf-8") as f:
                    f.write(marker_text)
                observed = _read_claim(p)
                return bool(
                    isinstance(observed, dict)
                    and str(observed.get("token")) == str(marker.get("token"))
                )
            except FileExistsError:
                return False
            except Exception:
                observed = _read_claim(p)
                if observed is not None and not _is_stale_claim(observed, now=now_val):
                    return False
                if observed is not None:
                    try:
                        p.unlink(missing_ok=True)
                    except Exception:
                        pass
                if attempt == MAX_CLAIM_CREATE_ATTEMPTS - 1:
                    return False
                time.sleep(CLAIM_CREATE_RETRY_DELAY_SECONDS)
    finally:
        _release_claim_file_lock(lock_path)


def _release_claim(message_id: str) -> None:
    path = _claim_path(message_id)
    try:
        path.unlink(missing_ok=True)
    except Exception:
        pass


def claim_message(path: Path, meta: dict, body: str, role: str | None = None) -> bool:
    """Mark one inbox message as claimed, with lease ownership.

    Returns True if this process owns the message; False for any race or invalid
    state. Writes minimal claim metadata into frontmatter for observability.
    """
    role = (role or "unknown").strip() or "unknown"
    if not path.exists() or not path.is_file():
        return False
    if not isinstance(meta, dict) or not isinstance(body, str):
        return False
    if meta.get("status") != "open":
        return False

    message_id = _msg_id_from_path(path, meta)
    if not message_id.startswith("MSG-"):
        return False

    # Re-parse before claiming: status can change between list and claim.
    try:
        current_text = path.read_text(encoding="utf-8")
        current_meta, current_body = parse_frontmatter(current_text)
    except Exception:
        return False
    if not current_meta or current_meta.get("status") != "open":
        return False
    message_id = _msg_id_from_path(path, current_meta)

    # Lease before mutation narrows the duplicate-response window.
    message_path = str(path.resolve())
    if not _acquire_claim(message_id, role=role, message_path=message_path):
        return False

    # If message changed after claiming, release and back out.
    try:
        current_text = path.read_text(encoding="utf-8")
        current_meta, current_body = parse_frontmatter(current_text)
    except Exception:
        _release_claim(message_id)
        return False
    if not current_meta or current_meta.get("status") != "open":
        _release_claim(message_id)
        return False

    current_meta["status"] = "claimed"
    now = _now_epoch()
    current_meta["claim"] = {
        "role": role,
        "pid": os.getpid(),
        "hostname": socket.gethostname(),
        "token": _claim_token_from_file(message_id),
        "claimed_at": now,
        "expires_at": now + CLAIM_TTL_SECONDS,
    }
    if not _write_text_atomic(path, serialize_frontmatter(current_meta, current_body)):
        _release_claim(message_id)
        return False
    return True


def mark_answered(
    path: Path,
    *,
    role: str | None = None,
    worker_identity: dict | None = None,
) -> bool:
    """Mark claimed/open message as answered if caller owns the lease."""
    if not path.exists() or not path.is_file():
        return False
    meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    if not meta:
        return False
    if meta.get("status") not in {"claimed", "open"}:
        return False
    message_id = _msg_id_from_path(path, meta)
    identity: dict[str, object] = _worker_identity(
        role,
        pid=worker_identity.get("pid") if isinstance(worker_identity, dict) else None,
        hostname=worker_identity.get("hostname") if isinstance(worker_identity, dict) else None,
    )
    if isinstance(worker_identity, dict):
        token = worker_identity.get("token")
        if token is not None:
            identity["token"] = token
        else:
            claim_token = worker_identity.get("claim_token")
            if claim_token is not None:
                identity["token"] = claim_token
    claim = _read_claim(_claim_path(message_id))
    if claim is not None:
        if not _claim_owner_matches(claim, role=role, identity=identity):
            # Explicit ownership mismatch -> do not let another worker close this claim.
            return False
        if _is_stale_claim(claim) and not _has_reply(message_id):
            # Stale claim without a reply is no longer valid.
            _release_claim(message_id)
            return False
        if _is_stale_claim(claim) and _has_reply(message_id):
            # A reply already exists; close the source as answered to prevent stale
            # claim deadlock.
            meta["status"] = "answered"
            if not _write_text_atomic(path, serialize_frontmatter(meta, body)):
                return False
            _release_claim(message_id)
            return True
    else:
        if _has_reply(message_id):
            # If the reply landed without a persisted claim file, treat this as
            # completed and continue (idempotent ownership).
            meta["status"] = "answered"
            if not _write_text_atomic(path, serialize_frontmatter(meta, body)):
                return False
            return True
        if not _claim_owner_matches(meta.get("claim", {}), role=role, identity=identity):
            return False

    meta["status"] = "answered"
    if not _write_text_atomic(path, serialize_frontmatter(meta, body)):
        return False
    _release_claim(message_id)
    return True


def recover_stale_claim(path: Path, *, now: float | None = None) -> bool:
    """Try to recover a stale claim in-place.

    Returns True only when the file changed.
    """
    if not path.exists() or not path.is_file():
        return False
    meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    if not meta:
        return False
    message_id = _msg_id_from_path(path, meta)
    lock_path = _claim_lock_path(message_id)
    if not _acquire_claim_file_lock(lock_path):
        return False
    try:
        claim = _read_claim(_claim_path(message_id))
        if claim is None:
            return False
        claim_path = str(claim.get("path", ""))
        expected_path = str(path.resolve())
        if claim_path and claim_path not in {str(message_id), expected_path}:
            _release_claim(message_id)
            return False
        if not _is_stale_claim(claim, now=_now_epoch() if now is None else now):
            return False

        if _has_reply(message_id):
            # Reply already exists -> lease can be deleted without reopening.
            _release_claim(message_id)
            return False

        if meta.get("status") != "claimed":
            _release_claim(message_id)
            return False

        meta["status"] = "open"
        if not _write_text_atomic(path, serialize_frontmatter(meta, body)):
            return False
        _release_claim(message_id)
        return True
    finally:
        _release_claim_file_lock(lock_path)


if __name__ == "__main__":
    raise SystemExit(main())
