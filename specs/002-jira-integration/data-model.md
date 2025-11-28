# Data Model: Jira Integration

**Feature**: 002-jira-integration
**Date**: 2025-11-28

## Entities

### JiraConfig

Configuration for Jira API access. Extends the existing configuration pattern.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `jira_url` | `str` | Yes | Jira instance URL (e.g., `https://company.atlassian.net`) |
| `jira_email` | `str` | Yes | User email for authentication |
| `jira_api_token` | `str` | Yes | API token (never logged) |
| `jira_projects_file` | `str` | No | Path to projects file (default: `jira_projects.txt`) |
| `api_version` | `str` | No | Auto-detected: `"2"` (Server) or `"3"` (Cloud) |

**Validation Rules**:
- `jira_url`: Valid HTTPS URL
- `jira_email`: Valid email format
- `jira_api_token`: Non-empty string (format not validated - varies by instance)

**Source**: Environment variables `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`

---

### JiraProject

Represents a Jira project.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `key` | `str` | Yes | Project key (e.g., `PROJ`, `DEV`) |
| `name` | `str` | No | Project display name |
| `description` | `str` | No | Project description |

**Validation Rules**:
- `key`: Matches pattern `^[A-Z][A-Z0-9_]*$`

---

### JiraIssue

Represents a Jira issue with core fields.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `key` | `str` | Yes | Issue key (e.g., `PROJ-123`) |
| `summary` | `str` | Yes | Issue title/summary |
| `description` | `str` | No | Issue description (plain text) |
| `status` | `str` | Yes | Current status name |
| `issue_type` | `str` | Yes | Type (Bug, Story, Task, etc.) |
| `priority` | `str` | No | Priority name (may be null) |
| `assignee` | `str` | No | Assignee display name (null if unassigned) |
| `reporter` | `str` | Yes | Reporter display name |
| `created` | `datetime` | Yes | Creation timestamp (UTC) |
| `updated` | `datetime` | Yes | Last update timestamp (UTC) |
| `resolution_date` | `datetime` | No | Resolution timestamp (null if unresolved) |
| `project_key` | `str` | Yes | Parent project key |

**Derived Fields**:
- `is_resolved`: `bool` = `resolution_date is not None`
- `age_days`: `int` = days since `created`

---

### JiraComment

Represents a comment on a Jira issue.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Comment ID |
| `issue_key` | `str` | Yes | Parent issue key |
| `author` | `str` | Yes | Author display name |
| `created` | `datetime` | Yes | Comment timestamp (UTC) |
| `body` | `str` | Yes | Comment content (plain text) |

---

### DataSource (Enum)

Enumeration of supported data sources.

| Value | Description |
|-------|-------------|
| `GITHUB` | GitHub repositories |
| `JIRA` | Jira projects |

---

### ExtractionConfig

Unified configuration for multi-source extraction.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sources` | `list[DataSource]` | Yes | Platforms to query |
| `days` | `int` | Yes | Analysis period |
| `output_dir` | `str` | Yes | Output directory for CSV files |
| `github_config` | `AnalyzerConfig` | No | GitHub config (if GitHub enabled) |
| `jira_config` | `JiraConfig` | No | Jira config (if Jira enabled) |

**Invariants**:
- At least one source must be configured
- Each source requires its corresponding config

## Relationships

```
ExtractionConfig
├── has-many → DataSource
├── has-one → AnalyzerConfig (optional)
└── has-one → JiraConfig (optional)

JiraConfig
└── references → JiraProject (via jira_projects.txt)

JiraProject
└── has-many → JiraIssue

JiraIssue
├── belongs-to → JiraProject
└── has-many → JiraComment

JiraComment
└── belongs-to → JiraIssue
```

## State Transitions

### JiraIssue Lifecycle (from Jira's perspective)

```
[Open] → [In Progress] → [In Review] → [Done]
                ↓                ↓
            [Blocked]      [Rejected]
```

Note: The analyzer captures the current state; it does not track transitions. State names are configurable per Jira project workflow.

## CSV Export Schemas

### jira_issues_export.csv

| Column | Type | Source Field |
|--------|------|--------------|
| `key` | string | `JiraIssue.key` |
| `summary` | string | `JiraIssue.summary` |
| `status` | string | `JiraIssue.status` |
| `issue_type` | string | `JiraIssue.issue_type` |
| `priority` | string | `JiraIssue.priority` |
| `assignee` | string | `JiraIssue.assignee` |
| `reporter` | string | `JiraIssue.reporter` |
| `created` | ISO 8601 | `JiraIssue.created` |
| `updated` | ISO 8601 | `JiraIssue.updated` |
| `resolution_date` | ISO 8601 | `JiraIssue.resolution_date` |
| `project_key` | string | `JiraIssue.project_key` |

### jira_comments_export.csv

| Column | Type | Source Field |
|--------|------|--------------|
| `issue_key` | string | `JiraComment.issue_key` |
| `author` | string | `JiraComment.author` |
| `created` | ISO 8601 | `JiraComment.created` |
| `body` | string | `JiraComment.body` |

## Data Volume Estimates

| Entity | Expected Volume | Storage Impact |
|--------|-----------------|----------------|
| JiraProject | 1-50 per instance | Negligible |
| JiraIssue | 100-10,000+ per extraction | ~1KB per issue |
| JiraComment | 0-50 per issue | ~500B per comment |

**Memory Considerations**:
- Issues are processed in batches (100 per API call)
- Comments are fetched per-issue, not bulk loaded
- CSV writing is streaming (no full dataset in memory)
