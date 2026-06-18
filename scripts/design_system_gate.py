"""Design-system governance gate for Agent Runtime UI work.

The default check is baseline-safe: it verifies governance artifacts and scans
added UI diff lines. Explicit ``--path`` / ``--all-ui`` checks scan whole files
and are useful for full debt audits or focused review.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_ARTIFACTS = [
    Path("docs/design/agent-runtime/DESIGN.md"),
    Path("docs/design/agent-runtime/DESIGN-SYSTEM.md"),
    Path("reviews/DIAGNOSTIC-2026-06-18-ui-design-system-maturity.md"),
]
REQUIRED_ROLES = [
    "lead-designer",
    "design-system-steward",
    "interface-designer",
    "ux-evaluator",
]
UI_SUFFIXES = {".css", ".html", ".js", ".jsx", ".ts", ".tsx", ".py"}
UI_PATH_HINTS = (
    "src/agent_runtime/ui_console.py",
    "src/agent_runtime/ui_",
    "public/",
    "web/",
    "components/",
    "src/components/",
    "src/app/",
)
# ``(?<!&)`` keeps HTML numeric character entities (e.g. ``&#9881;`` gear icon,
# ``&#9776;`` menu icon) from being misread as raw hex color literals.
RAW_COLOR_RE = re.compile(r"(?<!&)#[0-9a-fA-F]{3,8}\b")
RAW_SIZE_RE = re.compile(
    r"\b(?:font-size|margin|margin-[a-z]+|padding|padding-[a-z]+|gap|row-gap|column-gap|border-radius)\s*:\s*\d+(?:\.\d+)?px\b"
)


class Finding:
    def __init__(self, code: str, path: str, line: int, message: str) -> None:
        self.code = code
        self.path = path
        self.line = line
        self.message = message


def _repo_paths_from_git(root: Path, args: list[str]) -> list[str]:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return []
    if result.returncode not in (0, 1):
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def changed_paths(root: Path = ROOT) -> list[Path]:
    names = set(_repo_paths_from_git(root, ["diff", "--name-only", "--diff-filter=ACMRTUXB", "HEAD", "--"]))
    names.update(_repo_paths_from_git(root, ["diff", "--cached", "--name-only", "--diff-filter=ACMRTUXB", "--"]))
    return [root / name for name in sorted(names)]


def is_ui_path(path: Path, root: Path = ROOT) -> bool:
    if path.suffix.lower() not in UI_SUFFIXES:
        return False
    try:
        rel = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        rel = path.as_posix()
    return any(rel == hint or rel.startswith(hint) for hint in UI_PATH_HINTS)


def _is_token_definition(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("--") and ":" in stripped


def scan_raw_literals(paths: list[Path], root: Path = ROOT) -> list[Finding]:
    findings: list[Finding] = []
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        try:
            rel = path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            rel = str(path)
        text = path.read_text(encoding="utf-8", errors="replace")
        for idx, line in enumerate(text.splitlines(), start=1):
            if _is_token_definition(line):
                continue
            if RAW_COLOR_RE.search(line):
                findings.append(Finding("raw-color", rel, idx, "raw color literal outside token definition"))
            if RAW_SIZE_RE.search(line):
                findings.append(Finding("raw-size", rel, idx, "raw px literal outside token definition"))
    return findings


def scan_raw_literal_lines(rows: list[tuple[str, int, str]]) -> list[Finding]:
    findings: list[Finding] = []
    for rel, line_no, line in rows:
        if _is_token_definition(line):
            continue
        if RAW_COLOR_RE.search(line):
            findings.append(Finding("raw-color", rel, line_no, "raw color literal outside token definition"))
        if RAW_SIZE_RE.search(line):
            findings.append(Finding("raw-size", rel, line_no, "raw px literal outside token definition"))
    return findings


def _repo_text_from_git(root: Path, args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return ""
    if result.returncode not in (0, 1):
        return ""
    return result.stdout


def added_ui_lines_from_diff(diff_text: str, root: Path = ROOT) -> list[tuple[str, int, str]]:
    rows: list[tuple[str, int, str]] = []
    current_path = ""
    current_ui = False
    new_line = 0
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            target = line[4:].strip()
            current_path = target[2:] if target.startswith("b/") else target
            current_ui = current_path != "/dev/null" and is_ui_path(root / current_path, root)
            continue
        if not current_ui:
            continue
        if line.startswith("@@ "):
            match = re.search(r"\+(\d+)(?:,(\d+))?", line)
            new_line = int(match.group(1)) if match else 0
            continue
        if line.startswith("+") and not line.startswith("+++"):
            rows.append((current_path, new_line, line[1:]))
            new_line += 1
            continue
        if line.startswith("-") and not line.startswith("---"):
            continue
        if new_line:
            new_line += 1
    return rows


def untracked_ui_paths(root: Path = ROOT) -> list[Path]:
    names = _repo_paths_from_git(root, ["ls-files", "--others", "--exclude-standard", "--"])
    return [root / name for name in names if is_ui_path(root / name, root)]


def changed_ui_addition_findings(root: Path = ROOT) -> tuple[list[Finding], int]:
    diff_text = _repo_text_from_git(root, ["diff", "--unified=0", "--no-ext-diff", "HEAD", "--"])
    diff_text += _repo_text_from_git(root, ["diff", "--cached", "--unified=0", "--no-ext-diff", "--"])
    rows = added_ui_lines_from_diff(diff_text, root)
    findings = scan_raw_literal_lines(rows)
    untracked = untracked_ui_paths(root)
    findings.extend(scan_raw_literals(untracked, root))
    scanned_paths = {row[0] for row in rows}
    scanned_paths.update(
        path.resolve().relative_to(root.resolve()).as_posix()
        if path.resolve().is_relative_to(root.resolve())
        else path.as_posix()
        for path in untracked
    )
    return findings, len(scanned_paths)


def artifact_findings(root: Path = ROOT) -> list[Finding]:
    findings: list[Finding] = []
    for rel in REQUIRED_ARTIFACTS:
        if not (root / rel).exists():
            findings.append(Finding("missing-artifact", rel.as_posix(), 0, "required design-system artifact missing"))
    return findings


def role_findings(root: Path = ROOT) -> list[Finding]:
    sys.path.insert(0, str(root / "scripts"))
    from org_model_gate import load_registry, resolve_owner  # noqa: WPS433

    reg = load_registry(root / "agents" / "project" / "ORG-MODEL.yml")
    findings: list[Finding] = []
    for role in REQUIRED_ROLES:
        resolved = resolve_owner(role, reg)
        if not resolved or resolved.get("id") != role:
            findings.append(Finding("missing-role", "agents/project/ORG-MODEL.yml", 0, f"{role} role missing"))
    legacy = resolve_owner("uiux", reg)
    if not legacy:
        findings.append(Finding("missing-legacy-alias", "agents/project/ORG-MODEL.yml", 0, "uiux alias no longer resolves"))
    return findings


def cmd_check(
    *,
    root: Path = ROOT,
    paths: list[str] | None = None,
    all_ui: bool = False,
    json_output: bool = False,
) -> int:
    findings = []
    findings.extend(artifact_findings(root))
    findings.extend(role_findings(root))

    if paths:
        scan_paths = [Path(p) if Path(p).is_absolute() else root / p for p in paths]
    elif all_ui:
        scan_paths = [p for p in root.rglob("*") if is_ui_path(p, root)]
        findings.extend(scan_raw_literals(scan_paths, root))
    else:
        diff_findings, scanned_count = changed_ui_addition_findings(root)
        scan_paths = [Path(f"<diff:{scanned_count}>")] * scanned_count
        findings.extend(diff_findings)

    if paths:
        findings.extend(scan_raw_literals(scan_paths, root))

    payload = {
        "status": "fail" if findings else "pass",
        "checked_artifacts": len(REQUIRED_ARTIFACTS),
        "checked_roles": len(REQUIRED_ROLES),
        "scanned": len(scan_paths),
        "findings": [finding.__dict__ for finding in findings],
    }
    if json_output:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        for finding in findings:
            loc = f"{finding.path}:{finding.line}" if finding.line else finding.path
            print(f"design-system-gate: {finding.code}: {loc}: {finding.message}")
        print(
            "design-system-gate: "
            f"{payload['status']} artifacts={payload['checked_artifacts']} "
            f"roles={payload['checked_roles']} scanned={payload['scanned']} "
            f"findings={len(findings)}"
        )
    return 1 if findings else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Design-system governance gate")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--all-ui", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    return cmd_check(paths=args.path, all_ui=args.all_ui, json_output=args.json)


if __name__ == "__main__":
    raise SystemExit(main())
