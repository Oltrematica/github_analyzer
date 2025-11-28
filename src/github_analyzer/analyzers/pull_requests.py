"""Pull request analysis module.

This module provides the PullRequestAnalyzer class for fetching
and analyzing pull requests from GitHub repositories.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from src.github_analyzer.api.models import PullRequest

if TYPE_CHECKING:
    from src.github_analyzer.api.client import GitHubClient
    from src.github_analyzer.config.validation import Repository


class PullRequestAnalyzer:
    """Analyze pull requests from GitHub API responses.

    Fetches PRs from a repository and processes them into
    PullRequest objects with computed properties.
    """

    def __init__(self, client: GitHubClient, fetch_details: bool = False) -> None:
        """Initialize analyzer with API client.

        Args:
            client: GitHub API client instance.
            fetch_details: If True, fetch full PR details (slower but includes
                additions/deletions/changed_files). Default False for speed.
        """
        self._client = client
        self._fetch_details = fetch_details

    def fetch_and_analyze(
        self,
        repo: Repository,
        since: datetime,
    ) -> list[PullRequest]:
        """Fetch PRs and process into PullRequest objects.

        Args:
            repo: Repository to analyze.
            since: Start date for analysis period.

        Returns:
            List of processed PullRequest objects.
        """
        endpoint = f"/repos/{repo.full_name}/pulls"
        params = {
            "state": "all",
            "sort": "updated",
            "direction": "desc",
        }

        raw_prs = self._client.paginate(endpoint, params)
        prs: list[PullRequest] = []

        for raw in raw_prs:
            # Check if PR was updated within our timeframe
            # Since results are sorted by updated_at desc, we can break early
            updated_at = raw.get("updated_at", "")
            if updated_at:
                try:
                    updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                    if updated < since:
                        # All remaining PRs will also be older, so stop processing
                        break
                except ValueError:
                    pass

            # Optionally fetch full PR details (slower but more data)
            if self._fetch_details:
                number = raw.get("number")
                if number:
                    detail_endpoint = f"/repos/{repo.full_name}/pulls/{number}"
                    detail = self._client.get(detail_endpoint)
                    if detail and isinstance(detail, dict):
                        raw = detail

            pr = PullRequest.from_api_response(raw, repo.full_name)
            prs.append(pr)

        return prs

    def get_stats(self, prs: list[PullRequest]) -> dict:
        """Calculate aggregate statistics for PRs.

        Args:
            prs: List of PullRequest objects.

        Returns:
            Dictionary with aggregate statistics.
        """
        if not prs:
            return {
                "total": 0,
                "merged": 0,
                "open": 0,
                "closed_not_merged": 0,
                "draft": 0,
                "avg_time_to_merge_hours": None,
            }

        merged = [p for p in prs if p.is_merged]
        open_prs = [p for p in prs if p.state == "open"]
        draft = [p for p in prs if p.is_draft]

        # Calculate average time to merge
        merge_times = [p.time_to_merge_hours for p in merged if p.time_to_merge_hours]
        avg_merge_time = sum(merge_times) / len(merge_times) if merge_times else None

        return {
            "total": len(prs),
            "merged": len(merged),
            "open": len(open_prs),
            "closed_not_merged": len(prs) - len(merged) - len(open_prs),
            "draft": len(draft),
            "avg_time_to_merge_hours": avg_merge_time,
        }
