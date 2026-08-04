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


def test_task_ar_299_casebook_contracts_are_declared():
    readme = (ROOT / "agents" / "project" / "casebooks" / "README.md").read_text(encoding="utf-8")
    casebook = (
        ROOT / "agents" / "project" / "casebooks" / "failure-and-compound-casebook.md"
    ).read_text(encoding="utf-8")
    combined = "\n".join([readme, casebook])

    for token in [
        "dedupe_key",
        "symptom",
        "trigger",
        "owner_boundary",
        "affected_gate",
        "recurrence_count",
        "linked_regression_fixture",
        "task_proposal",
        "accepted_watch",
        "CASE-TASKSET-COMPLETION-CLAIM-ONLY",
    ]:
        assert token in combined


def test_task_ar_300_evidence_to_proposal_contract_is_declared():
    contract = (ROOT / "agents" / "project" / "EVIDENCE-TO-PROPOSAL-CONTRACT.md").read_text(encoding="utf-8")
    schema = (ROOT / "schemas" / "planning-proposal.schema.json").read_text(encoding="utf-8")
    planning_loop = (ROOT / "scripts" / "planning_loop.py").read_text(encoding="utf-8")
    combined = "\n".join([contract, schema, planning_loop])

    for token in [
        "proposal_output",
        "dedupe_key",
        "affected_owner_boundary",
        "expected_verification_command",
        "risk_tier",
        "blast_radius",
        "rejection_reason",
        "no_action",
        "skill_proposal",
        "canonical mutation",
    ]:
        assert token in combined


def test_task_ar_301_council_and_metrics_are_structured():
    protocol = (ROOT / "agents" / "project" / "DIVERSITY-COUNCIL-PROTOCOL.md").read_text(encoding="utf-8")
    evaluations = (
        ROOT / "agents" / "project" / "evidence" / "evaluations" / "README.md"
    ).read_text(encoding="utf-8")
    planning_loop = (ROOT / "scripts" / "planning_loop.py").read_text(encoding="utf-8")
    combined = "\n".join([protocol, evaluations, planning_loop])

    for token in [
        "skeptic",
        "advocate",
        "stabilizer",
        "explorer",
        "release-steward",
        "evaluator",
        "proposal_precision",
        "proposal_recall",
        "false_positive_proposal_rate",
        "proposal_metrics",
        "unresolved_block_verdicts",
    ]:
        assert token in combined


def test_task_ar_302_a2a_lifecycle_contract_is_declared():
    inbox = (ROOT / "agents" / "project" / "evidence" / "inbox" / "README.md").read_text(encoding="utf-8")
    gate = (ROOT / "scripts" / "a2a_lifecycle_gate.py").read_text(encoding="utf-8")
    fixture = (
        ROOT / "agents" / "project" / "evidence" / "a2a" / "A2A-LIFECYCLE-2026-06-12.json"
    ).read_text(encoding="utf-8")
    combined = "\n".join([inbox, gate, fixture])

    for token in [
        "context_id",
        "task_id",
        "actor_role",
        "access_boundary",
        "retry_idempotency_key",
        "request",
        "review",
        "decision",
        "correction",
        "proposal_routing",
        "reconstruction_result",
    ]:
        assert token in combined


def test_task_ar_303_c_mode_latent_boundary_is_declared():
    roadmap = (ROOT / "agents" / "project" / "C-MODE-LATENT-ROADMAP.md").read_text(encoding="utf-8")
    checklist = (ROOT / "agents" / "project" / "C-MODE-PROMOTION-CHECKLIST.md").read_text(encoding="utf-8")
    guardrails = (ROOT / "agents" / "project" / "PLANNING-GUARDRAILS.yml").read_text(encoding="utf-8")
    combined = "\n".join([roadmap, checklist, guardrails])

    for token in [
        "latent",
        "blocked",
        "three consecutive B-mode",
        "repeated_pass_threshold",
        "kill_switch_required",
        "owner_approval_always_required",
        "rollback_required",
        "gate_weakening",
    ]:
        assert token in combined


def test_task_ar_304_skill_layer_is_packaged():
    rsi_skill = (ROOT / "skills" / "rsi-planning-loop" / "SKILL.md").read_text(encoding="utf-8")
    failure_skill = (ROOT / "skills" / "failure-to-regression" / "SKILL.md").read_text(encoding="utf-8")
    consumer_failure_skill = (
        ROOT
        / "src"
        / "agent_runtime"
        / "templates"
        / "project"
        / "skills"
        / "failure-to-regression"
        / "SKILL.md"
    ).read_text(encoding="utf-8")
    session_skill = (ROOT / "skills" / "session-closeout" / "SKILL.md").read_text(encoding="utf-8")
    operating_system_skills = "\n".join([rsi_skill, session_skill])

    for token in [
        "agents/project/evidence/inbox/README.md",
        "agents/project/EVIDENCE-TO-PROPOSAL-CONTRACT.md",
        "agents/project/DIVERSITY-COUNCIL-PROTOCOL.md",
        "agents/project/C-MODE-LATENT-ROADMAP.md",
    ]:
        assert token in operating_system_skills

    assert failure_skill == consumer_failure_skill
    for token in [
        "python scripts/compound_record.py",
        "python scripts/work.py close",
        "prevention destination",
        "accepted_watch",
        "task proposal",
        "current work",
    ]:
        assert token in consumer_failure_skill

    for root_only_path in [
        "agents/project/casebooks/failure-and-compound-casebook.md",
        "agents/project/evidence/inbox/README.md",
        "agents/project/EVIDENCE-TO-PROPOSAL-CONTRACT.md",
    ]:
        assert root_only_path not in consumer_failure_skill
