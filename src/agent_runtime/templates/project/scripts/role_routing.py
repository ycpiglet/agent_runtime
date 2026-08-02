"""Flag-gated routing of work to dormant review/council/scout roles + beta activation.

WHY THIS EXISTS (2026-06-22 audit): the live dispatch loop centralizes on
lead-engineer (~76% of claims) and never exercises the council / skeptic /
progress-scout review paths; the beta_tester role is dormant (BTC output 0).
This module builds the capability to operationalize those dormant roles.

SAFETY CONTRACT (CRITICAL): other instances of this autonomous system run LIVE
in the same repo concurrently. Every behavior here that changes *who gets work*
is FLAG-GATED and DEFAULT-OFF, so merging this module is INERT until the Owner
flips a flag. The flags are independent kill-switches:

  * AR_ROLE_ROUTING    -> route_review_pass(): on a high-risk event (merge/
                          closeout), CREATE an ADDITIVE review claim for a review
                          role (skeptic / independent-auditor) as a PARALLEL
                          pass. It never removes or mutates the lead-engineer
                          claim — the review runs alongside it.
  * AR_SCOUT_COUNCIL   -> dispatch_wave_hooks(): per wave, dispatch a
                          progress-scout sweep; at the W6 boundary, additionally
                          dispatch a council deliberation.
  * AR_BETA_ACTIVATION -> maybe_activate_beta(): when beta_tester_due reports
                          due/overdue, emit a beta_tester claim + a BTC-*
                          scaffold so the dormant beta role actually runs.

Additive claims are written DIRECTLY here (not through task_claim_dispatcher),
because they are orchestration-overlay claims: they carry no worktree, must not
collide with the worker's task_id, and must not trip the dispatcher's
"one active claim per task_id/task_set" refusal against the live lead claim.
Each additive claim uses a deterministic claim_id so re-dispatch is idempotent.

With every flag OFF the public functions create NOTHING and return
``{"enabled": False, "created": []}`` — proven inert by tests/test_role_routing.py.
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import threading
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NamedTuple

import atomic_io
from agent_runtime import claim_store
from pane_event_log import append_event


SCHEMA = "agent-runtime-task-claim/v1"

ROLE_ROUTING_FLAG = "AR_ROLE_ROUTING"
SCOUT_COUNCIL_FLAG = "AR_SCOUT_COUNCIL"
BETA_ACTIVATION_FLAG = "AR_BETA_ACTIVATION"

# Routing labels for the additive overlay claims. These are intentionally the
# audit's role names (skeptic / progress-scout / council / beta-tester); they
# are written verbatim onto the claim's agent_role so dashboards can attribute
# the parallel pass. They do not need to resolve through ORG-MODEL because these
# claims are orchestration overlays, not gated worker claims.
DEFAULT_REVIEW_ROLE = "independent-auditor"
SKEPTIC_ROLE = "skeptic"
SCOUT_ROLE = "progress-scout"
COUNCIL_ROLE = "council"
BETA_ROLE = "beta-tester"

_WINDOWS_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x0400)
_BTC_DIRECTORY_COMPONENTS = ("agents", "beta_tester", "test_cases")

# These fields describe execution progress or terminal provenance and may
# legitimately change after the deterministic overlay is first published.
# Every other emitted field is stable authority metadata and is either checked
# for exact equality or validated against its creation-bound artifact below.
OVERLAY_MUTABLE_LIFECYCLE_FIELDS = frozenset(
    {
        "status",
        "phase",
        "progress_pct",
        "last_heartbeat",
        "updated_at",
        "released_at",
        "verified_by",
        "verifier_role",
        "verification_evidence",
        "recovered_from_status",
        "reaped_at",
        "reaped_by",
        "reaped_reason",
    }
)

# Merge-risk escalation signals: when a closeout/merge carries any of these
# (model_routing.ESCALATION_TRIGGERS members), route an ADDITIVE skeptic
# adversarial pass on top of the default auditor pass. This deliberately
# EXCLUDES bare "ambiguity": ambiguity is scope-clarity (resolve before work),
# not merge danger, so it does not warrant a skeptic on closeout. Tunable set.
HIGH_RISK_TRIGGERS = {
    "high_risk",
    "security",
    "external_effect",
    "cross_cutting",
    "repeated_failure",
}


def _truthy(value: str | None, default: bool) -> bool:
    """House-style flag reader (matches scripts/claim_reaper_hook.py)."""
    if value is None or value == "":
        return default
    return str(value).strip().lower() not in ("0", "false", "no", "off")


def role_routing_enabled() -> bool:
    return _truthy(os.environ.get(ROLE_ROUTING_FLAG), False)


def scout_council_enabled() -> bool:
    return _truthy(os.environ.get(SCOUT_COUNCIL_FLAG), False)


def beta_activation_enabled() -> bool:
    return _truthy(os.environ.get(BETA_ACTIVATION_FLAG), False)


ROUTING_CONFIG = "agents/project/role-routing.json"


def _config_enabled(root: Path, key: str) -> bool | None:
    """Config-driven gate: read ``agents/project/role-routing.json`` and return
    the bool for ``key``. Returns None (file missing / bad JSON / key absent /
    non-bool) so the caller falls back to the env flag. This lets the autonomous
    dispatch loop activate routing from committed config without depending on the
    process env reaching it (the env path stays as an override/fallback)."""
    try:
        data = json.loads((root / ROUTING_CONFIG).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    value = data.get(key) if isinstance(data, dict) else None
    return value if isinstance(value, bool) else None


def _feature_enabled(root: Path, key: str, env_flag: str) -> bool:
    """Resolve one feature flag with an explicit environment kill switch."""
    env_value = os.environ.get(env_flag)
    if env_value is not None and env_value != "":
        return _truthy(env_value, False)
    configured = _config_enabled(root, key)
    return configured if configured is not None else False


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _now_iso(now: str | None) -> str:
    if now:
        return now
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _claim_dir(root: Path) -> Path:
    return root / "agents" / "runtime" / "task_claims"


def _claim_path(root: Path, claim_id: str) -> Path:
    return _claim_dir(root) / f"{claim_id}.json"


def _artifact_path(root: Path, claim_id: str, suffix: str) -> Path:
    return _claim_dir(root) / f"{claim_id}.{suffix}.md"


def _rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _is_path_alias(metadata: os.stat_result) -> bool:
    attributes = int(getattr(metadata, "st_file_attributes", 0) or 0)
    reparse_tag = int(getattr(metadata, "st_reparse_tag", 0) or 0)
    return (
        stat.S_ISLNK(metadata.st_mode)
        or bool(attributes & _WINDOWS_REPARSE_POINT)
        or bool(reparse_tag)
    )


def _overlay_handoff_text(
    *,
    claim_id: str,
    task_id: str,
    parent_task_id: str,
    agent_role: str,
    mode: str,
    status_text: str,
) -> str:
    return (
        f"# Handoff: {claim_id}\n\n"
        f"- task_id: {task_id}\n"
        f"- parent_task_id: {parent_task_id or '-'}\n"
        f"- agent_role: {agent_role}\n"
        f"- mode: {mode}\n"
        f"- status: claimed\n"
        f"- status_text: {status_text}\n"
    )


def _overlay_log_text(
    *,
    claim_id: str,
    claimed_at: str,
    task_id: str,
    agent_instance_id: str,
    status_text: str,
) -> str:
    return (
        f"# Claim Log: {claim_id}\n\n"
        f"- claimed_at: {claimed_at}\n"
        f"- task_id: {task_id}\n"
        f"- agent_instance_id: {agent_instance_id}\n"
        f"- status_text: {status_text}\n"
    )


def _require_direct_overlay_artifact(
    path: Path,
    label: str,
    *,
    required_prefix: bytes,
) -> None:
    try:
        metadata = path.lstat()
    except FileNotFoundError as exc:
        raise claim_store.ClaimStoreError(
            f"claim-store overlay {label} is missing"
        ) from exc
    except (OSError, RuntimeError) as exc:
        raise claim_store.ClaimStoreError(
            f"claim-store overlay {label} metadata is unavailable"
        ) from exc
    if _is_path_alias(metadata) or not stat.S_ISREG(metadata.st_mode):
        raise claim_store.ClaimStoreError(
            f"claim-store overlay {label} is not a direct regular file"
        )
    if metadata.st_size < len(required_prefix):
        raise claim_store.ClaimStoreError(
            f"claim-store overlay {label} required prefix is truncated"
        )
    try:
        with path.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            payload_prefix = handle.read(len(required_prefix))
        metadata_after = path.lstat()
    except (OSError, RuntimeError) as exc:
        raise claim_store.ClaimStoreError(
            f"claim-store overlay {label} is unreadable"
        ) from exc
    identity = (int(metadata.st_dev), int(metadata.st_ino))
    if (
        _is_path_alias(opened)
        or not stat.S_ISREG(opened.st_mode)
        or (int(opened.st_dev), int(opened.st_ino)) != identity
        or _is_path_alias(metadata_after)
        or not stat.S_ISREG(metadata_after.st_mode)
        or (int(metadata_after.st_dev), int(metadata_after.st_ino)) != identity
    ):
        raise claim_store.ClaimStoreError(
            f"claim-store overlay {label} changed during validation"
        )
    if payload_prefix != required_prefix:
        raise claim_store.ClaimStoreError(
            f"claim-store overlay {label} required prefix is invalid"
        )


def _existing_overlay_claim(
    root: Path,
    *,
    claim_id: str,
    task_id: str,
    agent_role: str,
    mode: str,
    status_text: str,
    now: str,
    task_set_id: str = "",
    tags: list[str] | None = None,
    parent_task_id: str = "",
    parent_task_set_id: str = "",
    event_name: str = "",
) -> bool:
    """Return true only for the complete deterministic overlay contract."""

    del now
    path = _claim_path(root, claim_id)

    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False
    except (OSError, RuntimeError) as exc:
        raise claim_store.ClaimStoreError(
            "claim-store overlay claim metadata is unavailable"
        ) from exc
    if _is_path_alias(metadata):
        raise claim_store.ClaimStoreError(
            "claim-store overlay claim alias is invalid"
        )
    if not stat.S_ISREG(metadata.st_mode):
        raise claim_store.ClaimStoreError(
            "claim-store overlay claim is not a regular file"
        )
    payload = claim_store.read_claim_payload(path)
    handoff_path = _artifact_path(root, claim_id, "handoff")
    log_path = _artifact_path(root, claim_id, "log")
    expected = {
        "claim_id": claim_id,
        "task_id": task_id,
        "task_set_id": task_set_id,
        "active_scope": task_set_id,
        "agent_role": agent_role,
        "team_id": "agent-runtime-core",
        "agent_instance_id": f"{agent_role}-{claim_id}",
        "display_name": f"{agent_role}@{mode}",
        "callsite_id": (
            f"role-routing:{event_name or 'overlay'}:"
            f"{parent_task_id or parent_task_set_id or task_id}:{agent_role}"
        ),
        "pane_id": f"overlay:{claim_id}",
        "mode": mode,
        "status_text": status_text,
        "tags": list(tags or []),
        "overlay": True,
        "allow_parallel_task_set": True,
        "parent_task_id": parent_task_id,
        "parent_task_set_id": parent_task_set_id,
        "handoff_path": handoff_path.relative_to(root).as_posix(),
        "log_path": log_path.relative_to(root).as_posix(),
    }
    if any(payload.get(key) != value for key, value in expected.items()):
        raise claim_store.ClaimStoreError(
            "claim-store overlay claim contract is incomplete or mismatched"
        )
    unexpected_fields = set(payload) - (
        set(expected)
        | {"schema", "claimed_at", "persistence"}
        | OVERLAY_MUTABLE_LIFECYCLE_FIELDS
    )
    if unexpected_fields:
        raise claim_store.ClaimStoreError(
            "claim-store overlay claim has unsupported stable metadata"
        )
    lifecycle = {
        "status": payload.get("status"),
        "phase": payload.get("phase"),
        "progress_pct": payload.get("progress_pct"),
        "last_heartbeat": payload.get("last_heartbeat"),
        "updated_at": payload.get("updated_at"),
    }
    if (
        lifecycle["status"] not in (
            claim_store.ACTIVE_CLAIM_STATUSES
            | claim_store.INACTIVE_CLAIM_STATUSES
        )
        or not isinstance(lifecycle["phase"], str)
        or not lifecycle["phase"]
        or len(lifecycle["phase"]) > 128
        or isinstance(lifecycle["progress_pct"], bool)
        or not isinstance(lifecycle["progress_pct"], int)
        or not 0 <= lifecycle["progress_pct"] <= 100
        or any(
            not isinstance(lifecycle[field], str)
            or not lifecycle[field]
            or len(lifecycle[field]) > 128
            or "\n" in lifecycle[field]
            or "\r" in lifecycle[field]
            for field in ("last_heartbeat", "updated_at")
        )
    ):
        raise claim_store.ClaimStoreError(
            "claim-store overlay lifecycle metadata is invalid"
        )
    persistence = payload.get("persistence")
    if persistence != {
        "mode": "working_tree",
        "scm_commit_authorized": False,
    }:
        raise claim_store.ClaimStoreError(
            "claim-store overlay persistence contract is invalid"
        )
    claimed_at = payload.get("claimed_at")
    if (
        not isinstance(claimed_at, str)
        or not claimed_at
        or len(claimed_at) > 128
        or "\n" in claimed_at
        or "\r" in claimed_at
    ):
        raise claim_store.ClaimStoreError(
            "claim-store overlay claimed_at contract is invalid"
        )
    _require_direct_overlay_artifact(
        handoff_path,
        "handoff",
        required_prefix=_overlay_handoff_text(
            claim_id=claim_id,
            task_id=task_id,
            parent_task_id=parent_task_id,
            agent_role=agent_role,
            mode=mode,
            status_text=status_text,
        ).encode("utf-8"),
    )
    _require_direct_overlay_artifact(
        log_path,
        "log",
        required_prefix=_overlay_log_text(
            claim_id=claim_id,
            claimed_at=claimed_at,
            task_id=task_id,
            agent_instance_id=f"{agent_role}-{claim_id}",
            status_text=status_text,
        ).encode("utf-8"),
    )
    return True


def _require_overlay_artifact_absent(path: Path, label: str) -> None:
    try:
        path.lstat()
    except FileNotFoundError:
        return
    except (OSError, RuntimeError) as exc:
        raise claim_store.ClaimStoreError(
            f"claim-store overlay {label} metadata is unavailable"
        ) from exc
    raise claim_store.ClaimStoreError(
        f"claim-store overlay {label} already exists"
    )


class _CreatedOverlayPublication(NamedTuple):
    path: Path
    expected: bytes
    device: int
    inode: int


def _created_overlay_publication(
    path: Path,
    expected: bytes,
    identity: atomic_io.PublishedFileIdentity,
) -> _CreatedOverlayPublication:
    """Register rollback authority without re-opening a committed path."""

    return _CreatedOverlayPublication(
        path,
        expected,
        identity.device,
        identity.inode,
    )


def _remove_owned_overlay_publication(
    publication: _CreatedOverlayPublication,
) -> None:
    """Remove only the unchanged direct file captured after publication."""

    try:
        metadata = publication.path.lstat()
    except FileNotFoundError:
        return
    except (OSError, RuntimeError):
        return
    identity = (publication.device, publication.inode)
    if (
        _is_path_alias(metadata)
        or not stat.S_ISREG(metadata.st_mode)
        or metadata.st_size != len(publication.expected)
        or (int(metadata.st_dev), int(metadata.st_ino)) != identity
    ):
        return
    try:
        payload = publication.path.read_bytes()
        metadata_after = publication.path.lstat()
    except (OSError, RuntimeError):
        return
    if (
        payload != publication.expected
        or _is_path_alias(metadata_after)
        or not stat.S_ISREG(metadata_after.st_mode)
        or (int(metadata_after.st_dev), int(metadata_after.st_ino)) != identity
    ):
        return
    try:
        publication.path.unlink()
    except OSError:
        pass


def _rollback_overlay_publications(
    publications: list[_CreatedOverlayPublication],
) -> None:
    for publication in reversed(publications):
        _remove_owned_overlay_publication(publication)


def _first_store_marker_recovery_finding(root: Path) -> str | None:
    """Return recovery truth when a first overlay's marker may remain.

    The first overlay claim is also the marker pair's retained witness. If the
    marker transaction cannot remove every marker, deleting that claim would
    convert a recoverable inner-only store into an integrity-invalid store.
    """

    inner = _claim_dir(root) / ".claim-store"
    try:
        markers = (claim_store.outer_marker_path(root), inner)
    except (claim_store.ClaimStoreError, OSError, RuntimeError, ValueError):
        return (
            "claim-store recovery-required: marker rollback state is unknown; "
            "witness overlay was preserved"
        )
    for marker in markers:
        try:
            marker.lstat()
        except FileNotFoundError:
            continue
        except (OSError, RuntimeError):
            return (
                "claim-store recovery-required: marker rollback state is unknown; "
                "witness overlay was preserved"
            )
        return (
            "claim-store recovery-required: marker rollback is incomplete; "
            "witness overlay was preserved"
        )
    return None


def _write_overlay_claim_unlocked(
    root: Path,
    *,
    claim_id: str,
    task_id: str,
    agent_role: str,
    mode: str,
    status_text: str,
    now: str,
    task_set_id: str = "",
    tags: list[str] | None = None,
    parent_task_id: str = "",
    parent_task_set_id: str = "",
    event_name: str = "",
    created_publications: list[_CreatedOverlayPublication] | None = None,
) -> dict[str, Any] | None:
    """Write one additive overlay claim, idempotently.

    Returns the claim dict if newly created, or ``None`` if a claim with this
    deterministic ``claim_id`` already exists (re-dispatch is a no-op). The
    claim carries NO worktree_path on purpose: it is an orchestration overlay,
    not a worker checkout, so it never trips worktree-readiness gates and never
    competes with the live worker claim for a worktree.
    """
    if not claim_store.valid_claim_id(claim_id):
        raise claim_store.ClaimStoreError(
            "claim-store overlay claim id is invalid"
        )
    path = _claim_path(root, claim_id)
    if _existing_overlay_claim(
        root,
        claim_id=claim_id,
        task_id=task_id,
        agent_role=agent_role,
        mode=mode,
        status_text=status_text,
        now=now,
        task_set_id=task_set_id,
        tags=tags,
        parent_task_id=parent_task_id,
        parent_task_set_id=parent_task_set_id,
        event_name=event_name,
    ):
        return None
    handoff_path = _artifact_path(root, claim_id, "handoff")
    log_path = _artifact_path(root, claim_id, "log")
    _require_overlay_artifact_absent(handoff_path, "handoff")
    _require_overlay_artifact_absent(log_path, "log")
    claim: dict[str, Any] = {
        "schema": SCHEMA,
        "claim_id": claim_id,
        "task_id": task_id,
        "task_set_id": task_set_id,
        "active_scope": task_set_id,
        "agent_role": agent_role,
        "team_id": "agent-runtime-core",
        "agent_instance_id": f"{agent_role}-{claim_id}",
        "display_name": f"{agent_role}@{mode}",
        "callsite_id": (
            f"role-routing:{event_name or 'overlay'}:"
            f"{parent_task_id or parent_task_set_id or task_id}:{agent_role}"
        ),
        "pane_id": f"overlay:{claim_id}",
        "mode": mode,
        "status": "claimed",
        "phase": "claim-created",
        "progress_pct": 0,
        "status_text": status_text,
        "claimed_at": now,
        "last_heartbeat": now,
        "updated_at": now,
        "tags": list(tags or []),
        "overlay": True,  # additive orchestration overlay marker
        "allow_parallel_task_set": True,
        "parent_task_id": parent_task_id,
        "parent_task_set_id": parent_task_set_id,
        "handoff_path": _rel(root, handoff_path),
        "log_path": _rel(root, log_path),
        "persistence": {
            "mode": "working_tree",
            "scm_commit_authorized": False,
        },
    }
    publications = created_publications if created_publications is not None else []
    handoff_text = _overlay_handoff_text(
        claim_id=claim_id,
        task_id=task_id,
        parent_task_id=parent_task_id,
        agent_role=agent_role,
        mode=mode,
        status_text=status_text,
    )
    log_text = _overlay_log_text(
        claim_id=claim_id,
        claimed_at=now,
        task_id=task_id,
        agent_instance_id=claim["agent_instance_id"],
        status_text=status_text,
    )
    claim_bytes = (
        json.dumps(claim, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    ).encode("utf-8")
    try:
        handoff_identity = atomic_io.publish_text_owned_atomic(
            handoff_path,
            handoff_text,
        )
        publications.append(
            _created_overlay_publication(
                handoff_path,
                handoff_text.encode("utf-8"),
                handoff_identity,
            )
        )
        log_identity = atomic_io.publish_text_owned_atomic(log_path, log_text)
        publications.append(
            _created_overlay_publication(
                log_path,
                log_text.encode("utf-8"),
                log_identity,
            )
        )
        claim_identity = atomic_io.publish_json_owned_atomic(path, claim)
        publications.append(
            _created_overlay_publication(path, claim_bytes, claim_identity)
        )
    except BaseException:
        _rollback_overlay_publications(publications)
        raise
    return claim


def _write_overlay_claim(root: Path, **kwargs: Any) -> dict[str, Any] | None:
    """Publish one overlay under the checkout-local claim-store authority."""
    claim_id = str(kwargs.get("claim_id") or "")
    if not claim_store.valid_claim_id(claim_id):
        raise claim_store.ClaimStoreError(
            "claim-store overlay claim id is invalid"
        )
    event_payload: dict[str, Any] | None = None
    with claim_store.store_lock(root):
        inspection = claim_store.inspect_store(root)
        if inspection.state not in {"pristine", "initialized"}:
            raise claim_store.ClaimStoreError(
                f"{inspection.state}: "
                f"{inspection.finding or 'claim-store state is not writable'}"
            )
        if not claim_store.verify_snapshot(root, inspection.snapshot):
            raise claim_store.ClaimStoreError(
                "claim-store authority changed before overlay persistence"
            )
        if _existing_overlay_claim(root, **kwargs):
            return None

        created_publications: list[_CreatedOverlayPublication] = []
        claim = _write_overlay_claim_unlocked(
            root,
            created_publications=created_publications,
            **kwargs,
        )
        if claim is None:
            return None
        try:
            if inspection.state == "pristine":
                claim_store.initialize_store(root, witness_claim_id=claim_id)
            else:
                current = claim_store.inspect_store(root)
                if (
                    current.state != "initialized"
                    or current.generation_id != inspection.generation_id
                    or current.witness_claim_id != inspection.witness_claim_id
                ):
                    raise claim_store.ClaimStoreError(
                        "initialized claim-store authority changed during overlay persistence"
                    )
        except BaseException as exc:
            recovery_finding = (
                _first_store_marker_recovery_finding(root)
                if inspection.state == "pristine"
                else None
            )
            if recovery_finding is not None:
                raise claim_store.ClaimStoreError(recovery_finding) from exc
            _rollback_overlay_publications(created_publications)
            raise

        event_name = str(kwargs.get("event_name") or "")
        if event_name:
            event_payload = {
                "event": event_name,
                "actor": claim["agent_instance_id"],
                "actor_role": claim["agent_role"],
                "agent_instance_id": claim["agent_instance_id"],
                "display_name": claim["display_name"],
                "callsite_id": claim["callsite_id"],
                "pane_id": claim["pane_id"],
                "task_id": claim.get("parent_task_id") or claim["task_id"],
                "task_set_id": (
                    claim.get("parent_task_set_id") or claim.get("task_set_id")
                ),
                "claim_id": claim_id,
                "message": claim["status_text"],
                "ts": claim["claimed_at"],
            }
    if event_payload is not None:
        try:
            append_event(root, event_payload)
        except Exception:  # noqa: BLE001 - persisted authority stays successful
            pass
    return claim


def _bounded_claim_store_finding(operation: str, error: BaseException) -> str:
    detail = " ".join(str(error).split()) or "claim-store unavailable"
    if "traceback" in detail.casefold():
        detail = "claim-store operation failed"
    return (f"claim-store {operation} refused: {detail}")[:256]


def _try_write_overlay_claim(
    root: Path,
    *,
    operation: str,
    **kwargs: Any,
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        return _write_overlay_claim(root, **kwargs), None
    except (
        claim_store.ClaimStoreError,
        TimeoutError,
        OSError,
        RuntimeError,
        ValueError,
    ) as exc:
        return None, _bounded_claim_store_finding(operation, exc)


def _slug(value: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in str(value)).strip("-") or "item"


# ---------------------------------------------------------------------------
# 1. Review-role routing (additive parallel review pass)
# ---------------------------------------------------------------------------


def route_review_pass(
    root: Path,
    *,
    task_id: str,
    task_set_id: str = "",
    event: str = "merge",
    review_role: str = DEFAULT_REVIEW_ROLE,
    triggers: Sequence[str] | None = None,
    now: str | None = None,
) -> dict[str, Any]:
    """On a high-risk event (merge/closeout) create an ADDITIVE review claim.

    Default-off behind ``AR_ROLE_ROUTING``. When off, nothing is created and the
    live lead-engineer claim is left untouched (inert). When on, a parallel
    review pass is dispatched for ``review_role`` against a DISTINCT, additive
    task id (``REVIEW-<task>-<role>``) so it never collides with or removes the
    worker's claim — the lead keeps working while the reviewer runs in parallel.

    HIGH-RISK escalation: when ``triggers`` intersects ``HIGH_RISK_TRIGGERS`` the
    routine ADDITIONALLY dispatches an adversarial ``skeptic`` pass on top of the
    default auditor pass. This is purely additive — the auditor pass is created
    exactly as before, so non-high-risk closeouts (no triggers, or only
    scope-clarity "ambiguity") and existing callers that omit ``triggers`` are
    unchanged. If ``review_role`` is already the skeptic, the lead pass already
    covers it and no second skeptic overlay is created.
    """
    root = root.resolve()
    enabled = _feature_enabled(root, "role_routing", ROLE_ROUTING_FLAG)
    if not enabled:
        return {"enabled": False, "created": []}

    now = _now_iso(now)
    created: list[dict[str, Any]] = []

    review_task = f"REVIEW-{task_id}-{_slug(review_role)}"
    claim_id = f"CLAIM-REVIEW-{_slug(task_id)}-{_slug(review_role)}-{_slug(event)}"
    claim, finding = _try_write_overlay_claim(
        root,
        operation="review overlay",
        claim_id=claim_id,
        task_id=review_task,
        agent_role=review_role,
        mode="review",
        status_text=f"Additive {review_role} review pass for {task_id} ({event})",
        now=now,
        task_set_id=task_set_id,
        tags=["review", "additive", f"review-trigger:{event}"],
        parent_task_id=task_id,
        parent_task_set_id=task_set_id,
        event_name="review_pass_dispatched",
    )
    if finding:
        return {"enabled": True, "created": created, "finding": finding}
    if claim:
        created.append(claim)

    # High-risk escalation: an ADDITIVE adversarial skeptic pass. Skip when the
    # lead pass is already a skeptic (don't double-create).
    matched = sorted(set(triggers or ()) & HIGH_RISK_TRIGGERS)
    if matched and review_role != SKEPTIC_ROLE:
        skeptic_task = f"REVIEW-{task_id}-{_slug(SKEPTIC_ROLE)}"
        skeptic_claim_id = (
            f"CLAIM-REVIEW-{_slug(task_id)}-{_slug(SKEPTIC_ROLE)}-{_slug(event)}"
        )
        skeptic, finding = _try_write_overlay_claim(
            root,
            operation="skeptic overlay",
            claim_id=skeptic_claim_id,
            task_id=skeptic_task,
            agent_role=SKEPTIC_ROLE,
            mode="review",
            status_text=(
                f"Additive {SKEPTIC_ROLE} adversarial review pass for {task_id} "
                f"({event}; high-risk: {', '.join(matched)})"
            ),
            now=now,
            task_set_id=task_set_id,
            tags=["review", "additive", "high-risk", f"review-trigger:{event}", *matched],
            parent_task_id=task_id,
            parent_task_set_id=task_set_id,
            event_name="review_pass_dispatched",
        )
        if finding:
            return {"enabled": True, "created": created, "finding": finding}
        if skeptic:
            created.append(skeptic)

    return {"enabled": True, "created": created}


# ---------------------------------------------------------------------------
# 2. progress-scout per wave + council at W6
# ---------------------------------------------------------------------------


def dispatch_wave_hooks(
    root: Path,
    *,
    task_set_id: str,
    wave_no: int,
    is_w6: bool = False,
    now: str | None = None,
) -> dict[str, Any]:
    """Per-wave progress-scout sweep + W6-boundary council deliberation.

    Default-off behind ``AR_SCOUT_COUNCIL``. When off, nothing is created. When
    on: every wave gets a progress-scout sweep claim; only at the W6 boundary
    (``is_w6=True``) is a council deliberation additionally dispatched.
    """
    root = root.resolve()
    enabled = _feature_enabled(root, "scout_council", SCOUT_COUNCIL_FLAG)
    if not enabled:
        return {"enabled": False, "created": []}

    now = _now_iso(now)
    created: list[dict[str, Any]] = []

    scout, finding = _try_write_overlay_claim(
        root,
        operation="scout overlay",
        claim_id=f"CLAIM-SCOUT-{_slug(task_set_id)}-W{wave_no}",
        task_id=f"SCOUT-{task_set_id}-W{wave_no}",
        agent_role=SCOUT_ROLE,
        mode="scout-sweep",
        status_text=f"Progress-scout sweep for {task_set_id} wave {wave_no}",
        now=now,
        task_set_id=task_set_id,
        tags=["scout", "sweep", f"wave:{wave_no}"],
        parent_task_set_id=task_set_id,
        event_name="progress_scout_sweep",
    )
    if finding:
        return {"enabled": True, "created": created, "finding": finding}
    if scout:
        created.append(scout)

    if is_w6:
        council, finding = _try_write_overlay_claim(
            root,
            operation="council overlay",
            claim_id=f"CLAIM-COUNCIL-{_slug(task_set_id)}-W6",
            task_id=f"COUNCIL-{task_set_id}-W6",
            agent_role=COUNCIL_ROLE,
            mode="deliberation",
            status_text=f"Council deliberation at W6 boundary for {task_set_id}",
            now=now,
            task_set_id=task_set_id,
            tags=["council", "deliberation", "w6"],
            parent_task_set_id=task_set_id,
            event_name="council_deliberation",
        )
        if finding:
            return {"enabled": True, "created": created, "finding": finding}
        if council:
            created.append(council)

    return {"enabled": True, "created": created}


# ---------------------------------------------------------------------------
# 3. beta activation
# ---------------------------------------------------------------------------


def _btc_dir(root: Path) -> Path:
    return root / "agents" / "beta_tester" / "test_cases"


class _BtcScaffoldError(RuntimeError):
    """The BTC scaffold could not be published without following aliases."""


def _require_direct_directory(metadata: os.stat_result, label: str) -> None:
    if _is_path_alias(metadata) or not stat.S_ISDIR(metadata.st_mode):
        raise _BtcScaffoldError(f"BTC {label} is not a direct directory")


def _require_direct_regular(metadata: os.stat_result, label: str) -> None:
    if _is_path_alias(metadata) or not stat.S_ISREG(metadata.st_mode):
        raise _BtcScaffoldError(f"BTC {label} is not a direct regular file")


def _lstat_path(path: Path, label: str) -> os.stat_result | None:
    try:
        return path.lstat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise _BtcScaffoldError(f"BTC {label} metadata is unavailable") from exc


def _write_all(descriptor: int, payload: bytes) -> None:
    view = memoryview(payload)
    while view:
        written = os.write(descriptor, view)
        if written <= 0:
            raise _BtcScaffoldError("BTC temporary scaffold write made no progress")
        view = view[written:]


def _secure_dir_fd_available() -> bool:
    return (
        hasattr(os, "O_DIRECTORY")
        and hasattr(os, "O_NOFOLLOW")
        and os.open in os.supports_dir_fd
        and os.mkdir in os.supports_dir_fd
        and os.stat in os.supports_dir_fd
        and os.link in os.supports_dir_fd
        and os.link in os.supports_follow_symlinks
        and os.unlink in os.supports_dir_fd
    )


def _open_btc_directory_fd(root: Path) -> int:
    directory_flags = (
        os.O_RDONLY
        | os.O_DIRECTORY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_BINARY", 0)
    )
    try:
        current = os.open(root, directory_flags)
    except OSError as exc:
        raise _BtcScaffoldError("BTC repository root is unavailable") from exc
    try:
        _require_direct_directory(os.fstat(current), "repository root")
        for component in _BTC_DIRECTORY_COMPONENTS:
            try:
                child = os.open(component, directory_flags, dir_fd=current)
            except FileNotFoundError:
                try:
                    os.mkdir(component, mode=0o755, dir_fd=current)
                except FileExistsError:
                    pass
                except OSError as exc:
                    raise _BtcScaffoldError(
                        f"BTC parent component {component} could not be created"
                    ) from exc
                try:
                    child = os.open(component, directory_flags, dir_fd=current)
                except OSError as exc:
                    raise _BtcScaffoldError(
                        f"BTC parent component {component} is not a direct directory"
                    ) from exc
            except OSError as exc:
                raise _BtcScaffoldError(
                    f"BTC parent component {component} is not a direct directory"
                ) from exc
            try:
                opened = os.fstat(child)
                lexical = os.stat(component, dir_fd=current, follow_symlinks=False)
                _require_direct_directory(opened, f"parent component {component}")
                _require_direct_directory(lexical, f"parent component {component}")
                if (opened.st_dev, opened.st_ino) != (lexical.st_dev, lexical.st_ino):
                    raise _BtcScaffoldError(
                        f"BTC parent component {component} changed while opening"
                    )
            except BaseException:
                os.close(child)
                raise
            os.close(current)
            current = child
        return current
    except BaseException:
        os.close(current)
        raise


def _lstat_at(directory_fd: int, name: str, label: str) -> os.stat_result | None:
    try:
        return os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise _BtcScaffoldError(f"BTC {label} metadata is unavailable") from exc


def _publish_btc_with_dir_fd(root: Path, filename: str, payload: bytes) -> str:
    directory_fd = _open_btc_directory_fd(root)
    temporary = f".{filename}.{os.getpid()}.{threading.get_ident()}.tmp"
    temp_fd: int | None = None
    temp_exists = False
    try:
        target = _lstat_at(directory_fd, filename, "scaffold")
        if target is not None:
            _require_direct_regular(target, "scaffold")
            return "existing"

        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_BINARY", 0)
        )
        try:
            temp_fd = os.open(temporary, flags, 0o666, dir_fd=directory_fd)
            temp_exists = True
        except OSError as exc:
            raise _BtcScaffoldError("BTC temporary scaffold could not be created") from exc
        opened = os.fstat(temp_fd)
        lexical = _lstat_at(directory_fd, temporary, "temporary scaffold")
        if lexical is None:
            raise _BtcScaffoldError("BTC temporary scaffold disappeared while opening")
        _require_direct_regular(opened, "temporary scaffold")
        _require_direct_regular(lexical, "temporary scaffold")
        if (opened.st_dev, opened.st_ino) != (lexical.st_dev, lexical.st_ino):
            raise _BtcScaffoldError("BTC temporary scaffold changed while opening")
        _write_all(temp_fd, payload)
        try:
            os.fsync(temp_fd)
        except OSError:
            pass
        os.close(temp_fd)
        temp_fd = None

        try:
            os.link(
                temporary,
                filename,
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
                follow_symlinks=False,
            )
        except FileExistsError:
            target = _lstat_at(directory_fd, filename, "scaffold")
            if target is None:
                raise _BtcScaffoldError("BTC scaffold changed during publication")
            _require_direct_regular(target, "scaffold")
            return "existing"
        except OSError as exc:
            raise _BtcScaffoldError("BTC scaffold could not be published atomically") from exc

        # A successful no-clobber link is the scaffold commit point. Do not run
        # any fallible checks after it that could misreport a persisted target
        # as refused; temporary-name cleanup below is best-effort only.
        try:
            os.fsync(directory_fd)
        except OSError:
            pass
        return "created"
    finally:
        if temp_fd is not None:
            try:
                os.close(temp_fd)
            except OSError:
                pass
        if temp_exists:
            try:
                os.unlink(temporary, dir_fd=directory_fd)
            except OSError:
                pass
        try:
            os.close(directory_fd)
        except OSError:
            pass


def _ensure_btc_directory_portable(root: Path) -> tuple[Path, tuple[int, int]]:
    current = root
    root_metadata = _lstat_path(current, "repository root")
    if root_metadata is None:
        raise _BtcScaffoldError("BTC repository root is missing")
    _require_direct_directory(root_metadata, "repository root")
    for component in _BTC_DIRECTORY_COMPONENTS:
        current = current / component
        metadata = _lstat_path(current, f"parent component {component}")
        if metadata is None:
            try:
                current.mkdir(mode=0o755)
            except FileExistsError:
                pass
            except OSError as exc:
                raise _BtcScaffoldError(
                    f"BTC parent component {component} could not be created"
                ) from exc
            metadata = _lstat_path(current, f"parent component {component}")
            if metadata is None:
                raise _BtcScaffoldError(
                    f"BTC parent component {component} disappeared after creation"
                )
        _require_direct_directory(metadata, f"parent component {component}")
    final_metadata = current.lstat()
    return current, (final_metadata.st_dev, final_metadata.st_ino)


def _publish_btc_portable(root: Path, filename: str, payload: bytes) -> str:
    parent, parent_identity = _ensure_btc_directory_portable(root)
    target = parent / filename
    metadata = _lstat_path(target, "scaffold")
    if metadata is not None:
        _require_direct_regular(metadata, "scaffold")
        return "existing"

    temporary = parent / f".{filename}.{os.getpid()}.{threading.get_ident()}.tmp"
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_BINARY", 0)
    )
    descriptor: int | None = None
    temp_exists = False
    try:
        try:
            descriptor = os.open(temporary, flags, 0o666)
            temp_exists = True
        except OSError as exc:
            raise _BtcScaffoldError("BTC temporary scaffold could not be created") from exc
        opened = os.fstat(descriptor)
        lexical = _lstat_path(temporary, "temporary scaffold")
        if lexical is None:
            raise _BtcScaffoldError("BTC temporary scaffold disappeared while opening")
        _require_direct_regular(opened, "temporary scaffold")
        _require_direct_regular(lexical, "temporary scaffold")
        if (opened.st_dev, opened.st_ino) != (lexical.st_dev, lexical.st_ino):
            raise _BtcScaffoldError("BTC temporary scaffold changed while opening")
        _write_all(descriptor, payload)
        try:
            os.fsync(descriptor)
        except OSError:
            pass
        os.close(descriptor)
        descriptor = None

        current_parent = _lstat_path(parent, "scaffold parent")
        if current_parent is None:
            raise _BtcScaffoldError("BTC scaffold parent disappeared")
        _require_direct_directory(current_parent, "scaffold parent")
        if (current_parent.st_dev, current_parent.st_ino) != parent_identity:
            raise _BtcScaffoldError("BTC scaffold parent changed during publication")
        try:
            os.link(temporary, target, follow_symlinks=False)
        except FileExistsError:
            metadata = _lstat_path(target, "scaffold")
            if metadata is None:
                raise _BtcScaffoldError("BTC scaffold changed during publication")
            _require_direct_regular(metadata, "scaffold")
            return "existing"
        except OSError as exc:
            raise _BtcScaffoldError("BTC scaffold could not be published atomically") from exc
        # As above, link success is the portable commit point. Returning
        # ``created`` stays truthful even if best-effort temp cleanup later fails.
        return "created"
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temp_exists:
            try:
                temporary.unlink()
            except OSError:
                pass


def _write_btc_scaffold_atomic(root: Path, path: Path, text: str) -> str:
    """Publish one BTC without following parents or replacing an existing entry.

    ``created`` means this call atomically linked a complete temporary file into
    place; ``existing`` means a direct regular target already won the idempotent
    race. Any file, symlink, junction, or reparse-point boundary is refused.
    """
    try:
        filename = path.relative_to(_btc_dir(root)).name
    except ValueError as exc:
        raise _BtcScaffoldError("BTC scaffold path is outside its fixed directory") from exc
    if path.parent != _btc_dir(root) or not filename or filename != path.name:
        raise _BtcScaffoldError("BTC scaffold path is outside its fixed directory")
    payload = text.encode("utf-8")
    if _secure_dir_fd_available():
        return _publish_btc_with_dir_fd(root, filename, payload)
    return _publish_btc_portable(root, filename, payload)


def _bounded_beta_scaffold_finding(error: BaseException) -> str:
    detail = " ".join(str(error).split()) or "scaffold publication failed"
    if "traceback" in detail.casefold():
        detail = "scaffold publication failed"
    return (f"beta scaffold refused: {detail}")[:256]


def maybe_activate_beta(
    root: Path,
    *,
    due_state: str,
    cycle: int,
    now: str | None = None,
) -> dict[str, Any]:
    """Emit a beta exploration round when due/overdue AND the flag is on.

    Default-off behind ``AR_BETA_ACTIVATION``. ``due_state`` is the verdict from
    scripts/beta_tester_due.py ("ok" | "due" | "overdue"); only "due"/"overdue"
    trigger a round. When triggered: a beta_tester claim is emitted and a BTC-*
    scaffold is written under agents/beta_tester/test_cases/. Idempotent per
    cycle (the BTC scaffold + claim_id are keyed on the cycle number).
    """
    root = root.resolve()
    due = str(due_state or "").strip().lower() in {"due", "overdue"}
    enabled = _feature_enabled(root, "beta_activation", BETA_ACTIVATION_FLAG)
    if not enabled:
        return {"enabled": False, "due": due, "created": []}
    if not due:
        return {"enabled": True, "due": False, "created": []}

    now = _now_iso(now)
    cycle_tag = f"CYCLE-{int(cycle):03d}"
    claim, finding = _try_write_overlay_claim(
        root,
        operation="beta overlay",
        claim_id=f"CLAIM-BETA-{cycle_tag}",
        task_id=f"BETA-ROUND-{cycle_tag}",
        agent_role=BETA_ROLE,
        mode="beta-round",
        status_text=f"Beta exploration round for {cycle_tag} ({due_state})",
        now=now,
        tags=["beta", "exploration", cycle_tag.lower()],
        event_name="beta_round_dispatched",
    )
    if finding:
        return {
            "enabled": True,
            "due": True,
            "created": [],
            "finding": finding,
        }

    created = [claim] if claim else []
    btc_path = _btc_dir(root) / f"BTC-{cycle_tag}-001.md"
    btc_text = "\n".join(
        [
            f"# BTC-{cycle_tag}-001",
            "",
            f"- 라운드: {cycle_tag}",
            f"- dispatched_at: {now}",
            f"- due_state: {due_state}",
            "- status: open",
            "",
            "## 탐색 시나리오",
            "- (작성: agents/beta_tester/SKILL.md §탐색 시나리오)",
            "",
            "## 발견 케이스",
            "- (발견 시 QA가 BUG 리포트로 변환: CLAUDE.md §Beta->QA 흐름)",
            "",
        ]
    )
    scaffold_path = btc_path.relative_to(root).as_posix()
    try:
        scaffold_status = _write_btc_scaffold_atomic(root, btc_path, btc_text)
    except Exception as exc:  # noqa: BLE001 - claim authority is already committed
        return {
            "enabled": True,
            "due": True,
            "created": created,
            "scaffold": {"path": scaffold_path, "status": "refused"},
            "finding": _bounded_beta_scaffold_finding(exc),
        }

    return {
        "enabled": True,
        "due": True,
        "created": created,
        "scaffold": {"path": scaffold_path, "status": scaffold_status},
    }


# ---------------------------------------------------------------------------
# CLI (advisory / manual trigger; still flag-gated)
# ---------------------------------------------------------------------------


def _emit(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"role-routing: enabled={payload.get('enabled')} created={len(payload.get('created') or [])}")
    for claim in payload.get("created") or []:
        print(f"- {claim['agent_role']} claim {claim['claim_id']} ({claim['mode']})")


def cmd_review(args: argparse.Namespace) -> int:
    payload = route_review_pass(
        args.root, task_id=args.task_id, task_set_id=args.task_set_id,
        event=args.event, review_role=args.review_role,
        triggers=args.trigger, now=args.now,
    )
    _emit(payload, as_json=args.json)
    return 1 if payload.get("finding") else 0


def cmd_wave(args: argparse.Namespace) -> int:
    payload = dispatch_wave_hooks(
        args.root, task_set_id=args.task_set_id, wave_no=args.wave_no,
        is_w6=args.w6, now=args.now,
    )
    _emit(payload, as_json=args.json)
    return 1 if payload.get("finding") else 0


def cmd_beta(args: argparse.Namespace) -> int:
    payload = maybe_activate_beta(
        args.root, due_state=args.due_state, cycle=args.cycle, now=args.now,
    )
    _emit(payload, as_json=args.json)
    return 1 if payload.get("finding") else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Flag-gated routing to dormant review/council/scout roles + beta "
            "activation. All subcommands are DEFAULT-OFF: set AR_ROLE_ROUTING / "
            "AR_SCOUT_COUNCIL / AR_BETA_ACTIVATION to enable."
        )
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)

    review = sub.add_parser("review", help="Additive review pass (AR_ROLE_ROUTING)")
    review.add_argument("--task-id", required=True)
    review.add_argument("--task-set-id", default="")
    review.add_argument("--event", default="merge")
    review.add_argument("--review-role", default=DEFAULT_REVIEW_ROLE)
    review.add_argument(
        "--trigger",
        action="append",
        default=[],
        help=(
            "Escalation trigger carried by the closeout (repeatable). When any "
            "intersects HIGH_RISK_TRIGGERS, an additive skeptic pass is dispatched."
        ),
    )
    review.add_argument("--now")
    review.add_argument("--json", action="store_true")
    review.set_defaults(func=cmd_review)

    wave = sub.add_parser("wave", help="Per-wave scout + W6 council (AR_SCOUT_COUNCIL)")
    wave.add_argument("--task-set-id", required=True)
    wave.add_argument("--wave-no", type=int, required=True)
    wave.add_argument("--w6", action="store_true", help="This wave is the W6 boundary")
    wave.add_argument("--now")
    wave.add_argument("--json", action="store_true")
    wave.set_defaults(func=cmd_wave)

    beta = sub.add_parser("beta", help="Beta activation when due (AR_BETA_ACTIVATION)")
    beta.add_argument("--due-state", default="ok", choices=("ok", "due", "overdue"))
    beta.add_argument("--cycle", type=int, required=True)
    beta.add_argument("--now")
    beta.add_argument("--json", action="store_true")
    beta.set_defaults(func=cmd_beta)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
