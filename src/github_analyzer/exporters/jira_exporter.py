"""Jira CSV export functionality.

This module provides the JiraExporter class for exporting Jira
issues and comments to CSV files following RFC 4180 standards.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
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
    """

    def __init__(self, output_dir: str | Path) -> None:
        """Initialize exporter with output directory.

        Creates directory if it doesn't exist.

        Args:
            output_dir: Directory for output files.
        """
        self._output_dir = Path(output_dir)
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
                writer.writerow({
                    "key": issue.key,
                    "summary": issue.summary,
                    "description": issue.description,
                    "status": issue.status,
                    "issue_type": issue.issue_type,
                    "priority": issue.priority or "",
                    "assignee": issue.assignee or "",
                    "reporter": issue.reporter,
                    "created": issue.created.isoformat() if issue.created else "",
                    "updated": issue.updated.isoformat() if issue.updated else "",
                    "resolution_date": issue.resolution_date.isoformat() if issue.resolution_date else "",
                    "project_key": issue.project_key,
                })

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
                writer.writerow({
                    "id": comment.id,
                    "issue_key": comment.issue_key,
                    "author": comment.author,
                    "created": comment.created.isoformat() if comment.created else "",
                    "body": comment.body,
                })

        return filepath
