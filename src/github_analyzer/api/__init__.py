"""API module - GitHub API client and data models.

Public exports:
- GitHubClient: HTTP client for GitHub API
- Commit: Processed commit data
- PullRequest: Processed PR data
- Issue: Processed issue data
- RepositoryStats: Aggregate repository statistics
- QualityMetrics: Code quality metrics
- ContributorStats: Per-contributor statistics
- ProductivityAnalysis: Productivity analysis result
"""

from src.github_analyzer.api.client import GitHubClient
from src.github_analyzer.api.models import (
    Commit,
    ContributorStats,
    Issue,
    ProductivityAnalysis,
    PullRequest,
    QualityMetrics,
    RepositoryStats,
)

__all__ = [
    "GitHubClient",
    "Commit",
    "PullRequest",
    "Issue",
    "RepositoryStats",
    "QualityMetrics",
    "ContributorStats",
    "ProductivityAnalysis",
]
