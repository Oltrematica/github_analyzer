# Tasks: GitHub Repository Interactive Selection

**Input**: Design documents from `/specs/004-github-repo-selection/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Following constitution principle III (Test-Driven Development), tests are included for all user stories.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/github_analyzer/`, `tests/` at repository root
- Paths based on existing project structure from plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new project initialization needed - extending existing codebase

- [x] T001 Verify existing GitHubClient supports pagination in src/github_analyzer/api/client.py
- [x] T002 Verify existing TerminalOutput and error handling in src/github_analyzer/cli/output.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: API methods in GitHubClient that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational API Methods

- [x] T003 [P] Unit test for list_user_repos() in tests/unit/api/test_client.py
- [x] T004 [P] Unit test for list_org_repos() in tests/unit/api/test_client.py

### Implementation for Foundational API Methods

- [x] T005 Implement list_user_repos(affiliation="owner,collaborator") in src/github_analyzer/api/client.py
- [x] T006 Implement list_org_repos(org: str) in src/github_analyzer/api/client.py

**Checkpoint**: GitHubClient API methods ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Interactive Repository Selection Menu (Priority: P1) 🎯 MVP

**Goal**: Display interactive menu when repos.txt is missing/empty, offering options [A/S/O/L/Q]

**Independent Test**: Remove repos.txt, run `python github_analyzer.py --sources github`, verify menu appears with all options

### Tests for User Story 1

- [x] T007 [P] [US1] Test menu displays when repos.txt missing in tests/integration/test_interactive_selection.py
- [x] T008 [P] [US1] Test menu displays when repos.txt empty in tests/integration/test_interactive_selection.py
- [x] T009 [P] [US1] Test no menu when repos.txt has valid content in tests/integration/test_interactive_selection.py
- [x] T010 [P] [US1] Test EOF/Ctrl+C returns empty list in tests/integration/test_interactive_selection.py
- [x] T011 [P] [US1] Test non-interactive mode (--quiet) skips prompts in tests/integration/test_interactive_selection.py

### Implementation for User Story 1

- [x] T012 [US1] Create select_github_repos() function skeleton in src/github_analyzer/cli/main.py
- [x] T013 [US1] Implement load_github_repos_from_file() helper to read repos.txt in src/github_analyzer/cli/main.py
- [x] T014 [US1] Implement interactive menu display with [A/S/O/L/Q] options in src/github_analyzer/cli/main.py
- [x] T015 [US1] Implement EOF/KeyboardInterrupt handling (return empty list) in src/github_analyzer/cli/main.py
- [x] T016 [US1] Implement non-interactive mode check (interactive=False returns []) in src/github_analyzer/cli/main.py
- [x] T017 [US1] Integrate select_github_repos() call in main() before GitHub analysis in src/github_analyzer/cli/main.py

**Checkpoint**: User Story 1 complete - menu appears when repos.txt missing, file-based repos still work

---

## Phase 4: User Story 2 - List and Select Personal Repositories (Priority: P2)

**Goal**: Options [A] and [L] fetch and display user's personal repos using list_user_repos() API

**Independent Test**: Select option [A] or [L], verify all personal repos listed with owner/name format

### Tests for User Story 2

- [x] T018 [P] [US2] Test option [A] returns all user repos in tests/integration/test_interactive_selection.py
- [x] T019 [P] [US2] Test option [L] displays numbered list in tests/integration/test_interactive_selection.py
- [x] T020 [P] [US2] Test option [L] accepts "1,3,5" selection in tests/integration/test_interactive_selection.py
- [x] T021 [P] [US2] Test option [L] accepts "1-3" range selection in tests/integration/test_interactive_selection.py
- [x] T022 [P] [US2] Test option [L] accepts "all" selection in tests/integration/test_interactive_selection.py
- [x] T023 [P] [US2] Test pagination handles 100+ repos in tests/unit/api/test_client.py

### Implementation for User Story 2

- [x] T024 [P] [US2] Implement format_repo_list() helper in src/github_analyzer/cli/main.py
- [x] T025 [P] [US2] Implement parse_project_selection() helper (reuse pattern from Jira) in src/github_analyzer/cli/main.py
- [x] T026 [US2] Implement option [A] handler - call list_user_repos(), return all full_names in src/github_analyzer/cli/main.py
- [x] T027 [US2] Implement option [L] handler - display numbered list, parse selection in src/github_analyzer/cli/main.py
- [x] T028 [US2] Handle API errors and rate limits with user feedback in src/github_analyzer/cli/main.py

**Checkpoint**: User Story 2 complete - [A] and [L] options work, personal repos listed

---

## Phase 5: User Story 3 - List and Select Organization Repositories (Priority: P3)

**Goal**: Option [O] prompts for org name, fetches and displays org repos using list_org_repos() API

**Independent Test**: Select option [O], enter valid org name, verify org repos listed

### Tests for User Story 3

- [x] T029 [P] [US3] Test option [O] prompts for org name in tests/integration/test_interactive_selection.py
- [x] T030 [P] [US3] Test valid org name fetches repos in tests/integration/test_interactive_selection.py
- [x] T031 [P] [US3] Test invalid org name format shows error in tests/integration/test_interactive_selection.py
- [x] T032 [P] [US3] Test non-existent org shows error and retry option in tests/integration/test_interactive_selection.py
- [x] T033 [P] [US3] Test org with 100+ repos handles pagination in tests/unit/api/test_client.py

