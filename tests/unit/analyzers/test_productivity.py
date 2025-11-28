"""Tests for productivity analyzer."""

from datetime import datetime, timedelta, timezone

from src.github_analyzer.analyzers.productivity import ContributorTracker
from src.github_analyzer.api.models import Commit, Issue, PullRequest


class TestContributorTrackerInit:
    """Tests for ContributorTracker initialization."""

    def test_initializes_empty(self):
        """Test tracker initializes with empty state."""
        tracker = ContributorTracker()
        assert tracker._stats == {}


class TestContributorTrackerRecordCommit:
    """Tests for record_commit method."""

    def test_records_new_contributor(self):
        """Test records commit for new contributor."""
        tracker = ContributorTracker()
        now = datetime.now(timezone.utc)

        commit = Commit(
            repository="test/repo",
            sha="abc123def456",
            author_login="user1",
            author_email="user1@test.com",
            committer_login="user1",
            date=now,
            message="test commit",
            full_message="test commit",
            additions=100,
            deletions=50,
            files_changed=5,
        )

        tracker.record_commit(commit)

        assert "user1" in tracker._stats
        assert tracker._stats["user1"].commits == 1
        assert tracker._stats["user1"].additions == 100
        assert tracker._stats["user1"].deletions == 50

    def test_accumulates_for_existing_contributor(self):
        """Test accumulates stats for existing contributor."""
        tracker = ContributorTracker()
        now = datetime.now(timezone.utc)

        for i in range(3):
            commit = Commit(
                repository="test/repo",
                sha=f"abc{i}def456",
                author_login="user1",
                author_email="user1@test.com",
                committer_login="user1",
                date=now - timedelta(days=i),
                message=f"commit {i}",
                full_message=f"commit {i}",
                additions=10 * (i + 1),
                deletions=5 * (i + 1),
                files_changed=1,
            )
            tracker.record_commit(commit)

        assert tracker._stats["user1"].commits == 3
        assert tracker._stats["user1"].additions == 60  # 10 + 20 + 30
        assert tracker._stats["user1"].deletions == 30  # 5 + 10 + 15

    def test_skips_unknown_author(self):
        """Test skips commits with unknown author."""
        tracker = ContributorTracker()
        now = datetime.now(timezone.utc)

        commit = Commit(
            repository="test/repo",
            sha="abc123def456",
            author_login="unknown",
            author_email="",
            committer_login="unknown",
            date=now,
            message="test",
            full_message="test",
            additions=10,
            deletions=5,
            files_changed=1,
        )

        tracker.record_commit(commit)

        assert "unknown" not in tracker._stats


class TestContributorTrackerRecordPR:
    """Tests for record_pr method."""

    def test_records_pr_opened(self):
        """Test records PR for contributor."""
        tracker = ContributorTracker()
        now = datetime.now(timezone.utc)

        pr = PullRequest(
            repository="test/repo",
            number=1,
            title="Test PR",
            state="open",
            author_login="user1",
            created_at=now,
            updated_at=now,
            closed_at=None,
            merged_at=None,
            is_merged=False,
            is_draft=False,
            additions=100,
            deletions=50,
            changed_files=5,
            commits=3,
            comments=2,
            review_comments=1,
        )

        tracker.record_pr(pr)

        assert "user1" in tracker._stats
        assert tracker._stats["user1"].prs_opened == 1

    def test_records_merged_pr(self):
        """Test records merged PR."""
        tracker = ContributorTracker()
        now = datetime.now(timezone.utc)

        pr = PullRequest(
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
        )

        tracker.record_pr(pr)

        assert tracker._stats["user1"].prs_opened == 1
        assert tracker._stats["user1"].prs_merged == 1


class TestContributorTrackerRecordReview:
    """Tests for record_review method."""

    def test_records_review(self):
        """Test records review for contributor."""
        tracker = ContributorTracker()
        now = datetime.now(timezone.utc)

        tracker.record_review("reviewer1", "test/repo", now)

        assert "reviewer1" in tracker._stats
        assert tracker._stats["reviewer1"].prs_reviewed == 1

    def test_skips_unknown_reviewer(self):
        """Test skips unknown reviewer."""
        tracker = ContributorTracker()
        now = datetime.now(timezone.utc)

        tracker.record_review("unknown", "test/repo", now)

        assert "unknown" not in tracker._stats

    def test_skips_empty_reviewer(self):
        """Test skips empty reviewer."""
        tracker = ContributorTracker()
        now = datetime.now(timezone.utc)

        tracker.record_review("", "test/repo", now)

        assert "" not in tracker._stats


