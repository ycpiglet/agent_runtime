import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location("work_hierarchy_closeout", ROOT / "scripts" / "work_hierarchy_closeout.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_run_gates_reports_pass_and_fail():
    mod = _load()
    results = mod.run_gates([
        [sys.executable, "-c", "import sys; sys.exit(0)"],
        [sys.executable, "-c", "import sys; sys.exit(1)"],
    ])
    assert results[0]["ok"] is True and results[0]["rc"] == 0
    assert results[1]["ok"] is False and results[1]["rc"] == 1


def test_gate_chain_defined():
    mod = _load()
    # the closeout chain must cover identity, classifier, owner-doc, taskset, readiness
    flat = " ".join(" ".join(str(c) for c in g) for g in mod.GATES)
    for needle in ("task_identity", "work_item_classifier", "owner_doc_format_gate",
                   "taskset_work_gate", "unit_readiness_report"):
        assert needle in flat, needle
