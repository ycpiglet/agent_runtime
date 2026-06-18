import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location("org_read_api", ROOT / "scripts" / "org_read_api.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _fixture(tmp: Path):
    (tmp / "agents" / "project").mkdir(parents=True)
    (tmp / "agents" / "project" / "ORG-MODEL.yml").write_text(
        "schema: x\nteams:\n  - id: engineering\n    display_name: Engineering\n"
        "roles:\n  - id: lead-engineer\n    tier: planner\n    team: engineering\n"
        "    aliases: [lead_engineer, lead-engineer]\n",
        encoding="utf-8",
    )
    inst = tmp / "agents" / "runtime" / "instances"
    inst.mkdir(parents=True)
    (inst / "i1.json").write_text(json.dumps({"role": "lead_engineer", "display_name": "Eng-1"}), encoding="utf-8")
    tasks = tmp / "agents" / "lead_engineer" / "tasks"
    tasks.mkdir(parents=True)
    (tasks / "TASK-AR-901.md").write_text(
        "---\nid: TASK-AR-901\nstatus: planned\ntask_set_id: TS-X\nest_tokens: 100\n---\n", encoding="utf-8")
    (tasks / "TASK-AR-902.md").write_text(
        "---\nid: TASK-AR-902\nstatus: completed\ntask_set_id: TS-X\nest_tokens: 100\nactual_tokens: 80\n---\n",
        encoding="utf-8")


def test_org_tree_groups_live_instances_by_team_and_role(tmp_path):
    mod = _load()
    _fixture(tmp_path)
    tree = mod.org_tree(tmp_path)
    assert tree["engineering"]["lead-engineer"] == ["Eng-1"]   # alias resolved


def test_org_tree_exposes_business_operations_teams_from_live_registry():
    mod = _load()
    tree = mod.org_tree(ROOT)
    assert "finance-accounting" in tree
    assert "marketing-growth" in tree
    assert "sales-revenue" in tree


def test_org_tree_exposes_split_uiux_roles_from_live_registry():
    mod = _load()
    tree = mod.org_tree(ROOT)
    assert "ui-ux" in tree
    reg = mod.load_org(ROOT)
    roles = {role["id"] for role in reg["roles"] if role.get("team") == "ui-ux"}
    assert {"lead-designer", "design-system-steward", "interface-designer", "ux-evaluator"} <= roles


def test_work_state_buckets_waiting_and_done(tmp_path):
    mod = _load()
    _fixture(tmp_path)
    state = mod.work_state(tmp_path)
    assert state["TS-X"]["waiting"] == 1
    assert state["TS-X"]["done"] == 1
    assert len(state["TS-X"]["tasks"]) == 2


def test_token_ledger_sums_est_vs_actual(tmp_path):
    mod = _load()
    _fixture(tmp_path)
    led = mod.token_ledger(tmp_path)
    assert led["TS-X"]["est_tokens"] == 200
    assert led["TS-X"]["actual_tokens"] == 80
