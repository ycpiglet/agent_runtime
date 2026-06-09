# TEST-STRATEGY

## 목적

`qa` 역할의 실행, 배포 전 검증, 후속 회귀를 통일하기 위한 최소 전략입니다.

## 분류

1. **Contract 테스트 (필수)**
   - 입·출력 스키마/파서 일관성 검증
   - TASK/메시지 frontmatter 기본 규약
2. **통합 테스트 (필수)**
   - sync 후 템플릿 스크립트 기본 실행(help/help-like 명령)
   - 더미 처리 경로(`--provider dummy`)의 단일 라운드 완료
3. **보안 회귀 (권장)**
   - 승인되지 않은 명령 실행/경로 탈출 시도
   - 명령 정책 위반 경고 및 차단
4. **병렬성 회귀 (권장)**
   - 동시 claim/dispatch 시 중복 처리 방지

## 게이트

- 경고 0건 + 실패 0건은 기본 통과 조건.
- 보안 정책 우회 시도는 오류로 간주.
- template bootstrap 관련 회귀는 패키지 테스트와 분리하여 별도로 추적.

## PASS-39 경고 요약 게이트 운영

- 템플릿 런타임의 `scripts/message_queue.py warning-summary-gate`는 `PASS_39` 경고 정책과 함께 운영에서 직접 사용한다.
- 운영 입력은 템플릿 스모크와 동일한 인수를 사용한다.
  - `--summary-path`: 경고 요약 JSONL 경로
  - `--run-id`: 추적용 run_id
  - `--event-name`: 이벤트 이름
  - `--window-start`, `--window-end`: 집계 윈도우
  - `--warning`: 실행 직전 경고 카운트(`CODE=COUNT`)
  - `--max-warnings-per-context`: 컨텍스트 총 경고 상한
  - `--code-threshold`: 코드별 경고 상한(`CODE=COUNT`), 운영 정책 변경 시점 핵심 조절점
  - `--report-path`: 실행 결과가 JSONL로 append 되는 아티팩트 경로(기본: 생략)
- CI/운영에서 보고서 보존은 `PASS_39_WARNING_SUMMARY_GATE_REPORT_PATH`를 우선 주입한다.

운영 절차(변경/롤백):

1. 임계치 변경 전 현재 `PASS_39_WARNING_SUMMARY_GATE_REPORT_PATH` 대상 경로를 고정한다.
2. 임계치 후보를 적용해 게이트를 실행한다.
3. `policy_passed=false` 원인에 코드별 초과 항목이 있으면 변경 분기를 즉시 중단하고 이전 임계치로 롤백한다.
4. 릴리스 직전까지 실패가 재현되면 문맥(run/event/window)별 `code_warning_limits` 로그를 남겨서 변경 범위를 축소한다.
- 기본 룰: `code_threshold`는 조기 경고보다 점진적 강화만 허용하고, 1회 실패 시 즉시 이전 값으로 되돌린다.

운영 보고서 소비/알림(운영 대시보드 연계용, 수동 스크립트):

- `PASS_39_WARNING_SUMMARY_GATE_REPORT_PATH`의 누적 JSONL을 소비해 컨텍스트별 실패를 즉시 추출한다.
- 알림 기준 임계치 실패는 `policy_passed=false` 이벤트와 `reasons` 문자열의 갱신 빈도(`code_warning_limits`) 조합으로 판단한다.
- 운영자가 스크립트를 통해 대시보드에 반영할 수 있는 최소 규칙:
  - 실패 건수 증가 시 `event_name="smoke"` 또는 `run_id` 기준으로 최근 7개 실행만 비교
  - 동일 코드(`PASS_39_*`)가 연속 3회 초과 실패하면 경고 레벨 상향
  - 실패 원인(`reasons`) 내 `code=` 패턴 증가 추세를 임시 규칙 검토 항목으로 등록

- 리포트 소비기:
  - `src/agent_runtime/templates/project/scripts/summarize_warning_summary_gate_report.py`
  - 권장 입력: `--path .tmp/template-warning-summary-gate-report.jsonl --last 10`
  - 권장 출력: summary JSON 또는 텍스트
  - 대시보드 연동: `--github-annotations`을 붙여 CI 로그 경고로 승격 가능
