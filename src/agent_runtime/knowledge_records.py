from __future__ import annotations

"""Task-linked compound knowledge records.

The canonical store is append-only at the record level:

```
agents/project/knowledge/compounds/
  records/COMPOUND-<timestamp>-<slug>-<digest>.json
  INDEX.json
```

Record files are host-owned facts.  ``INDEX.json`` is a deterministic
projection and may always be rebuilt from validated records.
"""

import argparse
import hashlib
import json
import os
import re
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


RECORD_SCHEMA = "agent-runtime-compound-record/v1"
INDEX_SCHEMA = "agent-runtime-compound-index/v1"
STORE_REL = Path("agents/project/knowledge/compounds")
RECORDS_REL = STORE_REL / "records"
INDEX_REL = STORE_REL / "INDEX.json"
LEGACY_REL = Path("agents/lead_engineer/compound_log.md")
SIGNATURE_RE = re.compile(r"^defect:[a-z0-9][a-z0-9-]{0,47}:[0-9a-f]{16}$")
RECORD_ID_RE = re.compile(
    r"^COMPOUND-\d{8}-\d{6}-[a-z0-9][a-z0-9-]{0,47}-[0-9a-f]{12}$"
)
WORK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{1,127}$")
STATUS_VALUES = {"active", "mitigated", "resolved", "superseded"}
TEXT_LIMITS = {
    "title": 160,
    "summary": 1200,
    "cause": 2400,
    "prevention": 2400,
    "created_by": 160,
}
MAX_SIGNATURE_INPUT = 240
MAX_REFS = 64
MAX_RECORDS = 10000
MAX_SEARCH_RESULTS = 100
MAX_FRONTMATTER_SCALAR = 4096
MAX_ACCEPTED_WATCH_BYTES = 256 * 1024
ACCEPTED_WATCH_STATUSES = {"accepted", "approved"}
ACCEPTED_WATCH_DECISIONS = {"accepted_watch"}
ACCEPTED_WATCH_REVIEWER_FIELDS = (
    "reviewed_by",
    "reviewer",
    "approved_by",
    "accepted_by",
    "verified_by",
)
REVIEWER_IDENTITY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._@/+:-]{0,159}$")
FRONTMATTER_KEY_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$")
NONCANONICAL_FRONTMATTER_LINE_SEPARATORS = (
    "\v",
    "\f",
    "\x1c",
    "\x1d",
    "\x1e",
    "\x85",
    "\u2028",
    "\u2029",
)
REVIEWER_IDENTITY_PLACEHOLDERS = {
    "-",
    "~",
    "false",
    "n",
    "n/a",
    "na",
    "nil",
    "no",
    "none",
    "null",
    "off",
    "on",
    "tbd",
    "true",
    "unknown",
    "y",
    "yes",
}
SECRET_RE = re.compile(
    r"(?i)(?:"
    r"\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[:=]|"
    r"\bbearer\s+[a-z0-9._~+/=-]{12,}|"
    r"\bsk-(?:proj-)?[a-z0-9_-]{12,}|"
    r"\bgh[pousr]_[a-z0-9]{20,}|"
    r"\bAKIA[0-9A-Z]{16}\b"
    r")"
)

RECORD_FIELDS = {
    "schema",
    "id",
    "created_at",
    "created_by",
    "title",
    "summary",
    "cause",
    "prevention",
    "work_ids",
    "defect_signatures",
    "recurrence_count",
    "status",
    "source_refs",
    "prevention_refs",
    "verification_refs",
}


class CompoundRecordError(ValueError):
    """A bounded, user-displayable compound-record validation error."""

    def __init__(self, findings: str | Iterable[str]):
        values = [findings] if isinstance(findings, str) else list(findings)
        self.findings = tuple(str(item) for item in values if str(item))
        super().__init__("; ".join(self.findings))


def _canonical_json(payload: object) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _normalized_text(value: object) -> str:
    return " ".join(unicodedata.normalize("NFKC", str(value or "")).split())


def _secret_like(value: str) -> bool:
    return bool(SECRET_RE.search(value))


def _absolute_like(value: str) -> bool:
    return (
        value.startswith(("/", "\\", "~"))
        or bool(re.match(r"^[A-Za-z]:[\\/]", value))
        or value.startswith("\\\\")
    )


