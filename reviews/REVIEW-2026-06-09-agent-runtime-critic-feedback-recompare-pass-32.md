# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-32

## Bottom Line

`PASS-31`에서 추려둔 `R1`/`R2` 미결 항목을 실행 근접 테스트 보강까지 반영해 `PASS-32`로 정리했다.

- `R1`은 seed 기반 fuzz 조합으로 `agent_tools` command sandbox 우회 후보 집합을 재확장했다.
- `R2`는 분산/원격 FS에서 자주 보이는 원자 교체(rename) 지연/락을 모델링하는 테스트 두 건을 추가하고, 메시지 큐에 원자적 쓰기 재시도 유틸을 도입했다.
- 본 사이클은 코드 변경 반영 후 재실행 검증 기록은 남기지 않았고, 다음 사이클에서 `tests` 통합 실행으로 잠정 상태를 확정한다.

## Signal

| 항목 | PASS-31 상태 | PASS-32 변경 | 근거 |
|---|---|---|---|
| 템플릿 self-contained | ✅ 유지 | ✅ 유지 | 기존 증적 유지 |
| 템플릿 CI 누락 | ✅ 유지 | ✅ 유지 | 기존 증적 유지 |
| ToolRunner command sandbox (R1) | `R1` 추가 fuzz 필요 | ✅ 확장 | `tests/test_template_agent_tools.py::test_run_command_blocks_seeded_fuzz_vectors` 추가 |
| 병렬 claim 정합성 | ✅ 유지 | ✅ 유지 | 기존 병렬/회수 테스트 유지 |
| 분산/원격 FS claim robustness (R2) | `R2` 진행 중 | 🔧 진행 | `tests/test_template_message_queue.py`에 분산 지연 주입/복구 실패 정리 테스트 추가 및 원자 쓰기 재시도 적용 |
| 의존성 계약 | ✅ 유지 | ✅ 유지 | 기존 증적 유지 |

## Evidence (pass-32)

- `tests/test_template_agent_tools.py`
  - 신규 유닛: `test_run_command_blocks_seeded_fuzz_vectors`
- `src/agent_runtime/templates/project/scripts/message_queue.py`
  - `_write_text_atomic` 추가
  - `_write_json_atomic` 및 claim/회신 경로에 재사용 반영
- `tests/test_template_message_queue.py`
  - `test_claim_message_retries_frontmatter_replace_after_transient_fs_delay`
  - `test_claim_message_releases_claim_when_frontmatter_replace_keeps_failing`

## Remaining Risk

- Seed 기반 fuzz는 확장 방향을 열어 두었으나, 실제 플랫폼 특성(CMD/Pwsh 조합, 다중 인코딩 순환) 커버리지는 다음 사이클에서 측정 필요.
- R2의 분산 FS 시뮬레이션은 `os.replace` 경합 중심이며, `open/fsync/stat` 경로까지 확장할 여지가 남아 있음.

## Decision

- `PASS-32`의 보강은 완료 상태로 보고하고, 다음 단계에서 전체 테스트 스위트를 실행해 PASS-33에서 블록/회귀 여부를 확정한다:
  - `tests/test_template_agent_tools.py` 전체
  - `tests/test_template_message_queue.py` 전체
  - 기존 회귀군(`tests`)

## Cross-Reference

- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-31.md`
- `src/agent_runtime/templates/project/scripts/providers/agent_tools.py`
- `src/agent_runtime/templates/project/scripts/message_queue.py`
- `tests/test_template_agent_tools.py`
- `tests/test_template_message_queue.py`
