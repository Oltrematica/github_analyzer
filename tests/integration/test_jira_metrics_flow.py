"""Integration test for full Jira quality metrics flow.

Tests the complete pipeline from issue data to all 4 CSV exports:
- jira_issues_export.csv (with metrics columns)
- jira_project_metrics.csv
- jira_person_metrics.csv
- jira_type_metrics.csv

This test validates that all components work together correctly.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.github_analyzer.analyzers.jira_metrics import MetricsCalculator
from src.github_analyzer.api.jira_client import JiraComment, JiraIssue
from src.github_analyzer.exporters.jira_exporter import JiraExporter
from src.github_analyzer.exporters.jira_metrics_exporter import JiraMetricsExporter


def make_test_issue(
    key: str,
    project_key: str = "PROJ",
    issue_type: str = "Story",
    assignee: str | None = "John Doe",
    status: str = "Done",
    created_offset_days: int = 14,
    resolution_offset_days: int | None = 7,
    description: str = "## Description\n\nThis is a test issue with proper formatting.\n\n## Acceptance Criteria\n\n- [ ] First criterion\n- [x] Second criterion",
) -> JiraIssue:
    """Create a test JiraIssue with sensible defaults."""
    now = datetime.now(timezone.utc)
    created = datetime(2025, 11, 1, 10, 0, 0, tzinfo=timezone.utc)
    resolution = None
    if resolution_offset_days is not None:
        resolution = datetime(2025, 11, 1 + (created_offset_days - resolution_offset_days), 10, 0, 0, tzinfo=timezone.utc)

    return JiraIssue(
        key=key,
        summary=f"Test issue {key}",
        description=description,
        status=status,
        issue_type=issue_type,
        priority="Medium",
        assignee=assignee,
        reporter="Jane Smith",
        created=created,
        updated=now,
        resolution_date=resolution,
        project_key=project_key,
    )


def make_test_comment(
    comment_id: str,
    issue_key: str,
    author: str = "John Doe",
    offset_hours: int = 24,
) -> JiraComment:
    """Create a test JiraComment."""
    created = datetime(2025, 11, 2, 10, 0, 0, tzinfo=timezone.utc)
    return JiraComment(
        id=comment_id,
        issue_key=issue_key,
        author=author,
        created=created,
        body="Test comment",
    )


class TestFullMetricsFlow:
    """Integration tests for full metrics calculation and export flow."""

    def test_full_export_produces_all_files(self, tmp_path: Path) -> None:
        """Given issues with comments, export all 4 CSV files."""
        # Arrange: Create test data
        issues = [
            make_test_issue("PROJ-1", issue_type="Bug", assignee="John"),
            make_test_issue("PROJ-2", issue_type="Story", assignee="Jane"),
            make_test_issue("PROJ-3", issue_type="Bug", assignee="John"),
            make_test_issue("PROJ-4", issue_type="Task", assignee=None, status="Open", resolution_offset_days=None),
        ]

        comments_map = {
            "PROJ-1": [
                make_test_comment("1", "PROJ-1", author="Alice"),
                make_test_comment("2", "PROJ-1", author="Bob"),
            ],
            "PROJ-2": [make_test_comment("3", "PROJ-2", author="John")],
            "PROJ-3": [],  # Silent issue
            "PROJ-4": [make_test_comment("4", "PROJ-4", author="Jane")],
        }

        # Act: Calculate metrics
        calculator = MetricsCalculator()
        issue_metrics = []
        for issue in issues:
            comments = comments_map.get(issue.key, [])
            metrics = calculator.calculate_issue_metrics(issue, comments)
            issue_metrics.append(metrics)

        # Export issues with metrics
        jira_exporter = JiraExporter(tmp_path)
        issues_file = jira_exporter.export_issues_with_metrics(issue_metrics)

        # Export aggregated metrics
        metrics_exporter = JiraMetricsExporter(tmp_path)
        project_metrics = calculator.aggregate_project_metrics(issue_metrics, "PROJ")
        person_metrics = calculator.aggregate_person_metrics(issue_metrics)
        type_metrics = calculator.aggregate_type_metrics(issue_metrics)

        project_file = metrics_exporter.export_project_metrics([project_metrics])
        person_file = metrics_exporter.export_person_metrics(person_metrics)
        type_file = metrics_exporter.export_type_metrics(type_metrics)

        # Assert: All files created
        assert issues_file.exists()
        assert project_file.exists()
        assert person_file.exists()
        assert type_file.exists()

        assert issues_file.name == "jira_issues_export.csv"
        assert project_file.name == "jira_project_metrics.csv"
        assert person_file.name == "jira_person_metrics.csv"
        assert type_file.name == "jira_type_metrics.csv"

    def test_issues_export_has_all_metric_columns(self, tmp_path: Path) -> None:
        """Given issues, exported CSV has all 22 columns (12 original + 10 metrics)."""
        issues = [make_test_issue("PROJ-1")]
        comments = [make_test_comment("1", "PROJ-1")]

        calculator = MetricsCalculator()
        issue_metrics = [calculator.calculate_issue_metrics(issues[0], comments)]

        jira_exporter = JiraExporter(tmp_path)
        issues_file = jira_exporter.export_issues_with_metrics(issue_metrics)

        with open(issues_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            columns = reader.fieldnames or []

        # 12 original + 10 metric columns = 22 total
        assert len(columns) == 22

        # Verify metric columns present
        metric_cols = [
            "cycle_time_days", "aging_days", "comments_count",
            "description_quality_score", "acceptance_criteria_present",
            "comment_velocity_hours", "silent_issue", "same_day_resolution",
            "cross_team_score", "reopen_count",
        ]
        for col in metric_cols:
            assert col in columns, f"Missing column: {col}"

    def test_project_metrics_aggregation_correct(self, tmp_path: Path) -> None:
        """Given mix of issues, project aggregation is correct."""
        issues = [
            make_test_issue("PROJ-1", issue_type="Bug"),  # Resolved
            make_test_issue("PROJ-2", issue_type="Bug"),  # Resolved
            make_test_issue("PROJ-3", issue_type="Story"),  # Resolved
            make_test_issue("PROJ-4", status="Open", resolution_offset_days=None),  # Open
        ]

        calculator = MetricsCalculator()
        issue_metrics = [
            calculator.calculate_issue_metrics(issue, [])
            for issue in issues
        ]

        project_metrics = calculator.aggregate_project_metrics(issue_metrics, "PROJ")

        # 4 total, 3 resolved, 1 open
        assert project_metrics.total_issues == 4
        assert project_metrics.resolved_count == 3
        assert project_metrics.unresolved_count == 1

        # 2 bugs out of 4 = 50%
        assert project_metrics.bug_count == 2
        assert project_metrics.bug_ratio_percent == 50.0

        # All issues are silent (no comments)
        assert project_metrics.silent_issues_ratio_percent == 100.0

    def test_person_metrics_excludes_unassigned(self, tmp_path: Path) -> None:
        """Given unassigned issues, person metrics excludes them."""
        issues = [
            make_test_issue("PROJ-1", assignee="John"),
            make_test_issue("PROJ-2", assignee=None),  # Unassigned
            make_test_issue("PROJ-3", assignee="Jane"),
        ]

        calculator = MetricsCalculator()
        issue_metrics = [
            calculator.calculate_issue_metrics(issue, [])
            for issue in issues
        ]

        person_metrics = calculator.aggregate_person_metrics(issue_metrics)

        # Only John and Jane should appear (not None)
        names = {p.assignee_name for p in person_metrics}
        assert names == {"John", "Jane"}
        assert len(person_metrics) == 2

    def test_type_metrics_by_issue_type(self, tmp_path: Path) -> None:
        """Given different issue types, type metrics separates them."""
        issues = [
            make_test_issue("PROJ-1", issue_type="Bug"),
            make_test_issue("PROJ-2", issue_type="Bug"),
            make_test_issue("PROJ-3", issue_type="Story"),
            make_test_issue("PROJ-4", issue_type="Task"),
        ]

        calculator = MetricsCalculator()
        issue_metrics = [
            calculator.calculate_issue_metrics(issue, [])
            for issue in issues
        ]

        type_metrics = calculator.aggregate_type_metrics(issue_metrics)

        # 3 types: Bug, Story, Task
        types = {t.issue_type for t in type_metrics}
        assert types == {"Bug", "Story", "Task"}

        bug_metrics = next(t for t in type_metrics if t.issue_type == "Bug")
        assert bug_metrics.count == 2
        assert bug_metrics.bug_resolution_time_avg is not None  # Bug-specific field

        story_metrics = next(t for t in type_metrics if t.issue_type == "Story")
        assert story_metrics.bug_resolution_time_avg is None  # Not a bug

    def test_cross_team_score_calculated(self, tmp_path: Path) -> None:
        """Given comments from multiple authors, cross_team_score reflects collaboration."""
        issues = [make_test_issue("PROJ-1")]
        comments = [
            make_test_comment("1", "PROJ-1", author="Alice"),
            make_test_comment("2", "PROJ-1", author="Bob"),
            make_test_comment("3", "PROJ-1", author="Charlie"),
        ]

        calculator = MetricsCalculator()
        issue_metrics = calculator.calculate_issue_metrics(issues[0], comments)

        # 3 unique authors = 75 score per CROSS_TEAM_SCALE
        assert issue_metrics.cross_team_score == 75

    def test_description_quality_with_ac(self, tmp_path: Path) -> None:
        """Given well-formatted description with AC, quality score is high."""
        issue = make_test_issue(
            "PROJ-1",
            description="## Description\n\nDetailed description here with lots of content.\n\n## Acceptance Criteria\n\n- [ ] Criterion one\n- [x] Criterion two",
        )

        calculator = MetricsCalculator()
        metrics = calculator.calculate_issue_metrics(issue, [])

        # High score: 40 length + 40 AC + up to 20 formatting
        assert metrics.acceptance_criteria_present is True
        assert metrics.description_quality_score >= 80
