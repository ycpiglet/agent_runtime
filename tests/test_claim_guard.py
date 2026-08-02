"""Tests for claim_guard — commit claim artifacts so a concurrent reset/clean can't lose them.

Regression target (incident 2026-06-12): a freshly created claim JSON was left
*untracked*, so a sibling session's ``git reset --hard && git clean -fd`` erased it
and the claim had to be recreated. Committing the claim the instant it is written
makes it part of HEAD, which survives both reset and clean.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import claim_guard  # noqa: E402


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(root), capture_output=True, text=True)


def _reflog_rows(root: Path, ref: str) -> list[str]:
    result = _git(root, "reflog", "show", "--format=%H%x00%gs", ref)
    assert result.returncode == 0, result.stderr
    return result.stdout.splitlines()


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


def test_commit_claim_artifacts_allows_only_exact_inner_store_witness(tmp_path):
    _init_repo(tmp_path)
    claim = _write_claim(tmp_path)
    witness = claim.parent / ".claim-store"
    witness.write_text(
        '{"generation_id":"12345678-1234-4234-9234-123456789abc",'
        '"schema":"agent-runtime-task-claim-store/v1",'
        '"witness_claim_id":"CLAIM-test"}\n',
        encoding="utf-8",
    )

    result = claim_guard.commit_claim_artifacts(
        tmp_path,
        claim,
        extra_paths=(witness,),
        claim_id="CLAIM-test",
    )

    assert result["ok"] is True, result
    assert result["committed"] is True
    tracked = set(
        _git(tmp_path, "ls-files", "agents/runtime/task_claims").stdout.splitlines()
    )
    assert tracked == {
        "agents/runtime/task_claims/.claim-store",
        "agents/runtime/task_claims/CLAIM-test.json",
    }


def test_commit_claim_artifacts_rejects_lookalike_store_witness(tmp_path):
    _init_repo(tmp_path)
    claim = _write_claim(tmp_path)
    lookalike = claim.parent / ".claim-store-copy"
    lookalike.write_text("not authorized\n", encoding="utf-8")

    result = claim_guard.commit_claim_artifacts(
        tmp_path,
        claim,
        extra_paths=(lookalike,),
        claim_id="CLAIM-test",
    )

    assert result["ok"] is False
    assert result["reason"] == "claim-commit-non-artifact-path"


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


def test_explicit_claim_transaction_rejects_symlinked_symbolic_head(
    tmp_path: Path,
) -> None:
    _init_repo(tmp_path)
    _install_runtime_gate_hook(tmp_path)
    before = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()
    git_dir = tmp_path / ".git"
    symbolic_ref = _git(tmp_path, "symbolic-ref", "-q", "HEAD").stdout.strip()
    (git_dir / "HEAD").unlink()
    (git_dir / "HEAD").symlink_to(symbolic_ref)
    assert _git(tmp_path, "rev-parse", "HEAD").stdout.strip() == before
    claim, handoff, log = _write_runtime_claim(tmp_path)

    result = claim_guard.commit_claim_artifacts(
        tmp_path,
        claim,
        extra_paths=(handoff, log),
        claim_id="CLAIM-runtime-hook",
    )

    assert result["ok"] is False, result
    assert result["committed"] is False
    assert result["reason"] == "claim-commit-symbolic-head-seal-failed"
    assert _git(tmp_path, "rev-parse", "HEAD").stdout.strip() == before
    assert not list(_transaction_dir(tmp_path).glob("*"))


def test_explicit_claim_transaction_fails_closed_without_nofollow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_repo(tmp_path)
    _install_runtime_gate_hook(tmp_path)
    before = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()
    claim, handoff, log = _write_runtime_claim(tmp_path)
    monkeypatch.delattr(claim_guard.os, "O_NOFOLLOW")

    result = claim_guard.commit_claim_artifacts(
        tmp_path,
        claim,
        extra_paths=(handoff, log),
        claim_id="CLAIM-runtime-hook",
    )

    assert result["ok"] is False, result
    assert result["committed"] is False
    assert result["reason"] == "claim-commit-symbolic-head-seal-unsupported"
    assert _git(tmp_path, "rev-parse", "HEAD").stdout.strip() == before
    assert not list(_transaction_dir(tmp_path).glob("*"))


def test_explicit_claim_transaction_loses_compare_and_swap_ref_race(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_repo(tmp_path)
    _install_runtime_gate_hook(tmp_path)
    claim, handoff, log = _write_runtime_claim(tmp_path)
    original_ref = _git(tmp_path, "symbolic-ref", "-q", "HEAD").stdout.strip()
    original_git = claim_guard._git
    race: dict[str, str] = {}

    def racing_git(
        root: Path,
        args: list[str],
        *,
        env: dict[str, str] | None = None,
    ) -> dict[str, object]:
        if args and args[0] == "update-ref" and not race:
            old_oid = args[-1]
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
                ["update-ref", original_ref, concurrent, old_oid],
                env=claim_guard._repository_env(),
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


def test_explicit_claim_transaction_rejects_equal_oid_symbolic_head_switch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Git's prepared transaction must reject a switched equal-OID branch."""

    _init_repo(tmp_path)
    _install_runtime_gate_hook(tmp_path)
    assert _git(tmp_path, "branch", "concurrent-branch").returncode == 0
    start_head = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()
    original_ref = _git(tmp_path, "symbolic-ref", "-q", "HEAD").stdout.strip()
    claim, handoff, log = _write_runtime_claim(tmp_path)
    original_git = claim_guard._git
    switch: dict[str, object] = {}

    def switching_git(
        root: Path,
        args: list[str],
        *,
        env: dict[str, str] | None = None,
    ) -> dict[str, object]:
        if args and args[0] == "update-ref" and not switch:
            switch_env = dict(os.environ)
            for key in (
                "GIT_DIR",
                "GIT_COMMON_DIR",
                "GIT_WORK_TREE",
                "GIT_INDEX_FILE",
                claim_guard.CLAIM_COMMIT_TRANSACTION_ENV,
            ):
                switch_env.pop(key, None)
            switched = original_git(
                root,
                ["symbolic-ref", "HEAD", "refs/heads/concurrent-branch"],
                env=switch_env,
            )
            switch.update(switched)
        return original_git(root, args, env=env)

    monkeypatch.setattr(claim_guard, "_git", switching_git)
    result = claim_guard.commit_claim_artifacts(
        tmp_path,
        claim,
        extra_paths=(handoff, log),
        claim_id="CLAIM-runtime-hook",
    )

    assert switch["code"] == 0
    assert result["ok"] is False, result
    assert result["committed"] is False
    assert result["reason"].startswith("claim-commit-ref-update-failed:")
    assert (
        _git(tmp_path, "symbolic-ref", "-q", "HEAD").stdout.strip()
        == "refs/heads/concurrent-branch"
    )
    assert _git(tmp_path, "rev-parse", "HEAD").stdout.strip() == start_head
    assert _git(tmp_path, "rev-parse", original_ref).stdout.strip() == start_head
    rel = claim.relative_to(tmp_path).as_posix()
    assert _git(tmp_path, "cat-file", "-e", f"{original_ref}:{rel}").returncode != 0
    assert (
        _git(
            tmp_path,
            "cat-file",
            "-e",
            f"refs/heads/concurrent-branch:{rel}",
        ).returncode
        != 0
    )
    assert not list(_transaction_dir(tmp_path).glob("*"))


