# Tasks: Security Recommendations Implementation

**Input**: Design documents from `/specs/006-security-recommendations/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included per constitution requirement (TDD with ≥80% coverage)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Based on plan.md, this project uses single project structure:
- Source: `src/github_analyzer/`
- Tests: `tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and core security module creation

- [ ] T001 Create `src/github_analyzer/core/security.py` with module docstring and imports (pathlib, os, stat, logging, platform)
- [ ] T002 [P] Define constants in `src/github_analyzer/core/security.py`: FORMULA_TRIGGERS, SECURITY_LOG_PREFIX, API_LOG_PREFIX, DEFAULT_TIMEOUT_WARN_THRESHOLD, DEFAULT_SECURE_MODE
- [ ] T003 [P] Create `tests/unit/core/__init__.py` if not exists
- [ ] T004 [P] Create `tests/unit/core/test_security.py` with test class structure and imports

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core security utilities that MUST be complete before user stories can integrate them

**⚠️ CRITICAL**: User story integration cannot begin until this phase is complete

**TDD Approach**: Write tests FIRST (T005-T010), then implement (T011-T018), then verify (T019-T020)

### Step 1: Write Failing Tests First (TDD)

- [ ] T005 Write unit tests for `validate_output_path()` in `tests/unit/core/test_security.py` covering: valid paths, path traversal rejection, symlink resolution (FR-013), absolute paths, error message format
- [ ] T006 [P] Write unit tests for `escape_csv_formula()` and `escape_csv_row()` in `tests/unit/core/test_security.py` covering: all trigger chars (`=+-@\t\r`), normal text, non-strings, empty values
- [ ] T007 [P] Write unit tests for `check_file_permissions()` and `set_secure_permissions()` in `tests/unit/core/test_security.py` covering: Unix permissions, Windows skip behavior
- [ ] T008 [P] Write unit tests for `validate_content_type()` in `tests/unit/core/test_security.py` covering: matching types, mismatched types, missing header entirely (FR-006)
- [ ] T009 [P] Write unit tests for `log_api_request()` in `tests/unit/core/test_security.py` covering: log format with `[API]` prefix, token masking
- [ ] T010 [P] Write unit tests for `validate_timeout()` in `tests/unit/core/test_security.py` covering: normal timeout, high timeout warning, env var threshold override

### Step 2: Implement to Pass Tests

- [ ] T011 Implement `validate_output_path()` function in `src/github_analyzer/core/security.py` per contract (raises `ValidationError` with format per FR-001)
- [ ] T012 [P] Implement `escape_csv_formula()` function in `src/github_analyzer/core/security.py` per contract
- [ ] T013 [P] Implement `escape_csv_row()` function in `src/github_analyzer/core/security.py` per contract
- [ ] T014 [P] Implement `check_file_permissions()` function in `src/github_analyzer/core/security.py` per contract
- [ ] T015 [P] Implement `set_secure_permissions()` function in `src/github_analyzer/core/security.py` per contract
- [ ] T016 [P] Implement `validate_content_type()` function in `src/github_analyzer/core/security.py` per contract (handles missing header per FR-006)
- [ ] T017 [P] Implement `log_api_request()` function in `src/github_analyzer/core/security.py` per contract
- [ ] T018 [P] Implement `validate_timeout()` function in `src/github_analyzer/core/security.py` per contract (uses `GITHUB_ANALYZER_TIMEOUT_WARN_THRESHOLD` per FR-011)

### Step 3: Verify and Export

- [ ] T019 Export all public functions in `src/github_analyzer/core/__init__.py`
- [ ] T020 Run `pytest tests/unit/core/test_security.py -v` and verify all tests pass

**Checkpoint**: Foundation ready - all security utilities implemented and tested per TDD. User story integration can now begin.

---

## Phase 3: User Story 1 - Output Path Validation (Priority: P1) 🎯 MVP

**Goal**: Prevent path traversal attacks by validating output directory paths

**Independent Test**: Run `python -c "from src.github_analyzer.core.security import validate_output_path; validate_output_path('../../../etc')"` and verify ValidationError is raised

### Implementation for User Story 1

- [ ] T021 [US1] Import `validate_output_path` from `core.security` in `src/github_analyzer/exporters/csv_exporter.py`
- [ ] T022 [US1] Call `validate_output_path()` in `CSVExporter.__init__()` before `mkdir()` in `src/github_analyzer/exporters/csv_exporter.py`
- [ ] T023 [P] [US1] Import `validate_output_path` in `src/github_analyzer/exporters/jira_exporter.py` and add validation
- [ ] T024 [P] [US1] Import `validate_output_path` in `src/github_analyzer/exporters/jira_metrics_exporter.py` and add validation
- [ ] T025 [US1] Add test for path validation in `tests/unit/exporters/test_csv_exporter.py`: test_rejects_path_traversal
- [ ] T026 [US1] Run `pytest tests/unit/exporters/test_csv_exporter.py -v` and verify path validation tests pass

