"""Tests for API models."""

import pytest
from datetime import datetime, timezone, timedelta

from src.github_analyzer.api.models import (
    Commit,
    PullRequest,
    Issue,
    RepositoryStats,
    QualityMetrics,
    ContributorStats,
    ProductivityAnalysis,
    _parse_datetime,
    _safe_get,
)


class TestParseDatetime:
    """Tests for _parse_datetime helper."""

    def test_parses_iso_format_with_z(self):
        """Test parses ISO format with Z suffix."""
        result = _parse_datetime("2025-01-15T10:30:00Z")
        assert result is not None
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15

    def test_parses_iso_format_with_offset(self):
        """Test parses ISO format with timezone offset."""
        result = _parse_datetime("2025-01-15T10:30:00+00:00")
        assert result is not None
        assert result.year == 2025

    def test_returns_none_for_none_input(self):
        """Test returns None for None input."""
        result = _parse_datetime(None)
        assert result is None

    def test_returns_datetime_as_is(self):
        """Test returns datetime object unchanged."""
        now = datetime.now(timezone.utc)
        result = _parse_datetime(now)
        assert result is now

    def test_returns_none_for_invalid_format(self):
        """Test returns None for invalid format."""
        result = _parse_datetime("invalid-date")
        assert result is None


class TestSafeGet:
    """Tests for _safe_get helper."""

    def test_gets_nested_value(self):
        """Test gets deeply nested value."""
        data = {"level1": {"level2": {"level3": "value"}}}
        result = _safe_get(data, "level1", "level2", "level3")
        assert result == "value"

    def test_returns_default_for_missing_key(self):
        """Test returns default for missing key."""
        data = {"key1": "value1"}
        result = _safe_get(data, "key2", default="default")
        assert result == "default"

    def test_returns_default_for_none_value(self):
        """Test returns default when value is None."""
        data = {"key1": None}
        result = _safe_get(data, "key1", default="default")
        assert result == "default"

    def test_returns_default_for_non_dict(self):
        """Test returns default when traversing non-dict."""
        data = {"key1": "not_a_dict"}
        result = _safe_get(data, "key1", "key2", default="default")
        assert result == "default"


class TestCommit:
    """Tests for Commit model."""

    def test_short_sha_property(self):
        """Test short_sha returns first 7 chars."""
        commit = Commit(
            repository="test/repo",
            sha="abc123def456ghi789",
            author_login="user",
            author_email="user@test.com",
            committer_login="user",
            date=datetime.now(timezone.utc),
            message="test",
            full_message="test",
            additions=10,
            deletions=5,
            files_changed=1,
        )
        assert commit.short_sha == "abc123d"

    def test_total_changes_property(self):
        """Test total_changes is sum of additions and deletions."""
        commit = Commit(
            repository="test/repo",
            sha="abc123",
            author_login="user",
            author_email="user@test.com",
            committer_login="user",
            date=datetime.now(timezone.utc),
            message="test",
            full_message="test",
            additions=100,
            deletions=50,
            files_changed=1,
        )
        assert commit.total_changes == 150

    def test_is_merge_commit_property(self):
        """Test is_merge_commit for merge commits."""
        commit = Commit(
            repository="test/repo",
            sha="abc123",
            author_login="user",
            author_email="user@test.com",
            committer_login="user",
            date=datetime.now(timezone.utc),
            message="Merge pull request #1",
            full_message="Merge pull request #1",
            additions=10,
            deletions=5,
            files_changed=1,
        )
        assert commit.is_merge_commit is True

    def test_is_not_merge_commit(self):
        """Test is_merge_commit for non-merge commits."""
        commit = Commit(
            repository="test/repo",
            sha="abc123",
            author_login="user",
            author_email="user@test.com",
            committer_login="user",
            date=datetime.now(timezone.utc),
            message="feat: add feature",
            full_message="feat: add feature",
            additions=10,
            deletions=5,
            files_changed=1,
        )
        assert commit.is_merge_commit is False

    def test_is_revert_property(self):
        """Test is_revert for revert commits."""
        commit = Commit(
            repository="test/repo",
            sha="abc123",
            author_login="user",
            author_email="user@test.com",
            committer_login="user",
            date=datetime.now(timezone.utc),
            message="Revert \"feat: add feature\"",
            full_message="Revert \"feat: add feature\"",
            additions=10,
            deletions=5,
            files_changed=1,
        )
        assert commit.is_revert is True

    def test_from_api_response(self):
        """Test from_api_response creates commit correctly."""
        data = {
            "sha": "abc123def456",
            "commit": {
                "author": {
                    "name": "Test User",
                    "email": "test@example.com",
                    "date": "2025-01-15T10:00:00Z",
                },
                "message": "Test commit\n\nDetailed description",
            },
            "author": {"login": "testuser"},
            "committer": {"login": "testuser"},
            "stats": {"additions": 100, "deletions": 50},
            "files": [{"filename": "test.py"}, {"filename": "test.js"}],
            "html_url": "https://github.com/test/repo/commit/abc123",
        }

        commit = Commit.from_api_response(data, "test/repo")

        assert commit.sha == "abc123def456"
        assert commit.author_login == "testuser"
        assert commit.message == "Test commit"
        assert commit.full_message == "Test commit\n\nDetailed description"
        assert commit.additions == 100
        assert commit.deletions == 50
        assert commit.files_changed == 2
        assert "py" in commit.file_types
        assert "js" in commit.file_types


