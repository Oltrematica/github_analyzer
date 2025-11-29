# Data Model: Jira Quality Metrics Export

**Feature**: 003-jira-quality-metrics
**Date**: 2025-11-28

## Entities

### IssueMetrics

Extended issue data with calculated quality metrics. Wraps existing `JiraIssue` dataclass.

```python
@dataclass
class IssueMetrics:
    """Calculated quality metrics for a single Jira issue.

    Attributes:
        issue: Original JiraIssue data
        cycle_time_days: Days from created to resolution (None if unresolved)
        aging_days: Days from created to now (None if resolved)
        comments_count: Total number of comments
        description_quality_score: 0-100 score based on length/AC/formatting
        acceptance_criteria_present: True if AC patterns detected
        comment_velocity_hours: Hours from created to first comment (None if no comments)
        silent_issue: True if no comments exist
        same_day_resolution: True if resolved on creation date
        cross_team_score: 0-100 based on distinct comment authors
        reopen_count: Number of times reopened (0 if not trackable)
    """
    issue: JiraIssue
    cycle_time_days: float | None
    aging_days: float | None
    comments_count: int
    description_quality_score: int
    acceptance_criteria_present: bool
    comment_velocity_hours: float | None
    silent_issue: bool
    same_day_resolution: bool
    cross_team_score: int
    reopen_count: int
```

**Validation Rules**:
- `cycle_time_days`: Must be >= 0 if present; negative values logged as warning and set to None
- `aging_days`: Must be >= 0; calculated only for unresolved issues
- `description_quality_score`: Must be 0-100 inclusive
- `cross_team_score`: Must be 0-100 inclusive
- `reopen_count`: Must be >= 0

**Derived From**:
- `issue.created`, `issue.resolution_date` → `cycle_time_days`, `same_day_resolution`
- `issue.created`, `datetime.now()` → `aging_days`
- `issue.description` → `description_quality_score`, `acceptance_criteria_present`
- `comments` list → `comments_count`, `comment_velocity_hours`, `silent_issue`, `cross_team_score`
- Changelog API → `reopen_count`

---

### ProjectMetrics

Aggregated metrics for a single project.

```python
@dataclass
class ProjectMetrics:
    """Aggregated quality metrics for a Jira project.

    Attributes:
        project_key: Jira project key (e.g., PROJ)
        total_issues: Total issues in export
        resolved_count: Issues with resolution_date
        unresolved_count: Issues without resolution_date
        avg_cycle_time_days: Mean cycle time for resolved issues
        median_cycle_time_days: Median cycle time for resolved issues
        bug_count: Issues with type "Bug"
        bug_ratio_percent: (bug_count / total_issues) * 100
        same_day_resolution_rate_percent: (same_day / resolved) * 100
        avg_description_quality: Mean description_quality_score
        silent_issues_ratio_percent: (silent / total) * 100
        avg_comments_per_issue: Mean comments_count
        avg_comment_velocity_hours: Mean comment_velocity for non-silent issues
        reopen_rate_percent: (reopened / resolved) * 100
    """
    project_key: str
    total_issues: int
    resolved_count: int
    unresolved_count: int
    avg_cycle_time_days: float | None
    median_cycle_time_days: float | None
    bug_count: int
    bug_ratio_percent: float
    same_day_resolution_rate_percent: float
    avg_description_quality: float
    silent_issues_ratio_percent: float
    avg_comments_per_issue: float
    avg_comment_velocity_hours: float | None
    reopen_rate_percent: float
```

**Validation Rules**:
- All percentage fields: 0.0-100.0 inclusive
- `avg_*` fields: None if no data points available
- Division by zero: Return 0.0 for ratios, None for averages

---

### PersonMetrics

Aggregated metrics for a single assignee.

```python
@dataclass
class PersonMetrics:
    """Aggregated quality metrics for a Jira assignee.

    Attributes:
        assignee_name: Display name of assignee
        wip_count: Count of open (unresolved) assigned issues
        resolved_count: Count of resolved assigned issues
        total_assigned: Total issues assigned
        avg_cycle_time_days: Mean cycle time for their resolved issues
        bug_count_assigned: Bugs assigned to this person
    """
    assignee_name: str
    wip_count: int
    resolved_count: int
    total_assigned: int
    avg_cycle_time_days: float | None
    bug_count_assigned: int
```

**Validation Rules**:
- `assignee_name`: Must not be empty string; issues without assignee are excluded
- `wip_count` + `resolved_count` = `total_assigned`

---

### TypeMetrics

Aggregated metrics per issue type.

```python
@dataclass
class TypeMetrics:
    """Aggregated quality metrics for a Jira issue type.

    Attributes:
        issue_type: Issue type name (Bug, Story, Task, etc.)
        count: Total issues of this type
        resolved_count: Resolved issues of this type
        avg_cycle_time_days: Mean cycle time for resolved issues of this type
        bug_resolution_time_avg: Same as avg_cycle_time_days when type is Bug (None otherwise)
    """
    issue_type: str
    count: int
    resolved_count: int
    avg_cycle_time_days: float | None
    bug_resolution_time_avg: float | None  # Only populated for Bug type
```

**Validation Rules**:
- `issue_type`: Must not be empty string
- `bug_resolution_time_avg`: Only non-None when `issue_type == "Bug"`

---

## Relationships

```
JiraIssue (existing)
    │
    ├──[1:1]──> IssueMetrics (calculated wrapper)
    │               │
    │               ├──[many:1]──> ProjectMetrics (aggregated by project_key)
    │               │
    │               ├──[many:1]──> PersonMetrics (aggregated by assignee)
    │               │
    │               └──[many:1]──> TypeMetrics (aggregated by issue_type)
    │
    └──[1:many]──> JiraComment (existing)
```

---

## State Transitions

Issues don't have explicit state machine in this feature. The `reopen_count` metric tracks transitions through resolution states:

```
Created → In Progress → Done (resolution_date set)
                          │
                          ├──[reopen]──> In Progress (reopen_count++)
                          │                   │
                          │                   └──> Done (resolution_date updated)
                          │
                          └──[stays resolved]
```

**Reopen Detection Logic**:
1. Fetch changelog for issue
2. Find status field changes where `fromString` is in Done category
3. Check if `toString` is NOT in Done category
4. Each such transition = 1 reopen

---

## Configuration Constants

```python
# Description Quality Score weights (FR-004)
QUALITY_WEIGHT_LENGTH = 40      # Max points for description length
QUALITY_WEIGHT_AC = 40          # Points for acceptance criteria presence
QUALITY_WEIGHT_FORMAT = 20      # Max points for formatting (headers + lists)
QUALITY_LENGTH_THRESHOLD = 100  # Chars needed for full length score

# Cross-team Score scale (FR-009)
CROSS_TEAM_SCALE = {
    1: 25,
    2: 50,
    3: 75,
    4: 90,
    # 5+ authors = 100
}

# Acceptance Criteria detection patterns (FR-005)
AC_PATTERNS = [
    r'(?i)\bgiven\b.*\bwhen\b.*\bthen\b',
    r'(?i)^#+\s*acceptance\s+criteria',
    r'(?i)^ac\s*:',
    r'(?i)acceptance\s+criteria\s*:',
    r'^\s*[-*]\s*\[\s*[x ]?\s*\]',
]

# Done status categories for reopen detection
DONE_STATUSES = {'Done', 'Closed', 'Resolved', 'Complete', 'Completed'}
```
