from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "template_mirror_gate.py"
CONTRACT = REPO_ROOT / "agents" / "project" / "TEMPLATE-MIRROR-CONTRACT.json"
ROOT_SCRIPTS = REPO_ROOT / "scripts"
TEMPLATE_SCRIPTS = (
    REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts"
)
INTENTIONAL = {
    "compound_record.py",
    "owner_governance_gate.py",
    "stop_hook_owner_governance.py",
}
PORTABLE_REPAIRS = {
    "collaboration_concurrency_gate.py",
    "collaboration_governance_gate.py",
    "footprint_conflict_gate.py",
    "now.py",
    "taskset_work_gate.py",
}


def _eligible(directory: Path) -> dict[str, Path]:
    return {
        path.relative_to(directory).as_posix(): path
        for path in directory.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix in {".py", ".cmd"}
    }


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(root),
            "--check",
            "--json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _write_contract_payload(root: Path, payload: object) -> None:
    path = root / "agents" / "project" / "TEMPLATE-MIRROR-CONTRACT.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_contract(
    root: Path,
    divergences: dict[str, dict[str, str]],
    *,
    expected_common: list[str] | None = None,
    package_sources: dict[str, str] | None = None,
) -> None:
    if expected_common is None:
        source = _eligible(root / "scripts")
        template = _eligible(
            root / "src" / "agent_runtime" / "templates" / "project" / "scripts"
        )
        expected_common = sorted(source.keys() & template.keys())
    _write_contract_payload(
        root,
        {
            "schema": "agent-runtime-template-mirror-contract/v2",
            "expected_common": expected_common,
            "package_sources": package_sources or {},
            "intentional_divergences": divergences,
        },
    )


def _write_pair(root: Path, name: str, source: str, template: str) -> tuple[Path, Path]:
    left = root / "scripts" / name
    right = (
        root
        / "src"
        / "agent_runtime"
        / "templates"
        / "project"
        / "scripts"
        / name
    )
    left.parent.mkdir(parents=True, exist_ok=True)
    right.parent.mkdir(parents=True, exist_ok=True)
    left.write_text(source, encoding="utf-8")
    right.write_text(template, encoding="utf-8")
    return left, right


def test_product_common_script_census_has_only_three_pinned_variants() -> None:
    root_files = _eligible(ROOT_SCRIPTS)
    template_files = _eligible(TEMPLATE_SCRIPTS)
    common = sorted(root_files.keys() & template_files.keys())
    divergent = {
        path
        for path in common
        if root_files[path].read_bytes() != template_files[path].read_bytes()
    }

    assert len(common) == 86
    assert divergent == INTENTIONAL
    assert PORTABLE_REPAIRS.isdisjoint(divergent)
    assert CONTRACT.is_file()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["schema"] == "agent-runtime-template-mirror-contract/v2"
    assert contract["expected_common"] == common
    assert contract["package_sources"] == {
        "agent_runtime/claim_store.py": "src/agent_runtime/claim_store.py"
    }
    assert (
        ROOT_SCRIPTS / "agent_runtime" / "claim_store.py"
    ).read_bytes() == (REPO_ROOT / "src" / "agent_runtime" / "claim_store.py").read_bytes()

    result = _run(REPO_ROOT)
    assert result.returncode == 0, result.stdout or result.stderr
    payload = json.loads(result.stdout)
    assert payload["expected_common"] == 86
    assert payload["current_common"] == 86
    assert payload["eligible_common"] == 86
    assert payload["identical"] == 83
    assert payload["intentional"] == 3
    assert payload["package_sources"] == 1
    assert payload["findings"] == []


def test_package_source_drift_blocks(tmp_path: Path) -> None:
    _write_pair(
        tmp_path,
        "agent_runtime/helper.py",
        "same\n",
        "same\n",
    )
    package = tmp_path / "src" / "agent_runtime" / "helper.py"
    package.parent.mkdir(parents=True, exist_ok=True)
    package.write_text("stale\n", encoding="utf-8")
    _write_contract(
        tmp_path,
        {},
        package_sources={
            "agent_runtime/helper.py": "src/agent_runtime/helper.py"
        },
    )

    result = _run(tmp_path)

    assert result.returncode == 1
    assert "mirror:package-source-drift:agent_runtime/helper.py" in result.stdout
    assert "mirror:package-template-drift:agent_runtime/helper.py" in result.stdout


