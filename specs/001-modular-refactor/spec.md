# Feature Specification: Modular Architecture Refactoring

**Feature Branch**: `001-modular-refactor`
**Created**: 2025-11-28
**Status**: Draft
**Input**: User description: "Refactoring modulare del GitHub Analyzer: scomporre il monolite github_analyzer.py (1000+ righe) in moduli testabili seguendo la constitution (api/, analyzers/, exporters/, cli/, config/). Implementare gestione sicura dei token via environment variables, aggiungere validazione input, creare struttura per unit test con pytest."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Secure Token Configuration (Priority: P1)

As a user, I want to configure my GitHub token securely through environment variables so that my credentials are never exposed in logs, command history, or error messages.

**Why this priority**: Security is the highest priority. The current implementation asks for tokens via interactive input, which can be exposed in terminal history and process lists. Environment-based configuration is the industry standard for credential management.

**Independent Test**: Can be fully tested by setting `GITHUB_TOKEN` environment variable and running the analyzer. The tool should authenticate successfully without prompting for credentials.

**Acceptance Scenarios**:

1. **Given** `GITHUB_TOKEN` environment variable is set with a valid token, **When** I run the analyzer, **Then** the tool authenticates automatically without prompting for credentials
2. **Given** `GITHUB_TOKEN` is not set, **When** I run the analyzer, **Then** the tool displays a clear error message explaining how to set the environment variable
3. **Given** `GITHUB_TOKEN` contains an invalid token, **When** I run the analyzer, **Then** the tool displays an authentication error without revealing the token value in any output
4. **Given** the analyzer encounters an API error, **When** the error is logged, **Then** no token values appear in logs or error messages

---

### User Story 2 - Validated Repository Input (Priority: P2)

As a user, I want the tool to validate repository names and URLs before making API calls so that I receive immediate feedback on input errors rather than cryptic API failures.

**Why this priority**: Input validation prevents wasted API calls and rate limit consumption. It also protects against injection attacks when constructing API URLs.

**Independent Test**: Can be fully tested by providing various valid and invalid repository formats and verifying the tool's response before any API calls are made.

**Acceptance Scenarios**:

1. **Given** a repos.txt file with valid `owner/repo` format entries, **When** the analyzer loads repositories, **Then** all entries are accepted for processing
2. **Given** a repos.txt with GitHub URLs (`https://github.com/owner/repo`), **When** the analyzer loads repositories, **Then** URLs are normalized to `owner/repo` format
3. **Given** a repos.txt with malformed entries (empty lines, special characters, path traversal attempts), **When** the analyzer loads repositories, **Then** invalid entries are rejected with specific error messages identifying the problem
4. **Given** repository names containing dangerous characters (`;`, `|`, `&`, `..`), **When** processing input, **Then** the tool rejects these entries as potential injection attempts

---

### User Story 3 - Modular Code Organization (Priority: P3)

As a developer, I want the codebase organized into separate modules with clear responsibilities so that I can understand, test, and modify individual components without affecting others.

**Why this priority**: Modularity enables testability, maintainability, and parallel development. While critical for long-term health, the tool functions without it.

**Independent Test**: Can be verified by importing individual modules and testing their interfaces in isolation without loading the entire application.

**Acceptance Scenarios**:

1. **Given** the refactored codebase, **When** I import the API client module, **Then** I can create an API client instance without loading CLI, exporters, or analyzers
2. **Given** the refactored codebase, **When** I run the existing CLI command, **Then** all current functionality works identically to before the refactor
3. **Given** the modular structure, **When** I write a unit test for a single module, **Then** I can mock its dependencies without loading the full application

---

### User Story 4 - Automated Testing Infrastructure (Priority: P4)

As a developer, I want a test infrastructure in place so that I can write and run tests to verify the tool's behavior and catch regressions.

**Why this priority**: Testing infrastructure is foundational for confidence in changes. Lower priority because it's developer-facing, not user-facing.

