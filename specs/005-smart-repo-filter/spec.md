# Feature Specification: Smart Repository Filtering

**Feature Branch**: `005-smart-repo-filter`
**Created**: 2025-11-29
**Status**: Draft
**Input**: User description: "Smart Repository Filtering: Filter repositories by recent activity using GitHub Search API to show only repos with pushes in the analysis period"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Filter Repositories by Recent Activity (Priority: P1)

As a user analyzing GitHub repositories, I want to automatically filter out inactive repositories so that I only analyze repos that have actual activity in my analysis timeframe, saving time and getting relevant results.

**Why this priority**: This is the core value proposition - avoiding wasted analysis time on inactive repositories. With 100+ repos, analyzing only the ~20-30 with recent activity provides significant time savings and more focused results.

**Independent Test**: Select option [L] or [A] to list repositories, system shows activity statistics ("135 repos found, 28 with activity in last 30 days") and automatically filters to active repos only.

**Acceptance Scenarios**:

1. **Given** user selects [A] (all repos) or [L] (list repos), **When** repositories are fetched, **Then** system displays total count and active count based on analysis period (--days value)
2. **Given** user has 135 accessible repositories, **When** only 28 have been pushed to in the last 30 days, **Then** system shows "135 repos found, 28 with activity in last 30 days"
3. **Given** active filtering is applied, **When** analysis proceeds, **Then** only repositories with recent activity are analyzed

---

### User Story 2 - Organization Repository Filtering (Priority: P2)

As a user analyzing organization repositories, I want to filter organization repos by recent activity so that I can focus analysis on actively maintained projects within the organization.

**Why this priority**: Organizations often have many archived or inactive repositories. Filtering saves significant time when analyzing large organizations.

**Independent Test**: Select option [O], enter organization name, system shows activity statistics for that organization's repositories.

**Acceptance Scenarios**:

1. **Given** user selects [O] and enters an organization name, **When** org repos are fetched, **Then** system shows total org repos and count with recent activity
2. **Given** organization has 50 repos but only 12 have activity in analysis period, **Then** system displays "50 org repos found, 12 with activity in last N days"
3. **Given** user confirms selection, **When** analysis runs, **Then** only active org repos are analyzed

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

- What happens when no repositories have activity in the analysis period? System shows warning: "⚠️ No repositories have been pushed to in the last N days." and offers options: [1] Include all repos, [2] Adjust timeframe, [3] Cancel.
- What happens when GitHub Search API rate limit is exceeded? System shows warning: "⚠️ Search API rate limit exceeded. Showing all repositories without activity filter. Try again in X seconds." and falls back to unfiltered mode.
- How does system handle repositories with only non-push activity (issues, PRs)? System uses "pushed" date as the filter criterion since that indicates code changes.
- What happens when analysis period (--days) is very large (e.g., 365 days)? System still applies filter; most repos should have some activity over a year.
- What happens when Search API returns incomplete_results=true? System shows warning: "⚠️ Results may be incomplete due to API limitations."

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display repository activity statistics when listing repositories (total count vs active count)
- **FR-002**: System MUST filter repositories based on "pushed" date relative to the analysis period (--days parameter)
- **FR-003**: System MUST support activity filtering for personal repositories (options A, L)
- **FR-004**: System MUST support activity filtering for organization repositories (option O)
- **FR-005**: System MUST NOT apply activity filter to manually specified repositories (option S)
- **FR-006**: System MUST provide option to disable activity filtering when user wants all repos
- **FR-007**: System MUST display clear statistics format: "N repos found, M with activity in last X days"
- **FR-008**: System MUST handle API rate limits gracefully by falling back to unfiltered mode
- **FR-009**: System MUST warn user when zero repositories match the activity filter
- **FR-010**: System MUST use the --days parameter value to calculate the activity cutoff date

### Key Entities

- **Repository Activity Status**: Whether a repository has been pushed to within the analysis period
- **Activity Filter Settings**: User preference for filtering (enabled/disabled) and timeframe
- **Activity Statistics**: Counts of total vs active repositories for display purposes

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can identify active repositories within 5 seconds of requesting repository list
- **SC-002**: Analysis time reduced by filtering out inactive repos (e.g., analyzing 28 active repos instead of 135 total)
- **SC-003**: 100% of displayed statistics accurately reflect actual repository activity status
- **SC-004**: Users can override activity filter when needed without restarting the selection process
- **SC-005**: System handles organizations with 500+ repositories within 10 seconds response time

## Assumptions

- The GitHub Search API endpoint `/search/repositories` is available and provides `pushed` date filtering
- Search API has separate rate limits from the standard API (30 requests/minute for authenticated users)
- The "pushed" date is the most relevant indicator of repository activity for code analysis purposes
- Users typically want to focus on active repositories and will appreciate automatic filtering as the default behavior
