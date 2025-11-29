# Research: Jira Quality Metrics Export

**Feature**: 003-jira-quality-metrics
**Date**: 2025-11-28

## Research Tasks

### 1. Jira Changelog API for Reopen Detection (FR-022)

**Question**: How to detect issue reopens via Jira API?

**Decision**: Use issue changelog endpoint `/rest/api/3/issue/{issueKey}/changelog`

**Rationale**:
- Jira tracks all field changes in the changelog, including status transitions
- A "reopen" is detected when status changes FROM a "Done" category TO a non-Done category
- Both Cloud (v3) and Server (v2) support this endpoint
- Changelog includes: field name, from value, to value, timestamp, author

**API Details**:
- Endpoint: `GET /rest/api/{version}/issue/{issueKey}/changelog`
- Response includes `values[]` array with `items[]` containing field changes
- Status changes have `field: "status"` with `fromString` and `toString`
- Pagination supported via `startAt` and `maxResults`

**Alternatives Considered**:
- JQL for status changes: Rejected - JQL cannot query historical transitions
- Issue history field expansion: Rejected - requires explicit `expand=changelog` parameter which increases response size significantly

**Implementation Note**: Changelog fetching is optional (best-effort per FR-022). If API returns 403 (permissions) or 404, reopen_count defaults to 0 without error.

---

### 2. Acceptance Criteria Pattern Detection (FR-005)

**Question**: What patterns reliably detect acceptance criteria in descriptions?

**Decision**: Use regex pattern matching for common AC formats

**Rationale**:
- Acceptance criteria follow recognizable patterns across teams
- Regex is fast and doesn't require NLP dependencies
- False positives are acceptable (better to over-detect than miss)

**Patterns to Match**:
1. `Given ... When ... Then` (BDD/Gherkin style) - case insensitive
2. `AC:` or `Acceptance Criteria:` headers
3. `- [ ]` or `* [ ]` checkbox lists (markdown task lists)
4. `## Acceptance Criteria` heading
5. Numbered lists following AC header (e.g., `1.`, `2.`)

**Regex Patterns**:
```python
AC_PATTERNS = [
    r'(?i)\bgiven\b.*\bwhen\b.*\bthen\b',  # BDD
    r'(?i)^#+\s*acceptance\s+criteria',     # Markdown heading
    r'(?i)^ac\s*:',                         # AC: prefix
    r'(?i)acceptance\s+criteria\s*:',       # Full label
    r'^\s*[-*]\s*\[\s*[x ]?\s*\]',          # Checkbox list
]
```

**Alternatives Considered**:
- NLP-based detection: Rejected - adds heavy dependency, overkill for this use case
- Keyword counting: Rejected - too many false positives

---

### 3. Description Quality Score Algorithm (FR-004)

**Question**: How to implement the balanced 40/40/20 weighting?

**Decision**: Linear scoring with thresholds for each component

**Rationale**:
- Simple to implement, test, and explain
- Thresholds based on typical issue description characteristics
- Score is 0-100 integer for easy comparison

**Algorithm**:
```python
def calculate_description_quality(description: str, has_ac: bool) -> int:
    score = 0

    # Length component (40 points max)
    # 0 chars = 0, 100+ chars = 40 points (linear)
    length = len(description.strip())
    length_score = min(40, int(length * 40 / 100))
    score += length_score

    # AC presence component (40 points)
    if has_ac:
        score += 40

    # Formatting component (20 points max)
    # Check for headers (10 pts) and lists (10 pts)
    has_headers = bool(re.search(r'^#+\s', description, re.MULTILINE))
    has_lists = bool(re.search(r'^\s*[-*]\s', description, re.MULTILINE))
    if has_headers:
        score += 10
    if has_lists:
        score += 10

    return score
```

**Alternatives Considered**:
- Logarithmic scaling: Rejected - harder to explain, no clear benefit
- Word count instead of char count: Rejected - char count is simpler and sufficient

---

### 4. Cross-Team Score Calculation (FR-009)

**Question**: How to efficiently count distinct comment authors?

**Decision**: Use set-based counting with diminishing returns scale

**Rationale**:
- Comments are already fetched per issue (JiraClient.get_comments exists)
- Set gives O(1) lookup for unique authors
- Diminishing scale rewards collaboration without requiring large teams

**Algorithm**:
```python
CROSS_TEAM_SCALE = {1: 25, 2: 50, 3: 75, 4: 90}  # 5+ = 100

def calculate_cross_team_score(comments: list[JiraComment]) -> int:
    if not comments:
        return 0
    unique_authors = len({c.author for c in comments})
    return CROSS_TEAM_SCALE.get(unique_authors, 100)
```

**Alternatives Considered**:
- Include reporter in count: Rejected - reporter often doesn't engage in comments
- Weight by comment count per author: Rejected - adds complexity without value

---

### 5. Statistics Calculation (Median, Average)

**Question**: Best approach for calculating statistical aggregates?

**Decision**: Use Python `statistics` module (stdlib)

**Rationale**:
- `statistics.mean()` and `statistics.median()` handle edge cases properly
- No external dependencies needed
- Handles empty lists gracefully with clear exceptions

**Implementation**:
```python
from statistics import mean, median

def safe_mean(values: list[float]) -> float | None:
    return mean(values) if values else None

def safe_median(values: list[float]) -> float | None:
    return median(values) if values else None
```

**Alternatives Considered**:
- numpy: Rejected - adds heavy dependency for simple stats
- Manual implementation: Rejected - reinventing the wheel, error-prone

---

### 6. CSV Export Structure

**Question**: How to extend existing CSV export without breaking compatibility?

**Decision**: Add new columns to existing export + generate new summary files

**Rationale**:
- Existing consumers may parse by column name, not position
- Adding columns at end preserves positional parsing
- Summary files are new, no compatibility concerns

**Extended Issue Columns** (appended to existing):
```
cycle_time_days, aging_days, comments_count, description_quality_score,
acceptance_criteria_present, comment_velocity_hours, silent_issue,
same_day_resolution, cross_team_score, reopen_count
```

**New Files**:
- `jira_project_metrics.csv`
- `jira_person_metrics.csv`
- `jira_type_metrics.csv`

**Alternatives Considered**:
- Separate metrics-only CSV: Rejected - users need metrics alongside issue data
- JSON output: Rejected - spec requires CSV format consistency

---

## Summary

All technical unknowns have been resolved:

| Area | Decision | Risk Level |
|------|----------|------------|
| Reopen detection | Changelog API (best-effort) | Low - graceful fallback |
| AC detection | Regex patterns | Low - false positives acceptable |
| Quality score | Linear 40/40/20 algorithm | Low - simple, testable |
| Cross-team score | Set-based + diminishing scale | Low - deterministic |
| Statistics | stdlib statistics module | None - battle-tested |
| CSV structure | Extend + new files | Low - backwards compatible |

No NEEDS CLARIFICATION items remain. Ready for Phase 1.
