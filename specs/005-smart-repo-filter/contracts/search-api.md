# API Contract: GitHub Search Repositories

**Feature**: 005-smart-repo-filter
**Date**: 2025-11-29

## Endpoint

```
GET https://api.github.com/search/repositories
```

## Authentication

```
Authorization: token {GITHUB_TOKEN}
Accept: application/vnd.github.v3+json
```

## Request

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `q` | string | Yes | - | Search query with qualifiers |
| `sort` | string | No | best match | `stars`, `forks`, `help-wanted-issues`, `updated` |
| `order` | string | No | `desc` | `asc` or `desc` |
| `per_page` | integer | No | 30 | Results per page (1-100) |
| `page` | integer | No | 1 | Page number |

### Query Qualifiers

| Qualifier | Format | Example | Description |
|-----------|--------|---------|-------------|
| `user` | `user:USERNAME` | `user:octocat` | Repos owned by user |
| `org` | `org:ORGNAME` | `org:github` | Repos in organization |
| `pushed` | `pushed:>YYYY-MM-DD` | `pushed:>2025-10-30` | Last push after date |
| `pushed` | `pushed:>=YYYY-MM-DD` | `pushed:>=2025-10-30` | Last push on or after date |

### Example Request

```bash
curl -H "Authorization: token ghp_xxxx" \
  "https://api.github.com/search/repositories?q=org:github+pushed:>2025-10-30&per_page=100"
```

## Response

### Success (200 OK)

```json
{
  "total_count": 28,
  "incomplete_results": false,
  "items": [
    {
      "id": 123456,
      "node_id": "MDEwOlJlcG9zaXRvcnkxMjM0NTY=",
      "name": "repo-name",
      "full_name": "owner/repo-name",
      "private": false,
      "owner": {
        "login": "owner",
        "id": 789
      },
      "html_url": "https://github.com/owner/repo-name",
      "description": "Repository description",
      "pushed_at": "2025-11-28T10:30:00Z",
      "created_at": "2020-01-15T08:00:00Z",
      "updated_at": "2025-11-28T10:30:00Z",
      "default_branch": "main"
    }
  ]
}
```

### Response Fields (items)

| Field | Type | Always Present | Description |
|-------|------|----------------|-------------|
| `id` | integer | Yes | Unique repository ID |
| `full_name` | string | Yes | Full name (owner/repo) |
| `private` | boolean | Yes | Whether repo is private |
| `pushed_at` | string | Yes | ISO 8601 last push timestamp |
| `description` | string | No | May be null |
| `owner.login` | string | Yes | Owner username |

### Error Responses

#### 401 Unauthorized
```json
{
  "message": "Bad credentials",
  "documentation_url": "https://docs.github.com/rest"
}
```

#### 403 Rate Limit Exceeded
```json
{
  "message": "API rate limit exceeded",
  "documentation_url": "https://docs.github.com/rest/overview/resources-in-the-rest-api#rate-limiting"
}
```

**Headers**:
```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1701234567
```

#### 422 Validation Failed
```json
{
  "message": "Validation Failed",
  "errors": [
    {
      "resource": "Search",
      "field": "q",
      "code": "missing"
    }
  ]
}
```

## Rate Limits

| Type | Limit | Window |
|------|-------|--------|
| Authenticated | 30 requests | per minute |
| Unauthenticated | 10 requests | per minute |
| Max results | 1000 items | per query |

**Headers in Response**:
```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 29
X-RateLimit-Reset: 1701234567
X-RateLimit-Resource: search
```

## Pagination

When `total_count` exceeds `per_page`, paginate using `page` parameter:

```
Page 1: ?q=org:github+pushed:>2025-10-30&per_page=100&page=1
Page 2: ?q=org:github+pushed:>2025-10-30&per_page=100&page=2
...
```

**Maximum**: 1000 total results (10 pages at 100 per page).

## Python Client Implementation

```python
def search_repos(
    self,
    query: str,
    per_page: int = 100,
    max_results: int = 1000,
) -> dict:
    """Search repositories using GitHub Search API.

    Args:
        query: Search query with qualifiers (e.g., "org:github+pushed:>2025-10-30")
        per_page: Results per page (1-100)
        max_results: Maximum total results to fetch

    Returns:
        Dict with total_count, incomplete_results, and items list

    Raises:
        RateLimitError: If search rate limit exceeded
        APIError: On other API errors
    """
    all_items = []
    page = 1

    while len(all_items) < max_results:
        url = f"{GITHUB_API_BASE}/search/repositories"
        params = {"q": query, "per_page": per_page, "page": page}

        data, headers = self._request_with_retry(url, params)

        if data is None:
            break

        all_items.extend(data.get("items", []))

        if len(data.get("items", [])) < per_page:
            break

        page += 1

    return {
        "total_count": data.get("total_count", len(all_items)),
        "incomplete_results": data.get("incomplete_results", False),
        "items": all_items[:max_results]
    }
```

## Test Fixtures

### Mock Response: Active Repos

```python
MOCK_SEARCH_RESPONSE = {
    "total_count": 2,
    "incomplete_results": False,
    "items": [
        {
            "id": 1,
            "full_name": "org/active-repo-1",
            "private": False,
            "pushed_at": "2025-11-28T10:00:00Z",
            "description": "Recently active"
        },
        {
            "id": 2,
            "full_name": "org/active-repo-2",
            "private": True,
            "pushed_at": "2025-11-25T15:30:00Z",
            "description": "Also active"
        }
    ]
}
```

### Mock Response: Rate Limited

```python
MOCK_RATE_LIMIT_RESPONSE = {
    "status_code": 403,
    "headers": {
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": "1701234567"
    },
    "body": {
        "message": "API rate limit exceeded"
    }
}
```

### Mock Response: Empty Results

```python
MOCK_EMPTY_RESPONSE = {
    "total_count": 0,
    "incomplete_results": False,
    "items": []
}
```
