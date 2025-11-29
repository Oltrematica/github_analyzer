# Tasks: Jira Quality Metrics Export

**Input**: Design documents from `/specs/003-jira-quality-metrics/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: TDD approach per constitution principle III - tests written before implementation.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US5)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/github_analyzer/`, `tests/` at repository root
- Paths follow existing modular structure per plan.md

---

## Phase 1: Setup

**Purpose**: Configuration constants and test fixtures

- [x] T001 Add metrics configuration constants to src/github_analyzer/config/settings.py (QUALITY_WEIGHT_LENGTH=40, QUALITY_WEIGHT_AC=40, QUALITY_WEIGHT_FORMAT=20, QUALITY_LENGTH_THRESHOLD=100, CROSS_TEAM_SCALE, AC_PATTERNS, DONE_STATUSES)
- [x] T002 [P] Add metrics test fixtures to tests/fixtures/jira_responses.py (sample issues with various descriptions, comments, resolution dates for testing all metrics)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core dataclasses and metrics calculator that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Create IssueMetrics dataclass in src/github_analyzer/analyzers/jira_metrics.py per data-model.md
- [x] T004 Create ProjectMetrics dataclass in src/github_analyzer/analyzers/jira_metrics.py per data-model.md
- [x] T005 [P] Create PersonMetrics dataclass in src/github_analyzer/analyzers/jira_metrics.py per data-model.md
- [x] T006 [P] Create TypeMetrics dataclass in src/github_analyzer/analyzers/jira_metrics.py per data-model.md

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Individual Issue Quality Assessment (Priority: P1) 🎯 MVP

**Goal**: Calculate and export 10 quality metrics for each individual issue in jira_issues_export.csv

**Independent Test**: Export issues and verify CSV contains all new metric columns with correct values

### Tests for User Story 1

- [x] T007 [P] [US1] Write unit tests for cycle_time calculation in tests/unit/analyzers/test_jira_metrics.py (resolved issue, open issue, negative time edge case)
- [x] T008 [P] [US1] Write unit tests for aging calculation in tests/unit/analyzers/test_jira_metrics.py (open issue only, resolved returns None)
- [x] T009 [P] [US1] Write unit tests for description_quality_score in tests/unit/analyzers/test_jira_metrics.py (empty, short, long, with AC, with formatting)
- [x] T010 [P] [US1] Write unit tests for acceptance_criteria detection in tests/unit/analyzers/test_jira_metrics.py (Given/When/Then, AC:, checkbox, none)
- [x] T011 [P] [US1] Write unit tests for comments_count and silent_issue in tests/unit/analyzers/test_jira_metrics.py
- [x] T012 [P] [US1] Write unit tests for same_day_resolution in tests/unit/analyzers/test_jira_metrics.py
- [x] T013 [P] [US1] Write unit tests for cross_team_score calculation in tests/unit/analyzers/test_jira_metrics.py (1-5+ authors, diminishing scale per FR-009)
- [x] T014 [P] [US1] Write unit tests for comment_velocity_hours in tests/unit/analyzers/test_jira_metrics.py (FR-006)
- [x] T015 [P] [US1] Write unit test for extended CSV export columns in tests/unit/exporters/test_jira_exporter.py

### Implementation for User Story 1

- [x] T016 [US1] Implement calculate_cycle_time() function in src/github_analyzer/analyzers/jira_metrics.py (FR-001)
- [x] T017 [US1] Implement calculate_aging() function in src/github_analyzer/analyzers/jira_metrics.py (FR-002)
- [x] T018 [US1] Implement detect_acceptance_criteria() function in src/github_analyzer/analyzers/jira_metrics.py (FR-005)
- [x] T019 [US1] Implement calculate_description_quality() function in src/github_analyzer/analyzers/jira_metrics.py (FR-004)
- [x] T020 [US1] Implement calculate_comment_metrics() function in src/github_analyzer/analyzers/jira_metrics.py (FR-003, FR-006, FR-007)
- [x] T021 [US1] Implement calculate_same_day_resolution() function in src/github_analyzer/analyzers/jira_metrics.py (FR-008)
- [x] T022 [US1] Implement calculate_cross_team_score() function in src/github_analyzer/analyzers/jira_metrics.py (FR-009)
- [x] T023 [US1] Implement MetricsCalculator.calculate_issue_metrics() method combining all individual metrics in src/github_analyzer/analyzers/jira_metrics.py
- [x] T024 [US1] Extend ISSUE_COLUMNS tuple in src/github_analyzer/exporters/jira_exporter.py with 10 new metric columns per contracts/csv-schemas.md
- [x] T025 [US1] Modify JiraExporter.export_issues() in src/github_analyzer/exporters/jira_exporter.py to accept IssueMetrics and write extended columns