- PASS-81 연계(운영 수집기):
  - `--dashboard-json`: 경보 지표를 집계한 JSON payload 생성
- `--slack-payload`: Slack Webhook 바디 형식(JSON) 생성
- `--alert-threshold`: 이 값 이상 실패 시에만 경보 이벤트/Slack 텍스트를 `warning` 상태로 표시
- 예시:
  - `python scripts/summarize_warning_summary_gate_report.py --path .tmp/template-warning-summary-gate-report.jsonl --last 20 --dashboard-json .tmp/warn-dashboard.json --slack-payload .tmp/warn-slack.json`
- PASS-82 연계(관측 수집기 매핑):
  - `--monitoring-json`: 모니터링/관측 수집기(infra ingestion) 스키마를 준수한 이벤트 JSON 생성
  - `--monitoring-source`: 수집 이벤트의 `source` 태그(기본값 `agent-runtime-template`) 설정
  - 예시:
    - `python scripts/summarize_warning_summary_gate_report.py --path .tmp/template-warning-summary-gate-report.jsonl --last 20 --monitoring-json .tmp/warn-monitoring.json --monitoring-source monitor-ci`
- PASS-83 연계(실채널 연동):
  - `--slack-webhook-url` / env `PASS_39_WARNING_SUMMARY_GATE_SLACK_WEBHOOK_URL`
  - `--monitoring-endpoint-url` / env `PASS_39_WARNING_SUMMARY_GATE_MONITORING_ENDPOINT`
  - `--fail-on-send-failures`: 채널 송신 실패 시 비정상 종료
  - `--send-on-ok`: healthy 상태도 전송하려는 경우
  - `--slack-threshold`: healthy/경고 수치가 이 값 이상일 때 Slack 전송 (`--send-on-ok` 미사용 시)
  - `--monitoring-threshold`: healthy/경고 수치가 이 값 이상일 때 monitoring 전송 (`--send-on-ok` 미사용 시)
  - `--require-send-targets`: 전송 대상이 필요한데 유효 URL이 없으면 비정상 종료
  - `--dry-run`: payload 생성만 수행하고 전송을 생략
  - 비밀값 오염(`YOUR_SLACK_WEBHOOK_URL`, `placeholder` 등) 감지 시 전송하지 않고 경고만 남김
  - 예시:
    - `PASS_39_WARNING_SUMMARY_GATE_SLACK_WEBHOOK_URL=$SLACK_URL PASS_39_WARNING_SUMMARY_GATE_MONITORING_ENDPOINT=$MON_ENDPOINT python scripts/summarize_warning_summary_gate_report.py --path .tmp/template-warning-summary-gate-report.jsonl --last 20 --slack-webhook-url "$PASS_39_WARNING_SUMMARY_GATE_SLACK_WEBHOOK_URL" --monitoring-endpoint-url "$PASS_39_WARNING_SUMMARY_GATE_MONITORING_ENDPOINT" --fail-on-send-failures`

사전 dry-run 워크플로우(임계치 변경 전):

1. 변경할 코드별 임계치 후보를 `--code-threshold`로 준비한다.
2. `--dry-run` 옵션으로 동일 커맨드 실행한다.
3. 반환 코드가 항상 0이어야 하며, JSON 출력의 `policy_passed=false` 여부와 `reasons`를 검토한다.
4. 실패 이유가 운영 수용 범위 안이면 실제 임계치 변경을 승인한다.

권장 dry-run 예시:

```sh
PYTHONPATH=src python scripts/message_queue.py warning-summary-gate \
  --summary-path .tmp/summary.jsonl \
  --run-id run-template-smoke-76 \
  --event-name smoke \
  --window-start 2026-06-09T00:00:00Z \
  --window-end 2026-06-09T00:01:00Z \
  --warning PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE=1 \
  --max-warnings-per-context 2 \
  --code-threshold PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE=1 \
  --report-path .tmp/template-warning-summary-gate-report.jsonl \
  --dry-run
```

## PASS-85 연계(CI 라우팅 정책 고정)

