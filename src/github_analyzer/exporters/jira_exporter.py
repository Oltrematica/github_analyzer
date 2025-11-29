"""Jira CSV export functionality.

This module provides the JiraExporter class for exporting Jira
issues and comments to CSV files following RFC 4180 standards.

Extended in Feature 003 to support quality metrics columns.

Security features (Feature 006):
- Path traversal prevention via validate_output_path
- CSV formula injection protection via escape_csv_formula
- Secure file permissions via set_secure_permissions
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TYPE_CHECKING

from src.github_analyzer.core.security import (
    escape_csv_formula,
    set_secure_permissions,
    validate_output_path,
)

if TYPE_CHECKING:
    from src.github_analyzer.analyzers.jira_metrics import IssueMetrics
    from src.github_analyzer.api.jira_client import JiraComment, JiraIssue


# Column definitions for CSV exports (FR-004, FR-006)
ISSUE_COLUMNS = (
    "key",
    "summary",
    "description",
    "status",
    "issue_type",
    "priority",
    "assignee",
    "reporter",
    "created",
    "updated",
    "resolution_date",
    "project_key",
)

# Extended columns with metrics (Feature 003, contracts/csv-schemas.md)
EXTENDED_ISSUE_COLUMNS = ISSUE_COLUMNS + (
    "cycle_time_days",
    "aging_days",
    "comments_count",
    "description_quality_score",
    "acceptance_criteria_present",
    "comment_velocity_hours",
    "silent_issue",
    "same_day_resolution",
    "cross_team_score",
    "reopen_count",
)

COMMENT_COLUMNS = (
    "id",
    "issue_key",
    "author",
    "created",
    "body",
)


class JiraExporter:
    """Export Jira data to CSV files.

    Creates CSV files in the specified output directory with
    consistent naming and RFC 4180 compliant formatting.

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

    def export_issues(self, issues: list[JiraIssue]) -> Path:
        """Export issues to jira_issues_export.csv.

        Args:
            issues: List of JiraIssue objects.

        Returns:
            Path to created file.
        """
        filepath = self._output_dir / "jira_issues_export.csv"

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=ISSUE_COLUMNS)
            writer.writeheader()

            for issue in issues:
                # Apply formula injection protection (FR-004)
                writer.writerow({
                    "key": escape_csv_formula(issue.key),
                    "summary": escape_csv_formula(issue.summary),
                    "description": escape_csv_formula(issue.description),
                    "status": escape_csv_formula(issue.status),
                    "issue_type": escape_csv_formula(issue.issue_type),
                    "priority": escape_csv_formula(issue.priority or ""),
                    "assignee": escape_csv_formula(issue.assignee or ""),
                    "reporter": escape_csv_formula(issue.reporter),
                    "created": issue.created.isoformat() if issue.created else "",
                    "updated": issue.updated.isoformat() if issue.updated else "",
                    "resolution_date": issue.resolution_date.isoformat() if issue.resolution_date else "",
                    "project_key": escape_csv_formula(issue.project_key),
                })

        # Set secure file permissions (FR-008)
        set_secure_permissions(filepath)
        return filepath

    def export_comments(self, comments: list[JiraComment]) -> Path:
        """Export comments to jira_comments_export.csv.

        Args:
            comments: List of JiraComment objects.

        Returns:
            Path to created file.
        """
        filepath = self._output_dir / "jira_comments_export.csv"

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=COMMENT_COLUMNS)
            writer.writeheader()

            for comment in comments:
                # Apply formula injection protection (FR-004)
                writer.writerow({
                    "id": escape_csv_formula(comment.id),
                    "issue_key": escape_csv_formula(comment.issue_key),
                    "author": escape_csv_formula(comment.author),
                    "created": comment.created.isoformat() if comment.created else "",
                    "body": escape_csv_formula(comment.body),
                })

        # Set secure file permissions (FR-008)
        set_secure_permissions(filepath)
        return filepath

    def export_issues_with_metrics(self, metrics_list: list[IssueMetrics]) -> Path:
        """Export issues with quality metrics to jira_issues_export.csv.

        Exports all original issue columns plus 10 new metric columns
        per contracts/csv-schemas.md.

        Format rules:
        - Floats: 2 decimal places
        - Booleans: lowercase "true"/"false"
        - None values: empty string

        Args:
            metrics_list: List of IssueMetrics objects.

        Returns:
            Path to created file.
        """
        filepath = self._output_dir / "jira_issues_export.csv"

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=EXTENDED_ISSUE_COLUMNS)
            writer.writeheader()

            for metrics in metrics_list:
                issue = metrics.issue
                # Apply formula injection protection (FR-004)
                writer.writerow({
                    # Original columns
                    "key": escape_csv_formula(issue.key),
                    "summary": escape_csv_formula(issue.summary),
                    "description": escape_csv_formula(issue.description),
                    "status": escape_csv_formula(issue.status),
                    "issue_type": escape_csv_formula(issue.issue_type),
                    "priority": escape_csv_formula(issue.priority or ""),
                    "assignee": escape_csv_formula(issue.assignee or ""),
                    "reporter": escape_csv_formula(issue.reporter),
                    "created": issue.created.isoformat() if issue.created else "",
                    "updated": issue.updated.isoformat() if issue.updated else "",
                    "resolution_date": issue.resolution_date.isoformat() if issue.resolution_date else "",
                    "project_key": escape_csv_formula(issue.project_key),
                    # Metric columns (numeric - no escaping needed)
                    "cycle_time_days": self._format_float(metrics.cycle_time_days),
                    "aging_days": self._format_float(metrics.aging_days),
                    "comments_count": str(metrics.comments_count),
                    "description_quality_score": str(metrics.description_quality_score),
                    "acceptance_criteria_present": self._format_bool(metrics.acceptance_criteria_present),
                    "comment_velocity_hours": self._format_float(metrics.comment_velocity_hours),
                    "silent_issue": self._format_bool(metrics.silent_issue),
                    "same_day_resolution": self._format_bool(metrics.same_day_resolution),
                    "cross_team_score": str(metrics.cross_team_score),
                    "reopen_count": str(metrics.reopen_count),
                })

        # Set secure file permissions (FR-008)
        set_secure_permissions(filepath)
        return filepath

    @staticmethod
    def _format_float(value: float | None) -> str:
        """Format float with 2 decimal places, or empty string if None."""
        if value is None:
            return ""
        return f"{value:.2f}"

    @staticmethod
    def _format_bool(value: bool) -> str:
        """Format boolean as lowercase 'true' or 'false'."""
        return "true" if value else "false"
