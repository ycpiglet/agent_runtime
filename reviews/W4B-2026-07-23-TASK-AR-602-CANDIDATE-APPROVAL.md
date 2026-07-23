---
title: TASK-AR-602 v0.7.0 Candidate Independent W4b Approval
date: 2026-07-23
status: candidate_approved
signal: pass
score: 97
verdict: GO_FOR_PR_INTEGRATION
public_release: HOLD
task_id: TASK-AR-602
verified_base: 35051f9eac9a1c7be8e7bb49d3e6b483d29eaf4a
verified_head: ce537baba99919d327f61de38e88a0d81bf52c4e
verified_implementation: 97271073a381286658e498f44b5795497e2ae8d4
verified_by: codex-task-ar-602-independent-technical-auditor-20260723
worker: /root/task-ar-602
tags:
  - w4b
  - independent-verification
  - release-candidate
  - v0.7.0
  - deployment
  - rollback
---

# TASK-AR-602 v0.7.0 Candidate Independent W4b Approval

## 판정

**PR 통합 파이프라인 진입 GO — 97/100. 공개 태그·GitHub Release는 HOLD.**

정확한 HEAD `ce537baba99919d327f61de38e88a0d81bf52c4e`와 기준 main `35051f9eac9a1c7be8e7bb49d3e6b483d29eaf4a`를 고정해 버전 캐스케이드, 집중 테스트, owner governance, clean publish bundle, release preflight 및 후보 보고서의 수치 주장을 독립 감사했다. 후보 코드에서 PR 생성을 막을 기술 blocker는 발견되지 않았다.

이 GO는 브랜치 푸시와 PR 생성·검토 진입을 허용한다. 아직 원격 브랜치, PR 및 exact-head CI가 없으므로 실제 PR 병합은 `ce537b…`의 Python 3.10/3.11/3.12 검사가 모두 성공할 때까지 HOLD다. 태그와 공개 릴리스는 병합 후 main의 동일 커밋 CI와 annotated tag 대상 일치까지 계속 HOLD다.

## 측정 결과

| 지표 | 승인 기준 | 측정값 | 출처 | 상태 / 다음 조치 |
| --- | --- | --- | --- | --- |
| 감사 HEAD | 요청 SHA와 exact match | `ce537baba99919d327f61de38e88a0d81bf52c4e` | `git rev-parse HEAD` | pass |
| 검증 기준 | 요청 base와 exact match | `35051f9eac9a1c7be8e7bb49d3e6b483d29eaf4a` | `git rev-parse` | pass |
| 버전 캐스케이드 | current `0.7.0`, mismatch 0 | `0.7.0`, `[]` | `release_version_cascade.py --check --json` | pass |
| 후보 구현 범위 | 선언된 13개 managed file만 변경 | 12 CASCADE path + host lock = 13 | commit `97271073` diff | pass |
| 집중 릴리스 테스트 | 실패 0 | 108 passed in 8.83s | 독립 pytest | pass |
| Owner governance | exit 0 | exit 0 | 독립 gate 실행 | pass |
| 공개 번들 | findings 0, 704 files | findings 0, applied 704 | 독립 임시 bundle | pass |
| Clean-bundle preflight | 13 checks, findings 0 | 13 checks, findings 0 | 독립 bundle 입력 | pass |
| Strict-ref 정책 | CI 기본 3개 ref가 유효 | main/release/tags, findings 0 | 독립 preflight | pass |
| 전체 수집 범위 | 176 files, 2,204 tests | 176 files, 2,204 collected | 독립 collect-only | pass |
| 기록된 전체 실행 | 2,204 tests, 실패 0 | 2,198 passed + 6 skipped = 2,204 | 후보 보고서 8-batch 기록 | pass, transcript 미보존은 잔여 위험 |
| 기준 main CI | Python matrix 3/3 success | run `29977819328`, 3/3 success | GitHub Actions | pass |
| exact candidate CI | 병합 전 3/3 success | 원격 branch/PR/run 없음 | GitHub 조회 | pending — PR 병합 HOLD |
| v0.7.0 공개 상태 | 후보 단계에서는 tag/release 없음 | local/remote tag 없음, release 없음 | git/GitHub readback | pass — publication HOLD |

## 커밋 계보와 변경 경계

계보는 다음과 같이 선형이며 요청된 기준과 일치한다.

```text
35051f9eac9a1c7be8e7bb49d3e6b483d29eaf4a
  -> 97271073a381286658e498f44b5795497e2ae8d4
  -> ce537baba99919d327f61de38e88a0d81bf52c4e
```

- `97271073`: `0.6.0`에서 `0.7.0`으로 deterministic cascade 13개 파일만 변경한다.
- `ce537bab`: 후보 readiness 보고서와 생성된 `reviews/INDEX.md`만 추가·갱신한다.
- production 로직, 명령 동작, 테스트 assertion은 버전 문자열 외에 변경되지 않았다.
- `git diff --check`는 검증 기준과 현재 원격 기준 양쪽에서 통과했다.

`scripts/release_version_cascade.py`가 선언한 12개 참조는 모두 `0.7.0`이며, best-effort 재생성 대상인 host lock도 package version과 upstream ref가 `0.7.0`이다. `regen_host_lock_if_needed.py --check`는 lock이 최신이라고 판정했다. 활성 코드·workflow·release fixture에서 남은 `v0.6.0` 참조는 없고, 발견된 잔여 문자열은 과거 사건 설명 주석과 self-eval baseline뿐이다.

## 코드·테스트 감사

독립 실행:

```text
py -3.10 scripts/release_version_cascade.py --check --json
py -3.10 -m pytest tests/test_inventory_sync_sanitize.py tests/test_release_execution_gate.py -q
py -3.10 scripts/owner_governance_gate.py
py -3.10 scripts/regen_host_lock_if_needed.py --check
py -3.10 -m pytest --collect-only -q
```