- CI 요약 단계 기본 라우팅:
  - `--monitoring-threshold 1`로 monitoring 이벤트는 경보 상태를 기본으로 전파
  - `--slack-threshold 3`으로 Slack은 더 높은 장애 구간에서만 전송
- `main`, `release/*` 브랜치/태그 기준 동작:
  - `.github/workflows/test.yml`에서 release 브랜치 계열일 때만 `--require-send-targets` 적용
  - 해당 옵션은 비밀값이 유효하지 않거나 누락된 경우 CI 실패로 반영
- 운영 예시:
  - `--require-send-targets --monitoring-threshold 1 --slack-threshold 3`

## PASS-86 연계(요약 게이트 브랜치 정책 정규화)

- 워크플로우 정책을 명시적으로 고정해 분기 중복을 줄인다.
- CI에서 release-eligible ref 목록은 정책 상수 `PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS`로 관리한다.
  - 기본값: `refs/heads/main`, `refs/heads/release/`, `refs/tags/`
- 해당 목록에 현재 `github.ref`가 prefix match 되면 `--require-send-targets`를 항상 부여한다.

## PASS-87 연계(릴리스 정책-릴리스프리플라이트 동기화)

- `release-preflight`도 `PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS`를 정책 소스로 함께 읽는다.
- `release-preflight` 결과에 `warning-summary-gate-strict-refs` 항목이 추가되어, 정책 미설정 여부/포맷 정합성을 같이 노출한다.
- 정책 문자열이 비어 있거나 `refs/` 접두사 형식이 아닐 경우 별도 finding이 생성되어 배포 준비에서 즉시 확인 가능하다.

## PASS-88 연계(수동/재사용 워크플로우 입력 연동)

- `PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS`는 `.github/workflows/test.yml`의 `workflow_call`/`workflow_dispatch` 입력으로 재사용 가능하다.
- 입력 이름: `warning_summary_gate_strict_refs`
- 기본값은 `refs/heads/main`, `refs/heads/release/`, `refs/tags/`의 줄바꿈 구분 문자열이다.
- 워크플로우 실행/호출 시 입력이 제공되면 release 요약/프리플라이트 단계에 동일한 strict-ref 정책이 반영된다.

## PASS-89 연계(입력 정책 정규화 및 추적성)

- `workflow_call`/`workflow_dispatch` 입력값의 개행 문자를 `\r`를 제거해 정규화한 뒤 `PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS`로 반영한다.
- 입력이 비워진 경우에는 기본 job env 정책을 사용하도록 폴백 처리한다.
- 요약 단계에서 적용된 strict-ref 정책을 로그로 출력해 재현 실행 시 정책 drift를 쉽게 추적한다.

## PASS-90 연계(빈 입력/공백 정규화 방어)

- `workflow_call`/`workflow_dispatch` 입력이 공백/CRLF만 포함해도 기본 strict-ref 정책을 폴백 적용하도록 보강한다.
- 정책 라인을 좌우 공백 정리 후 빈 라인을 제거해 `github.ref` prefix match 오동작을 방지한다.

## PASS-91 연계(재현 실행 추적성 검증)

- `workflow_call`/`workflow_dispatch`에서 해석된 strict-ref 정책이 어떤 입력에서 왔는지 `workflow` 로그/summary에서 추적 가능해야 한다.
- 검증 케이스(재현용):
  - 기본 실행: 입력 비어있음 → `source: job_env_default` 또는 `fallback_job_env_default`
  - 수동 실행: `refs/heads/main` 한 줄만 전달 → `source: workflow_dispatch_input`이 반영되어 `--require-send-targets` 유효
- `PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS` 재해석 결과가 `require-send-targets` 판정과 일치해야 함.

## PASS-92 연계(단일 판별 채널 단일화)

