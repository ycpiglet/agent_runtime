from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_task_ar_297_evidence_inbox_contract_fields_are_declared():
    registry = (ROOT / "agents" / "project" / "evidence" / "README.md").read_text(encoding="utf-8")
    inbox = (ROOT / "agents" / "project" / "evidence" / "inbox" / "README.md").read_text(encoding="utf-8")
    meeting = (
        ROOT
        / "reviews"
        / "MEETING-2026-06-11-agent-runtime-rsi-operating-system-registration.md"
    ).read_text(encoding="utf-8")

    combined = "\n".join([registry, inbox])
    for token in [
        "source_type",
        "source_path",
        "task_ref",
        "task_set_id",
        "observed_failure",
        "observed_signal",
        "owner_boundary",
        "proposed_routing",
        "dedupe_key",
        "quality_check",
    ]:
        assert token in combined

    for phrase in [
        "Conversation record required",
        "Eval/verification registry required",
        "Failure/compound casebook required",
        "C option boundary",
        "TASKSET-AR-RSI-OPERATING-SYSTEM",
    ]:
        assert phrase in meeting


def test_task_ar_298_eval_and_verification_registry_contracts_are_declared():
    evaluations = (
        ROOT / "agents" / "project" / "evidence" / "evaluations" / "README.md"
    ).read_text(encoding="utf-8")
    verification = (
        ROOT / "agents" / "project" / "evidence" / "verification" / "README.md"
    ).read_text(encoding="utf-8")

    combined = "\n".join([evaluations, verification])
    for token in [
        "How To Add",
        "record_id",
        "source_command",
        "source_path",
        "scope_boundary",
        "local_deterministic",
        "provider_live",
        "proposal_precision",
        "proposal_recall",
        "eval_regression_rate",
        "repeated_failure_closure_rate",
        "evidence_to_task_latency",
        "free-form review scraping",
    ]:
        assert token in combined
