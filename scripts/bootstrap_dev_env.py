"""Bootstrap / verify a development checkout of agent_runtime on any machine.

One command that checks (and with ``--apply`` fixes) the local wiring that has
bitten real sessions when missing:

- **editable install**: src-layout package; without ``pip install -e .`` a stale
  site-packages build (or nothing) gets imported instead of this checkout.
- **git hooks path**: the gate chain and lock/board regeneration live in
  ``.githooks/``; if ``core.hooksPath`` does not point there, commits silently
  skip every gate locally and the problems only surface in CI.
- **push transport**: HTTPS OAuth tokens usually lack the ``workflow`` scope,
  so pushes touching ``.github/workflows/**`` (e.g. the release version
  cascade bumping test.yml) are rejected. SSH push is the reliable path.
- **GitHub CLI**: issue/PR automation (``gh``) must be installed and logged in.

Watch-only contract: always exits 0 (``--apply`` fixes what it safely can;
``--ssh-push`` additionally rewrites origin's push URL to SSH). See
``docs/DEV-ENVIRONMENT.md`` for the full onboarding guide.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from lock_merge_driver import is_pre_commit_executable, repair_pre_commit_executable

ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = ".githooks"


def check_codex_hook_contract() -> str:
    """Report tracked Codex hook wiring only; local user settings are never edited."""
    try:
        source_root = str(ROOT / "src")
        if source_root not in sys.path:
            sys.path.insert(0, source_root)
        from agent_runtime.doctor import _check_codex_hooks

        findings = []
        _check_codex_hooks(ROOT, findings)
    except Exception as exc:
        return (
            "FIX  Codex hooks: contract check unavailable "
            f"({exc.__class__.__name__}; run doctor --check)"
        )

    blockers = [finding for finding in findings if finding.severity == "blocker"]
    if blockers:
        kinds = ", ".join(sorted({finding.kind for finding in blockers})[:3])
        return (
            f"FIX  Codex hooks: {len(blockers)} tracked contract issue(s) "
            f"({kinds}; run doctor --check)"
        )
    return (
        "ok   Codex hooks: tracked portable contract present "
        "(review with /hooks; user settings untouched)"
    )


def _run(*args: str, timeout: int = 30) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            args,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, f"{exc.__class__.__name__}"
    return proc.returncode, (proc.stdout or "").strip()


def check_python() -> str:
    ok = sys.version_info >= (3, 10)
    return f"{'ok  ' if ok else 'WARN'} python: {sys.version.split()[0]}" + (
        "" if ok else " (requires >= 3.10)"
    )


def _editable_import_target() -> tuple[bool, str]:
    code = (
        "import agent_runtime, pathlib;"
        "print(pathlib.Path(agent_runtime.__file__).resolve())"
    )
    rc, out = _run(sys.executable, "-c", code)
    if rc != 0:
        return False, "not importable"
    return out.startswith(str((ROOT / "src").resolve())), out


def check_editable_install(apply: bool) -> str:
    ok, target = _editable_import_target()
    if ok:
        return f"ok   editable install: {target}"
    if apply:
        print("bootstrap: running pip install -e . (first run can take a minute)...")
        rc, _ = _run(sys.executable, "-m", "pip", "install", "-e", ".", timeout=600)
        if rc == 0:
            ok, target = _editable_import_target()
            if ok:
                return f"ok   editable install: installed -> {target}"
    return (
        f"FIX  editable install: {target} (not this checkout)"
        " -> run: pip install -e ."
    )


def check_hooks_path(apply: bool) -> str:
    rc, current = _run("git", "config", "core.hooksPath")
    normalized = current.replace("\\", "/").rstrip("/")
    path_ready = rc == 0 and normalized.endswith(HOOKS_DIR)
    hook_ready = is_pre_commit_executable(ROOT)
    if path_ready and hook_ready:
        return f"ok   hooksPath: {current}; pre-commit activation ready"
    if apply:
        if not path_ready:
            rc2, _ = _run("git", "config", "core.hooksPath", HOOKS_DIR)
            path_ready = rc2 == 0
        if not hook_ready:
            try:
                repair_pre_commit_executable(ROOT)
            except OSError:
                pass
            hook_ready = is_pre_commit_executable(ROOT)
        if path_ready and hook_ready:
            changed = "" if normalized.endswith(HOOKS_DIR) else f" (was: {current or 'unset'})"
            return f"ok   hooksPath: set to {HOOKS_DIR}{changed}; pre-commit activation ready"
    hook_detail = ""
    if not hook_ready:
        hook_detail = "; pre-commit is not executable -> run: chmod +x .githooks/pre-commit"
    return (
        f"FIX  hooksPath: {current or 'unset'} -> gates/lock-regen will NOT run"
        f" on local commits; run: git config core.hooksPath {HOOKS_DIR}{hook_detail}"
    )


def check_push_transport(ssh_push: bool) -> str:
    rc, url = _run("git", "remote", "get-url", "--push", "origin")
    if rc != 0:
        return "WARN push transport: no origin remote configured"
    if url.startswith("git@") or url.startswith("ssh://"):
        return f"ok   push transport: {url}"
    ssh_url = None
    if url.startswith("https://github.com/"):
        ssh_url = "git@github.com:" + url[len("https://github.com/"):]
    if ssh_push and ssh_url:
        rc2, _ = _run("git", "remote", "set-url", "--push", "origin", ssh_url)
        if rc2 == 0:
            return f"ok   push transport: push URL set to {ssh_url}"
    hint = f" -> run: git remote set-url --push origin {ssh_url}" if ssh_url else ""
    return (
        f"WARN push transport: {url} (HTTPS OAuth tokens usually lack the"
        f" 'workflow' scope; pushes touching .github/workflows/** are rejected){hint}"
    )


def check_gh_cli() -> str:
    if not shutil.which("gh"):
        return "WARN gh: not installed -> https://cli.github.com (needed for issue/PR automation)"
    rc, _ = _run("gh", "auth", "status")
    if rc != 0:
        return "WARN gh: installed but not authenticated -> run: gh auth login"
    return "ok   gh: installed and authenticated"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check/fix the local dev wiring (always exits 0)")
    parser.add_argument("--check", action="store_true", help="report only (default)")
    parser.add_argument(
        "--apply", action="store_true", help="fix what is safe: editable install + hooksPath"
    )
    parser.add_argument(
        "--ssh-push", action="store_true", help="with --apply: also switch origin push URL to SSH"
    )
    args = parser.parse_args(argv)

    lines = [
        check_python(),
        check_editable_install(apply=args.apply),
        check_hooks_path(apply=args.apply),
        check_codex_hook_contract(),
        check_push_transport(ssh_push=args.apply and args.ssh_push),
        check_gh_cli(),
    ]
    for line in lines:
        print(f"bootstrap: {line}")
    pending = sum(1 for line in lines if line.startswith("FIX"))
    if pending:
        print(
            f"bootstrap: {pending} item(s) need fixing"
            " (see FIX lines; --apply fixes editable install + hooksPath)"
        )
    else:
        print("bootstrap: environment ready")
    return 0  # watch-only: never blocks


if __name__ == "__main__":
    raise SystemExit(main())
