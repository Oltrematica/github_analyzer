# Implementation Plan: Security Recommendations

**Branch**: `006-security-recommendations` | **Date**: 2025-11-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-security-recommendations/spec.md`

## Summary

Implement security recommendations from SECURITY.md audit report to harden the GitHub Analyzer tool. Primary focus areas: output path validation to prevent path traversal, dependency version pinning for supply chain security, CSV formula injection protection, response header validation, file permission checks, verbose audit logging, and timeout warnings.

## Technical Context

**Language/Version**: Python 3.9+ (per constitution, leveraging type hints)
**Primary Dependencies**: Standard library (pathlib, csv, os, stat, logging); optional: requests
**Storage**: CSV files for export (existing pattern)
**Testing**: pytest with pytest-cov (≥80% coverage target per constitution)
**Target Platform**: Unix-like systems (macOS, Linux); Windows support limited for permission checks
**Project Type**: Single CLI application
**Performance Goals**: No performance impact on default operation; verbose logging opt-in only
**Constraints**: Must maintain backward compatibility with existing CSV exports
**Scale/Scope**: Modifications to ~5 existing modules, 1-2 new utility modules

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Status | Notes |
|-----------|-------------|--------|-------|
| I. Modular Architecture | Security utilities as separate module | ✅ PASS | New `core/security.py` module |
| II. Security First | Validate all inputs, mask credentials | ✅ PASS | Core focus of this feature |
| III. Test-Driven Development | Tests before implementation, ≥80% coverage | ✅ PASS | Will include comprehensive tests |
| IV. Configuration over Hardcoding | Externalize configurable values | ✅ PASS | Timeout threshold, permission modes configurable |
| V. Graceful Error Handling | Clear error messages, partial failures allowed | ✅ PASS | Security warnings are non-blocking |

**Code Quality Standards:**
- Type hints: REQUIRED on all new functions
- Docstrings: Google style for all public classes/functions
- Linting: ruff with zero tolerance
- Max function length: 50 lines
- Max module length: 300 lines

**Dependencies:**
- Core functionality with stdlib only ✅
- Pin versions in `requirements.txt` ✅ (part of this feature)

## Project Structure

### Documentation (this feature)

```text
specs/006-security-recommendations/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (internal APIs)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/github_analyzer/
├── api/
│   ├── client.py           # MODIFY: Add Content-Type validation, verbose logging
│   └── jira_client.py      # MODIFY: Add Content-Type validation, verbose logging
├── config/
│   ├── settings.py         # MODIFY: Add verbose mode flag, timeout warning threshold
│   └── validation.py       # MODIFY: Add output path validation
├── core/
│   ├── exceptions.py       # Existing
│   └── security.py         # NEW: Security utilities (path validation, permission checks)
├── exporters/
│   ├── csv_exporter.py     # MODIFY: Add formula injection protection, path validation
│   └── jira_exporter.py    # MODIFY: Add formula injection protection
│   └── jira_metrics_exporter.py  # MODIFY: Add formula injection protection
├── cli/
│   └── main.py             # MODIFY: Add verbose flag, file permission warnings

tests/
├── unit/
│   ├── core/
│   │   └── test_security.py    # NEW: Security utilities tests
│   ├── config/
│   │   └── test_validation.py  # MODIFY: Add path validation tests
│   ├── exporters/
│   │   └── test_csv_exporter.py # MODIFY: Add formula injection tests
│   └── api/
│       └── test_client.py       # MODIFY: Add header validation tests
└── integration/
    └── test_security_features.py  # NEW: End-to-end security tests
```

**Structure Decision**: Single project structure maintained per existing architecture. Security utilities centralized in new `core/security.py` module with modifications to existing modules.

## Complexity Tracking

> No violations requiring justification. All changes align with constitution principles.
