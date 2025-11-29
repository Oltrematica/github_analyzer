"""Unit tests for Jira metrics CSV exporters.

Tests cover: T027, T032, T036 (project, person, type metrics exports).
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.github_analyzer.analyzers.jira_metrics import (
    PersonMetrics,
    ProjectMetrics,
    TypeMetrics,
)
from src.github_analyzer.exporters.jira_metrics_exporter import (
    JiraMetricsExporter,
    PERSON_COLUMNS,
    PROJECT_COLUMNS,
    TYPE_COLUMNS,
)


# =============================================================================
# T027: Tests for project metrics CSV export
# =============================================================================


class TestProjectMetricsExport:
    """Tests for JiraMetricsExporter.export_project_metrics."""

    def test_creates_correct_file(self, tmp_path: Path) -> None:
        """Given project metrics, create jira_project_metrics.csv."""
        exporter = JiraMetricsExporter(tmp_path)
        metrics = ProjectMetrics(
            project_key="PROJ",
            total_issues=100,
            resolved_count=80,
            unresolved_count=20,
            avg_cycle_time_days=7.5,
            median_cycle_time_days=5.0,
            bug_count=25,
            bug_ratio_percent=25.0,
            same_day_resolution_rate_percent=10.0,
            avg_description_quality=70.0,
            silent_issues_ratio_percent=15.0,
            avg_comments_per_issue=3.5,
            avg_comment_velocity_hours=4.0,
            reopen_rate_percent=5.0,
        )

        result = exporter.export_project_metrics([metrics])

        assert result.name == "jira_project_metrics.csv"
        assert result.exists()

    def test_correct_columns(self, tmp_path: Path) -> None:
        """Given export, CSV has all 14 columns."""
        exporter = JiraMetricsExporter(tmp_path)
        metrics = ProjectMetrics(
            project_key="PROJ",
            total_issues=100,
            resolved_count=80,
            unresolved_count=20,
            avg_cycle_time_days=7.5,
            median_cycle_time_days=5.0,
            bug_count=25,
            bug_ratio_percent=25.0,
            same_day_resolution_rate_percent=10.0,
            avg_description_quality=70.0,
            silent_issues_ratio_percent=15.0,
            avg_comments_per_issue=3.5,
            avg_comment_velocity_hours=4.0,
            reopen_rate_percent=5.0,
        )

        result = exporter.export_project_metrics([metrics])

        with open(result, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []

        assert len(fieldnames) == 14
        assert fieldnames == list(PROJECT_COLUMNS)

    def test_float_formatting(self, tmp_path: Path) -> None:
        """Given float values, format with 2 decimal places."""
        exporter = JiraMetricsExporter(tmp_path)
        metrics = ProjectMetrics(
            project_key="PROJ",
            total_issues=100,
            resolved_count=80,
            unresolved_count=20,
            avg_cycle_time_days=7.556,  # Should round to 7.56
            median_cycle_time_days=5.0,
            bug_count=25,
            bug_ratio_percent=25.0,
            same_day_resolution_rate_percent=10.0,
            avg_description_quality=70.0,
            silent_issues_ratio_percent=15.0,
            avg_comments_per_issue=3.5,
            avg_comment_velocity_hours=4.0,
            reopen_rate_percent=5.0,
        )

        result = exporter.export_project_metrics([metrics])

        with open(result, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row = next(reader)

        assert row["avg_cycle_time_days"] == "7.56"

    def test_none_values_empty_string(self, tmp_path: Path) -> None:
        """Given None values, export as empty string."""
        exporter = JiraMetricsExporter(tmp_path)
        metrics = ProjectMetrics(
            project_key="PROJ",
            total_issues=0,
            resolved_count=0,
            unresolved_count=0,
            avg_cycle_time_days=None,
            median_cycle_time_days=None,
            bug_count=0,
            bug_ratio_percent=0.0,
            same_day_resolution_rate_percent=0.0,
            avg_description_quality=0.0,
            silent_issues_ratio_percent=0.0,
            avg_comments_per_issue=0.0,
            avg_comment_velocity_hours=None,
            reopen_rate_percent=0.0,
        )

        result = exporter.export_project_metrics([metrics])

        with open(result, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row = next(reader)

        assert row["avg_cycle_time_days"] == ""
        assert row["avg_comment_velocity_hours"] == ""

    def test_multiple_projects(self, tmp_path: Path) -> None:
        """Given multiple projects, export all rows."""
        exporter = JiraMetricsExporter(tmp_path)
        metrics = [
            ProjectMetrics(
                project_key="PROJ1",
                total_issues=50,
                resolved_count=40,
                unresolved_count=10,
                avg_cycle_time_days=5.0,
                median_cycle_time_days=4.0,
                bug_count=10,
                bug_ratio_percent=20.0,
                same_day_resolution_rate_percent=5.0,
                avg_description_quality=60.0,
                silent_issues_ratio_percent=10.0,
                avg_comments_per_issue=2.0,
                avg_comment_velocity_hours=3.0,
                reopen_rate_percent=2.0,
            ),
            ProjectMetrics(
                project_key="PROJ2",
                total_issues=100,
                resolved_count=80,
                unresolved_count=20,
                avg_cycle_time_days=10.0,
                median_cycle_time_days=8.0,
                bug_count=30,
                bug_ratio_percent=30.0,
                same_day_resolution_rate_percent=15.0,
                avg_description_quality=75.0,
                silent_issues_ratio_percent=8.0,
                avg_comments_per_issue=4.0,
                avg_comment_velocity_hours=2.0,
                reopen_rate_percent=3.0,
            ),
        ]

        result = exporter.export_project_metrics(metrics)

        with open(result, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["project_key"] == "PROJ1"
        assert rows[1]["project_key"] == "PROJ2"


# =============================================================================
# T032: Tests for person metrics CSV export
# =============================================================================


class TestPersonMetricsExport:
    """Tests for JiraMetricsExporter.export_person_metrics."""

    def test_creates_correct_file(self, tmp_path: Path) -> None:
        """Given person metrics, create jira_person_metrics.csv."""
        exporter = JiraMetricsExporter(tmp_path)
        metrics = PersonMetrics(
            assignee_name="John Doe",
            wip_count=5,
            resolved_count=25,
            total_assigned=30,
            avg_cycle_time_days=6.75,
            bug_count_assigned=8,
        )

        result = exporter.export_person_metrics([metrics])

        assert result.name == "jira_person_metrics.csv"
        assert result.exists()

    def test_correct_columns(self, tmp_path: Path) -> None:
        """Given export, CSV has all 6 columns."""
        exporter = JiraMetricsExporter(tmp_path)
        metrics = PersonMetrics(
            assignee_name="John Doe",
            wip_count=5,
            resolved_count=25,
            total_assigned=30,
            avg_cycle_time_days=6.75,
            bug_count_assigned=8,
        )

        result = exporter.export_person_metrics([metrics])

        with open(result, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []

        assert len(fieldnames) == 6
        assert fieldnames == list(PERSON_COLUMNS)

    def test_avg_cycle_time_none(self, tmp_path: Path) -> None:
        """Given no resolved issues, avg_cycle_time is empty."""
        exporter = JiraMetricsExporter(tmp_path)
        metrics = PersonMetrics(
            assignee_name="John Doe",
            wip_count=5,
            resolved_count=0,
            total_assigned=5,
            avg_cycle_time_days=None,
            bug_count_assigned=0,
        )

        result = exporter.export_person_metrics([metrics])

        with open(result, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row = next(reader)

        assert row["avg_cycle_time_days"] == ""

    def test_multiple_persons(self, tmp_path: Path) -> None:
        """Given multiple persons, export all rows."""
        exporter = JiraMetricsExporter(tmp_path)
        metrics = [
            PersonMetrics(
                assignee_name="John Doe",
                wip_count=5,
                resolved_count=25,
                total_assigned=30,
                avg_cycle_time_days=6.75,
                bug_count_assigned=8,
            ),
            PersonMetrics(
                assignee_name="Jane Smith",
                wip_count=3,
                resolved_count=40,
                total_assigned=43,
                avg_cycle_time_days=5.5,
                bug_count_assigned=12,
            ),
        ]

        result = exporter.export_person_metrics(metrics)

        with open(result, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        names = {row["assignee_name"] for row in rows}
        assert names == {"John Doe", "Jane Smith"}


# =============================================================================
# T036: Tests for type metrics CSV export
# =============================================================================


class TestTypeMetricsExport:
    """Tests for JiraMetricsExporter.export_type_metrics."""

    def test_creates_correct_file(self, tmp_path: Path) -> None:
        """Given type metrics, create jira_type_metrics.csv."""
        exporter = JiraMetricsExporter(tmp_path)
        metrics = TypeMetrics(
            issue_type="Bug",
            count=45,
            resolved_count=40,
            avg_cycle_time_days=4.5,
            bug_resolution_time_avg=4.5,
        )

        result = exporter.export_type_metrics([metrics])

        assert result.name == "jira_type_metrics.csv"
        assert result.exists()

    def test_correct_columns(self, tmp_path: Path) -> None:
        """Given export, CSV has all 5 columns."""
        exporter = JiraMetricsExporter(tmp_path)
        metrics = TypeMetrics(
            issue_type="Bug",
            count=45,
            resolved_count=40,
            avg_cycle_time_days=4.5,
            bug_resolution_time_avg=4.5,
        )

        result = exporter.export_type_metrics([metrics])

        with open(result, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []

        assert len(fieldnames) == 5
        assert fieldnames == list(TYPE_COLUMNS)

    def test_bug_resolution_empty_for_non_bug(self, tmp_path: Path) -> None:
        """Given non-Bug type, bug_resolution_time_avg is empty."""
        exporter = JiraMetricsExporter(tmp_path)
        metrics = TypeMetrics(
            issue_type="Story",
            count=60,
            resolved_count=50,
            avg_cycle_time_days=8.25,
            bug_resolution_time_avg=None,
        )

        result = exporter.export_type_metrics([metrics])

        with open(result, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row = next(reader)

        assert row["bug_resolution_time_avg"] == ""

    def test_multiple_types(self, tmp_path: Path) -> None:
        """Given multiple types, export all rows."""
        exporter = JiraMetricsExporter(tmp_path)
        metrics = [
            TypeMetrics(
                issue_type="Bug",
                count=45,
                resolved_count=40,
                avg_cycle_time_days=4.5,
                bug_resolution_time_avg=4.5,
            ),
            TypeMetrics(
                issue_type="Story",
                count=60,
                resolved_count=50,
                avg_cycle_time_days=8.25,
                bug_resolution_time_avg=None,
            ),
            TypeMetrics(
                issue_type="Task",
                count=35,
                resolved_count=25,
                avg_cycle_time_days=3.0,
                bug_resolution_time_avg=None,
            ),
        ]

        result = exporter.export_type_metrics(metrics)

        with open(result, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3
        types = {row["issue_type"] for row in rows}
        assert types == {"Bug", "Story", "Task"}
