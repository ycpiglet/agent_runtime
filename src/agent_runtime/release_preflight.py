from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from .host_update import build_update_execution
from .host_update import build_update_plan
from .lock import build_lock_plan
from .publish_bundle import build_bundle_plan
from .publish_check import PublishFinding, analyze as analyze_publish
from .publish_github_plan import build_github_plan
from .publish_tag_smoke import build_tag_smoke_plan
from .sanitize import analyze as analyze_sanitize
from .sync import build_sync_plan


@dataclass(frozen=True)
class PreflightCheck:
    name: str
    status: str
    detail: str
    findings: tuple[PublishFinding, ...] = ()


@dataclass(frozen=True)
class PreflightPlan:
    source_root: Path
    host_root: Path
    remote_url: str
    tag: str
    checks: tuple[PreflightCheck, ...]

    @property
    def findings_count(self) -> int:
        return sum(len(check.findings) for check in self.checks)


def _status(findings: tuple[PublishFinding, ...] | list[PublishFinding]) -> str:
    return "blocked" if findings else "ok"


def _host_upstream_match_findings(update_plan, remote_url: str, tag: str) -> tuple[PublishFinding, ...]:
    config = update_plan.config
    findings: list[PublishFinding] = []
    if config.upstream_remote_url != remote_url:
        findings.append(
            PublishFinding(
                "agent_runtime.yml",
                "upstream-remote-url-mismatch",
                "host upstream.remote_url must match release preflight remote_url",
            )
        )
    if config.upstream_ref != tag:
        findings.append(
            PublishFinding(
                "agent_runtime.yml",
                "upstream-ref-mismatch",
                "host upstream.ref must match release preflight tag",
            )
        )
    return tuple(findings)


def _host_sync_findings(sync_plan) -> tuple[PublishFinding, ...]:
    return tuple(
        PublishFinding(
            conflict.path,
            "host-sync-conflict",
            "host file diverged from the locked managed file and would block sync",
        )
        for conflict in sync_plan.conflicts
    )


def _parse_warning_summary_gate_strict_refs(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return ()
    refs = tuple(line.strip() for line in raw.splitlines() if line.strip())
    return refs


def _warning_summary_gate_strict_refs_findings(raw: str | None) -> tuple[PublishFinding, ...]:
    if raw is None:
        return ()
    refs = _parse_warning_summary_gate_strict_refs(raw)
    findings: list[PublishFinding] = []
    if not refs:
        findings.append(
            PublishFinding(
                "release-preflight",
                "missing-warning-summary-gate-strict-ref",
                "PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS is configured as an empty list",
            )
        )
        return tuple(findings)

    for strict_ref in refs:
        if not (strict_ref.startswith("refs/") or strict_ref == ""):
            findings.append(
                PublishFinding(
                    "release-preflight",
                    "invalid-warning-summary-gate-strict-ref",
                    f"strict-ref must start with refs/, got: {strict_ref}",
                )
            )
    return tuple(findings)


OWNER_DOC_REQUIRED_GROUPS = {
    "summary": (r"^##\s+(Summary|Bottom Line)\b", r"^Bottom Line\b"),
    "signal": (r"^##\s+(Signal|Status|Key Points)\b",),
    "action": (r"^##\s+(Action|Action Items|Action Board)\b",),
    "risk": (r"^##\s+(Risk|Risks|Risks / Blockers|Blockers)\b",),
    "decision": (r"^##\s+Decision\b",),
    "next": (r"^##\s+(Next|Next Steps)\b",),
}

OWNER_DOC_FRONTMATTER_PATTERN = re.compile(r"\A---\r?\n.*?\r?\n---\r?\n", re.DOTALL)
OWNER_DOC_SIGNAL_PATTERN = re.compile(r"^signal:\s*(pass|watch|block)\s*$", re.MULTILINE | re.IGNORECASE)
OWNER_DOC_SCORE_PATTERN = re.compile(r"^score:\s*([0-9]{1,3})\s*$", re.MULTILINE | re.IGNORECASE)
REQUIRED_STATE_MACHINES = {
    "health_signal",
    "cycle",
    "task",
    "task_claim",
    "agent_job",
    "gate",
    "review",
    "release",
    "owner_decision",
    "hook_enforcement",
    "ci",
    "document",
}


def _owner_doc_has_group(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, flags=re.MULTILINE | re.IGNORECASE) for pattern in patterns)


