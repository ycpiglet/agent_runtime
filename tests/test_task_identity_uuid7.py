import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import task_identity as ti  # noqa: E402


def test_uuid7_is_valid_version7_variant() -> None:
    u = ti._uuid7()
    assert u.version == 7  # RFC 9562 version nibble
    assert (u.int >> 62) & 0b11 == 0b10  # variant 10xx
    s = str(u)
    assert s[14] == "7"  # version position in the canonical string
    assert ti._valid_uuid(s)  # passes the (now v4|v7) validator


def test_uuid7_is_time_sortable_and_collision_free() -> None:
    us = [ti._uuid7() for _ in range(64)]
    strs = [str(u) for u in us]
    assert len(set(strs)) == 64  # no coordination, still collision-free
    ms = [u.int >> 80 for u in us]  # 48-bit unix-ms prefix
    assert ms == sorted(ms)  # minted in order -> time-sortable


def test_legacy_uuid4_keys_remain_valid() -> None:
    # The 196 existing task_uids are UUIDv4; the widened validator must still
    # accept them (and any new v4) so no historical record is invalidated.
    assert ti._valid_uuid("11111111-1111-4111-8111-111111111111")
    assert ti._valid_uuid(str(uuid.uuid4()))


def test_backfill_mints_a_uuid7() -> None:
    updates = ti._backfill_updates({"id": "TASK-AR-999", "status": "planned"}, "2026-06-14T10:00:00+09:00")
    assert ti._valid_uuid(updates["task_uid"])
    assert uuid.UUID(updates["task_uid"]).version == 7
