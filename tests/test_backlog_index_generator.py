import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location("backlog_index_generator", ROOT / "scripts" / "backlog_index_generator.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_render_index_lists_tasksets_by_order(tmp_path):
    mod = _load()
    defs = tmp_path / "defs.json"
    defs.write_text(
        '{"tasksets": ['
        '{"task_set_id": "TASKSET-B", "display_name": "Bee", "order": 20},'
        '{"task_set_id": "TASKSET-A", "display_name": "Ay", "order": 10}]}',
        encoding="utf-8",
    )
    block = mod.render_index(defs)
    a = block.index("TASKSET-A")
    b = block.index("TASKSET-B")
    assert a < b                       # sorted by order
    assert mod.START in block and mod.END in block


def test_apply_block_inserts_then_replaces_preserving_narrative():
    mod = _load()
    block1 = mod.START + "\nGEN-1\n" + mod.END
    block2 = mod.START + "\nGEN-2\n" + mod.END
    original = "# Backlog\n\n## Narrative 2026-06-15\n\n- planner note\n"
    once = mod.apply_block(original, block1)
    assert "GEN-1" in once and "planner note" in once and once.count(mod.START) == 1
    # regenerating replaces only the block, narrative preserved, no duplicate block
    twice = mod.apply_block(once, block2)
    assert "GEN-2" in twice and "GEN-1" not in twice
    assert "planner note" in twice and twice.count(mod.START) == 1
