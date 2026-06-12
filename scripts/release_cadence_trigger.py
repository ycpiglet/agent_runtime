"""Release cadence trigger: watch-only release proposal (TASK-AR-510).

Detects release timing by trigger instead of human memory. When accumulated
change since the latest release tag exceeds thresholds, emits a NON-BLOCKING
``release-cadence:proposal`` watch finding with a recommended version bump.

Boundaries:
- ``--check`` always exits 0 (watch-only) and stays silent below thresholds.
- Never mutates state: no version bump, tag, push, publish, or release.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_COMMITS_THRESHOLD = 40
DEFAULT_FEAT_THRESHOLD = 5
DEFAULT_DAYS_THRESHOLD = 14

FINDING = "release-cadence:proposal"
MUTATION_BOUNDARY = "no version bump, tag, push, publish, or release execution"

SEMVER_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)")
CONVENTIONAL_RE = re.compile(r"^(?P<type>[a-z]+)(?:\([^)]*\))?!?:")


def _ascii(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def _git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def _latest_tag(root: Path) -> str | None:
    out = _git(root, "describe", "--tags", "--abbrev=0")
    tag = (out or "").strip()
    return tag or None


def _commit_subjects(root: Path, tag: str) -> list[str]:
    out = _git(root, "log", "--format=%s", f"{tag}..HEAD")
    if not out:
        return []
    return [line for line in out.splitlines() if line.strip()]


def _commit_count(root: Path, tag: str) -> int:
    out = _git(root, "rev-list", "--count", f"{tag}..HEAD")
    try:
        return int((out or "").strip())
    except ValueError:
        return 0


def _days_since_tag(root: Path, tag: str, *, now_ts: float | None = None) -> int:
    out = _git(root, "log", "-1", "--format=%ct", tag)
    try:
        tag_ts = int((out or "").strip())
    except ValueError:
        return 0
    now = now_ts if now_ts is not None else time.time()
    return max(0, int((now - tag_ts) // 86400))


def _conventional_counts(subjects: list[str]) -> dict[str, int]:
    counts = {"feat": 0, "fix": 0}
    for subject in subjects:
        match = CONVENTIONAL_RE.match(subject.strip())
        if match and match.group("type") in counts:
            counts[match.group("type")] += 1
    return counts


def _bump_reasons(root: Path, tag: str) -> list[str]:
    """Minor heuristic: template deletions/renames or any schemas/** change."""
    reasons: list[str] = []
    out = _git(root, "diff", "--name-status", f"{tag}..HEAD", "--", "src/agent_runtime/templates/")
    for line in (out or "").splitlines():
        parts = line.split("\t")
        status = parts[0].strip()
        if status[:1] in {"D", "R"} and len(parts) > 1:
            reasons.append(f"template-deleted-or-renamed:{parts[-1]}")
    out = _git(root, "diff", "--name-only", f"{tag}..HEAD", "--", "schemas/")
    for line in (out or "").splitlines():
        name = line.strip()
        if name:
            reasons.append(f"schema-changed:{name}")
    return reasons


def _package_version(root: Path) -> str | None:
    try:
        text = (root / "pyproject.toml").read_text(encoding="utf-8")
    except OSError:
        return None
    match = re.search(r"(?m)^version\s*=\s*[\"']([^\"']+)[\"']", text)
    return match.group(1) if match else None


def _bump_version(version: str | None, bump: str) -> str | None:
    if not version:
        return None
    match = SEMVER_RE.match(version)
    if not match:
        return None
    major, minor, patch = (int(part) for part in match.groups())
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def _load_steward() -> Any | None:
    """Reuse release_version_consistency_steward's bump-target file list."""
    try:
        import release_version_consistency_steward as steward

        return steward
    except ImportError:
        pass
    try:
        from scripts import release_version_consistency_steward as steward

        return steward
    except ImportError:
        return None


def _bump_targets(root: Path) -> list[str]:
    targets = ["pyproject.toml"]
    steward = _load_steward()
    if steward is not None:
        for record in steward.build_report(root).get("release_versions", []):
            path = record.get("path")
            if path and path not in targets:
                targets.append(path)
    return targets


def build_report(
    root: Path,
    *,
    commits_threshold: int = DEFAULT_COMMITS_THRESHOLD,
    feat_threshold: int = DEFAULT_FEAT_THRESHOLD,
    days_threshold: int = DEFAULT_DAYS_THRESHOLD,
    now_ts: float | None = None,
) -> dict[str, Any]:
    thresholds = {
        "commits": commits_threshold,
        "feat": feat_threshold,
        "days": days_threshold,
    }
    base: dict[str, Any] = {
        "schema": "agent-runtime-release-cadence/v1",
        "thresholds": thresholds,
        "mutation_boundary": MUTATION_BOUNDARY,
    }

    tag = _latest_tag(root)
    if tag is None:
        base.update(
            {
                "status": "pass",
                "triggered": False,
                "finding": None,
                "reason": "no-baseline-tag",
                "baseline_tag": None,
                "metrics": None,
            }
        )
        return base

    subjects = _commit_subjects(root, tag)
    commits = _commit_count(root, tag)
    counts = _conventional_counts(subjects)
    days = _days_since_tag(root, tag, now_ts=now_ts)
    metrics = {
        "commits": commits,
        "feat": counts["feat"],
        "fix": counts["fix"],
        "days_since_tag": days,
    }

    trigger_reasons: list[str] = []
    if commits > 0:
        if commits >= commits_threshold:
            trigger_reasons.append(f"commits>={commits_threshold} (actual {commits})")
        if counts["feat"] >= feat_threshold:
            trigger_reasons.append(f"feat>={feat_threshold} (actual {counts['feat']})")
        if days >= days_threshold:
            trigger_reasons.append(f"days>={days_threshold} (actual {days})")
    triggered = bool(trigger_reasons)

    bump_reasons = _bump_reasons(root, tag)
    recommended_bump = "minor" if bump_reasons else "patch"
    current_version = _package_version(root)
    recommended_version = _bump_version(current_version, recommended_bump)

    base.update(
        {
            "status": "watch" if triggered else "pass",
            "triggered": triggered,
            "finding": FINDING if triggered else None,
            "baseline_tag": tag,
            "metrics": metrics,
            "trigger_reasons": trigger_reasons,
            "recommended_bump": recommended_bump if triggered else None,
            "current_version": current_version,
            "recommended_version": recommended_version if triggered else None,
            "bump_reasons": bump_reasons,
            "bump_targets": _bump_targets(root),
        }
    )
    return base


def _print_report(report: dict[str, Any], *, verbose: bool) -> None:
    thresholds = report["thresholds"]
    threshold_text = (
        f"commits>={thresholds['commits']} feat>={thresholds['feat']} days>={thresholds['days']}"
    )
    if not report["triggered"]:
        if not verbose:
            return
        if report.get("reason") == "no-baseline-tag":
            print(_ascii("release-cadence: pass no-baseline-tag (no tag found; nothing to compare)"))
            return
        metrics = report["metrics"]
        print(
            _ascii(
                "release-cadence: pass below-thresholds"
                f" tag={report['baseline_tag']} commits={metrics['commits']}"
                f" feat={metrics['feat']} fix={metrics['fix']} days={metrics['days_since_tag']}"
                f" (thresholds {threshold_text})"
            )
        )
        return

    metrics = report["metrics"]
    print(
        _ascii(
            f"release-cadence: watch finding={report['finding']}"
            f" recommended_bump={report['recommended_bump']}"
            f" recommended_version={report['recommended_version'] or 'unknown'}"
        )
    )
    print(
        _ascii(
            f"release-cadence: baseline tag={report['baseline_tag']}"
            f" commits={metrics['commits']} feat={metrics['feat']}"
            f" fix={metrics['fix']} days={metrics['days_since_tag']}"
            f" (thresholds {threshold_text})"
        )
    )
    print(_ascii("release-cadence: trigger reasons: " + "; ".join(report["trigger_reasons"])))
    if report["bump_reasons"]:
        print(_ascii("release-cadence: minor bump reasons: " + "; ".join(report["bump_reasons"])))
    print(
        _ascii(
            f"release-cadence: current version={report['current_version'] or 'unknown'}"
            " source=pyproject.toml"
        )
    )
    print(_ascii("release-cadence: bump targets: " + ", ".join(report["bump_targets"])))
    print(_ascii(f"release-cadence: non-blocking watch; {MUTATION_BOUNDARY}"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Release cadence trigger (watch-only)")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--check", action="store_true", help="watch-only mode; always exit 0")
    parser.add_argument("--verbose", action="store_true", help="print metrics even below thresholds")
    parser.add_argument("--json", action="store_true", help="print full JSON payload")
    parser.add_argument("--commits-threshold", type=int, default=DEFAULT_COMMITS_THRESHOLD)
    parser.add_argument("--feat-threshold", type=int, default=DEFAULT_FEAT_THRESHOLD)
    parser.add_argument("--days-threshold", type=int, default=DEFAULT_DAYS_THRESHOLD)
    args = parser.parse_args(argv)

    try:
        report = build_report(
            Path(args.root).resolve(),
            commits_threshold=args.commits_threshold,
            feat_threshold=args.feat_threshold,
            days_threshold=args.days_threshold,
        )
    except Exception as exc:  # noqa: BLE001 - watch-only trigger must not block sessions
        print(_ascii(f"release-cadence: error {type(exc).__name__}: {exc}"), file=sys.stderr)
        return 0 if args.check else 1

    if args.json:
        print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
    else:
        _print_report(report, verbose=args.verbose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
