#!/usr/bin/env python3
"""eval_harness — agentic 측정 substrate (TASK-238, 15패턴 ①).

라우팅(239)·협업(240)·생성트리오(242)가 **baseline 대비 개선을 증명하는 분모**.
architect subagent(collab-2026-06-05.jsonl): 측정은 peer 아닌 선행 의존 — 없으면 피드백
루프가 merge 시 unfalsifiable(soft 로그 재발).

구성:
  - record_outcome  : per-task outcome/usage 로그(eval_log.jsonl, gitignore = 런타임 데이터).
  - judge_outcome   : **객관 신호**(finish_reason·outcome)로 분류 — LLM-judge 아님(순환 회피).
  - report          : grade/model 별 usage·escalation 집계 + 검증된 token/billed-cost delta.
  - golden set      : 판정 회귀 가드(committed fixture, agents/lead_engineer/eval/golden.jsonl).

"맞는 모델" = escalation 신호 없이 끝낸 가장 싼 tier(별도 judge 모델 불요).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL_LOG = ROOT / "eval_log.jsonl"                       # gitignore (런타임)
GOLDEN = ROOT / "agents" / "lead_engineer" / "eval" / "golden.jsonl"  # committed fixture

# 객관 escalation 신호(model 이 약했거나 task 가 컸다 — under-route).
# 'length' 는 ambiguous(성공한 긴 출력일 수 있음) → outcome 도 나쁠 때만 escalate(reviewer #1).
ESCALATION_FINISH = {"error", "cap", "cap-hit", "max_tokens"}
ESCALATION_OUTCOME = {"rejected", "needs-changes", "gate-error", "recurrence", "reopen"}
NEUTRAL_OUTCOME = {"ok", "completed", ""}
MODEL_TIER = {"haiku": 1, "sonnet": 2, "opus": 3}       # 싼→비싼 (TASK-239 over-route 판정용)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


# ---------- logger ----------

def record_outcome(task_id: str, grade: str, model: str, tokens: int,
                   finish_reason: str = "stop", outcome: str | None = None,
                   path: Path = EVAL_LOG, policy_model: str | None = None,
                   selected_model: str | None = None,
                   routing_signals: list[str] | None = None,
                   baseline_tokens: int | None = None,
                   actual_tokens_known: bool | None = None,
                   baseline_verdict: str | None = None,
                   collab_verdict: str | None = None,
                   collab_members: list[str] | None = None,
                   provider: str | None = None,
                   requested_tier: str | None = None,
                   resolved_model: str | None = None,
                   observed_model: str | None = None,
                   model_changed: bool | None = None,
                   route_status: str | None = None,
                   application_status: str | None = None,
                   baseline_model: str | None = None,
                   billed_cost: float | None = None,
                   currency: str | None = None,
                   baseline_billed_cost: float | None = None,
                   baseline_currency: str | None = None) -> dict:
    rec = {"ts": datetime.now().astimezone().isoformat(timespec="seconds"),  # tz-aware(reviewer #3)
           "task_id": task_id, "grade": grade,
           "model": model, "tokens": int(tokens), "finish_reason": finish_reason,
           "outcome": "ok" if outcome is None else outcome}  # None 만 ok(빈 문자열 보존, reviewer #2)
    if policy_model is not None:
        rec["policy_model"] = policy_model
    if selected_model is not None:
        rec["selected_model"] = selected_model
    if routing_signals is not None:
        rec["routing_signals"] = list(routing_signals)
    if baseline_tokens is not None:
        rec["baseline_tokens"] = int(baseline_tokens)
    if actual_tokens_known is not None:
        rec["actual_tokens_known"] = bool(actual_tokens_known)
    if baseline_verdict is not None:
        rec["baseline_verdict"] = baseline_verdict
    if collab_verdict is not None:
        rec["collab_verdict"] = collab_verdict
    if collab_members is not None:
        rec["collab_members"] = list(collab_members)
    optional = {
        "provider": provider,
        "requested_tier": requested_tier,
        "resolved_model": resolved_model,
        "observed_model": observed_model,
        "model_changed": model_changed,
        "route_status": route_status,
        "application_status": application_status,
        "baseline_model": baseline_model,
    }
    for key, value in optional.items():
        if value is not None:
            rec[key] = value
    actual_currency = str(currency or "").strip().upper() or None
    baseline_cost_currency = str(baseline_currency or "").strip().upper() or None
    if billed_cost is not None:
        if actual_currency is None:
            raise ValueError("currency is required when billed_cost is supplied")
        actual_cost = float(billed_cost)
        if not math.isfinite(actual_cost) or actual_cost < 0:
            raise ValueError("billed_cost must be non-negative")
        rec["billed_cost"] = actual_cost
        rec["currency"] = actual_currency
    if baseline_billed_cost is not None:
        if baseline_cost_currency is None:
            raise ValueError(
                "baseline_currency is required when baseline_billed_cost is supplied"
            )
        baseline_cost = float(baseline_billed_cost)
        if not math.isfinite(baseline_cost) or baseline_cost < 0:
            raise ValueError("baseline_billed_cost must be non-negative")
        rec["baseline_billed_cost"] = baseline_cost
        rec["baseline_currency"] = baseline_cost_currency
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def read_outcomes(path: Path = EVAL_LOG) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out


# ---------- objective judge ----------

def judge_outcome(rec: dict) -> str:
    """객관 신호로 under-route 판정: ok | escalate. LLM-judge 아님(순환 회피).

    escalate = 명확한 실패(error/cap/max_tokens) 또는 나쁜 outcome(rejected/needs-changes/
    gate-error/recurrence/reopen). 'length' 는 outcome 도 나쁠 때만(성공한 긴 출력 false-positive
    방지, reviewer #1). over-route(불필요하게 비쌈)는 report 의 opus_by_grade 가 본다.
    """
    finish = str(rec.get("finish_reason", "")).lower()
    outcome = str(rec.get("outcome", "")).lower()
    if finish in ESCALATION_FINISH:
        return "escalate"
    if finish == "length" and outcome not in NEUTRAL_OUTCOME:
        return "escalate"
    if outcome in ESCALATION_OUTCOME:
        return "escalate"
    return "ok"


# ---------- report (scoreboard) ----------

def _routing_evidence_exclusion_reason(rec: dict) -> str | None:
    if not str(rec.get("observed_model") or "").strip():
        return "observed_model_unavailable"
    if not str(rec.get("baseline_model") or "").strip():
        return "baseline_model_unavailable"
    if rec.get("application_status") != "applied":
        return "route_not_applied"
    if rec.get("model_changed") is not True:
        if rec.get("route_status") == "ineffective_equivalent":
            return "route_ineffective_equivalent"
        return "model_change_unverified"
    if rec.get("route_status") != "effective":
        return "route_not_effective"
    return None


def _token_delta_exclusion_reason(rec: dict) -> str | None:
    routing_reason = _routing_evidence_exclusion_reason(rec)
    if routing_reason:
        return routing_reason
    if rec.get("actual_tokens_known") is not True:
        return "actual_token_usage_unavailable"
    if int(rec.get("tokens", 0) or 0) <= 0:
        return "actual_token_usage_not_positive"
    if int(rec.get("baseline_tokens", 0) or 0) <= 0:
        return "baseline_token_usage_unavailable"
    return None


def _monetary_delta_exclusion_reason(rec: dict) -> str | None:
    routing_reason = _routing_evidence_exclusion_reason(rec)
    if routing_reason:
        return routing_reason
    if rec.get("billed_cost") is None or not str(rec.get("currency") or "").strip():
        return "actual_billed_cost_unavailable"
    if (
        rec.get("baseline_billed_cost") is None
        or not str(rec.get("baseline_currency") or "").strip()
    ):
        return "baseline_billed_cost_unavailable"
    if str(rec["currency"]).upper() != str(rec["baseline_currency"]).upper():
        return "currency_mismatch"
    return None


def _exclusion_counts(records: list[dict], reason_fn) -> dict[str, int]:
    counts: dict[str, int] = {}
    for rec in records:
        reason = reason_fn(rec)
        if reason:
            counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items()))


def report(records: list[dict] | None = None) -> dict:
    records = read_outcomes() if records is None else records
    by_grade: dict[str, dict] = {}
    by_model: dict[str, dict] = {}
    for r in records:
        verdict = judge_outcome(r)
        g = by_grade.setdefault(r.get("grade", "?"), {"count": 0, "tokens": 0, "escalations": 0})
        g["count"] += 1
        g["tokens"] += int(r.get("tokens", 0))
        g["escalations"] += 1 if verdict == "escalate" else 0
        m = by_model.setdefault(r.get("model", "?"), {"count": 0, "tokens": 0, "escalations": 0})
        m["count"] += 1
        m["tokens"] += int(r.get("tokens", 0))
        m["escalations"] += 1 if verdict == "escalate" else 0
    for d in (*by_grade.values(), *by_model.values()):
        d["escalation_rate"] = round(d["escalations"] / d["count"], 3) if d["count"] else 0.0
    # 등급별 opus 비율 — over-route baseline(reviewer #2): TASK-239 가 줄여야 할 숫자.
    # (전체 opus_share 는 "라우팅 전이라 다 opus"와 "정당하게 opus"를 구분 못 함.)
    opus_by_grade: dict[str, dict] = {}
    for r in records:
        g = opus_by_grade.setdefault(r.get("grade", "?"), {"opus": 0, "total": 0})
        g["total"] += 1
        g["opus"] += 1 if "opus" in str(r.get("model", "")).lower() else 0
    for g in opus_by_grade.values():
        g["opus_share"] = round(g["opus"] / g["total"], 3) if g["total"] else 0.0
    total = len(records)
    opus = sum(1 for r in records if "opus" in str(r.get("model", "")).lower())
    delta_records = [r for r in records if _token_delta_exclusion_reason(r) is None]
    actual_tokens = sum(int(r.get("tokens", 0) or 0) for r in delta_records)
    baseline_tokens = sum(int(r.get("baseline_tokens", 0) or 0) for r in delta_records)
    saved_tokens = baseline_tokens - actual_tokens
    token_delta = {
        "evidence_type": "token_usage",
        "monetary_claim": False,
        "eligible_records": len(delta_records),
        "excluded_records": len(records) - len(delta_records),
        "exclusion_reasons": _exclusion_counts(records, _token_delta_exclusion_reason),
        "actual_tokens": actual_tokens,
        "baseline_tokens": baseline_tokens,
        "saved_tokens": saved_tokens,
        "saved_rate": round(saved_tokens / baseline_tokens, 3) if baseline_tokens else 0.0,
    }
    # Compatibility only: callers should migrate to token_delta.  The payload
    # explicitly says that token evidence is not a monetary cost claim.
    cost_delta = {
        **token_delta,
        "deprecated_alias": True,
        "label": "token delta (not monetary cost)",
    }
    monetary_records = [
        r for r in records if _monetary_delta_exclusion_reason(r) is None
    ]
    monetary_by_currency: dict[str, dict] = {}
    for rec in monetary_records:
        currency = str(rec["currency"]).upper()
        bucket = monetary_by_currency.setdefault(
            currency,
            {
                "records": 0,
                "actual_billed_cost": 0.0,
                "baseline_billed_cost": 0.0,
            },
        )
        bucket["records"] += 1
        bucket["actual_billed_cost"] += float(rec["billed_cost"])
        bucket["baseline_billed_cost"] += float(rec["baseline_billed_cost"])
    for bucket in monetary_by_currency.values():
        bucket["saved_billed_cost"] = round(
            bucket["baseline_billed_cost"] - bucket["actual_billed_cost"],
            9,
        )
        baseline_cost = bucket["baseline_billed_cost"]
        bucket["saved_rate"] = (
            round(bucket["saved_billed_cost"] / baseline_cost, 3)
            if baseline_cost
            else 0.0
        )
        bucket["actual_billed_cost"] = round(bucket["actual_billed_cost"], 9)
        bucket["baseline_billed_cost"] = round(
            bucket["baseline_billed_cost"], 9
        )
    monetary_delta = {
        "evidence_type": "provider_billed_cost",
        "verified": bool(monetary_records),
        "eligible_records": len(monetary_records),
        "excluded_records": len(records) - len(monetary_records),
        "exclusion_reasons": _exclusion_counts(
            records, _monetary_delta_exclusion_reason
        ),
        "by_currency": dict(sorted(monetary_by_currency.items())),
    }
    collab_records = [
        r for r in records
        if r.get("baseline_verdict") is not None
        and r.get("collab_verdict") is not None
        and r.get("collab_members")
        and int(r.get("baseline_tokens", 0) or 0) > 0
    ]
    collaboration_tokens = sum(int(r.get("tokens", 0) or 0) for r in collab_records)
    collaboration_baseline_tokens = sum(int(r.get("baseline_tokens", 0) or 0) for r in collab_records)
    verdict_changes = sum(
        1 for r in collab_records
        if str(r.get("baseline_verdict")) != str(r.get("collab_verdict"))
    )
    collaboration_delta = {
        "total": len(collab_records),
        "verdict_changes": verdict_changes,
        "verdict_change_rate": round(verdict_changes / len(collab_records), 3) if collab_records else 0.0,
        "baseline_tokens": collaboration_baseline_tokens,
        "collaboration_tokens": collaboration_tokens,
        "token_multiplier": (
            round(collaboration_tokens / collaboration_baseline_tokens, 3)
            if collaboration_baseline_tokens else 0.0
        ),
    }
    return {"total": total, "opus_share": round(opus / total, 3) if total else 0.0,
            "by_grade": by_grade, "by_model": by_model, "opus_by_grade": opus_by_grade,
            "token_delta": token_delta, "cost_delta": cost_delta,
            "monetary_delta": monetary_delta,
            "collaboration_delta": collaboration_delta}


def load_golden(path: Path = GOLDEN) -> list[dict]:
    return read_outcomes(path)


# ---------- escalation report (자가개선 제안 — 배치, 사람 ratify) ----------

def escalation_proposals(records: list[dict] | None = None, threshold: float = 0.3) -> list[str]:
    """grade 별 escalation율이 threshold 초과면 라우팅표 상향 제안(자동 적용 X — 사람 ratify)."""
    rep = report(records)
    props = []
    for grade, d in rep["by_grade"].items():
        if d["count"] >= 3 and d["escalation_rate"] > threshold:
            props.append(f"{grade}: escalation {d['escalations']}/{d['count']} "
                         f"({d['escalation_rate']}) > {threshold} → 상위 tier 라우팅 제안(사람 ratify)")
    for model, d in rep["by_model"].items():
        if d["count"] >= 3 and d["escalation_rate"] > threshold:
            props.append(f"{model}: escalation {d['escalations']}/{d['count']} "
                         f"({d['escalation_rate']}) > {threshold} → 모델 tier 재검토 제안(사람 ratify)")
    return props


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="agentic 측정 substrate (TASK-238)")
    ap.add_argument("--record", action="store_true", help="outcome/cost 로그 1건 기록")
    ap.add_argument("--report", action="store_true", help="스코어보드 출력")
    ap.add_argument("--proposals", action="store_true", help="라우팅 상향 제안(사람 ratify)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--log", type=Path, default=EVAL_LOG, help="eval 로그 경로(default: eval_log.jsonl)")
    ap.add_argument("--task-id")
    ap.add_argument("--grade")
    ap.add_argument("--model")
    ap.add_argument("--tokens", type=int)
    ap.add_argument("--finish-reason", default="stop")
    ap.add_argument("--outcome", default="ok")
    ap.add_argument("--policy-model")
    ap.add_argument("--selected-model")
    ap.add_argument("--routing-signal", action="append", default=[])
    ap.add_argument("--baseline-tokens", type=int)
    ap.add_argument("--actual-tokens-unknown", action="store_true",
                    help="mark tokens unknown so token_delta excludes this record")
    ap.add_argument("--provider")
    ap.add_argument("--requested-tier")
    ap.add_argument("--resolved-model")
    ap.add_argument("--observed-model")
    ap.add_argument("--model-changed", action="store_true")
    ap.add_argument("--route-status")
    ap.add_argument("--application-status")
    ap.add_argument("--baseline-model")
    ap.add_argument("--billed-cost", type=float)
    ap.add_argument("--currency")
    ap.add_argument("--baseline-billed-cost", type=float)
    ap.add_argument("--baseline-currency")
    ap.add_argument("--baseline-verdict")
    ap.add_argument("--collab-verdict")
    ap.add_argument("--collab-member", action="append", default=[])
    args = ap.parse_args(argv)
    if args.record:
        missing = [name for name in ("task_id", "grade", "model", "tokens") if getattr(args, name) in (None, "")]
        if missing:
            ap.error("--record requires " + ", ".join("--" + m.replace("_", "-") for m in missing))
        rec = record_outcome(
            args.task_id,
            args.grade,
            args.model,
            args.tokens,
            finish_reason=args.finish_reason,
            outcome=args.outcome,
            path=args.log,
            policy_model=args.policy_model,
            selected_model=args.selected_model,
            routing_signals=args.routing_signal or None,
            baseline_tokens=args.baseline_tokens,
            actual_tokens_known=False if args.actual_tokens_unknown else None,
            baseline_verdict=args.baseline_verdict,
            collab_verdict=args.collab_verdict,
            collab_members=args.collab_member or None,
            provider=args.provider,
            requested_tier=args.requested_tier,
            resolved_model=args.resolved_model,
            observed_model=args.observed_model,
            model_changed=True if args.model_changed else None,
            route_status=args.route_status,
            application_status=args.application_status,
            baseline_model=args.baseline_model,
            billed_cost=args.billed_cost,
            currency=args.currency,
            baseline_billed_cost=args.baseline_billed_cost,
            baseline_currency=args.baseline_currency,
        )
        print(json.dumps(rec, ensure_ascii=False, indent=2) if args.json else
              f"[eval] recorded {rec['task_id']} {rec['grade']} {rec['model']} {rec['tokens']} tokens")
        return 0
    if args.proposals:
        props = escalation_proposals()
        print(json.dumps(props, ensure_ascii=False, indent=2) if args.json else
              ("\n".join("  " + p for p in props) or "  (제안 없음)"))
        return 0
    rep = report()
    print(json.dumps(rep, ensure_ascii=False, indent=2) if args.json else
          f"[eval] total={rep['total']} opus_share={rep['opus_share']} "
          f"grades={ {g: d['escalation_rate'] for g, d in rep['by_grade'].items()} }")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
