# Tasks: Modular Architecture Refactoring

**Input**: Design documents from `/specs/001-modular-refactor/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are included as per FR-017 through FR-019 (pytest infrastructure requirement in spec).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/github_analyzer/`, `tests/` at repository root
- Paths follow plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create source directory structure: `src/github_analyzer/{api,analyzers,exporters,cli,config,core}/`
- [ ] T002 [P] Create all `__init__.py` files in src/github_analyzer/ and subdirectories
- [ ] T003 [P] Create test directory structure: `tests/{unit,integration,fixtures}/`
- [ ] T004 [P] Create all `__init__.py` files in tests/ and subdirectories
- [ ] T005 [P] Create requirements.txt with optional dependencies (requests)
- [ ] T006 [P] Create requirements-dev.txt with pytest, pytest-cov, ruff
- [ ] T007 [P] Create pyproject.toml with ruff configuration
- [ ] T008 [P] Create pytest.ini with test configuration and coverage settings

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T009 Implement custom exceptions in src/github_analyzer/core/exceptions.py (GitHubAnalyzerError, ConfigurationError, ValidationError, APIError, RateLimitError)
- [ ] T010 [P] Create test fixtures directory structure: tests/fixtures/api_responses/, tests/fixtures/sample_data/
- [ ] T011 [P] Create sample API response fixtures in tests/fixtures/api_responses/ (commits.json, prs.json, issues.json)
- [ ] T012 [P] Create sample repos.txt fixture in tests/fixtures/sample_data/repos.txt
- [ ] T013 Create conftest.py with shared pytest fixtures in tests/conftest.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Secure Token Configuration (Priority: P1) 🎯 MVP

**Goal**: Configure GitHub token securely via environment variables, never expose in logs/errors

**Independent Test**: Set `GITHUB_TOKEN` env var and verify tool authenticates without prompting

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T014 [P] [US1] Unit test for AnalyzerConfig.from_env() in tests/unit/config/test_settings.py
- [ ] T015 [P] [US1] Unit test for token format validation (including whitespace stripping) in tests/unit/config/test_settings.py
- [ ] T016 [P] [US1] Unit test for missing token error in tests/unit/config/test_settings.py
- [ ] T017 [P] [US1] Unit test verifying token never appears in exception messages in tests/unit/config/test_settings.py

### Implementation for User Story 1

- [ ] T018 [US1] Implement AnalyzerConfig dataclass in src/github_analyzer/config/settings.py
- [ ] T019 [US1] Implement AnalyzerConfig.from_env() classmethod in src/github_analyzer/config/settings.py
- [ ] T020 [US1] Implement validate_token_format() function in src/github_analyzer/config/validation.py
- [ ] T021 [US1] Implement AnalyzerConfig.validate() method in src/github_analyzer/config/settings.py
- [ ] T022 [US1] Add token masking utility in src/github_analyzer/core/exceptions.py (ensure no token in error messages)
- [ ] T023 [US1] Export public interfaces in src/github_analyzer/config/__init__.py

**Checkpoint**: Token configuration works securely via GITHUB_TOKEN env var

---

## Phase 4: User Story 2 - Validated Repository Input (Priority: P2)

**Goal**: Validate repository names/URLs before API calls, reject injection attempts

**Independent Test**: Provide valid/invalid repo formats, verify validation before any API calls

### Tests for User Story 2

- [ ] T024 [P] [US2] Unit test for Repository.from_string() with valid inputs in tests/unit/config/test_validation.py
- [ ] T025 [P] [US2] Unit test for Repository.from_string() with URL inputs (including http→https normalization) in tests/unit/config/test_validation.py
- [ ] T026 [P] [US2] Unit test for Repository.from_string() rejecting invalid chars in tests/unit/config/test_validation.py
- [ ] T027 [P] [US2] Unit test for Repository.from_string() rejecting injection attempts in tests/unit/config/test_validation.py
- [ ] T028 [P] [US2] Unit test for load_repositories() with valid file in tests/unit/config/test_validation.py
- [ ] T029 [P] [US2] Unit test for load_repositories() deduplication in tests/unit/config/test_validation.py
- [ ] T030 [P] [US2] Unit test for load_repositories() with missing file in tests/unit/config/test_validation.py

### Implementation for User Story 2

- [ ] T031 [US2] Implement Repository dataclass in src/github_analyzer/config/validation.py
- [ ] T032 [US2] Implement Repository.from_string() factory method in src/github_analyzer/config/validation.py
- [ ] T033 [US2] Implement URL normalization in Repository.from_string() in src/github_analyzer/config/validation.py
- [ ] T034 [US2] Implement injection character validation in src/github_analyzer/config/validation.py
- [ ] T035 [US2] Implement load_repositories() function in src/github_analyzer/config/validation.py
- [ ] T036 [US2] Implement deduplication with warning in load_repositories() in src/github_analyzer/config/validation.py
- [ ] T037 [US2] Update config/__init__.py exports in src/github_analyzer/config/__init__.py