def normalize_signature(value: object) -> str:
    """Return a stable, non-secret defect identifier for an explicit input."""

    text = _normalized_text(value)
    if not text:
        raise CompoundRecordError("compound:signature-empty")
    lowered = text.lower()
    if SIGNATURE_RE.fullmatch(lowered):
        return lowered
    if len(text) > MAX_SIGNATURE_INPUT:
        raise CompoundRecordError(
            f"compound:signature-oversized:{len(text)}>{MAX_SIGNATURE_INPUT}"
        )
    if _absolute_like(text):
        raise CompoundRecordError("compound:signature-absolute-path")
    if _secret_like(text):
        raise CompoundRecordError("compound:signature-secret-like")
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")[:48].rstrip("-")
    if not slug:
        slug = "defect"
    digest = hashlib.sha256(lowered.encode("utf-8")).hexdigest()[:16]
    return f"defect:{slug}:{digest}"


def normalize_signatures(values: Iterable[object]) -> list[str]:
    return list(dict.fromkeys(normalize_signature(value) for value in values))


def normalize_work_id(value: object) -> str:
    text = _normalized_text(value)
    if not WORK_ID_RE.fullmatch(text) or _secret_like(text):
        raise CompoundRecordError(f"compound:invalid-work-id:{text or 'empty'}")
    return text


def normalize_ref(value: object) -> str:
    text = str(value or "").strip().replace("\\", "/")
    if not text or len(text) > 512:
        raise CompoundRecordError("compound:invalid-ref:empty-or-oversized")
    if _absolute_like(text) or _secret_like(text):
        raise CompoundRecordError(f"compound:invalid-ref:{text[:80]}")
    parts = text.split("/")
    if any(part in {"", ".", ".."} for part in parts) or parts[0] == ".git":
        raise CompoundRecordError(f"compound:invalid-ref:{text[:80]}")
    return "/".join(parts)


def _frontmatter_key(raw_key: str) -> str:
    token = raw_key.strip(" \t")
    if not token:
        raise CompoundRecordError("compound:prevention-watch-invalid-field")
    if token.startswith("'"):
        if len(token) < 2 or not token.endswith("'"):
            raise CompoundRecordError(
                "compound:prevention-watch-invalid-field"
            )
        inner = token[1:-1]
        if "'" in inner.replace("''", ""):
            raise CompoundRecordError(
                "compound:prevention-watch-invalid-field"
            )
        key = inner.replace("''", "'")
    elif token.startswith('"'):
        if len(token) < 2 or not token.endswith('"'):
            raise CompoundRecordError(
                "compound:prevention-watch-invalid-field"
            )
        try:
            key = json.loads(token)
        except (json.JSONDecodeError, UnicodeError) as exc:
            raise CompoundRecordError(
                "compound:prevention-watch-invalid-field"
            ) from exc
    else:
        key = token
    if not isinstance(key, str) or FRONTMATTER_KEY_RE.fullmatch(key) is None:
        raise CompoundRecordError("compound:prevention-watch-invalid-field")
    return key


def _frontmatter_scalar(raw_value: str) -> str:
    token = raw_value.strip(" \t")
    if not token or len(token) > MAX_FRONTMATTER_SCALAR:
        raise CompoundRecordError("compound:prevention-watch-invalid-value")
    if token.startswith("'"):
        if len(token) < 2 or not token.endswith("'"):
            raise CompoundRecordError(
                "compound:prevention-watch-invalid-value"
            )
        inner = token[1:-1]
        if "'" in inner.replace("''", ""):
            raise CompoundRecordError(
                "compound:prevention-watch-invalid-value"
            )
        value = inner.replace("''", "'")
    elif token.startswith('"'):
        if len(token) < 2 or not token.endswith('"'):
            raise CompoundRecordError(
                "compound:prevention-watch-invalid-value"
            )
        try:
            value = json.loads(token)
        except (json.JSONDecodeError, UnicodeError) as exc:
            raise CompoundRecordError(
                "compound:prevention-watch-invalid-value"
            ) from exc
    else:
        if token.endswith(("'", '"')):
            raise CompoundRecordError(
                "compound:prevention-watch-invalid-value"
            )
        value = token
    if (
        not isinstance(value, str)
        or len(value) > MAX_FRONTMATTER_SCALAR
        or any(ord(character) < 32 for character in value)
        or any(character.isspace() and character != " " for character in value)
    ):
        raise CompoundRecordError("compound:prevention-watch-invalid-value")
    return value


def _unique_watch_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, value in pairs:
        if key in payload:
            raise CompoundRecordError(
                f"compound:prevention-watch-duplicate-field:{key}"
            )
        payload[key] = value
    return payload


