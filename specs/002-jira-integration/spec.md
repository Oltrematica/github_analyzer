# Feature Specification: Jira Integration & Multi-Platform Support

**Feature Branch**: `002-jira-integration`
**Created**: 2025-11-28
**Status**: Draft
**Input**: User description: "Integrazione API Jira: aggiungere supporto per estrarre issue Jira (con dati e commenti) per il periodo di tempo selezionato dall'utente. Include: client API Jira con autenticazione, estrazione issue/commenti/metadata, filtri temporali, esportazione unificata. Richiede anche rinominare l'entrypoint da github_analyzer.py a un nome più generale (es. dev_analyzer.py o project_analyzer.py) per riflettere il supporto multi-piattaforma."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Jira Issue Extraction with Time Filter (Priority: P1)

As a project manager or developer, I want to extract all Jira issues (including their details and comments) for a specific time period so that I can analyze team activity across both GitHub and Jira in a unified report.

**Why this priority**: This is the core functionality of the feature. Without the ability to extract Jira issues with temporal filtering, the integration provides no value.

**Independent Test**: Can be fully tested by configuring Jira credentials, specifying a date range, and running the extraction. The tool should produce a CSV file containing all issues updated within that period.

**Acceptance Scenarios**:

1. **Given** valid Jira credentials and a project key, **When** I run the analyzer with a 7-day time range, **Then** I receive all issues updated in the last 7 days with their key, summary, status, assignee, reporter, created date, updated date, and priority
2. **Given** valid Jira credentials, **When** I run the analyzer for a specific date range, **Then** only issues with `updated` date within that range are included
3. **Given** an issue with multiple comments, **When** the issue is extracted, **Then** all comments are included with author, timestamp, and content
4. **Given** a Jira project with 500+ issues matching the time filter, **When** I run the extraction, **Then** all issues are retrieved using pagination without data loss

---

### User Story 2 - Secure Jira Authentication (Priority: P2)

As a user, I want to configure my Jira credentials securely through environment variables so that my authentication details are never exposed in logs or command history.

**Why this priority**: Security is fundamental. Jira credentials (API tokens or personal access tokens) must be handled with the same care as GitHub tokens.

**Independent Test**: Can be fully tested by setting Jira environment variables and verifying authentication works without credential exposure.

**Acceptance Scenarios**:

1. **Given** `JIRA_URL`, `JIRA_EMAIL`, and `JIRA_API_TOKEN` environment variables are set, **When** I run the analyzer, **Then** the tool authenticates to Jira automatically
2. **Given** any Jira credential is missing, **When** I run the analyzer, **Then** Jira integration is skipped with a clear informational message (not an error, since Jira is optional)
3. **Given** invalid Jira credentials, **When** authentication fails, **Then** a clear error message appears without revealing the token value
4. **Given** any Jira API error, **When** the error is logged, **Then** no credential values appear in logs or error messages

---

### User Story 3 - Unified Multi-Platform Entrypoint (Priority: P3)

As a user, I want a single command-line tool that can analyze both GitHub and Jira data so that I have a unified workflow for extracting development metrics from multiple sources.

**Why this priority**: The unified entrypoint provides user experience improvements and reflects the tool's expanded capabilities, but the tool functions with separate invocations.

**Independent Test**: Can be tested by running the renamed tool with various combinations of configured platforms (GitHub only, Jira only, both).

**Acceptance Scenarios**:

1. **Given** the new entrypoint name, **When** I run `dev_analyzer.py`, **Then** the tool starts and shows available data sources based on configured credentials
2. **Given** only GitHub credentials configured, **When** I run the analyzer, **Then** only GitHub data is extracted without Jira-related errors
3. **Given** only Jira credentials configured, **When** I run the analyzer, **Then** only Jira data is extracted without GitHub-related errors
4. **Given** both GitHub and Jira credentials configured, **When** I run the analyzer, **Then** both data sources are extracted and exported

---

### User Story 4 - Jira Data Export (Priority: P4)

As a user, I want Jira data exported in CSV format consistent with the existing GitHub exports so that I can analyze all data using the same tools and workflows.

**Why this priority**: Export is essential for the feature to be useful, but it depends on extraction (P1) being implemented first.

**Independent Test**: Can be verified by running extraction and checking the output CSV files for correct structure and content.

**Acceptance Scenarios**:

1. **Given** extracted Jira issues, **When** export completes, **Then** a `jira_issues_export.csv` file is created with columns: key, summary, status, issue_type, priority, assignee, reporter, created, updated, resolution_date
2. **Given** extracted Jira comments, **When** export completes, **Then** a `jira_comments_export.csv` file is created with columns: issue_key, author, created, body
3. **Given** both GitHub and Jira data, **When** export completes, **Then** separate files are created for each platform maintaining existing GitHub export formats unchanged

---

### Edge Cases

- What happens when a Jira project key doesn't exist?
  - Clear error message identifying the invalid project key, continue with other valid projects
- What happens when Jira API rate limit is exceeded?
  - Automatic retry with exponential backoff (max 5 retries, 1s initial delay, 60s max delay), clear message to user about rate limiting
