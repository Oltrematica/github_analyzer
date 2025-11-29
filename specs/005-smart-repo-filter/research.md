# Research: Smart Repository Filtering

**Feature**: 005-smart-repo-filter
**Date**: 2025-11-29

## GitHub Search API for Repository Activity

### Decision
Use GitHub Search API endpoint `/search/repositories` with `pushed:>YYYY-MM-DD` qualifier to filter repositories by recent activity.

### Rationale
- Search API provides server-side filtering, reducing data transfer
- `pushed` date is the most reliable indicator of code activity
- Separate rate limit pool (30 req/min) from core API (5000 req/hour)
- Returns repository metadata including `pushed_at` timestamp for verification

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| Client-side filtering | Requires fetching ALL repos first, then filtering - slow for 500+ repos |
| Events API | Returns all events, not just pushes; higher API cost; complex parsing |
| GraphQL API | More complex setup; rate limits based on points; not in current codebase |

## Search API Endpoint Details

### Endpoint
```
GET /search/repositories
```

### Query Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `q` | Yes | Search query with qualifiers |
| `sort` | No | Sort field: `stars`, `forks`, `help-wanted-issues`, `updated` |
| `order` | No | `asc` or `desc` (default) |
| `per_page` | No | Results per page (max 100) |
| `page` | No | Page number for pagination |

### Query Qualifiers for Activity Filtering

| Qualifier | Example | Description |
|-----------|---------|-------------|
| `user:USERNAME` | `user:octocat` | Repos owned by user |
| `org:ORGNAME` | `org:github` | Repos in organization |
| `pushed:>YYYY-MM-DD` | `pushed:>2025-10-30` | Pushed after date |
| `pushed:>=YYYY-MM-DD` | `pushed:>=2025-10-30` | Pushed on or after date |

### Example Queries

```bash
# User repos pushed in last 30 days
/search/repositories?q=user:octocat+pushed:>2025-10-30

# Organization repos pushed in last 30 days
/search/repositories?q=org:github+pushed:>2025-10-30

# Combined with affiliation (user's accessible repos)
# NOTE: Search API doesn't support affiliation - need alternative approach
```

### Response Structure

```json
{
  "total_count": 28,
  "incomplete_results": false,
  "items": [
    {
      "id": 12345,
      "full_name": "owner/repo",
      "private": false,
      "pushed_at": "2025-11-28T10:30:00Z",
      "description": "Repository description"
    }
  ]
}
```

### Rate Limits

| Limit Type | Authenticated | Unauthenticated |
|------------|---------------|-----------------|
| Requests/minute | 30 | 10 |
| Results/query | 1000 | 1000 |

**Important**: Search API has separate rate limit from REST API core.

## Implementation Strategy

### Decision
Hybrid approach: Use Search API for org repos, client-side filtering for personal repos.

### Rationale
- Search API `user:` qualifier only returns repos OWNED by user
- Personal repos include collaborator access (not searchable via Search API)
- Org repos are searchable via `org:` qualifier

### Implementation Details

1. **Personal Repos ([A] and [L] options)**:
   - Fetch all repos via `list_user_repos()` (existing method)
   - Filter client-side by comparing `pushed_at` to cutoff date
   - Display: "135 repos found, 28 with activity in last 30 days"

2. **Organization Repos ([O] option)**:
   - Use Search API: `q=org:ORGNAME+pushed:>YYYY-MM-DD`
   - More efficient for large orgs (500+ repos)
   - Fallback to client-side if Search API rate limited

3. **Manual Specification ([S] option)**:
   - No filtering applied (per FR-005)
   - User explicitly chose repos

### Date Calculation

```python
from datetime import datetime, timedelta

def get_activity_cutoff_date(days: int) -> str:
    """Calculate ISO date for activity filter.

    Args:
        days: Number of days to look back

    Returns:
        ISO date string: YYYY-MM-DD
    """
    cutoff = datetime.now() - timedelta(days=days)
    return cutoff.strftime("%Y-%m-%d")
```

## Error Handling

### Decision
Graceful fallback to unfiltered mode on Search API failures.

### Rationale
- Per FR-008: System MUST handle API rate limits gracefully
- User should not be blocked from analysis due to Search API issues
- Core functionality (list repos) uses different rate limit pool

### Fallback Scenarios

| Error | Response |
|-------|----------|
| Search API rate limit (403) | Show warning, proceed with all repos unfiltered |
| Search API server error (5xx) | Retry once, then fallback to unfiltered |
| Incomplete results flag | Show warning, results may be partial |

### User Feedback

```
⚠️  Search API rate limit exceeded. Showing all repositories without activity filter.
    Try again in 60 seconds for filtered results.
```

## Performance Considerations

### Decision
Paginate Search API results, limit to 1000 repos max.

### Rationale
- GitHub Search API returns max 1000 results per query
- Most orgs have fewer than 1000 active repos
- Pagination via `page` parameter (100 per page max)

### Performance Targets

| Metric | Target | How Achieved |
|--------|--------|--------------|
| Stats display time | <5 seconds | Single Search API call for counts |
| Filter 500+ repos | <5 seconds | Server-side filtering via Search API |
| Memory usage | <10MB | Stream pagination, don't load all at once |

## Testing Strategy

### Unit Tests
- Mock Search API responses
- Test date calculation
- Test query string construction
- Test rate limit handling

### Integration Tests
- Test filter toggle (enable/disable)
- Test zero results handling
- Test fallback behavior
- Test stats display format

## Dependencies

### Existing (no new dependencies)
- `urllib` / `requests` - HTTP client (already in use)
- `datetime` - Date calculations (standard library)
- `json` - Response parsing (already in use)

### New Methods Required

| Location | Method | Purpose |
|----------|--------|---------|
| `api/client.py` | `search_repos()` | Generic search method |
| `api/client.py` | `search_active_repos()` | Activity-filtered search |
| `cli/main.py` | `filter_repos_by_activity()` | Client-side filtering |
| `cli/main.py` | `display_activity_stats()` | Show "N of M repos active" |
