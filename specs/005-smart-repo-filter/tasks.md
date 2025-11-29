# Tasks: Smart Repository Filtering

**Input**: Design documents from `/specs/005-smart-repo-filter/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Following constitution principle III (Test-Driven Development), tests are included for all user stories.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/github_analyzer/`, `tests/` at repository root
- Paths based on existing project structure from plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new project initialization needed - extending existing codebase

- [ ] T001 Verify existing GitHubClient supports search endpoint pattern in src/github_analyzer/api/client.py
- [ ] T002 Verify select_github_repos() skeleton from Feature 004 in src/github_analyzer/cli/main.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core API method and helper functions that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational Methods

- [ ] T003 [P] Unit test for search_repos() in tests/unit/api/test_client.py
- [ ] T004 [P] Unit test for get_cutoff_date() helper in tests/unit/cli/test_main.py
- [ ] T005 [P] Unit test for filter_by_activity() in tests/unit/cli/test_main.py

### Implementation for Foundational Methods

- [ ] T006 Implement search_repos(query: str, per_page: int = 100) in src/github_analyzer/api/client.py
- [ ] T007 [P] Implement get_cutoff_date(days: int) -> str helper in src/github_analyzer/cli/main.py
- [ ] T008 [P] Implement filter_by_activity(repos: list, days: int) in src/github_analyzer/cli/main.py
- [ ] T009 Implement display_activity_stats(total: int, active: int, days: int) in src/github_analyzer/cli/main.py

**Checkpoint**: GitHubClient.search_repos() and filtering helpers ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Filter Repositories by Recent Activity (Priority: P1) 🎯 MVP

**Goal**: Display activity statistics when listing personal repositories via [A] or [L] options

**Independent Test**: Select option [L] or [A], verify system shows "135 repos found, 28 with activity in last 30 days" and filters to active repos only

### Tests for User Story 1

- [ ] T010 [P] [US1] Test [A] option displays activity stats in tests/integration/test_smart_filter.py
- [ ] T011 [P] [US1] Test [L] option displays activity stats in tests/integration/test_smart_filter.py
- [ ] T012 [P] [US1] Test filter correctly identifies active repos by pushed_at (verify SC-003 accuracy) in tests/integration/test_smart_filter.py
- [ ] T013 [P] [US1] Test stats format matches FR-007 "N repos found, M with activity" in tests/integration/test_smart_filter.py
- [ ] T014 [P] [US1] Test uses --days parameter for cutoff date (FR-010) in tests/integration/test_smart_filter.py

### Implementation for User Story 1

- [ ] T015 [US1] Modify _handle_option_a() to call filter_by_activity() in src/github_analyzer/cli/main.py
- [ ] T016 [US1] Modify _handle_option_l() to call filter_by_activity() in src/github_analyzer/cli/main.py
- [ ] T017 [US1] Add display_activity_stats() call after repo fetch in both handlers in src/github_analyzer/cli/main.py
- [ ] T018 [US1] Add confirmation prompt "Proceed with N active repositories? [Y/n/all]" in src/github_analyzer/cli/main.py
- [ ] T019 [US1] Pass days parameter from config to filtering functions in src/github_analyzer/cli/main.py

**Checkpoint**: User Story 1 complete - [A] and [L] show activity stats and filter by default

---

## Phase 4: User Story 2 - Organization Repository Filtering (Priority: P2)

**Goal**: Use GitHub Search API for efficient org repo filtering via [O] option

**Independent Test**: Select option [O], enter organization name, verify stats show for that organization

### Tests for User Story 2

- [ ] T020 [P] [US2] Test [O] option uses Search API for org repos in tests/integration/test_smart_filter.py
- [ ] T021 [P] [US2] Test org search query format "org:NAME+pushed:>DATE" in tests/unit/api/test_client.py
- [ ] T022 [P] [US2] Test org stats display "50 org repos found, 12 with activity" in tests/integration/test_smart_filter.py
- [ ] T023 [P] [US2] Test Search API pagination for large orgs (100+ active) in tests/unit/api/test_client.py

### Implementation for User Story 2

- [ ] T024 [US2] Implement search_active_org_repos(org: str, days: int) in src/github_analyzer/api/client.py
- [ ] T025 [US2] Modify _handle_option_o() to use search_active_org_repos() in src/github_analyzer/cli/main.py
- [ ] T026 [US2] Fetch total org count via list_org_repos() for stats display in src/github_analyzer/cli/main.py
- [ ] T027 [US2] Add confirmation prompt for org repos matching [A]/[L] pattern in src/github_analyzer/cli/main.py

**Checkpoint**: User Story 2 complete - [O] option uses Search API for efficient filtering

---

## Phase 5: User Story 3 - Override Activity Filter (Priority: P3)

**Goal**: Allow users to include inactive repositories when needed

**Independent Test**: User can respond "all" to include inactive repos, or use [S] without filter

### Tests for User Story 3

