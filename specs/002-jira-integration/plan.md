# Implementation Plan: Jira Integration & Multi-Platform Support

**Branch**: `002-jira-integration` | **Date**: 2025-11-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-jira-integration/spec.md`

## Summary

Add Jira REST API integration to extract issues and comments within a user-specified time range. The tool will become a multi-platform analyzer supporting both GitHub and Jira data sources. This requires renaming the entrypoint from `github_analyzer.py` to `dev_analyzer.py` while maintaining backward compatibility.

Key technical approach:
- New `api/jira_client.py` module mirroring the existing GitHub client pattern
- Configuration extended to support Jira credentials via environment variables
- Interactive project selection when `jira_projects.txt` is missing
- CSV export for Jira issues and comments following existing exporter patterns

## Technical Context

**Language/Version**: Python 3.9+ (per constitution, leveraging type hints)
**Primary Dependencies**: Standard library (urllib, json, csv, os, re); optional: requests
**Storage**: CSV files for export (same as existing GitHub exports)
**Testing**: pytest with mocks for API responses
**Target Platform**: CLI tool (macOS, Linux, Windows)
**Project Type**: Single project with modular architecture
**Performance Goals**: Extract 1000 issues in under 5 minutes (SC-001)
**Constraints**: No external dependencies required; requests optional with urllib fallback
**Scale/Scope**: Support up to 10,000+ issues per extraction with pagination (SC-005)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Modular Architecture | ✅ PASS | New modules: `api/jira_client.py`, `analyzers/jira_issues.py`, `exporters/jira_exporter.py` |
| II. Security First | ✅ PASS | Jira credentials via env vars only; no logging of tokens (FR-003) |
| III. Test-Driven Development | ✅ PASS | Tests with mocked Jira API responses; no network calls |
| IV. Configuration over Hardcoding | ✅ PASS | All Jira settings via env vars; `jira_projects.txt` for project list |
| V. Graceful Error Handling | ✅ PASS | Jira optional; missing credentials = skip with info message (FR-004) |

**Gate Result**: ✅ PASSED - No violations. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/002-jira-integration/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── jira-api.md      # Jira REST API contract documentation
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
src/github_analyzer/          # Existing structure (rename to dev_analyzer/ in future)
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── client.py             # Existing GitHub client
│   ├── jira_client.py        # NEW: Jira REST API client (includes JiraProject, JiraIssue, JiraComment dataclasses)
│   └── models.py             # Existing GitHub models
├── analyzers/
│   ├── __init__.py
│   ├── commits.py            # Existing
│   ├── issues.py             # Existing (GitHub issues)
│   ├── jira_issues.py        # NEW: Jira issue analyzer
│   ├── productivity.py       # Existing
│   ├── pull_requests.py      # Existing
│   └── quality.py            # Existing
├── cli/
│   ├── __init__.py
│   ├── main.py               # MODIFIED: Multi-source support, --sources flag
│   └── output.py             # Existing
├── config/
│   ├── __init__.py
│   ├── settings.py           # MODIFIED: Add Jira config (JiraConfig)
│   └── validation.py         # MODIFIED: Add Jira URL/project key validation
├── core/
│   ├── __init__.py
│   └── exceptions.py         # MODIFIED: Add JiraAPIError
└── exporters/
    ├── __init__.py
    ├── csv_exporter.py       # Existing
    └── jira_exporter.py      # NEW: Jira CSV exporter

tests/
├── unit/
│   ├── api/
│   │   └── test_jira_client.py    # NEW
│   ├── analyzers/
│   │   └── test_jira_issues.py    # NEW
│   ├── config/
│   │   └── test_jira_settings.py  # NEW
│   └── exporters/
│       └── test_jira_exporter.py  # NEW
└── integration/
    └── test_jira_flow.py          # NEW: End-to-end with mocked API

# Root level
dev_analyzer.py               # NEW: Primary entrypoint
github_analyzer.py            # MODIFIED: Backward compat wrapper
jira_projects.txt             # NEW: Optional project list (like repos.txt)
```

**Structure Decision**: Extend existing modular structure with parallel Jira modules. Follow same patterns as GitHub implementation for consistency.

## Complexity Tracking

> No violations requiring justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |
