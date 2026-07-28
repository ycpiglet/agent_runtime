from __future__ import annotations

"""Read-only brownfield adoption planning; this module intentionally has no apply path."""

import json
import os
from dataclasses import dataclass
from pathlib import Path

from . import config as _config
from .inventory import adoption_scan, generated_path_root, is_generated_path
from .template_profiles import selected_paths


@dataclass(frozen=True)
class AdoptionAction:
    path: str
    action: str
    ownership: str
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {"path": self.path, "action": self.action, "ownership": self.ownership, "reason": self.reason}


@dataclass(frozen=True)
class AdoptionPlan:
    root: Path
    profiles: tuple[str, ...]
    capabilities: tuple[str, ...]
    scan_strategy: str
    scan_warnings: tuple[str, ...]
    source_paths: tuple[str, ...]
    generated_paths: tuple[str, ...]
    ignored_count: int
    generated_roots: tuple[str, ...]
    assets: tuple[str, ...]
    actions: tuple[AdoptionAction, ...]
    findings: tuple[str, ...]
    config_invalid: bool = False

    @property
    def conflicts(self) -> tuple[AdoptionAction, ...]:
        return tuple(action for action in self.actions if action.action == "conflict")


def _template_root() -> Path:
    return Path(__file__).resolve().parent / "templates" / "project"


def _template_files(profiles: tuple[str, ...] | None = None) -> dict[str, Path]:
    root = _template_root()
    manifest = root / "agents/project/RUNTIME-PROFILE-MANIFEST.json"
    if profiles is not None and not manifest.exists() and root.resolve() == (Path(__file__).resolve().parent / "templates" / "project").resolve():
        raise ValueError("packaged template profile manifest is missing")
    if profiles is not None and manifest.exists():
        return {path.relative_to(root).as_posix(): path for path in selected_paths(root, profiles) if not is_generated_path(path.relative_to(root))}
    files: dict[str, Path] = {}
    for current, directories, names in os.walk(root, followlinks=False):
        current_path = Path(current)
        relative_current = current_path.relative_to(root)
        directories[:] = sorted(
            directory
            for directory in directories
            if directory != ".git" and not is_generated_path(relative_current / directory)
        )
        for name in sorted(names):
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            if path.is_file() and not is_generated_path(relative):
                files[relative] = path
    return files


def _detected_assets(paths: tuple[str, ...]) -> tuple[str, ...]:
    detected: list[str] = []
    for path in paths:
        lower = path.lower()
        name = Path(path).name
        if path in {"AGENTS.md", "CLAUDE.md", "CURSOR.md", "GEMINI.md"}:
            detected.append(path)
        elif path.startswith(".claude/agents/") or path.startswith(".claude/skills/"):
            detected.append(path)
        elif path.startswith((".codex/", ".agents/", "agents/marketplace/", "plugins/")):
            detected.append(path)
        elif path in {_config.CONFIG_FILE, "agent_runtime.lock.json", _config.LEGACY_CONFIG_FILE, "ralph.lock.json"}:
            detected.append(path)
        elif path.startswith("docs/") and name.endswith((".md", ".mdx")) and any(
            token in lower for token in ("editorial", "integration", "security", "status", "manual")
        ):
            detected.append(path)
    return tuple(sorted(set(detected)))


def _ownership(config: _config.AgentRuntimeConfig | None, path: str) -> str:
    if config:
        for mode, paths in config.ownership:
            if any(path == candidate or path.startswith(candidate.rstrip("/") + "/") for candidate in paths):
                return mode
    return _config.default_ownership(path)


def _generated_roots(paths: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted({root for path in paths if (root := generated_path_root(path)) is not None}))