def test_post_commit_hook_cannot_switch_symbolic_head_after_publication(
    tmp_path: Path,
) -> None:
    _init_repo(tmp_path)
    _install_runtime_gate_hook(tmp_path)
    assert _git(tmp_path, "branch", "concurrent-branch").returncode == 0
    original_ref = _git(tmp_path, "symbolic-ref", "-q", "HEAD").stdout.strip()
    post_hook = tmp_path / ".githooks" / "post-commit"
    post_hook.write_text(
        "#!/bin/sh\n"
        "git symbolic-ref HEAD refs/heads/concurrent-branch\n",
        encoding="utf-8",
    )
    post_hook.chmod(0o755)
    claim, handoff, log = _write_runtime_claim(tmp_path)

    result = claim_guard.commit_claim_artifacts(
        tmp_path,
        claim,
        extra_paths=(handoff, log),
        claim_id="CLAIM-runtime-hook",
    )

    assert result["ok"] is True, result
    assert "post_commit_warning" in result
    assert _git(tmp_path, "symbolic-ref", "-q", "HEAD").stdout.strip() == original_ref
    assert _git(tmp_path, "rev-parse", "HEAD").stdout.strip() == result["commit"]
    assert not list(_transaction_dir(tmp_path).glob("*"))


def test_reference_transaction_hook_can_reject_claim_publication(
    tmp_path: Path,
) -> None:
    _init_repo(tmp_path)
    _install_runtime_gate_hook(tmp_path)
    reference_hook = tmp_path / ".githooks" / "reference-transaction"
    reference_hook.write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' \"$1\" >> reference-transaction.log\n"
        "test \"$1\" != prepared\n",
        encoding="utf-8",
    )
    reference_hook.chmod(0o755)
    before = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()
    symbolic_ref = _git(tmp_path, "symbolic-ref", "-q", "HEAD").stdout.strip()
    head_reflog_before = _reflog_rows(tmp_path, "HEAD")
    branch_reflog_before = _reflog_rows(tmp_path, symbolic_ref)
    claim, handoff, log = _write_runtime_claim(tmp_path)

    result = claim_guard.commit_claim_artifacts(
        tmp_path,
        claim,
        extra_paths=(handoff, log),
        claim_id="CLAIM-runtime-hook",
    )

    assert result["ok"] is False, result
    assert result["committed"] is False
    assert result["reason"].startswith("claim-commit-ref-update-failed:")
    assert _git(tmp_path, "rev-parse", "HEAD").stdout.strip() == before
    assert _reflog_rows(tmp_path, "HEAD") == head_reflog_before
    assert _reflog_rows(tmp_path, symbolic_ref) == branch_reflog_before
    assert (tmp_path / "reference-transaction.log").read_text(
        encoding="utf-8"
    ).splitlines() == ["prepared", "aborted"]
    assert not list(_transaction_dir(tmp_path).glob("*"))