**Checkpoint**: User Story 1 complete. Path traversal attacks are now blocked in all exporters.

---

## Phase 4: User Story 2 - Dependency Version Pinning (Priority: P1)

**Goal**: Pin all dependencies with exact versions for reproducible builds and security audits

**Independent Test**: Check `requirements.txt` contains `requests==2.31.0` (not `>=2.28.0`)

### Implementation for User Story 2

- [ ] T027 [US2] Update `requirements.txt` to pin `requests==2.31.0` (replace `requests>=2.28.0`)
- [ ] T028 [US2] Update `requirements-dev.txt` to use bounded ranges: `pytest>=7.0.0,<9.0.0`, `pytest-cov>=4.0.0,<6.0.0`, `ruff>=0.1.0,<1.0.0`, `mypy>=1.0.0,<2.0.0`
- [ ] T029 [US2] Run `pip install -r requirements.txt` to verify pinned versions install correctly
- [ ] T030 [US2] Run `pip install -r requirements-dev.txt` to verify dev dependencies install correctly

**Checkpoint**: User Story 2 complete. All dependencies are now pinned for reproducible builds.

---

## Phase 5: User Story 3 - CSV Formula Injection Protection (Priority: P2)

**Goal**: Escape formula trigger characters in CSV exports to prevent spreadsheet injection attacks

**Independent Test**: Export data containing `=SUM(A1)` and verify the CSV cell contains `'=SUM(A1)`

### Implementation for User Story 3

- [ ] T031 [US3] Import `escape_csv_row` from `core.security` in `src/github_analyzer/exporters/csv_exporter.py`
- [ ] T032 [US3] Modify `_write_csv()` method in `src/github_analyzer/exporters/csv_exporter.py` to apply `escape_csv_row()` to each row before writing
- [ ] T033 [P] [US3] Import and apply `escape_csv_row` in `src/github_analyzer/exporters/jira_exporter.py`
- [ ] T034 [P] [US3] Import and apply `escape_csv_row` in `src/github_analyzer/exporters/jira_metrics_exporter.py`
- [ ] T035 [US3] Add tests for formula escaping in `tests/unit/exporters/test_csv_exporter.py`: test_escapes_formula_triggers, test_preserves_normal_data
- [ ] T036 [US3] Run `pytest tests/unit/exporters/test_csv_exporter.py -v` and verify formula injection tests pass

**Checkpoint**: User Story 3 complete. CSV exports are now protected against formula injection.

---

## Phase 6: User Story 4 - Security Response Headers Check (Priority: P2)

**Goal**: Log warnings when API responses have unexpected Content-Type headers

**Independent Test**: Mock an API response with `Content-Type: text/html` and verify `[SECURITY]` warning is logged

### Implementation for User Story 4

- [ ] T037 [US4] Import `validate_content_type` from `core.security` in `src/github_analyzer/api/client.py`
- [ ] T038 [US4] Add `validate_content_type()` call after successful API responses in `src/github_analyzer/api/client.py` `_make_request()` method
- [ ] T039 [P] [US4] Import and add `validate_content_type()` to `src/github_analyzer/api/jira_client.py` `_make_request()` method
- [ ] T040 [US4] Add tests for Content-Type validation in `tests/unit/api/test_client.py`: test_warns_on_unexpected_content_type
- [ ] T041 [US4] Run `pytest tests/unit/api/test_client.py -v` and verify header validation tests pass

**Checkpoint**: User Story 4 complete. Unexpected Content-Type headers now generate security warnings.

---

## Phase 7: User Story 5 - File Permission Checks (Priority: P3)

**Goal**: Warn users about overly permissive file permissions on sensitive files

**Independent Test**: Create a repos.txt with mode 644, run the tool, and verify `[SECURITY]` warning appears

### Implementation for User Story 5

- [ ] T042 [US5] Add `check_file_permissions` config option to `src/github_analyzer/config/settings.py` with default `True` and env var `GITHUB_ANALYZER_CHECK_PERMISSIONS`
- [ ] T043 [US5] Import `check_file_permissions`, `set_secure_permissions` from `core.security` in `src/github_analyzer/cli/main.py`
- [ ] T044 [US5] Call `check_file_permissions()` when reading repos.txt in `src/github_analyzer/cli/main.py`
- [ ] T045 [US5] Import `set_secure_permissions` in `src/github_analyzer/exporters/csv_exporter.py` and call after file creation in `_write_csv()`
- [ ] T046 [US5] Add tests for permission checks in `tests/unit/cli/test_main.py`: test_warns_on_permissive_repos_file
- [ ] T047 [US5] Run `pytest tests/unit/cli/test_main.py -v` and verify permission check tests pass

