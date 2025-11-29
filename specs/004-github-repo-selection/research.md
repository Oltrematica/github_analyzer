# Research: GitHub Repository Interactive Selection

**Feature**: 004-github-repo-selection
**Date**: 2025-11-29

## Research Tasks Completed

### 1. GitHub API: List Authenticated User Repositories

**Endpoint**: `GET /user/repos`

**Decision**: Use `affiliation=owner,collaborator` parameter to list personal repos per spec clarification.

**Rationale**:
- The spec clarifies that "personal repos" should include repos where user is owner + repos where user is collaborator (not organization member repos)
- This aligns with user expectation of "my repos" without including all org repos they can access

**Parameters Identified**:
| Parameter | Values | Default | Purpose |
|-----------|--------|---------|---------|
| `affiliation` | `owner`, `collaborator`, `organization_member` (comma-separated) | `owner,collaborator,organization_member` | Filter by relationship |
| `visibility` | `all`, `public`, `private` | `all` | Filter by visibility |
| `sort` | `created`, `updated`, `pushed`, `full_name` | `full_name` | Sort order |
| `direction` | `asc`, `desc` | `asc` when sort=full_name | Sort direction |
| `per_page` | 1-100 | 30 | Results per page |
| `page` | positive integer | 1 | Page number |

**Implementation**: Use `affiliation=owner,collaborator` for FR-005 (list personal repos).

### 2. GitHub API: List Organization Repositories

**Endpoint**: `GET /orgs/{org}/repos`

**Decision**: Use `type=all` to list all accessible org repositories.

**Rationale**:
- User wants to see all repos they can access in an organization
- The `type=all` default includes public, private, forks, sources, member repos

**Parameters Identified**:
| Parameter | Values | Default | Purpose |
|-----------|--------|---------|---------|
| `type` | `all`, `public`, `private`, `forks`, `sources`, `member` | `all` | Repository type filter |
| `sort` | `created`, `updated`, `pushed`, `full_name` | `created` | Sort order |
| `direction` | `asc`, `desc` | `desc` (except full_name) | Sort direction |
| `per_page` | 1-100 | 30 | Results per page |
| `page` | positive integer | 1 | Page number |

**Implementation**: Use `type=all` for FR-006 (list org repos).

### 3. Pagination Strategy

**Decision**: Use existing `GitHubClient.paginate()` method with automatic page handling.

**Rationale**:
- Existing client already handles pagination efficiently
- Uses `per_page=100` (configured in AnalyzerConfig) for fewer API calls
- Respects `max_pages` configuration to prevent runaway pagination

**Alternatives Considered**:
- Manual pagination: Rejected - would duplicate existing logic
- Link header parsing: Rejected - current simple page iteration is sufficient

### 4. Rate Limit Handling

**Decision**: Use existing rate limit handling from `GitHubClient`.

**Rationale**:
- `GitHubClient` already implements rate limit detection and `RateLimitError`
- Exponential backoff retry is already implemented for transient failures
- Per spec edge case: show wait time to user when rate limited

**Implementation**: Catch `RateLimitError` in selection flow, display remaining wait time.

### 5. UX Pattern: Select from List

**Decision**: Follow exact pattern from `select_jira_projects` for consistency (FR-003).

**Rationale**:
- Spec explicitly requires UX consistency with Jira project selection
- Existing `parse_project_selection()` helper can parse "1,3,5" and "1-3" syntax
- Existing `format_project_list()` pattern can be adapted for repos

**Pattern to Follow** (from `cli/main.py:464-582`):
1. Load from file first (repos.txt)
2. If missing/empty, fetch available options from API
3. Display numbered list
4. Show menu: [A] All, [S] Specify, [O] Organization, [L] List, [Q] Quit
5. Handle EOF/KeyboardInterrupt gracefully
6. Validate input, retry on invalid

### 6. Organization Name Validation

**Decision**: Validate org name format before API call.

**Rationale**:
- Per spec edge case: "Validate organization name format before API call, reject invalid names"
- GitHub org names: alphanumeric + hyphens, 1-39 chars, cannot start/end with hyphen

**Pattern**: `^[a-zA-Z0-9]([a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$`

### 7. Repository Name Format

**Decision**: Use `owner/repo` format consistently.

**Rationale**:
- Existing repos.txt uses this format
- FR-009 requires comma-separated `owner/repo` for manual entry
- API returns `full_name` field in this format

## Summary of Decisions

| Topic | Decision | Spec Requirement |
|-------|----------|------------------|
| Personal repos API | `GET /user/repos?affiliation=owner,collaborator` | FR-005, Clarification |
| Org repos API | `GET /orgs/{org}/repos?type=all` | FR-006 |
| Pagination | Use existing `paginate()` method | FR-007 |
| Rate limits | Use existing handler, show wait time | Edge case |
| UX pattern | Follow `select_jira_projects` exactly | FR-003 |
| Org name validation | Regex pattern before API call | Edge case |
| Repo format | `owner/repo` (full_name) | FR-009, FR-011 |