**Checkpoint**: User Story 1 complete - issues export with all individual metrics

---

## Phase 4: User Story 2 - Project-Level Aggregated Metrics (Priority: P2)

**Goal**: Generate jira_project_metrics.csv with aggregated metrics per project

**Independent Test**: Export project summary and verify CSV contains avg/median cycle time, bug ratio, resolution rates

### Tests for User Story 2

- [x] T026 [P] [US2] Write unit tests for project aggregation in tests/unit/analyzers/test_jira_metrics.py (avg, median cycle time, bug ratio, silent ratio)
- [x] T027 [P] [US2] Write unit tests for project metrics CSV export in tests/unit/exporters/test_jira_metrics_exporter.py

### Implementation for User Story 2

- [x] T028 [US2] Implement MetricsCalculator.aggregate_project_metrics() in src/github_analyzer/analyzers/jira_metrics.py (FR-010 to FR-014)
- [x] T029 [US2] Create JiraMetricsExporter class in src/github_analyzer/exporters/jira_metrics_exporter.py
- [x] T030 [US2] Implement JiraMetricsExporter.export_project_metrics() in src/github_analyzer/exporters/jira_metrics_exporter.py per contracts/csv-schemas.md

**Checkpoint**: User Story 2 complete - project summary CSV available

---

## Phase 5: User Story 3 - Team Member Performance Metrics (Priority: P2)

**Goal**: Generate jira_person_metrics.csv with WIP, cycle time, and counts per assignee

**Independent Test**: Export person summary and verify CSV contains correct WIP and performance metrics per assignee

### Tests for User Story 3

- [x] T031 [P] [US3] Write unit tests for person aggregation in tests/unit/analyzers/test_jira_metrics.py (WIP count, resolved count, avg cycle time, explicitly test unassigned issues are excluded per edge case)
- [x] T032 [P] [US3] Write unit tests for person metrics CSV export in tests/unit/exporters/test_jira_metrics_exporter.py

### Implementation for User Story 3

- [x] T033 [US3] Implement MetricsCalculator.aggregate_person_metrics() in src/github_analyzer/analyzers/jira_metrics.py (FR-015 to FR-018)
- [x] T034 [US3] Implement JiraMetricsExporter.export_person_metrics() in src/github_analyzer/exporters/jira_metrics_exporter.py per contracts/csv-schemas.md

**Checkpoint**: User Story 3 complete - person summary CSV available

---

## Phase 6: User Story 4 - Issue Type Performance Analysis (Priority: P3)

**Goal**: Generate jira_type_metrics.csv with cycle time and counts per issue type

**Independent Test**: Export type summary and verify CSV shows distinct metrics for Bug, Story, Task

### Tests for User Story 4

- [x] T035 [P] [US4] Write unit tests for type aggregation in tests/unit/analyzers/test_jira_metrics.py (per-type counts, avg cycle time, bug_resolution_time_avg only for Bug)
- [x] T036 [P] [US4] Write unit tests for type metrics CSV export in tests/unit/exporters/test_jira_metrics_exporter.py

### Implementation for User Story 4

- [x] T037 [US4] Implement MetricsCalculator.aggregate_type_metrics() in src/github_analyzer/analyzers/jira_metrics.py (FR-019 to FR-021)
- [x] T038 [US4] Implement JiraMetricsExporter.export_type_metrics() in src/github_analyzer/exporters/jira_metrics_exporter.py per contracts/csv-schemas.md

**Checkpoint**: User Story 4 complete - type summary CSV available

---

## Phase 7: User Story 5 - Reopen Tracking and Aggregation Enhancement (Priority: P3)

**Goal**: Add reopen_count per issue via changelog API, and include reopen_rate_percent in project aggregation (FR-022, FR-023)

**Independent Test**: Export issues with reopen_count populated (best-effort), verify project CSV includes reopen_rate_percent

### Tests for User Story 5

- [x] T039 [P] [US5] Write unit tests for reopen detection in tests/unit/analyzers/test_jira_metrics.py (mock changelog response, status transitions from Done to non-Done)
- [x] T040 [P] [US5] Write unit tests for changelog API error handling in tests/unit/api/test_jira_client.py (mock 403/404 responses, verify graceful degradation returns 0)
- [x] T041 [P] [US5] Write unit tests for reopen_rate_percent in project aggregation in tests/unit/analyzers/test_jira_metrics.py

### Implementation for User Story 5