- `strict-ref` 정책 해석(`workflow_call`/`workflow_dispatch`)에서 `source`, `refs`, `require_send_targets`를 한 번 계산해 summary/로그에 함께 기록한다.
- 요약 단계에서 `require-send-targets`는 별도 loop 재판별 없이 step output을 그대로 사용해 결정 일관성을 유지한다.
- 기본 env 폴백 라인과 입력 라인 모두 공백/CR/빈 줄 정규화를 거쳐 prefix-match 입력 오차를 줄인다.
- 재현 시나리오:
  - 입력 공백/기본 폴백 케이스에서 `require_send_targets=0`인지,
  - 매칭되는 ref 입력(`refs/heads/main`)에서 `require_send_targets=1`인지,
  - Summary와 실행 로그 값이 서로 일치하는지 확인한다.

## PASS-93 연계(워크플로우 실행 증빙 아티팩트)

- strict-ref 정책 해석/판정 결과를 `.tmp/warning-summary-strict-ref-policy.json` 아티팩트로 남겨 추적한다.
- 아티팩트 필드:
  - `github_event_name`, `github_ref`, `run_id`, `job_attempt`, `matrix_python_version`
  - `strict_refs_source`, `strict_refs`, `require_send_targets`
- 수동 실행(`workflow_dispatch`)과 기본 실행 모두에서 `.tmp/warning-summary-strict-ref-policy.json` 생성을 기대한다.

## PASS-94 연계(증거-결정 일치 검증)

- strict-ref 결정 단계에서 생성한 아티팩트(`.tmp/warning-summary-strict-ref-policy.json`)와
  워크플로우 step output(`github_event_name`, `github_ref`, `run_id`, `job_attempt`,
  `strict_refs_source`, `strict_refs`, `require_send_targets`)를 CI에서 즉시 비교한다.
- 정합성 실패 시 즉시 fail 하여 `summary`/artifact 간 drift를 유입되지 않게 차단한다.
- 확인 항목:
  - strict-ref source 일치
  - strict-ref 라인 정규화(`trim`/공백/CR 제거) 후 일치
  - require-send-targets 일치
- 기대 동작:
  - `--require-send-targets` 적용 여부가 summary 로직에서 별도 재판별되지 않고, 동일 판정값이 artifact/summary 둘 다 반영되는지 추적한다.

## PASS-95 연계(재현 도구 표준화)

- `scripts/warning_summary_strict_ref_policy.py`를 통해
  - `--mode write`: 결정값 기반 `warning-summary-strict-ref-policy.json` 생성
  - `--mode validate`: step output/ artifact 결정값 정합성 비교
  를 표준 재현 루틴으로 고정한다.
- 수동 운영에서도 동일 비교 코드를 재사용하므로, `workflow_dispatch` 재현 시 `artifact`와 `요약 판정값`의 일치 확인을 빠르게 반복 가능하다.

## PASS-96 연계(회귀 차단 테스트)

- `scripts/warning_summary_strict_ref_policy.py`의 핵심 동작을 패키지 테스트로 고정.
  - write/validate roundtrip 성공
  - strict-ref 라인 정규화 일치(`CRLF`, 공백, 빈 줄 정리) 성공
  - mismatch 탐지 실패
  - artifact 누락 시 fail 하위 케이스
- 새 테스트 파일:
  - `tests/test_warning_summary_strict_ref_policy.py`

## PASS-97 연계(환경 fallback 재현 고정)

- `scripts/warning_summary_strict_ref_policy.py`의 환경변수 fallback 동작을 고정.
  - `--mode write/validate` 모두에서 `--github-*`, `--matrix-*`,
    `--strict-refs-source`, `--strict-refs`, `--require-send-targets`가 없을 때
    `GITHUB_*`, `MATRIX_PYTHON_VERSION`, `STRICT_*` 환경변수로 동작하는지 검증.
- 재현 시나리오:
    - `.github/workflows/test.yml`/README의 `--mode` 호출과 별개로, local 재현은
      환경변수 주입만으로 동일 동작 보장 여부 점검.

## PASS-98 연계(요약 게이트 전송 판단 정합성)

- `src/agent_runtime/templates/project/scripts/summarize_warning_summary_gate_report.py`의
  `--require-send-targets` 동작을 고정.
  - 정책 실패 건수/임계치가 낮아 전송이 발생해야 하는 경우에만 유효 target 결함이 실패로 이어져야 함.
  - 정책 실패가 없거나 임계치 미도달로 전송이 발생하지 않는 경우에는
    `--require-send-targets`가 실패를 강제하지 않아야 함.
