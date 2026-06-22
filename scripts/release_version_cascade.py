"""Release version cascade: check/bump the 'current public tag' everywhere at once.

A release version is not one file. The same current-public-tag value is mirrored
across pyproject + __init__, the CLI ``--tag`` defaults, the CI workflow's publish
gates, the release-gate template, the host fixture ``ref``, and two test
constants. A partial bump reds CI in several separate places (this happened three
times during the v0.3.0 cut). This module is the single source of truth for that
coupled set:

  python scripts/release_version_cascade.py --check          # exit 1 if any ref drifts
  python scripts/release_version_cascade.py --write 0.3.2     # bump the whole set
  python scripts/release_version_cascade.py --json

``--write`` also regenerates the host lock fixture when a template digest is in
play (best-effort; see lock_merge_driver). It NEVER tags, pushes, or publishes.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SOURCE_OF_TRUTH = "pyproject.toml"


@dataclass(frozen=True)
class Ref:
    """One file whose text mirrors the current public version (captured group 1)."""

    path: str
    pattern: re.Pattern[str]

    def versions(self, root: Path) -> list[str]:
        try:
            text = (root / self.path).read_text(encoding="utf-8")
        except OSError:
            return []
        return self.pattern.findall(text)


# Quoted "vX.Y.Z" covers every CLI tag default (argparse `default=` and the
# `tag: str =` function defaults in the publish modules).
_CLI_TAG = re.compile(r'"v(\d+\.\d+\.\d+)"')

CASCADE: tuple[Ref, ...] = (
    Ref("pyproject.toml", re.compile(r'(?m)^version = "(\d+\.\d+\.\d+)"')),
    Ref("src/agent_runtime/__init__.py", re.compile(r'__version__ = "(\d+\.\d+\.\d+)"')),
    Ref("src/agent_runtime/cli.py", _CLI_TAG),
    Ref("src/agent_runtime/publish_tag_smoke.py", _CLI_TAG),
    Ref("src/agent_runtime/publish_github_plan.py", _CLI_TAG),
    Ref("src/agent_runtime/publish_github_execute.py", _CLI_TAG),
    Ref("src/agent_runtime/release_preflight.py", _CLI_TAG),
    Ref(".github/workflows/test.yml", re.compile(r"--tag v(\d+\.\d+\.\d+)")),
    Ref("agents/project/RELEASE-GATE-TEMPLATE.yml", re.compile(r"(?m)^version: v(\d+\.\d+\.\d+)")),
    Ref("tests/fixtures/host/agent_runtime.yml", re.compile(r"(?m)^\s*ref: v(\d+\.\d+\.\d+)")),
    Ref("tests/test_inventory_sync_sanitize.py", re.compile(r'CURRENT_RELEASE_VERSION = "(\d+\.\d+\.\d+)"')),
    Ref("tests/test_release_execution_gate.py", re.compile(r'CURRENT_VERSION = "(\d+\.\d+\.\d+)"')),
)


def current_version(root: Path) -> str | None:
    """The source-of-truth version from pyproject.toml."""
    for spec in CASCADE:
        if spec.path == SOURCE_OF_TRUTH:
            found = spec.versions(root)
            return found[0] if found else None
    return None


def check(root: Path) -> list[str]:
    """Return a list of mismatch descriptions; empty means consistent."""
    expected = current_version(root)
    if expected is None:
        return [f"{SOURCE_OF_TRUTH}: no version found (source of truth missing)"]
    mismatches: list[str] = []
    for spec in CASCADE:
        found = spec.versions(root)
        if not found:
            mismatches.append(f"{spec.path}: no version reference matched (format drift?)")
            continue
        bad = sorted({v for v in found if v != expected})
        if bad:
            mismatches.append(f"{spec.path}: has {', '.join(bad)} but expected {expected}")
    return mismatches


def write(root: Path, new_version: str) -> list[str]:
    """Rewrite every cascade ref to ``new_version``. Returns the changed paths."""
    if not re.fullmatch(r"\d+\.\d+\.\d+", new_version):
        raise ValueError(f"not a semver: {new_version!r}")
    changed: list[str] = []
    for spec in CASCADE:
        file = root / spec.path
        try:
            text = file.read_text(encoding="utf-8")
        except OSError:
            continue
        new_text = spec.pattern.sub(lambda m: m.group(0).replace(m.group(1), new_version), text)
        if new_text != text:
            file.write_text(new_text, encoding="utf-8")
            changed.append(spec.path)
    _regenerate_host_lock(root)
    return changed


def _regenerate_host_lock(root: Path) -> None:
    """Best-effort host-lock regen (template digest may have changed)."""
    try:
        sys.path.insert(0, str(root / "scripts"))
        import lock_merge_driver as lmd  # noqa: PLC0415

        host = root / "tests" / "fixtures" / "host"
        if host.exists():
            lmd.regenerate(host)
    except Exception:  # noqa: BLE001 - lock regen is best-effort, never fail the bump
        pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check or bump the release version cascade")
    parser.add_argument("--root", default=str(ROOT))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="exit 1 if any cascade ref drifts")
    mode.add_argument("--write", metavar="VERSION", help="bump every cascade ref to VERSION")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    if args.write:
        changed = write(root, args.write)
        remaining = check(root)
        payload = {"action": "write", "version": args.write, "changed": changed, "mismatches": remaining}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"release-cascade: bumped {len(changed)} files to {args.write}")
            for path in changed:
                print(f"  - {path}")
            if remaining:
                print("release-cascade: WARNING still inconsistent:")
                for m in remaining:
                    print(f"  ! {m}")
        return 1 if remaining else 0

    mismatches = check(root)
    if args.json:
        print(json.dumps({"action": "check", "current": current_version(root), "mismatches": mismatches}, indent=2, sort_keys=True))
    elif mismatches:
        print(f"release-cascade: INCONSISTENT ({len(mismatches)} ref(s)):")
        for m in mismatches:
            print(f"  ! {m}")
    else:
        print(f"release-cascade: consistent at {current_version(root)} across {len(CASCADE)} refs")
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
