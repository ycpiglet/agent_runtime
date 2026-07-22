---
type: role-review
task_id: TASK-AR-598
claim_id: CLAIM-REVIEW-TASK-AR-598-skeptic-closeout
role: skeptic
verdict: pass
reviewed_commit: da1a180
integrated_commit: 8de7e44
reviewed_at: 2026-07-19T12:49:55+09:00
supersedes: "TASK-AR-598 pre-closeout skeptic FAIL (message-only evidence)"
baseline_implementation: 3066f3c
baseline_w4a: 0ebbc02
hardening_commits:
  - d020ee6
  - da1a180
resolved_findings:
  - SKEPTIC-598-001
  - SKEPTIC-598-002
  - SKEPTIC-598-003
  - SKEPTIC-598-004
verification_commands:
  - "Release the original MSG-x/../../../outside/VICTIM traversal fixture against the hardened CLI and compare the full file-tree digest"
  - "Run the original claimed message with missing claim fixture against the hardened CLI and compare message/tree state"
  - "Inject build_report failure into default JSON and strict JSON modes and parse both outputs"
  - "Replace message_queue._read_claim with an AssertionError spy while scanning a traversal message ID"
  - "Run the default audit on malformed state and compare all file hashes before and after"
  - "py -3.10 -m pytest tests/test_session_resume_check.py tests/test_orchestrator_atomic_writes.py -q -p no:cacheprovider"
  - "py -3.10 scripts/regen_host_lock_if_needed.py --check"
  - "git diff --check d3b069c..8de7e44"
  - "git diff --exit-code 8de7e44..HEAD -- src/agent_runtime/templates/project/scripts/session_resume_check.py tests/test_session_resume_check.py tests/fixtures/host/agent_runtime.lock.json"
findings: []
---

# TASK-AR-598 Skeptic Closeout Review

## 최종 판정

PASS. 초기 implementation `3066f3c` 및 W4a `0ebbc02`에 대한 사전 적대
검토에서는 세 차단 finding과 하나의 추가 정보경계 우려가 확인됐습니다.
`d020ee6`이 mutating recovery/checkpoint CLI와 JSON/strict 결함을 제거했고,
`da1a180`이 남아 있던 out-of-bound claim read까지 차단했습니다.

동일한 공격 fixture를 hardening 이후 다시 실행한 결과 네 우려가 모두
재현되지 않았습니다. 새 차단 finding은 없습니다. 이 문서는 사전 검토에서
메시지로 보고한 TASK-AR-598 FAIL 판정을 supersede합니다.

root에 통합된 대응 commit은 각각 `d3b069c`와 `8de7e44`이며, 최종 product
파일은 reviewed commit `da1a180` 이후 변경되지 않았습니다.

## 초기 Finding과 해소 판정

### SKEPTIC-598-001 — `--fix` message ID 경로 이탈 삭제 (High) — RESOLVED

초기 구현은 claimed message의 frontmatter `id`를 검증하지 않고
`message_queue.recover_stale_claim`에 전달했습니다. 다음 ID를 사용한 임시 host
fixture에서 claims 디렉터리 밖 victim claim이 실제 삭제됐습니다.

```text
MSG-x/../../../outside/VICTIM
```

초기 측정값은 `victim_before=true`, `victim_after=false`였고, CLI는 삭제가
발생했음에도 recovery가 declined됐다고 출력했습니다.

`d020ee6`은 `--fix`, `_apply_fix`, checkpoint writer/subcommand를 완전히
제거해 SessionStart 도구를 report-only로 축소했습니다. 동일 공격을 다시
실행하면 `--fix`는 argparse exit 2로 거부되고 victim은 유지되며 전체 tree
digest가 변하지 않습니다.

`da1a180`은 read 경계도 추가로 닫았습니다. claim path를 만들기 전에
message ID를 `MSG-[A-Za-z0-9._-]+` 형식으로 제한하고, traversal ID는
`invalid-message-id`로 보고한 뒤 즉시 건너뜁니다. 회귀 테스트는
`message_queue._read_claim`을 AssertionError spy로 바꾸어 unsafe read가 한 번도
호출되지 않음을 검증하며 victim 내용도 그대로 유지합니다.

### SKEPTIC-598-002 — missing-claim 복구가 작동하지 않음 (Medium) — RESOLVED

