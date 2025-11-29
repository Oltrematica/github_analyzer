# CSV Export Schemas: Jira Quality Metrics

**Feature**: 003-jira-quality-metrics
**Date**: 2025-11-28

## 1. Extended Issue Export

**File**: `jira_issues_export.csv` (modified)

### Schema

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| key | string | Issue key | `PROJ-123` |
| summary | string | Issue title | `Fix login bug` |
| description | string | Issue description (plain text) | `Users cannot...` |
| status | string | Current status | `Done` |
| issue_type | string | Issue type | `Bug` |
| priority | string | Priority (empty if unset) | `High` |
| assignee | string | Assignee name (empty if unassigned) | `John Doe` |
| reporter | string | Reporter name | `Jane Smith` |
| created | ISO8601 | Creation timestamp | `2025-11-01T10:00:00+00:00` |
| updated | ISO8601 | Last update timestamp | `2025-11-28T14:30:00+00:00` |
| resolution_date | ISO8601 | Resolution timestamp (empty if unresolved) | `2025-11-15T16:00:00+00:00` |
| project_key | string | Parent project key | `PROJ` |
| **cycle_time_days** | float | Days from created to resolved (empty if unresolved) | `14.25` |
| **aging_days** | float | Days since created (empty if resolved) | `27.5` |
| **comments_count** | int | Number of comments | `5` |
| **description_quality_score** | int | Quality score 0-100 | `75` |
| **acceptance_criteria_present** | boolean | AC detected | `true` |
| **comment_velocity_hours** | float | Hours to first comment (empty if no comments) | `2.5` |
| **silent_issue** | boolean | No comments exist | `false` |
| **same_day_resolution** | boolean | Resolved same day as created | `false` |
| **cross_team_score** | int | Collaboration score 0-100 | `75` |
| **reopen_count** | int | Times reopened | `0` |

**Notes**:
- Columns 1-12: Existing (unchanged order and format)
- Columns 13-22: NEW (appended)
- Boolean values: lowercase `true`/`false`
- Empty values: empty string (not `null` or `N/A`)
- Floats: 2 decimal places

### Example

```csv
key,summary,description,status,issue_type,priority,assignee,reporter,created,updated,resolution_date,project_key,cycle_time_days,aging_days,comments_count,description_quality_score,acceptance_criteria_present,comment_velocity_hours,silent_issue,same_day_resolution,cross_team_score,reopen_count
PROJ-123,Fix login bug,Users cannot login when...,Done,Bug,High,John Doe,Jane Smith,2025-11-01T10:00:00+00:00,2025-11-15T16:00:00+00:00,2025-11-15T16:00:00+00:00,PROJ,14.25,,5,75,true,2.50,false,false,75,0
PROJ-124,Add dark mode,As a user I want...,In Progress,Story,Medium,Jane Smith,John Doe,2025-11-20T09:00:00+00:00,2025-11-28T11:00:00+00:00,,PROJ,,8.08,0,45,false,,true,false,0,0
```

---

## 2. Project Metrics Summary

**File**: `jira_project_metrics.csv` (new)

### Schema

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| project_key | string | Project key | `PROJ` |
| total_issues | int | Total issues | `150` |
| resolved_count | int | Resolved issues | `120` |
| unresolved_count | int | Unresolved issues | `30` |
| avg_cycle_time_days | float | Mean cycle time | `7.50` |
| median_cycle_time_days | float | Median cycle time | `5.00` |
| bug_count | int | Bug issues | `45` |
| bug_ratio_percent | float | Bug percentage | `30.00` |
| same_day_resolution_rate_percent | float | Same-day resolution % | `15.00` |
| avg_description_quality | float | Mean quality score | `68.50` |
| silent_issues_ratio_percent | float | Silent issues % | `12.00` |
| avg_comments_per_issue | float | Mean comments | `3.20` |
| avg_comment_velocity_hours | float | Mean time to first comment | `4.50` |
| reopen_rate_percent | float | Reopen percentage | `5.00` |

### Example

```csv
project_key,total_issues,resolved_count,unresolved_count,avg_cycle_time_days,median_cycle_time_days,bug_count,bug_ratio_percent,same_day_resolution_rate_percent,avg_description_quality,silent_issues_ratio_percent,avg_comments_per_issue,avg_comment_velocity_hours,reopen_rate_percent
PROJ,150,120,30,7.50,5.00,45,30.00,15.00,68.50,12.00,3.20,4.50,5.00
DEV,80,60,20,10.25,8.00,20,25.00,10.00,72.00,8.00,4.50,3.00,2.50
```

---

## 3. Person Metrics Summary

**File**: `jira_person_metrics.csv` (new)

### Schema

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| assignee_name | string | Person's display name | `John Doe` |
| wip_count | int | Open assigned issues | `5` |
| resolved_count | int | Resolved assigned issues | `25` |
| total_assigned | int | Total assigned issues | `30` |
| avg_cycle_time_days | float | Mean cycle time | `6.75` |
| bug_count_assigned | int | Bugs assigned | `8` |

### Example

```csv
assignee_name,wip_count,resolved_count,total_assigned,avg_cycle_time_days,bug_count_assigned
John Doe,5,25,30,6.75,8
Jane Smith,3,40,43,5.50,12
Bob Wilson,8,15,23,9.00,5
```

---

## 4. Type Metrics Summary

**File**: `jira_type_metrics.csv` (new)

### Schema

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| issue_type | string | Issue type name | `Bug` |
| count | int | Total issues of type | `45` |
| resolved_count | int | Resolved issues of type | `40` |
| avg_cycle_time_days | float | Mean cycle time | `4.50` |
| bug_resolution_time_avg | float | Bug-specific avg (empty for non-bugs) | `4.50` |

### Example

```csv
issue_type,count,resolved_count,avg_cycle_time_days,bug_resolution_time_avg
Bug,45,40,4.50,4.50
Story,60,50,8.25,
Task,35,25,3.00,
Epic,10,5,45.00,
```

---

## Validation Rules (All Files)

1. **Encoding**: UTF-8
2. **Line endings**: LF (Unix style)
3. **Header**: First row contains column names
4. **Quoting**: RFC 4180 - quote fields containing commas, quotes, or newlines
5. **Empty values**: Empty string (no quotes needed)
6. **Booleans**: `true` or `false` (lowercase)
7. **Floats**: 2 decimal places, no thousands separator
8. **Dates**: ISO 8601 format with timezone
9. **Strings**: No length limit; newlines converted to spaces
