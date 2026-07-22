---
title: PR 303 CI Baseline Schema Recovery
date: 2026-07-22
signal: pass
score: 96
tags: [ci, work-schema, task-ar-594, pr-303]
---

# PR 303 CI baseline schema recovery

## Bottom Line

PR #303의 Python 3.10, 3.11, 3.12 작업은 모두 기존
`agents/lead_engineer/tasks/TASK-AR-594.md`의 스키마 외
`failed_evidence_refs` 필드 때문에 동일하게 실패했다. TASK-AR-600 구현과 focused
tests는 원인이 아니며, 원격 `main`에도 이미 같은 필드가 존재한다.

## Evidence

- GitHub Actions run: `29907765665`
- Failing gate: `python scripts/taskset_work_gate.py --check`
- Finding: `work-item:unknown-field:failed_evidence_refs`
- Local reproduction: Owner governance exit `1` with the same finding

## Decision

실패한 검증 기록을 삭제하지 않는다. 별도 비표준 필드만 제거하고 그 경로를 기존
canonical `evidence_refs` 목록에 합쳐, 성공·실패 W4a 이력을 모두 같은 증거 계약으로
보존한다.

이 수정은 TASK-AR-600 범위 밖에서 발견된 CI baseline 결함이므로 별도 initiative,
taskset, task, unit으로 등록한 뒤 claim-first로 처리한다.

## Scope

- Target: `agents/lead_engineer/tasks/TASK-AR-594.md`
- In scope: evidence-reference frontmatter normalization and governance verification
- Out of scope: schema 확장, 과거 evidence 삭제, TASK-AR-594 기능 재구현

