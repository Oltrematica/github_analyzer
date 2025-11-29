# Feature Specification: Smart Repository Filtering

**Feature Branch**: `005-smart-repo-filter`
**Created**: 2025-11-29
**Status**: Draft
**Input**: User description: "Smart Repository Filtering: Filter repositories by recent activity using GitHub Search API to show only repos with pushes in the analysis period"

## Glossary

| Term | Definition |
|------|------------|
| **Active repository** | A repository where `pushed_at` timestamp is greater than or equal to the cutoff date |
| **Inactive repository** | A repository where `pushed_at` timestamp is before the cutoff date |
| **Cutoff date** | Calculated as `today - days` (exclusive boundary: repos pushed ON cutoff date are included) |
| **pushed_at** | ISO 8601 timestamp (e.g., `2025-11-28T10:30:00Z`) indicating the last push to any branch |
| **Activity filter** | The mechanism that shows only active repositories by default |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Filter Repositories by Recent Activity (Priority: P1)

As a user analyzing GitHub repositories, I want to automatically filter out inactive repositories so that I only analyze repos that have actual activity in my analysis timeframe, saving time and getting relevant results.

**Why this priority**: This is the core value proposition - avoiding wasted analysis time on inactive repositories. With 100+ repos, analyzing only the ~20-30 with recent activity provides significant time savings and more focused results. Quantified benefit: analyzing 28 repos instead of 135 saves ~80% analysis time.

**Independent Test**: Select option [L] or [A] to list repositories, system shows activity statistics ("135 repos found, 28 with activity in last 30 days") and automatically filters to active repos only.

**Acceptance Scenarios**:

1. **Given** user selects [A] (all repos) or [L] (list repos), **When** repositories are fetched, **Then** system displays total count and active count based on analysis period (--days value)
2. **Given** user has 135 accessible repositories, **When** only 28 have been pushed to in the last 30 days, **Then** system shows "135 repos found, 28 with activity in last 30 days"
3. **Given** active filtering is applied, **When** analysis proceeds, **Then** only repositories with recent activity are analyzed
4. **Given** user sees confirmation prompt "Proceed with N active repositories? [Y/n/all]", **When** user enters "Y" or presses Enter, **Then** analysis proceeds with filtered repos
5. **Given** confirmation prompt is displayed, **When** user enters "n", **Then** selection is cancelled and user returns to main menu

---

### User Story 2 - Organization Repository Filtering (Priority: P2)

As a user analyzing organization repositories, I want to filter organization repos by recent activity so that I can focus analysis on actively maintained projects within the organization.

**Why this priority**: Organizations often have many archived or inactive repositories. Filtering saves significant time when analyzing large organizations. Quantified benefit: for a 500-repo org with 50 active repos, saves ~90% analysis time.

**Independent Test**: Select option [O], enter organization name, system shows activity statistics for that organization's repositories.

**Acceptance Scenarios**:

1. **Given** user selects [O] and enters an organization name, **When** org repos are fetched, **Then** system shows total org repos and count with recent activity
2. **Given** organization has 50 repos but only 12 have activity in analysis period, **Then** system displays "50 org repos found, 12 with activity in last N days"
3. **Given** user confirms selection, **When** analysis runs, **Then** only active org repos are analyzed
4. **Given** user sees org confirmation prompt, **When** user enters "all", **Then** all org repos are included regardless of activity

---

### User Story 3 - Override Activity Filter (Priority: P3)

As a user who needs to analyze specific repositories regardless of activity, I want the option to include inactive repositories so that I can analyze repos that may not have recent pushes but are still relevant.

**Why this priority**: Some users may need to analyze archived or dormant repositories for auditing, historical analysis, or compliance purposes.

**Independent Test**: User can toggle activity filter off to include all repositories regardless of push date.

**Acceptance Scenarios**:

1. **Given** user sees activity statistics, **When** user wants to include inactive repos, **Then** system provides option to disable filter
2. **Given** filter is disabled, **When** analysis proceeds, **Then** all selected repositories are analyzed regardless of activity
3. **Given** manual specification [S] option is used, **When** user enters repos manually, **Then** no activity filter is applied (manual selection implies intentional choice)

---

### Edge Cases

1. **Zero active repositories**: When no repositories have activity in the analysis period, system shows warning: "⚠️ No repositories have been pushed to in the last N days." and offers options: [1] Include all repos, [2] Adjust timeframe, [3] Cancel.