- What happens when Jira issue description or comments contain special characters (newlines, commas, quotes)?
  - Proper CSV escaping following RFC 4180 standards
- What happens when Jira is hosted on-premises vs Atlassian Cloud?
  - Support both with appropriate URL handling (Cloud uses `*.atlassian.net`, on-premises uses custom domain)
- What happens when time range spans across Jira server timezone vs local timezone?
  - Use UTC internally, accept ISO 8601 format for user input
- What happens when a Jira issue is moved between projects during the time range?
  - Include the issue based on its current project location, note original project if available in history

## Requirements *(mandatory)*

### Functional Requirements

**Jira Authentication**
- **FR-001**: System MUST read Jira credentials from environment variables: `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`
- **FR-002**: System MUST support both Atlassian Cloud and on-premises Jira Server/Data Center instances
- **FR-003**: System MUST NOT log, print, or expose Jira credentials in any output including error messages
- **FR-004**: System MUST gracefully skip Jira integration when credentials are not configured (informational message, not error)

**Jira Data Extraction**
- **FR-005**: System MUST extract issues using JQL queries filtered by update date within user-specified time range
- **FR-006**: System MUST retrieve issue core fields: key, summary, description, status, issue type, priority, assignee, reporter, created date, updated date, resolution date
- **FR-007**: System MUST retrieve all comments for each extracted issue including author, timestamp, and body
- **FR-008**: System MUST handle pagination for large result sets using maxResults=100 (Jira maximum)
- **FR-009**: System MUST read Jira project keys from `jira_projects.txt` file (one project key per line) if present
- **FR-009a**: If `jira_projects.txt` is missing or empty, system MUST prompt user interactively to choose between: (a) analyze all accessible projects, or (b) specify project keys manually
- **FR-010**: System MUST respect Jira API rate limits with automatic retry and exponential backoff (max 5 retries, 1s initial delay, 60s max delay)

**Data Export**
- **FR-011**: System MUST export Jira issues to `jira_issues_export.csv` with consistent column structure
- **FR-012**: System MUST export Jira comments to `jira_comments_export.csv` with issue key reference
- **FR-013**: System MUST properly escape CSV special characters per RFC 4180
- **FR-014**: Existing GitHub export formats MUST remain unchanged

**Multi-Platform Entrypoint**
- **FR-015**: Primary entrypoint MUST be renamed from `github_analyzer.py` to `dev_analyzer.py`
- **FR-016**: System MUST maintain backward compatibility wrapper at `github_analyzer.py` that redirects to the new entrypoint
- **FR-017**: CLI MUST support `--sources` flag to specify which platforms to query (github, jira, or both)
- **FR-018**: System MUST operate in single-platform mode when only one set of credentials is configured

**Input Validation**
- **FR-019**: System MUST validate Jira URL format (valid URL with https scheme)
- **FR-020**: System MUST validate Jira project keys match pattern `^[A-Z][A-Z0-9_]*$`
- **FR-021**: System MUST validate time range parameters are valid ISO 8601 dates

### Key Entities

- **JiraConfig**: Authentication and configuration including instance URL, user email, API token reference, and projects file path
- **JiraIssue**: Issue data including key, summary, description, status, type, priority, assignee, reporter, timestamps, resolution
- **JiraComment**: Comment data including parent issue key, author, timestamp, and body content
- **JiraProject**: Project identifier with key and optional metadata
- **DataSource**: Enumeration of available platforms (GitHub, Jira) with associated configuration
- **ExtractionConfig**: Unified configuration for time range, sources, and output settings

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can extract all Jira issues for a 30-day period in under 5 minutes for projects with up to 1000 issues
- **SC-002**: Jira credentials never appear in any log output, error messages, or console display
- **SC-003**: All existing GitHub functionality works identically after the entrypoint rename
- **SC-004**: CSV exports pass validation with standard CSV parsers without manual correction
- **SC-005**: Tool handles Jira API pagination correctly for result sets of 10,000+ issues
- **SC-006**: Both Atlassian Cloud and on-premises Jira instances authenticate successfully
- **SC-007**: Running with `--sources=github` produces identical output to the pre-integration version

## Clarifications

### Session 2025-11-28

- Q: Come vengono configurati i progetti Jira da analizzare? → A: File `jira_projects.txt` se presente; altrimenti prompt interattivo che chiede all'utente se analizzare tutti i progetti accessibili o specificarne alcuni.
- Q: Come gestire i custom fields Jira nell'export? → A: Solo campi core in v1; custom fields fuori scope per questa release.

## Assumptions

- Users have valid Jira API tokens (generated from Atlassian account settings for Cloud, or PAT for Server/Data Center)
- The tool will use Basic Authentication with email + API token, which is the standard method for Jira REST API
- Jira Cloud uses API v3, while Server/Data Center may use v2; the implementation will detect and adapt
- Custom fields are explicitly out of scope for v1; only core Jira fields will be exported
- The `--days` parameter will apply to both GitHub and Jira when extracting from multiple sources
- No Jira webhooks or real-time sync is needed; this is a batch extraction tool
- The `requests` library will be used for Jira API calls if available, with urllib fallback