class TestContributorTrackerRecordIssue:
    """Tests for record_issue method."""

    def test_records_issue(self):
        """Test records issue for contributor."""
        tracker = ContributorTracker()
        now = datetime.now(timezone.utc)

        issue = Issue(
            repository="test/repo",
            number=1,
            title="Test Issue",
            state="open",
            author_login="user1",
            created_at=now,
            updated_at=now,
            closed_at=None,
            labels=["bug"],
            assignees=[],
            comments=0,
        )

        tracker.record_issue(issue)

        assert "user1" in tracker._stats
        assert tracker._stats["user1"].issues_opened == 1

    def test_skips_unknown_author_in_issue(self):
        """Test skips issues with unknown author."""
        tracker = ContributorTracker()
        now = datetime.now(timezone.utc)

        issue = Issue(
            repository="test/repo",
            number=1,
            title="Test Issue",
            state="open",
            author_login="unknown",
            created_at=now,
            updated_at=now,
            closed_at=None,
            labels=[],
            assignees=[],
            comments=0,
        )

        tracker.record_issue(issue)

        assert "unknown" not in tracker._stats


class TestContributorTrackerGetStats:
    """Tests for get_stats method."""

    def test_returns_empty_for_no_contributors(self):
        """Test returns empty dict for no contributors."""
        tracker = ContributorTracker()

        result = tracker.get_stats()

        assert result == {}

    def test_returns_copy_of_stats(self):
        """Test returns a copy of internal stats."""
        tracker = ContributorTracker()
        now = datetime.now(timezone.utc)

        commit = Commit(
            repository="test/repo",
            sha="abc123def456",
            author_login="user1",
            author_email="user1@test.com",
            committer_login="user1",
            date=now,
            message="test",
            full_message="test",
            additions=10,
            deletions=5,
            files_changed=1,
        )
        tracker.record_commit(commit)

        result = tracker.get_stats()

        # Modifying result shouldn't affect internal state
        del result["user1"]
        assert "user1" in tracker._stats


class TestContributorTrackerGenerateAnalysis:
    """Tests for generate_analysis method."""

    def test_returns_empty_for_no_contributors(self):
        """Test returns empty list for no contributors."""
        tracker = ContributorTracker()

        result = tracker.generate_analysis()

        assert result == []

    def test_calculates_productivity_scores(self):
        """Test calculates productivity scores for contributors."""
        tracker = ContributorTracker()
        now = datetime.now(timezone.utc)

        # Add commits for user1
        for i in range(5):
            commit = Commit(
                repository="test/repo",
                sha=f"abc{i}def456",
                author_login="user1",
                author_email="user1@test.com",
                committer_login="user1",
                date=now - timedelta(days=i),
                message=f"commit {i}",
                full_message=f"commit {i}",
                additions=50,
                deletions=25,
                files_changed=3,
            )
            tracker.record_commit(commit)

        # Add a PR for user1
        pr = PullRequest(
            repository="test/repo",
            number=1,
            title="Test PR",
            state="closed",
            author_login="user1",
            created_at=now - timedelta(days=3),
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
        )
        tracker.record_pr(pr)

        result = tracker.generate_analysis()

        assert len(result) == 1
        assert result[0].contributor == "user1"
        assert result[0].total_commits == 5
        assert result[0].prs_opened == 1
        assert result[0].prs_merged == 1
        assert result[0].productivity_score > 0

    def test_sorts_by_productivity_score(self):
        """Test results sorted by productivity score descending."""
        tracker = ContributorTracker()
        now = datetime.now(timezone.utc)

        # User1 - more active
        for i in range(10):
            commit = Commit(
                repository="test/repo",
                sha=f"u1_{i}def456",
                author_login="user1",
                author_email="user1@test.com",
                committer_login="user1",
                date=now - timedelta(days=i % 7),
                message=f"commit {i}",
                full_message=f"commit {i}",
                additions=50,
                deletions=25,
                files_changed=3,
            )
            tracker.record_commit(commit)

        # User2 - less active
        for i in range(2):
            commit = Commit(
                repository="test/repo",
                sha=f"u2_{i}def456",
                author_login="user2",
                author_email="user2@test.com",
                committer_login="user2",
                date=now - timedelta(days=i),
                message=f"commit {i}",
                full_message=f"commit {i}",
                additions=10,
                deletions=5,
                files_changed=1,
            )
            tracker.record_commit(commit)

        result = tracker.generate_analysis()

        assert len(result) == 2
        assert result[0].contributor == "user1"
        assert result[1].contributor == "user2"
        assert result[0].productivity_score >= result[1].productivity_score