def _frontmatter_lines(text: str) -> list[str]:
    """Split authority Markdown using only explicit LF or CRLF endings."""

    if any(
        separator in text
        for separator in NONCANONICAL_FRONTMATTER_LINE_SEPARATORS
    ):
        raise CompoundRecordError(
            "compound:prevention-watch-invalid-line-ending"
        )
    normalized = text.replace("\r\n", "\n")
    if "\r" in normalized:
        raise CompoundRecordError(
            "compound:prevention-watch-invalid-line-ending"
        )
    return normalized.split("\n")


def _read_accepted_watch_text(path: Path) -> str:
    """Read one authority-bearing watch without unbounded text decoding."""

    with path.open("rb") as stream:
        raw = stream.read(MAX_ACCEPTED_WATCH_BYTES + 1)
    if len(raw) > MAX_ACCEPTED_WATCH_BYTES:
        raise CompoundRecordError(
            "compound:prevention-watch-oversized"
        )
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CompoundRecordError(
            "compound:prevention-watch-invalid-utf8"
        ) from exc


def _simple_frontmatter_payload(path: Path) -> dict[str, Any]:
    """Read the bounded ASCII-separation subset used by accepted-watch refs."""

    text = _read_accepted_watch_text(path)
    lines = _frontmatter_lines(text)
    if not lines or lines[0] != "---":
        return {}
    try:
        end = next(
            index
            for index, line in enumerate(lines[1:], start=1)
            if line == "---"
        )
    except StopIteration:
        return {}

    payload: dict[str, Any] = {}
    seen: set[str] = set()
    active_list = ""
    active_list_indent: int | None = None
    for raw in lines[1:end]:
        if not raw or raw.startswith("#"):
            continue
        if raw.startswith((" ", "\t")):
            prefix_length = len(raw) - len(raw.lstrip(" \t"))
            indentation = raw[:prefix_length]
            content = raw[prefix_length:]
            if "\t" in indentation:
                raise CompoundRecordError(
                    "compound:prevention-watch-invalid-indentation"
                )
            if not content or content.startswith("#"):
                continue
            if active_list and content.startswith("- "):
                if active_list_indent is None:
                    active_list_indent = prefix_length
                elif prefix_length != active_list_indent:
                    raise CompoundRecordError(
                        "compound:prevention-watch-invalid-indentation"
                    )
                payload.setdefault(active_list, []).append(
                    _frontmatter_scalar(content[2:])
                )
                continue
            raise CompoundRecordError(
                "compound:prevention-watch-invalid-indentation"
            )
        if ":" not in raw:
            active_list = ""
            active_list_indent = None
            raise CompoundRecordError(
                "compound:prevention-watch-invalid-field"
            )
        key, value = raw.split(":", 1)
        key = _frontmatter_key(key)
        if key in seen:
            raise CompoundRecordError(
                f"compound:prevention-watch-duplicate-field:{key}"
            )
        seen.add(key)
        if value.strip(" \t"):
            payload[key] = _frontmatter_scalar(value)
            active_list = ""
            active_list_indent = None
        else:
            payload[key] = []
            active_list = key
            active_list_indent = None
    return payload


def _watch_payload(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".json":
        payload = json.loads(
            _read_accepted_watch_text(path),
            object_pairs_hook=_unique_watch_object,
        )
        if not isinstance(payload, dict):
            raise CompoundRecordError("compound:prevention-watch-invalid-root")
        return payload
    return _simple_frontmatter_payload(path)


def _value_items(value: object) -> list[str]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str) and item]
    return [value] if isinstance(value, str) and value else []


def _accepted_watch_token(value: object, allowed: set[str]) -> bool:
    return isinstance(value, str) and value.casefold() in allowed


def _reviewer_identity(value: object) -> str:
    if not isinstance(value, str):
        return ""
    text = value
    if (
        not text
        or text != text.strip()
        or text.casefold() in REVIEWER_IDENTITY_PLACEHOLDERS
        or REVIEWER_IDENTITY_RE.fullmatch(text) is None
    ):
        return ""
    return text