2. **Search API rate limit (HTTP 403)**: System shows warning: "⚠️ Search API rate limit exceeded. Showing all repositories without activity filter. Try again in X seconds." and falls back to unfiltered mode, proceeding with all repositories.

3. **Search API server errors (HTTP 5xx)**: System retries once after 2 seconds. If retry fails, falls back to unfiltered mode with warning: "⚠️ Search API unavailable. Showing all repositories without activity filter."

4. **Network timeout during Search API call**: After 30-second timeout, system falls back to unfiltered mode with warning: "⚠️ Search API timeout. Showing all repositories without activity filter."

5. **Authentication failure during search (HTTP 401)**: System shows error: "❌ GitHub authentication failed. Check your token and try again." and aborts operation.

6. **Non-push activity only**: System uses `pushed_at` date as the filter criterion since that indicates code changes. Repositories with only issues/PRs but no pushes are considered inactive.

7. **Very large analysis period (365+ days)**: System still applies filter; most repos should have some activity over a year. No special handling needed.

8. **Search API incomplete_results=true**: System shows warning: "⚠️ Results may be incomplete due to API limitations. Some active repositories may not be shown."

9. **Invalid menu selection**: System shows "Invalid option. Please enter A, S, O, L, or Q:" and re-prompts without exiting.

10. **User cancels during confirmation prompt (Ctrl+C)**: System catches KeyboardInterrupt, displays "Selection cancelled.", and returns to main menu gracefully.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display repository activity statistics when listing repositories (total count vs active count)
- **FR-002**: System MUST filter repositories based on `pushed_at` field (ISO 8601 timestamp, e.g., `2025-11-28T10:30:00Z`) relative to the analysis period (--days parameter). Filtering logic: `repo.pushed_at >= cutoff_date` where `cutoff_date = today - days`
- **FR-003**: System MUST support activity filtering for personal repositories via options [A] and [L]:
  - [A]: Fetch all accessible repos via `list_user_repos()`, filter client-side by `pushed_at`, display stats, show confirmation prompt
  - [L]: Same as [A], but display numbered list for selection after filtering
- **FR-004**: System MUST support activity filtering for organization repositories via option [O]:
  - Use Search API query: `org:{org_name} pushed:>{cutoff_date}` (date format: `YYYY-MM-DD`)
  - Fetch total org count via `list_org_repos()` for stats comparison
  - Display stats and confirmation prompt matching [A]/[L] pattern
- **FR-005**: System MUST NOT apply activity filter to manually specified repositories (option [S]) - manual selection implies intentional choice
- **FR-006**: System MUST provide option to disable activity filtering via "all" response to confirmation prompt "Proceed with N active repositories? [Y/n/all]":
  - "Y" or Enter: proceed with active repos only
  - "n": cancel and return to menu
  - "all": proceed with all repos (filter disabled)
- **FR-007**: System MUST display statistics in exact format: `"{total} repos found, {active} with activity in last {days} days"` (e.g., "135 repos found, 28 with activity in last 30 days")
- **FR-008**: System MUST handle API rate limits gracefully:
  - On HTTP 403 (rate limit): show warning with remaining cooldown time, fall back to unfiltered mode
  - On HTTP 5xx (server error): retry once after 2 seconds, then fall back to unfiltered mode
  - On timeout (30s): fall back to unfiltered mode with warning
  - Fallback means: proceed with all repositories without activity filter
- **FR-009**: System MUST warn user when zero repositories match the activity filter and offer options: [1] Include all repos, [2] Adjust timeframe, [3] Cancel
- **FR-010**: System MUST use the --days parameter value to calculate the activity cutoff date. When --days is not provided, default value from config (typically 30) is used

### Key Entities

- **Repository Activity Status**: Whether a repository has been pushed to within the analysis period
- **Activity Filter Settings**: User preference for filtering (enabled/disabled) and timeframe
- **Activity Statistics**: Counts of total vs active repositories for display purposes

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Activity statistics (total count, active count) MUST be displayed within 5 seconds of user selecting [A], [L], or [O] option. Measurement starts when user presses Enter after menu selection.
- **SC-002**: Analysis time reduction: when filtering is applied, only active repos are analyzed. Example: analyzing 28 active repos instead of 135 total saves ~80% analysis time.
- **SC-003**: Statistics accuracy: displayed counts MUST match actual repository activity status. Test by comparing `active_count` against manual count of repos where `pushed_at >= cutoff_date`.
- **SC-004**: Filter override: users can select "all" at confirmation prompt to include inactive repos without returning to main menu.
- **SC-005**: Large organization support: system MUST complete activity filtering for organizations with 500+ repositories within 10 seconds. This includes Search API pagination (up to 5 pages of 100 results each).
- **SC-006**: Memory efficiency: system MUST NOT load more than 1000 repositories into memory at once. Use pagination/streaming for larger result sets.

