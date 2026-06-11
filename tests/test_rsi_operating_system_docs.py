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
        "false_positive_proposal_rate",
        "evidence_to_task_latency",
        "free-form review scraping",
    ]:
        assert token in combined


def test_task_ar_299_casebook_records_regression_routing_fields():
    readme = (ROOT / "agents" / "project" / "casebooks" / "README.md").read_text(encoding="utf-8")
    casebook = (
        ROOT / "agents" / "project" / "casebooks" / "failure-and-compound-casebook.md"
    ).read_text(encoding="utf-8")
    combined = "\n".join([readme, casebook])

    for token in [
        "symptom",
        "trigger",
        "owner_boundary",
        "affected_gate",
        "recurrence_count",
        "linked_regression_fixture",
        "accepted_watch",
        "needs_enforcement",
        "agents/lead_engineer/compound_log.md",
    ]:
        assert token in combined


def test_task_ar_300_proposal_contract_and_schema_include_rsi_os_fields():
    contract = (ROOT / "agents" / "project" / "EVIDENCE-TO-PROPOSAL-CONTRACT.md").read_text(
        encoding="utf-8"
    )
    schema = (ROOT / "schemas" / "planning-proposal.schema.json").read_text(encoding="utf-8")
    combined = "\n".join([contract, schema])

    for token in [
        "evidence_ids",
        "affected_owner_boundary",
        "expected_verification_command",
        "estimated_blast_radius",
        "proposal_output",
        "rejection_reason",
        "failure_regression_links",
        "task",
        "plan",
        "doc",
        "eval",
        "release",
        "skill",
        "no_action",
        "apply gate",
    ]:
        assert token in combined


def test_task_ar_301_council_protocol_and_metrics_are_structured():
    protocol = (ROOT / "agents" / "project" / "DIVERSITY-COUNCIL-PROTOCOL.md").read_text(
        encoding="utf-8"
    )
    evaluations = (
        ROOT / "agents" / "project" / "evidence" / "evaluations" / "README.md"
    ).read_text(encoding="utf-8")
    combined = "\n".join([protocol, evaluations])

    for token in [
        "skeptic",
        "advocate",
        "stabilizer",
        "explorer",
        "release-steward",
        "evaluator",
        "decision",
        "score",
        "reason",
        "proposal_precision",
        "proposal_recall",
        "false_positive_proposal_rate",
        "block verdict",
    ]:
        assert token in combined


def test_task_ar_303_and_304_cmode_and_skill_layer_are_discoverable():
    roadmap = (ROOT / "agents" / "project" / "C-MODE-LATENT-ROADMAP.md").read_text(encoding="utf-8")
    guardrails = (ROOT / "agents" / "project" / "PLANNING-GUARDRAILS.yml").read_text(
        encoding="utf-8"
    )
    rsi_skill = (ROOT / "skills" / "rsi-planning-loop" / "SKILL.md").read_text(encoding="utf-8")
    failure_skill = (ROOT / "skills" / "failure-to-regression" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    closeout_skill = (ROOT / "skills" / "session-closeout" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    combined = "\n".join([roadmap, guardrails, rsi_skill, failure_skill, closeout_skill])

    for token in [
        "latent option",
        "repeated B-mode pass evidence",
        "Owner-gated",
        "rollback evidence",
        "skills/rsi-planning-loop",
        "evidence inbox",
        "proposal engine",
        "council review",
        "casebook entry",
        "reproduction command",
        "parallel-session closeout",
    ]:
        assert token in combined


def test_task_ar_305_closeout_verifier_and_review_are_declared():
    verifier = (ROOT / "scripts" / "verify_rsi_operating_system_taskset.py").read_text(
        encoding="utf-8"
    )
    review = (
        ROOT
        / "reviews"
        / "REVIEW-2026-06-11-agent-runtime-rsi-operating-system-closeout.md"
    ).read_text(encoding="utf-8")
    combined = "\n".join([verifier, review])

    for token in [
        "TASKSET-AR-RSI-OPERATING-SYSTEM",
        "taskset_work_gate.py",
        "owner_doc_format_gate.py",
        "task_identity.py",
        "a2a_lifecycle_gate.py",
        "remaining watch",
        "C-mode remains latent",
    ]:
        assert token in combined