**Checkpoint**: User Story 5 complete. File permission warnings are now active on Unix systems.

---

## Phase 8: User Story 6 - Audit Logging (Priority: P3)

**Goal**: Provide optional verbose logging of API operations for debugging and security audits

**Independent Test**: Run with `--verbose` flag and verify `[API]` log entries appear (without token values)

### Implementation for User Story 6

- [ ] T048 [US6] Add `verbose` config option to `src/github_analyzer/config/settings.py` with default `False` and env var `GITHUB_ANALYZER_VERBOSE`
- [ ] T049 [US6] Add `--verbose` / `-v` CLI flag to argument parser in `src/github_analyzer/cli/main.py`
- [ ] T050 [US6] Import `log_api_request` from `core.security` in `src/github_analyzer/api/client.py`
- [ ] T051 [US6] Add conditional `log_api_request()` call in `src/github_analyzer/api/client.py` `_make_request()` when verbose mode enabled
- [ ] T052 [P] [US6] Add same verbose logging to `src/github_analyzer/api/jira_client.py` `_make_request()` method
- [ ] T053 [US6] Add tests for verbose logging in `tests/unit/api/test_client.py`: test_verbose_logs_api_requests, test_verbose_masks_tokens
- [ ] T054 [US6] Run `pytest tests/unit/api/test_client.py -v` and verify verbose logging tests pass

**Checkpoint**: User Story 6 complete. Verbose mode now logs API operations without credential leakage.

---

## Phase 9: User Story 7 - Timeout Warning (Priority: P3)

**Goal**: Warn users when configuring unusually long timeout values

**Independent Test**: Set timeout to 120s and verify `[SECURITY]` warning about timeout threshold appears

### Implementation for User Story 7

- [ ] T055 [US7] Add `timeout_warn_threshold` config option to `src/github_analyzer/config/settings.py` with default `60` and env var `GITHUB_ANALYZER_TIMEOUT_WARN_THRESHOLD`
- [ ] T056 [US7] Import `validate_timeout` from `core.security` in `src/github_analyzer/cli/main.py`
- [ ] T057 [US7] Call `validate_timeout()` at configuration load time in `src/github_analyzer/cli/main.py`
- [ ] T058 [US7] Add tests for timeout warning in `tests/unit/config/test_settings.py`: test_warns_on_high_timeout
- [ ] T059 [US7] Run `pytest tests/unit/config/test_settings.py -v` and verify timeout warning tests pass

**Checkpoint**: User Story 7 complete. Timeout configuration warnings are now active.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Integration testing, coverage verification, and final cleanup

- [ ] T060 [P] Create `tests/integration/test_security_features.py` with end-to-end security tests
- [ ] T061 [P] Add integration test: test_path_traversal_blocked_end_to_end in `tests/integration/test_security_features.py`
- [ ] T062 [P] Add integration test: test_csv_formula_injection_protected in `tests/integration/test_security_features.py`
- [ ] T063 [P] Add integration test: test_verbose_mode_works_end_to_end in `tests/integration/test_security_features.py`
- [ ] T064 Run `pytest tests/ -v` and verify all tests pass
- [ ] T065 Run `pytest --cov=src/github_analyzer --cov-report=term-missing` and verify ≥80% coverage on new code
- [ ] T066 Run `ruff check src/github_analyzer/` and fix any linting issues
- [ ] T067 Verify all security warnings use `[SECURITY]` prefix consistently
- [ ] T068 Run quickstart.md validation checklist

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001-T004) - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase (T020)
- **User Story 2 (Phase 4)**: Depends on Setup only (can run in parallel with Foundational)
- **User Story 3 (Phase 5)**: Depends on Foundational phase (T020)
- **User Story 4 (Phase 6)**: Depends on Foundational phase (T020)
- **User Story 5 (Phase 7)**: Depends on Foundational phase (T020)
- **User Story 6 (Phase 8)**: Depends on Foundational phase (T020)
- **User Story 7 (Phase 9)**: Depends on Foundational phase (T020)
- **Polish (Phase 10)**: Depends on all user stories being complete

### User Story Dependencies

