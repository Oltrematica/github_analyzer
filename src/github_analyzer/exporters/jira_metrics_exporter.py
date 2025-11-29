"""Jira metrics CSV export functionality.

This module provides the JiraMetricsExporter class for exporting
aggregated Jira metrics to CSV files following RFC 4180 standards.

Implements: T029, T030, T034, T038 per tasks.md

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
    from src.github_analyzer.analyzers.jira_metrics import (
        PersonMetrics,
        ProjectMetrics,
        TypeMetrics,
    )


# Column definitions for metrics CSV exports per contracts/csv-schemas.md
PROJECT_COLUMNS = (
    "project_key",
    "total_issues",
    "resolved_count",
    "unresolved_count",
    "avg_cycle_time_days",
    "median_cycle_time_days",
    "bug_count",
    "bug_ratio_percent",
    "same_day_resolution_rate_percent",
    "avg_description_quality",
    "silent_issues_ratio_percent",
    "avg_comments_per_issue",
    "avg_comment_velocity_hours",
    "reopen_rate_percent",
)

PERSON_COLUMNS = (
    "assignee_name",
    "wip_count",
    "resolved_count",
    "total_assigned",
    "avg_cycle_time_days",
    "bug_count_assigned",
)

TYPE_COLUMNS = (
    "issue_type",
    "count",
    "resolved_count",
    "avg_cycle_time_days",
    "bug_resolution_time_avg",
)


class JiraMetricsExporter:
    """Export aggregated Jira metrics to CSV files.

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

    def export_project_metrics(self, metrics_list: list[ProjectMetrics]) -> Path:
        """Export project metrics to jira_project_metrics.csv.

        Args:
            metrics_list: List of ProjectMetrics objects.

        Returns:
            Path to created file.
        """
        filepath = self._output_dir / "jira_project_metrics.csv"

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=PROJECT_COLUMNS)
            writer.writeheader()

            for metrics in metrics_list:
                # Apply formula injection protection to string fields (FR-004)
                writer.writerow({
                    "project_key": escape_csv_formula(metrics.project_key),
                    "total_issues": str(metrics.total_issues),
                    "resolved_count": str(metrics.resolved_count),
                    "unresolved_count": str(metrics.unresolved_count),
                    "avg_cycle_time_days": self._format_float(metrics.avg_cycle_time_days),
                    "median_cycle_time_days": self._format_float(metrics.median_cycle_time_days),
                    "bug_count": str(metrics.bug_count),
                    "bug_ratio_percent": self._format_float(metrics.bug_ratio_percent),
                    "same_day_resolution_rate_percent": self._format_float(metrics.same_day_resolution_rate_percent),
                    "avg_description_quality": self._format_float(metrics.avg_description_quality),
                    "silent_issues_ratio_percent": self._format_float(metrics.silent_issues_ratio_percent),
                    "avg_comments_per_issue": self._format_float(metrics.avg_comments_per_issue),
                    "avg_comment_velocity_hours": self._format_float(metrics.avg_comment_velocity_hours),
                    "reopen_rate_percent": self._format_float(metrics.reopen_rate_percent),
                })

        # Set secure file permissions (FR-008)
        set_secure_permissions(filepath)
        return filepath

    def export_person_metrics(self, metrics_list: list[PersonMetrics]) -> Path:
        """Export person metrics to jira_person_metrics.csv.

        Args:
            metrics_list: List of PersonMetrics objects.

        Returns:
            Path to created file.
        """
        filepath = self._output_dir / "jira_person_metrics.csv"

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=PERSON_COLUMNS)
            writer.writeheader()

            for metrics in metrics_list:
                # Apply formula injection protection to string fields (FR-004)
                writer.writerow({
                    "assignee_name": escape_csv_formula(metrics.assignee_name),
                    "wip_count": str(metrics.wip_count),
                    "resolved_count": str(metrics.resolved_count),
                    "total_assigned": str(metrics.total_assigned),
                    "avg_cycle_time_days": self._format_float(metrics.avg_cycle_time_days),
                    "bug_count_assigned": str(metrics.bug_count_assigned),
                })

        # Set secure file permissions (FR-008)
        set_secure_permissions(filepath)
        return filepath

    def export_type_metrics(self, metrics_list: list[TypeMetrics]) -> Path:
        """Export type metrics to jira_type_metrics.csv.

        Args:
            metrics_list: List of TypeMetrics objects.

        Returns:
            Path to created file.
        """
        filepath = self._output_dir / "jira_type_metrics.csv"

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=TYPE_COLUMNS)
            writer.writeheader()

            for metrics in metrics_list:
                # Apply formula injection protection to string fields (FR-004)
                writer.writerow({
                    "issue_type": escape_csv_formula(metrics.issue_type),
                    "count": str(metrics.count),
                    "resolved_count": str(metrics.resolved_count),
                    "avg_cycle_time_days": self._format_float(metrics.avg_cycle_time_days),
                    "bug_resolution_time_avg": self._format_float(metrics.bug_resolution_time_avg),
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
