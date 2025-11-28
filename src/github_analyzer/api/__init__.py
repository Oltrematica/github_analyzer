"""API module - GitHub and Jira API clients and data models.

Public exports:
- GitHubClient: HTTP client for GitHub API
- JiraClient: HTTP client for Jira API
- JiraProject: Jira project metadata
- JiraIssue: Jira issue with core fields
- JiraComment: Jira issue comment
- Commit: Processed commit data
- PullRequest: Processed PR data
- Issue: Processed issue data
- RepositoryStats: Aggregate repository statistics
- QualityMetrics: Code quality metrics
- ContributorStats: Per-contributor statistics
- ProductivityAnalysis: Productivity analysis result
"""

from src.github_analyzer.api.client import GitHubClient
from src.github_analyzer.api.jira_client import (
    JiraClient,
    JiraComment,
    JiraIssue,
    JiraProject,
)
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
    "JiraClient",
    "JiraProject",
    "JiraIssue",
    "JiraComment",
    "Commit",
    "PullRequest",
    "Issue",
    "RepositoryStats",
    "QualityMetrics",
    "ContributorStats",
    "ProductivityAnalysis",
]
