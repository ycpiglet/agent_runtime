"""Power-loss-safe atomic file writes shared across runtime scripts.

Why this exists: several scripts independently re-implemented a "write a temp file
then ``os.replace`` it" helper, but (a) the logic was duplicated and (b) none of
them called ``fsync`` — so a hard power loss between the buffered write and the
rename could leave a *stale* or *zero-length* target even though ``os.replace`` is
atomic w.r.t. the directory entry. Centralizing here gives every call-site the same
durable primitive: temp file -> flush -> fsync -> atomic rename.

The temp name embeds both PID and thread id so concurrent writers to the *same*
target (e.g. multi-threaded ``claim_reaper`` sweeps) never collide on the sidecar.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any


def _tmp_path(path: Path) -> Path:
    # PID + thread id => unique per writer, so concurrent writers to one target
    # never share a sidecar (matches the most careful prior implementations).
    return path.with_name(f"{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")


def write_text_atomic(path: Path, text: str, *, encoding: str = "utf-8", fsync: bool = True) -> None:
    """Atomically write ``text`` to ``path``.

    Creates parent dirs as needed. On success no ``.tmp`` sidecar remains; on any
    failure the partial temp file is cleaned up and the original target is left
    untouched (the write never corrupts an existing file).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = _tmp_path(path)
    try:
        with open(tmp, "w", encoding=encoding) as handle:
            handle.write(text)
            handle.flush()
            if fsync:
                try:
                    os.fsync(handle.fileno())
                except OSError:
                    # Durability is best-effort: even without fsync the os.replace
                    # below is still atomic, so we never leave a torn file.
                    pass
        os.replace(tmp, path)
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise


def write_json_atomic(
    path: Path,
    payload: Any,
    *,
    indent: int = 2,
    sort_keys: bool = False,
    fsync: bool = True,
) -> None:
    """Atomically write ``payload`` as JSON (trailing newline included)."""
    text = json.dumps(payload, ensure_ascii=False, indent=indent, sort_keys=sort_keys) + "\n"
    write_text_atomic(Path(path), text, fsync=fsync)
