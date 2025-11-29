# Feature Specification: GitHub Repository Interactive Selection

**Feature Branch**: `004-github-repo-selection`
**Created**: 2025-11-29
**Status**: Draft
**Input**: User description: "Selezione interattiva repository GitHub: quando repos.txt è assente o vuoto, il sistema chiede all'utente se vuole (a) specificare repo manualmente, (b) analizzare tutti i propri repo personali, (c) analizzare tutti i repo di una organization specifica. Implementare API calls per listare repo utente e repo organization. Seguire lo stesso pattern di select_jira_projects per consistenza UX."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Interactive Repository Selection Menu (Priority: P1)

As a user without a repos.txt file, I want to be presented with options to select repositories interactively so that I can quickly choose which repositories to analyze without creating a configuration file.

**Why this priority**: This is the core functionality. Without the interactive menu, users with no repos.txt cannot use the tool for GitHub analysis.

**Independent Test**: Can be fully tested by removing repos.txt, running the analyzer with `--sources github`, and verifying the interactive menu appears with options A/S/O/L/Q.

**Acceptance Scenarios**:

1. **Given** repos.txt is missing, **When** I run the analyzer with GitHub source enabled, **Then** I see an interactive menu with options: [A] Analyze all my repos, [S] Specify manually, [O] Analyze organization repos, [L] Select from list, [Q] Quit
2. **Given** repos.txt exists but is empty, **When** I run the analyzer, **Then** I see the same interactive menu
3. **Given** repos.txt contains valid repositories, **When** I run the analyzer, **Then** no interactive menu appears and those repositories are used directly
4. **Given** I'm in non-interactive mode (piped input or --quiet without --repos), **When** repos.txt is missing, **Then** GitHub analysis is skipped with an informational log message (not an error)

---

### User Story 2 - List and Select Personal Repositories (Priority: P2)

As a user, I want to see a list of all my personal GitHub repositories so that I can select which ones to analyze without remembering exact names.

**Why this priority**: Personal repos are the most common use case. Users typically want to analyze their own repositories.

**Independent Test**: Can be tested by selecting option [A] or [L] and verifying all personal repositories are listed with correct names.

**Acceptance Scenarios**:

1. **Given** I select option [A] (all my repos), **When** the API call completes, **Then** all my public and private repositories are included for analysis
2. **Given** I select option [L] (select from list), **When** the list appears, **Then** I see all my repositories numbered with owner/name format
3. **Given** I have 50+ repositories, **When** the list appears, **Then** all repositories are shown (paginated API calls handle large accounts)
4. **Given** I select specific numbers from the list (e.g., "1,3,5" or "1-3"), **When** I confirm, **Then** only those repositories are analyzed

---

### User Story 3 - List and Select Organization Repositories (Priority: P3)

As a user who belongs to GitHub organizations, I want to select an organization and analyze its repositories so that I can generate reports for team projects.

**Why this priority**: Organization repos are a common enterprise use case, but secondary to personal repos.

**Independent Test**: Can be tested by selecting option [O], entering an organization name, and verifying org repos are listed.

**Acceptance Scenarios**:

1. **Given** I select option [O], **When** prompted for organization name, **Then** I can enter any organization name I have access to
2. **Given** I enter a valid organization name, **When** the API call completes, **Then** I see all repositories I can access in that organization
3. **Given** I enter an organization I don't have access to, **When** the API call fails, **Then** I see a clear error message and can try again or quit
4. **Given** the organization has 100+ repositories, **When** the list appears, **Then** all repositories are shown (paginated API calls)
5. **Given** I want to analyze all org repos, **When** I choose [A] after seeing the list, **Then** all listed org repos are included

---

### User Story 4 - Manual Repository Specification (Priority: P4)

As a user who knows exactly which repositories I want, I want to type repository names directly so that I can quickly specify them without browsing lists.

**Why this priority**: Power users prefer direct input. This provides a quick path for experienced users.

**Independent Test**: Can be tested by selecting option [S] and entering comma-separated repository names.

**Acceptance Scenarios**:

1. **Given** I select option [S], **When** prompted, **Then** I can enter repository names in `owner/repo` format, comma-separated
2. **Given** I enter "owner/repo1, owner/repo2", **When** I confirm, **Then** those exact repositories are used for analysis
3. **Given** I enter an invalid repository format, **When** validation runs, **Then** I see a warning about invalid entries and can correct or continue
4. **Given** I enter a mix of valid and invalid repos, **When** I confirm, **Then** only valid repos are used and I'm warned about invalid ones

---

### Edge Cases

- What happens when GitHub API rate limit is exceeded during repository listing?
  - Retry with exponential backoff (same pattern as existing GitHubClient), show wait time to user: "Rate limit exceeded. Waiting X seconds..."
- What happens when the user's token doesn't have repo read permissions?
  - Clear error message: "GitHub token requires 'repo' scope to list repositories. Please check your token permissions."
- What happens when user presses Ctrl+C or EOF during interactive menu?
  - Graceful exit with "GitHub analysis skipped." message, return empty list
- What happens when organization name contains special characters?
  - Validate organization name format (alphanumeric + hyphens, 1-39 chars, no leading/trailing hyphen) before API call, show: "Invalid organization name format."
- What happens in quiet mode (--quiet) without repos.txt?
  - Skip interactive prompts, log: "No repos.txt found. Skipping GitHub analysis in non-interactive mode."
- What happens when user has zero repositories?
  - Display: "No repositories found for your account." and return to menu or exit gracefully
- What happens when organization has zero repositories?
  - Display: "No repositories found in organization '{org}'." and allow retry or quit