def test_expected_source_side_missing_blocks(tmp_path: Path) -> None:
    template = (
        tmp_path
        / "src"
        / "agent_runtime"
        / "templates"
        / "project"
        / "scripts"
        / "portable.py"
    )
    template.parent.mkdir(parents=True, exist_ok=True)
    template.write_text("portable\n", encoding="utf-8")
    (tmp_path / "scripts").mkdir(parents=True)
    _write_contract(tmp_path, {}, expected_common=["portable.py"])

    result = _run(tmp_path)

    assert result.returncode == 1
    assert "mirror:expected-source-missing:portable.py" in result.stdout


def test_expected_template_side_missing_blocks(tmp_path: Path) -> None:
    source = tmp_path / "scripts" / "portable.py"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("portable\n", encoding="utf-8")
    (
        tmp_path
        / "src"
        / "agent_runtime"
        / "templates"
        / "project"
        / "scripts"
    ).mkdir(parents=True)
    _write_contract(tmp_path, {}, expected_common=["portable.py"])

    result = _run(tmp_path)

    assert result.returncode == 1
    assert "mirror:expected-template-missing:portable.py" in result.stdout


def test_deleting_one_side_of_formerly_common_path_blocks(tmp_path: Path) -> None:
    _, template = _write_pair(tmp_path, "portable.py", "same\n", "same\n")
    _write_contract(tmp_path, {})
    template.unlink()

    result = _run(tmp_path)

    assert result.returncode == 1
    assert "mirror:expected-template-missing:portable.py" in result.stdout


def test_unreviewed_new_common_path_blocks(tmp_path: Path) -> None:
    _write_pair(tmp_path, "expected.py", "same\n", "same\n")
    _write_contract(tmp_path, {}, expected_common=["expected.py"])
    _write_pair(tmp_path, "new_portable.py", "new\n", "new\n")

    result = _run(tmp_path)

    assert result.returncode == 1
    assert "mirror:unexpected-common:new_portable.py" in result.stdout


def test_legitimate_one_sided_assets_outside_inventory_are_allowed(
    tmp_path: Path,
) -> None:
    _write_pair(tmp_path, "portable.py", "same\n", "same\n")
    source_only = tmp_path / "scripts" / "source_only.py"
    source_only.write_text("source\n", encoding="utf-8")
    template_only = (
        tmp_path
        / "src"
        / "agent_runtime"
        / "templates"
        / "project"
        / "scripts"
        / "template_only.py"
    )
    template_only.write_text("template\n", encoding="utf-8")
    _write_contract(tmp_path, {}, expected_common=["portable.py"])

    result = _run(tmp_path)

    assert result.returncode == 0, result.stdout or result.stderr
    payload = json.loads(result.stdout)
    assert payload["expected_common"] == 1
    assert payload["current_common"] == 1
    assert payload["findings"] == []


@pytest.mark.parametrize(
    ("expected_common", "finding"),
    [
        ("portable.py", "mirror:invalid-expected-common-list"),
        (["portable.py", "portable.py"], "mirror:duplicate-expected-path:portable.py"),
        (["../escape.py"], "mirror:invalid-expected-path:../escape.py"),
        (["z.py", "a.py"], "mirror:unsorted-expected-common"),
        ([7], "mirror:invalid-expected-path:7"),
    ],
)
def test_invalid_expected_inventory_blocks(
    tmp_path: Path,
    expected_common: object,
    finding: str,
) -> None:
    _write_pair(tmp_path, "portable.py", "same\n", "same\n")
    _write_pair(tmp_path, "a.py", "same\n", "same\n")
    _write_pair(tmp_path, "z.py", "same\n", "same\n")
    _write_contract_payload(
        tmp_path,
        {
            "schema": "agent-runtime-template-mirror-contract/v2",
            "expected_common": expected_common,
            "intentional_divergences": {},
        },
    )

    result = _run(tmp_path)

    assert result.returncode == 1
    assert finding in result.stdout


def test_intentional_divergence_must_belong_to_expected_inventory(
    tmp_path: Path,
) -> None:
    _write_pair(tmp_path, "expected.py", "same\n", "same\n")
    source, template = _write_pair(
        tmp_path, "variant.py", "source\n", "template\n"
    )
    _write_contract(
        tmp_path,
        {
            "variant.py": {
                "reason": "This variant is pinned but omitted from the reviewed expected inventory.",
                "source_sha256": _digest(source),
                "template_sha256": _digest(template),
            }
        },
        expected_common=["expected.py"],
    )

    result = _run(tmp_path)

    assert result.returncode == 1
    assert "mirror:exception-not-expected:variant.py" in result.stdout


