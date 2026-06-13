"""Parity guard for the owner governance gate chain (TASK-AR-521).

The repo ships two copies of ``owner_governance_gate.py``:

- ``scripts/owner_governance_gate.py`` (root, canonical)
- ``src/agent_runtime/templates/project/scripts/owner_governance_gate.py`` (template)

Five independent W4b reviews flagged that the template chain silently drifted
from the root chain whenever a new gate was wired only into the root copy.
This test parses both ``checks`` lists via ``ast`` and enforces:

1. every template chain entry exists in the root chain,
2. shared entries appear in the same relative order,
3. any root entry absent from the template is an explicit, documented
   exception (so wiring a new gate into root without mirroring it forces a
   conscious decision here), and
4. every template chain entry's script ships in the template scripts
   directory, minus explicit known-missing exceptions.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT_GATE = REPO_ROOT / "scripts" / "owner_governance_gate.py"
TEMPLATE_GATE = (
    REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "owner_governance_gate.py"
)
TEMPLATE_SCRIPTS_DIR = REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts"

# Root chain entries intentionally NOT mirrored into the template chain.
# Adding a new gate to root without wiring it into the template fails this
# test unless the gap is consciously documented here AND as a comment in the
# template gate file.
DOCUMENTED_TEMPLATE_OMISSIONS: dict[str, str] = {
    "scripts/context_knowledge_gate.py": (
        "root-repo-specific: validates TASKSET-AR-CONTEXT-KNOWLEDGE contracts against "
        "src/agent_runtime/templates/**, agents/project/overlays/**, and root eval files "
        "that generated projects do not ship"
    ),
}

# Template chain entries whose script is known to be missing from the
# template scripts directory (pre-existing gap, tracked separately).
# If the script gets copied into the template, remove it here.
KNOWN_MISSING_TEMPLATE_SCRIPTS: dict[str, str] = {
    "scripts/planning_loop.py": (
        "pre-existing gap: chain entry shipped before the script; the 'gate' subcommand "
        "is portable but the script has not been copied into the template yet"
    ),
}


def _resolve_entry(node: ast.expr, assignments: dict[str, ast.expr]) -> ast.expr:
    """Resolve a chain element to its list literal (follows simple Name refs)."""
    seen: set[str] = set()
    while isinstance(node, ast.Name):
        if node.id in seen or node.id not in assignments:
            raise AssertionError(f"cannot resolve chain entry name: {node.id}")
        seen.add(node.id)
        node = assignments[node.id]
    return node


def _literal_argv(node: ast.expr) -> tuple[str, ...]:
    assert isinstance(node, ast.List), f"chain entry is not a list literal: {ast.dump(node)}"
    argv: list[str] = []
    for element in node.elts:
        assert isinstance(element, ast.Constant) and isinstance(element.value, str), (
            f"chain entry argument is not a string constant: {ast.dump(element)}"
        )
        argv.append(element.value)
    assert argv, "chain entry is empty"
    return tuple(argv)


def parse_chain(path: Path) -> list[tuple[str, ...]]:
    """Return the ``checks`` chain of ``main()`` as a list of argv tuples."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    main_fn = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main"
    )
    assignments: dict[str, ast.expr] = {}
    checks: ast.List | None = None
    for node in ast.walk(main_fn):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            assignments[target.id] = node.value
            if target.id == "checks":
                assert isinstance(node.value, ast.List), "checks must be a list literal"
                checks = node.value
    assert checks is not None, f"no `checks` assignment found in main() of {path}"
    return [_literal_argv(_resolve_entry(element, assignments)) for element in checks.elts]


def test_chains_are_parseable_and_nonempty() -> None:
    root_chain = parse_chain(ROOT_GATE)
    template_chain = parse_chain(TEMPLATE_GATE)
    assert len(root_chain) >= 20
    assert len(template_chain) >= 20
    # Each chain must be duplicate-free for the order comparison to be sound.
    assert len(set(root_chain)) == len(root_chain)
    assert len(set(template_chain)) == len(template_chain)


def test_every_template_entry_exists_in_root_chain() -> None:
    root_chain = set(parse_chain(ROOT_GATE))
    extras = [entry for entry in parse_chain(TEMPLATE_GATE) if entry not in root_chain]
    assert not extras, (
        "template chain has entries missing from the root chain "
        f"(add them to scripts/owner_governance_gate.py or drop them): {extras}"
    )


def test_shared_entries_keep_root_relative_order() -> None:
    root_chain = parse_chain(ROOT_GATE)
    template_chain = parse_chain(TEMPLATE_GATE)
    template_set = set(template_chain)
    shared_in_root_order = [entry for entry in root_chain if entry in template_set]
    assert template_chain == shared_in_root_order, (
        "template chain order drifted from root chain order.\n"
        f"expected (root order): {shared_in_root_order}\n"
        f"actual   (template):   {template_chain}"
    )


def test_root_entries_absent_from_template_are_documented_exceptions() -> None:
    template_set = set(parse_chain(TEMPLATE_GATE))
    missing_scripts = {entry[0] for entry in parse_chain(ROOT_GATE) if entry not in template_set}
    documented = set(DOCUMENTED_TEMPLATE_OMISSIONS)
    undocumented = missing_scripts - documented
    assert not undocumented, (
        "root governance chain entries are missing from the template chain without a "
        "documented exception. Mirror them into "
        "src/agent_runtime/templates/project/scripts/owner_governance_gate.py (copying the "
        "script into the template if needed) or add them to DOCUMENTED_TEMPLATE_OMISSIONS "
        f"with a reason: {sorted(undocumented)}"
    )
    stale = documented - missing_scripts
    assert not stale, (
        f"stale DOCUMENTED_TEMPLATE_OMISSIONS entries (now mirrored or removed): {sorted(stale)}"
    )


def test_documented_omissions_are_commented_in_template_gate() -> None:
    template_text = TEMPLATE_GATE.read_text(encoding="utf-8")
    for script in DOCUMENTED_TEMPLATE_OMISSIONS:
        assert f"intentionally omitted: {script}" in template_text, (
            f"template gate file lacks an `# intentionally omitted: {script} -- <reason>` comment"
        )


def test_template_chain_scripts_ship_in_template() -> None:
    missing = {
        entry[0]
        for entry in parse_chain(TEMPLATE_GATE)
        if not (TEMPLATE_SCRIPTS_DIR / Path(entry[0]).name).exists()
    }
    known = set(KNOWN_MISSING_TEMPLATE_SCRIPTS)
    unexpected = missing - known
    assert not unexpected, (
        "template chain references scripts that are not shipped under "
        f"src/agent_runtime/templates/project/scripts/: {sorted(unexpected)}"
    )
    stale = known - missing
    assert not stale, (
        f"stale KNOWN_MISSING_TEMPLATE_SCRIPTS entries (script now shipped): {sorted(stale)}"
    )


def test_evidence_index_generator_template_mirror_matches_root() -> None:
    root_script = (REPO_ROOT / "scripts" / "evidence_index_generator.py").read_text(encoding="utf-8")
    template_script = (TEMPLATE_SCRIPTS_DIR / "evidence_index_generator.py").read_text(encoding="utf-8")
    assert root_script == template_script, "template evidence_index_generator.py drifted from root copy"
