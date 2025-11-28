# Tasks: Jira Integration & Multi-Platform Support

**Input**: Design documents from `/specs/002-jira-integration/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Constitution mandates TDD (Principle III). Tests included for all new modules.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/github_analyzer/`, `tests/` at repository root
- Based on existing modular architecture from 001-modular-refactor

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and Jira-specific exceptions

- [ ] T001 Add Jira-specific exceptions to src/github_analyzer/core/exceptions.py (JiraAPIError, JiraAuthenticationError, JiraPermissionError, JiraNotFoundError, JiraRateLimitError)
- [ ] T002 [P] Create test directory structure: tests/unit/api/, tests/unit/config/, tests/unit/exporters/, tests/integration/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Add DataSource enum to src/github_analyzer/config/settings.py (GITHUB, JIRA values)
- [ ] T004 Add JiraConfig dataclass to src/github_analyzer/config/settings.py (from_env, validate, __repr__ with masked token)
- [ ] T005 [P] Add validate_jira_url() function to src/github_analyzer/config/validation.py
- [ ] T006 [P] Add validate_project_key() function to src/github_analyzer/config/validation.py
- [ ] T006a [P] Add validate_iso8601_date() function to src/github_analyzer/config/validation.py (FR-021)
- [ ] T007 [P] Write unit tests for JiraConfig in tests/unit/config/test_jira_settings.py
- [ ] T008 [P] Write unit tests for Jira validation functions in tests/unit/config/test_jira_validation.py (include ISO 8601 date tests)

**Checkpoint**: Foundation ready - JiraConfig and validation available. User story implementation can now begin.

---

## Phase 3: User Story 1 - Jira Issue Extraction with Time Filter (Priority: P1) 🎯 MVP

**Goal**: Extract all Jira issues and comments for a specified time period using JQL queries with pagination

**Independent Test**: Configure Jira credentials, run extraction for 7 days, verify CSV contains issues with all core fields and comments

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Create test fixtures for Jira API responses in tests/fixtures/jira_responses.py
- [ ] T010 [P] [US1] Write unit tests for JiraClient in tests/unit/api/test_jira_client.py (test_connection, get_projects, search_issues, get_comments, pagination, rate_limit_retry)
- [ ] T011 [P] [US1] Write integration test for Jira extraction flow in tests/integration/test_jira_flow.py

### Implementation for User Story 1

- [ ] T012 [P] [US1] Create JiraProject dataclass in src/github_analyzer/api/jira_client.py
- [ ] T013 [P] [US1] Create JiraIssue dataclass in src/github_analyzer/api/jira_client.py
- [ ] T014 [P] [US1] Create JiraComment dataclass in src/github_analyzer/api/jira_client.py
- [ ] T015 [US1] Implement JiraClient.__init__() with config, session setup, and API version detection in src/github_analyzer/api/jira_client.py
- [ ] T016 [US1] Implement JiraClient._get_headers() with Basic Auth (base64 email:token) in src/github_analyzer/api/jira_client.py
- [ ] T017 [US1] Implement JiraClient._make_request() with retry logic and rate limit handling in src/github_analyzer/api/jira_client.py
- [ ] T018 [US1] Implement JiraClient.test_connection() using /rest/api/{version}/serverInfo in src/github_analyzer/api/jira_client.py
- [ ] T019 [US1] Implement JiraClient.get_projects() with pagination in src/github_analyzer/api/jira_client.py
- [ ] T020 [US1] Implement JiraClient.search_issues() with JQL time filter and pagination (yields JiraIssue) in src/github_analyzer/api/jira_client.py
- [ ] T021 [US1] Implement JiraClient.get_comments() with pagination in src/github_analyzer/api/jira_client.py
- [ ] T022 [US1] Implement ADF (Atlassian Document Format) to plain text conversion helper in src/github_analyzer/api/jira_client.py
- [ ] T023 [US1] Export JiraClient and models from src/github_analyzer/api/__init__.py
- [ ] T024 [US1] Run tests and verify all US1 tests pass

**Checkpoint**: JiraClient fully functional. Can extract issues and comments from any Jira instance.

---

## Phase 4: User Story 2 - Secure Jira Authentication (Priority: P2)

**Goal**: Secure credential handling via environment variables with no token exposure in logs/errors

**Independent Test**: Set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN; verify auth works; check no token in any output

### Tests for User Story 2

- [ ] T025 [P] [US2] Write unit tests for credential masking in tests/unit/config/test_jira_settings.py (repr, str, error messages)
- [ ] T026 [P] [US2] Write unit tests for missing credentials handling in tests/unit/config/test_jira_settings.py

### Implementation for User Story 2

- [ ] T027 [US2] Add mask_jira_token() helper to src/github_analyzer/core/exceptions.py (reuse pattern from mask_token)
- [ ] T028 [US2] Update JiraConfig.__repr__() to use masked token in src/github_analyzer/config/settings.py
- [ ] T029 [US2] Update JiraConfig.to_dict() to use masked token in src/github_analyzer/config/settings.py
- [ ] T030 [US2] Verify all JiraAPIError subclasses never include token in message in src/github_analyzer/core/exceptions.py
- [ ] T031 [US2] Implement JiraConfig.from_env() returning None when credentials incomplete in src/github_analyzer/config/settings.py
- [ ] T032 [US2] Run tests and verify all US2 tests pass

**Checkpoint**: Authentication secure. Credentials never exposed in any output.

---

## Phase 5: User Story 3 - Unified Multi-Platform Entrypoint (Priority: P3)

**Goal**: Rename entrypoint to dev_analyzer.py with --sources flag and backward compatibility wrapper

**Independent Test**: Run dev_analyzer.py with various --sources combinations; verify github_analyzer.py wrapper works

### Tests for User Story 3

- [ ] T033 [P] [US3] Write unit tests for CLI argument parsing (--sources flag) in tests/unit/cli/test_main_args.py
- [ ] T034 [P] [US3] Write integration test for multi-source extraction in tests/integration/test_multi_source.py
- [ ] T034a [P] [US3] Write integration test for interactive project selection (FR-009a) in tests/integration/test_interactive_selection.py

### Implementation for User Story 3

- [ ] T035 [US3] Add --sources argument to create_parser() in src/github_analyzer/cli/main.py (accepts: github, jira, github,jira)
- [ ] T036 [US3] Implement source auto-detection logic in src/github_analyzer/cli/main.py (detect available credentials)
- [ ] T037 [US3] Update run_extraction() to support DataSource list in src/github_analyzer/cli/main.py
- [ ] T038 [US3] Implement Jira extraction orchestration in main() in src/github_analyzer/cli/main.py
- [ ] T039 [US3] Implement interactive project selection when jira_projects.txt missing in src/github_analyzer/cli/main.py
- [ ] T040 [US3] Create dev_analyzer.py as primary entrypoint at repository root
- [ ] T041 [US3] Update github_analyzer.py as backward compatibility wrapper (imports from dev_analyzer.py)
- [ ] T042 [US3] Run tests and verify all US3 tests pass

**Checkpoint**: Multi-platform CLI ready. Both entrypoints work, auto-detection functional.

---

## Phase 6: User Story 4 - Jira Data Export (Priority: P4)

**Goal**: Export Jira issues and comments to CSV files following RFC 4180 standards

**Independent Test**: Extract Jira data, verify jira_issues_export.csv and jira_comments_export.csv have correct structure

### Tests for User Story 4

- [ ] T043 [P] [US4] Write unit tests for JiraExporter in tests/unit/exporters/test_jira_exporter.py (export_issues, export_comments, CSV escaping)

### Implementation for User Story 4

