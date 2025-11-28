<!--
SYNC IMPACT REPORT
==================
Version change: 1.0.0 → 1.0.1 (patch: clarification)
Modified principles:
  - I. Modular Architecture: Added `core/` to required modules list
Added sections: None
Removed sections: None
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ (no changes needed - compatible)
  - .specify/templates/spec-template.md ✅ (no changes needed - compatible)
  - .specify/templates/tasks-template.md ✅ (no changes needed - compatible)
Follow-up TODOs: None
-->

# GitHub Analyzer Constitution

## Core Principles

### I. Modular Architecture

Every feature MUST be implemented as a separate, independently testable module.

- The codebase MUST be organized into distinct modules: `api/`, `analyzers/`, `exporters/`, `cli/`, `config/`, `core/`
- Each module MUST have a single responsibility and clear boundaries
- Inter-module communication MUST use well-defined interfaces (abstract base classes or protocols)
- No module may directly access another module's internal state
- Dependencies between modules MUST flow in one direction (no circular imports)

**Rationale**: The current monolithic 1000+ line single file is untestable and unmaintainable. Modular architecture enables unit testing, easier debugging, and parallel development.

### II. Security First

All external inputs and credentials MUST be validated and handled securely.

- GitHub tokens MUST be loaded from environment variables (`GITHUB_TOKEN`) or secure config files, NEVER hardcoded
- Token values MUST NOT be logged, printed, or exposed in error messages
- All repository URLs and user inputs MUST be validated against injection attacks
- API responses MUST be validated before processing (schema validation)
- Rate limit handling MUST NOT expose sensitive timing information
- Error messages MUST NOT leak internal system details or credentials

**Rationale**: The tool handles sensitive GitHub credentials with full repo access. Security vulnerabilities could lead to token theft or unauthorized repository access.

### III. Test-Driven Development

All new features and bug fixes MUST have corresponding tests written BEFORE implementation.

- Unit tests MUST cover all public module interfaces with ≥80% coverage target
- Integration tests MUST verify API client behavior with mocked responses
- Contract tests MUST validate GitHub API response parsing against real schemas
- Tests MUST be isolated and not depend on external services (use mocks/fixtures)
- Test files MUST mirror source structure: `src/module.py` → `tests/unit/test_module.py`
- CI pipeline MUST fail if tests fail or coverage drops below threshold

**Rationale**: Current codebase has zero tests. Without tests, refactoring is risky and bugs are caught late. TDD ensures reliability and enables confident changes.

### IV. Configuration over Hardcoding

All configurable values MUST be externalized and injectable.

- Default values (days, output dir, per_page, etc.) MUST be defined in a central config module
- Configuration MUST support multiple sources: environment variables, config files, CLI arguments
- Configuration precedence: CLI args > env vars > config file > defaults
- Sensitive configuration (tokens) MUST use environment variables only
- All magic numbers and strings MUST be named constants with clear documentation
- Configuration schema MUST be validated at startup

**Rationale**: Hardcoded values make the tool inflexible and harder to test. Externalized config enables different environments (dev/test/prod) and easier customization.

### V. Graceful Error Handling

All errors MUST be handled gracefully with informative, actionable messages.

- Exceptions MUST be caught at appropriate boundaries, not swallowed silently
- Error messages MUST explain what went wrong and suggest remediation
- API errors MUST be categorized: auth errors, rate limits, not found, server errors
- Partial failures MUST NOT abort entire analysis; continue with available data
- All errors MUST be logged with context (repo, operation, timestamp)
- Exit codes MUST follow conventions: 0=success, 1=user error, 2=system error

**Rationale**: Current error handling is inconsistent. Users need clear feedback to diagnose and fix issues. Graceful degradation improves reliability.

## Technical Standards

### Code Quality

- Python version: 3.9+ (leverage type hints fully)
- Type hints: REQUIRED on all public function signatures
- Docstrings: REQUIRED on all public classes and functions (Google style)
- Linting: `ruff` for linting and formatting, zero tolerance for errors
- Import organization: `isort` with sections (stdlib, third-party, local)
- Maximum function length: 50 lines (excluding docstrings)
- Maximum module length: 300 lines (excluding tests)
- No bare `except:` clauses; always catch specific exceptions

### Dependencies

- Core functionality MUST work with Python standard library only
- Optional dependencies (requests, rich) MUST be gracefully degraded
- All dependencies MUST be pinned in `requirements.txt` with versions
- Development dependencies MUST be separate in `requirements-dev.txt`
- No vendored code without explicit justification and license compliance

### API Client Standards

- All HTTP requests MUST have configurable timeouts (default: 30s)
- Retry logic MUST use exponential backoff for transient failures
- Rate limit responses MUST trigger automatic wait-and-retry
- All API URLs MUST be constructed safely (no string concatenation with user input)
- Response parsing MUST handle missing/null fields gracefully

## Development Workflow

### Branch Strategy

- `main`: Production-ready code only
- `feat/*`: New features (branch from main)
- `fix/*`: Bug fixes (branch from main)
- `refactor/*`: Code improvements without behavior changes

### Code Review Requirements

- All changes to `main` MUST go through pull request
- PRs MUST have passing CI (tests, linting, type checking)
- PRs MUST include tests for new functionality
- Security-related changes MUST have explicit security review

### Testing Workflow

1. Write failing test that defines expected behavior
2. Implement minimum code to pass the test
3. Refactor while keeping tests green
4. Run full test suite before committing
5. CI validates all tests pass

## Governance

This constitution defines non-negotiable standards for the GitHub Analyzer project.

### Amendment Process

1. Propose change via GitHub issue with rationale
2. Document impact on existing code and tests
3. Update constitution version following semantic versioning
4. Update dependent templates if principles change
5. Migrate existing code to comply (within reasonable timeframe)

### Versioning Policy

- **MAJOR**: Removing or fundamentally changing a principle
- **MINOR**: Adding new principles or expanding existing guidance
- **PATCH**: Clarifications, typo fixes, non-semantic updates

### Compliance

- All code reviews MUST verify adherence to constitution principles
- Violations MUST be documented and tracked
- Technical debt from violations MUST have remediation timeline
- Constitution takes precedence over convenience

**Version**: 1.0.1 | **Ratified**: 2025-11-28 | **Last Amended**: 2025-11-28
