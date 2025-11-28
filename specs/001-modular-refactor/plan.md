# Implementation Plan: Modular Architecture Refactoring

**Branch**: `001-modular-refactor` | **Date**: 2025-11-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-modular-refactor/spec.md`

## Summary

Refactor the monolithic `github_analyzer.py` (1000+ lines) into a modular, testable architecture following the project constitution. Key deliverables:
- Secure token management via environment variables
- Input validation with injection protection
- Modular code organization (api/, analyzers/, exporters/, cli/, config/)
- pytest-based test infrastructure

## Technical Context

**Language/Version**: Python 3.9+ (as per constitution, leveraging type hints)
**Primary Dependencies**: Standard library only (urllib, json, csv, os, re); optional: requests
**Storage**: File-based (CSV exports, repos.txt configuration)
**Testing**: pytest with pytest-cov for coverage reporting
**Target Platform**: Cross-platform CLI (macOS, Linux, Windows)
**Project Type**: Single project (CLI tool)
**Performance Goals**: Maintain current performance characteristics; no regression
**Constraints**: Must work without `requests` library (stdlib fallback)
**Scale/Scope**: Analyze multiple GitHub repositories; handle API rate limits

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Status | Notes |
|-----------|-------------|--------|-------|
| **I. Modular Architecture** | Organize into api/, analyzers/, exporters/, cli/, config/ | ✅ PASS | Core goal of this refactor |
| **II. Security First** | Token via env vars, no credential leaks | ✅ PASS | US1 addresses this directly |
| **III. Test-Driven Development** | Tests before implementation, ≥80% coverage | ✅ PASS | US4 establishes infrastructure |
| **IV. Configuration over Hardcoding** | Central config module, externalized values | ✅ PASS | FR-001 through FR-004 |
| **V. Graceful Error Handling** | Actionable errors, partial failure handling | ✅ PASS | Already in existing code, will preserve |

**Technical Standards Compliance**:
- Type hints: Will be added to all public interfaces
- Docstrings: Google style on all public functions
- Linting: ruff configured
- Max module size: 300 lines target
- No bare except clauses

## Project Structure

### Documentation (this feature)

```text
specs/001-modular-refactor/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (internal module interfaces)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── github_analyzer/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── client.py        # GitHubClient class (HTTP requests, pagination)
│   │   └── models.py        # API response models (Commit, PR, Issue)
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── commits.py       # Commit analysis logic
│   │   ├── pull_requests.py # PR analysis logic
│   │   ├── issues.py        # Issue analysis logic
│   │   ├── quality.py       # Quality metrics calculation
│   │   └── productivity.py  # Productivity scoring
│   ├── exporters/
│   │   ├── __init__.py
│   │   └── csv_exporter.py  # CSV file generation
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── main.py          # Entry point, argument parsing
│   │   └── output.py        # Terminal output formatting (Colors, banners)
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py      # Configuration management
│   │   └── validation.py    # Input validation (repos, tokens)
│   └── core/
│       ├── __init__.py
│       └── exceptions.py    # Custom exceptions

tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── unit/
│   ├── __init__.py
│   ├── api/
│   │   ├── test_client.py
│   │   └── test_models.py
│   ├── analyzers/
│   │   ├── test_commits.py
│   │   ├── test_pull_requests.py
│   │   ├── test_issues.py
│   │   ├── test_quality.py
│   │   └── test_productivity.py
│   ├── exporters/
│   │   └── test_csv_exporter.py
│   └── config/
│       ├── test_settings.py
│       └── test_validation.py
├── integration/
│   ├── __init__.py
│   └── test_analyzer_flow.py
└── fixtures/
    ├── api_responses/       # Mock GitHub API responses
    └── sample_data/         # Sample repos.txt, expected CSVs

github_analyzer.py           # Backward-compatible entry point (imports from src/)
```

**Structure Decision**: Single project structure selected. The `github_analyzer.py` at root level is preserved for backward compatibility and delegates to `src/github_analyzer/cli/main.py`.

## Complexity Tracking

> No constitution violations identified. All requirements align with principles.

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Module count | 6 modules (api, analyzers, exporters, cli, config, core) | Follows constitution's prescribed structure |
| Backward compat | Keep root `github_analyzer.py` | Users can run existing command unchanged |
| Test structure | Mirrors source | Per constitution III |