- [ ] T044 [P] [US4] Create JiraExporter class with ISSUE_COLUMNS and COMMENT_COLUMNS constants in src/github_analyzer/exporters/jira_exporter.py
- [ ] T045 [US4] Implement JiraExporter.__init__() with output_dir in src/github_analyzer/exporters/jira_exporter.py
- [ ] T046 [US4] Implement JiraExporter.export_issues() with streaming CSV write in src/github_analyzer/exporters/jira_exporter.py
- [ ] T047 [US4] Implement JiraExporter.export_comments() with streaming CSV write in src/github_analyzer/exporters/jira_exporter.py
- [ ] T048 [US4] Ensure RFC 4180 CSV escaping (quotes, newlines, commas) in src/github_analyzer/exporters/jira_exporter.py
- [ ] T049 [US4] Export JiraExporter from src/github_analyzer/exporters/__init__.py
- [ ] T050 [US4] Integrate JiraExporter into main extraction flow in src/github_analyzer/cli/main.py
- [ ] T051 [US4] Run tests and verify all US4 tests pass

**Checkpoint**: Export complete. CSV files generated with correct structure and escaping.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T052 [P] Create JiraIssueAnalyzer for project summaries in src/github_analyzer/analyzers/jira_issues.py
- [ ] T053 [P] Write unit tests for JiraIssueAnalyzer in tests/unit/analyzers/test_jira_issues.py
- [ ] T054 [P] Update src/github_analyzer/__init__.py to export new Jira modules
- [ ] T055 [P] Create example jira_projects.txt at repository root with documentation comments
- [ ] T056 Run full test suite: pytest tests/ -v --cov=src/github_analyzer
- [ ] T057 Run linter: ruff check src/github_analyzer/
- [ ] T058 Validate quickstart.md scenarios manually
- [ ] T059 Update README.md with Jira integration documentation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (P1): Core extraction - MVP, can start first
  - US2 (P2): Security - can run parallel to US1, enhances it
  - US3 (P3): CLI entrypoint - depends on US1 for Jira extraction to integrate
  - US4 (P4): Export - depends on US1 for data models, US3 for CLI integration
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

```
Phase 1: Setup
    ↓
Phase 2: Foundational (BLOCKS all)
    ↓
    ├── US1 (P1): Jira Extraction ─────────────────┐
    │       ↓                                      │
    │   US2 (P2): Secure Auth (can parallel US1)   │
    │                                              │
    ├── US3 (P3): Multi-Platform CLI ←─────────────┤
    │       ↓                                      │
    └── US4 (P4): CSV Export ←─────────────────────┘
            ↓
Phase 7: Polish
```

### Within Each User Story

1. Tests MUST be written and FAIL before implementation (TDD per constitution)
2. Models/dataclasses before client methods
3. Client methods before CLI integration
4. Core implementation before integration
5. Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks can run in parallel
- All Foundational tasks marked [P] can run in parallel
- Test fixtures (T009) can run parallel to unit test files (T010, T011)
- All dataclass definitions (T012, T013, T014) can run in parallel
- US1 and US2 can run in parallel (different focus areas)

---

## Parallel Example: User Story 1

```bash
# Launch all test files for User Story 1 together:
Task: "Create test fixtures for Jira API responses in tests/fixtures/jira_responses.py"
Task: "Write unit tests for JiraClient in tests/unit/api/test_jira_client.py"
Task: "Write integration test for Jira extraction flow in tests/integration/test_jira_flow.py"

# Launch all dataclass definitions together:
Task: "Create JiraProject dataclass in src/github_analyzer/api/jira_client.py"
Task: "Create JiraIssue dataclass in src/github_analyzer/api/jira_client.py"
Task: "Create JiraComment dataclass in src/github_analyzer/api/jira_client.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T008)
3. Complete Phase 3: User Story 1 (T009-T024)
4. **STOP and VALIDATE**: Test Jira extraction independently
5. Can extract issues and comments - core value delivered

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → **MVP: Jira extraction works!**
3. Add User Story 2 → Security hardened
4. Add User Story 3 → Multi-platform CLI ready
5. Add User Story 4 → Full export capability
6. Polish → Production ready

### Recommended Execution Order

For single developer:
```
T001 → T002 → T003 → T004 → [T005, T006, T007, T008 in parallel]
→ [T009, T010, T011 in parallel] → [T012, T013, T014 in parallel]
→ T015 → T016 → T017 → T018 → T019 → T020 → T021 → T022 → T023 → T024
→ Continue with US2, US3, US4 in order
```

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Total tasks: 61 (added T006a, T034a)