**Checkpoint**: Repository input validation works, rejects malformed/dangerous inputs

---

## Phase 5: User Story 3 - Modular Code Organization (Priority: P3)

**Goal**: Organize codebase into separate, independently testable modules

**Independent Test**: Import individual modules in isolation, verify no circular dependencies

### Tests for User Story 3

- [ ] T038 [P] [US3] Unit test for GitHubClient initialization in tests/unit/api/test_client.py
- [ ] T039 [P] [US3] Unit test for GitHubClient.get() with mocked response in tests/unit/api/test_client.py
- [ ] T040 [P] [US3] Unit test for GitHubClient.paginate() in tests/unit/api/test_client.py
- [ ] T041 [P] [US3] Unit test for Commit model in tests/unit/api/test_models.py
- [ ] T042 [P] [US3] Unit test for PullRequest model in tests/unit/api/test_models.py
- [ ] T043 [P] [US3] Unit test for Issue model in tests/unit/api/test_models.py
- [ ] T044 [P] [US3] Unit test for CSVExporter in tests/unit/exporters/test_csv_exporter.py
- [ ] T045 [P] [US3] Unit test for CommitAnalyzer in tests/unit/analyzers/test_commits.py
- [ ] T046 [P] [US3] Unit test for calculate_quality_metrics() in tests/unit/analyzers/test_quality.py
- [ ] T047 [P] [US3] Unit test for ContributorTracker in tests/unit/analyzers/test_productivity.py

### Implementation for User Story 3

#### API Module

- [ ] T048 [P] [US3] Implement Commit dataclass in src/github_analyzer/api/models.py
- [ ] T049 [P] [US3] Implement PullRequest dataclass in src/github_analyzer/api/models.py
- [ ] T050 [P] [US3] Implement Issue dataclass in src/github_analyzer/api/models.py
- [ ] T051 [P] [US3] Implement RepositoryStats dataclass in src/github_analyzer/api/models.py
- [ ] T052 [P] [US3] Implement QualityMetrics dataclass in src/github_analyzer/api/models.py
- [ ] T053 [P] [US3] Implement ContributorStats dataclass in src/github_analyzer/api/models.py
- [ ] T054 [P] [US3] Implement ProductivityAnalysis dataclass in src/github_analyzer/api/models.py
- [ ] T055 [US3] Implement GitHubClient class in src/github_analyzer/api/client.py
- [ ] T056 [US3] Implement GitHubClient.get() method with requests/urllib fallback in src/github_analyzer/api/client.py
- [ ] T057 [US3] Implement GitHubClient.paginate() method in src/github_analyzer/api/client.py
- [ ] T058 [US3] Implement rate limit tracking in GitHubClient in src/github_analyzer/api/client.py
- [ ] T058a [US3] Implement exponential backoff retry logic for transient failures in src/github_analyzer/api/client.py
- [ ] T058b [US3] Implement API response validation for missing/null fields in src/github_analyzer/api/client.py
- [ ] T059 [US3] Export public interfaces in src/github_analyzer/api/__init__.py

#### Analyzers Module

- [ ] T060 [P] [US3] Implement CommitAnalyzer class in src/github_analyzer/analyzers/commits.py
- [ ] T061 [P] [US3] Implement PullRequestAnalyzer class in src/github_analyzer/analyzers/pull_requests.py
- [ ] T062 [P] [US3] Implement IssueAnalyzer class in src/github_analyzer/analyzers/issues.py
- [ ] T063 [P] [US3] Implement calculate_quality_metrics() in src/github_analyzer/analyzers/quality.py
- [ ] T064 [P] [US3] Implement ContributorTracker class in src/github_analyzer/analyzers/productivity.py
- [ ] T065 [US3] Export public interfaces in src/github_analyzer/analyzers/__init__.py

#### Exporters Module

- [ ] T066 [US3] Implement CSVExporter class in src/github_analyzer/exporters/csv_exporter.py
- [ ] T067 [US3] Implement all export methods (commits, prs, issues, stats, quality, productivity, contributors) in src/github_analyzer/exporters/csv_exporter.py
- [ ] T068 [US3] Export public interfaces in src/github_analyzer/exporters/__init__.py

#### CLI Module

