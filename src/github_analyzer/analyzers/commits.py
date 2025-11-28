"""Commit analysis module.

This module provides the CommitAnalyzer class for fetching and
analyzing commits from GitHub repositories.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from src.github_analyzer.api.models import Commit

if TYPE_CHECKING:
    from src.github_analyzer.api.client import GitHubClient
    from src.github_analyzer.config.validation import Repository


class CommitAnalyzer:
    """Analyze commits from GitHub API responses.

    Fetches commits from a repository and processes them into
    Commit objects with computed properties.
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
    ) -> list[Commit]:
        """Fetch commits and process into Commit objects.

        Args:
            repo: Repository to analyze.
            since: Start date for analysis period.

        Returns:
            List of processed Commit objects.
        """
        endpoint = f"/repos/{repo.full_name}/commits"
        params = {
            "since": since.isoformat(),
        }

        raw_commits = self._client.paginate(endpoint, params)
        commits: list[Commit] = []

        for raw in raw_commits:
            # Fetch full commit details for stats
            sha = raw.get("sha", "")
            if sha:
                detail_endpoint = f"/repos/{repo.full_name}/commits/{sha}"
                detail = self._client.get(detail_endpoint)
                if detail and isinstance(detail, dict):
                    raw = detail

            commit = Commit.from_api_response(raw, repo.full_name)
            commits.append(commit)

        return commits

    def get_stats(self, commits: list[Commit]) -> dict:
        """Calculate aggregate statistics for commits.

        Args:
            commits: List of Commit objects.

        Returns:
            Dictionary with aggregate statistics.
        """
        if not commits:
            return {
                "total": 0,
                "merge_commits": 0,
                "revert_commits": 0,
                "regular_commits": 0,
                "total_additions": 0,
                "total_deletions": 0,
                "unique_authors": 0,
            }

        merge_commits = sum(1 for c in commits if c.is_merge_commit)
        revert_commits = sum(1 for c in commits if c.is_revert)
        total_additions = sum(c.additions for c in commits)
        total_deletions = sum(c.deletions for c in commits)
        unique_authors = len({c.author_login for c in commits})

        return {
            "total": len(commits),
            "merge_commits": merge_commits,
            "revert_commits": revert_commits,
            "regular_commits": len(commits) - merge_commits - revert_commits,
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "unique_authors": unique_authors,
        }
