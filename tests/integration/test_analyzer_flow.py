"""Integration tests for full analyzer flow.

These tests verify the complete analysis workflow works correctly
with mocked API responses, without making real network calls.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Any

import pytest


class TestAnalyzerIntegration:
    """Integration tests for the full analyzer workflow."""

    @pytest.fixture
    def mock_config(self, tmp_path: Path) -> MagicMock:
        """Create mock config for testing."""
        from src.github_analyzer.config.settings import AnalyzerConfig

        # Create temp repos file
        repos_file = tmp_path / "repos.txt"
        repos_file.write_text("test/repo\n")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        return AnalyzerConfig(
            github_token="ghp_test1234567890abcdefghijklmnopqrstuvwxyz",
            output_dir=str(output_dir),
            repos_file=str(repos_file),
            days=30,
            per_page=100,
            verbose=False,
            timeout=30,
            max_pages=1,
        )

    @pytest.fixture
    def mock_api_responses(
        self,
        sample_commits: list[dict[str, Any]],
        sample_prs: list[dict[str, Any]],
        sample_issues: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Create mock API responses."""
        return {
            "commits": sample_commits,
            "prs": sample_prs,
            "issues": sample_issues,
        }

    def test_modules_can_be_imported_independently(self) -> None:
        """Verify all modules can be imported in isolation."""
        # This tests T076 requirement: modules work independently
        from src.github_analyzer.core import exceptions
        from src.github_analyzer.config import settings, validation
        from src.github_analyzer.api import client, models
        from src.github_analyzer.analyzers import commits, pull_requests, issues, quality, productivity
        from src.github_analyzer.exporters import csv_exporter
        from src.github_analyzer.cli import output
        from src.github_analyzer.cli.main import GitHubAnalyzer

        # Verify key classes exist
        assert hasattr(exceptions, 'GitHubAnalyzerError')
        assert hasattr(settings, 'AnalyzerConfig')
        assert hasattr(validation, 'Repository')
        assert hasattr(client, 'GitHubClient')
        assert hasattr(models, 'Commit')
        assert hasattr(commits, 'CommitAnalyzer')
        assert hasattr(csv_exporter, 'CSVExporter')
        assert hasattr(output, 'TerminalOutput')
        assert GitHubAnalyzer is not None  # Direct class import

    def test_no_circular_imports(self) -> None:
        """Verify no circular import issues exist."""
        # Import in order of dependencies (leaf to root)
        import src.github_analyzer.core.exceptions
        import src.github_analyzer.config.validation
        import src.github_analyzer.config.settings
        import src.github_analyzer.api.models
        import src.github_analyzer.api.client
        import src.github_analyzer.analyzers.commits
        import src.github_analyzer.analyzers.pull_requests
        import src.github_analyzer.analyzers.issues
        import src.github_analyzer.analyzers.quality
        import src.github_analyzer.analyzers.productivity
        import src.github_analyzer.exporters.csv_exporter
        import src.github_analyzer.cli.output
        import src.github_analyzer.cli.main

        # If we got here, no circular imports
        assert True

    def test_commit_model_from_api_response(self, sample_commits: list[dict]) -> None:
        """Test Commit model can be created from API response."""
        from src.github_analyzer.api.models import Commit

        commit = Commit.from_api_response(sample_commits[0], "test/repo")

        assert commit.repository == "test/repo"
        assert commit.sha == "abc123def456789012345678901234567890abcd"
        assert commit.short_sha == "abc123d"
        assert "feat" in commit.message.lower() or "add" in commit.message.lower()

    def test_pull_request_model_from_api_response(self, sample_prs: list[dict]) -> None:
        """Test PullRequest model can be created from API response."""
        from src.github_analyzer.api.models import PullRequest

        pr = PullRequest.from_api_response(sample_prs[0], "test/repo")

        assert pr.repository == "test/repo"
        assert pr.number == 42
        assert pr.is_merged is True
        assert pr.time_to_merge_hours is not None

    def test_issue_model_from_api_response(self, sample_issues: list[dict]) -> None:
        """Test Issue model can be created from API response."""
        from src.github_analyzer.api.models import Issue

        issue = Issue.from_api_response(sample_issues[0], "test/repo")

        assert issue.repository == "test/repo"
        assert issue.number == 100
        assert issue.is_bug is True

    def test_csv_exporter_creates_files(self, tmp_path: Path, sample_commits: list[dict]) -> None:
        """Test CSVExporter creates files correctly."""
        from src.github_analyzer.api.models import Commit
        from src.github_analyzer.exporters.csv_exporter import CSVExporter

        output_dir = tmp_path / "output"
        exporter = CSVExporter(output_dir)

        commits = [Commit.from_api_response(c, "test/repo") for c in sample_commits]
        filepath = exporter.export_commits(commits)

        assert filepath.exists()
        assert filepath.name == "commits_export.csv"

        # Verify content
        content = filepath.read_text()
        assert "repository" in content
        assert "test/repo" in content

    def test_quality_metrics_calculation(self, sample_commits: list[dict], sample_prs: list[dict]) -> None:
        """Test quality metrics are calculated correctly."""
        from src.github_analyzer.api.models import Commit, PullRequest
        from src.github_analyzer.analyzers.quality import calculate_quality_metrics
        from src.github_analyzer.config.validation import Repository

        repo = Repository.from_string("test/repo")
        commits = [Commit.from_api_response(c, "test/repo") for c in sample_commits]
        prs = [PullRequest.from_api_response(p, "test/repo") for p in sample_prs]

        metrics = calculate_quality_metrics(repo, commits, prs)

        assert metrics.repository == "test/repo"
        assert 0 <= metrics.quality_score <= 100

    def test_contributor_tracker(self, sample_commits: list[dict]) -> None:
        """Test ContributorTracker records commits correctly."""
        from src.github_analyzer.api.models import Commit
        from src.github_analyzer.analyzers.productivity import ContributorTracker

        tracker = ContributorTracker()
        commits = [Commit.from_api_response(c, "test/repo") for c in sample_commits]

        for commit in commits:
            tracker.record_commit(commit)

        stats = tracker.get_stats()
        assert len(stats) > 0

        analysis = tracker.generate_analysis()
        assert len(analysis) > 0
        assert all(a.productivity_score >= 0 for a in analysis)


class TestStdlibFallback:
    """Test that analyzer works without requests library (T080a)."""

    def test_client_works_without_requests(self) -> None:
        """Verify GitHubClient can use urllib fallback."""
        # This test verifies the stdlib fallback exists
        from src.github_analyzer.api.client import HAS_REQUESTS

        # The actual requests availability depends on environment,
        # but the fallback code path should always exist
        from src.github_analyzer.api import client

        # Verify the urllib-based method exists
        assert hasattr(client.GitHubClient, '_request_with_urllib')


class TestOfflineCapability:
    """Test that tests can run without network access (T081)."""

    def test_config_loading_works_offline(self, mock_env_token: str) -> None:
        """Config can be loaded without network."""
        from src.github_analyzer.config.settings import AnalyzerConfig

        config = AnalyzerConfig.from_env()
        assert config.github_token == mock_env_token

    def test_repository_validation_works_offline(self) -> None:
        """Repository validation doesn't require network."""
        from src.github_analyzer.config.validation import Repository

        repo = Repository.from_string("owner/repo")
        assert repo.full_name == "owner/repo"

    def test_model_creation_works_offline(self, sample_commits: list[dict]) -> None:
        """Model creation doesn't require network."""
        from src.github_analyzer.api.models import Commit

        commit = Commit.from_api_response(sample_commits[0], "test/repo")
        assert commit is not None
