"""Quality metrics calculation module.

This module provides functions for calculating code quality metrics
from commits and pull requests data.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from src.github_analyzer.api.models import QualityMetrics

if TYPE_CHECKING:
    from src.github_analyzer.api.models import Commit, PullRequest
    from src.github_analyzer.config.validation import Repository


# Conventional commit pattern
CONVENTIONAL_COMMIT_PATTERN = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?!?:\s"
)

# Large commit threshold (lines changed)
LARGE_COMMIT_THRESHOLD = 500


def calculate_quality_metrics(
    repo: Repository,
    commits: list[Commit],
    prs: list[PullRequest],
) -> QualityMetrics:
    """Calculate quality metrics for a repository.

    Metrics include:
    - Revert ratio
    - Average commit size
    - Large commits percentage
    - PR review coverage
    - PR approval rate
    - Conventional commits percentage
    - Composite quality score

    Args:
        repo: Repository being analyzed.
        commits: List of commits.
        prs: List of pull requests.

    Returns:
        QualityMetrics instance with calculated values.
    """
    # Initialize metrics
    metrics = QualityMetrics(repository=repo.full_name)

    # Commit metrics
    if commits:
        total_commits = len(commits)
        revert_commits = sum(1 for c in commits if c.is_revert)
        commit_sizes = [c.total_changes for c in commits]
        large_commits = sum(1 for size in commit_sizes if size > LARGE_COMMIT_THRESHOLD)
        conventional = sum(
            1
            for c in commits
            if CONVENTIONAL_COMMIT_PATTERN.match(c.message)
        )

        metrics.revert_ratio_pct = (revert_commits / total_commits) * 100
        metrics.avg_commit_size_lines = sum(commit_sizes) / len(commit_sizes)
        metrics.large_commits_count = large_commits
        metrics.large_commits_ratio_pct = (large_commits / total_commits) * 100
        metrics.commit_message_quality_pct = (conventional / total_commits) * 100

    # PR metrics
    if prs:
        total_prs = len(prs)
        reviewed = sum(1 for p in prs if p.reviewers_count > 0 or p.review_comments > 0)
        approved = sum(1 for p in prs if p.approvals > 0)
        changes_requested = sum(1 for p in prs if p.changes_requested > 0)
        drafts = sum(1 for p in prs if p.is_draft)

        metrics.pr_review_coverage_pct = (reviewed / total_prs) * 100
        metrics.pr_approval_rate_pct = (approved / total_prs) * 100
        metrics.pr_changes_requested_ratio_pct = (changes_requested / total_prs) * 100
        metrics.draft_pr_ratio_pct = (drafts / total_prs) * 100

    # Calculate composite quality score
    # Formula from data-model.md:
    # quality_score = (
    #     (100 - revert_ratio_pct) * 0.20 +
    #     pr_review_coverage_pct * 0.25 +
    #     pr_approval_rate_pct * 0.20 +
    #     (100 - pr_changes_requested_ratio_pct) * 0.15 +
    #     commit_message_quality_pct * 0.20
    # )
    metrics.quality_score = (
        (100 - metrics.revert_ratio_pct) * 0.20
        + metrics.pr_review_coverage_pct * 0.25
        + metrics.pr_approval_rate_pct * 0.20
        + (100 - metrics.pr_changes_requested_ratio_pct) * 0.15
        + metrics.commit_message_quality_pct * 0.20
    )

    return metrics
