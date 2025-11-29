# Data Model: Smart Repository Filtering

**Feature**: 005-smart-repo-filter
**Date**: 2025-11-29

## Entities

### ActivityFilterSettings

Settings for repository activity filtering.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enabled` | `bool` | Yes | Whether activity filtering is active |
| `days` | `int` | Yes | Number of days to look back for activity |
| `cutoff_date` | `str` | Yes | ISO date string (YYYY-MM-DD) calculated from days |

**Validation Rules**:
- `days` must be positive integer (1-365)
- `cutoff_date` derived from `days`, not user-supplied

**Example**:
```python
{
    "enabled": True,
    "days": 30,
    "cutoff_date": "2025-10-30"
}
```

### ActivityStatistics

Statistics about repository activity for display.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `total_count` | `int` | Yes | Total repositories found |
| `active_count` | `int` | Yes | Repositories with recent activity |
| `days` | `int` | Yes | Analysis period in days |
| `source` | `str` | Yes | "personal", "organization", or "manual" |

**Derived Fields**:
- `inactive_count`: `total_count - active_count`
- `active_percentage`: `(active_count / total_count) * 100`

**Example**:
```python
{
    "total_count": 135,
    "active_count": 28,
    "days": 30,
    "source": "personal"
}
```

**Display Format** (FR-007):
```
135 repos found, 28 with activity in last 30 days
```

### RepositoryActivityInfo

Extended repository info with activity status.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `full_name` | `str` | Yes | Repository full name (owner/repo) |
| `pushed_at` | `str` | Yes | ISO 8601 timestamp of last push |
| `is_active` | `bool` | Yes | Whether pushed_at is within cutoff |
| `private` | `bool` | No | Whether repository is private |
| `description` | `str` | No | Repository description |

**Validation Rules**:
- `full_name` must match pattern `^[a-zA-Z0-9.][a-zA-Z0-9._-]*/[a-zA-Z0-9.][a-zA-Z0-9._-]*$`
- `pushed_at` must be valid ISO 8601 timestamp

**Example**:
```python
{
    "full_name": "owner/repo",
    "pushed_at": "2025-11-28T10:30:00Z",
    "is_active": True,
    "private": False,
    "description": "A sample repository"
}
```

### SearchResult

GitHub Search API response structure.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `total_count` | `int` | Yes | Total matching repositories |
| `incomplete_results` | `bool` | Yes | Whether results are partial |
| `items` | `list[dict]` | Yes | Repository objects |

**State Transitions**:
- `incomplete_results=True` → Show warning to user
- `total_count > 1000` → Results truncated (Search API limit)

## Relationships

```
ActivityFilterSettings
        │
        │ configures
        ▼
┌───────────────────┐
│ select_github_repos() │
└───────────────────┘
        │
        │ produces
        ▼
ActivityStatistics ◄────── RepositoryActivityInfo[]
        │                          │
        │ displays                 │ filters to
        ▼                          ▼
"N repos, M active"          Active repos list
```

## State Machine: Filter Toggle

```
                    ┌─────────────────┐
                    │ Filter Enabled  │ (default)
                    │  (active only)  │
                    └────────┬────────┘
                             │
              user selects "include inactive"
                             │
                             ▼
                    ┌─────────────────┐
                    │ Filter Disabled │
                    │   (all repos)   │
                    └────────┬────────┘
                             │
                user selects "filter active"
                             │
                             ▼
                    ┌─────────────────┐
                    │ Filter Enabled  │
                    └─────────────────┘
```

## Data Flow

### Personal Repositories ([A]/[L])

```
1. Call list_user_repos()
   └── Returns: list[dict] with pushed_at

2. Calculate cutoff_date from --days

3. For each repo:
   └── is_active = parse(pushed_at) >= cutoff_date

4. Build ActivityStatistics
   └── total_count = len(repos)
   └── active_count = len([r for r in repos if r.is_active])

5. Display stats
   └── "135 repos found, 28 with activity in last 30 days"

6. Return filtered list (if filter enabled)
```

### Organization Repositories ([O])

```
1. Build search query
   └── q = f"org:{org_name}+pushed:>{cutoff_date}"

2. Call search_repos(query)
   └── Returns: SearchResult

3. Build ActivityStatistics from response
   └── active_count = len(items)
   └── total_count = fetch separately or estimate

4. Display stats

5. Return search items (already filtered)
```

## Integration Points

### Existing Code to Modify

| File | Function | Change |
|------|----------|--------|
| `api/client.py` | new `search_repos()` | Add Search API method |
| `cli/main.py` | `select_github_repos()` | Add activity filtering |
| `cli/main.py` | `_handle_option_a()` | Add stats display |
| `cli/main.py` | `_handle_option_l()` | Add stats display |
| `cli/main.py` | `_handle_option_o()` | Use Search API |

### New Functions Required

| Location | Function | Signature |
|----------|----------|-----------|
| `api/client.py` | `search_repos` | `(query: str, per_page: int = 100) -> SearchResult` |
| `cli/main.py` | `filter_by_activity` | `(repos: list[dict], days: int) -> tuple[list[dict], ActivityStatistics]` |
| `cli/main.py` | `display_activity_stats` | `(stats: ActivityStatistics) -> None` |
| `cli/main.py` | `get_cutoff_date` | `(days: int) -> str` |
