"""Tests for pull request analyzer."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock

from src.github_analyzer.analyzers.pull_requests import PullRequestAnalyzer
from src.github_analyzer.api.models import PullRequest
from src.github_analyzer.config.validation import Repository


class TestPullRequestAnalyzerInit:
    """Tests for PullRequestAnalyzer initialization."""

    def test_initializes_with_client(self):
        """Test analyzer initializes with client."""
        client = Mock()
        analyzer = PullRequestAnalyzer(client)
        assert analyzer._client is client
        assert analyzer._fetch_details is False

    def test_initializes_with_fetch_details(self):
        """Test analyzer initializes with fetch_details flag."""
        client = Mock()
        analyzer = PullRequestAnalyzer(client, fetch_details=True)
        assert analyzer._fetch_details is True


class TestPullRequestAnalyzerFetchAndAnalyze:
    """Tests for fetch_and_analyze method."""

    def test_fetches_prs_from_api(self):
        """Test fetches PRs from GitHub API."""
        client = Mock()
        client.paginate.return_value = []

        analyzer = PullRequestAnalyzer(client)
        repo = Repository(owner="test", name="repo")
        since = datetime.now(timezone.utc)

        result = analyzer.fetch_and_analyze(repo, since)

        client.paginate.assert_called_once()
        assert result == []

    def test_filters_prs_by_created_date(self):
        """Test filters PRs created before since date."""
        now = datetime.now(timezone.utc)
        old_date = (now - timedelta(days=60)).isoformat().replace("+00:00", "Z")
        new_date = (now - timedelta(days=5)).isoformat().replace("+00:00", "Z")

        client = Mock()
        client.paginate.return_value = [
            {"number": 1, "created_at": old_date, "state": "closed"},
            {"number": 2, "created_at": new_date, "state": "open"},
        ]

        analyzer = PullRequestAnalyzer(client)
        repo = Repository(owner="test", name="repo")
        since = now - timedelta(days=30)

        result = analyzer.fetch_and_analyze(repo, since)

        # Only the newer PR should be included
        assert len(result) == 1
        assert result[0].number == 2

    def test_fetches_details_when_enabled(self):
        """Test fetches full PR details when fetch_details is True."""
        now = datetime.now(timezone.utc)
        created = (now - timedelta(days=5)).isoformat().replace("+00:00", "Z")

        client = Mock()
        client.paginate.return_value = [
            {"number": 1, "created_at": created, "state": "open"}
        ]
        client.get.return_value = {
            "number": 1,
            "title": "Test PR",
            "state": "open",
            "created_at": created,
            "updated_at": created,
            "user": {"login": "testuser"},
            "additions": 100,
            "deletions": 50,
            "changed_files": 5,
        }

        analyzer = PullRequestAnalyzer(client, fetch_details=True)
        repo = Repository(owner="test", name="repo")
        since = now - timedelta(days=30)

        result = analyzer.fetch_and_analyze(repo, since)

        client.get.assert_called_once()
        assert len(result) == 1

    def test_skips_details_when_disabled(self):
        """Test skips detail fetch when fetch_details is False."""
        now = datetime.now(timezone.utc)
        created = (now - timedelta(days=5)).isoformat().replace("+00:00", "Z")

        client = Mock()
        client.paginate.return_value = [
            {"number": 1, "created_at": created, "state": "open"}
        ]

        analyzer = PullRequestAnalyzer(client, fetch_details=False)
        repo = Repository(owner="test", name="repo")
        since = now - timedelta(days=30)

        result = analyzer.fetch_and_analyze(repo, since)

        client.get.assert_not_called()
        assert len(result) == 1

    def test_handles_invalid_date_format(self):
        """Test handles PRs with invalid date format."""
        client = Mock()
        client.paginate.return_value = [
            {"number": 1, "created_at": "invalid-date", "state": "open"}
        ]

        analyzer = PullRequestAnalyzer(client)
        repo = Repository(owner="test", name="repo")
        since = datetime.now(timezone.utc) - timedelta(days=30)

        # Should not raise, should include PR
        result = analyzer.fetch_and_analyze(repo, since)
        assert len(result) == 1

    def test_handles_missing_created_at(self):
        """Test handles PRs without created_at field."""
        client = Mock()
        client.paginate.return_value = [
            {"number": 1, "state": "open"}
        ]

        analyzer = PullRequestAnalyzer(client)
        repo = Repository(owner="test", name="repo")
        since = datetime.now(timezone.utc) - timedelta(days=30)

        result = analyzer.fetch_and_analyze(repo, since)
        assert len(result) == 1


class TestPullRequestAnalyzerGetStats:
    """Tests for get_stats method."""

    def test_returns_empty_stats_for_no_prs(self):
        """Test returns zeros for empty PR list."""
        client = Mock()
        analyzer = PullRequestAnalyzer(client)

        stats = analyzer.get_stats([])

        assert stats["total"] == 0
        assert stats["merged"] == 0
        assert stats["open"] == 0
        assert stats["closed_not_merged"] == 0
        assert stats["draft"] == 0
        assert stats["avg_time_to_merge_hours"] is None

    def test_calculates_correct_stats(self):
        """Test calculates correct statistics."""
        client = Mock()
        analyzer = PullRequestAnalyzer(client)

        now = datetime.now(timezone.utc)
        prs = [
            PullRequest(
                repository="test/repo",
                number=1,
                title="Open PR",
                state="open",
                author_login="user1",
                created_at=now - timedelta(days=2),
                updated_at=now,
                closed_at=None,
                merged_at=None,
                is_merged=False,
                is_draft=True,
                additions=10,
                deletions=5,
                changed_files=2,
                commits=1,
                comments=0,
                review_comments=0,
            ),
            PullRequest(
                repository="test/repo",
                number=2,
                title="Merged PR",
                state="closed",
                author_login="user2",
                created_at=now - timedelta(days=5),
                updated_at=now - timedelta(days=1),
                closed_at=now - timedelta(days=1),
                merged_at=now - timedelta(days=1),
                is_merged=True,
                is_draft=False,
                additions=100,
                deletions=50,
                changed_files=10,
                commits=5,
                comments=2,
                review_comments=3,
            ),
            PullRequest(
                repository="test/repo",
                number=3,
                title="Closed not merged",
                state="closed",
                author_login="user3",
                created_at=now - timedelta(days=3),
                updated_at=now - timedelta(days=2),
                closed_at=now - timedelta(days=2),
                merged_at=None,
                is_merged=False,
                is_draft=False,
                additions=5,
                deletions=2,
                changed_files=1,
                commits=1,
                comments=1,
                review_comments=0,
            ),
        ]

        stats = analyzer.get_stats(prs)

        assert stats["total"] == 3
        assert stats["merged"] == 1
        assert stats["open"] == 1
        assert stats["closed_not_merged"] == 1
        assert stats["draft"] == 1
        assert stats["avg_time_to_merge_hours"] is not None
        # 4 days = 96 hours
        assert abs(stats["avg_time_to_merge_hours"] - 96) < 1
