"""CSV export functionality.

This module provides the CSVExporter class for exporting analysis
results to CSV files. All output formats match the existing tool
for backward compatibility.

Security features (Feature 006):
- Path traversal prevention via validate_output_path
- CSV formula injection protection via escape_csv_row
- Secure file permissions via set_secure_permissions
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.github_analyzer.core.security import (
    escape_csv_row,
    set_secure_permissions,
    validate_output_path,
)

if TYPE_CHECKING:
    from src.github_analyzer.api.models import (
        Commit,
        ContributorStats,
        Issue,
        ProductivityAnalysis,
        PullRequest,
        QualityMetrics,
        RepositoryStats,
    )


class CSVExporter:
    """Export analysis results to CSV files.

    Creates CSV files in the specified output directory with
    consistent naming and formatting.

    Security:
        - Output path is validated against path traversal attacks
        - CSV cell values are escaped to prevent formula injection
        - Output files are created with restrictive permissions
    """

    def __init__(self, output_dir: str | Path) -> None:
        """Initialize exporter with output directory.

        Creates directory if it doesn't exist.

        Args:
            output_dir: Directory for output files.

        Raises:
            ValidationError: If output_dir is outside safe boundary.
        """
        # Validate output path before creating directory (FR-001)
        self._output_dir = validate_output_path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def _write_csv(
        self,
        filename: str,
        fieldnames: list[str],
        rows: list[dict[str, Any]],
    ) -> Path:
        """Write data to CSV file.

        Applies formula injection protection to all cell values
        and sets secure file permissions on output.

        Args:
            filename: Name of output file.
            fieldnames: Column headers.
            rows: Data rows as dictionaries.

        Returns:
            Path to created file.
        """
        filepath = self._output_dir / filename
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            # Apply formula injection protection to each row (FR-004)
            for row in rows:
                writer.writerow(escape_csv_row(row))

        # Set secure file permissions (FR-008)
        set_secure_permissions(filepath)
        return filepath

    def export_commits(self, commits: list[Commit]) -> Path:
        """Export commits to commits_export.csv.

        Args:
            commits: List of Commit objects.

        Returns:
            Path to created file.
        """
        fieldnames = [
            "repository",
            "sha",
            "short_sha",
            "author_login",
            "author_email",
            "committer_login",
            "date",
            "message",
            "additions",
            "deletions",
            "total_changes",
            "files_changed",
            "is_merge_commit",
            "is_revert",
            "file_types",
            "url",
        ]

        rows = []
        for commit in commits:
            rows.append({
                "repository": commit.repository,
                "sha": commit.sha,
                "short_sha": commit.short_sha,
                "author_login": commit.author_login,
                "author_email": commit.author_email,
                "committer_login": commit.committer_login,
                "date": commit.date.isoformat() if commit.date else "",
                "message": commit.message,
                "additions": commit.additions,
                "deletions": commit.deletions,
                "total_changes": commit.total_changes,
                "files_changed": commit.files_changed,
                "is_merge_commit": commit.is_merge_commit,
                "is_revert": commit.is_revert,
                "file_types": str(commit.file_types),
                "url": commit.url,
            })

        return self._write_csv("commits_export.csv", fieldnames, rows)

    def export_pull_requests(self, prs: list[PullRequest]) -> Path:
        """Export PRs to pull_requests_export.csv.

        Args:
            prs: List of PullRequest objects.

        Returns:
            Path to created file.
        """
        fieldnames = [
            "repository",
            "number",
            "title",
            "state",
            "author_login",
            "created_at",
            "updated_at",
            "closed_at",
            "merged_at",
            "is_merged",
            "is_draft",
            "time_to_merge_hours",
            "reviewers_count",
            "approvals",
            "changes_requested",
            "url",
        ]

        rows = []
        for pr in prs:
            rows.append({
                "repository": pr.repository,
                "number": pr.number,
                "title": pr.title,
                "state": pr.state,
                "author_login": pr.author_login,
                "created_at": pr.created_at.isoformat() if pr.created_at else "",
                "updated_at": pr.updated_at.isoformat() if pr.updated_at else "",
                "closed_at": pr.closed_at.isoformat() if pr.closed_at else "",
                "merged_at": pr.merged_at.isoformat() if pr.merged_at else "",
                "is_merged": pr.is_merged,
                "is_draft": pr.is_draft,
                "time_to_merge_hours": pr.time_to_merge_hours or "",
                "reviewers_count": pr.reviewers_count,
                "approvals": pr.approvals,
                "changes_requested": pr.changes_requested,
                "url": pr.url,
            })

        return self._write_csv("pull_requests_export.csv", fieldnames, rows)

    def export_issues(self, issues: list[Issue]) -> Path:
        """Export issues to issues_export.csv.

        Args:
            issues: List of Issue objects.

        Returns:
            Path to created file.
        """
        fieldnames = [
            "repository",
            "number",
            "title",
            "state",
            "author_login",
            "created_at",
            "closed_at",
            "labels",
            "assignees",
            "comments_count",
            "time_to_close_hours",
            "is_bug",
            "is_enhancement",
            "url",
        ]

        rows = []
        for issue in issues:
            rows.append({
                "repository": issue.repository,
                "number": issue.number,
                "title": issue.title,
                "state": issue.state,
                "author_login": issue.author_login,
                "created_at": issue.created_at.isoformat() if issue.created_at else "",
                "closed_at": issue.closed_at.isoformat() if issue.closed_at else "",
                "labels": ", ".join(issue.labels),
                "assignees": ", ".join(issue.assignees),
                "comments_count": issue.comments,
                "time_to_close_hours": issue.time_to_close_hours or "",
                "is_bug": issue.is_bug,
                "is_enhancement": issue.is_enhancement,
                "url": issue.url,
            })

        return self._write_csv("issues_export.csv", fieldnames, rows)

    def export_repository_summary(self, stats: list[RepositoryStats]) -> Path:
        """Export repository stats to repository_summary.csv.

        Args:
            stats: List of RepositoryStats objects.

        Returns:
            Path to created file.
        """
        fieldnames = [
            "repository",
            "total_commits",
            "merge_commits",
            "revert_commits",
            "regular_commits",
            "total_additions",
            "total_deletions",
            "net_lines",
            "unique_authors",
            "total_prs",
            "merged_prs",
            "open_prs",
            "pr_merge_rate",
            "avg_time_to_merge_hours",
            "total_issues",
            "closed_issues",
            "open_issues",
            "bug_issues",
            "issue_close_rate",
            "analysis_period_days",
        ]

        rows = []
        for stat in stats:
            rows.append({
                "repository": stat.repository,
                "total_commits": stat.total_commits,
                "merge_commits": stat.merge_commits,
                "revert_commits": stat.revert_commits,
                "regular_commits": stat.regular_commits,
                "total_additions": stat.total_additions,
                "total_deletions": stat.total_deletions,
                "net_lines": stat.net_lines,
                "unique_authors": stat.unique_authors,
                "total_prs": stat.total_prs,
                "merged_prs": stat.merged_prs,
                "open_prs": stat.open_prs,
                "pr_merge_rate": f"{stat.pr_merge_rate:.1f}",
                "avg_time_to_merge_hours": stat.avg_time_to_merge_hours or "",
                "total_issues": stat.total_issues,
                "closed_issues": stat.closed_issues,
                "open_issues": stat.open_issues,
                "bug_issues": stat.bug_issues,
                "issue_close_rate": f"{stat.issue_close_rate:.1f}",
                "analysis_period_days": stat.analysis_period_days,
            })

        return self._write_csv("repository_summary.csv", fieldnames, rows)

    def export_quality_metrics(self, metrics: list[QualityMetrics]) -> Path:
        """Export quality metrics to quality_metrics.csv.

        Args:
            metrics: List of QualityMetrics objects.

        Returns:
            Path to created file.
        """
        fieldnames = [
            "repository",
            "revert_ratio_pct",
            "avg_commit_size",
            "large_commits_pct",
            "pr_review_coverage_pct",
            "approval_rate_pct",
            "change_request_rate_pct",
            "draft_prs_pct",
            "conventional_commits_pct",
            "quality_score",
        ]

        rows = []
        for metric in metrics:
            rows.append({
                "repository": metric.repository,
                "revert_ratio_pct": f"{metric.revert_ratio_pct:.1f}",
                "avg_commit_size": f"{metric.avg_commit_size_lines:.1f}",
                "large_commits_pct": f"{metric.large_commits_ratio_pct:.1f}",
                "pr_review_coverage_pct": f"{metric.pr_review_coverage_pct:.1f}",
                "approval_rate_pct": f"{metric.pr_approval_rate_pct:.1f}",
                "change_request_rate_pct": f"{metric.pr_changes_requested_ratio_pct:.1f}",
                "draft_prs_pct": f"{metric.draft_pr_ratio_pct:.1f}",
                "conventional_commits_pct": f"{metric.commit_message_quality_pct:.1f}",
                "quality_score": f"{metric.quality_score:.1f}",
            })

        return self._write_csv("quality_metrics.csv", fieldnames, rows)

    def export_productivity(self, analysis: list[ProductivityAnalysis]) -> Path:
        """Export productivity analysis to productivity_analysis.csv.

        Args:
            analysis: List of ProductivityAnalysis objects.

        Returns:
            Path to created file.
        """
        fieldnames = [
            "contributor",
            "repositories_count",
            "total_commits",
            "total_additions",
            "total_deletions",
            "prs_opened",
            "prs_merged",
            "prs_reviewed",
            "merge_rate_pct",
            "first_activity",
            "last_activity",
            "active_days",
            "consistency_pct",
            "productivity_score",
        ]

        rows = []
        for item in analysis:
            rows.append({
                "contributor": item.contributor,
                "repositories_count": item.repositories_count,
                "total_commits": item.total_commits,
                "total_additions": item.total_additions,
                "total_deletions": item.total_deletions,
                "prs_opened": item.prs_opened,
                "prs_merged": item.prs_merged,
                "prs_reviewed": item.prs_reviewed,
                "merge_rate_pct": f"{item.pr_merge_rate_pct:.1f}",
                "first_activity": item.first_activity,
                "last_activity": item.last_activity,
                "active_days": item.active_days,
                "consistency_pct": f"{item.consistency_pct:.1f}",
                "productivity_score": f"{item.productivity_score:.1f}",
            })

        return self._write_csv("productivity_analysis.csv", fieldnames, rows)

    def export_contributors(self, stats: dict[str, ContributorStats]) -> Path:
        """Export contributor summary to contributors_summary.csv.

        Args:
            stats: Dictionary mapping login to ContributorStats.

        Returns:
            Path to created file.
        """
        fieldnames = [
            "contributor",
            "repositories",
            "total_commits",
            "total_additions",
            "total_deletions",
            "prs_opened",
            "prs_merged",
            "issues_opened",
            "first_activity",
            "last_activity",
        ]

        rows = []
        for login, stat in sorted(stats.items()):
            rows.append({
                "contributor": login,
                "repositories": ", ".join(sorted(stat.repositories)),
                "total_commits": stat.commits,
                "total_additions": stat.additions,
                "total_deletions": stat.deletions,
                "prs_opened": stat.prs_opened,
                "prs_merged": stat.prs_merged,
                "issues_opened": stat.issues_opened,
                "first_activity": stat.first_activity.isoformat() if stat.first_activity else "",
                "last_activity": stat.last_activity.isoformat() if stat.last_activity else "",
            })

        return self._write_csv("contributors_summary.csv", fieldnames, rows)
