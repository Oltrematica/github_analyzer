# Tasks: Frontend Report Generator

**Input**: Design documents from `/specs/007-frontend-report-generator/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/perplexity-api.md

**Tests**: Constitution richiede TDD (Principle III) - test inclusi per ogni modulo.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Based on plan.md:
- Source: `src/github_analyzer/report_generator/`
- Tests: `tests/unit/report_generator/`
- Frontend assets: `frontend/`
- Config: `frontend/config/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and module structure

- [ ] T001 Create report_generator module structure in src/github_analyzer/report_generator/__init__.py
- [ ] T002 [P] Create models.py with all dataclasses in src/github_analyzer/report_generator/models.py
- [ ] T003 [P] Create frontend directory structure (frontend/config/, frontend/assets/, frontend/reports/)
- [ ] T004 [P] Add PyYAML to requirements.txt (optional dependency)
- [ ] T005 [P] Create test directory structure in tests/unit/report_generator/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 [P] Create default report_config.yaml in frontend/config/report_config.yaml
- [ ] T007 [P] Implement config loading with YAML/JSON fallback in src/github_analyzer/report_generator/config.py
- [ ] T008 Create base HTML template structure in src/github_analyzer/report_generator/templates/report.html
- [ ] T009 [P] Implement template rendering utility with html.escape in src/github_analyzer/report_generator/html_generator.py
- [ ] T010 [P] Add CSS styles (gradient theme, responsive) in frontend/assets/css/report.css
- [ ] T011 [P] Add Chart.js configuration utilities in frontend/assets/js/charts.js

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Generazione Report Base (Priority: P1) 🎯 MVP

**Goal**: Generare report HTML con sezioni Team Overview, Quality Metrics, Individual Reports, GitHub Metrics aggregando dati CSV

**Independent Test**: Generare report con CSV esistenti e verificare HTML con tutte le sezioni navigabili

### Tests for User Story 1

- [ ] T012 [P] [US1] Unit test for CSV parsing in tests/unit/report_generator/test_data_aggregator.py
- [ ] T013 [P] [US1] Unit test for metrics aggregation in tests/unit/report_generator/test_data_aggregator.py
- [ ] T014 [P] [US1] Unit test for trend calculation in tests/unit/report_generator/test_data_aggregator.py
- [ ] T015 [P] [US1] Unit test for HTML generation in tests/unit/report_generator/test_html_generator.py

### Implementation for User Story 1

