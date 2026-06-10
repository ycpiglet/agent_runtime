from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "governance_ops_report.py"


def load_module():
    spec = importlib.util.spec_from_file_location("governance_ops_report", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_status_blocks_on_any_block():
    report = load_module()
    summary = {
        "collaboration": report.GateSummary("collab", 1, 0, 0),
        "runtime_assets": report.GateSummary("assets", 0, 0, 0),
        "state_sync": report.GateSummary("sync", 0, 0, 0),
    }

    assert report.status_for(summary) == "block"


def test_render_uses_owner_brief_frame():
    report = load_module()
    summary = {
        "collaboration": report.GateSummary("collab", 0, 1, 1),
        "runtime_assets": report.GateSummary("assets", 0, 0, 0, "assets=1"),
        "state_sync": report.GateSummary("sync", 0, 0, 0),
        "asset_kind_counts": {"gate": 1},
        "asset_lifecycle_counts": {"keep": 1},
        "low_reuse_assets": ["gate.example"],
        "asset_metrics": [
            type(
                "Metric",
                (),
                {
                    "asset_id": "gate.example",
                    "kind": "gate",
                    "lifecycle": "keep",
                    "usage_count": 1,
                    "distinct_evidence_hits": 1,
                },
            )()
        ],
    }

    rendered = report.render(summary, generated_at="2026-06-10T23:50:00+09:00")

    assert "## Bottom Line" in rendered
    assert "## Signal" in rendered
    assert "## Insight" in rendered
    assert "## Decision" in rendered
    assert "## Action Board" in rendered
    assert "## Next" in rendered
    assert "gate.example" in rendered
