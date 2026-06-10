from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _package_version(root: Path) -> str | None:
    text = _read(root / "pyproject.toml")
    match = re.search(r"(?m)^version\s*=\s*[\"']([^\"']+)[\"']", text)
    return match.group(1) if match else None


def _release_versions(root: Path) -> list[dict[str, str]]:
    release_dir = root / "agents" / "project" / "release"
    records: list[dict[str, str]] = []
    if not release_dir.is_dir():
        return records
    for path in sorted(release_dir.glob("*.yml")):
        text = _read(path)
        for match in re.finditer(r"(?m)^\s*(?:version|release_version)\s*:\s*v?([0-9]+\.[0-9]+\.[0-9]+)", text):
            records.append({"path": _rel(root, path), "version": match.group(1)})
    return records


def build_report(root: Path) -> dict[str, Any]:
    package = _package_version(root)
    release_versions = _release_versions(root)
    findings: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    if package is None:
        findings.append({"category": "package-version-missing", "source_path": "pyproject.toml"})
    for record in release_versions:
        if package and record["version"] != package:
            findings.append(
                {
                    "category": "release-version-mismatch",
                    "source_path": record["path"],
                    "package_version": package,
                    "release_version": record["version"],
                    "route": "proposal_doc_reconciliation",
                }
            )
    status = "block" if findings else "pass"
    if not findings and not release_versions:
        status = "watch"
        warnings.append({"category": "release-state-missing", "route": "proposal_doc_reconciliation"})
    return {
        "status": status,
        "route": "proposal_doc_reconciliation" if status != "pass" else "release_consistency_pass",
        "package": package,
        "release_versions": release_versions,
        "findings": findings,
        "warnings": warnings,
        "mutation_boundary": "no version bump, tag, push, publish, or release execution",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Release/version consistency steward")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--out")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    report = build_report(root)
    if args.out:
        out = root / args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"status={report['status']} route={report['route']}")
    return 0 if report["status"] != "block" else 1


if __name__ == "__main__":
    raise SystemExit(main())
