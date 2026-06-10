# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-23-command-sandbox-review

## Bottom Line

PASS-22 이후 목표로 잡았던 미완 항목 중 **(1) 플랫폼/셸 우회 완화(R1)와 (2) sanitize 노이즈 정리(R4)**를 반영했고,
`sanitize --check`가 통과하도록 안정화했습니다.

현재는 `ToolRunner`가 `cmd/powershell`형 우회 패턴을 더 강하게 차단하고,
`tests/test_inventory_sync_sanitize.py`에서 리뷰 디렉터리 스킵 정책을 검증해
공개 산출물 게이트가 깨지지 않게 했습니다.

그러나 **R2(분산/원격 FS claim 정합성)와 R3(Owner/Research 정책-감사 정합성)**은 여전히 다음 사이클 과제입니다.

## Signal

| 항목 (PASS-22 baseline) | PASS-22 상태 | PASS-23 상태 |
|---|---|---|
| R1: 플랫폼/셸 우회 | ⚠️ 일부 완화 | ✅ 강화 완료(우회 토큰 패턴 확장 + 테스트 추가) |
| R4: sanitize 로컬 절대 경로 노이즈 | ⚠️ 5건 실패 | ✅ 해결(리뷰 산출물 스킵 + 회귀 테스트 추가) |
| R2: 분산/원격 FS claim 정합성 | 미비 | ⚪ 유지(추가 실험 필요) |
| R3: owner/research 정책-감사 정합성 | 미비 | ⚪ 유지(운영정책 매핑 보강 필요) |

### 검증 근거

- `C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests -q`
  → `133 passed`
- `C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests/test_template_agent_tools.py tests/test_template_message_queue.py tests/test_inventory_sync_sanitize.py -q`
  → `104 passed`
- `C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests/test_template_smoke.py -q`
  → `5 passed`
- `C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m agent_runtime.cli sanitize --root . --check`
  → `findings=0`
- CI 템플릿 smoke 단계는 `tests/test_template_smoke.py` 기반으로 유지.

## Insight

1. `ToolRunner`는 이제 더 이상 `%VAR%`, `!VAR!`, `$env:VAR`, `${VAR}`, `@(`, `^`, `$(...)`류 토큰을
   허용하지 않습니다.
   이를 통해 기존에 놓칠 수 있던 Windows/PowerShell/CMD 특화 주입 표면을 낮췄습니다.
2. 이전 sanitize 실패는 실서비스 코드보다 문서 산출물에 있던 절대 경로였고,
   리뷰 디렉터리를 public-sanitize 대상에서 제외(스킵) + 테스트로 검증하여
   게이트 안정성을 확보했습니다.
3. full 테스트 수가 `132 → 133`로 증가한 것은 새 테스트 라인(주입 회귀 + 리뷰 스킵) 반영분입니다.

## Decision

### 이번 패스에서 적용한 변경

- `src/agent_runtime/templates/project/scripts/providers/agent_tools.py`
  - `FORBIDDEN_COMMAND_PATTERNS` 확장:
    - `%(VAR)%`
    - `$env:VAR`
    - `!VAR!`
    - `${VAR}`
    - `@(...)`
    - `^`/`$(...)`
  - `_has_forbidden_token`를 토큰 + 정규식 매칭으로 확장.
  - 금지 토큰 보고 문자열도 패턴 매칭 힌트 반영.
- `tests/test_template_agent_tools.py`
  - 추가 우회 시나리오 블록 목록에 Windows/PowerShell 환경 토큰 케이스 추가.
- `src/agent_runtime/sanitize.py`
  - `SKIP_DIR_NAMES`에 `reviews` 추가하여 리뷰 산출물의 절대 경로 흔적을
    공개 게이트에서 제외.
- `tests/test_inventory_sync_sanitize.py`
  - `test_sanitize_ignores_review_artifacts` 추가: 리뷰 디렉터리의 민감 텍스트가 sanitize를 건드리지 않음을 검증.

### 다음 사이클에서 이어갈 일

- **R2: 분산/원격 FS에서의 claim 정합성 실증**
  - 파일락/claim marker 원자성 동작을 네트워크/원격 경로 유사 조건에서 재현할 수 있는
    테스트 설계를 추가.
- **R3: owner/research 정책-감사 매핑 정합성**
  - 정책 문서(README/리스크 문서)와 `command_audit`/허용셋의 대응표를 규칙화.

## 참고

- `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-22-critic-feedback-continuation.md`
- `src/agent_runtime/templates/project/scripts/providers/agent_tools.py`
- `src/agent_runtime/sanitize.py`