def test_unlisted_drift_blocks(tmp_path: Path) -> None:
    _write_pair(tmp_path, "portable.py", "source\n", "stale\n")
    _write_contract(tmp_path, {})

    result = _run(tmp_path)

    assert result.returncode == 1
    assert "mirror:unlisted-drift:portable.py" in result.stdout


def test_digest_pinned_intentional_divergence_passes(tmp_path: Path) -> None:
    source, template = _write_pair(
        tmp_path, "variant.py", "source entrypoint\n", "standalone consumer\n"
    )
    _write_contract(
        tmp_path,
        {
            "variant.py": {
                "reason": "Source entrypoint and standalone consumer have different dependency boundaries.",
                "source_sha256": _digest(source),
                "template_sha256": _digest(template),
            }
        },
    )

    result = _run(tmp_path)

    assert result.returncode == 0, result.stdout or result.stderr
    payload = json.loads(result.stdout)
    assert payload["intentional"] == 1
    assert payload["findings"] == []


def test_stale_exception_that_became_identical_blocks(tmp_path: Path) -> None:
    source, template = _write_pair(tmp_path, "variant.py", "same\n", "same\n")
    _write_contract(
        tmp_path,
        {
            "variant.py": {
                "reason": "This reason is intentionally long enough but the exception is stale.",
                "source_sha256": _digest(source),
                "template_sha256": _digest(template),
            }
        },
    )

    result = _run(tmp_path)

    assert result.returncode == 1
    assert "mirror:stale-identical-exception:variant.py" in result.stdout


def test_exception_digest_mismatch_blocks(tmp_path: Path) -> None:
    source, template = _write_pair(tmp_path, "variant.py", "source\n", "template\n")
    _write_contract(
        tmp_path,
        {
            "variant.py": {
                "reason": "Both implementations are intentionally distinct and independently pinned.",
                "source_sha256": "sha256:" + "0" * 64,
                "template_sha256": _digest(template),
            }
        },
    )

    result = _run(tmp_path)

    assert result.returncode == 1
    assert "mirror:exception-source-digest-mismatch:variant.py" in result.stdout
    assert _digest(source) not in {"sha256:" + "0" * 64}


def test_exception_path_must_be_safe_and_common(tmp_path: Path) -> None:
    _write_pair(tmp_path, "same.py", "same\n", "same\n")
    _write_contract(
        tmp_path,
        {
            "../escape.py": {
                "reason": "Path traversal must never become a mirror exception boundary.",
                "source_sha256": "sha256:" + "0" * 64,
                "template_sha256": "sha256:" + "1" * 64,
            }
        },
    )

    result = _run(tmp_path)

    assert result.returncode == 1
    assert "mirror:invalid-exception-path:../escape.py" in result.stdout


def test_duplicate_exception_key_blocks(tmp_path: Path) -> None:
    source, template = _write_pair(
        tmp_path, "variant.py", "source\n", "template\n"
    )
    digest_source = _digest(source)
    digest_template = _digest(template)
    first = json.dumps(
        {
            "variant.py": {
                "reason": "First duplicate entry must not be silently overwritten.",
                "source_sha256": digest_source,
                "template_sha256": digest_template,
            }
        }
    )
    second = json.dumps(
        {
            "variant.py": {
                "reason": "Second duplicate entry must be rejected before validation.",
                "source_sha256": digest_source,
                "template_sha256": digest_template,
            }
        }
    )
    contract = (
        '{"schema":"agent-runtime-template-mirror-contract/v2",'
        '"expected_common":["variant.py"],'
        f'"intentional_divergences":{first},'
        f'"intentional_divergences":{second}}}'
    )
    contract_path = (
        tmp_path / "agents" / "project" / "TEMPLATE-MIRROR-CONTRACT.json"
    )
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(contract + "\n", encoding="utf-8")

    result = _run(tmp_path)

    assert result.returncode == 1
    assert "mirror:duplicate-contract-key:intentional_divergences" in result.stdout


def test_source_owner_chain_runs_mirror_gate_and_template_documents_omission() -> None:
    root_gate = (ROOT_SCRIPTS / "owner_governance_gate.py").read_text(
        encoding="utf-8"
    )
    template_gate = (TEMPLATE_SCRIPTS / "owner_governance_gate.py").read_text(
        encoding="utf-8"
    )

    assert '["scripts/template_mirror_gate.py", "--check"]' in root_gate
    assert '["scripts/template_mirror_gate.py", "--check"]' not in template_gate
    assert (
        "intentionally omitted: scripts/template_mirror_gate.py" in template_gate
    )