def test_post_publication_symbolic_switch_cannot_return_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_repo(tmp_path)
    _install_runtime_gate_hook(tmp_path)
    assert _git(tmp_path, "branch", "concurrent-branch").returncode == 0
    original_ref = _git(tmp_path, "symbolic-ref", "-q", "HEAD").stdout.strip()
    start_head = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()
    post_hook = tmp_path / ".githooks" / "post-commit"
    post_hook.write_text(
        "#!/bin/sh\n"
        "printf 'ran\\n' > post-commit-ran.log\n",
        encoding="utf-8",
    )
    post_hook.chmod(0o755)
    claim, handoff, log = _write_runtime_claim(tmp_path)
    original_acquire = claim_guard._acquire_owned_lock
    race: dict[str, object] = {}

    def switch_then_lock(path: Path) -> tuple[int, int] | None:
        if not race:
            switched = claim_guard._git(
                tmp_path,
                ["symbolic-ref", "HEAD", "refs/heads/concurrent-branch"],
                env=claim_guard._repository_env(),
            )
            race.update(switched)
        return original_acquire(path)

    monkeypatch.setattr(claim_guard, "_acquire_owned_lock", switch_then_lock)
    result = claim_guard.commit_claim_artifacts(
        tmp_path,
        claim,
        extra_paths=(handoff, log),
        claim_id="CLAIM-runtime-hook",
    )

    assert race["code"] == 0
    assert result["ok"] is False, result
    assert result["committed"] is True
    assert result["reason"] == "claim-commit-sealed-head-identity-changed"
    assert result["publication_state"] == "published_unverified"
    assert (
        _git(tmp_path, "symbolic-ref", "-q", "HEAD").stdout.strip()
        == "refs/heads/concurrent-branch"
    )
    assert _git(tmp_path, "rev-parse", original_ref).stdout.strip() == result["commit"]
    assert _git(tmp_path, "rev-parse", "HEAD").stdout.strip() == start_head
    assert not (tmp_path / "post-commit-ran.log").exists()
    assert not list(_transaction_dir(tmp_path).glob("*"))