def build_adoption_plan(root: Path) -> AdoptionPlan:
    root = root.resolve()
    scan = adoption_scan(root)
    findings = list(scan.warnings)
    config_invalid = False
    try:
        config = _config.load_config(root)
    except FileNotFoundError:
        config = None
        profiles, capabilities = ("core",), _config.PROFILE_CAPABILITIES["core"]
    except Exception as exc:
        config = None
        profiles, capabilities = ("core",), _config.PROFILE_CAPABILITIES["core"]
        findings.append(f"config unavailable for adoption projection: {exc}")
        config_invalid = True
    else:
        profiles, capabilities = config.profiles, config.capabilities

    actions: list[AdoptionAction] = []
    for rel in scan.paths:
        target = root / rel
        if target.is_symlink():
            try:
                target.resolve().relative_to(root)
            except ValueError:
                findings.append(f"external symlink cannot be adopted: {rel}")
    for rel, template in _template_files(tuple(profiles)).items():
        ownership = _ownership(config, rel)
        target = root / rel
        if ownership == "generated":
            actions.append(AdoptionAction(rel, "skip", "generated", "generated lifecycle is producer-owned"))
            continue
        if target.is_symlink():
            try:
                target.resolve().relative_to(root)
            except ValueError:
                findings.append(f"external symlink cannot be adopted: {rel}")
            actions.append(AdoptionAction(rel, "conflict", ownership, "non-regular or external symlink collision"))
        elif target.exists():
            if ownership in {"seed_once", "host_owned"}:
                actions.append(AdoptionAction(rel, "preserve", ownership, "existing host-owned seed seam"))
            elif target.is_file() and target.read_bytes() == template.read_bytes():
                actions.append(AdoptionAction(rel, "skip", ownership, "already identical to packaged template"))
            else:
                actions.append(AdoptionAction(rel, "conflict", ownership, "existing managed path differs from packaged template"))
        else:
            actions.append(AdoptionAction(rel, "add", ownership, "missing packaged template file; plan only"))
    return AdoptionPlan(
        root=root, profiles=tuple(profiles), capabilities=tuple(capabilities), scan_strategy=scan.strategy,
        scan_warnings=tuple(sorted(scan.warnings)), source_paths=scan.paths, generated_paths=scan.generated_paths, ignored_count=scan.ignored_count, generated_roots=_generated_roots(scan.generated_paths),
        assets=_detected_assets(scan.paths), actions=tuple(sorted(actions, key=lambda action: (action.path, action.action, action.ownership))),
        findings=tuple(sorted(findings)), config_invalid=config_invalid,
    )


def plan_json(plan: AdoptionPlan) -> str:
    payload = {
        "schema": "agent-runtime-adoption-plan/v1", "root": str(plan.root), "profiles": list(plan.profiles),
        "capabilities": list(plan.capabilities),
        "inventory": {"included_count": len(plan.source_paths), "ignored_count": plan.ignored_count, "generated_count": len(plan.generated_paths), "generated_roots": list(plan.generated_roots), "scan_strategy": plan.scan_strategy, "warnings": list(plan.scan_warnings)},
        "assets": list(plan.assets), "actions": [action.as_dict() for action in plan.actions], "findings": list(plan.findings),
        "readiness": {"conflicts": len(plan.conflicts), "ready": not plan.conflicts and not plan.config_invalid and not any("external symlink" in item for item in plan.findings)},
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)


def render(plan: AdoptionPlan) -> str:
    lines = ["# Agent Runtime Adoption Plan", "", f"root={plan.root}", f"scan_strategy={plan.scan_strategy}", f"included_paths={len(plan.source_paths)}", f"ignored_paths={plan.ignored_count}", f"generated_paths={len(plan.generated_paths)}", f"generated_roots={','.join(plan.generated_roots)}", f"conflicts={len(plan.conflicts)}", "", "| Path | Action | Ownership | Reason |", "|---|---|---|---|"]
    lines.extend(f"| `{a.path}` | {a.action} | {a.ownership} | {a.reason} |" for a in plan.actions)
    return "\n".join(lines)


def run_adopt(root: Path, *, plan_only: bool, json_output: bool) -> int:
    if not plan_only:
        raise ValueError("adopt requires --plan; no apply mode exists")
    plan = build_adoption_plan(root)
    print(plan_json(plan) if json_output else render(plan))
    return 0
