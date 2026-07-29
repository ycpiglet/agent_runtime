"""Tests for claim_guard — commit claim artifacts so a concurrent reset/clean can't lose them.

Regression target (incident 2026-06-12): a freshly created claim JSON was left
*untracked*, so a sibling session's ``git reset --hard && git clean -fd`` erased it
and the claim had to be recreated. Committing the claim the instant it is written
makes it part of HEAD, which survives both reset and clean.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import claim_guard  # noqa: E402


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(root), capture_output=True, text=True)


def _init_repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "Test")
    _git(tmp_path, "config", "commit.gpgsign", "false")
    (tmp_path / "seed.txt").write_text("seed\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "seed")
    return tmp_path


def _write_claim(root: Path, name: str = "CLAIM-test.json") -> Path:
    claims = root / "agents" / "runtime" / "task_claims"
    claims.mkdir(parents=True, exist_ok=True)
    path = claims / name
    path.write_text('{"claim_id": "CLAIM-test"}\n', encoding="utf-8")
    return path


def _write_runtime_claim(root: Path) -> tuple[Path, Path, Path]:
    claims = root / "agents" / "runtime" / "task_claims"
    claims.mkdir(parents=True, exist_ok=True)
    claim = claims / "CLAIM-runtime-hook.json"
    handoff = claims / "CLAIM-runtime-hook.handoff.md"
    log = claims / "CLAIM-runtime-hook.log.md"
    handoff.write_text("# Handoff\n\n- Next Steps: verify\n", encoding="utf-8")
    log.write_text("# Claim Log\n\n- transaction test\n", encoding="utf-8")
    claim.write_text(
        json.dumps(
            {
                "schema": "agent-runtime-task-claim/v1",
                "claim_id": "CLAIM-runtime-hook",
                "task_id": "TASK-AR-648",
                "task_set_id": "TASKSET-AR-V080-ADOPTION-ENFORCEMENT",
                "agent_role": "orchestrator",
                "team_id": "evaluation-office",
                "agent_instance_id": "claim-hook-test",
                "display_name": "claim-hook@test",
                "callsite_id": "pytest:claim-hook",
                "pane_id": "pytest:claim-hook",
                "mode": "orchestrator",
                "status": "claimed",
                "phase": "claim-created",
                "progress_pct": 0,
                "status_text": "Verify explicit claim commit transaction",
                "worktree_path": ".",
                "branch": "test/claim-hook",
                "claimed_at": "2026-07-29T19:00:00+09:00",
                "last_heartbeat": "2026-07-29T19:00:00+09:00",
                "handoff_path": handoff.relative_to(root).as_posix(),
                "log_path": log.relative_to(root).as_posix(),
                "persistence": {
                    "mode": "scm_commit",
                    "scm_commit_authorized": True,
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return claim, handoff, log


def _install_runtime_gate_hook(
    root: Path,
    *,
    mutate_after_gate: str = "",
) -> None:
    (root / "STATUS.md").write_text(
        "## Next Steps\n- finish the claim transaction\n",
        encoding="utf-8",
    )
    scripts = root / "scripts"
    scripts.mkdir(exist_ok=True)
    (scripts / "parallel_worktree_gate.py").write_text(
        (ROOT / "scripts" / "parallel_worktree_gate.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    hooks = root / ".githooks"
    hooks.mkdir(exist_ok=True)
    hook = hooks / "pre-commit"
    hook.write_text(
        "#!/bin/sh\n"
        "python3 scripts/parallel_worktree_gate.py --check || exit 1\n"
        "if [ -n \"${AGENT_RUNTIME_CLAIM_COMMIT_TRANSACTION:-}\" ]; then\n"
        ":\n"
        f"{mutate_after_gate}"
        "fi\n",
        encoding="utf-8",
    )
    hook.chmod(0o755)
    _git(root, "config", "core.hooksPath", ".githooks")
    _git(root, "add", "STATUS.md", "scripts/parallel_worktree_gate.py", ".githooks/pre-commit")
    assert _git(root, "commit", "-m", "runtime hook fixture").returncode == 0


def _post_gate_mutator(relative_path: str) -> str:
    if relative_path.endswith(".json"):
        mutation = (
            "import json, pathlib\n"
            f"path = pathlib.Path({relative_path!r})\n"
            "payload = json.loads(path.read_text(encoding='utf-8'))\n"
            "payload['status_text'] = 'modified after successful gate validation'\n"
            "path.write_text(json.dumps(payload, indent=2) + '\\n', encoding='utf-8')\n"
        )
    else:
        mutation = (
            "import pathlib\n"
            f"path = pathlib.Path({relative_path!r})\n"
            "path.write_text(path.read_text(encoding='utf-8') + "
            "'\\nmodified after successful gate validation\\n', encoding='utf-8')\n"
        )
    return (
        f"if [ -f {relative_path!r} ]; then\n"
        "python3 - <<'PY'\n"
        f"{mutation}"
        "PY\n"
        f"git add -- {relative_path!r} || exit 1\n"
        "fi\n"
    )


def _post_gate_omitter(relative_path: str) -> str:
    return f"git rm --cached -- {relative_path!r} || exit 1\n"


def _transaction_dir(root: Path) -> Path:
    path = Path(
        _git(root, "rev-parse", "--git-path", "agent-runtime/claim-commit").stdout.strip()
    )
    if not path.is_absolute():
        path = root / path
    return path


def _seed_unrelated_files(root: Path) -> None:
    for name in ("staged.txt", "partial.txt", "unstaged.txt"):
        (root / name).write_text(f"{name}: base\n", encoding="utf-8")
    _git(root, "add", "staged.txt", "partial.txt", "unstaged.txt")
    assert _git(root, "commit", "-m", "seed unrelated state fixtures").returncode == 0


def _prepare_unrelated_state(root: Path) -> None:
    (root / "staged.txt").write_text("staged.txt: staged\n", encoding="utf-8")
    _git(root, "add", "staged.txt")
    (root / "partial.txt").write_text("partial.txt: staged\n", encoding="utf-8")
    _git(root, "add", "partial.txt")
    (root / "partial.txt").write_text("partial.txt: staged plus unstaged\n", encoding="utf-8")
    (root / "unstaged.txt").write_text("unstaged.txt: unstaged\n", encoding="utf-8")
    (root / "untracked.txt").write_text("untracked.txt: user data\n", encoding="utf-8")


def _unrelated_state(root: Path) -> dict[str, object]:
    tracked = ("staged.txt", "partial.txt", "unstaged.txt")
    return {
        "index": _git(root, "ls-files", "--stage", "--", *tracked).stdout,
        "cached_diff": _git(root, "diff", "--binary", "--cached", "--", *tracked).stdout,
        "working_diff": _git(root, "diff", "--binary", "--", *tracked).stdout,
        "files": {
            name: (root / name).read_bytes()
            for name in (*tracked, "untracked.txt")
        },
    }


def test_is_git_repo(tmp_path):
    assert claim_guard.is_git_repo(tmp_path) is False
    _init_repo(tmp_path)
    assert claim_guard.is_git_repo(tmp_path) is True


def test_commit_claim_artifacts_tracks_the_file(tmp_path):
    _init_repo(tmp_path)
    claim = _write_claim(tmp_path)
    result = claim_guard.commit_claim_artifacts(tmp_path, claim, claim_id="CLAIM-test")
    assert result["ok"] is True
    assert result["committed"] is True
    tracked = _git(tmp_path, "ls-files", "agents/runtime/task_claims").stdout
    assert "CLAIM-test.json" in tracked


def test_committed_claim_survives_reset_and_clean(tmp_path):
    """The actual incident regression: committed claim must outlive reset+clean."""
    _init_repo(tmp_path)
    claim = _write_claim(tmp_path)
    claim_guard.commit_claim_artifacts(tmp_path, claim, claim_id="CLAIM-test")

    # A sibling session does the destructive cleanup that caused the 2026-06-12 loss.
    _git(tmp_path, "reset", "--hard", "HEAD")
    _git(tmp_path, "clean", "-fd")

    assert claim.exists(), "committed claim was lost by reset+clean"


def test_uncommitted_claim_is_lost_by_clean(tmp_path):
    """Control: prove the hazard is real when the guard does NOT run."""
    _init_repo(tmp_path)
    claim = _write_claim(tmp_path, "CLAIM-orphan.json")
    _git(tmp_path, "clean", "-fd")
    assert not claim.exists()


def test_not_a_git_repo_is_reported_not_raised(tmp_path):
    claim = _write_claim(tmp_path)
    result = claim_guard.commit_claim_artifacts(tmp_path, claim, claim_id="CLAIM-test")
    assert result["ok"] is False
    assert result["reason"] == "not-a-git-repo"
    assert result["committed"] is False


def test_commit_is_idempotent(tmp_path):
    _init_repo(tmp_path)
    claim = _write_claim(tmp_path)
    claim_guard.commit_claim_artifacts(tmp_path, claim, claim_id="CLAIM-test")
    # Second call with no new changes must not error.
    again = claim_guard.commit_claim_artifacts(tmp_path, claim, claim_id="CLAIM-test")
    assert again["ok"] is True
    assert again["committed"] is False


def test_sweep_commits_orphan_claims(tmp_path):
    _init_repo(tmp_path)
    _write_claim(tmp_path, "CLAIM-a.json")
    _write_claim(tmp_path, "CLAIM-b.json")
    result = claim_guard.sweep(tmp_path, apply=True)
    assert result["committed"] is True
    assert len(result["paths"]) == 2
    tracked = _git(tmp_path, "ls-files", "agents/runtime/task_claims").stdout
    assert "CLAIM-a.json" in tracked and "CLAIM-b.json" in tracked


def test_sweep_dry_run_does_not_commit(tmp_path):
    _init_repo(tmp_path)
    _write_claim(tmp_path, "CLAIM-a.json")
    result = claim_guard.sweep(tmp_path, apply=False)
    assert result["committed"] is False
    tracked = _git(tmp_path, "ls-files", "agents/runtime/task_claims").stdout
    assert "CLAIM-a.json" not in tracked


def test_commit_only_touches_claim_paths(tmp_path):
    """A pre-existing unrelated working-tree change must remain uncommitted."""
    _init_repo(tmp_path)
    (tmp_path / "other.txt").write_text("dirty\n", encoding="utf-8")
    claim = _write_claim(tmp_path)
    claim_guard.commit_claim_artifacts(tmp_path, claim, claim_id="CLAIM-test")
    status = _git(tmp_path, "status", "--porcelain").stdout
    assert "other.txt" in status  # still uncommitted / untracked


def test_runtime_precommit_allows_exact_explicit_claim_transaction(tmp_path):
    """The Runtime gate must not reject the claim-only commit it is guarding."""
    _init_repo(tmp_path)
    _install_runtime_gate_hook(tmp_path)

    claim, handoff, log = _write_runtime_claim(tmp_path)
    before = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()
    result = claim_guard.commit_claim_artifacts(
        tmp_path,
        claim,
        extra_paths=(handoff, log),
        claim_id="CLAIM-runtime-hook",
    )

    assert result["ok"] is True, result
    assert result["committed"] is True
    assert _git(tmp_path, "rev-parse", "HEAD").stdout.strip() != before
    assert "AGENT_RUNTIME_CLAIM_COMMIT_TRANSACTION" not in os.environ
    transaction_dir = Path(
        _git(tmp_path, "rev-parse", "--git-path", "agent-runtime/claim-commit").stdout.strip()
    )
    if not transaction_dir.is_absolute():
        transaction_dir = tmp_path / transaction_dir
    assert not list(transaction_dir.glob("*"))


def test_explicit_claim_commit_uses_exact_sealed_tree_and_preserves_real_index(
    tmp_path: Path,
) -> None:
    _init_repo(tmp_path)
    _seed_unrelated_files(tmp_path)
    _install_runtime_gate_hook(tmp_path)
    _prepare_unrelated_state(tmp_path)
    before_user_state = _unrelated_state(tmp_path)
    claim, handoff, log = _write_runtime_claim(tmp_path)
    artifacts = (claim, handoff, log)
    artifact_rels = {path.relative_to(tmp_path).as_posix() for path in artifacts}
    artifact_oids = {
        path.relative_to(tmp_path).as_posix(): _git(
            tmp_path,
            "hash-object",
            f"--path={path.relative_to(tmp_path).as_posix()}",
            path.relative_to(tmp_path).as_posix(),
        ).stdout.strip()
        for path in artifacts
    }
    before = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()

    result = claim_guard.commit_claim_artifacts(
        tmp_path,
        claim,
        extra_paths=(handoff, log),
        claim_id="CLAIM-runtime-hook",
    )

    assert result["ok"] is True, result
    assert result["committed"] is True
    after = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()
    assert after != before
    assert result["tree"] == _git(tmp_path, "rev-parse", f"{after}^{{tree}}").stdout.strip()
    committed_paths = set(
        _git(
            tmp_path,
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            before,
            after,
        ).stdout.splitlines()
    )
    assert committed_paths == artifact_rels
    for rel, expected_oid in artifact_oids.items():
        assert _git(tmp_path, "rev-parse", f"{after}:{rel}").stdout.strip() == expected_oid
        assert _git(tmp_path, "diff", "--quiet", "HEAD", "--", rel).returncode == 0
    assert _unrelated_state(tmp_path) == before_user_state
    gate = subprocess.run(
        [sys.executable, "scripts/parallel_worktree_gate.py", "--check"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert gate.returncode == 0, gate.stdout
    assert "block=0" in gate.stdout
    assert not list(_transaction_dir(tmp_path).glob("*"))


def test_explicit_claim_commit_artifacts_survive_reset_and_clean(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _install_runtime_gate_hook(tmp_path)
    claim, handoff, log = _write_runtime_claim(tmp_path)

    result = claim_guard.commit_claim_artifacts(
        tmp_path,
        claim,
        extra_paths=(handoff, log),
        claim_id="CLAIM-runtime-hook",
    )
    assert result["ok"] is True, result

    assert _git(tmp_path, "reset", "--hard", "HEAD").returncode == 0
    assert _git(tmp_path, "clean", "-fd").returncode == 0
    assert all(path.exists() for path in (claim, handoff, log))


@pytest.mark.parametrize(
    "relative_path",
    [
        "agents/runtime/task_claims/CLAIM-runtime-hook.json",
        "agents/runtime/task_claims/CLAIM-runtime-hook.handoff.md",
        "agents/runtime/task_claims/CLAIM-runtime-hook.log.md",
    ],
)
def test_runtime_precommit_rejects_artifact_restage_after_successful_gate(
    tmp_path: Path,
    relative_path: str,
) -> None:
    """The hook-reviewed blob set, not merely its paths, must reach HEAD."""

    _init_repo(tmp_path)
    _seed_unrelated_files(tmp_path)
    _install_runtime_gate_hook(
        tmp_path,
        mutate_after_gate=_post_gate_mutator(relative_path),
    )
    _prepare_unrelated_state(tmp_path)
    before_user_state = _unrelated_state(tmp_path)
    claim, handoff, log = _write_runtime_claim(tmp_path)
    before = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()

    result = claim_guard.commit_claim_artifacts(
        tmp_path,
        claim,
        extra_paths=(handoff, log),
        claim_id="CLAIM-runtime-hook",
    )

    assert result["ok"] is False, result
    assert result["committed"] is False
    assert "transaction" in result["reason"]
    assert _git(tmp_path, "rev-parse", "HEAD").stdout.strip() == before
    staged = set(_git(tmp_path, "diff", "--cached", "--name-only").stdout.splitlines())
    assert {
        claim.relative_to(tmp_path).as_posix(),
        handoff.relative_to(tmp_path).as_posix(),
        log.relative_to(tmp_path).as_posix(),
    }.issubset(staged)
    assert _unrelated_state(tmp_path) == before_user_state
    gate = subprocess.run(
        [sys.executable, "scripts/parallel_worktree_gate.py", "--check"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert gate.returncode == 1
    assert "task-claim:authorized-commit-not-persisted" in gate.stdout
    transaction_dir = Path(
        _git(tmp_path, "rev-parse", "--git-path", "agent-runtime/claim-commit").stdout.strip()
    )
    if not transaction_dir.is_absolute():
        transaction_dir = tmp_path / transaction_dir
    assert not list(transaction_dir.glob("*"))


@pytest.mark.parametrize(
    "relative_path",
    [
        "agents/runtime/task_claims/CLAIM-runtime-hook.handoff.md",
        "agents/runtime/task_claims/CLAIM-runtime-hook.log.md",
    ],
)
def test_explicit_claim_transaction_rejects_sidecar_omission(
    tmp_path: Path,
    relative_path: str,
) -> None:
    _init_repo(tmp_path)
    _install_runtime_gate_hook(
        tmp_path,
        mutate_after_gate=_post_gate_omitter(relative_path),
    )
    claim, handoff, log = _write_runtime_claim(tmp_path)
    before = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()

    result = claim_guard.commit_claim_artifacts(
        tmp_path,
        claim,
        extra_paths=(handoff, log),
        claim_id="CLAIM-runtime-hook",
    )

    assert result["ok"] is False, result
    assert result["reason"] == "claim-commit-transaction-tree-changed"
    assert _git(tmp_path, "rev-parse", "HEAD").stdout.strip() == before
    assert not list(_transaction_dir(tmp_path).glob("*"))


def test_explicit_claim_transaction_cleans_private_files_on_hook_failure(
    tmp_path: Path,
) -> None:
    _init_repo(tmp_path)
    _install_runtime_gate_hook(tmp_path, mutate_after_gate="exit 23\n")
    claim, handoff, log = _write_runtime_claim(tmp_path)
    before = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()

    result = claim_guard.commit_claim_artifacts(
        tmp_path,
        claim,
        extra_paths=(handoff, log),
        claim_id="CLAIM-runtime-hook",
    )

    assert result["ok"] is False, result
    assert result["reason"].startswith("git-pre-commit-failed:")
    assert _git(tmp_path, "rev-parse", "HEAD").stdout.strip() == before
    assert not list(_transaction_dir(tmp_path).glob("*"))


def test_explicit_claim_transaction_loses_compare_and_swap_ref_race(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_repo(tmp_path)
    _install_runtime_gate_hook(tmp_path)
    claim, handoff, log = _write_runtime_claim(tmp_path)
    original_git = claim_guard._git
    race: dict[str, str] = {}

    def racing_git(
        root: Path,
        args: list[str],
        *,
        env: dict[str, str] | None = None,
    ) -> dict[str, object]:
        if args and args[0] == "update-ref" and not race:
            ref_name = args[3]
            old_oid = args[5]
            tree_oid = original_git(root, ["rev-parse", f"{old_oid}^{{tree}}"], env=env)[
                "out"
            ].strip()
            concurrent = original_git(
                root,
                [
                    "commit-tree",
                    tree_oid,
                    "-p",
                    old_oid,
                    "-m",
                    "simulated concurrent branch writer",
                ],
                env=env,
            )["out"].strip()
            moved = original_git(
                root,
                ["update-ref", ref_name, concurrent, old_oid],
                env=env,
            )
            assert moved["code"] == 0
            race["commit"] = concurrent
        return original_git(root, args, env=env)

    monkeypatch.setattr(claim_guard, "_git", racing_git)
    result = claim_guard.commit_claim_artifacts(
        tmp_path,
        claim,
        extra_paths=(handoff, log),
        claim_id="CLAIM-runtime-hook",
    )

    assert result["ok"] is False, result
    assert result["reason"].startswith("claim-commit-ref-update-failed:")
    assert _git(tmp_path, "rev-parse", "HEAD").stdout.strip() == race["commit"]
    rel = claim.relative_to(tmp_path).as_posix()
    assert _git(tmp_path, "cat-file", "-e", f"HEAD:{rel}").returncode != 0
    assert not list(_transaction_dir(tmp_path).glob("*"))


def test_explicit_claim_transaction_rejects_detached_head(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _install_runtime_gate_hook(tmp_path)
    assert _git(tmp_path, "checkout", "--detach").returncode == 0
    claim, handoff, log = _write_runtime_claim(tmp_path)
    before = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()

    result = claim_guard.commit_claim_artifacts(
        tmp_path,
        claim,
        extra_paths=(handoff, log),
        claim_id="CLAIM-runtime-hook",
    )

    assert result["ok"] is False, result
    assert result["committed"] is False
    assert result["reason"] == "claim-commit-detached-head"
    assert _git(tmp_path, "rev-parse", "HEAD").stdout.strip() == before
