"""Tests for CSV exporter."""

import pytest
import csv
from pathlib import Path
from datetime import datetime, timezone, timedelta

from src.github_analyzer.exporters.csv_exporter import CSVExporter
from src.github_analyzer.api.models import (
    Commit,
    PullRequest,
    Issue,
    RepositoryStats,
    QualityMetrics,
    ProductivityAnalysis,
    ContributorStats,
)


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Create a temporary output directory."""
    return tmp_path / "output"


class TestCSVExporterInit:
    """Tests for CSVExporter initialization."""

    def test_creates_output_directory(self, tmp_output_dir):
        """Test creates output directory if not exists."""
        assert not tmp_output_dir.exists()
        exporter = CSVExporter(tmp_output_dir)
        assert tmp_output_dir.exists()

    def test_works_with_existing_directory(self, tmp_output_dir):
        """Test works with existing directory."""
        tmp_output_dir.mkdir(parents=True)
        exporter = CSVExporter(tmp_output_dir)
        assert tmp_output_dir.exists()


class TestCSVExporterCommits:
    """Tests for export_commits method."""

    def test_exports_commits_to_csv(self, tmp_output_dir):
        """Test exports commits to CSV file."""
        exporter = CSVExporter(tmp_output_dir)
        now = datetime.now(timezone.utc)

        commits = [
            Commit(
                repository="test/repo",
                sha="abc123def456",
                author_login="user1",
                author_email="user1@test.com",
                committer_login="user1",
                date=now,
                message="Test commit",
                full_message="Test commit",
                additions=100,
                deletions=50,
                files_changed=5,
                file_types={"py": 3, "md": 2},
                url="https://github.com/test/repo/commit/abc123",
            )
        ]

        result = exporter.export_commits(commits)

        assert result.exists()
        assert result.name == "commits_export.csv"

        # Verify CSV content
        with open(result, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["sha"] == "abc123def456"
            assert rows[0]["author_login"] == "user1"

    def test_exports_empty_commits(self, tmp_output_dir):
        """Test exports empty list creates file with headers only."""
        exporter = CSVExporter(tmp_output_dir)
        result = exporter.export_commits([])

        assert result.exists()
        with open(result, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 0


class TestCSVExporterPullRequests:
    """Tests for export_pull_requests method."""

    def test_exports_prs_to_csv(self, tmp_output_dir):
        """Test exports PRs to CSV file."""
        exporter = CSVExporter(tmp_output_dir)
        now = datetime.now(timezone.utc)

        prs = [
            PullRequest(
                repository="test/repo",
                number=1,
                title="Test PR",
                state="closed",
                author_login="user1",
                created_at=now - timedelta(days=2),
                updated_at=now,
                closed_at=now,
                merged_at=now,
                is_merged=True,
                is_draft=False,
                additions=100,
                deletions=50,
                changed_files=5,
                commits=3,
                comments=2,
                review_comments=1,
                reviewers_count=2,
                approvals=1,
                changes_requested=0,
                url="https://github.com/test/repo/pull/1",
            )
        ]

        result = exporter.export_pull_requests(prs)

        assert result.exists()
        assert result.name == "pull_requests_export.csv"

        with open(result, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["number"] == "1"
            assert rows[0]["is_merged"] == "True"


class TestCSVExporterIssues:
    """Tests for export_issues method."""

    def test_exports_issues_to_csv(self, tmp_output_dir):
        """Test exports issues to CSV file."""
        exporter = CSVExporter(tmp_output_dir)
        now = datetime.now(timezone.utc)

        issues = [
            Issue(
                repository="test/repo",
                number=1,
                title="Bug report",
                state="open",
                author_login="user1",
                created_at=now,
                updated_at=now,
                closed_at=None,
                labels=["bug", "critical"],
                assignees=["user1", "user2"],
                comments=5,
                url="https://github.com/test/repo/issues/1",
            )
        ]

        result = exporter.export_issues(issues)

        assert result.exists()
        assert result.name == "issues_export.csv"

        with open(result, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["title"] == "Bug report"
            assert "bug" in rows[0]["labels"]


class TestCSVExporterRepositorySummary:
    """Tests for export_repository_summary method."""

    def test_exports_repository_stats(self, tmp_output_dir):
        """Test exports repository stats to CSV file."""
        exporter = CSVExporter(tmp_output_dir)

        stats = [
            RepositoryStats(
                repository="test/repo",
                total_commits=100,
                merge_commits=10,
                revert_commits=5,
                total_additions=5000,
                total_deletions=2000,
                unique_authors=5,
                total_prs=20,
                merged_prs=15,
                open_prs=5,
                avg_time_to_merge_hours=24.5,
                total_issues=30,
                closed_issues=25,
                open_issues=5,
                bug_issues=10,
                analysis_period_days=30,
            )
        ]

        result = exporter.export_repository_summary(stats)

        assert result.exists()
        assert result.name == "repository_summary.csv"

        with open(result, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["repository"] == "test/repo"
            assert rows[0]["total_commits"] == "100"


class TestCSVExporterQualityMetrics:
    """Tests for export_quality_metrics method."""

    def test_exports_quality_metrics(self, tmp_output_dir):
        """Test exports quality metrics to CSV file."""
        exporter = CSVExporter(tmp_output_dir)

        metrics = [
            QualityMetrics(
                repository="test/repo",
                revert_ratio_pct=5.0,
                avg_commit_size_lines=50.5,
                large_commits_count=3,
                large_commits_ratio_pct=3.0,
                pr_review_coverage_pct=90.0,
                pr_approval_rate_pct=85.0,
                pr_changes_requested_ratio_pct=15.0,
                draft_pr_ratio_pct=10.0,
                commit_message_quality_pct=80.0,
                quality_score=75.5,
            )
        ]

        result = exporter.export_quality_metrics(metrics)

        assert result.exists()
        assert result.name == "quality_metrics.csv"

        with open(result, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["quality_score"] == "75.5"


class TestCSVExporterProductivity:
    """Tests for export_productivity method."""

    def test_exports_productivity_analysis(self, tmp_output_dir):
        """Test exports productivity analysis to CSV file."""
        exporter = CSVExporter(tmp_output_dir)

        analysis = [
            ProductivityAnalysis(
                contributor="user1",
                repositories="repo1, repo2",
                repositories_count=2,
                total_commits=50,
                total_additions=1000,
                total_deletions=500,
                net_lines=500,
                avg_commit_size=30.0,
                prs_opened=10,
                prs_merged=8,
                pr_merge_rate_pct=80.0,
                prs_reviewed=5,
                issues_opened=3,
                issues_closed=2,
                active_days=15,
                commits_per_active_day=3.33,
                first_activity="2025-01-01T00:00:00",
                last_activity="2025-01-15T00:00:00",
                activity_span_days=14,
                consistency_pct=50.0,
                productivity_score=75.5,
            )
        ]

        result = exporter.export_productivity(analysis)

        assert result.exists()
        assert result.name == "productivity_analysis.csv"

        with open(result, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["contributor"] == "user1"


class TestCSVExporterContributors:
    """Tests for export_contributors method."""

    def test_exports_contributors(self, tmp_output_dir):
        """Test exports contributors to CSV file."""
        exporter = CSVExporter(tmp_output_dir)
        now = datetime.now(timezone.utc)

        stats = {
            "user1": ContributorStats(
                login="user1",
                repositories={"repo1", "repo2"},
                commits=50,
                additions=1000,
                deletions=500,
                prs_opened=10,
                prs_merged=8,
                issues_opened=3,
                first_activity=now - timedelta(days=30),
                last_activity=now,
            )
        }

        result = exporter.export_contributors(stats)

        assert result.exists()
        assert result.name == "contributors_summary.csv"

        with open(result, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["contributor"] == "user1"
            assert rows[0]["total_commits"] == "50"

    def test_exports_empty_contributors(self, tmp_output_dir):
        """Test exports empty contributors."""
        exporter = CSVExporter(tmp_output_dir)
        result = exporter.export_contributors({})

        assert result.exists()
        with open(result, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 0


class TestCSVExporterWriteCsv:
    """Tests for _write_csv method."""

    def test_writes_csv_with_headers(self, tmp_output_dir):
        """Test writes CSV with correct headers."""
        exporter = CSVExporter(tmp_output_dir)

        fieldnames = ["col1", "col2", "col3"]
        rows = [
            {"col1": "a", "col2": "b", "col3": "c"},
            {"col1": "d", "col2": "e", "col3": "f"},
        ]

        result = exporter._write_csv("test.csv", fieldnames, rows)

        assert result.exists()
        with open(result, "r") as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames
            assert header == ["col1", "col2", "col3"]
            data = list(reader)
            assert len(data) == 2

    def test_handles_special_characters(self, tmp_output_dir):
        """Test handles special characters in data."""
        exporter = CSVExporter(tmp_output_dir)

        fieldnames = ["message"]
        rows = [{"message": "Fix: 'bug' with \"quotes\" and,commas"}]

        result = exporter._write_csv("special.csv", fieldnames, rows)

        with open(result, "r") as f:
            reader = csv.DictReader(f)
            data = list(reader)
            assert "Fix:" in data[0]["message"]
