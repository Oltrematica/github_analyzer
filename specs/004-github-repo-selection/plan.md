# Implementation Plan: GitHub Repository Interactive Selection

**Branch**: `004-github-repo-selection` | **Date**: 2025-11-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-github-repo-selection/spec.md`

## Summary

Implement interactive repository selection for GitHub analysis when `repos.txt` is missing or empty. Users can choose to (A) analyze all personal repos, (S) specify manually, (O) analyze organization repos, (L) select from list, or (Q) quit. The implementation follows the established `select_jira_projects` UX pattern from Feature 002.

## Technical Context

**Language/Version**: Python 3.9+ (as per constitution, leveraging type hints)
**Primary Dependencies**: Standard library only (urllib, json); optional: requests (existing pattern)
**Storage**: N/A (repos.txt file is input, not storage)
**Testing**: pytest with fixtures and mocking (existing pattern)
**Target Platform**: CLI on macOS/Linux/Windows
**Project Type**: Single project (existing structure)
**Performance Goals**: Repository listing in <10s for 200 repos, <15s for 500 org repos (per SC-002, SC-003)
**Constraints**: Rate limit aware, graceful error handling, non-blocking in quiet mode
**Scale/Scope**: Support users with 200+ personal repos, orgs with 500+ repos

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Modular Architecture | ✅ PASS | New function `select_github_repos` in `cli/main.py` following existing `select_jira_projects` pattern. API methods added to existing `GitHubClient` in `api/client.py` |
| II. Security First | ✅ PASS | Uses existing token handling via `AnalyzerConfig`. No new token exposure points |
| III. Test-Driven Development | ✅ PASS | Tests will mirror `test_interactive_selection.py` pattern for Jira |
| IV. Configuration over Hardcoding | ✅ PASS | Uses existing `repos_file` from config, affiliation parameter configurable |
| V. Graceful Error Handling | ✅ PASS | EOF/KeyboardInterrupt handled, API errors caught, partial failures tolerated |

**Gate Result**: PASS - No violations

## Project Structure

### Documentation (this feature)

```text
specs/004-github-repo-selection/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/github_analyzer/
├── api/
│   └── client.py           # Extended: list_user_repos(), list_org_repos()
├── cli/
│   └── main.py             # Extended: select_github_repos(), helpers
└── ...

tests/
├── unit/
│   └── api/
│       └── test_github_client.py  # New: list_user_repos, list_org_repos tests
└── integration/
    └── test_interactive_selection.py  # Extended: GitHub selection tests
```

**Structure Decision**: Extend existing modules following established patterns. No new modules needed - consistent with constitution's modular architecture principle.

## Complexity Tracking

> No violations to justify - all decisions follow existing patterns.

| Decision | Justification |
|----------|---------------|
| Extend existing `GitHubClient` | Follows constitution's modular architecture - API client is the correct location for API calls |
| Add to `cli/main.py` | Follows `select_jira_projects` pattern for UX consistency (FR-003) |