def test_post_publication_symbolic_roundtrip_cannot_return_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A final-state-preserving A→B→A switch must still break the HEAD seal."""

    _init_repo(tmp_path)
    _install_runtime_gate_hook(tmp_path)
    assert _git(tmp_path, "branch", "concurrent-branch").returncode == 0
    original_ref = _git(tmp_path, "symbolic-ref", "-q", "HEAD").stdout.strip()
    post_hook = tmp_path / ".githooks" / "post-commit"
    post_hook.write_text(
        "#!/bin/sh\n"
        "printf 'ran\\n' > post-commit-ran.log\n",
        encoding="utf-8",
    )
    post_hook.chmod(0o755)
    claim, handoff, log = _write_runtime_claim(tmp_path)
    original_acquire = claim_guard._acquire_owned_lock
    switches: list[int] = []

    def roundtrip_then_lock(path: Path) -> tuple[int, int] | None:
        if not switches:
            for target in ("refs/heads/concurrent-branch", original_ref):
                switched = claim_guard._git(
                    tmp_path,
                    ["symbolic-ref", "HEAD", target],
                    env=claim_guard._repository_env(),
                )
                switches.append(int(switched["code"]))
        return original_acquire(path)

    monkeypatch.setattr(claim_guard, "_acquire_owned_lock", roundtrip_then_lock)
    result = claim_guard.commit_claim_artifacts(
        tmp_path,
        claim,
        extra_paths=(handoff, log),
        claim_id="CLAIM-runtime-hook",
    )

    assert switches == [0, 0]
    assert result["ok"] is False, result
    assert result["committed"] is True
    assert result["publication_state"] == "published_unverified"
    assert result["reason"] == "claim-commit-sealed-head-identity-changed"
    assert _git(tmp_path, "symbolic-ref", "-q", "HEAD").stdout.strip() == original_ref
    assert _git(tmp_path, "rev-parse", "HEAD").stdout.strip() == result["commit"]
    assert not (tmp_path / "post-commit-ran.log").exists()
    assert not list(_transaction_dir(tmp_path).glob("*"))


def test_explicit_claim_transaction_updates_actual_head_and_branch_reflogs(
    tmp_path: Path,
) -> None:
    """Crash-safe publication must retain native worktree recovery semantics."""

    _init_repo(tmp_path)
    _install_runtime_gate_hook(tmp_path)
    symbolic_ref = _git(tmp_path, "symbolic-ref", "-q", "HEAD").stdout.strip()
    head_before = _reflog_rows(tmp_path, "HEAD")
    branch_before = _reflog_rows(tmp_path, symbolic_ref)
    claim, handoff, log = _write_runtime_claim(tmp_path)

    result = claim_guard.commit_claim_artifacts(
        tmp_path,
        claim,
        extra_paths=(handoff, log),
        claim_id="CLAIM-runtime-hook",
    )

    assert result["ok"] is True, result
    expected = (
        f"{result['commit']}\x00"
        "claim-guard: chore(claim): persist CLAIM-runtime-hook "
        "(crash-safety guard)"
    )
    head_after = _reflog_rows(tmp_path, "HEAD")
    branch_after = _reflog_rows(tmp_path, symbolic_ref)
    assert head_after == [expected, *head_before]
    assert branch_after == [expected, *branch_before]


def test_explicit_claim_transaction_creates_reflogs_when_logging_is_disabled(
    tmp_path: Path,
) -> None:
    _init_repo(tmp_path)
    _install_runtime_gate_hook(tmp_path)
    symbolic_ref = _git(tmp_path, "symbolic-ref", "-q", "HEAD").stdout.strip()
    assert _git(tmp_path, "config", "core.logAllRefUpdates", "false").returncode == 0
    for ref in ("HEAD", symbolic_ref):
        path = claim_guard._git_path(
            tmp_path,
            f"logs/{ref}",
            env=claim_guard._repository_env(),
        )
        assert path is not None
        path.unlink(missing_ok=True)
    claim, handoff, log = _write_runtime_claim(tmp_path)

    result = claim_guard.commit_claim_artifacts(
        tmp_path,
        claim,
        extra_paths=(handoff, log),
        claim_id="CLAIM-runtime-hook",
    )

    assert result["ok"] is True, result
    assert result["publication_state"] == "verified"
    expected = (
        f"{result['commit']}\x00"
        "claim-guard: chore(claim): persist CLAIM-runtime-hook "
        "(crash-safety guard)"
    )
    assert _reflog_rows(tmp_path, "HEAD") == [expected]
    assert _reflog_rows(tmp_path, symbolic_ref) == [expected]


def test_explicit_claim_transaction_respects_external_head_lock(
    tmp_path: Path,
) -> None:
    _init_repo(tmp_path)
    _install_runtime_gate_hook(tmp_path)
    claim, handoff, log = _write_runtime_claim(tmp_path)
    before = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()
    git_dir = Path(
        _git(tmp_path, "rev-parse", "--absolute-git-dir").stdout.strip()
    )
    head_lock = git_dir / "HEAD.lock"
    head_lock.write_text("external lock\n", encoding="utf-8")

    try:
        result = claim_guard.commit_claim_artifacts(
            tmp_path,
            claim,
            extra_paths=(handoff, log),
            claim_id="CLAIM-runtime-hook",
        )

        assert result["ok"] is False, result
        assert result["committed"] is False
        assert result["reason"] == "claim-commit-head-lock-unavailable"
        assert _git(tmp_path, "rev-parse", "HEAD").stdout.strip() == before
        assert head_lock.read_text(encoding="utf-8") == "external lock\n"
        assert not list(_transaction_dir(tmp_path).glob("*"))
    finally:
        head_lock.unlink()


def test_linked_worktree_uses_actual_head_lock_and_private_ref_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    linked = tmp_path / "linked"
    source.mkdir()
    _init_repo(source)
    added = _git(
        source,
        "worktree",
        "add",
        "-q",
        "-b",
        "claim-linked",
        str(linked),
    )
    assert added.returncode == 0, added.stderr
    _install_runtime_gate_hook(linked)
    assert (
        _git(linked, "config", "extensions.worktreeConfig", "true").returncode
        == 0
    )
    assert (
        _git(linked, "config", "--local", "--unset-all", "core.hooksPath").returncode
        == 0
    )
    assert (
        _git(
            linked,
            "config",
            "--worktree",
            "core.hooksPath",
            ".githooks",
        ).returncode
        == 0
    )
    assert _git(linked, "branch", "concurrent-branch").returncode == 0
    reference_hook = linked / ".githooks" / "reference-transaction"
    reference_hook.write_text(
        "#!/bin/sh\n"
        "if test \"$1\" = prepared; then\n"
        "  if git symbolic-ref HEAD refs/heads/concurrent-branch; then\n"
        "    printf 'prepared:switched\\n' >> reference-transaction.log\n"
        "  else\n"
        "    printf 'prepared:blocked\\n' >> reference-transaction.log\n"
        "  fi\n"
        "else\n"
        "  printf '%s\\n' \"$1\" >> reference-transaction.log\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    reference_hook.chmod(0o755)
    start_head = _git(linked, "rev-parse", "HEAD").stdout.strip()
    original_ref = _git(linked, "symbolic-ref", "-q", "HEAD").stdout.strip()
    git_dir = Path(
        _git(linked, "rev-parse", "--absolute-git-dir").stdout.strip()
    ).resolve()
    common_raw = Path(
        _git(linked, "rev-parse", "--git-common-dir").stdout.strip()
    )
    common_dir = (
        common_raw if common_raw.is_absolute() else linked / common_raw
    ).resolve()
    assert git_dir != common_dir
    claim, handoff, log = _write_runtime_claim(linked)
    original_git = claim_guard._git
    observed: dict[str, object] = {}

    def inspect_and_switch_git(
        root: Path,
        args: list[str],
        *,
        env: dict[str, str] | None = None,
    ) -> dict[str, object]:
        if args and args[0] == "update-ref" and not observed:
            assert env is not None
            context = Path(env["GIT_CONFIG_VALUE_0"])
            observed.update(
                {
                    "context": context,
                    "dir_mode": stat.S_IMODE(context.stat().st_mode),
                    "hook_mode": stat.S_IMODE(
                        (context / "reference-transaction").stat().st_mode
                    ),
                    "hook_shebang": (
                        context / "reference-transaction"
                    ).read_text(encoding="utf-8").splitlines()[0],
                    "index_env": env.get("GIT_INDEX_FILE"),
                    "git_dir_env": env.get("GIT_DIR"),
                    "common_env": env.get("GIT_COMMON_DIR"),
                    "namespace_env": env.get("GIT_NAMESPACE"),
                    "expected_ref": env.get(claim_guard.CLAIM_REF_EXPECTED_ENV),
                    "expected_old": env.get(claim_guard.CLAIM_REF_OLD_ENV),
                    "expected_lock": env.get(
                        claim_guard.CLAIM_REF_HEAD_LOCK_ENV
                    ),
                    "expected_head_path": env.get(
                        claim_guard.CLAIM_REF_HEAD_PATH_ENV
                    ),
                    "expected_head_device": env.get(
                        claim_guard.CLAIM_REF_HEAD_DEVICE_ENV
                    ),
                    "expected_head_inode": env.get(
                        claim_guard.CLAIM_REF_HEAD_INODE_ENV
                    ),
                    "original_hook": env.get(
                        claim_guard.CLAIM_REF_ORIGINAL_HOOK_ENV
                    ),
                }
            )
        return original_git(root, args, env=env)

    monkeypatch.setattr(claim_guard, "_git", inspect_and_switch_git)
    result = claim_guard.commit_claim_artifacts(
        linked,
        claim,
        extra_paths=(handoff, log),
        claim_id="CLAIM-runtime-hook",
    )

    assert result["ok"] is True, result
    assert observed["dir_mode"] == 0o700
    assert observed["hook_mode"] == 0o700
    assert observed["hook_shebang"] == f"#!{Path(sys.executable).resolve()}"
    assert observed["index_env"] is None
    assert observed["git_dir_env"] is None
    assert observed["common_env"] is None
    assert observed["namespace_env"] is None
    assert observed["expected_ref"] == original_ref
    assert observed["expected_old"] == start_head
    assert observed["expected_lock"] == str((git_dir / "HEAD.lock").resolve())
    assert observed["expected_head_path"] == str((git_dir / "HEAD").absolute())
    assert int(observed["expected_head_device"]) > 0
    assert int(observed["expected_head_inode"]) > 0
    assert observed["original_hook"] == str(reference_hook.resolve())
    assert not Path(observed["context"]).exists()
    assert _git(linked, "symbolic-ref", "-q", "HEAD").stdout.strip() == original_ref
    assert _git(linked, "rev-parse", "HEAD").stdout.strip() == result["commit"]
    assert (linked / "reference-transaction.log").read_text(
        encoding="utf-8"
    ).splitlines() == ["prepared:blocked", "committed"]
    assert (
        _git(linked, "rev-parse", "concurrent-branch").stdout.strip()
        == start_head
    )
    assert not list(_transaction_dir(linked).glob("*"))


def test_linked_claim_transaction_updates_only_its_actual_head_reflog(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    linked = tmp_path / "linked"
    source.mkdir()
    _init_repo(source)
    added = _git(
        source,
        "worktree",
        "add",
        "-q",
        "-b",
        "claim-linked",
        str(linked),
    )
    assert added.returncode == 0, added.stderr
    _install_runtime_gate_hook(linked)
    assert (
        _git(linked, "config", "extensions.worktreeConfig", "true").returncode
        == 0
    )
    symbolic_ref = _git(linked, "symbolic-ref", "-q", "HEAD").stdout.strip()
    source_head_before = _reflog_rows(source, "HEAD")
    linked_head_before = _reflog_rows(linked, "HEAD")
    branch_before = _reflog_rows(linked, symbolic_ref)
    claim, handoff, log = _write_runtime_claim(linked)

    result = claim_guard.commit_claim_artifacts(
        linked,
        claim,
        extra_paths=(handoff, log),
        claim_id="CLAIM-runtime-hook",
    )

    assert result["ok"] is True, result
    expected = (
        f"{result['commit']}\x00"
        "claim-guard: chore(claim): persist CLAIM-runtime-hook "
        "(crash-safety guard)"
    )
    assert _reflog_rows(linked, "HEAD") == [expected, *linked_head_before]
    assert _reflog_rows(linked, symbolic_ref) == [expected, *branch_before]
    assert _reflog_rows(source, "HEAD") == source_head_before


def test_claim_transaction_ignores_repository_redirecting_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "target"
    foreign = tmp_path / "foreign"
    target.mkdir()
    foreign.mkdir()
    _init_repo(target)
    _init_repo(foreign)
    _install_runtime_gate_hook(target)
    claim, handoff, log = _write_runtime_claim(target)
    target_before = _git(target, "rev-parse", "HEAD").stdout.strip()
    foreign_before = _git(foreign, "rev-parse", "HEAD").stdout.strip()
    poisoned = {
        "GIT_DIR": str(foreign / ".git"),
        "GIT_COMMON_DIR": str(foreign / ".git"),
        "GIT_WORK_TREE": str(foreign),
        "GIT_INDEX_FILE": str(foreign / ".git" / "index"),
        "GIT_OBJECT_DIRECTORY": str(foreign / ".git" / "objects"),
        "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(target / ".git" / "objects"),
        "GIT_NAMESPACE": "foreign-namespace",
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "core.hooksPath",
        "GIT_CONFIG_VALUE_0": "/definitely/not/a/runtime/hook",
        claim_guard.CLAIM_REF_ROOT_ENV: str(foreign),
        claim_guard.CLAIM_REF_EXPECTED_ENV: "refs/heads/foreign",
        claim_guard.CLAIM_REF_OLD_ENV: foreign_before,
        claim_guard.CLAIM_REF_NEW_ENV: foreign_before,
        claim_guard.CLAIM_REF_HEAD_LOCK_ENV: str(foreign / ".git" / "HEAD.lock"),
        claim_guard.CLAIM_REF_HEAD_PATH_ENV: str(foreign / ".git" / "HEAD"),
        claim_guard.CLAIM_REF_HEAD_DEVICE_ENV: "1",
        claim_guard.CLAIM_REF_HEAD_INODE_ENV: "1",
        claim_guard.CLAIM_REF_ORIGINAL_HOOK_ENV: "/definitely/not/a/runtime/hook",
    }
    for key, value in poisoned.items():
        monkeypatch.setenv(key, value)

    result = claim_guard.commit_claim_artifacts(
        target,
        claim,
        extra_paths=(handoff, log),
        claim_id="CLAIM-runtime-hook",
    )

    for key in poisoned:
        monkeypatch.delenv(key)
    assert result["ok"] is True, result
    assert _git(target, "rev-parse", "HEAD").stdout.strip() != target_before
    assert _git(foreign, "rev-parse", "HEAD").stdout.strip() == foreign_before
    rel = claim.relative_to(target).as_posix()
    assert _git(target, "cat-file", "-e", f"HEAD:{rel}").returncode == 0
    assert _git(foreign, "cat-file", "-e", f"HEAD:{rel}").returncode != 0
    assert not list(_transaction_dir(target).glob("*"))


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


def test_cli_returns_nonzero_for_published_unverified_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    partial = {
        "ok": False,
        "committed": True,
        "publication_state": "published_unverified",
        "reason": "claim-commit-post-publication-head-lock-unavailable",
        "paths": ["agents/runtime/task_claims/CLAIM-partial.json"],
    }
    monkeypatch.setattr(claim_guard, "sweep", lambda *_args, **_kwargs: partial)

    code = claim_guard.main(["--root", str(tmp_path), "--apply", "--json"])

    assert code == 1
    assert json.loads(capsys.readouterr().out) == partial
