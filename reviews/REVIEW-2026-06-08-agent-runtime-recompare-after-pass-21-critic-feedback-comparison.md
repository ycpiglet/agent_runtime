# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-21-critic-feedback-comparison

## Bottom Line

PASS-20에서 반영된 `template self-contained`, `template smoke CI`, `message claim`, `의존성 계약`은 유지되고, 이번 PASS-21에서 핵심적으로 추가된 ToolRunner hardening이 반영되었다.
다만 여전히 **임의 파워셸/셸 인젝션 우회**, **원격/분산 FS에서의 lease 정합성**, **프로파일 권한 확장 시 감사/운영 정합성**은 미해결 상태라 남겨 둔다.

## Signal

| 항목 | Baseline (초기 비판 리뷰) | PASS-20 | PASS-21 (현재) |
|---|---|---|---|
| 템플릿 self-contained | Critical (누락으로 즉시 실패) | ✅ Closed | ✅ Closed (변화 없음) |
| 템플릿 실행 smoke CI | Critical (미검증) | ✅ Closed | ✅ Closed (유지) |
| ToolRunner sandbox | High (임의 `python/git` 경로 우회) | ⚠️ 일부 완화 | ✅ 부분 완화 + 추적 추가 (`command_profile`, 감사로그, 우회 패턴 확장 차단) |
| 메시지 claim 병렬성 | High (중복 claim/reply 위험) | ✅ 크게 개선 | ✅ 유지(해당 항목 변화 없음) |
| 의존성 계약 | Medium (runtime/템플릿 오염) | ✅ Closed | ✅ Closed |

### 검증 근거 (현재)

- `C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests -q` → `132 passed`
- `...python.exe -m pytest tests/test_template_agent_tools.py tests/test_template_smoke.py tests/test_template_message_queue.py tests/test_provider_import_contract.py tests/test_doctor.py -q` → `38 passed`

## Insight

1. 이번 패스의 실체적 변화는 `ToolRunner` 쪽이다. 기존 임계 이슈 중 가장 공격적인 부분(임의 실행)에서 진전이 있었다.
2. 기존 비판 리뷰에서 요구한 **구조적 공통 이슈 5개**는 여전히 `템플릿/claim/의존성`은 안정적이고, `샌드박스`만 분리되어 추적되기 시작했다.
3. 다만 보안은 “차단 규칙 수량이 증가한 상태”에서 “플랫폼별 우회까지 줄인 상태”로 보기엔 아직 이르다. 특히 분산환경 claim/운영 감사는 별도 PASS에서 독립 검증 필요.

## Decision

### 이번 패스에서 닫힌 항목

- `providers/agent_tools.py`
  - `ci / owner / research` 프로파일 기반 실행 정책 도입
  - `run_command`에 `command_audit` 추가 및 최대 보존 개수 상수 지정 (`MAX_AUDIT_ENTRIES`)
  - `python -c`, `python -`, 임의 `pip`/`git` write 경로 등을 거부하도록 규칙 확장
  - 경로 토큰 정규화 및 메시지에 표시할 경고/정책 텍스트 통일
  - 허용/차단 내역 감사 로그 추적 및 tail 조회 API 추가
- `tests/test_template_agent_tools.py`
  - 위험 패턴 계열 회귀 추가:
    - `python3`, `scripts/../` 경로 변형, 따옴표/개행/쉘 토큰 혼합 형태 차단
    - 허용 command audit 수집/경계(bound) 테스트
    - profile 분기(`ci` vs `research`, `owner`)에 대한 allow/deny 비교

### 남은 미비점 (재평가 대상)

- **R1: 플랫폼/셸 레벨 우회 미검증**
  - PowerShell/Windows 환경에서 특수 토큰 우회(변형 인용, 환경변수 치환, `%COMSPEC%` 경로형 실행 등)가 완전히 포괄되지 않음.
- **R2: 분산/원격 FS에서 claim 정합성 증명 미흡**
  - 현재 동시성/lease 검증은 주로 단일 FS 전제에서 빠른 검증에 그침.
- **R3: `owner/research` 확장과 운영 감사 정합성**
  - 허용군 확대가 필요한 구간에서 `audit`는 남아 있으나, 운영 정책 문서/승인 로직과 1:1 매핑이 아직 자동 점검되지 않음.

### 후속 점수(현재 비교)

- Public release hygiene: B+ (유지)
- Sync/update safety: B+ (유지)
- Template execution completeness: B- (유지)
- Parallel claim safety: B- (유지)
- Security / command sandbox: C- (개선됨, 완결 아님)
- Governance/governance design: B (유지)
- Self-improvement loop: C- (유지)

## 참고

- `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md`
- `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-20-critic-feedback-retrospective.md`