class TestPullRequest:
    """Tests for PullRequest model."""

    def test_time_to_merge_hours_when_merged(self):
        """Test time_to_merge_hours for merged PR."""
        now = datetime.now(timezone.utc)
        created = now - timedelta(hours=48)

        pr = PullRequest(
            repository="test/repo",
            number=1,
            title="Test PR",
            state="closed",
            author_login="user",
            created_at=created,
            updated_at=now,
            closed_at=now,
            merged_at=now,
            is_merged=True,
            is_draft=False,
            additions=10,
            deletions=5,
            changed_files=1,
            commits=1,
            comments=0,
            review_comments=0,
        )

        assert pr.time_to_merge_hours is not None
        assert abs(pr.time_to_merge_hours - 48) < 0.1

    def test_time_to_merge_hours_when_not_merged(self):
        """Test time_to_merge_hours returns None when not merged."""
        now = datetime.now(timezone.utc)

        pr = PullRequest(
            repository="test/repo",
            number=1,
            title="Test PR",
            state="open",
            author_login="user",
            created_at=now,
            updated_at=now,
            closed_at=None,
            merged_at=None,
            is_merged=False,
            is_draft=False,
            additions=10,
            deletions=5,
            changed_files=1,
            commits=1,
            comments=0,
            review_comments=0,
        )

        assert pr.time_to_merge_hours is None

    def test_from_api_response(self):
        """Test from_api_response creates PR correctly."""
        data = {
            "number": 42,
            "title": "Add new feature",
            "state": "open",
            "user": {"login": "author"},
            "created_at": "2025-01-15T10:00:00Z",
            "updated_at": "2025-01-16T10:00:00Z",
            "closed_at": None,
            "merged_at": None,
            "draft": True,
            "additions": 100,
            "deletions": 50,
            "changed_files": 5,
            "commits": 3,
            "comments": 2,
            "review_comments": 1,
            "labels": [{"name": "enhancement"}],
            "requested_reviewers": [{"login": "reviewer1"}],
            "base": {"ref": "main"},
            "head": {"ref": "feature-branch"},
            "html_url": "https://github.com/test/repo/pull/42",
        }

        pr = PullRequest.from_api_response(data, "test/repo")

        assert pr.number == 42
        assert pr.title == "Add new feature"
        assert pr.author_login == "author"
        assert pr.is_draft is True
        assert pr.is_merged is False
        assert pr.labels == ["enhancement"]
        assert pr.reviewers_count == 1
        assert pr.base_branch == "main"
        assert pr.head_branch == "feature-branch"


