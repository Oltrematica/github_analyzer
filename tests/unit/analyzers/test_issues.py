"""Tests for issue analyzer."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock

from src.github_analyzer.analyzers.issues import IssueAnalyzer
from src.github_analyzer.api.models import Issue
from src.github_analyzer.config.validation import Repository


class TestIssueAnalyzerInit:
    """Tests for IssueAnalyzer initialization."""

    def test_initializes_with_client(self):
        """Test analyzer initializes with client."""
        client = Mock()
        analyzer = IssueAnalyzer(client)
        assert analyzer._client is client


class TestIssueAnalyzerFetchAndAnalyze:
    """Tests for fetch_and_analyze method."""

    def test_fetches_issues_from_api(self):
        """Test fetches issues from GitHub API."""
        client = Mock()
        client.paginate.return_value = []

        analyzer = IssueAnalyzer(client)
        repo = Repository(owner="test", name="repo")
        since = datetime.now(timezone.utc)

        result = analyzer.fetch_and_analyze(repo, since)

        client.paginate.assert_called_once()
        assert result == []

    def test_filters_out_pull_requests(self):
        """Test filters out items that are pull requests."""
        now = datetime.now(timezone.utc)
        created = now.isoformat()

        client = Mock()
        client.paginate.return_value = [
            {"number": 1, "title": "Issue", "state": "open", "created_at": created, "updated_at": created, "user": {"login": "user1"}},
            {"number": 2, "title": "PR", "state": "open", "created_at": created, "updated_at": created, "pull_request": {}, "user": {"login": "user1"}},
        ]

        analyzer = IssueAnalyzer(client)
        repo = Repository(owner="test", name="repo")
        since = now - timedelta(days=30)

        result = analyzer.fetch_and_analyze(repo, since)

        # Only issue should be included, not PR
        assert len(result) == 1
        assert result[0].number == 1

    def test_processes_issues_into_objects(self):
        """Test processes raw issues into Issue objects."""
        now = datetime.now(timezone.utc)
        created = now.isoformat()

        raw_issue = {
            "number": 1,
            "title": "Test Issue",
            "state": "open",
            "user": {"login": "testuser"},
            "created_at": created,
            "updated_at": created,
            "closed_at": None,
            "labels": [{"name": "bug"}],
            "assignees": [{"login": "assignee1"}],
            "comments": 5,
            "html_url": "https://github.com/test/repo/issues/1",
        }

        client = Mock()
        client.paginate.return_value = [raw_issue]

        analyzer = IssueAnalyzer(client)
        repo = Repository(owner="test", name="repo")
        since = now - timedelta(days=30)

        result = analyzer.fetch_and_analyze(repo, since)

        assert len(result) == 1
        assert isinstance(result[0], Issue)
        assert result[0].number == 1
        assert result[0].title == "Test Issue"
        assert result[0].author_login == "testuser"


class TestIssueAnalyzerGetStats:
    """Tests for get_stats method."""

    def test_returns_empty_stats_for_no_issues(self):
        """Test returns zeros for empty issue list."""
        client = Mock()
        analyzer = IssueAnalyzer(client)

        stats = analyzer.get_stats([])

        assert stats["total"] == 0
        assert stats["open"] == 0
        assert stats["closed"] == 0
        assert stats["bugs"] == 0
        assert stats["enhancements"] == 0
        assert stats["avg_time_to_close_hours"] is None

    def test_calculates_correct_stats(self):
        """Test calculates correct statistics."""
        client = Mock()
        analyzer = IssueAnalyzer(client)

        now = datetime.now(timezone.utc)
        issues = [
            Issue(
                repository="test/repo",
                number=1,
                title="Open Bug",
                state="open",
                author_login="user1",
                created_at=now - timedelta(days=5),
                updated_at=now,
                closed_at=None,
                labels=["bug"],
                assignees=["user1"],
                comments=2,
            ),
            Issue(
                repository="test/repo",
                number=2,
                title="Closed Enhancement",
                state="closed",
                author_login="user2",
                created_at=now - timedelta(days=10),
                updated_at=now - timedelta(days=2),
                closed_at=now - timedelta(days=2),
                labels=["enhancement"],
                assignees=[],
                comments=5,
            ),
            Issue(
                repository="test/repo",
                number=3,
                title="Closed Bug",
                state="closed",
                author_login="user3",
                created_at=now - timedelta(days=3),
                updated_at=now - timedelta(days=1),
                closed_at=now - timedelta(days=1),
                labels=["bug"],
                assignees=["user3"],
                comments=1,
            ),
        ]

        stats = analyzer.get_stats(issues)

        assert stats["total"] == 3
        assert stats["open"] == 1
        assert stats["closed"] == 2
        assert stats["bugs"] == 2
        assert stats["enhancements"] == 1
        assert stats["avg_time_to_close_hours"] is not None