- [ ] T016 [P] [US1] Implement GitHub CSV parser (commits, PRs, issues, contributors, quality, productivity) in src/github_analyzer/report_generator/data_aggregator.py
- [ ] T017 [P] [US1] Implement Jira CSV parser (issues, person_metrics, project_quality) in src/github_analyzer/report_generator/data_aggregator.py
- [ ] T018 [US1] Implement metrics aggregation (team stats, individual stats) in src/github_analyzer/report_generator/data_aggregator.py
- [ ] T019 [US1] Implement trend calculation (period-over-period comparison) in src/github_analyzer/report_generator/data_aggregator.py
- [ ] T020 [P] [US1] Create header.html component in src/github_analyzer/report_generator/templates/components/header.html
- [ ] T021 [P] [US1] Create team_overview.html component with KPI cards in src/github_analyzer/report_generator/templates/components/team_overview.html
- [ ] T022 [P] [US1] Create quality_metrics.html component in src/github_analyzer/report_generator/templates/components/quality_metrics.html
- [ ] T023 [P] [US1] Create member_report.html component in src/github_analyzer/report_generator/templates/components/member_report.html
- [ ] T024 [P] [US1] Create footer.html component in src/github_analyzer/report_generator/templates/components/footer.html
- [ ] T025 [US1] Implement full HTML assembly with inline CSS/JS in src/github_analyzer/report_generator/html_generator.py
- [ ] T026 [US1] Add sticky navigation with deep linking (#section-name) in report template
- [ ] T027 [US1] Implement ReportData to JSON serialization for data.json export in src/github_analyzer/report_generator/html_generator.py

**Checkpoint**: Report base funzionante con tutte le sezioni (senza AI, senza mapping avanzato)

---

## Phase 4: User Story 2 - Mapping Utenti Jira↔GitHub (Priority: P2)

**Goal**: Associare account Jira a GitHub con auto-matching fuzzy e riconciliazione CLI interattiva

**Independent Test**: Eseguire mapping con lista utenti, verificare match automatici e persistenza YAML

### Tests for User Story 2

- [ ] T028 [P] [US2] Unit test for fuzzy matching algorithm in tests/unit/report_generator/test_user_mapping.py
- [ ] T029 [P] [US2] Unit test for YAML persistence in tests/unit/report_generator/test_user_mapping.py
- [ ] T030 [P] [US2] Unit test for edge cases (solo-Jira, solo-GitHub, bots) in tests/unit/report_generator/test_user_mapping.py

### Implementation for User Story 2

- [ ] T031 [P] [US2] Implement fuzzy matching with difflib.SequenceMatcher in src/github_analyzer/report_generator/user_mapping.py
- [ ] T032 [US2] Implement auto-matching strategies (email, username, name fuzzy, initials) in src/github_analyzer/report_generator/user_mapping.py
- [ ] T033 [US2] Implement confidence scoring and ranking in src/github_analyzer/report_generator/user_mapping.py
- [ ] T034 [US2] Implement CLI interactive reconciliation interface in src/github_analyzer/report_generator/user_mapping.py
- [ ] T035 [US2] Implement YAML load/save for user_mapping.yaml in src/github_analyzer/report_generator/user_mapping.py
- [ ] T036 [US2] Implement bot detection patterns (dependabot, github-actions) in src/github_analyzer/report_generator/user_mapping.py
- [ ] T037 [US2] Integrate user mapping into data aggregation pipeline in src/github_analyzer/report_generator/data_aggregator.py

**Checkpoint**: Mapping utenti funzionante con persistenza e riconciliazione interattiva

---

## Phase 5: User Story 3 - Analisi AI con Perplexity (Priority: P3)

**Goal**: Integrare Perplexity API per generare insights qualitativi con cache e graceful degradation

**Independent Test**: Inviare metriche a Perplexity, verificare JSON response con rating/strengths/improvements

### Tests for User Story 3

- [ ] T038 [P] [US3] Unit test for Perplexity client with mocked API in tests/unit/report_generator/test_ai_client.py
- [ ] T039 [P] [US3] Unit test for AI response parsing in tests/unit/report_generator/test_ai_client.py
- [ ] T040 [P] [US3] Unit test for cache mechanism in tests/unit/report_generator/test_ai_client.py
- [ ] T041 [P] [US3] Unit test for rate limit handling in tests/unit/report_generator/test_ai_client.py

### Implementation for User Story 3

- [ ] T042 [P] [US3] Implement PerplexityClient base class in src/github_analyzer/report_generator/ai_client.py
- [ ] T043 [US3] Implement prompt templates (team, member, project analysis) in src/github_analyzer/report_generator/ai_client.py
- [ ] T044 [US3] Implement AI response parsing with JSON extraction in src/github_analyzer/report_generator/ai_client.py
- [ ] T045 [US3] Implement AICache with TTL and hash-based keys in src/github_analyzer/report_generator/ai_client.py
- [ ] T046 [US3] Implement RateLimitError and interactive handling in src/github_analyzer/report_generator/ai_client.py
- [ ] T047 [US3] Implement graceful degradation (placeholder when API unavailable) in src/github_analyzer/report_generator/ai_client.py
- [ ] T048 [US3] Integrate AI insights into report HTML generation in src/github_analyzer/report_generator/html_generator.py
- [ ] T049 [US3] Add AI analysis sections to team_overview.html and member_report.html templates

**Checkpoint**: AI insights funzionanti con cache e fallback

---

## Phase 6: User Story 4 - Visualizzazioni Interattive (Priority: P4)

**Goal**: Aggiungere grafici Chart.js interattivi (bar, donut, trend) con supporto mobile

**Independent Test**: Verificare rendering grafici in browser e interattività touch su mobile

### Tests for User Story 4

- [ ] T050 [P] [US4] Unit test for Chart.js config generation in tests/unit/report_generator/test_html_generator.py

### Implementation for User Story 4

- [ ] T051 [P] [US4] Implement bar chart config generator (task assigned vs resolved) in src/github_analyzer/report_generator/html_generator.py
- [ ] T052 [P] [US4] Implement donut chart config generator (issue type distribution) in src/github_analyzer/report_generator/html_generator.py
- [ ] T053 [P] [US4] Implement horizontal bar chart for cycle time per project in src/github_analyzer/report_generator/html_generator.py
- [ ] T054 [US4] Add Chart.js CDN and initialization script to report template
- [ ] T055 [US4] Implement responsive chart containers with CSS breakpoints in frontend/assets/css/report.css
- [ ] T056 [US4] Add chart animations and hover interactions in Chart.js configs

**Checkpoint**: Grafici interattivi funzionanti su desktop e mobile

---

## Phase 7: User Story 5 - Interfaccia CLI di Generazione (Priority: P5)

**Goal**: Comando CLI con opzioni configurabili (--period, --output, --sources, --user-mapping, --ai/--no-ai)

**Independent Test**: Eseguire comando con varie combinazioni di flag e verificare output

### Tests for User Story 5

- [ ] T057 [P] [US5] Integration test for CLI with various flag combinations in tests/integration/test_report_generation.py

### Implementation for User Story 5

- [ ] T058 [US5] Implement CLI entry point with argparse in src/github_analyzer/report_generator/cli.py
- [ ] T059 [US5] Implement --period, --output, --sources options parsing in src/github_analyzer/report_generator/cli.py
- [ ] T060 [US5] Implement --user-mapping and --ai/--no-ai flags in src/github_analyzer/report_generator/cli.py
- [ ] T061 [US5] Implement --config option for custom report_config.yaml in src/github_analyzer/report_generator/cli.py
- [ ] T062 [US5] Implement progress output with phase indicators in src/github_analyzer/report_generator/cli.py
- [ ] T063 [US5] Implement error handling and exit codes (0, 1, 2) in src/github_analyzer/report_generator/cli.py
- [ ] T064 [US5] Add __main__.py for `python -m src.github_analyzer.report_generator` invocation

**Checkpoint**: CLI completa e funzionante con tutte le opzioni

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T065 [P] Update CLAUDE.md with new report_generator commands
- [ ] T066 [P] Create example report with mock data in frontend/example/
- [ ] T067 Run full integration test with real CSV data
- [ ] T068 [P] Add security hardening (validate_output_path for report output) in src/github_analyzer/report_generator/cli.py
- [ ] T069 Validate HTML output <2MB and load time <3s
- [ ] T070 Run quickstart.md validation (manual test)
- [ ] T071 [P] Add type hints validation with mypy

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User stories can proceed in priority order (P1 → P2 → P3 → P4 → P5)
  - US2-US5 depend on US1 for base report structure
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

```
US1 (Report Base) ─────────────────────────────────────┐
                                                        │
US2 (User Mapping) ───────────┐                        │
                              │                        │
US3 (AI Integration) ─────────┼──────> US1 base       │
                              │                        │
US4 (Charts) ─────────────────┘                        │
                                                        │
US5 (CLI) ─────────────────────────────> All stories ──┘
```

- **User Story 1 (P1)**: No dependencies on other stories - MVP standalone
- **User Story 2 (P2)**: Enhances US1 with unified user metrics
- **User Story 3 (P3)**: Enhances US1 with AI sections (optional)
- **User Story 4 (P4)**: Enhances US1 with interactive charts
- **User Story 5 (P5)**: Orchestrates all stories via CLI

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/utilities before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**:
```bash
# All in parallel:
T002, T003, T004, T005
```

**Phase 2 (Foundational)**:
```bash
# All in parallel:
T006, T007, T009, T010, T011
# Then T008 (depends on T010 for CSS)
```

**Phase 3 (US1)**:
```bash
# Tests in parallel:
T012, T013, T014, T015

# CSV parsers in parallel:
T016, T017

# Templates in parallel:
T020, T021, T022, T023, T024
```

**Phase 4 (US2)**:
```bash
# Tests in parallel:
T028, T029, T030
```

**Phase 5 (US3)**:
```bash
# Tests in parallel:
T038, T039, T040, T041

# Then implementation
T042 (base) → T043, T044, T045, T046, T047 (can parallelize some)
```

**Phase 6 (US4)**:
```bash
# Chart generators in parallel:
T051, T052, T053
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test report generation with existing CSV
5. Deploy/demo basic report

### Incremental Delivery

1. **v0.1**: Setup + Foundational → Base structure ready
2. **v0.2**: + User Story 1 → Basic report with all sections (MVP!)
3. **v0.3**: + User Story 2 → Unified user metrics with mapping
4. **v0.4**: + User Story 3 → AI-powered insights
5. **v0.5**: + User Story 4 → Interactive charts
6. **v1.0**: + User Story 5 + Polish → Full CLI with all features

---

## Summary

| Phase | Tasks | Parallel Tasks | Description |
|-------|-------|----------------|-------------|
| 1. Setup | 5 | 4 | Module structure |
| 2. Foundational | 6 | 5 | Base infrastructure |
| 3. US1 (P1) | 16 | 12 | Report base - MVP |
| 4. US2 (P2) | 10 | 3 | User mapping |
| 5. US3 (P3) | 12 | 4 | AI integration |
| 6. US4 (P4) | 6 | 4 | Charts |
| 7. US5 (P5) | 8 | 1 | CLI |
| 8. Polish | 7 | 4 | Final touches |
| **Total** | **70** | **37** | |

**MVP Scope**: Phases 1-3 (27 tasks) → Functional report generator without AI/mapping/CLI features

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD per Constitution)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