초기 `--fix`는 claimed message의 claim file이 없음을 `missing-claim`으로
보고하면서도 message를 `open`으로 돌리지 못했습니다. 실측 상태는 계속
`claimed`였고 출력은 recovery declined였습니다.

Hardening은 불완전하고 오해를 부르는 복구 기능 자체를 제거했습니다.
missing-claim은 이제 명확한 report-only anomaly이며, 명시적 operator 판단 없이
message 상태를 변경한다고 주장하지 않습니다. 같은 fixture에서 unsupported
`--fix`는 exit 2이고 message 및 tree는 완전히 불변입니다.

### SKEPTIC-598-003 — JSON/strict 계약 불일치 (Medium) — RESOLVED

초기 구현은 `--fix --json`에서 JSON 앞에 일반 경고문을 출력했고,
unexpected exception을 `--strict`로 실행해도 exit 0을 반환했습니다.

`d020ee6` 이후 mutating `--fix` 조합은 지원 인터페이스에서 제거됐습니다.
지원되는 JSON audit에서 `build_report` 예외를 주입한 최종 측정은 다음과
같습니다.

| 모드 | 종료 코드 | 출력 |
| --- | ---: | --- |
| default `--json` | 0 | parseable `{warnings: [...], clean: false}` |
| `--json --strict` | 1 | parseable `{warnings: [...], clean: false}` |

따라서 SessionStart 기본은 non-blocking이고, strict는 예상치 못한 실패를
차단 신호로 올리며, JSON 출력은 순수하게 유지됩니다.

### SKEPTIC-598-004 — traversal ID의 out-of-bound claim read (Low) — RESOLVED

Mutating CLI 제거 후에도 초기 scanner는 traversal ID로 claims 디렉터리 밖
`.claim` 파일의 존재와 stale 여부를 읽고 분류할 수 있었습니다. 삭제 위험은
사라졌지만 정보경계가 완전히 닫히지는 않은 상태였습니다.

`da1a180`의 basename-safe ID 검증은 경로 계산과 `_read_claim`보다 먼저
실행됩니다. traversal fixture는 이제 `invalid-message-id` 한 건만 반환하며
외부 victim file을 열지 않습니다.

## Report-only 및 호환성 확인

- 기본 audit은 malformed pointer/claim에서도 exit 0입니다.
- 기본 실행 전후 임시 host의 모든 파일 경로와 SHA-256 map이 동일했습니다.
- malformed `{half-written` claim은 실제 message_queue의 `_read_claim -> {}` 및
  `_is_stale_claim -> true` 분기를 거쳐 `stale claim file`로 보고됩니다.
- current template의 `message_queue` API와 runtime 경로
  (`agents/runtime/claims`, `agents/messages/inbox`)가 일치합니다.
- SessionStart hook 순서는 update notify, dashboard, claim reaper, interrupted
  detector, resume check 순으로 유지됩니다.
- Mutating checkpoint writer와 `--fix` interface는 더 이상 노출되지 않습니다.

## 최종 검증 결과

| 항목 | 결과 |
| --- | --- |
| Focused session/atomic suite | `12 passed in 1.44s` |
| Host lock | current |
| Integrated diff quality | whitespace 오류 없음 |
| Post-integration target drift | 없음 (`8de7e44..HEAD`) |
| Default audit writes | 0 |
| Traversal victim reads | 0 |
| Traversal victim writes/deletes | 0 |
| Unexpected failure JSON | parseable |
| Strict unexpected failure | exit 1 |
| 새 findings | 없음 |

## 잔여 위험

- 이 도구는 여러 `message_queue` private helper를 사용하므로 해당 API를
  변경할 때 focused compatibility test를 함께 갱신해야 합니다.
- 큰 host에서 디렉터리 scan 시간이 30초 hook timeout에 근접할 가능성은 운영
  관찰 대상이지만, 현재 fixture와 범위에서는 차단 증거가 없습니다.

위 잔여 위험은 TASK-AR-598 acceptance criterion을 차단하지 않습니다.

## 범위 준수

코드, claim, release 상태, `reviews/INDEX.md`, 커밋은 변경하지 않았습니다.
이 skeptic role-review 문서만 추가했습니다.
