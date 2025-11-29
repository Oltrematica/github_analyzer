"""Tests for Jira CSV exporter.

Tests for:
- Export Jira issues to CSV
- Export Jira comments to CSV
- RFC 4180 CSV escaping (quotes, newlines, commas)
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.github_analyzer.api.jira_client import JiraComment, JiraIssue


class TestJiraExporterInit:
    """Tests for JiraExporter initialization."""

    def test_creates_output_directory(self, tmp_path: Path) -> None:
        """Creates output directory if not exists."""
        from src.github_analyzer.exporters.jira_exporter import JiraExporter

        output_dir = tmp_path / "output"
        assert not output_dir.exists()

        JiraExporter(output_dir)

        assert output_dir.exists()

    def test_works_with_existing_directory(self, tmp_path: Path) -> None:
        """Works with existing directory."""
        from src.github_analyzer.exporters.jira_exporter import JiraExporter

        output_dir = tmp_path / "output"
        output_dir.mkdir(parents=True)

        JiraExporter(output_dir)

        assert output_dir.exists()


class TestExportIssues:
    """Tests for export_issues method."""

    @pytest.fixture
    def sample_issues(self) -> list[JiraIssue]:
        """Sample Jira issues for testing."""
        now = datetime.now(timezone.utc)
        return [
            JiraIssue(
                key="PROJ-123",
                summary="Fix authentication bug",
                description="Users cannot log in with SSO",
                status="In Progress",
                issue_type="Bug",
                priority="High",
                assignee="John Doe",
                reporter="Jane Smith",
                created=now,
                updated=now,
                resolution_date=None,
                project_key="PROJ",
            ),
            JiraIssue(
                key="PROJ-124",
                summary="Add dark mode",
                description="",
                status="Done",
                issue_type="Story",
                priority="Medium",
                assignee=None,
                reporter="Jane Smith",
                created=now,
                updated=now,
                resolution_date=now,
                project_key="PROJ",
            ),
        ]

    def test_exports_issues_to_csv(
        self, tmp_path: Path, sample_issues: list[JiraIssue]
    ) -> None:
        """Exports issues to jira_issues_export.csv."""
        from src.github_analyzer.exporters.jira_exporter import JiraExporter

        exporter = JiraExporter(tmp_path)
        result = exporter.export_issues(sample_issues)

        assert result.exists()
        assert result.name == "jira_issues_export.csv"

    def test_csv_has_correct_columns(
        self, tmp_path: Path, sample_issues: list[JiraIssue]
    ) -> None:
        """CSV has correct column headers."""
        from src.github_analyzer.exporters.jira_exporter import (
            ISSUE_COLUMNS,
            JiraExporter,
        )

        exporter = JiraExporter(tmp_path)
        result = exporter.export_issues(sample_issues)

        with open(result, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == list(ISSUE_COLUMNS)

    def test_csv_contains_issue_data(
        self, tmp_path: Path, sample_issues: list[JiraIssue]
    ) -> None:
        """CSV contains correct issue data."""
        from src.github_analyzer.exporters.jira_exporter import JiraExporter

        exporter = JiraExporter(tmp_path)
        result = exporter.export_issues(sample_issues)

        with open(result, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["key"] == "PROJ-123"
        assert rows[0]["summary"] == "Fix authentication bug"
        assert rows[0]["status"] == "In Progress"
        assert rows[0]["issue_type"] == "Bug"
        assert rows[0]["priority"] == "High"
        assert rows[0]["assignee"] == "John Doe"
        assert rows[0]["reporter"] == "Jane Smith"
        assert rows[0]["project_key"] == "PROJ"

    def test_handles_none_values(self, tmp_path: Path) -> None:
        """Handles None values gracefully."""
        from src.github_analyzer.exporters.jira_exporter import JiraExporter

        now = datetime.now(timezone.utc)
        issues = [
            JiraIssue(
                key="PROJ-1",
                summary="Test",
                description="",
                status="Open",
                issue_type="Task",
                priority=None,  # None priority
                assignee=None,  # None assignee
                reporter="Reporter",
                created=now,
                updated=now,
                resolution_date=None,  # None resolution
                project_key="PROJ",
            )
        ]

        exporter = JiraExporter(tmp_path)
        result = exporter.export_issues(issues)

        with open(result, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert rows[0]["priority"] == ""
        assert rows[0]["assignee"] == ""
        assert rows[0]["resolution_date"] == ""

    def test_exports_empty_list(self, tmp_path: Path) -> None:
        """Exports empty list creates file with headers only."""
        from src.github_analyzer.exporters.jira_exporter import JiraExporter

        exporter = JiraExporter(tmp_path)
        result = exporter.export_issues([])

        assert result.exists()
        with open(result, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 0

    def test_formats_datetime_as_iso8601(
        self, tmp_path: Path, sample_issues: list[JiraIssue]
    ) -> None:
        """Formats datetime values as ISO 8601."""
        from src.github_analyzer.exporters.jira_exporter import JiraExporter

        exporter = JiraExporter(tmp_path)
        result = exporter.export_issues(sample_issues)

        with open(result, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should be ISO 8601 format
        created = rows[0]["created"]
        assert "T" in created
        assert "+" in created or "Z" in created


class TestExportComments:
    """Tests for export_comments method."""

    @pytest.fixture
    def sample_comments(self) -> list[JiraComment]:
        """Sample Jira comments for testing."""
        now = datetime.now(timezone.utc)
        return [
            JiraComment(
                id="10001",
                issue_key="PROJ-123",
                author="John Doe",
                created=now,
                body="This is the first comment.",
            ),
            JiraComment(
                id="10002",
                issue_key="PROJ-123",
                author="Jane Smith",
                created=now,
                body="Following up on the issue.",
            ),
        ]

    def test_exports_comments_to_csv(
        self, tmp_path: Path, sample_comments: list[JiraComment]
    ) -> None:
        """Exports comments to jira_comments_export.csv."""
        from src.github_analyzer.exporters.jira_exporter import JiraExporter

        exporter = JiraExporter(tmp_path)
        result = exporter.export_comments(sample_comments)

        assert result.exists()
        assert result.name == "jira_comments_export.csv"

    def test_csv_has_correct_columns(
        self, tmp_path: Path, sample_comments: list[JiraComment]
    ) -> None:
        """CSV has correct column headers."""
        from src.github_analyzer.exporters.jira_exporter import (
            COMMENT_COLUMNS,
            JiraExporter,
        )

        exporter = JiraExporter(tmp_path)
        result = exporter.export_comments(sample_comments)

        with open(result, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == list(COMMENT_COLUMNS)

    def test_csv_contains_comment_data(
        self, tmp_path: Path, sample_comments: list[JiraComment]
    ) -> None:
        """CSV contains correct comment data."""
        from src.github_analyzer.exporters.jira_exporter import JiraExporter

        exporter = JiraExporter(tmp_path)
        result = exporter.export_comments(sample_comments)

        with open(result, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["id"] == "10001"
        assert rows[0]["issue_key"] == "PROJ-123"
        assert rows[0]["author"] == "John Doe"
        assert rows[0]["body"] == "This is the first comment."

    def test_exports_empty_comments(self, tmp_path: Path) -> None:
        """Exports empty list creates file with headers only."""
        from src.github_analyzer.exporters.jira_exporter import JiraExporter

        exporter = JiraExporter(tmp_path)
        result = exporter.export_comments([])

        assert result.exists()
        with open(result, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 0


class TestCSVEscaping:
    """Tests for RFC 4180 CSV escaping."""

    def test_escapes_commas_in_description(self, tmp_path: Path) -> None:
        """Escapes commas in text fields."""
        from src.github_analyzer.exporters.jira_exporter import JiraExporter

        now = datetime.now(timezone.utc)
        issues = [
            JiraIssue(
                key="PROJ-1",
                summary="Fix bug, urgent",
                description="Commas, in, description",
                status="Open",
                issue_type="Bug",
                priority="High",
                assignee="User, Name",
                reporter="Reporter",
                created=now,
                updated=now,
                resolution_date=None,
                project_key="PROJ",
            )
        ]

        exporter = JiraExporter(tmp_path)
        result = exporter.export_issues(issues)

        with open(result, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert rows[0]["summary"] == "Fix bug, urgent"
        assert rows[0]["description"] == "Commas, in, description"
        assert rows[0]["assignee"] == "User, Name"

    def test_escapes_quotes_in_text(self, tmp_path: Path) -> None:
        """Escapes quotes in text fields."""
        from src.github_analyzer.exporters.jira_exporter import JiraExporter

        now = datetime.now(timezone.utc)
        issues = [
            JiraIssue(
                key="PROJ-1",
                summary='Fix "critical" bug',
                description='Error says "undefined"',
                status="Open",
                issue_type="Bug",
                priority="High",
                assignee=None,
                reporter="Reporter",
                created=now,
                updated=now,
                resolution_date=None,
                project_key="PROJ",
            )
        ]

        exporter = JiraExporter(tmp_path)
        result = exporter.export_issues(issues)

        with open(result, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert rows[0]["summary"] == 'Fix "critical" bug'
        assert rows[0]["description"] == 'Error says "undefined"'

    def test_escapes_newlines_in_text(self, tmp_path: Path) -> None:
        """Escapes newlines in text fields."""
        from src.github_analyzer.exporters.jira_exporter import JiraExporter

        now = datetime.now(timezone.utc)
        issues = [
            JiraIssue(
                key="PROJ-1",
                summary="Multi-line issue",
                description="Line 1\nLine 2\nLine 3",
                status="Open",
                issue_type="Bug",
                priority="High",
                assignee=None,
                reporter="Reporter",
                created=now,
                updated=now,
                resolution_date=None,
                project_key="PROJ",
            )
        ]

        exporter = JiraExporter(tmp_path)
        result = exporter.export_issues(issues)

        with open(result, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert "Line 1\nLine 2\nLine 3" == rows[0]["description"]

    def test_escapes_all_special_chars_together(self, tmp_path: Path) -> None:
        """Escapes commas, quotes, and newlines together."""
        from src.github_analyzer.exporters.jira_exporter import JiraExporter

        now = datetime.now(timezone.utc)
        comments = [
            JiraComment(
                id="1",
                issue_key="PROJ-1",
                author="Test User",
                created=now,
                body='He said "hello, world"\nThen left.',
            )
        ]

        exporter = JiraExporter(tmp_path)
        result = exporter.export_comments(comments)

        with open(result, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert rows[0]["body"] == 'He said "hello, world"\nThen left.'


class TestStreamingExport:
    """Tests for streaming (large dataset) exports."""

    def test_exports_many_issues_efficiently(self, tmp_path: Path) -> None:
        """Can export many issues efficiently."""
        from src.github_analyzer.exporters.jira_exporter import JiraExporter

        now = datetime.now(timezone.utc)
        issues = [
            JiraIssue(
                key=f"PROJ-{i}",
                summary=f"Issue {i}",
                description=f"Description {i}",
                status="Open",
                issue_type="Task",
                priority="Medium",
                assignee=None,
                reporter="Reporter",
                created=now,
                updated=now,
                resolution_date=None,
                project_key="PROJ",
            )
            for i in range(1000)
        ]

        exporter = JiraExporter(tmp_path)
        result = exporter.export_issues(issues)

        with open(result, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1000

    def test_exports_many_comments_efficiently(self, tmp_path: Path) -> None:
        """Can export many comments efficiently."""
        from src.github_analyzer.exporters.jira_exporter import JiraExporter

        now = datetime.now(timezone.utc)
        comments = [
            JiraComment(
                id=str(i),
                issue_key="PROJ-1",
                author="Author",
                created=now,
                body=f"Comment {i}",
            )
            for i in range(1000)
        ]

        exporter = JiraExporter(tmp_path)
        result = exporter.export_comments(comments)

        with open(result, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1000


# =============================================================================
# T015: Tests for extended CSV export columns with metrics (Feature 003)
# =============================================================================


class TestExtendedIssueExport:
    """Tests for export_issues_with_metrics method (FR-003 extended export)."""

    def test_exports_all_metric_columns(self, tmp_path: Path) -> None:
        """Extended export includes all 10 new metric columns."""
        from src.github_analyzer.analyzers.jira_metrics import IssueMetrics
        from src.github_analyzer.exporters.jira_exporter import (
            EXTENDED_ISSUE_COLUMNS,
            JiraExporter,
        )

        now = datetime(2025, 11, 15, 10, 0, 0, tzinfo=timezone.utc)
        issue = JiraIssue(
            key="PROJ-1",
            summary="Test issue",
            description="Test description",
            status="Done",
            issue_type="Story",
            priority="High",
            assignee="John Doe",
            reporter="Jane Smith",
            created=datetime(2025, 11, 1, 10, 0, 0, tzinfo=timezone.utc),
            updated=now,
            resolution_date=now,
            project_key="PROJ",
        )

        metrics = IssueMetrics(
            issue=issue,
            cycle_time_days=14.0,
            aging_days=None,
            comments_count=5,
            description_quality_score=75,
            acceptance_criteria_present=True,
            comment_velocity_hours=24.5,
            silent_issue=False,
            same_day_resolution=False,
            cross_team_score=75,
            reopen_count=1,
        )

        exporter = JiraExporter(tmp_path)
        result = exporter.export_issues_with_metrics([metrics])

        with open(result, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == list(EXTENDED_ISSUE_COLUMNS)

    def test_metric_values_correct_format(self, tmp_path: Path) -> None:
        """Metric values are formatted correctly (2 decimal floats, lowercase booleans)."""
        from src.github_analyzer.analyzers.jira_metrics import IssueMetrics
        from src.github_analyzer.exporters.jira_exporter import JiraExporter

        now = datetime(2025, 11, 15, 10, 0, 0, tzinfo=timezone.utc)
        issue = JiraIssue(
            key="PROJ-1",
            summary="Test issue",
            description="Test description",
            status="Done",
            issue_type="Story",
            priority="High",
            assignee="John Doe",
            reporter="Jane Smith",
            created=datetime(2025, 11, 1, 10, 0, 0, tzinfo=timezone.utc),
            updated=now,
            resolution_date=now,
            project_key="PROJ",
        )

        metrics = IssueMetrics(
            issue=issue,
            cycle_time_days=14.25,
            aging_days=None,
            comments_count=5,
            description_quality_score=75,
            acceptance_criteria_present=True,
            comment_velocity_hours=24.5,
            silent_issue=False,
            same_day_resolution=False,
            cross_team_score=75,
            reopen_count=1,
        )

        exporter = JiraExporter(tmp_path)
        result = exporter.export_issues_with_metrics([metrics])

        with open(result, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row = next(reader)

        # Check float format (2 decimals)
        assert row["cycle_time_days"] == "14.25"
        assert row["comment_velocity_hours"] == "24.50"

        # Check integer format
        assert row["comments_count"] == "5"
        assert row["description_quality_score"] == "75"
        assert row["cross_team_score"] == "75"
        assert row["reopen_count"] == "1"

        # Check boolean format (lowercase)
        assert row["acceptance_criteria_present"] == "true"
        assert row["silent_issue"] == "false"
        assert row["same_day_resolution"] == "false"

    def test_none_values_as_empty_string(self, tmp_path: Path) -> None:
        """None metric values are exported as empty strings."""
        from src.github_analyzer.analyzers.jira_metrics import IssueMetrics
        from src.github_analyzer.exporters.jira_exporter import JiraExporter

        now = datetime(2025, 11, 15, 10, 0, 0, tzinfo=timezone.utc)
        issue = JiraIssue(
            key="PROJ-1",
            summary="Open issue",
            description="",
            status="Open",
            issue_type="Task",
            priority=None,
            assignee=None,
            reporter="Jane Smith",
            created=datetime(2025, 11, 1, 10, 0, 0, tzinfo=timezone.utc),
            updated=now,
            resolution_date=None,
            project_key="PROJ",
        )

        metrics = IssueMetrics(
            issue=issue,
            cycle_time_days=None,  # Open issue, no cycle time
            aging_days=14.0,
            comments_count=0,
            description_quality_score=0,
            acceptance_criteria_present=False,
            comment_velocity_hours=None,  # Silent issue
            silent_issue=True,
            same_day_resolution=False,
            cross_team_score=0,
            reopen_count=0,
        )

        exporter = JiraExporter(tmp_path)
        result = exporter.export_issues_with_metrics([metrics])

        with open(result, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row = next(reader)

        # None values should be empty strings
        assert row["cycle_time_days"] == ""
        assert row["comment_velocity_hours"] == ""
        assert row["priority"] == ""
        assert row["assignee"] == ""

        # Aging should have value
        assert row["aging_days"] == "14.00"

    def test_preserves_original_columns(self, tmp_path: Path) -> None:
        """Extended export preserves all original issue columns."""
        from src.github_analyzer.analyzers.jira_metrics import IssueMetrics
        from src.github_analyzer.exporters.jira_exporter import JiraExporter

        created = datetime(2025, 11, 1, 10, 0, 0, tzinfo=timezone.utc)
        resolved = datetime(2025, 11, 15, 16, 0, 0, tzinfo=timezone.utc)
        issue = JiraIssue(
            key="PROJ-123",
            summary="Test summary",
            description="Test description with details",
            status="Done",
            issue_type="Bug",
            priority="Critical",
            assignee="Alice Johnson",
            reporter="Bob Wilson",
            created=created,
            updated=resolved,
            resolution_date=resolved,
            project_key="MYPROJ",
        )

        metrics = IssueMetrics(
            issue=issue,
            cycle_time_days=14.25,
            aging_days=None,
            comments_count=3,
            description_quality_score=60,
            acceptance_criteria_present=False,
            comment_velocity_hours=12.0,
            silent_issue=False,
            same_day_resolution=False,
            cross_team_score=50,
            reopen_count=0,
        )

        exporter = JiraExporter(tmp_path)
        result = exporter.export_issues_with_metrics([metrics])

        with open(result, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row = next(reader)

        # Check original columns preserved
        assert row["key"] == "PROJ-123"
        assert row["summary"] == "Test summary"
        assert row["description"] == "Test description with details"
        assert row["status"] == "Done"
        assert row["issue_type"] == "Bug"
        assert row["priority"] == "Critical"
        assert row["assignee"] == "Alice Johnson"
        assert row["reporter"] == "Bob Wilson"
        assert row["project_key"] == "MYPROJ"
        assert "2025-11-01" in row["created"]
        assert "2025-11-15" in row["resolution_date"]
