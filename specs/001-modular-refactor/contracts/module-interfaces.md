# Module Interfaces: Modular Architecture Refactoring

**Feature**: 001-modular-refactor
**Date**: 2025-11-28

This document defines the public interfaces between modules. These are internal contracts, not external APIs.

## Module: config

### settings.py

```python
@dataclass(frozen=True)
class AnalyzerConfig:
    """Immutable configuration for the analyzer."""
    github_token: str
    output_dir: str = "github_export"
    repos_file: str = "repos.txt"
    days: int = 30
    per_page: int = 100
    verbose: bool = True
    timeout: int = 30
    max_pages: int = 50

    @classmethod
    def from_env(cls) -> "AnalyzerConfig":
        """Load configuration from environment variables.

        Raises:
            ConfigurationError: If GITHUB_TOKEN is not set.
        """
        ...

    def validate(self) -> None:
        """Validate all configuration values.

        Raises:
            ValidationError: If any value is invalid.
        """
        ...
```

### validation.py

```python
@dataclass(frozen=True)
class Repository:
    """Validated GitHub repository identifier."""
    owner: str
    name: str

    @property
    def full_name(self) -> str:
        """Return 'owner/name' format."""
        ...

    @classmethod
    def from_string(cls, repo_str: str) -> "Repository":
        """Parse repository from string (owner/repo or URL).

        Raises:
            ValidationError: If format is invalid or contains dangerous characters.
        """
        ...


def load_repositories(filepath: str) -> list[Repository]:
    """Load and validate repositories from file.

    Args:
        filepath: Path to repos.txt file.

    Returns:
        List of validated Repository objects (deduplicated).

    Raises:
        ConfigurationError: If file not found or empty.
        ValidationError: If any entry is invalid (logs warning, continues).
    """
    ...


def validate_token_format(token: str) -> bool:
    """Check if token matches GitHub token patterns.

    Does NOT validate against API - only format check.
    """
    ...
```

## Module: api

### client.py

```python
class GitHubClient:
    """HTTP client for GitHub REST API."""

    def __init__(self, config: AnalyzerConfig) -> None:
        """Initialize client with configuration.

        Note: Token is accessed from config, never stored separately.
        """
        ...

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict | None:
        """Make GET request to GitHub API.

        Args:
            endpoint: API endpoint path (e.g., "/repos/{owner}/{repo}/commits")
            params: Query parameters.

        Returns:
            JSON response as dict, or None on error.

        Raises:
            RateLimitError: If rate limit exceeded.
            APIError: On other API errors (logs details).
        """
        ...

    def paginate(self, endpoint: str, params: dict[str, Any] | None = None) -> list[dict]:
        """Fetch all pages from paginated endpoint.

        Automatically handles pagination up to max_pages limit.
        """
        ...

    @property
    def rate_limit_remaining(self) -> int | None:
        """Return remaining API calls, if known."""
        ...
```

### models.py

```python
# Data classes for API responses - see data-model.md for full definitions

@dataclass
class Commit:
    """Processed commit data."""
    ...

@dataclass
class PullRequest:
    """Processed pull request data."""
    ...

@dataclass
class Issue:
    """Processed issue data."""
    ...
```

## Module: analyzers

### commits.py

```python
class CommitAnalyzer:
    """Analyze commits from GitHub API responses."""

    def __init__(self, client: GitHubClient) -> None:
        ...

    def fetch_and_analyze(self, repo: Repository, since: datetime) -> list[Commit]:
        """Fetch commits and process into Commit objects.

        Args:
            repo: Repository to analyze.
            since: Start date for analysis period.

        Returns:
            List of processed Commit objects.
        """
        ...
```

### pull_requests.py

```python
class PullRequestAnalyzer:
    """Analyze pull requests from GitHub API responses."""

    def __init__(self, client: GitHubClient) -> None:
        ...

    def fetch_and_analyze(self, repo: Repository, since: datetime) -> list[PullRequest]:
        """Fetch PRs and process into PullRequest objects."""
        ...
```

### issues.py

```python
class IssueAnalyzer:
    """Analyze issues from GitHub API responses."""

    def __init__(self, client: GitHubClient) -> None:
        ...

    def fetch_and_analyze(self, repo: Repository, since: datetime) -> list[Issue]:
        """Fetch issues (excluding PRs) and process into Issue objects."""
        ...
```

### quality.py

```python
def calculate_quality_metrics(
    repo: Repository,
    commits: list[Commit],
    prs: list[PullRequest]
) -> QualityMetrics:
    """Calculate quality metrics for a repository."""
    ...
```