- 검증 케이스:
  - non-send 시나리오: `policy_passed=True`, `alert-threshold=5`, `--require-send-targets`만 사용 → 정상 종료
  - send-on-ok 시나리오: `policy_passed=True`, `--send-on-ok --require-send-targets` + invalid target → 실패

## PASS-99 연계(Preflight strict-ref 판정 정합성)

- `agent_runtime release-preflight`의 strict-ref 입력 처리 경계를 고정.
  - 줄 단위 정규화(공백/빈 줄 제거)와 빈 문자열/미설정 판정 구분을 회귀 고정.
  - `refs/` prefix 위반 항목은 `invalid-warning-summary-gate-strict-ref`로 일관 보고.
- 신규 테스트:
  - `tests/test_release_preflight_warning_summary_gate_strict_refs.py`

## PASS-100 연계(Preflight 렌더 보고서 정합성)

- `agent_runtime release-preflight`의 strict-ref 판정 결과가 report 체크 상태/상세/행(row)까지 일관되게 반영되는지 고정.
- `warning-summary-gate-strict-refs` 항목이:
  - `blocked`/`ok` 상태를 정확히 노출
  - `refs=` 상세정보 포맷을 정확히 노출
  - 마크다운 렌더 문자열에 일관 포함
- 검증 테스트:
  - `tests/test_inventory_sync_sanitize.py`에 preflight `build_preflight_plan` + `render` 기반 추가

## PASS-101 연계(strict-ref 입력 우선순위)

- `agent_runtime release-preflight`의 `warning-summary-gate-strict-refs` 입력 원천 우선순위를 고정.
  - CLI `--warning-summary-gate-strict-refs`가 설정되면 env(`PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS`)보다 우선.
  - CLI 미지정 시 env를 fallback 사용.
- 신규 테스트:
  - `tests/test_release_preflight_warning_summary_source_precedence.py`

## PASS-102 연계(CI release-preflight strict-ref 인자 고정)
- `agent_runtime release-preflight`가 workflow에서 계산된 strict-ref를 env 우회가 아닌 CLI arg로 직접 받도록 고정.
- `release-preflight` 재현 실행은 `warning-summary strict-ref policy inputs`의 정책 해석 결과를 그대로 `--warning-summary-gate-strict-refs`로 반영.
- CI 재현성 보강: workflow step 문자열 기반 점검에서 CLI arg 노출을 확인.

## PASS-103 연계(문서 재현 실행에 strict-ref 전달 예시 반영)
- `README.md` 재현 예시 `release-preflight` 호출에 `--warning-summary-gate-strict-refs`를 반영해, 실제 운영 입력 경로를 문서에서 그대로 재현할 수 있도록 정리.

## PASS-104 연계(CI release-preflight 호출 블록 경로 고정)
- `tests/test_inventory_sync_sanitize.py`에서 `release-preflight` 실행 블록만 분리해 `--warning-summary-gate-strict-refs "${{ steps.resolve_warning_summary_strict_refs.outputs.strict_refs }}"` 존재를 검증.
- 동일 블록에서 `PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS` env 문자열 노출이 없는지 확인해 CLI 경로 우선을 고정.

## PASS-105 연계(CI 테스트 보정: 스텝 추출 유틸로 릴리즈 프리플라이트 검증 강화)
- `tests/test_inventory_sync_sanitize.py`에 workflow step 추출 헬퍼를 추가해 `Check release preflight` 블록을 안정적으로 파싱.
- 검증 항목에 `--check` 경로의 실행 커맨드 헤더(`PYTHONPATH=.tmp/public-source/src python -m agent_runtime.cli release-preflight`)를 추가해 블록 전용 정합성 검증.

## PASS-106 연계(CLI 빈 문자열 우선 경계 고정)
- `tests/test_release_preflight_warning_summary_source_precedence.py`에 `warning_summary_gate_strict_refs=""`(빈 문자열) 경로를 추가.
- env 미설정 조건에서 fallback를 쓰지 않고 CLI 빈 문자열을 그대로 전달해 precedence 경계를 보강.

