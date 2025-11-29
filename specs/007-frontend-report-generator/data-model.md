# Data Model: Frontend Report Generator

**Feature**: 007-frontend-report-generator
**Date**: 2025-11-29
**Status**: Complete

## Entity Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   UserMapping   │────▶│   TeamMember    │◀────│  GitHubMetrics  │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 │
                        ┌────────┴────────┐
                        │                 │
                        ▼                 ▼
               ┌─────────────────┐ ┌─────────────────┐
               │   JiraMetrics   │ │    AIInsight    │
               └─────────────────┘ └─────────────────┘

┌─────────────────┐     ┌─────────────────┐
│     Project     │────▶│  ProjectMetrics │
└─────────────────┘     └─────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         ReportData                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │   Meta   │ │TeamStats │ │ Members  │ │     Projects     │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Entities

### UserMapping

Associazione tra identità Jira e GitHub per un singolo utente.

```python
@dataclass
class UserMapping:
    """Mapping between Jira and GitHub user identities."""

    # Jira identity
    jira_display_name: str          # "Mircha Emanuel D'Angelo"
    jira_account_id: str | None     # "712020:abc123" (optional)
    jira_email: str | None          # "mircha@company.com"

    # GitHub identity
    github_username: str            # "mircha"
    github_id: int | None           # 12345678 (optional)

    # Matching metadata
    confidence: float               # 0.0-1.0, matching confidence score
    match_method: str               # "email_exact", "username_exact", "name_fuzzy", "manual"
    aliases: list[str]              # ["Mircha D'Angelo", "mircha.dangelo"]

    # Status
    is_confirmed: bool              # True if manually verified
    is_bot: bool                    # True for dependabot, github-actions, etc.
```

**Validation Rules**:
- `jira_display_name` required, non-empty
- `github_username` required, non-empty
- `confidence` must be 0.0-1.0
- `match_method` must be one of: "email_exact", "username_exact", "name_fuzzy", "initials", "manual"

**State Transitions**:
- `unconfirmed` → `confirmed`: User manually verifies match
- `confirmed` → `updated`: User changes mapping

### TeamMember

Rappresentazione unificata di un membro del team con metriche aggregate.

```python
@dataclass
class TeamMember:
    """Unified team member with aggregated metrics from all sources."""

    # Identity (from UserMapping)
    id: str                         # Canonical identifier (github_username or jira_name)
    display_name: str               # Human-readable name
    github_username: str | None     # GitHub username if mapped
    jira_id: str | None             # Jira account ID if mapped
    email: str | None               # Primary email

    # Visual
    color: str                      # Hex color for charts "#667eea"
    avatar_url: str | None          # Avatar image URL

    # Aggregated metrics
    jira_metrics: JiraMetrics | None
    github_metrics: GitHubMetrics | None

    # AI analysis
    ai_insight: AIInsight | None

    # Computed
    @property
    def has_jira_data(self) -> bool: ...

    @property
    def has_github_data(self) -> bool: ...

    @property
    def resolution_rate(self) -> float | None: ...
```

**Validation Rules**:
- `id` required, unique within report
- `display_name` required, non-empty
- At least one of `github_username` or `jira_id` must be present
- `color` must be valid hex color

### JiraMetrics

Metriche Jira per un singolo membro o progetto.

```python
@dataclass
class JiraMetrics:
    """Jira-specific metrics for a team member or project."""

    # Task counts
    assigned: int                   # Total tasks assigned
    resolved: int                   # Tasks resolved/closed
    wip: int                        # Work in progress count

    # Time metrics
    cycle_time_days: float          # Average cycle time in days
    bug_resolution_time_days: float | None  # Bug-specific resolution time

    # Quality indicators
    bugs_count: int                 # Bug issues handled
    reopen_count: int               # Tasks reopened after closure

    # Computed
    @property
    def resolution_rate(self) -> float:
        return (self.resolved / self.assigned * 100) if self.assigned > 0 else 0.0

    @property
    def reopen_rate(self) -> float:
        return (self.reopen_count / self.resolved * 100) if self.resolved > 0 else 0.0
```

### GitHubMetrics

Metriche GitHub per un singolo membro.