### productivity.py

```python
class ContributorTracker:
    """Track contributor statistics across repositories."""

    def __init__(self) -> None:
        self._stats: dict[str, ContributorStats] = {}

    def record_commit(self, commit: Commit) -> None:
        """Update stats from commit."""
        ...

    def record_pr(self, pr: PullRequest) -> None:
        """Update stats from PR."""
        ...

    def record_review(self, reviewer: str, repo: str, timestamp: datetime) -> None:
        """Update stats from review."""
        ...

    def generate_analysis(self) -> list[ProductivityAnalysis]:
        """Generate productivity analysis for all tracked contributors."""
        ...
```

## Module: exporters

### csv_exporter.py

```python
class CSVExporter:
    """Export analysis results to CSV files."""

    def __init__(self, output_dir: str) -> None:
        """Initialize exporter with output directory.

        Creates directory if it doesn't exist.
        """
        ...

    def export_commits(self, commits: list[Commit]) -> Path:
        """Export commits to commits_export.csv."""
        ...

    def export_pull_requests(self, prs: list[PullRequest]) -> Path:
        """Export PRs to pull_requests_export.csv."""
        ...

    def export_issues(self, issues: list[Issue]) -> Path:
        """Export issues to issues_export.csv."""
        ...

    def export_repository_summary(self, stats: list[RepositoryStats]) -> Path:
        """Export repository stats to repository_summary.csv."""
        ...

    def export_quality_metrics(self, metrics: list[QualityMetrics]) -> Path:
        """Export quality metrics to quality_metrics.csv."""
        ...

    def export_productivity(self, analysis: list[ProductivityAnalysis]) -> Path:
        """Export productivity analysis to productivity_analysis.csv."""
        ...

    def export_contributors(self, stats: dict[str, ContributorStats]) -> Path:
        """Export contributor summary to contributors_summary.csv."""
        ...
```

## Module: cli

### main.py

```python
def main() -> int:
    """Main entry point for CLI.

    Returns:
        Exit code (0=success, 1=user error, 2=system error).
    """
    ...


class GitHubAnalyzer:
    """Main analyzer orchestrator."""

    def __init__(self, config: AnalyzerConfig) -> None:
        ...

    def run(self, repositories: list[Repository]) -> None:
        """Run full analysis on all repositories."""
        ...
```

### output.py

```python
class Colors:
    """ANSI color codes for terminal output."""
    HEADER: str
    BLUE: str
    CYAN: str
    GREEN: str
    YELLOW: str
    RED: str
    BOLD: str
    DIM: str
    RESET: str


class TerminalOutput:
    """Formatted terminal output."""

    def __init__(self, verbose: bool = True) -> None:
        ...

    def banner(self) -> None:
        """Print welcome banner."""
        ...

    def log(self, message: str, level: str = "info") -> None:
        """Print log message with timestamp and color."""
        ...

    def progress(self, current: int, total: int, label: str) -> None:
        """Print progress indicator."""
        ...

    def summary(self, stats: dict) -> None:
        """Print final summary."""
        ...
```

## Module: core

### exceptions.py

```python
class GitHubAnalyzerError(Exception):
    """Base exception for all analyzer errors."""
    exit_code: int = 1

    def __init__(self, message: str, details: str | None = None) -> None:
        ...


class ConfigurationError(GitHubAnalyzerError):
    """Invalid configuration."""
    exit_code = 1


class ValidationError(GitHubAnalyzerError):
    """Input validation failed."""
    exit_code = 1


class APIError(GitHubAnalyzerError):
    """GitHub API error."""
    exit_code = 2


class RateLimitError(APIError):
    """Rate limit exceeded."""
    exit_code = 2
```

## Dependency Rules

```
┌─────────┐
│  cli    │ ─────────────────────────────────┐
└────┬────┘                                  │
     │                                       │
     ▼                                       ▼
┌─────────┐     ┌───────────┐     ┌──────────────┐
│  api    │ ◄── │ analyzers │ ──► │  exporters   │
└────┬────┘     └─────┬─────┘     └──────┬───────┘
     │                │                   │
     ▼                ▼                   ▼
┌─────────────────────────────────────────────────┐
│                    config                        │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│                     core                         │
└─────────────────────────────────────────────────┘
```

**Rules**:
1. `core` has no internal dependencies
2. `config` depends only on `core`
3. `api` depends on `config` and `core`
4. `analyzers` depends on `api`, `config`, and `core`
5. `exporters` depends on `analyzers` (data types), `config`, and `core`
6. `cli` can depend on all modules
