# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-95.md

## Bottom Line

`PASS-95`에서는 strict-ref 정책 아티팩트 판단의 `write/validate` 로직을
`scripts/warning_summary_strict_ref_policy.py`로 분리해, CI와 수동 재현에서 동일한 비교 경로를 사용하도록 정리했습니다.

## Signal

| 항목 | PASS-94 상태 | PASS-95 상태 | 근거 |
|---|---|---|---|
| 정합성 검사 재사용성 | workflow 인라인 Python으로만 검증 | `scripts/warning_summary_strict_ref_policy.py`로 분리되어 write/validate 공통화 | `.github/workflows/test.yml`, `scripts/warning_summary_strict_ref_policy.py` |
| 재현 도구 접근성 | 수동 점검은 임시 JSON 출력/파싱 스니펫 | PASS-95 보조 스크립트로 `--mode validate`/`--mode write` 표준화 | `README.md`, `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md` |
| 문서화 추적성 | PASS-93/94 기록이 분산 | PASS-95 항목에서 워크플로우-재현 표준 절차 통합 | `TEST-STRATEGY.md` |

## Insight

- inline 파싱 로직은 중복·드리프트 위험이 있어 향후 정책 변경 시 오탐/누락 가능성이 있었다.
- 동일 스크립트를 워크플로우와 수동 재현에 함께 쓰면, `require_send_targets` 판단/직렬화 차이 버그를 빠르게 탐지할 수 있다.
- 정규화 비교(_normalize_lines_)를 공통화해 다중 라인 strict-ref 판단을 일관되게 처리한다.

## Decision

- 신규 파일: `scripts/warning_summary_strict_ref_policy.py`
  - `--mode write`: artifact JSON 생성
  - `--mode validate`: `artifact` vs 기대값 정합성 검사
  - `strict_refs` 정규화 및 mismatch 리포팅 제공
- `.github/workflows/test.yml`
  - strict-ref artifact 생성/검증 스텝을 위 스크립트 호출로 변경
- `README.md`
  - PASS-95 재현 보조 스크립트 사용 예시 추가
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - `PASS-95 연계(재현 도구 표준화)` 항목 추가

## Evidence

- `scripts/warning_summary_strict_ref_policy.py`
- `.github/workflows/test.yml`
- `README.md`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- 로컬 실행 없이도 문서상으로 workflow에서 write/validate를 동일 스크립트로 호출하도록 정합화됨.
- 실제 PASS-95 최종 검증은 깃헙 workflow 또는 `python scripts/warning_summary_strict_ref_policy.py --mode validate ...`로 이어서 실행 필요.
