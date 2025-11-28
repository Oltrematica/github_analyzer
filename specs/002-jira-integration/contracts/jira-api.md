# Jira REST API Contract

**Feature**: 002-jira-integration
**Date**: 2025-11-28
**API Versions**: v2 (Server/Data Center), v3 (Cloud)

## Authentication

### Request Header

```http
Authorization: Basic {base64(email:api_token)}
Content-Type: application/json
```

### Example

```python
import base64

credentials = base64.b64encode(f"{email}:{api_token}".encode()).decode()
headers = {
    "Authorization": f"Basic {credentials}",
    "Content-Type": "application/json"
}
```

## Endpoints

### 1. Search Issues (JQL)

**Purpose**: Retrieve issues matching time filter

**Request**:
```http
POST /rest/api/{version}/search
Content-Type: application/json

{
  "jql": "project IN (PROJ1, PROJ2) AND updated >= \"2025-11-21\"",
  "startAt": 0,
  "maxResults": 100,
  "fields": [
    "summary",
    "description",
    "status",
    "issuetype",
    "priority",
    "assignee",
    "reporter",
    "created",
    "updated",
    "resolutiondate",
    "project"
  ]
}
```

**Response** (200 OK):
```json
{
  "startAt": 0,
  "maxResults": 100,
  "total": 250,
  "issues": [
    {
      "key": "PROJ-123",
      "fields": {
        "summary": "Issue title",
        "description": {
          "type": "doc",
          "content": [...]
        },
        "status": {
          "name": "In Progress"
        },
        "issuetype": {
          "name": "Bug"
        },
        "priority": {
          "name": "High"
        },
        "assignee": {
          "displayName": "John Doe",
          "accountId": "abc123"
        },
        "reporter": {
          "displayName": "Jane Smith",
          "accountId": "xyz789"
        },
        "created": "2025-11-20T10:30:00.000+0000",
        "updated": "2025-11-28T14:15:00.000+0000",
        "resolutiondate": null,
        "project": {
          "key": "PROJ"
        }
      }
    }
  ]
}
```

**Error Responses**:
- `400 Bad Request`: Invalid JQL syntax
- `401 Unauthorized`: Invalid credentials
- `403 Forbidden`: No permission to access project

---

### 2. Get Issue Comments

**Purpose**: Retrieve comments for a specific issue

**Request**:
```http
GET /rest/api/{version}/issue/{issueKey}/comment?startAt=0&maxResults=100
```

**Response** (200 OK):
```json
{
  "startAt": 0,
  "maxResults": 100,
  "total": 5,
  "comments": [
    {
      "id": "10001",
      "author": {
        "displayName": "John Doe",
        "accountId": "abc123"
      },
      "created": "2025-11-21T09:00:00.000+0000",
      "body": {
        "type": "doc",
        "content": [
          {
            "type": "paragraph",
            "content": [
              {"type": "text", "text": "This is a comment"}
            ]
          }
        ]
      }
    }
  ]
}
```

**Note**: In API v2, `body` is a plain string. In API v3, it's ADF (Atlassian Document Format).

---

### 3. List Projects

**Purpose**: Get all accessible projects (for interactive selection)

**Request**:
```http
GET /rest/api/{version}/project
```

**Response** (200 OK):
```json
[
  {
    "key": "PROJ",
    "name": "Project Name",
    "projectTypeKey": "software"
  },
  {
    "key": "DEV",
    "name": "Development",
    "projectTypeKey": "software"
  }
]
```

---

### 4. Get Server Info (Version Detection)

**Purpose**: Verify connection and detect API version

**Request**:
```http
GET /rest/api/{version}/serverInfo
```

**Response** (200 OK):
```json
{
  "baseUrl": "https://company.atlassian.net",
  "version": "1001.0.0",
  "deploymentType": "Cloud",
  "buildNumber": 100000
}
```

**Version Detection Logic**:
- If `deploymentType` == "Cloud" → use API v3
- Otherwise → use API v2

## Rate Limiting

### Cloud (Atlassian)

- HTTP 429 response when exceeded
- `Retry-After` header indicates wait time (seconds)
- Limits vary by plan (typically ~100 req/min for free tier)

### Server/Data Center

- No default rate limiting
- May be configured by admin
- Same 429 handling if configured

## Error Handling Contract

### Error Response Format

```json
{
  "errorMessages": ["Error description"],
  "errors": {
    "fieldName": "Field-specific error"
  }
}
```

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response |
| 400 | Bad Request | Log error, fail operation |
| 401 | Unauthorized | Fail with auth error message |
| 403 | Forbidden | Log warning, skip resource |
| 404 | Not Found | Log warning, skip resource |
| 429 | Rate Limited | Retry with backoff |
| 500 | Server Error | Retry with backoff |
| 503 | Service Unavailable | Retry with backoff |

## Module Interface Contract

### JiraClient Class

```python
class JiraClient:
    """Jira REST API client with pagination and rate limiting."""

    def __init__(self, config: JiraConfig) -> None:
        """Initialize client with configuration."""

    def test_connection(self) -> bool:
        """Test authentication and connectivity."""

    def get_projects(self) -> list[JiraProject]:
        """Get all accessible projects."""

    def search_issues(
        self,
        project_keys: list[str],
        since_date: datetime,
    ) -> Iterator[JiraIssue]:
        """Search issues with time filter. Yields issues (handles pagination)."""

    def get_comments(self, issue_key: str) -> list[JiraComment]:
        """Get all comments for an issue."""
```

### JiraExporter Class

```python
class JiraExporter:
    """Export Jira data to CSV files."""

    def __init__(self, output_dir: str) -> None:
        """Initialize exporter with output directory."""

    def export_issues(self, issues: Iterable[JiraIssue]) -> Path:
        """Export issues to jira_issues_export.csv."""

    def export_comments(self, comments: Iterable[JiraComment]) -> Path:
        """Export comments to jira_comments_export.csv."""
```

## ADF (Atlassian Document Format) Handling

### Input (API v3)

```json
{
  "type": "doc",
  "content": [
    {
      "type": "paragraph",
      "content": [
        {"type": "text", "text": "Hello "},
        {"type": "text", "text": "world", "marks": [{"type": "strong"}]}
      ]
    },
    {
      "type": "bulletList",
      "content": [
        {
          "type": "listItem",
          "content": [
            {
              "type": "paragraph",
              "content": [{"type": "text", "text": "Item 1"}]
            }
          ]
        }
      ]
    }
  ]
}
```

### Output (Plain Text)

```
Hello world
- Item 1
```

### Conversion Rules

1. Recursively traverse `content` arrays
2. Extract `text` from text nodes
3. Add newlines between block elements (paragraph, listItem)
4. Prefix list items with `- `
5. Ignore formatting marks (bold, italic, etc.)