class TestIssue:
    """Tests for Issue model."""

    def test_time_to_close_hours_when_closed(self):
        """Test time_to_close_hours for closed issue."""
        now = datetime.now(timezone.utc)
        created = now - timedelta(hours=24)

        issue = Issue(
            repository="test/repo",
            number=1,
            title="Bug",
            state="closed",
            author_login="user",
            created_at=created,
            updated_at=now,
            closed_at=now,
            comments=1,
            labels=["bug"],
        )

        assert issue.time_to_close_hours is not None
        assert abs(issue.time_to_close_hours - 24) < 0.1

    def test_time_to_close_hours_when_open(self):
        """Test time_to_close_hours returns None when open."""
        now = datetime.now(timezone.utc)

        issue = Issue(
            repository="test/repo",
            number=1,
            title="Bug",
            state="open",
            author_login="user",
            created_at=now,
            updated_at=now,
            closed_at=None,
            comments=1,
            labels=["bug"],
        )

        assert issue.time_to_close_hours is None

    def test_is_bug_property(self):
        """Test is_bug property."""
        issue = Issue(
            repository="test/repo",
            number=1,
            title="Bug",
            state="open",
            author_login="user",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            closed_at=None,
            comments=1,
            labels=["bug", "critical"],
        )
        assert issue.is_bug is True

    def test_is_enhancement_property(self):
        """Test is_enhancement property."""
        issue = Issue(
            repository="test/repo",
            number=1,
            title="Feature",
            state="open",
            author_login="user",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            closed_at=None,
            comments=1,
            labels=["enhancement"],
        )
        assert issue.is_enhancement is True

    def test_is_enhancement_with_feature_label(self):
        """Test is_enhancement with feature label."""
        issue = Issue(
            repository="test/repo",
            number=1,
            title="Feature",
            state="open",
            author_login="user",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            closed_at=None,
            comments=1,
            labels=["new feature"],
        )
        assert issue.is_enhancement is True

    def test_from_api_response(self):
        """Test from_api_response creates issue correctly."""
        data = {
            "number": 10,
            "title": "Bug report",
            "state": "open",
            "user": {"login": "reporter"},
            "created_at": "2025-01-15T10:00:00Z",
            "updated_at": "2025-01-16T10:00:00Z",
            "closed_at": None,
            "comments": 3,
            "labels": [{"name": "bug"}],
            "assignees": [{"login": "assignee1"}, {"login": "assignee2"}],
            "html_url": "https://github.com/test/repo/issues/10",
        }

        issue = Issue.from_api_response(data, "test/repo")

        assert issue.number == 10
        assert issue.title == "Bug report"
        assert issue.author_login == "reporter"
        assert issue.comments == 3
        assert issue.labels == ["bug"]
        assert issue.assignees == ["assignee1", "assignee2"]


class TestRepositoryStats:
    """Tests for RepositoryStats model."""

    def test_regular_commits_property(self):
        """Test regular_commits excludes merge and revert."""
        stats = RepositoryStats(
            repository="test/repo",
            total_commits=100,
            merge_commits=15,
            revert_commits=5,
        )
        assert stats.regular_commits == 80

    def test_net_lines_property(self):
        """Test net_lines is additions minus deletions."""
        stats = RepositoryStats(
            repository="test/repo",
            total_additions=1000,
            total_deletions=300,
        )
        assert stats.net_lines == 700

    def test_pr_merge_rate_with_prs(self):
        """Test pr_merge_rate calculation."""
        stats = RepositoryStats(
            repository="test/repo",
            total_prs=10,
            merged_prs=8,
        )
        assert stats.pr_merge_rate == 80.0

    def test_pr_merge_rate_zero_prs(self):
        """Test pr_merge_rate with zero PRs."""
        stats = RepositoryStats(repository="test/repo", total_prs=0)
        assert stats.pr_merge_rate == 0.0

    def test_issue_close_rate_with_issues(self):
        """Test issue_close_rate calculation."""
        stats = RepositoryStats(
            repository="test/repo",
            total_issues=20,
            closed_issues=15,
        )
        assert stats.issue_close_rate == 75.0

    def test_issue_close_rate_zero_issues(self):
        """Test issue_close_rate with zero issues."""
        stats = RepositoryStats(repository="test/repo", total_issues=0)
        assert stats.issue_close_rate == 0.0


class TestContributorStats:
    """Tests for ContributorStats model."""

    def test_default_values(self):
        """Test default values are set correctly."""
        stats = ContributorStats(login="user1")

        assert stats.login == "user1"
        assert stats.commits == 0
        assert stats.additions == 0
        assert stats.deletions == 0
        assert stats.prs_opened == 0
        assert stats.prs_merged == 0
        assert stats.issues_opened == 0
        assert stats.first_activity is None
        assert stats.last_activity is None
        assert len(stats.repositories) == 0
        assert len(stats.commit_days) == 0
        assert len(stats.commit_sizes) == 0


class TestProductivityAnalysis:
    """Tests for ProductivityAnalysis model."""

    def test_all_fields(self):
        """Test all fields are stored correctly."""
        analysis = ProductivityAnalysis(
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

        assert analysis.contributor == "user1"
        assert analysis.repositories_count == 2
        assert analysis.total_commits == 50
        assert analysis.productivity_score == 75.5