def _owner_doc_manifest_paths(source: Path) -> tuple[tuple[str, ...], tuple[PublishFinding, ...]]:
    manifest = source / "owner-docs.yml"
    if not manifest.exists():
        return (), (
            PublishFinding(
                "owner-docs.yml",
                "owner-doc-manifest-missing",
                "release source must declare Owner-facing docs checked by the format gate",
            ),
        )
    docs: list[str] = []
    in_owner_docs = False
    for raw in manifest.read_text(encoding="utf-8").splitlines():
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
            docs.append(value)
    return tuple(docs), ()


def _owner_doc_format_findings(source: Path) -> tuple[PublishFinding, ...]:
    docs, manifest_findings = _owner_doc_manifest_paths(source)
    findings: list[PublishFinding] = list(manifest_findings)
    if manifest_findings:
        return tuple(findings)
    if not docs:
        findings.append(
            PublishFinding(
                "owner-docs.yml",
                "owner-doc-manifest-empty",
                "release source must list at least one Owner-facing doc",
            )
        )
        return tuple(findings)
    for rel in docs:
        path = source / rel
        if not path.exists():
            findings.append(PublishFinding(rel, "owner-doc-missing", "manifest entry does not exist in release source"))
            continue
        text = path.read_text(encoding="utf-8")
        frontmatter = OWNER_DOC_FRONTMATTER_PATTERN.search(text)
        if not frontmatter:
            findings.append(PublishFinding(rel, "owner-doc-frontmatter-missing", "Owner doc must start with YAML frontmatter"))
        else:
            frontmatter_text = frontmatter.group(0)
            if not OWNER_DOC_SIGNAL_PATTERN.search(frontmatter_text):
                findings.append(PublishFinding(rel, "owner-doc-signal-missing", "Owner doc frontmatter must include signal: pass|watch|block"))
            score_match = OWNER_DOC_SCORE_PATTERN.search(frontmatter_text)
            if not score_match:
                findings.append(PublishFinding(rel, "owner-doc-score-missing", "Owner doc frontmatter must include score: 0-100"))
            elif int(score_match.group(1)) > 100:
                findings.append(PublishFinding(rel, "owner-doc-score-invalid", "Owner doc score must be 0-100"))
        for group, patterns in OWNER_DOC_REQUIRED_GROUPS.items():
            if not _owner_doc_has_group(text, patterns):
                findings.append(PublishFinding(rel, f"owner-doc-{group}-missing", "Owner doc is missing a required executive section"))
        if len(re.findall(r"^\|.+\|$", text, flags=re.MULTILINE)) < 3:
            findings.append(PublishFinding(rel, "owner-doc-table-missing", "Owner doc must include a compact tracking table"))
    return tuple(findings)


def _state_machine_findings(source: Path) -> tuple[PublishFinding, ...]:
    checks = (
        ("schemas/state-machines.schema.json", True),
        ("src/agent_runtime/templates/project/schemas/state-machines.schema.json", True),
        ("src/agent_runtime/templates/project/agents/project/STATE-MACHINES.yml", True),
        ("agents/project/STATE-MACHINES.yml", False),
    )
    findings: list[PublishFinding] = []
    for rel, required in checks:
        path = source / rel
        if not path.exists():
            if required:
                findings.append(PublishFinding(rel, "state-machine-missing", "required state machine schema or SSoT file is missing"))
            continue
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".json":
            try:
                json.loads(text)
            except json.JSONDecodeError as exc:
                findings.append(PublishFinding(rel, "state-machine-schema-invalid-json", exc.msg))
            continue
        ids = set(re.findall(r"^\s*-\s*id:\s*([A-Za-z0-9_-]+)\s*$", text, flags=re.MULTILINE))
        missing = REQUIRED_STATE_MACHINES - ids
        findings.extend(
            PublishFinding(rel, f"state-machine-missing-id:{machine_id}", "required machine id is absent")
            for machine_id in sorted(missing)
        )
        if not re.search(r"\bpass\b", text) or not re.search(r"\bwatch\b", text) or not re.search(r"\bblock\b", text):
            findings.append(PublishFinding(rel, "state-machine-signal-scale-missing", "must define pass/watch/block signal scale"))
        if re.search(r"\b(Green|Yellow|Red)\b", text):
            findings.append(PublishFinding(rel, "state-machine-color-label", "use pass/watch/block instead of color labels"))
    return tuple(findings)


