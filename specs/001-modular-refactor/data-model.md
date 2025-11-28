# Data Model: Modular Architecture Refactoring

**Feature**: 001-modular-refactor
**Date**: 2025-11-28

## Overview

This document defines the core data structures for the refactored GitHub Analyzer. All models use Python dataclasses for type safety and immutability.

## Entities

### Configuration

```
AnalyzerConfig
├── github_token: str (required, from GITHUB_TOKEN env var)
├── output_dir: str = "github_export"
├── repos_file: str = "repos.txt"
├── days: int = 30
├── per_page: int = 100
├── verbose: bool = True
├── timeout: int = 30
└── max_pages: int = 50
```

**Validation Rules**:
- `github_token`: Must be non-empty, match GitHub token patterns
- `output_dir`: Must be valid path, created if not exists
- `days`: Must be positive integer, max 365
- `per_page`: Must be 1-100 (GitHub API limit)
- `timeout`: Must be positive integer, max 300

### Repository

```
Repository
├── owner: str
├── name: str
└── full_name: str (computed: "{owner}/{name}")
```

**Validation Rules**:
- `owner`: Must match `^[a-zA-Z0-9._-]+$`
- `name`: Must match `^[a-zA-Z0-9._-]+$`
- Max 100 characters per component
- No shell metacharacters

**Factory Methods**:
- `from_string(repo_str: str) -> Repository`: Parses "owner/repo" or URL
- `from_url(url: str) -> Repository`: Parses GitHub URL

### Commit

```
Commit
├── repository: str
├── sha: str
├── short_sha: str
├── author_name: str
├── author_email: str
├── author_login: str
├── committer_name: str
├── committer_email: str
├── committer_login: str
├── date: datetime
├── message: str
├── full_message: str
├── additions: int
├── deletions: int
├── total_changes: int
├── files_changed: int
├── is_merge_commit: bool
├── is_revert: bool
├── file_types: dict[str, int]
└── url: str
```

**Computed Properties**:
- `short_sha`: First 7 characters of SHA
- `is_merge_commit`: Message starts with "Merge" (case-insensitive)
- `is_revert`: Message starts with "Revert" (case-insensitive)

### PullRequest

```
PullRequest
├── repository: str
├── number: int
├── title: str
├── state: str ("open" | "closed")
├── author_login: str
├── author_type: str
├── created_at: datetime
├── updated_at: datetime
├── closed_at: datetime | None
├── merged_at: datetime | None
├── merged_by: str
├── is_merged: bool
├── is_draft: bool
├── additions: int
├── deletions: int
├── changed_files: int
├── commits: int
├── comments: int
├── review_comments: int
├── time_to_merge_hours: float | None
├── labels: list[str]
├── reviewers_count: int
├── approvals: int
├── changes_requested: int
├── base_branch: str
├── head_branch: str
└── url: str
```

**Computed Properties**:
- `time_to_merge_hours`: Calculated from `created_at` to `merged_at`

### Issue

```
Issue
├── repository: str
├── number: int
├── title: str
├── state: str ("open" | "closed")
├── author_login: str
├── created_at: datetime
├── updated_at: datetime
├── closed_at: datetime | None
├── closed_by: str
├── comments: int
├── labels: list[str]
├── assignees: list[str]
├── time_to_close_hours: float | None
├── is_bug: bool
├── is_enhancement: bool
└── url: str
```

**Computed Properties**:
- `is_bug`: Any label contains "bug" (case-insensitive)
- `is_enhancement`: Any label contains "enhancement" or "feature"
- `time_to_close_hours`: Calculated from `created_at` to `closed_at`

### RepositoryStats

```
RepositoryStats
├── repository: str
├── total_commits: int
├── merge_commits: int
├── revert_commits: int
├── regular_commits: int
├── total_additions: int
├── total_deletions: int
├── net_lines: int
├── unique_authors: int
├── total_prs: int
├── merged_prs: int
├── open_prs: int
├── pr_merge_rate: float
├── avg_time_to_merge_hours: float | None
├── total_issues: int
├── closed_issues: int
├── open_issues: int
├── bug_issues: int
├── issue_close_rate: float
├── active_days: int
├── commits_per_active_day: float
└── analysis_period_days: int
```

### QualityMetrics

```
QualityMetrics
├── repository: str
├── revert_ratio_pct: float
├── avg_commit_size_lines: float
├── large_commits_count: int
├── large_commits_ratio_pct: float
├── pr_review_coverage_pct: float
├── pr_approval_rate_pct: float
├── pr_changes_requested_ratio_pct: float
├── draft_pr_ratio_pct: float
├── commit_message_quality_pct: float
└── quality_score: float
```

**Quality Score Formula**:
```
quality_score = (
    (100 - revert_ratio_pct) * 0.20 +
    pr_review_coverage_pct * 0.25 +
    pr_approval_rate_pct * 0.20 +
    (100 - pr_changes_requested_ratio_pct) * 0.15 +
    commit_message_quality_pct * 0.20
)
```

### ContributorStats

```
ContributorStats
├── login: str
├── repositories: set[str]
├── commits: int
├── additions: int
├── deletions: int
├── prs_opened: int
├── prs_merged: int
├── prs_reviewed: int
├── issues_opened: int
├── issues_closed: int
├── first_activity: datetime | None
├── last_activity: datetime | None
├── commit_days: set[str]  # ISO date strings
└── avg_commit_sizes: list[int]
```

### ProductivityAnalysis

```
ProductivityAnalysis
├── contributor: str
├── repositories: str  # Comma-separated
├── repositories_count: int
├── total_commits: int
├── total_additions: int
├── total_deletions: int
├── net_lines: int
├── avg_commit_size: float
├── prs_opened: int
├── prs_merged: int
├── pr_merge_rate_pct: float
├── prs_reviewed: int
├── issues_opened: int
├── issues_closed: int
├── active_days: int
├── commits_per_active_day: float
├── first_activity: str  # ISO datetime
├── last_activity: str  # ISO datetime
├── activity_span_days: int
├── consistency_pct: float
└── productivity_score: float
```

**Productivity Score Formula**:
```
productivity_score = (
    min(total_commits / 10, 30) +
    min(prs_merged * 5, 25) +
    min(prs_reviewed * 3, 20) +
    min(consistency_pct / 5, 15) +
    min(repositories_count * 2, 10)
)
```

## Relationships

```
AnalyzerConfig
    └── validates → Repository[]

Repository
    ├── has many → Commit[]
    ├── has many → PullRequest[]
    ├── has many → Issue[]
    ├── produces → RepositoryStats
    └── produces → QualityMetrics

Commit
    └── contributes to → ContributorStats

PullRequest
    └── contributes to → ContributorStats

ContributorStats
    └── produces → ProductivityAnalysis
```

## State Transitions

### Analysis Flow

```
1. INIT: Config loaded, token validated
2. LOADING: Reading repos.txt, validating entries
3. FETCHING: API requests in progress (per repository)
4. ANALYZING: Computing metrics
5. EXPORTING: Writing CSV files
6. COMPLETE: Summary displayed
```

### Error States

```
CONFIG_ERROR: Missing token, invalid config
VALIDATION_ERROR: Invalid repository format
API_ERROR: Network failure, 4xx/5xx responses
RATE_LIMITED: 403 with rate limit headers
PARTIAL_SUCCESS: Some repos failed, others completed
```
