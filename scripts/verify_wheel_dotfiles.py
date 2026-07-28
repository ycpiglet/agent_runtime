"""Verify the built wheel ships the templates/project dot-files (TASK-AR-531, GH #121).

setuptools' `package-data` glob silently drops dot-prefixed paths, so a
`pip install agent_runtime` host never received the template wiring
(.gitattributes / .githooks / .github / .codex). This builds a wheel and asserts
those paths ARE present -- a regression guard so a future packaging change cannot
silently drop them again.

    python scripts/verify_wheel_dotfiles.py --check    # build + assert; exit 1 if any missing
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REQUIRED_FILES = [
    "agent_runtime/templates/project/.gitattributes",
    "agent_runtime/templates/project/agents/project/RUNTIME-PROFILE-MANIFEST.json",
    "agent_runtime/templates/project/scripts/work.py",
    "agent_runtime/templates/project/scripts/session_baseline.py",
    "agent_runtime/templates/project/scripts/dirty_intake.py",
    "agent_runtime/templates/project/scripts/save_report.py",
    "agent_runtime/templates/project/scripts/runtime_asset_usage.py",
    "agent_runtime/templates/project/skills/release-conductor/SKILL.md",
    "agent_runtime/templates/project/skills/independent-verification/SKILL.md",
    "agent_runtime/templates/project/skills/work-analytics/SKILL.md",
    "agent_runtime/templates/project/skills/session-closeout/SKILL.md",
    "agent_runtime/templates/project/agents/runtime/session_checkpoints/.gitignore",
]
REQUIRED_SUBTREES = [
    "agent_runtime/templates/project/.githooks/",
    "agent_runtime/templates/project/.github/",
    "agent_runtime/templates/project/.codex/",
]


def build_and_inspect(workdir: Path) -> tuple[list[str], set[str]]:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "wheel", str(ROOT), "--no-deps", "-w", str(workdir)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return [f"build-failed:{result.stderr.strip()[-200:]}"], set()
    wheels = list(workdir.glob("agent_runtime-*.whl"))
    if not wheels:
        return ["no-wheel-built"], set()
    with zipfile.ZipFile(wheels[0]) as archive:
        names = set(archive.namelist())
    findings: list[str] = []
    for required in REQUIRED_FILES:
        if required not in names:
            findings.append(f"missing-file:{required}")
    for subtree in REQUIRED_SUBTREES:
        if not any(name.startswith(subtree) for name in names):
            findings.append(f"missing-subtree:{subtree}")
    return findings, names


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the wheel ships template dot-files (TASK-AR-531)")
    parser.add_argument("--check", action="store_true", help="build the wheel and assert dot-files present")
    parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        findings, names = build_and_inspect(Path(tmp))
    dot_entries = sorted(n for n in names if "templates/project/." in n)
    print(f"verify-wheel-dotfiles: template dot-file entries in wheel: {len(dot_entries)}")
    for name in dot_entries[:10]:
        print(f"  {name}")
    if findings:
        for finding in findings:
            print(f"verify-wheel-dotfiles: fail: {finding}")
        print(f"findings={len(findings)}")
        return 1
    print("verify-wheel-dotfiles: pass")
    print("findings=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
