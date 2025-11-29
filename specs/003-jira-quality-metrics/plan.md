# Implementation Plan: Jira Quality Metrics Export

**Branch**: `003-jira-quality-metrics` | **Date**: 2025-11-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-jira-quality-metrics/spec.md`

## Summary

Enhance Jira export functionality with 12 quality metrics calculated at issue-level (cycle time, aging, description quality, comments count, acceptance criteria detection, comment velocity, silent issue flag, same-day resolution, cross-team score) plus aggregated metrics exported to 3 new CSV files (project, person, type summaries). Technical approach: extend existing `JiraExporter` and `JiraIssueAnalyzer` classes with new metrics calculator module.

## Technical Context

**Language/Version**: Python 3.9+ (per constitution, leveraging type hints)
**Primary Dependencies**: Standard library only (urllib, json, csv, os, re, datetime, statistics); optional: requests (already used in jira_client.py)
**Storage**: CSV files for export (same as existing GitHub exports)
**Testing**: pytest with fixtures (existing test infrastructure in tests/)
**Target Platform**: CLI tool (macOS/Linux)
**Project Type**: single (CLI application with modular structure)
**Performance Goals**: Export generation with metrics ≤200% of current base export time (SC-005)
**Constraints**: No new external dependencies; maintain backwards compatibility with existing export format
**Scale/Scope**: Handles typical Jira project sizes (hundreds to thousands of issues per project)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Modular Architecture | ✅ PASS | New metrics calculator in `analyzers/`, extends existing `exporters/jira_exporter.py` |
| II. Security First | ✅ PASS | No new credentials; uses existing JiraClient auth; no sensitive data in metrics |
| III. Test-Driven Development | ✅ PASS | Tests will be written before implementation; fixtures exist |
| IV. Configuration over Hardcoding | ✅ PASS | Metric thresholds (quality score weights) defined as constants |
| V. Graceful Error Handling | ✅ PASS | Edge cases documented; null handling specified in spec |

**Code Quality Standards**:
- Type hints: REQUIRED (all new functions)
- Docstrings: REQUIRED (Google style)
- Max function length: 50 lines
- Max module length: 300 lines

## Project Structure

### Documentation (this feature)

```text
specs/003-jira-quality-metrics/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (CSV schemas)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/github_analyzer/
├── analyzers/
│   ├── jira_issues.py           # Existing - basic stats
│   └── jira_metrics.py          # NEW - quality metrics calculator
├── exporters/
│   ├── jira_exporter.py         # MODIFY - add metrics columns
│   └── jira_metrics_exporter.py # NEW - summary CSV exports
├── api/
│   └── jira_client.py           # Existing - may need changelog API
├── config/
│   └── settings.py              # MODIFY - add metrics config constants
└── core/
    └── exceptions.py            # Existing - reuse for errors

tests/
├── unit/
│   ├── analyzers/
│   │   └── test_jira_metrics.py # NEW
│   └── exporters/
│       └── test_jira_metrics_exporter.py # NEW
├── integration/
│   └── test_jira_metrics_flow.py # NEW
└── fixtures/
    └── jira_responses.py        # MODIFY - add metrics test data
```

**Structure Decision**: Single project structure following existing modular layout. New functionality added as separate modules (`jira_metrics.py`, `jira_metrics_exporter.py`) to maintain single responsibility and testability per constitution principle I.

## Complexity Tracking

No constitution violations. All complexity is justified by spec requirements.