- What happens when API authentication fails (invalid/expired token)?
  - Display: "GitHub authentication failed. Please verify your GITHUB_TOKEN." and exit with code 1
- What happens when network timeout occurs during API call?
  - Display: "Network timeout while connecting to GitHub API. Please check your connection." and allow retry
- What happens when selection numbers exceed list length?
  - Ignore invalid numbers, warn: "Selection '99' is out of range (1-N). Ignored.", continue with valid selections
- What happens with partial API response (some pages fetched, then error)?
  - Use already-fetched repositories, warn: "Warning: Could not fetch all repositories. Showing {N} of potentially more."

## Requirements *(mandatory)*

### Functional Requirements

**Interactive Selection Menu**
- **FR-001**: System MUST display interactive menu when repos.txt is missing or empty and GitHub source is enabled
- **FR-002**: System MUST offer options: [A] All personal repos, [S] Specify manually, [O] Organization repos, [L] Select from personal list, [Q] Quit/Skip
- **FR-003**: System MUST follow the same UX pattern as `select_jira_projects` for consistency
- **FR-004**: System MUST handle EOF/KeyboardInterrupt gracefully, returning empty repository list

**GitHub API Integration**
- **FR-005**: System MUST list all repositories for authenticated user via GET /user/repos API
- **FR-006**: System MUST list organization repositories via GET /orgs/{org}/repos API
- **FR-007**: System MUST handle pagination for users/orgs with many repositories (100+ repos)
- **FR-008**: System MUST respect existing rate limit handling from GitHubClient

**User Input Handling**
- **FR-009**: System MUST accept comma-separated repository names in `owner/repo` format for manual entry
- **FR-010**: System MUST accept number selection for list mode (e.g., "1,3,5" or "1-3" or "all")
- **FR-011**: System MUST validate repository name format before attempting analysis
- **FR-012**: System MUST warn about invalid entries but continue with valid ones

**Non-Interactive Mode**
- **FR-013**: System MUST skip interactive prompts in non-interactive mode (--quiet without explicit --repos)
- **FR-014**: System MUST log clear message when GitHub analysis is skipped due to missing repos.txt in non-interactive mode

### Key Entities

- **Repository**: Existing entity representing a GitHub repository (owner, name)
- **GitHubClient**: Extended to support list_user_repos() and list_org_repos(org_name) methods
- **RepositorySelection**: Enum or type representing selection mode (ALL_PERSONAL, ORGANIZATION, MANUAL, FROM_LIST)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users without repos.txt can see the interactive menu within 2 seconds of starting the tool; repository listing completes within 30 seconds total (including API calls)
- **SC-002**: Personal repository listing completes in under 10 seconds for users with up to 200 repositories
- **SC-003**: Organization repository listing completes in under 15 seconds for orgs with up to 500 repositories
- **SC-004**: All existing repos.txt functionality works identically (no regression)
- **SC-005**: Interactive selection UX mirrors Jira project selection (same menu patterns, keyboard shortcuts, error handling)
- **SC-006**: Non-interactive mode (--quiet) never blocks waiting for user input

## Assumptions

- GitHub token has `repo` scope to list private repositories
- User knows their organization names (system doesn't list user's organizations, user must enter org name)
- Repository listing returns repositories the user can access based on their token permissions
- Follow existing `select_jira_projects` pattern in `cli/main.py` for consistency
- API timeouts use existing GitHubClient configurable timeout (default: 30s per constitution)
- Performance thresholds (SC-002, SC-003) assume standard network conditions (< 200ms latency)

## Display Format

### Repository List Format
Each repository is displayed as:
```
  N. owner/repo-name         - Description (truncated to 50 chars)
  N. owner/private-repo      - [private] Description here
```

### Menu Prompt Format
```
Options:
  [A] Analyze ALL accessible repositories
  [S] Specify repository names manually (owner/repo format)
  [O] Analyze organization repositories
  [L] Select from list by number (e.g., 1,3,5 or 1-3)
  [Q] Quit/Skip GitHub analysis

Your choice [A/S/O/L/Q]:
```

## Validation Patterns

### Repository Name Format (FR-011)
- Pattern: `^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$`
- Valid: `owner/repo`, `my-org/my-repo`, `user123/project_v2`
- Invalid: `just-repo`, `owner/`, `/repo`

### Organization Name Format
- Pattern: `^[a-zA-Z0-9]([a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$`
- Rules: 1-39 characters, alphanumeric and hyphens only, cannot start/end with hyphen
- Valid: `myorg`, `my-organization`
- Invalid: `-invalid-`, `org--double`

### Selection Input Format (FR-010)
- Single number: `3`
- Comma-separated: `1,3,5`
- Range: `1-3`
- Mixed: `1,3-5,7`
- All: `all`

## Non-Functional Requirements

### Performance
- Menu display: < 2 seconds from tool start (SC-001)
- Personal repo listing: < 10 seconds for up to 200 repos (SC-002)
- Org repo listing: < 15 seconds for up to 500 repos (SC-003)
- Assumes standard network conditions (< 200ms latency to GitHub API)

### Security
- Token values MUST NOT be logged, printed, or exposed in error messages (constitution §II)
- Organization name input MUST be validated to prevent injection attacks
- API URLs MUST be constructed safely (no string concatenation with user input)

### Accessibility
- Menu output uses plain text, compatible with screen readers
- No ANSI color codes required; uses TerminalOutput for optional formatting
- All prompts are clear and self-explanatory

## Clarifications

### Session 2025-11-29

- Q: Per "personal repos", quali repository includere? → A: Owner + repos dove l'utente è collaborator diretto (affiliation=owner,collaborator)