- [x] T042 [US5] Add get_issue_changelog() method to JiraClient in src/github_analyzer/api/jira_client.py (best-effort, graceful 403/404 handling per spec assumptions)
- [x] T043 [US5] Implement detect_reopens() function in src/github_analyzer/analyzers/jira_metrics.py (FR-022)
- [x] T044 [US5] Update MetricsCalculator.calculate_issue_metrics() to include reopen_count in src/github_analyzer/analyzers/jira_metrics.py
- [x] T045 [US5] Add reopen_rate_percent to MetricsCalculator.aggregate_project_metrics() in src/github_analyzer/analyzers/jira_metrics.py (FR-023)
- [x] T046 [US5] Ensure reopen_rate_percent column is exported in JiraMetricsExporter.export_project_metrics() per contracts/csv-schemas.md

**Checkpoint**: User Story 5 complete - reopen tracking functional with graceful degradation

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Integration, CLI wiring, and final validation

- [x] T047 Create integration test for full metrics flow in tests/integration/test_jira_metrics_flow.py
- [x] T048 Wire metrics calculation and export into CLI in src/github_analyzer/cli/main.py (add --jira-metrics flag or auto-include with --jira)
- [x] T049 Run quickstart.md validation - verify all documented commands work
- [x] T050 [P] Run ruff check and fix any linting issues
- [x] T051 [P] Verify all tests pass with pytest tests/ -v

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational completion
  - US1 (P1): No story dependencies - MVP standalone (includes all issue-level metrics: cycle_time, aging, description_quality, comments, cross_team_score, comment_velocity, same_day_resolution)
  - US2 (P2): Requires US1 IssueMetrics for aggregation input
  - US3 (P2): Requires US1 IssueMetrics for aggregation input
  - US4 (P3): Requires US1 IssueMetrics for aggregation input
  - US5 (P3): Adds reopen tracking (changelog API) and reopen_rate_percent to aggregations
- **Polish (Phase 8)**: Depends on all user stories

### User Story Dependencies

```
Phase 1: Setup
    ↓
Phase 2: Foundational (dataclasses)
    ↓
Phase 3: US1 - Issue Metrics [MVP] ← Can stop here for MVP delivery
    ↓
Phase 4: US2 - Project Aggregation ─┐
Phase 5: US3 - Person Aggregation  ─┼── Can run in parallel (different exports)
Phase 6: US4 - Type Aggregation    ─┤
Phase 7: US5 - Reopen Tracking     ─┘
    ↓
Phase 8: Polish & Integration
```

### Within Each User Story

1. Tests MUST be written and FAIL before implementation
2. Individual metric functions before composite calculator
3. Calculator before exporter modifications
4. Story complete before moving to next priority

### Parallel Opportunities

Within Phase 2 (Foundational):
- T004, T005, T006 can run in parallel (different dataclasses)

Within US1 Tests:
- T007-T015 can ALL run in parallel (different test functions)

Within US1 Implementation:
- T016-T022 can run in parallel (independent functions)
- T023-T025 must be sequential (dependencies)

Within US2-US5:
- Test tasks marked [P] can run in parallel
- Aggregation phases US2-US4 can run in parallel once US1 complete

---

## Parallel Example: User Story 1 Tests

```bash
# Launch all US1 tests together (T007-T015):
Task: "Write unit tests for cycle_time calculation"
Task: "Write unit tests for aging calculation"
Task: "Write unit tests for description_quality_score"
Task: "Write unit tests for acceptance_criteria detection"
Task: "Write unit tests for comments_count and silent_issue"
Task: "Write unit tests for same_day_resolution"
Task: "Write unit tests for cross_team_score"
Task: "Write unit tests for comment_velocity_hours"
Task: "Write unit test for extended CSV export columns"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T006)
3. Complete Phase 3: User Story 1 (T007-T025)
4. **STOP and VALIDATE**: Export issues, verify all 10 new columns present
5. Deploy/demo if ready - MVP complete!

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Test → **MVP delivered** (issue-level metrics including cross_team_score, comment_velocity)
3. Add US2 → Test → Project summary available
4. Add US3 → Test → Person summary available
5. Add US4 → Test → Type summary available
6. Add US5 → Test → Reopen tracking complete
7. Polish → Final validation → **Full feature complete**

### Single Developer Strategy

Follow phases sequentially:
- Phase 1 → Phase 2 → Phase 3 (MVP) → Phase 4 → Phase 5 → Phase 6 → Phase 7 → Phase 8

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story (US1-US5)
- Each user story can be delivered independently after US1 (MVP)
- Constitution requires TDD: write failing tests first
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Total tasks: 51
