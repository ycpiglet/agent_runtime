---
title: TASK-AR-610 Scope Amendment
date: 2026-07-22
signal: pass
score: 97
tags: [task-ar-610, ci, work-schema, scope-amendment]
---

# TASK-AR-610 scope amendment

## Bottom Line

`failed_evidence_refs`를 제거한 뒤 Owner governance의 다음 차단 계층인
`rbac_write_gate.py`가 동일한 2026-07 closeout 기록군에서 15개의 추가 비표준 필드를
보고했다. 모두 `review_evidence_refs`, `implementation_commit`, `remote_closeout`이며
원격 `main`에 이미 존재한다.

TASK-AR-610을 같은 원인의 legacy closeout metadata normalization으로 확장한다. 이는
스키마를 넓히거나 증거를 삭제하는 변경이 아니다.

## Added Targets

- `agents/lead_engineer/tasks/TASK-AR-595.md`
- `agents/lead_engineer/tasks/TASK-AR-596.md`
- `agents/lead_engineer/tasks/TASK-AR-597.md`
- `agents/lead_engineer/tasks/TASK-AR-598.md`
- `agents/lead_engineer/tasks/TASK-AR-601.md`
- `agents/lead_engineer/tasks/units/TASK-AR-596/UNIT-TASK-AR-596-001.md`
- `agents/lead_engineer/tasks/units/TASK-AR-597/UNIT-TASK-AR-597-001.md`
- `agents/lead_engineer/tasks/units/TASK-AR-598/UNIT-TASK-AR-598-001.md`

기존 target `TASK-AR-594.md`는 유지한다.

## Preservation Rule

- `review_evidence_refs` 값은 canonical `evidence_refs`에 합친다.
- `implementation_commit`과 `remote_closeout` 값은 각 기록의 Markdown closeout
  구역으로 이동한다.
- referenced review/verification files는 삭제하거나 수정하지 않는다.

## Verification

- `python scripts/taskset_work_gate.py --check`
- `python scripts/rbac_write_gate.py --check`
- `python scripts/owner_governance_gate.py --allow-empty-owner-docs`