def _accepted_watch_findings(
    path: Path,
    ref: str,
    *,
    current_work_ids: set[str],
) -> tuple[bool, list[str]]:
    try:
        payload = _watch_payload(path)
    except (OSError, json.JSONDecodeError, CompoundRecordError):
        return False, [f"compound:prevention-watch-invalid:{ref}"]

    decision = payload.get("decision")
    if not _accepted_watch_token(decision, ACCEPTED_WATCH_DECISIONS):
        return False, []

    findings: list[str] = []
    if not _accepted_watch_token(payload.get("status"), ACCEPTED_WATCH_STATUSES):
        findings.append(f"compound:prevention-watch-not-accepted:{ref}")
    reviewers = {
        identity
        for field in ACCEPTED_WATCH_REVIEWER_FIELDS
        if (identity := _reviewer_identity(payload.get(field)))
    }
    if not any(reviewers):
        findings.append(f"compound:prevention-watch-reviewer-missing:{ref}")

    linked_work: set[str] = set()
    for field in ("work_id", "task_id", "unit_id", "work_ids"):
        for value in _value_items(payload.get(field)):
            try:
                normalized = normalize_work_id(value)
            except CompoundRecordError:
                continue
            if normalized == value:
                linked_work.add(normalized)
    if not current_work_ids.intersection(linked_work):
        findings.append(f"compound:prevention-watch-work-mismatch:{ref}")
    return not findings, findings


def validate_prevention_destinations(
    root: Path,
    record: dict[str, Any],
    *,
    current_work_ids: Iterable[object] = (),
) -> list[str]:
    """Validate durable prevention destinations when a Compound is consumed.

    This is deliberately separate from store validation so historical
    append-only records are never rewritten or newly invalidated in bulk.
    """

    try:
        normalized_record = validate_record(record)
        accepted_work_ids = {
            normalize_work_id(value) for value in current_work_ids
        }
    except CompoundRecordError as exc:
        return list(exc.findings)

    repository = Path(root).resolve()
    findings: list[str] = []
    supported = False
    for ref in normalized_record["prevention_refs"]:
        candidate = repository / ref
        try:
            resolved = candidate.resolve(strict=True)
        except (FileNotFoundError, OSError):
            findings.append(f"compound:prevention-ref-missing:{ref}")
            continue
        try:
            resolved.relative_to(repository)
        except ValueError:
            findings.append(f"compound:prevention-ref-outside-root:{ref}")
            continue
        if not resolved.is_file():
            findings.append(f"compound:prevention-ref-not-file:{ref}")
            continue

        relative = Path(ref)
        parts = relative.parts
        is_regression = bool(
            parts
            and (
                parts[0] == "tests"
                or (
                    parts[0] == "scripts"
                    and relative.suffix == ".py"
                    and relative.name.startswith("test_")
                )
            )
        )
        is_gate = relative.suffix == ".py" and relative.name.endswith("_gate.py")
        is_task = (
            len(parts) >= 4
            and parts[:3] == ("agents", "lead_engineer", "tasks")
            and relative.suffix.lower() == ".md"
        )
        if is_regression or is_gate or is_task:
            supported = True
            continue

        if parts and parts[0] == "reviews":
            accepted, watch_findings = _accepted_watch_findings(
                resolved,
                ref,
                current_work_ids=accepted_work_ids,
            )
            supported = supported or accepted
            findings.extend(watch_findings)

    if not supported:
        findings.append("compound:prevention-destination-unsupported")
    return list(dict.fromkeys(findings))


def _string_field(payload: dict[str, Any], field: str) -> str:
    value = _normalized_text(payload.get(field))
    limit = TEXT_LIMITS[field]
    if not value:
        raise CompoundRecordError(f"compound:missing-{field}")
    if len(value) > limit:
        raise CompoundRecordError(f"compound:{field}-oversized:{len(value)}>{limit}")
    if _secret_like(value):
        raise CompoundRecordError(f"compound:{field}-secret-like")
    return value


def _list_field(payload: dict[str, Any], field: str, normalizer: Any) -> list[str]:
    value = payload.get(field)
    if not isinstance(value, list) or not value:
        raise CompoundRecordError(f"compound:missing-{field}")
    if len(value) > MAX_REFS:
        raise CompoundRecordError(f"compound:{field}-oversized:{len(value)}>{MAX_REFS}")
    return list(dict.fromkeys(normalizer(item) for item in value))


def _parse_created_at(value: object) -> datetime:
    text = str(value or "").strip()
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00" if text.endswith("Z") else text)
    except ValueError as exc:
        raise CompoundRecordError("compound:invalid-created-at") from exc
    if parsed.tzinfo is None:
        raise CompoundRecordError("compound:created-at-missing-timezone")
    return parsed


