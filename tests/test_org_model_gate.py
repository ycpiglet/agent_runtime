from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "scripts" / "org_model_gate.py"


def _load():
    spec = importlib.util.spec_from_file_location("org_model_gate", SPEC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_registry_loads_and_covers_existing_owners():
    mod = _load()
    reg = mod.load_registry()
    for value in ["lead_engineer", "lead-engineer", "qa", "research-agent",
                  "managing-partner", "release-integrity", "finance",
                  "accounting", "marketing", "sales", "operations",
                  "support", "strategy", "business-planning"]:
        assert mod.resolve_owner(value, reg) is not None, f"{value} unresolved"
    ids = [r["id"] for r in reg["roles"]]
    assert len(ids) == len(set(ids))
    assert all("_" not in i for i in ids)


def test_resolve_owner_aliases_and_unknown():
    mod = _load()
    reg = mod.load_registry()
    assert mod.resolve_owner("lead_engineer", reg)["id"] == "lead-engineer"
    assert mod.resolve_owner("lead-engineer", reg)["id"] == "lead-engineer"
    assert mod.resolve_owner("ci-cd", reg)["id"] == "release-integrity"
    assert mod.resolve_owner("totally-unknown-role", reg) is None


def test_business_operations_teams_and_aliases_resolve():
    mod = _load()
    reg = mod.load_registry()
    team_ids = {team["id"] for team in reg["teams"]}
    assert {
        "finance-accounting",
        "marketing-growth",
        "sales-revenue",
        "operations-support",
        "planning-strategy",
    } <= team_ids
    assert all("_" not in team_id for team_id in team_ids)

    expected_aliases = {
        "finance": "finance-controller",
        "billing": "accounting-operator",
        "asset-management": "asset-steward",
        "unit-economics": "revenue-analyst",
        "marketing": "marketing-lead",
        "seo": "content-marketer",
        "growth": "growth-analyst",
        "brand": "brand-steward",
        "sales": "sales-lead",
        "crm": "crm-operator",
        "partnerships": "partnership-manager",
        "revops": "sales-ops",
        "operations": "operations-lead",
        "helpdesk": "support-operator",
        "customer-success": "customer-success-steward",
        "runbook": "process-steward",
        "strategy": "strategy-lead",
        "business-planning": "planning-architect",
        "requirements": "business-analyst",
        "portfolio": "portfolio-steward",
    }
    for alias, role_id in expected_aliases.items():
        assert mod.resolve_owner(alias, reg)["id"] == role_id


def test_uiux_roles_are_split_but_legacy_alias_resolves():
    mod = _load()
    reg = mod.load_registry()
    expected_aliases = {
        "lead-designer": "lead-designer",
        "visual-designer": "lead-designer",
        "design-system": "design-system-steward",
        "token-steward": "design-system-steward",
        "interface-designer": "interface-designer",
        "uiux": "interface-designer",
        "ux-evaluator": "ux-evaluator",
        "accessibility": "ux-evaluator",
    }
    for alias, role_id in expected_aliases.items():
        assert mod.resolve_owner(alias, reg)["id"] == role_id


def test_check_reports_unresolved_but_is_watch_level(tmp_path, capsys):
    mod = _load()
    f = tmp_path / "TASK-X.md"
    f.write_text("---\nowner: nope-not-a-role\nkind: task\n---\n", encoding="utf-8")
    rc = mod.cmd_check([str(f)], enforce=False)
    out = capsys.readouterr().out
    assert "nope-not-a-role" in out
    assert rc == 0


def test_check_enforce_blocks_on_unresolved(tmp_path):
    mod = _load()
    f = tmp_path / "TASK-Y.md"
    f.write_text("---\nowner: nope\nkind: task\n---\n", encoding="utf-8")
    assert mod.cmd_check([str(f)], enforce=True) == 1


def test_governance_gate_invokes_org_model():
    text = (ROOT / "scripts" / "owner_governance_gate.py").read_text(encoding="utf-8")
    assert "org_model_gate.py" in text


def test_corrupt_registry_is_watch_safe(tmp_path, monkeypatch):
    # W4b finding #1: a watch check must never block governance, even if the
    # registry is missing/malformed. Fail-soft: watch -> 0, enforce -> 1.
    mod = _load()

    def boom(*a, **k):
        raise ValueError("corrupt registry")

    monkeypatch.setattr(mod, "load_registry", boom)
    f = tmp_path / "TASK-Z.md"
    f.write_text("---\nowner: x\n---\n", encoding="utf-8")
    assert mod.cmd_check([str(f)], enforce=False) == 0
    assert mod.cmd_check([str(f)], enforce=True) == 1
