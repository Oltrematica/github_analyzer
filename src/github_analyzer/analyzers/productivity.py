"""Productivity analysis module.

This module provides the ContributorTracker class for tracking
contributor statistics and generating productivity analysis.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from src.github_analyzer.api.models import ContributorStats, ProductivityAnalysis

if TYPE_CHECKING:
    from src.github_analyzer.api.models import Commit, Issue, PullRequest


class ContributorTracker:
    """Track contributor statistics across repositories.

    Collects data from commits, PRs, and issues to build
    per-contributor statistics for productivity analysis.
    """

    def __init__(self) -> None:
        """Initialize tracker with empty stats."""
        self._stats: dict[str, ContributorStats] = {}

    def _get_or_create(self, login: str) -> ContributorStats:
        """Get or create stats for a contributor.

        Args:
            login: GitHub login.

        Returns:
            ContributorStats instance.
        """
        if login not in self._stats:
            self._stats[login] = ContributorStats(login=login)
        return self._stats[login]

    def _update_activity(self, stats: ContributorStats, timestamp: datetime) -> None:
        """Update first/last activity timestamps.

        Args:
            stats: Stats to update.
            timestamp: Activity timestamp.
        """
        if stats.first_activity is None or timestamp < stats.first_activity:
            stats.first_activity = timestamp
        if stats.last_activity is None or timestamp > stats.last_activity:
            stats.last_activity = timestamp

    def record_commit(self, commit: Commit) -> None:
        """Update stats from commit.

        Args:
            commit: Commit to record.
        """
        if not commit.author_login or commit.author_login == "unknown":
            return

        stats = self._get_or_create(commit.author_login)
        stats.repositories.add(commit.repository)
        stats.commits += 1
        stats.additions += commit.additions
        stats.deletions += commit.deletions
        stats.commit_sizes.append(commit.total_changes)
        stats.commit_days.add(commit.date.strftime("%Y-%m-%d"))
        self._update_activity(stats, commit.date)

    def record_pr(self, pr: PullRequest) -> None:
        """Update stats from PR.

        Args:
            pr: PullRequest to record.
        """
        if not pr.author_login or pr.author_login == "unknown":
            return

        stats = self._get_or_create(pr.author_login)
        stats.repositories.add(pr.repository)
        stats.prs_opened += 1
        if pr.is_merged:
            stats.prs_merged += 1
        self._update_activity(stats, pr.created_at)

    def record_review(
        self,
        reviewer: str,
        repo: str,
        timestamp: datetime,
    ) -> None:
        """Update stats from review.

        Args:
            reviewer: Reviewer's GitHub login.
            repo: Repository full name.
            timestamp: Review timestamp.
        """
        if not reviewer or reviewer == "unknown":
            return

        stats = self._get_or_create(reviewer)
        stats.repositories.add(repo)
        stats.prs_reviewed += 1
        self._update_activity(stats, timestamp)

    def record_issue(self, issue: Issue, is_opener: bool = True) -> None:
        """Update stats from issue.

        Args:
            issue: Issue to record.
            is_opener: Whether recording issue opener or closer.
        """
        login = issue.author_login if is_opener else None
        if not login or login == "unknown":
            return

        stats = self._get_or_create(login)
        stats.repositories.add(issue.repository)
        if is_opener:
            stats.issues_opened += 1
        else:
            stats.issues_closed += 1
        self._update_activity(stats, issue.created_at)

    def get_stats(self) -> dict[str, ContributorStats]:
        """Get all contributor statistics.

        Returns:
            Dictionary mapping login to stats.
        """
        return self._stats.copy()

    def generate_analysis(
        self,
        analysis_period_days: int = 30,
    ) -> list[ProductivityAnalysis]:
        """Generate productivity analysis for all tracked contributors.

        Calculates productivity metrics and scores based on the
        formula from data-model.md.

        Args:
            analysis_period_days: Days in the analysis period.

        Returns:
            List of ProductivityAnalysis objects sorted by score.
        """
        analyses: list[ProductivityAnalysis] = []

        for login, stats in self._stats.items():
            # Calculate derived metrics
            repos_list = sorted(stats.repositories)
            repos_count = len(repos_list)
            net_lines = stats.additions - stats.deletions
            avg_commit_size = (
                sum(stats.commit_sizes) / len(stats.commit_sizes)
                if stats.commit_sizes
                else 0.0
            )

            # PR metrics
            merge_rate = (
                (stats.prs_merged / stats.prs_opened * 100)
                if stats.prs_opened > 0
                else 0.0
            )

            # Activity metrics
            active_days = len(stats.commit_days)
            commits_per_day = (
                stats.commits / active_days if active_days > 0 else 0.0
            )

            # Time span
            first_str = (
                stats.first_activity.isoformat()
                if stats.first_activity
                else ""
            )
            last_str = (
                stats.last_activity.isoformat()
                if stats.last_activity
                else ""
            )

            activity_span = 0
            if stats.first_activity and stats.last_activity:
                delta = stats.last_activity - stats.first_activity
                activity_span = max(1, delta.days)

            # Consistency: active_days / analysis_period_days
            consistency = (active_days / analysis_period_days * 100) if analysis_period_days > 0 else 0.0

            # Productivity score (from data-model.md):
            # productivity_score = (
            #     min(total_commits / 10, 30) +
            #     min(prs_merged * 5, 25) +
            #     min(prs_reviewed * 3, 20) +
            #     min(consistency_pct / 5, 15) +
            #     min(repositories_count * 2, 10)
            # )
            productivity_score = (
                min(stats.commits / 10, 30)
                + min(stats.prs_merged * 5, 25)
                + min(stats.prs_reviewed * 3, 20)
                + min(consistency / 5, 15)
                + min(repos_count * 2, 10)
            )

            analysis = ProductivityAnalysis(
                contributor=login,
                repositories=", ".join(repos_list),
                repositories_count=repos_count,
                total_commits=stats.commits,
                total_additions=stats.additions,
                total_deletions=stats.deletions,
                net_lines=net_lines,
                avg_commit_size=avg_commit_size,
                prs_opened=stats.prs_opened,
                prs_merged=stats.prs_merged,
                pr_merge_rate_pct=merge_rate,
                prs_reviewed=stats.prs_reviewed,
                issues_opened=stats.issues_opened,
                issues_closed=stats.issues_closed,
                active_days=active_days,
                commits_per_active_day=commits_per_day,
                first_activity=first_str,
                last_activity=last_str,
                activity_span_days=activity_span,
                consistency_pct=consistency,
                productivity_score=productivity_score,
            )
            analyses.append(analysis)

        # Sort by productivity score descending
        analyses.sort(key=lambda a: a.productivity_score, reverse=True)
        return analyses