def _record_content(payload: dict[str, Any]) -> dict[str, Any]:
    return {field: payload[field] for field in sorted(RECORD_FIELDS - {"id"})}


def record_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(_record_content(payload))).hexdigest()


def validate_record(payload: object, *, path: Path | None = None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise CompoundRecordError("compound:record-root-not-object")
    unknown = sorted(set(payload) - RECORD_FIELDS)
    missing = sorted(RECORD_FIELDS - set(payload))
    findings = [f"compound:unknown-field:{field}" for field in unknown]
    findings.extend(f"compound:missing-field:{field}" for field in missing)
    if findings:
        raise CompoundRecordError(findings)
    if payload.get("schema") != RECORD_SCHEMA:
        raise CompoundRecordError("compound:invalid-schema")

    record_id = str(payload.get("id") or "")
    if not RECORD_ID_RE.fullmatch(record_id):
        raise CompoundRecordError(f"compound:invalid-id:{record_id or 'empty'}")
    created = _parse_created_at(payload["created_at"])
    normalized: dict[str, Any] = {
        "schema": RECORD_SCHEMA,
        "id": record_id,
        "created_at": created.isoformat(timespec="seconds"),
        "created_by": _string_field(payload, "created_by"),
        "title": _string_field(payload, "title"),
        "summary": _string_field(payload, "summary"),
        "cause": _string_field(payload, "cause"),
        "prevention": _string_field(payload, "prevention"),
        "work_ids": _list_field(payload, "work_ids", normalize_work_id),
        "defect_signatures": _list_field(
            payload, "defect_signatures", normalize_signature
        ),
        "source_refs": _list_field(payload, "source_refs", normalize_ref),
        "prevention_refs": _list_field(payload, "prevention_refs", normalize_ref),
        "verification_refs": _list_field(
            payload, "verification_refs", normalize_ref
        ),
    }
    recurrence = payload.get("recurrence_count")
    if isinstance(recurrence, bool) or not isinstance(recurrence, int) or recurrence < 1:
        raise CompoundRecordError("compound:invalid-recurrence-count")
    normalized["recurrence_count"] = recurrence
    status = str(payload.get("status") or "").strip().lower()
    if status not in STATUS_VALUES:
        raise CompoundRecordError(f"compound:invalid-status:{status or 'empty'}")
    normalized["status"] = status

    digest = record_digest(normalized)
    if not record_id.endswith("-" + digest[:12]):
        raise CompoundRecordError(f"compound:id-content-digest-mismatch:{record_id}")
    if path is not None and path.name != record_id + ".json":
        raise CompoundRecordError(f"compound:id-filename-mismatch:{path.name}")
    return normalized


def records_dir(root: Path) -> Path:
    return Path(root).resolve() / RECORDS_REL


def index_path(root: Path) -> Path:
    return Path(root).resolve() / INDEX_REL


def _atomic_replace(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            try:
                os.fsync(handle.fileno())
            except OSError:
                pass
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _atomic_create(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            try:
                os.fsync(handle.fileno())
            except OSError:
                pass
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise CompoundRecordError(f"compound:record-already-exists:{path.name}") from exc
        except (AttributeError, NotImplementedError, PermissionError):
            try:
                target = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            except FileExistsError as exc:
                raise CompoundRecordError(
                    f"compound:record-already-exists:{path.name}"
                ) from exc
            with os.fdopen(target, "wb") as handle:
                handle.write(data)
                handle.flush()
                try:
                    os.fsync(handle.fileno())
                except OSError:
                    pass
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def load_records(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    directory = records_dir(root)
    if not directory.exists():
        return []
    paths = sorted(directory.glob("COMPOUND-*.json"))
    if len(paths) > MAX_RECORDS:
        raise CompoundRecordError(f"compound:too-many-records:{len(paths)}>{MAX_RECORDS}")
    records: list[tuple[Path, dict[str, Any]]] = []
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CompoundRecordError(f"compound:invalid-json:{path.name}:{exc}") from exc
        records.append((path, validate_record(payload, path=path)))
    return records


def _index_entry(root: Path, path: Path, record: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": record["id"],
        "path": path.resolve().relative_to(Path(root).resolve()).as_posix(),
        "created_at": record["created_at"],
        "title": record["title"],
        "status": record["status"],
        "recurrence_count": record["recurrence_count"],
        "work_ids": record["work_ids"],
        "defect_signatures": record["defect_signatures"],
    }


def build_index(root: Path) -> dict[str, Any]:
    entries = [_index_entry(root, path, record) for path, record in load_records(root)]
    by_work: dict[str, list[str]] = {}
    by_signature: dict[str, list[str]] = {}
    for entry in entries:
        for work_id in entry["work_ids"]:
            by_work.setdefault(work_id, []).append(entry["id"])
        for signature in entry["defect_signatures"]:
            by_signature.setdefault(signature, []).append(entry["id"])
    source_digest = hashlib.sha256(_canonical_json(entries)).hexdigest()
    return {
        "schema": INDEX_SCHEMA,
        "source_digest": f"sha256:{source_digest}",
        "record_count": len(entries),
        "records": entries,
        "by_work": {key: sorted(value) for key, value in sorted(by_work.items())},
        "by_signature": {
            key: sorted(value) for key, value in sorted(by_signature.items())
        },
    }


def write_index(root: Path) -> Path:
    path = index_path(root)
    _atomic_replace(path, _canonical_json(build_index(root)))
    return path


def check_store(root: Path, *, require_index: bool = True) -> list[str]:
    findings: list[str] = []
    try:
        expected = build_index(root)
    except CompoundRecordError as exc:
        return list(exc.findings)
    path = index_path(root)
    if not path.exists():
        if require_index:
            findings.append(f"compound:index-missing:{INDEX_REL.as_posix()}")
        return findings
    try:
        actual = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(f"compound:index-invalid-json:{exc}")
        return findings
    if actual != expected:
        findings.append(f"compound:index-stale:{INDEX_REL.as_posix()}")
    return findings


def create_record(
    root: Path,
    *,
    work_ids: Iterable[object],
    defect_signatures: Iterable[object],
    title: object,
    summary: object,
    cause: object,
    prevention: object,
    source_refs: Iterable[object],
    prevention_refs: Iterable[object],
    verification_refs: Iterable[object],
    recurrence_count: int = 1,
    status: str = "active",
    created_by: object = "compound_record.py",
    created_at: str | None = None,
    update_index: bool = True,
) -> tuple[Path, dict[str, Any]]:
    moment = (
        _parse_created_at(created_at)
        if created_at
        else datetime.now(timezone.utc).astimezone()
    )
    draft: dict[str, Any] = {
        "schema": RECORD_SCHEMA,
        "created_at": moment.isoformat(timespec="seconds"),
        "created_by": _normalized_text(created_by),
        "title": _normalized_text(title),
        "summary": _normalized_text(summary),
        "cause": _normalized_text(cause),
        "prevention": _normalized_text(prevention),
        "work_ids": [normalize_work_id(item) for item in work_ids],
        "defect_signatures": normalize_signatures(defect_signatures),
        "recurrence_count": recurrence_count,
        "status": str(status).strip().lower(),
        "source_refs": [normalize_ref(item) for item in source_refs],
        "prevention_refs": [normalize_ref(item) for item in prevention_refs],
        "verification_refs": [normalize_ref(item) for item in verification_refs],
    }
    digest = record_digest(draft)
    slug = re.sub(r"[^a-z0-9]+", "-", draft["title"].lower()).strip("-")[:48]
    slug = slug.rstrip("-") or "lesson"
    timestamp = moment.strftime("%Y%m%d-%H%M%S")
    draft["id"] = f"COMPOUND-{timestamp}-{slug}-{digest[:12]}"
    record = validate_record(draft)
    path = records_dir(root) / f"{record['id']}.json"
    _atomic_create(path, _canonical_json(record))
    if update_index:
        write_index(root)
    return path, record


def record_ref(root: Path, path: Path) -> str:
    return path.resolve().relative_to(Path(root).resolve()).as_posix()


def load_record_ref(root: Path, ref: object) -> tuple[Path, dict[str, Any]]:
    normalized = normalize_ref(ref)
    expected_prefix = RECORDS_REL.as_posix() + "/"
    if not normalized.startswith(expected_prefix):
        raise CompoundRecordError(f"compound:ref-outside-record-store:{normalized}")
    path = Path(root).resolve() / normalized
    if not path.is_file():
        raise CompoundRecordError(f"compound:record-ref-missing:{normalized}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CompoundRecordError(f"compound:invalid-json:{normalized}:{exc}") from exc
    return path, validate_record(payload, path=path)


def record_links(
    record: dict[str, Any],
    *,
    work_ids: Iterable[object] = (),
    defect_signatures: Iterable[object] = (),
) -> bool:
    wanted_work = {normalize_work_id(value) for value in work_ids}
    wanted_signatures = set(normalize_signatures(defect_signatures))
    return bool(
        wanted_work.intersection(record["work_ids"])
        or wanted_signatures.intersection(record["defect_signatures"])
    )


def search_records(
    root: Path,
    *,
    work_ids: Iterable[object] = (),
    defect_signatures: Iterable[object] = (),
    keywords: Iterable[object] = (),
    limit: int = 20,
) -> list[dict[str, Any]]:
    wanted_work = {normalize_work_id(item) for item in work_ids}
    wanted_signatures = set(normalize_signatures(defect_signatures))
    wanted_keywords = [
        _normalized_text(item).lower()
        for item in keywords
        if _normalized_text(item)
    ]
    if any(_secret_like(item) for item in wanted_keywords):
        raise CompoundRecordError("compound:search-secret-like")
    limit = max(1, min(int(limit), MAX_SEARCH_RESULTS))
    filtered: list[tuple[int, dict[str, Any]]] = []
    for path, record in load_records(root):
        score = 0
        if wanted_work.intersection(record["work_ids"]):
            score += 100
        if wanted_signatures.intersection(record["defect_signatures"]):
            score += 80
        haystack = " ".join(
            str(record[field]).lower()
            for field in ("title", "summary", "cause", "prevention")
        )
        score += sum(haystack.count(keyword) for keyword in wanted_keywords)
        if (wanted_work or wanted_signatures or wanted_keywords) and score == 0:
            continue
        filtered.append(
            (
                score,
                {
                    **_index_entry(root, path, record),
                    "score": score,
                    "legacy": False,
                },
            )
        )
    filtered.sort(
        key=lambda pair: (
            -pair[0],
            -pair[1]["recurrence_count"],
            pair[1]["created_at"],
            pair[1]["id"],
        )
    )
    return [entry for _score, entry in filtered[:limit]]


def search_legacy(
    root: Path, *, keywords: Iterable[object] = (), limit: int = 20
) -> list[dict[str, Any]]:
    path = Path(root).resolve() / LEGACY_REL
    if not path.is_file():
        return []
    terms = [_normalized_text(item).lower() for item in keywords if _normalized_text(item)]
    if any(_secret_like(term) for term in terms):
        raise CompoundRecordError("compound:legacy-search-secret-like")
    text = path.read_text(encoding="utf-8", errors="replace")
    chunks = re.split(
        r"(?=^#{2,3}\s+COMPOUND-[^\n]+)", text, flags=re.MULTILINE
    )
    rows: list[dict[str, Any]] = []
    for chunk in chunks:
        heading = chunk.strip().splitlines()[0] if chunk.strip() else ""
        match = re.match(r"^#{2,3}\s+(COMPOUND-[^:\s]+)(?::\s*(.*))?$", heading)
        if not match:
            continue
        lowered = chunk.lower()
        score = sum(lowered.count(term) for term in terms)
        if terms and score == 0:
            continue
        rows.append(
            {
                "id": match.group(1),
                "path": LEGACY_REL.as_posix(),
                "title": _normalized_text(match.group(2) or match.group(1))[:160],
                "score": score,
                "legacy": True,
            }
        )
    rows.sort(key=lambda row: (-row["score"], row["id"]))
    return rows[: max(1, min(int(limit), MAX_SEARCH_RESULTS))]


def search_knowledge(
    root: Path,
    *,
    work_ids: Iterable[object] = (),
    defect_signatures: Iterable[object] = (),
    keywords: Iterable[object] = (),
    include_legacy: bool = True,
    limit: int = 20,
) -> list[dict[str, Any]]:
    work_values = list(work_ids)
    signature_values = list(defect_signatures)
    keyword_values = list(keywords)
    rows = search_records(
        root,
        work_ids=work_values,
        defect_signatures=signature_values,
        keywords=keyword_values,
        limit=limit,
    )
    if include_legacy and len(rows) < limit:
        legacy_terms = [*work_values, *signature_values, *keyword_values]
        rows.extend(
            search_legacy(root, keywords=legacy_terms, limit=limit - len(rows))
        )
    return rows[:limit]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create, validate, index, and search task-linked compound records"
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)

    signature = sub.add_parser("signature", help="Normalize explicit defect signatures")
    signature.add_argument("values", nargs="+")

    create = sub.add_parser("create", help="Atomically create one compound record")
    create.add_argument("--work-id", action="append", required=True)
    create.add_argument("--signature", action="append", required=True)
    create.add_argument("--title", required=True)
    create.add_argument("--summary", required=True)
    create.add_argument("--cause", required=True)
    create.add_argument("--prevention", required=True)
    create.add_argument("--source-ref", action="append", required=True)
    create.add_argument("--prevention-ref", action="append", required=True)
    create.add_argument("--verification-ref", action="append", required=True)
    create.add_argument("--recurrence-count", type=int, default=1)
    create.add_argument("--status", choices=sorted(STATUS_VALUES), default="active")
    create.add_argument("--created-by", default="compound_record.py")
    create.add_argument("--created-at")
    create.add_argument("--no-index", action="store_true")

    index = sub.add_parser("index", help="Write or check the generated index")
    index.add_argument("--check", action="store_true")

    check = sub.add_parser("check", help="Validate all records and the index")
    check.add_argument("--allow-missing-index", action="store_true")

    search = sub.add_parser("search", help="Search canonical records and legacy fallback")
    search.add_argument("--work-id", action="append", default=[])
    search.add_argument("--signature", action="append", default=[])
    search.add_argument("--keyword", action="append", default=[])
    search.add_argument("--no-legacy", action="store_true")
    search.add_argument("--limit", type=int, default=20)
    search.add_argument("--json", action="store_true")
    return parser


def _render_rows(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "compound-record: no matches"
    lines = ["ID | SCORE | SOURCE | TITLE", "---|---:|---|---"]
    for row in rows:
        source = "legacy" if row.get("legacy") else "record"
        lines.append(
            f"{row['id']} | {row.get('score', 0)} | {source} | {row.get('title', '')}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "signature":
            for value in args.values:
                print(normalize_signature(value))
            return 0
        if args.command == "create":
            path, record = create_record(
                root,
                work_ids=args.work_id,
                defect_signatures=args.signature,
                title=args.title,
                summary=args.summary,
                cause=args.cause,
                prevention=args.prevention,
                source_refs=args.source_ref,
                prevention_refs=args.prevention_ref,
                verification_refs=args.verification_ref,
                recurrence_count=args.recurrence_count,
                status=args.status,
                created_by=args.created_by,
                created_at=args.created_at,
                update_index=not args.no_index,
            )
            print(
                json.dumps(
                    {
                        "status": "created",
                        "path": record_ref(root, path),
                        "record": record,
                        "index": INDEX_REL.as_posix() if not args.no_index else "",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        if args.command == "index":
            if args.check:
                findings = check_store(root)
                status = "pass" if not findings else "fail"
                print(f"compound-index: {status}")
                for finding in findings:
                    print(f"- {finding}")
                return 0 if not findings else 1
            path = write_index(root)
            print(f"compound-index: wrote {record_ref(root, path)}")
            return 0
        if args.command == "check":
            findings = check_store(
                root, require_index=not args.allow_missing_index
            )
            status = "pass" if not findings else "fail"
            print(f"compound-record: {status}")
            for finding in findings:
                print(f"- {finding}")
            return 0 if not findings else 1
        if args.command == "search":
            rows = search_knowledge(
                root,
                work_ids=args.work_id,
                defect_signatures=args.signature,
                keywords=args.keyword,
                include_legacy=not args.no_legacy,
                limit=args.limit,
            )
            print(
                json.dumps(rows, ensure_ascii=False, indent=2)
                if args.json
                else _render_rows(rows)
            )
            return 0
    except (CompoundRecordError, OSError) as exc:
        findings = exc.findings if isinstance(exc, CompoundRecordError) else (str(exc),)
        print("compound-record: fail")
        for finding in findings:
            print(f"- {finding}")
        return 1
    return 2


__all__ = [
    "CompoundRecordError",
    "INDEX_REL",
    "INDEX_SCHEMA",
    "LEGACY_REL",
    "RECORDS_REL",
    "RECORD_SCHEMA",
    "build_index",
    "check_store",
    "create_record",
    "index_path",
    "load_record_ref",
    "load_records",
    "main",
    "normalize_ref",
    "normalize_signature",
    "normalize_signatures",
    "normalize_work_id",
    "record_digest",
    "record_links",
    "record_ref",
    "records_dir",
    "search_knowledge",
    "search_legacy",
    "search_records",
    "validate_prevention_destinations",
    "validate_record",
    "write_index",
]


if __name__ == "__main__":
    raise SystemExit(main())
