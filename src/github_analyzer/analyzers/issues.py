"""Issue analysis module.

This module provides the IssueAnalyzer class for fetching and
analyzing issues from GitHub repositories.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from src.github_analyzer.api.models import Issue

if TYPE_CHECKING:
    from src.github_analyzer.api.client import GitHubClient
    from src.github_analyzer.config.validation import Repository


class IssueAnalyzer:
    """Analyze issues from GitHub API responses.

    Fetches issues (excluding PRs) from a repository and processes
    them into Issue objects with computed properties.
    """

    def __init__(self, client: GitHubClient) -> None:
        """Initialize analyzer with API client.

        Args:
            client: GitHub API client instance.
        """
        self._client = client

    def fetch_and_analyze(
        self,
        repo: Repository,
        since: datetime,
    ) -> list[Issue]:
        """Fetch issues and process into Issue objects.

        Args:
            repo: Repository to analyze.
            since: Start date for analysis period.

        Returns:
            List of processed Issue objects (excluding PRs).
        """
        endpoint = f"/repos/{repo.full_name}/issues"
        params = {
            "state": "all",
            "since": since.isoformat(),
            "sort": "updated",
            "direction": "desc",
        }

        raw_issues = self._client.paginate(endpoint, params)
        issues: list[Issue] = []

        for raw in raw_issues:
            # Skip pull requests (GitHub returns PRs in issues endpoint)
            if "pull_request" in raw:
                continue

            issue = Issue.from_api_response(raw, repo.full_name)
            issues.append(issue)

        return issues

    def get_stats(self, issues: list[Issue]) -> dict:
        """Calculate aggregate statistics for issues.

        Args:
            issues: List of Issue objects.

        Returns:
            Dictionary with aggregate statistics.
        """
        if not issues:
            return {
                "total": 0,
                "closed": 0,
                "open": 0,
                "bugs": 0,
                "enhancements": 0,
                "avg_time_to_close_hours": None,
            }

        closed = [i for i in issues if i.state == "closed"]
        open_issues = [i for i in issues if i.state == "open"]
        bugs = [i for i in issues if i.is_bug]
        enhancements = [i for i in issues if i.is_enhancement]

        # Calculate average time to close
        close_times = [i.time_to_close_hours for i in closed if i.time_to_close_hours]
        avg_close_time = sum(close_times) / len(close_times) if close_times else None

        return {
            "total": len(issues),
            "closed": len(closed),
            "open": len(open_issues),
            "bugs": len(bugs),
            "enhancements": len(enhancements),
            "avg_time_to_close_hours": avg_close_time,
        }