- [ ] T028 [P] [US3] Test "all" response includes inactive repos in tests/integration/test_smart_filter.py
- [ ] T029 [P] [US3] Test [S] option skips activity filter (FR-005) in tests/integration/test_smart_filter.py
- [ ] T030 [P] [US3] Test filter toggle state preserved during selection in tests/integration/test_smart_filter.py

### Implementation for User Story 3

- [ ] T031 [US3] Handle "all" response to bypass filter in confirmation prompt in src/github_analyzer/cli/main.py
- [ ] T032 [US3] Ensure [S] handler never applies activity filter in src/github_analyzer/cli/main.py
- [ ] T033 [US3] Add "include inactive" option to zero-results warning (FR-009) in src/github_analyzer/cli/main.py

**Checkpoint**: User Story 3 complete - users can override filter when needed

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, edge cases, and final validation

### Edge Cases (from spec.md)

- [ ] T034 [P] Test zero active repos shows warning and options (FR-009) in tests/integration/test_smart_filter.py
- [ ] T035 [P] Test Search API rate limit fallback to unfiltered (FR-008) in tests/integration/test_smart_filter.py
- [ ] T036 [P] Test incomplete_results flag shows warning in tests/integration/test_smart_filter.py

### Implementation for Edge Cases

- [ ] T037 Implement rate limit fallback with warning message (FR-008) in src/github_analyzer/cli/main.py
- [ ] T038 Implement zero-results warning with timeframe adjustment option in src/github_analyzer/cli/main.py
- [ ] T039 Handle incomplete_results flag from Search API with warning in src/github_analyzer/cli/main.py

### Final Validation

- [ ] T040 Run full test suite to ensure no regressions: pytest tests/ -v
- [ ] T041 Validate quickstart.md scenarios work end-to-end (verify SC-001: stats display <5 seconds)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - verification only
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - US1 is MVP and should complete first
  - US2-3 can proceed in parallel after US1 establishes pattern
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

```
Phase 1: Setup (verify existing)
    │
    ▼
Phase 2: Foundational (search_repos, filter_by_activity, helpers)
    │
    ├───────────────┬───────────────┐
    ▼               ▼               ▼
Phase 3: US1    Phase 4: US2    Phase 5: US3
(Personal)      (Org)           (Override)
    │               │               │
    └───────────────┴───────────────┘
                    │
                    ▼
            Phase 6: Polish
```

### Within Each User Story

1. Tests MUST be written and FAIL before implementation
2. Helper functions before main handlers
3. Core implementation before integration
4. Story complete before moving to next priority

### Parallel Opportunities

**Phase 2 (Foundational)**:
- T003, T004, T005 (tests) can run in parallel
- T007, T008 (helpers) can run in parallel (different functions)

**Phase 3 (User Story 1)**:
- T010-T014 (all test tasks) can run in parallel
- T015, T016 can run in parallel (different option handlers)

**Phase 4 (User Story 2)**:
- T020-T023 (all test tasks) can run in parallel

**Phase 5 (User Story 3)**:
- T028-T030 (all test tasks) can run in parallel

---

## Parallel Example: Foundational Phase

```bash
# Launch tests in parallel:
Task: T003 "Unit test for search_repos() in tests/unit/api/test_client.py"
Task: T004 "Unit test for get_cutoff_date() in tests/unit/cli/test_main.py"
Task: T005 "Unit test for filter_by_activity() in tests/unit/cli/test_main.py"

# Then implementation (helpers in parallel, then API):
Task: T007 "get_cutoff_date() helper"
Task: T008 "filter_by_activity() helper"
# After helpers:
Task: T006 "search_repos() API method"
Task: T009 "display_activity_stats()"
```

## Parallel Example: User Story 1

```bash
# Launch all tests in parallel:
Task: T010-T014 (all test tasks for US1)

# Then implementation (handlers can be parallel):
Task: T015 "_handle_option_a() modification"
Task: T016 "_handle_option_l() modification"
# After handlers:
Task: T017 "Add display_activity_stats() calls"
Task: T018 "Add confirmation prompt"
Task: T019 "Pass days parameter"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verification)
2. Complete Phase 2: Foundational (API + helpers)
3. Complete Phase 3: User Story 1 (personal repos filtering)
4. **STOP and VALIDATE**: Stats appear for [A] and [L] options
5. Deploy/demo if ready - users can now see activity filtering

### Incremental Delivery

1. Complete Setup + Foundational → API ready
2. Add User Story 1 → [A] and [L] filter → (MVP!)
3. Add User Story 2 → [O] uses Search API → Org filtering
4. Add User Story 3 → Override option → Full control
5. Polish → Edge cases, rate limits → Production ready

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Tests follow existing patterns in tests/integration/test_smart_filter.py (new file)
- Constitution requires TDD - all tests written before implementation
- Extends Feature 004 pattern - reuse select_github_repos() structure
- Search API has separate rate limit (30/min) from core API (5000/hour)