결과:

```text
current=0.7.0
mismatches=[]
108 passed in 8.83s
owner-governance exit=0
host lock up to date
176 test files
2204 tests collected in 3.46s
```

후보 보고서의 배치 합계도 재계산했다.

```text
passed = 192 + 169 + 273 + 162 + 213 + 254 + 710 + 225 = 2,198
skipped = 2 + 4 = 6
total = 2,198 + 6 = 2,204
```

전체 8-batch를 다시 장시간 실행하지는 않았다. 독립 감사에서는 정확한 test file/node 수를 재수집하고, 변경 표면을 직접 겨냥한 108개 테스트와 governance를 재실행했다. 동일 전체 범위는 exact-head PR matrix가 다시 실행해야 하며, 그 전 병합은 승인하지 않는다.

## Clean publish bundle 및 preflight

현재 HEAD에서 시스템 임시 디렉터리에 공개 번들을 새로 생성하고, 생성된 번들 자체를 `source`로 삼아 preflight를 실행했다.

```text
publish-bundle: files=704, findings=0, applied=704
release-preflight: 13 checks, findings=0
```

통과 항목:

- sanitize
- warning-summary strict refs
- owner document format
- state machines
- publish check
- publish bundle
- local annotated-tag smoke plan
- GitHub publish plan
- host update plan
- host upstream remote/ref match
- host update command
- host sync: updates 281, conflicts 0
- host lock: expected template digest 일치

설치 검증 디렉터리를 source/host 바깥에 둔 adversarial 호출은 `unsafe-github-install-dir` 및 `unsafe-install-dir`로 차단됐다. 계약대로 번들과 host 내부 `.tmp/` 경로를 사용한 재실행은 findings 0이었다. 안전경로 경계가 우회되지 않고 fail-closed함도 확인했다.

## 후보 보고서 주장 감사

`reviews/RELEASE-READINESS-2026-07-23-v0.7.0-CANDIDATE.md`의 핵심 주장은 측정 결과와 일치한다.

- 구현 후보 `97271073`의 13-file cascade-only 범위: 일치
- cascade current `0.7.0`, mismatches `[]`: 일치
- focused 108 passed: 독립 재현
- owner governance exit 0: 독립 재현
- publish bundle 704 files, findings 0: 독립 재현
- release preflight 13 checks, findings 0: clean bundle에서 독립 재현
- 176 files, 2,204 collected: 독립 재현
- 8-batch 산술 2,198 passed + 6 skipped: 합계 일치
- public release를 후속 exact-head gate까지 HOLD: 적절

보고서가 가리키는 코드 후보는 `97271073`이고 감사 HEAD는 readiness 기록 커밋 `ce537bab`이다. 후자는 코드 후보 이후 문서/index만 변경하므로 후보 주장의 계보가 끊기지 않는다.

## GitHub·통합 상태

감사 시점 원격 상태:

- remote `main`: `3c27bf8fa353fb46e5d5d2b6db49c3678e16b9fb`
- 기준 main `35051f9e…`: remote main보다 orchestrator-only 기록 2개 커밋 앞섬
- candidate remote branch: 없음
- candidate PR: 없음
- candidate Actions run: 없음
- `v0.7.0` local/remote tag: 없음
- `v0.7.0` GitHub Release: 없음
- latest public release: `v0.6.0`
- issue #280: OPEN
- intake #274, #279, #285, #287, #289, #290: CLOSED

기준 main의 두 선행 커밋은 T3 replan과 claim/orchestrator state이며 code/test/workflow 파일을 변경하지 않는다. 현재 상태에서 PR을 바로 열면 remote main 기준 patch는 이 두 커밋까지 포함해 28개 파일로 보인다. PR 생성 전에 remote base를 `35051f9e…`까지 정렬하거나, PR 리뷰에서 이 두 orchestrator 커밋이 의도된 범위임을 명시적으로 포함해야 한다.

## GO/HOLD 경계

### GO

- `codex/task-ar-602-v0-7-0-release`를 push한다.
- `main` 대상 PR을 생성한다.
- verified base와 PR patch scope를 확인한다.
- exact head `ce537b…`의 Python 3.10/3.11/3.12 검사를 실행한다.

### 계속 HOLD

- exact-head matrix가 3/3 success이기 전 PR 병합
- 병합 commit의 post-merge main matrix가 3/3 success이기 전 태그 생성
- annotated `v0.7.0` object type과 peeled target가 검증된 merge commit과 같음을 증명하기 전 tag push
- GitHub Release publication 및 #280 close

## 잔여 위험

- 로컬 8-batch 전체 실행의 원시 transcript/evidence JSON은 후보 보고서와 별도로 보존되지 않았다. 독립 collect-only, 집중 108개, governance, clean-bundle preflight는 재현됐으며 exact-head PR matrix를 병합 차단 게이트로 유지한다.
- verified local base가 현재 remote main보다 두 orchestrator 커밋 앞서므로 PR patch가 후보 보고서의 15-file base-relative diff보다 넓게 보일 수 있다. base 정렬 또는 명시적 scope review가 필요하다.
- `v0.6.0` 이후 누적 변경량이 크다. 공개 전 generated release notes를 사람 검토하고 내부 경로·비밀·일시적 evidence가 포함되지 않았는지 확인해야 한다.
- 공개 태그 이후 rollback은 tag 이동이 아니라 release warning과 `v0.7.1` forward-fix여야 한다.

위 위험은 PR 생성·검토 진입을 막지 않지만, 병합 및 공개 artifact 생성 전에는 명시된 exact-head gate를 모두 충족해야 한다.