**Independent Test**: Can be verified by running the test suite and seeing test discovery, execution, and reporting work correctly.

**Acceptance Scenarios**:

1. **Given** the test infrastructure is set up, **When** I run the test command, **Then** the test runner discovers and executes all tests
2. **Given** test files in the tests directory, **When** tests are executed, **Then** results show pass/fail status and coverage report
3. **Given** the modular code structure, **When** I write a unit test with mocked dependencies, **Then** the test runs in isolation without network calls

---

### Edge Cases

- What happens when repos.txt contains duplicate repository entries?
  - Duplicates should be deduplicated with a warning, processing each repository only once
- What happens when a repository URL uses http:// instead of https://?
  - The URL should be normalized to https:// automatically
- What happens when environment variable contains leading/trailing whitespace?
  - Whitespace should be stripped from the token value
- What happens when repos.txt file doesn't exist?
  - Clear error message with instructions on how to create the file
- What happens when repos.txt is empty or contains only comments?
  - Clear error message indicating no repositories were found to analyze

## Requirements *(mandatory)*

### Functional Requirements

**Security**
- **FR-001**: System MUST read GitHub token from `GITHUB_TOKEN` environment variable
- **FR-002**: System MUST NOT log, print, or expose token values in any output including error messages
- **FR-003**: System MUST NOT accept token via command line arguments (to prevent exposure in process lists)
- **FR-004**: System MUST validate token format before making API calls (basic format check, not API validation)

**Input Validation**
- **FR-005**: System MUST validate repository names match pattern `^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$`
- **FR-006**: System MUST reject repository names containing shell metacharacters (`;|&$\`(){}[]`)
- **FR-007**: System MUST normalize GitHub URLs to `owner/repo` format
- **FR-008**: System MUST deduplicate repository entries and warn about duplicates
- **FR-009**: System MUST provide specific validation error messages for each type of invalid input

**Modularity**
- **FR-010**: Codebase MUST be organized into distinct modules: API client, analyzers, exporters, CLI, configuration
- **FR-011**: Each module MUST have a single responsibility and clear public interface
- **FR-012**: Modules MUST NOT have circular dependencies
- **FR-013**: All inter-module communication MUST use defined interfaces (no direct internal state access)

**Backward Compatibility**
- **FR-014**: All existing CLI functionality MUST continue to work after refactoring
- **FR-015**: All existing CSV export formats MUST remain unchanged
- **FR-016**: System MUST support graceful fallback when optional dependencies (requests) are unavailable

**Testing**
- **FR-017**: Project MUST include test infrastructure with pytest
- **FR-018**: Test structure MUST mirror source structure for discoverability
- **FR-019**: Tests MUST be runnable without network access (using mocks/fixtures)

### Key Entities

- **Configuration**: Application settings including token reference, output directory, analysis period, verbosity level
- **Repository**: Validated repository identifier with owner and name components
- **APIClient**: Interface for GitHub API communication with rate limiting awareness
- **Analyzer**: Processing component that transforms raw API data into metrics
- **Exporter**: Output component that writes analysis results to files

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All existing functionality works identically after refactoring (zero user-visible behavioral changes)
- **SC-002**: Token values never appear in any log output, error messages, or console display (verified by grep search of all outputs)
- **SC-003**: Invalid repository inputs are caught and reported before any API calls are made
- **SC-004**: Individual modules can be imported and tested in isolation without loading the full application
- **SC-005**: Test suite runs and passes without requiring network access or valid GitHub credentials
- **SC-006**: Maximum module size is under 300 lines (excluding tests and docstrings)
- **SC-007**: All public functions and classes have type hints and docstrings

## Assumptions

- The existing interactive token prompt will be removed in favor of environment variable only
- Users are expected to set environment variables through their shell profile or CI/CD configuration
- The `requests` library remains optional; stdlib `urllib` fallback continues to be supported
- No new CLI arguments are added in this refactoring phase
- Performance characteristics remain similar to the current implementation
