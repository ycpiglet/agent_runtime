"""Check compact-v1 owner reports and the historical executive outline."""

from __future__ import annotations

import argparse
import html
import json
import re
import unicodedata
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
LAYOUT_PATTERN = re.compile(r"^[ \t]*report_layout:[ \t]*(.*?)[ \t]*$", re.MULTILINE | re.IGNORECASE)
PROFILE_KEY_PATTERN = re.compile(r"^[ \t]*[\"']?report_layout\b", re.MULTILINE | re.IGNORECASE)
COMPACT_SECTIONS = ("현재 상태", "다음 행동", "한도와 미확인", "검증 근거")
COMPACT_METADATA_KEYS = {"report_layout", "signal", "score", "score_source"}


def compact_metadata_findings(frontmatter: str) -> list[str]:
    """Reject key aliases that the host's scalar parser would strip/overwrite."""
    findings = []
    seen = set()
    for line in frontmatter.splitlines():
        raw_key, separator, _ = line.partition(":")
        key = raw_key.strip().strip("'\"").lower()
        if not separator or key not in COMPACT_METADATA_KEYS:
            continue
        if raw_key != key:
            findings.append(f"compact:metadata-noncanonical:{key}")
        if key in seen:
            findings.append(f"compact:metadata-duplicate:{key}")
        seen.add(key)
    return findings


def has_unescaped_bracket(text: str) -> bool:
    escaped = False
    for char in text:
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char in "[]":
            return True
    return False


def check_compact(frontmatter: str, body: str) -> list[str]:
    """The first layer is deliberately a small, visible, line-based grammar."""
    findings: list[str] = compact_metadata_findings(frontmatter)
    compact_signal = re.compile(r"^signal:[ \t]*(pass|watch|block)[ \t]*$", re.MULTILINE)
    signals = compact_signal.findall(frontmatter)
    signal_match = compact_signal.search(frontmatter)
    if len(signals) != 1 or len(re.findall(r"^signal:", frontmatter, flags=re.MULTILINE | re.IGNORECASE)) != 1:
        findings.append("signal:missing-or-invalid")
    score_fields = re.findall(r"^score:", frontmatter, flags=re.MULTILINE | re.IGNORECASE)
    if score_fields:
        score_match = SCORE_PATTERN.search(frontmatter)
        if not score_match or len(score_fields) != 1:
            findings.append("score:invalid")
        elif int(score_match.group(1)) > 100:
            findings.append("score:out-of-range")
        sources = re.findall(r"^score_source:[ \t]*(.*?)[ \t]*$", frontmatter, flags=re.MULTILINE)
        valid_source = len(sources) == 1 and bool(sources[0].strip())
        if valid_source and sources[0].startswith('"'):
            try:
                value = json.loads(sources[0])
                valid_source = isinstance(value, str) and bool(value.strip())
            except ValueError:
                valid_source = False
        if not valid_source or sources[0] in {"''", "null", "~"}:
            findings.append("score:source-required")

    section_matches = list(re.finditer(r"^## (.+)$", body, flags=re.MULTILINE))
    headings = [match.group(1) for match in section_matches]
    if headings != list(COMPACT_SECTIONS):
        return findings + ["compact:sections-missing-or-out-of-order"]
    first_layer = body[:section_matches[3].start()]
    if len(first_layer.strip("\r\n")) > 1200:
        findings.append("compact:first-layer-too-long")
    if has_unescaped_bracket(first_layer) or re.search(r"<|(?<!\\)`|(?<!\\)~{3}|^\s*\|", first_layer, flags=re.MULTILINE):
        findings.append("compact:hidden-or-dense-content")
    # Markdown entities decode once when displayed. Do not recursively decode
    # escaped literals such as &amp;#8238; into active bidi controls.
    visible_text = "".join(html.unescape(line) for line in first_layer.replace("\r\n", "\n").split("\n"))
    if any(unicodedata.category(char).startswith("C") or char in "\u2028\u2029" for char in visible_text):
        findings.append("compact:hidden-or-dense-content")

    intro = body[:section_matches[0].start()]
    intro_lines = [line for line in intro.splitlines() if line.strip()]
    if len(intro_lines) != 2 or not re.fullmatch(r"# .{1,70}", intro_lines[0]):
        findings.append("compact:title-invalid")
    if len(intro_lines) != 2 or not re.fullmatch(r"> \*\*\S(?:.*\S)?\*\*", intro_lines[-1]):
        findings.append("compact:summary-invalid")
    elif len(intro_lines[-1][4:-2]) > 140:
        findings.append("compact:summary-too-long")

    statuses, actions, limits = (
        body[start.end():end.start()]
        for start, end in zip(section_matches, section_matches[1:])
    )
    groups = (("statuses", statuses, 3), ("next", actions, 2), ("limits", limits, 3))
    state_labels = []
    for name, content, maximum in groups:
        lines = [line for line in content.splitlines() if line.strip()]
        if not 1 <= len(lines) <= maximum:
            findings.append(f"compact:{name}-count")
        for line in lines:
            if not re.fullmatch(r"- \S(?:.*\S)?", line):
                findings.append(f"compact:{name}-invalid")
            if name == "statuses":
                match = re.fullmatch(r"- \*\*(완료|진행 중|차단|미확인|미실행)\*\* · \S(?:.*\S)?: \S(?:.*\S)?", line)
                if not match:
                    findings.append("compact:state-label-invalid")
                else:
                    state_labels.append(match.group(1))
    if signal_match:
        signal = signal_match.group(1).lower()
        if ("차단" in state_labels and signal != "block") or (
            any(state != "완료" for state in state_labels) and signal == "pass"
        ):
            findings.append("compact:signal-understates-state")
    return findings


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
        if text.startswith("---") and PROFILE_KEY_PATTERN.search(text):
            findings.append("report_layout:unknown-or-invalid")
    else:
        frontmatter_text = frontmatter.group(0)
        layouts = LAYOUT_PATTERN.findall(frontmatter_text)
        if PROFILE_KEY_PATTERN.search(frontmatter_text):
            if layouts != ["compact-v1"]:
                return ["report_layout:unknown-or-invalid"]
            return check_compact(frontmatter_text, text[frontmatter.end():])
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
