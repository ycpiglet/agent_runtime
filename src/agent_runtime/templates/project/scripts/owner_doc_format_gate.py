"""Check Owner-facing docs for the required executive outline contract."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REQUIRED_GROUPS = {
    "summary": (r"^##\s+(Summary|Bottom Line)\b", r"^Bottom Line\b"),
    "signal": (r"^##\s+(Signal|Status|Key Points)\b",),
    "action": (r"^##\s+(Action|Action Items|Action Board)\b",),
    "risk": (r"^##\s+(Risk|Risks|Risks / Blockers|Blockers)\b",),
    "decision": (r"^##\s+Decision\b",),
    "next": (r"^##\s+(Next|Next Steps)\b",),
}

FRONTMATTER_PATTERN = re.compile(r"\A---\r?\n.*?\r?\n---\r?\n", re.DOTALL)
SIGNAL_PATTERN = re.compile(r"^signal:\s*(pass|watch|block)\s*$", re.MULTILINE | re.IGNORECASE)
SCORE_PATTERN = re.compile(r"^score:\s*([0-9]{1,3})\s*$", re.MULTILINE | re.IGNORECASE)


def has_group(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, flags=re.MULTILINE | re.IGNORECASE) for pattern in patterns)


def check_path(path: Path) -> list[str]:
    findings: list[str] = []
    if not path.exists():
        return ["file:missing"]
    text = path.read_text(encoding="utf-8")
    frontmatter = FRONTMATTER_PATTERN.search(text)
    if not frontmatter:
        findings.append("frontmatter:missing")
    else:
        frontmatter_text = frontmatter.group(0)
        if not SIGNAL_PATTERN.search(frontmatter_text):
            findings.append("signal:missing-or-invalid")
        score_match = SCORE_PATTERN.search(frontmatter_text)
        if not score_match:
            findings.append("score:missing")
        else:
            score = int(score_match.group(1))
            if score < 0 or score > 100:
                findings.append("score:out-of-range")
    for group, patterns in REQUIRED_GROUPS.items():
        if not has_group(text, patterns):
            findings.append(f"{group}:missing")
    if len(re.findall(r"^\|.+\|$", text, flags=re.MULTILINE)) < 3:
        findings.append("table:missing-or-too-small")
    return findings


def manifest_paths(path: Path) -> tuple[list[Path], list[str]]:
    if not path.exists():
        return [], [f"manifest:missing:{path}"]
    docs: list[Path] = []
    in_owner_docs = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not raw.startswith((" ", "\t", "-")):
            in_owner_docs = stripped in {"owner_docs:", "owner_docs: []"}
            if stripped == "owner_docs: []":
                in_owner_docs = False
            continue
        if not in_owner_docs:
            continue
        match = re.match(r"^-\s*(?:path:\s*)?(.+?)\s*$", stripped)
        if not match:
            continue
        value = match.group(1).split("#", 1)[0].strip().strip("'\"")
        if value:
            docs.append((path.parent / value).resolve())
    return docs, []


def main() -> int:
    parser = argparse.ArgumentParser(description="Owner document format gate")
    parser.add_argument("paths", nargs="*", help="Markdown files to check")
    parser.add_argument("--manifest", type=Path, help="Manifest with owner_docs entries")
    parser.add_argument("--allow-empty", action="store_true", help="Allow zero candidate docs")
    args = parser.parse_args()

    paths = [Path(raw).resolve() for raw in args.paths]
    manifest_findings: list[str] = []
    if args.manifest:
        manifest_doc_paths, manifest_findings = manifest_paths(args.manifest)
        paths.extend(manifest_doc_paths)

    if not paths and not args.allow_empty:
        print("owner-doc-format: fail: no paths")
        print("findings=1")
        return 1

    total = 0
    for finding in manifest_findings:
        total += 1
        print(f"{args.manifest}: fail: {finding}")
    for path in paths:
        findings = check_path(path)
        if findings:
            total += len(findings)
            print(f"{path}: fail: {', '.join(findings)}")
        else:
            print(f"{path}: pass")
    print(f"findings={total}")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
