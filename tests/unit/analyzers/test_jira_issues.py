"""Tests for Jira issue analyzer.

Tests for:
- Project summary statistics
- Issue type breakdown
- Status distribution
- Priority distribution
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.github_analyzer.api.jira_client import JiraIssue


class TestJiraIssueAnalyzerStats:
    """Tests for get_stats method."""

    @pytest.fixture
    def sample_issues(self) -> list[JiraIssue]:
        """Sample Jira issues for testing."""
        now = datetime.now(timezone.utc)
        return [
            JiraIssue(
                key="PROJ-1",
                summary="Bug in login",
                description="Login fails",
                status="Done",
                issue_type="Bug",
                priority="High",
                assignee="John",
                reporter="Jane",
                created=now,
                updated=now,
                resolution_date=now,
                project_key="PROJ",
            ),
            JiraIssue(
                key="PROJ-2",
                summary="Add feature",
                description="New feature",
                status="In Progress",
                issue_type="Story",
                priority="Medium",
                assignee="John",
                reporter="Jane",
                created=now,
                updated=now,
                resolution_date=None,
                project_key="PROJ",
            ),
            JiraIssue(
                key="PROJ-3",
                summary="Update docs",
                description="Documentation",
                status="To Do",
                issue_type="Task",
                priority="Low",
                assignee=None,
                reporter="Jane",
                created=now,
                updated=now,
                resolution_date=None,
                project_key="PROJ",
            ),
            JiraIssue(
                key="DEV-1",
                summary="Critical bug",
                description="Critical issue",
                status="Done",
                issue_type="Bug",
                priority="Critical",
                assignee="Bob",
                reporter="Alice",
                created=now,
                updated=now,
                resolution_date=now,
                project_key="DEV",
            ),
        ]

    def test_get_stats_returns_correct_totals(
        self, sample_issues: list[JiraIssue]
    ) -> None:
        """Returns correct total counts."""
        from src.github_analyzer.analyzers.jira_issues import JiraIssueAnalyzer

        analyzer = JiraIssueAnalyzer()
        stats = analyzer.get_stats(sample_issues)

        assert stats["total"] == 4

    def test_get_stats_counts_resolved(
        self, sample_issues: list[JiraIssue]
    ) -> None:
        """Counts resolved issues correctly."""
        from src.github_analyzer.analyzers.jira_issues import JiraIssueAnalyzer

        analyzer = JiraIssueAnalyzer()
        stats = analyzer.get_stats(sample_issues)

        # 2 issues have resolution_date set
        assert stats["resolved"] == 2

    def test_get_stats_counts_unresolved(
        self, sample_issues: list[JiraIssue]
    ) -> None:
        """Counts unresolved issues correctly."""
        from src.github_analyzer.analyzers.jira_issues import JiraIssueAnalyzer

        analyzer = JiraIssueAnalyzer()
        stats = analyzer.get_stats(sample_issues)

        # 2 issues without resolution_date
        assert stats["unresolved"] == 2

    def test_get_stats_groups_by_type(
        self, sample_issues: list[JiraIssue]
    ) -> None:
        """Groups issues by type."""
        from src.github_analyzer.analyzers.jira_issues import JiraIssueAnalyzer

        analyzer = JiraIssueAnalyzer()
        stats = analyzer.get_stats(sample_issues)

        assert stats["by_type"]["Bug"] == 2
        assert stats["by_type"]["Story"] == 1
        assert stats["by_type"]["Task"] == 1

    def test_get_stats_groups_by_status(
        self, sample_issues: list[JiraIssue]
    ) -> None:
        """Groups issues by status."""
        from src.github_analyzer.analyzers.jira_issues import JiraIssueAnalyzer

        analyzer = JiraIssueAnalyzer()
        stats = analyzer.get_stats(sample_issues)

        assert stats["by_status"]["Done"] == 2
        assert stats["by_status"]["In Progress"] == 1
        assert stats["by_status"]["To Do"] == 1

    def test_get_stats_groups_by_priority(
        self, sample_issues: list[JiraIssue]
    ) -> None:
        """Groups issues by priority."""
        from src.github_analyzer.analyzers.jira_issues import JiraIssueAnalyzer

        analyzer = JiraIssueAnalyzer()
        stats = analyzer.get_stats(sample_issues)

        assert stats["by_priority"]["High"] == 1
        assert stats["by_priority"]["Medium"] == 1
        assert stats["by_priority"]["Low"] == 1
        assert stats["by_priority"]["Critical"] == 1

    def test_get_stats_groups_by_project(
        self, sample_issues: list[JiraIssue]
    ) -> None:
        """Groups issues by project."""
        from src.github_analyzer.analyzers.jira_issues import JiraIssueAnalyzer

        analyzer = JiraIssueAnalyzer()
        stats = analyzer.get_stats(sample_issues)

        assert stats["by_project"]["PROJ"] == 3
        assert stats["by_project"]["DEV"] == 1

    def test_get_stats_handles_empty_list(self) -> None:
        """Handles empty issue list."""
        from src.github_analyzer.analyzers.jira_issues import JiraIssueAnalyzer

        analyzer = JiraIssueAnalyzer()
        stats = analyzer.get_stats([])

        assert stats["total"] == 0
        assert stats["resolved"] == 0
        assert stats["unresolved"] == 0
        assert stats["by_type"] == {}
        assert stats["by_status"] == {}
        assert stats["by_priority"] == {}
        assert stats["by_project"] == {}

    def test_get_stats_handles_none_priority(self) -> None:
        """Handles issues with None priority."""
        from src.github_analyzer.analyzers.jira_issues import JiraIssueAnalyzer

        now = datetime.now(timezone.utc)
        issues = [
            JiraIssue(
                key="PROJ-1",
                summary="No priority",
                description="Test",
                status="Open",
                issue_type="Task",
                priority=None,
                assignee=None,
                reporter="Test",
                created=now,
                updated=now,
                resolution_date=None,
                project_key="PROJ",
            ),
        ]

        analyzer = JiraIssueAnalyzer()
        stats = analyzer.get_stats(issues)

        # None priority should be counted as "Unset"
        assert stats["by_priority"]["Unset"] == 1


class TestJiraIssueAnalyzerProjectSummary:
    """Tests for get_project_summary method."""

    @pytest.fixture
    def multi_project_issues(self) -> list[JiraIssue]:
        """Issues across multiple projects."""
        now = datetime.now(timezone.utc)
        return [
            JiraIssue(
                key="PROJ-1", summary="Issue 1", description="",
                status="Done", issue_type="Bug", priority="High",
                assignee="John", reporter="Jane", created=now, updated=now,
                resolution_date=now, project_key="PROJ",
            ),
            JiraIssue(
                key="PROJ-2", summary="Issue 2", description="",
                status="In Progress", issue_type="Story", priority="Medium",
                assignee="John", reporter="Jane", created=now, updated=now,
                resolution_date=None, project_key="PROJ",
            ),
            JiraIssue(
                key="DEV-1", summary="Issue 3", description="",
                status="Done", issue_type="Bug", priority="Critical",
                assignee="Bob", reporter="Alice", created=now, updated=now,
                resolution_date=now, project_key="DEV",
            ),
            JiraIssue(
                key="DEV-2", summary="Issue 4", description="",
                status="To Do", issue_type="Task", priority="Low",
                assignee=None, reporter="Alice", created=now, updated=now,
                resolution_date=None, project_key="DEV",
            ),
        ]

    def test_get_project_summary_returns_per_project_stats(
        self, multi_project_issues: list[JiraIssue]
    ) -> None:
        """Returns statistics per project."""
        from src.github_analyzer.analyzers.jira_issues import JiraIssueAnalyzer

        analyzer = JiraIssueAnalyzer()
        summary = analyzer.get_project_summary(multi_project_issues)

        assert "PROJ" in summary
        assert "DEV" in summary
        assert summary["PROJ"]["total"] == 2
        assert summary["DEV"]["total"] == 2

    def test_get_project_summary_includes_resolution_rates(
        self, multi_project_issues: list[JiraIssue]
    ) -> None:
        """Includes resolution rate per project."""
        from src.github_analyzer.analyzers.jira_issues import JiraIssueAnalyzer

        analyzer = JiraIssueAnalyzer()
        summary = analyzer.get_project_summary(multi_project_issues)

        # PROJ: 1 resolved out of 2 = 50%
        assert summary["PROJ"]["resolution_rate"] == 50.0
        # DEV: 1 resolved out of 2 = 50%
        assert summary["DEV"]["resolution_rate"] == 50.0

    def test_get_project_summary_handles_empty_list(self) -> None:
        """Handles empty issue list."""
        from src.github_analyzer.analyzers.jira_issues import JiraIssueAnalyzer

        analyzer = JiraIssueAnalyzer()
        summary = analyzer.get_project_summary([])

        assert summary == {}

    def test_get_project_summary_includes_bug_count(
        self, multi_project_issues: list[JiraIssue]
    ) -> None:
        """Includes bug count per project."""
        from src.github_analyzer.analyzers.jira_issues import JiraIssueAnalyzer

        analyzer = JiraIssueAnalyzer()
        summary = analyzer.get_project_summary(multi_project_issues)

        assert summary["PROJ"]["bugs"] == 1
        assert summary["DEV"]["bugs"] == 1
