# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-15

## Bottom Line

지난 번의 비판적 리뷰에서 지적한 핵심 리스크(템플릿 완결성, 템플릿 실행 검증, ToolRunner 임의 실행 경로, 병렬 claim 경합, provider 의존성) 중에서
**템플릿 완결성/런타임 검증/의존성/부분 보안 경계**는 안정적으로 정리됐고,
**병렬 claim + 자동 치유 루프의 신뢰도**만 실전 수준까지 추가 강화가 남았다.

즉, "좋은 아키텍처" 상태에서 "현장에서 깨지지 않는 운영 체인" 상태로 한 단계 더 근접했다.

## Signal

- 기준 문서:
  - `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md`
  - `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-14.md`
- 실행한 증거:
  - `PYTHONPATH=src python -m pytest tests/test_doctor.py tests/test_template_agent_tools.py tests/test_template_message_queue.py tests/test_template_smoke.py -q`
    - `27 passed`
  - `PYTHONPATH=src python -m pytest tests -q`
    - `124 passed`
- 구현 범위:
  - `src/agent_runtime/doctor.py` `--repair` 실행 경로 안정화
  - `src/agent_runtime/cli.py` doctor 서브커맨드에 `--repair` 전달
  - `tests/test_doctor.py`에 repair 동작 검증 추가 (디렉터리 복구 / stale claim 제거 / no-op)

## Insight (전회 대비 재평가)

| 항목 | 이전 상태(Pass-14) | 현재(Pass-15) | 상태 |
|---|---|---|---|
| `orchestrator_safety_gate.py`, `pipeline.py`, `schemas/task.schema.json` 누락 | 없음(이미 해결됨) | 없음(유지) | ✅ |
| 템플릿 런타임 `sync --apply` 후 실행성 | 검증 체계는 존재 | 테스트/CI 경로에서 스모크 + 워커 1개 메시지 처리 검증 통과 | ✅ |
| ToolRunner 기본 위험 `python -c`, `git commit/checkout/restore/stash`, `pip install` | 차단되었으나 우회패턴 검증이 보강 필요 | `ci`/`owner`/`research` profile 기반으로 대부분 차단, 테스트로 보강 | ⚠️ 고도화 여지 있음 |
| 메시지 병렬 claim 안전성 | lease 기반 + stale recovery 구현 | 동일 프레임 유지, 다중 race 테스트는 통과 | ✅(로컬) / ⚠️(분산 FS 및 운영 대규모 동시성 미검증) |
| provider import/extra 분리 | 완화 필요 | 현재 경로에서 dummy 경로 중심 실행 안정화, 의존성 경고 정책 정착 | ✅ |
| `doctor` 실행성 | 보고/점검만 존재 | `doctor --repair`가 실제 수정(디렉터리 생성, stale claim 제거) 동작 | ✅ |
| `doctor` 리뷰 기록성 | 누락된 비판 리뷰를 별도 아카이브에 남김 필요 | 비판적 리뷰 기반 재비교 리뷰 문서 작성 완료 | ✅ |

## Remaining Risk

1. **분산 claim 신뢰성 완성도**
   - 현재 claim lease/recover는 단일/공유 로컬 파일시스템에서 검증됨.
   - NFS/원격 FS, 동시성 폭주, 프로세스 crash 타이밍 조합에 대한 실증 테스트는 추가 필요.

2. **ToolRunner 우회 패턴 확장**
   - 쉘 토큰/인코딩 우회 조합(`python` 하위 표현식, 경로 인젝션 변형 등)에 대한 보안 테스트를 더 늘려야 함.

3. **운영 자동 복구 범위 확장**
   - `doctor --repair`는 안전 동작(디렉터리/claim 처리)으로는 충분하지만, 권장 템플릿 정합성·동기화 충돌 복구까지 자동화는 추가 설계가 필요.

## Decision

- 이번 pass에서는 "비판 리뷰 기반 gap을 실행 이력으로 고정"하는 목표를 완료했다.
- `PASS-15` 재비교 기준 문서는 다음 항목을 남긴다:
  - 초기 비판 내용 보존(기준점),
  - 변경사항의 실행증거,
  - 미해결 위험의 우선순위.
- 다음 액션은 위 `Remaining Risk` 1, 2부터 고치고, 3단계에서는 `doctor --repair` 범위를 `runtime.health` 상태 복구까지 점진 확장하면 된다.
