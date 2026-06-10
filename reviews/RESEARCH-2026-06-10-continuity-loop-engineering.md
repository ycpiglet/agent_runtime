# RESEARCH-2026-06-10: Continuity And Loop Engineering

## Bottom Line

- The proposed runtime direction is consistent with established improvement,
  evaluation, reliability, and AI risk-management practice.
- The important distinction is enforcement: rules should become live pointers,
  evals, gates, APIs, or tasks, not remain only in long prose documents.

## Sources

| Source | Relevant Signal |
|---|---|
| W. Edwards Deming Institute, PDSA Cycle | PDSA defines a learning loop: plan, do, study measured outcomes, act on learning, then repeat. |
| OpenAI Evals | Evals provide benchmark and custom evaluation infrastructure for LLM systems; without evals, model-version impact is hard to understand. |
| Google SRE Book, Service Level Objectives | SLO practice starts with behaviors that matter, quantitative indicators, targets, and action based on measured gaps. |
| NIST AI Risk Management Framework | AI risk management should be incorporated into design, development, use, and evaluation of AI systems. |

## Fit To Agent Runtime

The Owner's requested loop maps cleanly:

| Owner Concept | Established Analogue | Runtime Implementation |
|---|---|---|
| 평가 -> 제안 -> 검증 -> 병합 | PDSA / scientific method | measured improvement loop in `AGENTS.md` and `CLAUDE.md` |
| 측정 가능한 평가 | SLI/SLO and eval practice | golden set, score, failure notes, verification commands |
| 한 번에 하나씩 수정 | controlled experiment discipline | one variable per verified change |
| golden set / 오답 노트 | regression tests and benchmark sets | fixed cases, failures, edge cases |
| 문제 출제자와 채점자 분리 | independent review / grader separation | proposer and grader role split when stakes justify |
| Owner가 기준과 병합 결정 | SLO/business target ownership | Owner owns success criteria and final merge |
| 반복 요청은 API화 | operationalizing recurring work | function/API, script, hook, gate, checklist, template, or task |

## Conclusion

The structural fix is not to make AGENTS or skills longer. Long documents help
only after an agent knows where to look. The stronger pattern is:

1. short live work pointer for active agents, teams, panes, phases, and progress;
2. concise protocol rule;
3. executable gate or test;
4. Compound record when recurrence happens;
5. Owner-owned criteria for what counts as improvement.

## Source URLs

- https://deming.org/explore/pdsa/
- https://github.com/openai/evals
- https://sre.google/sre-book/service-level-objectives/
- https://www.nist.gov/itl/ai-risk-management-framework