```
                    ┌─────────────┐
                    │   Setup     │
                    │  (Phase 1)  │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               │
    ┌─────────────┐ ┌─────────────┐        │
    │ Foundational│ │   US2 (P1)  │        │
    │  (Phase 2)  │ │ Dep Pinning │        │
    └──────┬──────┘ └─────────────┘        │
           │                               │
    ┌──────┴──────────────────────────┐    │
    │  After Foundational Complete:   │    │
    │                                 │    │
    │  ┌───────┐ ┌───────┐ ┌───────┐ │    │
    │  │US1 P1 │ │US3 P2 │ │US4 P2 │ │    │
    │  │ Path  │ │ CSV   │ │Headers│ │    │
    │  └───────┘ └───────┘ └───────┘ │    │
    │                                 │    │
    │  ┌───────┐ ┌───────┐ ┌───────┐ │    │
    │  │US5 P3 │ │US6 P3 │ │US7 P3 │ │    │
    │  │ Perms │ │Verbose│ │Timeout│ │    │
    │  └───────┘ └───────┘ └───────┘ │    │
    │                                 │    │
    │  (All can run in parallel)     │    │
    └─────────────────────────────────┘    │
                    │                      │
                    ▼                      │
             ┌─────────────┐               │
             │   Polish    │◄──────────────┘
             │ (Phase 10)  │
             └─────────────┘
```

### Within Each User Story

- Models/utilities before services
- Services before integration
- Core implementation before tests (TDD: tests written first but run after impl)
- Story complete before marking checkpoint

### Parallel Opportunities

- **Setup**: T002, T003, T004 can run in parallel
- **Foundational**: T006-T012 can run in parallel, T015-T019 can run in parallel
- **US1**: T023, T024 can run in parallel
- **US3**: T033, T034 can run in parallel
- **US4**: T039 can run in parallel with T038
- **US6**: T052 can run in parallel with T051
- **Polish**: T060-T063 can all run in parallel

---

## Parallel Example: Foundational Phase

```bash
# Launch all security utility implementations in parallel:
Task: "Implement escape_csv_formula() in src/github_analyzer/core/security.py"
Task: "Implement escape_csv_row() in src/github_analyzer/core/security.py"
Task: "Implement check_file_permissions() in src/github_analyzer/core/security.py"
Task: "Implement set_secure_permissions() in src/github_analyzer/core/security.py"
Task: "Implement validate_content_type() in src/github_analyzer/core/security.py"
Task: "Implement log_api_request() in src/github_analyzer/core/security.py"
Task: "Implement validate_timeout() in src/github_analyzer/core/security.py"

# Then launch all unit tests in parallel:
Task: "Write unit tests for escape_csv_formula() in tests/unit/core/test_security.py"
Task: "Write unit tests for check_file_permissions() in tests/unit/core/test_security.py"
Task: "Write unit tests for validate_content_type() in tests/unit/core/test_security.py"
Task: "Write unit tests for log_api_request() in tests/unit/core/test_security.py"
Task: "Write unit tests for validate_timeout() in tests/unit/core/test_security.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1 (Path Validation)
4. Complete Phase 4: User Story 2 (Dependency Pinning)
5. **STOP and VALIDATE**: Run `pytest tests/` - should pass
6. Deploy/demo if ready - critical security features are in place

### Incremental Delivery

1. Setup + Foundational → Core security module ready
2. Add US1 (Path Validation) → Immediate security improvement
3. Add US2 (Dep Pinning) → Supply chain security
4. Add US3 (CSV Escaping) → Export safety
5. Add US4 (Header Check) → Defense-in-depth
6. Add US5-7 (P3 features) → Completeness
7. Polish → Production ready

### Parallel Team Strategy

With multiple developers after Foundational is complete:
- Developer A: User Stories 1, 5 (file/path related)
- Developer B: User Stories 3 (CSV/export related)
- Developer C: User Stories 4, 6, 7 (API/config related)
- Developer D: User Story 2 + Polish phase

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Tasks** | 68 |
| **Setup Phase** | 4 tasks |
| **Foundational Phase** | 16 tasks |
| **User Story 1 (P1)** | 6 tasks |
| **User Story 2 (P1)** | 4 tasks |
| **User Story 3 (P2)** | 6 tasks |
| **User Story 4 (P2)** | 5 tasks |
| **User Story 5 (P3)** | 6 tasks |
| **User Story 6 (P3)** | 7 tasks |
| **User Story 7 (P3)** | 5 tasks |
| **Polish Phase** | 9 tasks |
| **Parallel Opportunities** | 25+ tasks marked [P] |
| **MVP Scope** | US1 + US2 (10 tasks after foundational) |

---

## Notes

- [P] tasks = different files, no dependencies - can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- TDD approach: tests are written FIRST (T005-T010), implementation follows (T011-T018), per Constitution III
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All security warnings use `[SECURITY]` prefix for consistency