## PASS-107 연계(preflight 종료코드 경계 고정)
- `agent_runtime release-preflight`의 `run_preflight`가 체크 실패 계획에 대해 종료코드를 고정하는지 회귀 고정.
- `check=True`인데도 plan.findings_count가 0이면 `0`, 하나라도 있으면 `1` 반환하도록 테스트로 고정.
- 신규 테스트:
  - `tests/test_release_preflight_warning_summary_source_precedence.py`

## PASS-108 연계(비-체크 모드 종료코드 경계 고정)
- `agent_runtime release-preflight`의 기본 동작 경계를 고정.
- `check=False`일 때 plan에 finding이 있어도 종료코드는 `0`이 되어, 실제 실패 판단이 `--check` 플래그 의존으로 제한됨을 회귀 고정.
- 신규 테스트:
  - `tests/test_release_preflight_warning_summary_source_precedence.py`

## PASS-109 연계(CLI check 플래그 전달 경계 고정)
- `agent_runtime release-preflight` CLI 진입점이 `--check` 플래그를 `run_preflight(check=...)`로 정확히 전달하는지 회귀 고정.
- 기본 실행(`--check` 미지정)에서 `check=False`, `--check` 지정에서 `check=True`가 전달되는지 검증.
- 신규 테스트:
  - `tests/test_release_preflight_warning_summary_source_precedence.py`

## PASS-110 연계(CLI strict-ref 전달 경계 고정)
- `agent_runtime release-preflight` CLI에서 `warning_summary_gate_strict_refs` 값이 미지정 시 `None`, 빈 문자열 지정 시 `""`로 그대로 `run_preflight`에 전달되는지 회귀 고정.
- `PASS-39_WARNING_SUMMARY_GATE_STRICT_REFS` 폴백 개입을 방지하는 최종 전달 경로를 CLI 진입점에서 확인.
- 신규 테스트:
  - `tests/test_release_preflight_warning_summary_source_precedence.py`

## PASS-111 연계(CLI 경로 전달 경계 고정)
- `agent_runtime release-preflight` CLI에서 경로 인자(`source`, `host-root`, `bundle-dir`, `tag-repo-dir`, `tag-install-dir`, `github-install-dir`, `host-install-dir`) 기본값 및 명시값 전달을 고정.
- `source/host-root` 미지정 시 `Path.cwd()` 기본값 전달과 각 경로 인자의 사용자 지정 값이 정확히 반영되는지 검증.
- 신규 테스트:
  - `tests/test_release_preflight_warning_summary_source_precedence.py`

## PASS-112 연계(CLI tag 전달 경계 고정)
- `agent_runtime release-preflight` CLI에서 `tag` 기본값과 사용자 지정값이 `run_preflight(tag=...)`로 정확히 전달되는지 고정.
- `build_parser()`의 기본 `tag`값과 동일값이 미지정 시 반영되는지, 명시값이 그대로 전달되는지 검증.
- 신규 테스트:
  - `tests/test_release_preflight_warning_summary_source_precedence.py`

## PASS-113 연계(CLI remote-url 전달/필수성 경계 고정)
- `agent_runtime release-preflight` CLI에서 `--remote-url` 전달을 `run_preflight(remote_url=...)`로 고정.
- `remote-url` 미지정 시 parser 실패를 고정해 진입점 자체의 필수 인자 계약을 보강.
- 신규 테스트:
  - `tests/test_release_preflight_warning_summary_source_precedence.py`

## PASS-114 연계(CLI main 엔트리 경계 고정)
- `agent_runtime release-preflight` CLI에서 `--remote-url` 누락 시 `main()`이 `SystemExit(code=2)`로 종료되는지 계약 고정.
- parser 경계만이 아닌 `main()` 진입점 경계로 이어서 필수 인자 실패를 고정.
- 신규 테스트:
  - `tests/test_release_preflight_warning_summary_source_precedence.py`

## 산출물 요건

- `pytest tests -q` 결과
- 템플릿 기본 실행 결과(`--help`, 상태 조회, 메시지 스캔)
- 최소 1건의 더미 메시지 파이프라인 처리 결과
