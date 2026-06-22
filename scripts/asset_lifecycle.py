"""Close the DETECT->ACTION gap in asset lifecycle management.

Usage:
  python scripts/asset_lifecycle.py --propose [--root R] [--reuse-threshold 1]
  python scripts/asset_lifecycle.py --apply   [--root R] [--reuse-threshold 1]
  python scripts/asset_lifecycle.py --propose --json ...

The SAFE, REVERSIBLE ladder:
  keep -> observe   (soft "watch closely" demotion — the ONLY auto-transition)

Owner-gated transitions (deprecate, remove) are NEVER performed automatically.
Running --apply twice is a no-op once assets are already in observe.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import runtime_asset_usage  # noqa: E402


REGISTRY_PATH = Path("agents/project/RUNTIME-ASSET-REGISTRY.json")

# Only lifecycle values eligible for auto-demotion source
_DEMOTABLE_LIFECYCLE = {"keep"}
# Only status values eligible for auto-demotion
_DEMOTABLE_STATUS = {"active"}


def _read_registry(root: Path) -> tuple[dict[str, Any] | None, str]:
    """Return (registry_dict, error_message). error_message is empty on success."""
    path = root / REGISTRY_PATH
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"cannot read registry: {exc}"
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, f"registry is not valid JSON: {exc}"
    if not isinstance(payload, dict):
        return None, "registry root must be a JSON object"
    return payload, ""


def _write_registry(root: Path, registry: dict[str, Any]) -> None:
    path = root / REGISTRY_PATH
    path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def propose(root: Path = Path("."), *, reuse_threshold: int = 1) -> list[dict[str, Any]]:
    """Return a list of proposal dicts for assets that should move keep->observe.

    Each proposal dict has:
      asset_id, kind, status, current_lifecycle, proposed_lifecycle, reuse, reason
    """
    root = root.resolve()
    _findings, metrics = runtime_asset_usage.analyze(root)

    # Build a reuse map from metrics
    reuse_by_id: dict[str, int] = {m.asset_id: m.distinct_evidence_hits for m in metrics}

    registry, err = _read_registry(root)
    if registry is None:
        return []

    proposals: list[dict[str, Any]] = []
    for asset in registry.get("assets") or []:
        if not isinstance(asset, dict):
            continue
        asset_id = str(asset.get("id") or "").strip()
        lifecycle = str(asset.get("lifecycle") or "").strip()
        status = str(asset.get("status") or "").strip()
        if lifecycle not in _DEMOTABLE_LIFECYCLE or status not in _DEMOTABLE_STATUS:
            continue
        reuse = reuse_by_id.get(asset_id, 0)
        if reuse > reuse_threshold:
            continue
        proposals.append(
            {
                "asset_id": asset_id,
                "kind": str(asset.get("kind") or "unknown"),
                "status": status,
                "current_lifecycle": lifecycle,
                "proposed_lifecycle": "observe",
                "reuse": reuse,
                "reason": f"reuse={reuse} <= threshold={reuse_threshold}; safe demotion keep->observe",
            }
        )
    return proposals


def apply(root: Path = Path("."), *, reuse_threshold: int = 1) -> dict[str, Any]:
    """Perform keep->observe demotion for qualifying assets. Returns result dict.

    Result keys:
      demoted: list of asset_ids that were transitioned this run
      skipped: list of asset_ids already at observe that met the criteria (idempotent guard)
      note: advisory message about owner-gated transitions
    """
    root = root.resolve()
    _findings, metrics = runtime_asset_usage.analyze(root)
    reuse_by_id: dict[str, int] = {m.asset_id: m.distinct_evidence_hits for m in metrics}

    registry, err = _read_registry(root)
    if registry is None:
        return {"demoted": [], "skipped": [], "note": f"registry read error: {err}"}

    demoted: list[str] = []
    skipped: list[str] = []

    for asset in registry.get("assets") or []:
        if not isinstance(asset, dict):
            continue
        asset_id = str(asset.get("id") or "").strip()
        status = str(asset.get("status") or "").strip()
        lifecycle = str(asset.get("lifecycle") or "").strip()
        reuse = reuse_by_id.get(asset_id, 0)

        # Only consider assets that are (or were) candidates for demotion
        if status not in _DEMOTABLE_STATUS:
            continue
        if reuse > reuse_threshold:
            continue

        if lifecycle == "observe":
            # Already at the target state — idempotent no-op
            skipped.append(asset_id)
        elif lifecycle in _DEMOTABLE_LIFECYCLE:
            asset["lifecycle"] = "observe"
            demoted.append(asset_id)
        # lifecycle in {deprecate, modify, remove} is not touched — owner-gated

    if demoted:
        _write_registry(root, registry)

    return {
        "demoted": demoted,
        "skipped": skipped,
        "note": (
            "deprecate and remove transitions require Owner approval; "
            "this tool only performs the reversible keep->observe demotion."
        ),
    }


def _render_propose(proposals: list[dict[str, Any]], root: Path) -> str:
    if not proposals:
        return "asset-lifecycle: no proposals (all active keep assets have reuse > threshold)"
    lines = [
        f"asset-lifecycle: {len(proposals)} proposal(s)",
        f"root={root}",
        "",
        "Proposed transitions (keep -> observe):",
    ]
    for p in proposals:
        lines.append(
            f"  {p['asset_id']}  kind={p['kind']}  reuse={p['reuse']}  reason: {p['reason']}"
        )
    lines.append("")
    lines.append("NOTE: deprecate/remove transitions require Owner approval and are never auto-applied.")
    return "\n".join(lines)


def _render_apply(result: dict[str, Any], root: Path) -> str:
    demoted = result["demoted"]
    skipped = result["skipped"]
    lines = [
        "asset-lifecycle apply",
        f"root={root}",
        f"demoted={len(demoted)}  skipped={len(skipped)}",
    ]
    for asset_id in demoted:
        lines.append(f"  DEMOTED: {asset_id}  keep -> observe")
    for asset_id in skipped:
        lines.append(f"  SKIPPED: {asset_id}  already at observe (idempotent)")
    lines.append("")
    lines.append(result["note"])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Asset lifecycle: propose or apply reversible keep->observe demotion"
    )
    parser.add_argument("--root", type=Path, default=Path("."), help="Repository root (default: cwd)")
    parser.add_argument("--reuse-threshold", type=int, default=1, dest="reuse_threshold",
                        help="Assets with distinct_evidence_hits <= this value are flagged (default: 1)")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--propose", action="store_true", help="Emit proposals without writing (advisory, exit 0)")
    mode.add_argument("--apply", action="store_true", help="Apply keep->observe demotions to registry")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()

    if args.propose:
        proposals = propose(root=root, reuse_threshold=args.reuse_threshold)
        if args.json:
            print(json.dumps({"proposals": proposals, "count": len(proposals)}, indent=2, ensure_ascii=False))
        else:
            print(_render_propose(proposals, root))
        return 0

    if args.apply:
        result = apply(root=root, reuse_threshold=args.reuse_threshold)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(_render_apply(result, root))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