### Implementation for User Story 3

- [x] T034 [P] [US3] Implement validate_org_name() helper in src/github_analyzer/cli/main.py
- [x] T035 [US3] Implement option [O] handler - prompt org, validate, call list_org_repos() in src/github_analyzer/cli/main.py
- [x] T036 [US3] Display org repos list and accept selection (reuse format_repo_list) in src/github_analyzer/cli/main.py
- [x] T037 [US3] Handle org not found / permission denied errors in src/github_analyzer/cli/main.py

**Checkpoint**: User Story 3 complete - [O] option works for organization repos

---

## Phase 6: User Story 4 - Manual Repository Specification (Priority: P4)

**Goal**: Option [S] accepts comma-separated owner/repo input with validation

**Independent Test**: Select option [S], enter "owner/repo1, owner/repo2", verify those repos used

### Tests for User Story 4

- [x] T038 [P] [US4] Test option [S] prompts for manual input in tests/integration/test_interactive_selection.py
- [x] T039 [P] [US4] Test valid "owner/repo" format accepted in tests/integration/test_interactive_selection.py
- [x] T040 [P] [US4] Test invalid format shows warning in tests/integration/test_interactive_selection.py
- [x] T041 [P] [US4] Test mixed valid/invalid continues with valid only in tests/integration/test_interactive_selection.py
- [x] T042 [P] [US4] Test empty input prompts again in tests/integration/test_interactive_selection.py

### Implementation for User Story 4

- [x] T043 [P] [US4] Implement validate_repo_format() helper in src/github_analyzer/cli/main.py
- [x] T044 [US4] Implement option [S] handler - prompt, parse comma-separated, validate in src/github_analyzer/cli/main.py
- [x] T045 [US4] Show warnings for invalid repos, continue with valid ones in src/github_analyzer/cli/main.py
- [x] T046 [US4] Handle empty input with retry prompt in src/github_analyzer/cli/main.py

**Checkpoint**: User Story 4 complete - [S] option works for manual specification

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final integration, edge cases, and cleanup

- [x] T047 [P] Test option [Q] returns empty list in tests/integration/test_interactive_selection.py
- [x] T048 [P] Test invalid menu choice shows error and reprompts in tests/integration/test_interactive_selection.py
- [x] T049 Implement rate limit handling with wait time display to user in src/github_analyzer/cli/main.py (FR-008)
- [x] T050 Implement auth error handling (token missing/invalid scope) with clear message in src/github_analyzer/cli/main.py (Edge Case)
- [x] T051 Run full test suite to ensure no regressions: pytest tests/ -v (727 passed)
- [ ] T052 Validate quickstart.md scenarios work end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - verification only
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories (API methods required)
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (menu) is MVP and should complete first
  - US2-4 can proceed in parallel after US1 establishes select_github_repos() skeleton
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

```
Phase 1: Setup (verify existing)
    │
    ▼
Phase 2: Foundational (list_user_repos, list_org_repos)
    │
    ├───────────────┬───────────────┬───────────────┐
    ▼               ▼               ▼               ▼
Phase 3: US1    Phase 4: US2    Phase 5: US3    Phase 6: US4
(Menu MVP)      (Personal)      (Org)           (Manual)
    │               │               │               │
    └───────────────┴───────────────┴───────────────┘
                            │
                            ▼
                    Phase 7: Polish
```

### Within Each User Story

1. Tests MUST be written and FAIL before implementation
2. Helper functions before main handlers
3. Core implementation before integration
4. Story complete before moving to next priority

### Parallel Opportunities

**Phase 2 (Foundational)**:
- T003 and T004 (tests) can run in parallel
- T005 and T006 (implementation) are sequential (same file)

**Phase 3-6 (User Stories)**:
- All test tasks within a story can run in parallel
- Helper functions (format_repo_list, parse_repo_selection, validate_*) can run in parallel
- After US1 establishes skeleton, US2-4 can proceed in parallel

---

## Parallel Example: Foundational Phase

```bash
# Launch tests in parallel:
Task: T003 "Unit test for list_user_repos()"
Task: T004 "Unit test for list_org_repos()"

# Then implementation (sequential - same file):
Task: T005 "Implement list_user_repos()"
Task: T006 "Implement list_org_repos()"
```

## Parallel Example: User Story 2

```bash
# Launch all tests in parallel:
Task: T018-T023 (all test tasks)

# Launch helpers in parallel:
Task: T024 "format_repo_list()"
Task: T025 "parse_repo_selection()"

# Then handlers (sequential):
Task: T026 "option [A] handler"
Task: T027 "option [L] handler"
Task: T028 "error handling"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verification)
2. Complete Phase 2: Foundational (API methods)
3. Complete Phase 3: User Story 1 (interactive menu)
4. **STOP and VALIDATE**: Menu appears when repos.txt missing
5. Deploy/demo if ready - users can now see options

### Incremental Delivery

1. Complete Setup + Foundational → API ready
2. Add User Story 1 → Menu appears → (MVP!)
3. Add User Story 2 → [A] and [L] work → Personal repos
4. Add User Story 3 → [O] works → Org repos
5. Add User Story 4 → [S] works → Manual entry
6. Polish → Edge cases, rate limits → Production ready

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Tests follow existing patterns in tests/integration/test_interactive_selection.py
- Constitution requires TDD - all tests written before implementation
- Follow select_jira_projects pattern in cli/main.py for UX consistency (FR-003)
