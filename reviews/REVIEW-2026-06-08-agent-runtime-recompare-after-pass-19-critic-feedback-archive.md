# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-19-critic-feedback-archive

## Bottom Line

초기 비판 리뷰(템플릿 완결성·템플릿 실행성 CI·명령 샌드박스·병렬 claim·의존성 계약)는
`PASS-18` 기준으로 다시 정렬해도 방향은 유효하다.
단, 이번 패스는 **새로운 고위험 이슈를 추가로 제거한 것이 아니라**, `PASS-18`에서 드러난
`reply` 중복/권한 경합 리스크를 더 줄인 보완 패치가 핵심이다.

## Signal

| 항목 | Baseline(초기 리뷰) | PASS-18 현재 상태 | 상태 |
|---|---|---|---|
| 템플릿 자체 완결성 | Critical (누락 파일 다수) | ✅ | 해결 |
| 템플릿 실행 산출물 CI 검증 | Critical (package only) | ✅ | 유지 개선 |
| ToolRunner 샌드박스 | High (python/git 우회 가능성) | ⚠️ | 미해결 |
| 메시지 claim 병렬 안전성 | High (non-atomic) | ⚠️→완화 | 부분 개선 |
| 의존성 선언 계약 | Medium | ✅ | 해결 |

실행 근거:

- `tests/test_template_smoke.py`를 통한 sync/smoke 경로: pass
- `PYTHONPATH=src pytest tests -q` 또는 Python310 가상환경 기준 `129 passed`
- `mark_answered`/`has_active_claim`/`_has_reply` 회귀 강화 반영
- `tests/test_template_message_queue.py` 신규 회귀: `test_has_active_claim_reflects_owner`,
  `test_mark_answered_accepts_existing_reply_as_completed`

## Insight

1. 초기 비판 리뷰의 핵심 5개 중
   `템플릿 완결성`, `CI 템플릿 실행 검증`, `의존성 계약`은 실제로 모두 닫힌 상태로 기록됨.

2. 남은 고위험군은 그대로 유효. 특히 `ToolRunner`는 `python -c`, `git commit/checkout/restore/stash`,
   임의 스크립트 실행 루트를 계속 면밀히 추적해야 한다.

3. `PASS-18`은 `claim` 상태의 idempotency를 강화해 **권한 상실/중복 reply 상태**를 많이 줄였지만,
   분산/원격 FS에서의 동시성 증명은 아직 미완성이다.

4. 초기 비판 리뷰에서 제시한 “즉시 조치 4가지” 중에서
   1) 템플릿 실행 self-contained, 2) template smoke CI는 실전적으로 정리 완료,
   3) ToolRunner 하네스와 4) claim 병렬성은 여전히 다음 단계 개선 대상으로 남아 있다.

## Decision

### 이번 패스(이 문서 기준) 변화

- `message_queue.py`: `has_active_claim` 강화, `mark_answered` idempotent 완료 경로 보강
- `agent_worker.py`, `auto_dispatch.py`: reply 이전/이후 소유권 재검증, 기존 reply 존재시 중복 쓰기 차단
- `test_template_message_queue.py`: owner/worker identity + 기존 reply idempotency 회귀 테스트 추가

### 다음 1~2주 액션(재평가 기준)

1. `ToolRunner`를 `cmdlet`/PowerShell/셸 escape 우회까지 포함해 음영 없는 통합 거부 정책으로 마무리
2. 분산 파일시스템 시나리오(동일 메시지 동시 claim + stale lease 회수) 통합 테스트 추가
3. 기존 초기 비판 리뷰의 “임계 5개”를 PASS-19에서 한 번 더 **정량 재평가**

## 원본 비판 리뷰(요약 보관)

아래 항목은 `user_action: review`로 들어온 초기 비판 리뷰의 핵심입니다. 추후 PASS 재평가 시 “변경됨 / 미비함 / 미해결” 판단의 기준으로 사용합니다.

### Baseline 결론

`agent_runtime`는 배포/거버넌스 코어는 안정적이지만,
실전 멀티에이전트 런타임으로 보기에는
템플릿 자체 실행성, 병렬 claim, 보안 샌드박스가 약점이었다.

### 핵심 Finding(심각도 순)

1. **템플릿 self-contained 이슈 (Critical)**
   - 누락 파일: `orchestrator_safety_gate.py`, `pipeline.py`, `schemas/task.schema.json`, 일부 참조 문서
   - 위험: sync 후 바로 실행 경로가 깨짐

2. **CI가 템플릿 산출물을 검증 못함 (Critical)**
   - 현재 패키지 테스트 중심으로는 배포 템플릿 실패를 놓침

3. **ToolRunner sandbox 미성숙 (High)**
   - `python -c`, mutable git 명령 등 우회 가능

4. **병렬 claim 취약 (High)**
   - 동시 worker에서 duplicate claim/reply 가능성

5. **의존성 계약 부재 (Medium)**
   - base 패키지와 optional provider 의존성 경계가 실제 실행과 어긋남

### 초기 추천 우선순위(요약)

1. 템플릿 self-contained 마감(필수 파일/스키마 정합성)
2. 템플릿 smoke CI 추가( sync -> help -> 1개 메시지 처리 )
3. provider 의존성 분리
4. ToolRunner command allowlist 강화

### 비교 점수(초기 → 현재 축적)

- Public release hygiene: B+
- sync/update safety: B+
- template execution completeness: D+ (현재는 보완된 상태로 상향)
- parallelism: C-
- security: D+ / D (개선 전)
- governance design: B
- self-improvement loop: C-
- OSS 경쟁력: C

이 항목들은 이후 PASS-19 재검토 기준과 동일하게 계속 점검합니다.

### 참조

- `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md`
- `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-18.md`
