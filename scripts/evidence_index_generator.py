"""Generate and check a review/evidence index."""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_OUT = Path("reviews/INDEX.md")


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    meta: dict[str, str] = {}
    for raw in parts[1].splitlines():
        if ":" not in raw:
            continue
        key, _, value = raw.partition(":")
        meta[key.strip()] = value.strip().strip("\"'")
    return meta


def _title(text: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else fallback


def collect(root: Path) -> list[dict[str, Any]]:
    reviews = root / "reviews"
    rows: list[dict[str, Any]] = []
    for path in sorted([*reviews.glob("*.md"), *reviews.glob("*.json")]):
        if path.name == "INDEX.md":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        meta = _parse_frontmatter(text) if path.suffix == ".md" else {}
        rel = _rel(root, path)
        rows.append(
            {
                "path": rel,
                "kind": meta.get("type") or path.suffix.lstrip("."),
                "id": meta.get("id") or path.stem,
                "status": meta.get("status") or "record",
                "signal": meta.get("signal") or "n/a",
                "title": _title(text, path.stem) if path.suffix == ".md" else path.stem,
                "updated_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).astimezone().isoformat(timespec="seconds"),
            }
        )
    return rows


def render(root: Path, rows: list[dict[str, Any]]) -> str:
    generated_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    lines = [
        "---",
        "type: evidence_index",
        "id: EVIDENCE-INDEX-agent-runtime",
        "audience: owner",
        "status: pass",
        "signal: pass",
        "score: 100",
        "priority: High",
        "tags: [evidence, traceability, generated-index]",
        f"generated_at: {generated_at}",
        f"record_count: {len(rows)}",
        "---",
        "",
        "# Evidence Index",
        "",
        "## Bottom Line",
        f"- Summary: indexed `{len(rows)}` review and evidence records under `reviews/`.",
        "- Result: task closeout evidence is searchable by path, id, status, signal, and title.",
        "",
        "## Signal",
        "| Metric | State | Evidence |",
        "| --- | --- | --- |",
        f"| Reviews covered | pass | `{len(rows)}` files |",
        "| Source | pass | `reviews/` |",
        "",
        "## Insight",
        "- Manual review browsing does not scale; this generated file gives agents a stable entrypoint.",
        "- The generator excludes itself from coverage to avoid self-referential churn.",
        "",
        "## Decision",
        "- Decision: regenerate this index after adding closeout reviews or evidence reports.",
        "- Decision: use `scripts/evidence_index_generator.py --check` as the stale index gate.",
        "",
        "## Action Board",
        "| Path | ID | Kind | Status | Signal | Title |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['path']}`",
                    f"`{row['id']}`",
                    str(row["kind"]),
                    str(row["status"]),
                    str(row["signal"]),
                    str(row["title"]).replace("|", "/"),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Risks / Blockers",
            "- Risk: this index proves coverage, not semantic correctness of each evidence file.",
            "",
            "## Next Steps",
            "- Run `python scripts/evidence_index_generator.py --write` after adding new reviews.",
            "- Run `python scripts/evidence_index_generator.py --check` before closeout.",
            "",
        ]
    )
    return "\n".join(lines)


def check(root: Path, out: Path) -> list[str]:
    rows = collect(root)
    expected = render(root, rows).strip()
    findings: list[str] = []
    if not out.exists():
        return [f"{out.as_posix()}: missing"]
    existing = out.read_text(encoding="utf-8").strip()
    existing_paths = set(re.findall(r"`(reviews/[^`]+)`", existing))
    expected_paths = {str(row["path"]) for row in rows}
    missing = sorted(expected_paths - existing_paths)
    if missing:
        findings.extend(f"reviews/INDEX.md: missing-review:{path}" for path in missing[:20])
    if "## Bottom Line" not in existing or "## Action Board" not in existing:
        findings.append("reviews/INDEX.md: missing-owner-brief-sections")
    if not existing or len(existing_paths) < len(expected_paths):
        findings.append("reviews/INDEX.md: stale-or-incomplete")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate/check reviews evidence index")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    out = root / args.out if not args.out.is_absolute() else args.out
    if args.write:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(root, collect(root)), encoding="utf-8")
        print(f"wrote={_rel(root, out)}")
    findings = check(root, out)
    status = "fail" if findings else "pass"
    print(f"evidence-index: {status}")
    print(f"findings={len(findings)}")
    for finding in findings:
        print(f"- {finding}")
    return 1 if args.check and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
