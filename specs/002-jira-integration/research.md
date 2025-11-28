# Research: Jira Integration

**Feature**: 002-jira-integration
**Date**: 2025-11-28

## Research Topics

### 1. Jira REST API Authentication

**Decision**: Basic Authentication with email + API token

**Rationale**:
- Standard method for Jira Cloud (API v3) and Server/Data Center (API v2)
- API tokens are generated from Atlassian account settings (Cloud) or user profile (Server)
- Base64 encoding of `email:api_token` in Authorization header
- Simpler than OAuth 2.0 for CLI tools; no browser redirect needed

**Alternatives Considered**:
- OAuth 2.0 (3LO): More complex, requires browser flow, overkill for CLI tool
- Personal Access Tokens (PAT) only: Server/Data Center specific, not Cloud compatible

**Implementation Notes**:
```python
# Header format
Authorization: Basic base64(email:api_token)
```

### 2. Jira REST API Version Differences

**Decision**: Support both API v2 (Server/Data Center) and v3 (Cloud) with auto-detection

**Rationale**:
- Cloud instances use `*.atlassian.net` domain → API v3
- Self-hosted instances use custom domain → API v2
- Most endpoints are compatible; differences mainly in response format for user references

**Key Differences**:
| Aspect | API v2 (Server) | API v3 (Cloud) |
|--------|-----------------|----------------|
| User reference | `name` field | `accountId` field |
| Base URL | `https://jira.company.com/rest/api/2/` | `https://company.atlassian.net/rest/api/3/` |
| Auth header | Same Basic Auth | Same Basic Auth |

**Auto-detection Logic**:
```python
def detect_api_version(url: str) -> str:
    if ".atlassian.net" in url:
        return "3"  # Cloud
    return "2"  # Server/Data Center
```

### 3. JQL Query for Time-Filtered Issues

**Decision**: Use `updated >= "YYYY-MM-DD"` JQL clause

**Rationale**:
- `updated` captures all changes including status transitions, comments, field edits
- More comprehensive than `created` which only catches new issues
- JQL date format is `YYYY-MM-DD` or relative (`-7d`)
- Aligns with existing GitHub `--days` parameter semantics

**Query Pattern**:
```
project IN (PROJ1, PROJ2) AND updated >= "2025-11-21"
```

**Alternatives Considered**:
- `created >= date`: Misses updated existing issues
- `updated >= -7d`: Relative format works but absolute is more predictable

### 4. Pagination Strategy

**Decision**: Offset-based pagination with `startAt` and `maxResults`

**Rationale**:
- Jira search API uses offset pagination (not cursor-based)
- Default `maxResults` is 50; max is typically 100
- Must iterate until `startAt + results.length >= total`

**Implementation Pattern**:
```python
start_at = 0
max_results = 100
all_issues = []

while True:
    response = search_issues(jql, start_at, max_results)
    all_issues.extend(response["issues"])

    if start_at + len(response["issues"]) >= response["total"]:
        break
    start_at += max_results
```

### 5. Rate Limiting

**Decision**: Exponential backoff with 429 detection

**Rationale**:
- Jira Cloud: Rate limits vary by plan; 429 response when exceeded
- Jira Server: Typically no rate limiting unless configured
- Same pattern as existing GitHub client for consistency

**Implementation**:
- Check for HTTP 429 response
- Read `Retry-After` header if present
- Exponential backoff: 1s, 2s, 4s, 8s, max 60s
- Max 5 retries before failing

### 6. Issue Fields to Extract

**Decision**: Core fields only (per clarification session)

**Fields**:
- `key`: Issue key (e.g., PROJ-123)
- `fields.summary`: Issue title
- `fields.description`: Issue description (ADF in v3, wiki markup in v2)
- `fields.status.name`: Current status
- `fields.issuetype.name`: Issue type (Bug, Story, Task, etc.)
- `fields.priority.name`: Priority level
- `fields.assignee.displayName` / `accountId`: Assigned user
- `fields.reporter.displayName` / `accountId`: Reporter
- `fields.created`: Creation timestamp (ISO 8601)
- `fields.updated`: Last update timestamp (ISO 8601)
- `fields.resolutiondate`: Resolution timestamp (null if unresolved)

**Custom Fields**: Explicitly out of scope for v1.

### 7. Comments Retrieval

**Decision**: Fetch comments via issue endpoint expansion or separate API call

**Rationale**:
- Comments can be included via `expand=renderedFields,changelog` on issue fetch
- Or retrieved separately via `/rest/api/3/issue/{issueKey}/comment`
- Separate call is cleaner and allows pagination for issues with many comments

**Endpoint**:
```
GET /rest/api/3/issue/{issueKey}/comment?startAt=0&maxResults=100
```

**Comment Fields**:
- `id`: Comment ID
- `author.displayName`: Author name
- `created`: Timestamp
- `body`: Comment content (ADF in v3, wiki markup in v2)

### 8. Project Discovery

**Decision**: Interactive prompt when `jira_projects.txt` missing (per clarification)

**Implementation Flow**:
1. Check for `jira_projects.txt`
2. If exists and non-empty → use listed projects
3. If missing/empty → prompt user:
   - Option A: Fetch all accessible projects via `/rest/api/3/project`
   - Option B: Enter project keys manually (comma-separated)

**Project List Endpoint**:
```
GET /rest/api/3/project?expand=description
```

### 9. Description Format Handling

**Decision**: Convert ADF (Atlassian Document Format) to plain text for CSV export

**Rationale**:
- Jira API v3 returns descriptions in ADF JSON format
- CSV export needs plain text
- Simple recursive text extraction from ADF nodes

**ADF Structure**:
```json
{
  "type": "doc",
  "content": [
    {
      "type": "paragraph",
      "content": [
        {"type": "text", "text": "Hello world"}
      ]
    }
  ]
}
```

**Extraction**: Recursively collect all `text` values from ADF nodes.

### 10. Error Handling Strategy

**Decision**: Consistent with existing GitHub error handling

**Error Categories**:
- `JiraAuthenticationError`: Invalid credentials (401)
- `JiraPermissionError`: No access to project/issue (403)
- `JiraNotFoundError`: Project/issue doesn't exist (404)
- `JiraRateLimitError`: Rate limit exceeded (429)
- `JiraAPIError`: Other API errors (5xx, etc.)

**Behavior**:
- Auth errors: Fail fast with clear message
- Permission/Not found: Log warning, continue with other projects
- Rate limit: Retry with backoff
- Server errors: Retry with backoff, fail after max retries

## Resolved NEEDS CLARIFICATION

All technical unknowns have been resolved through research. No blocking questions remain.

## Next Steps

Proceed to Phase 1: Design & Contracts