def _source_work_dir(source_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else source_root / path


def build_preflight_plan(
    *,
    source_root: Path,
    host_root: Path,
    bundle_dir: Path,
    tag_repo_dir: Path,
    tag_install_dir: Path,
    github_install_dir: Path,
    host_install_dir: Path,
    remote_url: str,
    tag: str,
    warning_summary_gate_strict_refs: str | None = None,
) -> PreflightPlan:
    source = source_root.resolve()
    host = host_root.resolve()
    resolved_bundle_dir = _source_work_dir(source, bundle_dir)
    resolved_tag_repo_dir = _source_work_dir(source, tag_repo_dir)
    resolved_tag_install_dir = _source_work_dir(source, tag_install_dir)
    resolved_host_install_dir = host_install_dir if host_install_dir.is_absolute() else host / host_install_dir
    resolved_github_install_dir = github_install_dir if github_install_dir.is_absolute() else source / github_install_dir

    sanitize_findings = tuple(analyze_sanitize(source))
    publish_findings = tuple(analyze_publish(source))
    bundle_plan = build_bundle_plan(source, resolved_bundle_dir)
    tag_plan = build_tag_smoke_plan(source, resolved_tag_repo_dir, resolved_tag_install_dir, tag)
    github_plan = build_github_plan(source, remote_url, resolved_github_install_dir, tag=tag)
    update_plan = build_update_plan(host, resolved_host_install_dir)
    if update_plan.findings:
        upstream_match_check = PreflightCheck("host-upstream-match", "skipped", "waiting-for-host-update-plan", ())
        update_command_check = PreflightCheck("host-update-command", "skipped", "waiting-for-host-update-plan", ())
        sync_check = PreflightCheck("host-sync-check", "skipped", "waiting-for-host-update-plan", ())
        lock_check = PreflightCheck("host-lock", "skipped", "waiting-for-host-update-plan", ())
    else:
        upstream_match_findings = _host_upstream_match_findings(update_plan, remote_url, tag)
        upstream_match_check = PreflightCheck(
            "host-upstream-match",
            _status(upstream_match_findings),
            "remote/ref match release inputs",
            upstream_match_findings,
        )
        update_execution = build_update_execution(host, resolved_host_install_dir, mode="check")
        if upstream_match_findings:
            update_command_check = PreflightCheck("host-update-command", "skipped", "waiting-for-host-upstream-match", ())
            sync_check = PreflightCheck("host-sync-check", "skipped", "waiting-for-host-upstream-match", ())
            lock_check = PreflightCheck("host-lock", "skipped", "waiting-for-host-upstream-match", ())
        else:
            update_command_check = PreflightCheck(
                "host-update-command",
                _status(update_execution.findings),
                f"steps={len(update_execution.steps)}",
                tuple(update_execution.findings),
            )
            sync_plan = build_sync_plan(host, template_root=source / "src" / "agent_runtime" / "templates" / "project")
            sync_findings = _host_sync_findings(sync_plan)
            sync_check = PreflightCheck(
                "host-sync-check",
                _status(sync_findings),
                f"updates={len(sync_plan.updates)} conflicts={len(sync_plan.conflicts)}",
                sync_findings,
            )
            lock_plan = build_lock_plan(host, template_root=source / "src" / "agent_runtime" / "templates" / "project")
            lock_detail = f"template_digest={lock_plan.record['installed']['template_digest']}"
            lock_check = PreflightCheck("host-lock", _status(lock_plan.findings), lock_detail, tuple(lock_plan.findings))

    strict_refs_findings = _warning_summary_gate_strict_refs_findings(warning_summary_gate_strict_refs)
    strict_refs = _parse_warning_summary_gate_strict_refs(warning_summary_gate_strict_refs)
    strict_refs_detail = f"refs={';'.join(strict_refs)}" if strict_refs else "refs=<none>"
    strict_refs_status = "skipped" if warning_summary_gate_strict_refs is None else _status(strict_refs_findings)
    owner_doc_findings = _owner_doc_format_findings(source)
    state_machine_findings = _state_machine_findings(source)
    checks = (
        PreflightCheck("sanitize", _status(sanitize_findings), f"findings={len(sanitize_findings)}", sanitize_findings),
        PreflightCheck(
            "warning-summary-gate-strict-refs",
            strict_refs_status,
            strict_refs_detail,
            strict_refs_findings,
        ),
        PreflightCheck(
            "owner-doc-format",
            _status(owner_doc_findings),
            f"manifest=owner-docs.yml findings={len(owner_doc_findings)}",
            owner_doc_findings,
        ),
        PreflightCheck(
            "state-machines",
            _status(state_machine_findings),
            f"schema=state-machines findings={len(state_machine_findings)}",
            state_machine_findings,
        ),
        PreflightCheck("publish-check", _status(publish_findings), f"findings={len(publish_findings)}", publish_findings),
        PreflightCheck(
            "publish-bundle",
            _status(bundle_plan.findings),
            f"files={len(bundle_plan.files)}",
            tuple(bundle_plan.findings),
        ),
        PreflightCheck(
            "local-tag-smoke-plan",
            _status(tag_plan.findings),
            f"install_spec={tag_plan.install_spec}",
            tuple(tag_plan.findings),
        ),
        PreflightCheck(
            "github-publish-plan",
            _status(github_plan.findings),
            f"install_spec={github_plan.install_spec}",
            tuple(github_plan.findings),
        ),
        PreflightCheck(
            "host-update-plan",
            _status(update_plan.findings),
            f"install_spec={update_plan.install_spec}",
            tuple(update_plan.findings),
        ),
        upstream_match_check,
        update_command_check,
        sync_check,
        lock_check,
    )
    return PreflightPlan(source, host, remote_url, tag, checks)


def render(plan: PreflightPlan) -> str:
    lines = [
        "# Agent Runtime Release Preflight",
        "",
        f"source={plan.source_root}",
        f"host_root={plan.host_root}",
        f"remote_url={plan.remote_url}",
        f"tag={plan.tag}",
        f"findings={plan.findings_count}",
        "",
        "| Check | Status | Detail | Findings |",
        "|-------|--------|--------|----------|",
    ]
    for check in plan.checks:
        lines.append(f"| {check.name} | {check.status} | {check.detail} | {len(check.findings)} |")
    if plan.findings_count:
        lines.extend(["", "## Findings", ""])
        for check in plan.checks:
            for finding in check.findings:
                lines.append(f"- {check.name}: `{finding.path}` {finding.kind}: {finding.detail}")
    return "\n".join(lines)


def run_preflight(
    source_root: Path,
    host_root: Path,
    remote_url: str,
    *,
    bundle_dir: Path,
    tag_repo_dir: Path,
    tag_install_dir: Path,
    github_install_dir: Path,
    host_install_dir: Path,
    tag: str,
    check: bool,
    warning_summary_gate_strict_refs: str | None = None,
) -> int:
    if warning_summary_gate_strict_refs is None:
        warning_summary_gate_strict_refs = os.getenv("PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS")
    plan = build_preflight_plan(
        source_root=source_root,
        host_root=host_root,
        bundle_dir=bundle_dir,
        tag_repo_dir=tag_repo_dir,
        tag_install_dir=tag_install_dir,
        github_install_dir=github_install_dir,
        host_install_dir=host_install_dir,
        remote_url=remote_url,
        tag=tag,
        warning_summary_gate_strict_refs=warning_summary_gate_strict_refs,
    )
    print(render(plan))
    return 1 if check and plan.findings_count else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a non-mutating Agent Runtime release readiness preflight")
    parser.add_argument("--source", type=Path, default=Path.cwd(), help="Package source root")
    parser.add_argument("--host-root", type=Path, default=Path.cwd(), help="Host project root")
    parser.add_argument("--remote-url", required=True, help="GitHub remote URL to publish/install from")
    parser.add_argument(
        "--warning-summary-gate-strict-refs",
        help="Optional strict-ref configuration for warning-summary-gate checks",
    )
    parser.add_argument("--tag", default="v0.4.0", help="Release tag")
    parser.add_argument("--bundle-dir", type=Path, default=Path(".tmp/public-source"), help="Temporary publish bundle dir")
    parser.add_argument("--tag-repo-dir", type=Path, default=Path(".tmp/tag-repo"), help="Temporary local tag repo dir")
    parser.add_argument("--tag-install-dir", type=Path, default=Path(".tmp/tag-install"), help="Temporary local tag install dir")
    parser.add_argument("--github-install-dir", type=Path, default=Path(".tmp/github-install"), help="Temporary GitHub tag install dir")
    parser.add_argument("--host-install-dir", type=Path, default=Path(".tmp/agent_runtime-upstream"), help="Temporary host upstream install dir")
    parser.add_argument("--check", action="store_true", help="Fail if any preflight finding exists")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_preflight(
        args.source,
        args.host_root,
        args.remote_url,
        bundle_dir=args.bundle_dir,
        tag_repo_dir=args.tag_repo_dir,
        tag_install_dir=args.tag_install_dir,
        github_install_dir=args.github_install_dir,
        host_install_dir=args.host_install_dir,
        tag=args.tag,
        check=args.check,
        warning_summary_gate_strict_refs=args.warning_summary_gate_strict_refs,
    )


if __name__ == "__main__":
    raise SystemExit(main())