```python
@dataclass
class GitHubMetrics:
    """GitHub-specific metrics for a team member."""

    # Commit activity
    commits: int                    # Total commits
    additions: int                  # Lines added
    deletions: int                  # Lines deleted

    # PR activity
    prs_opened: int                 # PRs opened
    prs_merged: int                 # PRs merged
    prs_reviewed: int               # PRs reviewed (as reviewer)

    # Quality
    avg_pr_size: int                # Average lines per PR
    review_coverage: float          # % of PRs with reviews

    # Computed
    @property
    def merge_rate(self) -> float:
        return (self.prs_merged / self.prs_opened * 100) if self.prs_opened > 0 else 0.0

    @property
    def net_lines(self) -> int:
        return self.additions - self.deletions
```

### Project

Progetto/repository con metriche di qualità aggregate.

```python
@dataclass
class Project:
    """Project or repository with quality metrics."""

    # Identity
    key: str                        # Project key "PM", "DEV", etc.
    name: str                       # Full project name

    # Metrics
    metrics: ProjectMetrics

    # AI analysis
    ai_insight: AIInsight | None

@dataclass
class ProjectMetrics:
    """Quality metrics for a project."""

    # Volume
    issues_count: int               # Total issues

    # Time metrics
    cycle_time_days: float          # Average cycle time

    # Quality ratios (percentages)
    bug_ratio: float                # % issues that are bugs
    same_day_rate: float            # % resolved same day
    silent_issues_ratio: float      # % issues without comments
    reopen_rate: float              # % issues reopened

    # Health score (0-100)
    health_score: float
```

### AIInsight

Output strutturato dall'analisi AI.

```python
@dataclass
class AIInsight:
    """Structured AI analysis output."""

    # Rating
    rating: str                     # "A", "B+", "C", etc.
    rating_numeric: float           # 0.0-4.0 (GPA style)

    # Analysis sections
    strengths: list[str]            # 3-5 positive points
    improvements: list[str]         # 3-5 areas to improve
    red_flags: list[str]            # 0-3 critical issues
    recommendations: list[str]      # 2-4 actionable suggestions

    # Summary
    summary: str                    # 2-3 sentence overview

    # Metadata
    generated_at: datetime          # When analysis was generated
    model: str                      # "llama-3.1-sonar-small-128k-online"
    prompt_hash: str                # Hash of input data for cache key
```

**Validation Rules**:
- `rating` must match pattern: `[A-F][+-]?`
- `rating_numeric` must be 0.0-4.0
- `strengths` must have 1-5 items
- `improvements` must have 1-5 items
- `red_flags` must have 0-3 items

### ReportData

Struttura completa per la generazione del report.

```python
@dataclass
class ReportData:
    """Complete data structure for report generation."""

    # Metadata
    meta: ReportMeta

    # Team overview
    team: TeamStats

    # Individual data
    members: list[TeamMember]       # Max 30 members

    # Project data
    projects: list[Project]

    # Team-level AI insight
    team_ai_insight: AIInsight | None

@dataclass
class ReportMeta:
    """Report metadata."""

    generated_at: datetime          # Generation timestamp
    period_start: date              # Analysis period start
    period_end: date                # Analysis period end
    period_days: int                # Number of days
    sources: list[str]              # ["github", "jira"]
    title: str                      # Report title
    subtitle: str | None            # Optional subtitle

@dataclass
class TeamStats:
    """Aggregated team statistics."""

    name: str                       # Team name
    total_members: int              # Active members count

    # KPIs
    total_tasks: int
    resolved_tasks: int
    resolution_rate: float
    avg_cycle_time: float
    total_bugs: int
    wip_total: int

    # Trends (vs previous period)
    trends: dict[str, TrendData]

@dataclass
class TrendData:
    """Trend comparison with previous period."""

    current: float                  # Current period value
    previous: float | None          # Previous period value
    change_pct: float | None        # Percentage change
    direction: str                  # "up", "down", "stable", "new"
```

## Configuration Schema

### report_config.yaml

