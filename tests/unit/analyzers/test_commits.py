"""Tests for commit analyzer."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock

from src.github_analyzer.analyzers.commits import CommitAnalyzer
from src.github_analyzer.api.models import Commit
from src.github_analyzer.config.validation import Repository


class TestCommitAnalyzerInit:
    """Tests for CommitAnalyzer initialization."""

    def test_initializes_with_client(self):
        """Test analyzer initializes with client."""
        client = Mock()
        analyzer = CommitAnalyzer(client)
        assert analyzer._client is client


class TestCommitAnalyzerFetchAndAnalyze:
    """Tests for fetch_and_analyze method."""

    def test_fetches_commits_from_api(self):
        """Test fetches commits from GitHub API."""
        client = Mock()
        client.paginate.return_value = []
        client.get.return_value = None

        analyzer = CommitAnalyzer(client)
        repo = Repository(owner="test", name="repo")
        since = datetime.now(timezone.utc)

        result = analyzer.fetch_and_analyze(repo, since)

        client.paginate.assert_called_once()
        assert result == []

    def test_processes_commits_into_objects(self):
        """Test processes raw commits into Commit objects."""
        raw_commit = {
            "sha": "abc123def456",
            "commit": {
                "author": {
                    "name": "Test Author",
                    "email": "test@example.com",
                    "date": "2025-01-15T10:00:00Z",
                },
                "message": "Test commit message",
            },
            "author": {"login": "testuser"},
            "committer": {"login": "testuser"},
            "stats": {"additions": 10, "deletions": 5, "total": 15},
            "files": [{"filename": "test.py"}],
            "html_url": "https://github.com/test/repo/commit/abc123",
        }

        client = Mock()
        client.paginate.return_value = [{"sha": "abc123def456"}]
        client.get.return_value = raw_commit

        analyzer = CommitAnalyzer(client)
        repo = Repository(owner="test", name="repo")
        since = datetime.now(timezone.utc)

        result = analyzer.fetch_and_analyze(repo, since)

        assert len(result) == 1
        assert isinstance(result[0], Commit)
        assert result[0].sha == "abc123def456"
        assert result[0].author_login == "testuser"

    def test_handles_missing_commit_details(self):
        """Test handles when commit details fetch returns None."""
        client = Mock()
        # Return a commit with sha but no details
        client.paginate.return_value = [{"sha": "abc123def456"}]
        client.get.return_value = None

        analyzer = CommitAnalyzer(client)
        repo = Repository(owner="test", name="repo")
        since = datetime.now(timezone.utc)

        result = analyzer.fetch_and_analyze(repo, since)
        # Should still create commit from basic data
        assert len(result) == 1

    def test_fetches_details_for_each_commit(self):
        """Test fetches details for each commit."""
        raw_detail = {
            "sha": "valid123def456",
            "commit": {"author": {"date": "2025-01-15T10:00:00Z"}, "message": "test"},
            "author": {"login": "user"},
            "committer": {"login": "user"},
            "stats": {"additions": 10, "deletions": 5},
            "files": [],
        }

        client = Mock()
        client.paginate.return_value = [{"sha": "valid123def456"}]
        client.get.return_value = raw_detail

        analyzer = CommitAnalyzer(client)
        repo = Repository(owner="test", name="repo")
        since = datetime.now(timezone.utc)

        result = analyzer.fetch_and_analyze(repo, since)

        assert len(result) == 1
        assert client.get.called


class TestCommitAnalyzerGetStats:
    """Tests for get_stats method."""

    def test_returns_empty_stats_for_no_commits(self):
        """Test returns zeros for empty commit list."""
        client = Mock()
        analyzer = CommitAnalyzer(client)

        stats = analyzer.get_stats([])

        assert stats["total"] == 0
        assert stats["merge_commits"] == 0
        assert stats["revert_commits"] == 0
        assert stats["total_additions"] == 0
        assert stats["total_deletions"] == 0
        assert stats["unique_authors"] == 0

    def test_calculates_correct_stats(self):
        """Test calculates correct statistics."""
        client = Mock()
        analyzer = CommitAnalyzer(client)

        commits = [
            Commit(
                repository="test/repo",
                sha="abc123def456",
                author_login="user1",
                author_email="user1@test.com",
                committer_login="user1",
                date=datetime.now(timezone.utc),
                message="feat: add feature",
                full_message="feat: add feature",
                additions=100,
                deletions=50,
                files_changed=5,
            ),
            Commit(
                repository="test/repo",
                sha="def456ghi789",
                author_login="user2",
                author_email="user2@test.com",
                committer_login="user2",
                date=datetime.now(timezone.utc),
                message="Merge pull request #1",
                full_message="Merge pull request #1",
                additions=20,
                deletions=10,
                files_changed=2,
            ),
            Commit(
                repository="test/repo",
                sha="ghi789jkl012",
                author_login="user1",
                author_email="user1@test.com",
                committer_login="user1",
                date=datetime.now(timezone.utc),
                message="Revert \"feat: add feature\"",
                full_message="Revert \"feat: add feature\"",
                additions=50,
                deletions=100,
                files_changed=5,
            ),
        ]

        stats = analyzer.get_stats(commits)

        assert stats["total"] == 3
        assert stats["merge_commits"] == 1
        assert stats["revert_commits"] == 1
        assert stats["total_additions"] == 170
        assert stats["total_deletions"] == 160
        assert stats["unique_authors"] == 2