- [ ] T069 [P] [US3] Implement Colors class in src/github_analyzer/cli/output.py
- [ ] T070 [P] [US3] Implement TerminalOutput class in src/github_analyzer/cli/output.py
- [ ] T071 [US3] Implement GitHubAnalyzer orchestrator class in src/github_analyzer/cli/main.py
- [ ] T072 [US3] Implement main() entry point in src/github_analyzer/cli/main.py
- [ ] T073 [US3] Export public interfaces in src/github_analyzer/cli/__init__.py

#### Integration

- [ ] T074 [US3] Update root github_analyzer.py to import from src/github_analyzer/cli/main.py
- [ ] T075 [US3] Export top-level interfaces in src/github_analyzer/__init__.py
- [ ] T076 [US3] Integration test for full analyzer flow in tests/integration/test_analyzer_flow.py

**Checkpoint**: All modules work independently, can be imported in isolation

---

## Phase 6: User Story 4 - Automated Testing Infrastructure (Priority: P4)

**Goal**: Test infrastructure in place with pytest, coverage reporting, all tests pass without network

**Independent Test**: Run pytest and see test discovery, execution, coverage report

### Tests for User Story 4

- [ ] T077 [P] [US4] Verify test discovery works by running pytest --collect-only
- [ ] T078 [P] [US4] Verify coverage reporting works with pytest --cov

### Implementation for User Story 4

- [ ] T079 [US4] Ensure all fixtures are properly set up for offline testing in tests/conftest.py
- [ ] T080 [US4] Add mock GitHub API responses for all API endpoints in tests/fixtures/api_responses/
- [ ] T080a [US4] Test that analyzer works without requests library (stdlib urllib only) in tests/integration/test_analyzer_flow.py
- [ ] T081 [US4] Verify all tests pass without GITHUB_TOKEN set
- [ ] T082 [US4] Verify coverage meets 80% threshold

**Checkpoint**: Full test suite runs offline, coverage report generated

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and validation

- [ ] T083 [P] Add type hints to all public interfaces across all modules
- [ ] T084 [P] Add Google-style docstrings to all public functions and classes
- [ ] T085 [P] Run ruff linter and fix all issues
- [ ] T086 Verify no module exceeds 300 lines (excluding docstrings/comments)
- [ ] T087 Verify no circular imports by importing each module individually
- [ ] T088 Verify backward compatibility: python github_analyzer.py works identically
- [ ] T089 Run quickstart.md validation steps manually
- [ ] T090 Final test run: pytest --cov with all tests passing

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (P1): Can start after Phase 2
  - US2 (P2): Can start after Phase 2 (parallel with US1)
  - US3 (P3): Depends on US1 and US2 for config/validation modules
  - US4 (P4): Can start after Phase 2 (testing infra), completes after US3
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies - implements config/token handling
- **User Story 2 (P2)**: No dependencies - implements validation (can run parallel with US1)
- **User Story 3 (P3)**: Depends on US1 (config) and US2 (validation) - needs their exported interfaces before API client and analyzers can use them
- **User Story 4 (P4)**: Infrastructure tasks (T077-T078) can start after Phase 2; validation tasks (T079-T082) must wait for US3 completion

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

Phase 1 (all parallel):
```bash
T002, T003, T004, T005, T006, T007, T008
```

Phase 2:
```bash
T010, T011, T012 (parallel)
```

US1 Tests (parallel):
```bash
T014, T015, T016, T017
```

US2 Tests (parallel):
```bash
T024, T025, T026, T027, T028, T029, T030
```

US3 Tests (parallel):
```bash
T038, T039, T040, T041, T042, T043, T044, T045, T046, T047
```

US3 Models (parallel):
```bash
T048, T049, T050, T051, T052, T053, T054
```

US3 Analyzers (parallel):
```bash
T060, T061, T062, T063, T064
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1 (Secure Token)
4. **STOP and VALIDATE**: Verify token config works securely
5. Can demo secure token handling

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Token) → Test independently → Secure config working
3. Add US2 (Validation) → Test independently → Input validation working
4. Add US3 (Modules) → Test independently → Full modular architecture
5. Add US4 (Tests) → Verify coverage → Complete test infrastructure
6. Polish → Final validation → Production ready

### Single Developer Strategy

Execute in strict phase order:
1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Summary

| Phase | Tasks | Parallel | Description |
|-------|-------|----------|-------------|
| Setup | 8 | 7 | Project structure initialization |
| Foundational | 5 | 3 | Core infrastructure |
| US1 (P1) | 10 | 4 | Secure token configuration |
| US2 (P2) | 14 | 7 | Repository input validation |
| US3 (P3) | 41 | 25 | Modular code organization (+2: retry, validation) |
| US4 (P4) | 7 | 2 | Testing infrastructure (+1: stdlib test) |
| Polish | 8 | 3 | Final validation |
| **Total** | **93** | **51** | |
