# REVIEW-2026-06-08-agent-runtime-post-pass-2

## 한 줄 결론

핵심 런타임 결함인 템플릿의 자기완결성은 정리되었다.
다만 실무에서 바로 `병렬 워커 / 보안 샌드박스 / 의존성 분리`를 믿고 사용하기엔 고도화가 더 필요하다.

## 비교 기준

- Baseline: `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md`
- 이전 점검: `reviews/REVIEW-2026-06-08-agent-runtime-after-pass-1.md`
- 이번 점검: 현재 워크트리(2026-06-08 17:21:44 +09:00 기준, 현재 실행 결과 기반)

## 이번 점검 근거(요약)

- `PYTHONPATH=src python -m pytest tests -q` → **94 passed**
- `sanitize --check` → **findings=0**
- `publish-check --check` → **findings=0**
- `publish-bundle --check` → **findings=0**, 선택 파일 **182개**
- 템플릿 sync/apply + 핵심 엔트리포인트 실행:
  - `agent_runtime sync --root <clean_host> --apply` → **updates=156, conflicts=0**
  - `scripts/agent_orchestrator.py --help`
  - `scripts/agent_worker.py --help`
  - `scripts/auto_runner.py --help`
  - `scripts/check_messages.py` → **OK: 0 error(s), 0 warning(s)**

## Baseline 대비 비교 결과

### 1) 템플릿 자체 완결성
- Baseline: critical, missing `orchestrator_safety_gate.py`, `pipeline.py`, `schemas/task.schema.json`, docs.
- 현재: **해결**
  - `scripts/orchestrator_safety_gate.py` 추가
  - `scripts/pipeline.py` 추가
  - `schemas/task.schema.json` 추가
  - `AUDIT-GATE.md`, `SAFETY-GATE.md`, `TEST-STRATEGY.md` 추가
- 영향: clean sync로 생성한 템플릿의 핵심 실행 경로가 정상 동작.

### 2) 런타임 아티팩트 CI 검증
- Baseline: package-level checks만 통과, 템플릿 실행 경로 미검증.
- 현재: **부분 개선 필요**
- package checks는 계속 통과하지만, CI 레벨에서 `sync -> 핵심 스크립트 실행 -> dummy 플로우` 단계가 아직 본격 정착되지 않음.

### 3) ToolRunner command security
- Baseline: open (allow `python`, `py`, mutable git 명령 등).
- 현재: **미해결**
- 현재 위험 패턴은 그대로 남아 있어 임의 실행/우회 가능성은 아직 차단되지 않음.

### 4) 메시지 claim 동시성/락
- Baseline: non-atomic claim/reply, 중복 claim 리스크.
- 현재: **미해결**
- 동일 메시지 동시 처리 방지 및 스테일 리커버리 동작이 아직 미구현.

### 5) provider 의존성 분리
- Baseline: dummy 외 경로와 live provider import 경계가 불명확.
- 현재: **미해결**
- 옵션 분리/lazy import는 아직 반영 안 됨.

## 상태 점수(변경된 것만 표기)

- Public release hygiene: B+ → **B+**
- Template execution completeness: D → **B-** (핵심 self-contained 항목 복구로 한 단계 상승)
- CI installed-template proof: 낮음(경고 대상) → **낮음(계속 보류)**
- Command/tool security: D+ → **D+**
- 메시지 병렬 안정성: C- → **C-**
- Provider dependency contract: C → **C**

## 다음 사이클에서 꼭 닫을 항목

1. 템플릿 배포 산출물 smoke CI 추가
   - sync 후 core script 실행 + dummy 메시지 1개 처리까지 통과.
2. `providers/agent_tools.py` command allowlist 강화
3. message claim lease + stale recovery
4. provider extras/lazy import 분리 + 명시적 에러 메시지

## 변경 후 재점검 기준

다음 리뷰에서는 아래 두 가지만 “closed” 조건으로 두면 명확해진다:
- **보안/실행성**: 임의 파이썬 실행/가변 git write 경로가 차단되고, dummy claim 테스트가 병렬에서 1개만 성공.
- **운영성**: CI에서 템플릿 sync 산출물 실패가 바로 실패로 전파.