### Performance Requirements

| Scenario | Max Response Time | Memory Limit |
|----------|-------------------|--------------|
| Personal repos (<100) | 3 seconds | 10 MB |
| Personal repos (100-500) | 5 seconds | 25 MB |
| Organization repos (<100) | 3 seconds | 10 MB |
| Organization repos (500+) | 10 seconds | 50 MB |
| Search API pagination | 2 seconds per page | N/A |

## API Constraints

### GitHub Search API Limits

| Constraint | Value | Impact |
|------------|-------|--------|
| Rate limit (authenticated) | 30 requests/minute | May trigger fallback to unfiltered mode |
| Rate limit (unauthenticated) | 10 requests/minute | Not supported - auth required |
| Max results per query | 1000 repositories | Orgs with >1000 active repos will be truncated |
| Max results per page | 100 repositories | Requires pagination for large result sets |
| Rate limit pool | Separate from REST API | Search limits don't affect core API usage |

### Search API Query Qualifiers

| Qualifier | Format | Example |
|-----------|--------|---------|
| `org:` | `org:{org_name}` | `org:microsoft` |
| `user:` | `user:{username}` | `user:octocat` |
| `pushed:` | `pushed:>{YYYY-MM-DD}` | `pushed:>2025-10-30` |
| Combined | `{qualifier}+{qualifier}` | `org:github+pushed:>2025-10-30` |

## Dependencies

### Internal Dependencies (existing codebase)

| Dependency | Location | Purpose | Validated |
|------------|----------|---------|-----------|
| `GitHubClient` | `src/github_analyzer/api/client.py` | Base API client class | ✅ Exists |
| `list_user_repos()` | `GitHubClient` method | Fetch user's accessible repos | ✅ Exists |
| `list_org_repos()` | `GitHubClient` method | Fetch org repos for total count | ✅ Exists |
| `select_github_repos()` | `src/github_analyzer/cli/main.py` | Interactive repo selection (Feature 004) | ✅ Exists |
| `--days` parameter | CLI/config | Analysis period configuration | ✅ Exists |

### External Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| GitHub REST API | v3 | Repository listing |
| GitHub Search API | v3 | Activity-filtered search |
| Python datetime | stdlib | Date calculations |

## Assumptions

- The GitHub Search API endpoint `/search/repositories` is available and provides `pushed` date filtering via `pushed:>YYYY-MM-DD` qualifier
- Search API has separate rate limits from the standard API (30 requests/minute for authenticated users vs 5000 requests/hour for REST API)
- The `pushed_at` field is the most relevant indicator of repository activity for code analysis purposes (indicates actual code changes, not just issues/PRs)
- Users typically want to focus on active repositories and will appreciate automatic filtering as the default behavior
- The existing `list_org_repos()` method in GitHubClient is available for fetching total org repo count (dependency on existing codebase)

## Design Decisions

### Hybrid Filtering Approach

**Decision**: Use client-side filtering for personal repos, Search API for organization repos.

**Rationale**:
- Search API `user:` qualifier only returns repos OWNED by user, not collaborator access
- Personal repos via `list_user_repos()` include all accessible repos (owned + collaborator)
- Organization repos are efficiently searchable via `org:` qualifier
- This approach provides accurate results while leveraging API efficiency where possible

**Alternatives Rejected**:
1. Search API only: Would miss collaborator repos for personal selection
2. Client-side only: Would be slow for large organizations (500+ repos)
3. GraphQL API: More complex setup, point-based rate limits, not in current codebase

### Default Behavior

**Decision**: Activity filter is ON by default for [A], [L], [O] options; OFF for [S] option.

**Rationale**:
- Users selecting many repos typically want active ones (primary use case)
- Manual specification [S] implies intentional choice of specific repos
- Users can easily override with "all" response if needed
- This may surprise users expecting to see all repos - mitigated by clear stats display showing what's filtered