```yaml
report:
  title: "Team Performance Report"
  subtitle: "Development Team"
  language: "it"  # it, en
  period_days: 30

sections:
  team_overview:
    enabled: true
    show_rankings: true
    show_ai_analysis: true

  quality_metrics:
    enabled: true
    projects_to_include: "all"  # or list: ["PM", "DEV"]

  individual_reports:
    enabled: true
    members_to_include: "all"  # or list: ["mircha", "alex"]
    min_tasks_for_report: 3

  github_metrics:
    enabled: true
    repos_to_include: "all"

ai_analysis:
  enabled: true
  provider: "perplexity"
  cache_ttl_hours: 24
  generate_for:
    - team_overview
    - individual_reports
    - project_analysis

design:
  theme: "gradient"  # gradient, minimal, dark
  member_colors: "auto"
  animations: true
```

### user_mapping.yaml

```yaml
# Confirmed user mappings
mappings:
  - jira_display_name: "Mircha Emanuel D'Angelo"
    jira_account_id: "712020:abc123"
    jira_email: "mircha@company.com"
    github_username: "mircha"
    github_id: 12345678
    confidence: 1.0
    match_method: "email_exact"
    is_confirmed: true
    is_bot: false
    aliases:
      - "Mircha D'Angelo"
      - "mircha.dangelo"

  - jira_display_name: "Alexandru Ungureanu"
    github_username: "alexu"
    confidence: 0.95
    match_method: "username_exact"
    is_confirmed: true
    is_bot: false
    aliases: []

# Bot accounts (excluded from individual reports)
bots:
  - pattern: "dependabot*"
  - pattern: "github-actions*"
  - pattern: "*[bot]"

# Unconfirmed mappings (pending user verification)
unconfirmed:
  - jira_name: "setek"
    candidates:
      - github_username: "setek-user"
        confidence: 0.85
      - github_username: "setekdev"
        confidence: 0.72
```

## JSON Output Schema

### data.json (debug/export)

```json
{
  "meta": {
    "generated_at": "2025-11-29T10:30:00Z",
    "period_start": "2025-10-29",
    "period_end": "2025-11-28",
    "period_days": 30,
    "sources": ["github", "jira"]
  },
  "team": {
    "name": "Development Team",
    "total_members": 4,
    "kpis": {
      "total_tasks": 82,
      "resolved_tasks": 73,
      "resolution_rate": 89.0,
      "avg_cycle_time": 10.5,
      "total_bugs": 8,
      "wip_total": 9
    },
    "trends": {
      "total_tasks": {"current": 82, "previous": 75, "change_pct": 9.3, "direction": "up"},
      "resolution_rate": {"current": 89.0, "previous": 85.0, "change_pct": 4.7, "direction": "up"}
    }
  },
  "members": [
    {
      "id": "mircha",
      "display_name": "Mircha Emanuel D'Angelo",
      "github_username": "mircha",
      "jira_id": "712020:abc123",
      "color": "#667eea",
      "jira_metrics": {
        "assigned": 47,
        "resolved": 44,
        "wip": 3,
        "cycle_time_days": 5.87,
        "bugs_count": 4,
        "resolution_rate": 93.6
      },
      "github_metrics": {
        "commits": 156,
        "additions": 5420,
        "deletions": 2100,
        "prs_opened": 23,
        "prs_merged": 21
      },
      "ai_insight": {
        "rating": "A",
        "strengths": ["Alta produttività", "Cycle time eccellente"],
        "improvements": ["Aumentare code review"],
        "red_flags": [],
        "summary": "Performance eccellente..."
      }
    }
  ],
  "projects": [
    {
      "key": "PM",
      "name": "Pescara Multiservice",
      "metrics": {
        "issues_count": 50,
        "cycle_time_days": 8.88,
        "bug_ratio": 14.0,
        "same_day_rate": 38.1,
        "silent_issues_ratio": 68.0,
        "reopen_rate": 7.14,
        "health_score": 72.0
      }
    }
  ]
}
```

## Relationships

| From | To | Cardinality | Description |
|------|-----|-------------|-------------|
| UserMapping | TeamMember | 1:1 | Each mapping creates one member |
| TeamMember | JiraMetrics | 1:0..1 | Optional Jira data |
| TeamMember | GitHubMetrics | 1:0..1 | Optional GitHub data |
| TeamMember | AIInsight | 1:0..1 | Optional AI analysis |
| Project | ProjectMetrics | 1:1 | Required metrics |
| Project | AIInsight | 1:0..1 | Optional AI analysis |
| ReportData | TeamMember | 1:0..30 | Up to 30 members |
| ReportData | Project | 1:0..n | Multiple projects |
