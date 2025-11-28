"""Tests for quality metrics calculation module."""

from datetime import datetime, timezone

import pytest
from src.github_analyzer.analyzers.quality import (
    CONVENTIONAL_COMMIT_PATTERN,
    calculate_quality_metrics,
)
from src.github_analyzer.api.models import Commit, PullRequest, QualityMetrics
from src.github_analyzer.config.validation import Repository


@pytest.fixture
def sample_repo():
    """Create a sample repository."""
    return Repository(owner="test", name="repo")


@pytest.fixture
def sample_commit():
    """Create a sample commit."""
    return Commit(
        repository="test/repo",
        sha="abc123",
        author_login="user1",
        author_email="user1@test.com",
        committer_login="user1",
        date=datetime.now(timezone.utc),
        message="feat: add new feature",
        full_message="feat: add new feature\n\nDetails here",
        additions=50,
        deletions=20,
        files_changed=3,
    )


@pytest.fixture
def sample_pr():
    """Create a sample PR."""
    return PullRequest(
        repository="test/repo",
        number=1,
        title="Test PR",
        state="closed",
        author_login="user1",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        closed_at=datetime.now(timezone.utc),
        merged_at=datetime.now(timezone.utc),
        is_merged=True,
        is_draft=False,
        additions=100,
        deletions=50,
        changed_files=5,
        commits=3,
        comments=2,
        review_comments=1,
        reviewers_count=1,
        approvals=1,
    )


class TestConventionalCommitPattern:
    """Tests for CONVENTIONAL_COMMIT_PATTERN regex."""

    def test_matches_feat(self):
        """Test matches 'feat' prefix."""
        assert CONVENTIONAL_COMMIT_PATTERN.match("feat: add new feature")

    def test_matches_fix(self):
        """Test matches 'fix' prefix."""
        assert CONVENTIONAL_COMMIT_PATTERN.match("fix: resolve bug")

    def test_matches_docs(self):
        """Test matches 'docs' prefix."""
        assert CONVENTIONAL_COMMIT_PATTERN.match("docs: update readme")

    def test_matches_style(self):
        """Test matches 'style' prefix."""
        assert CONVENTIONAL_COMMIT_PATTERN.match("style: format code")

    def test_matches_refactor(self):
        """Test matches 'refactor' prefix."""
        assert CONVENTIONAL_COMMIT_PATTERN.match("refactor: simplify logic")

    def test_matches_perf(self):
        """Test matches 'perf' prefix."""
        assert CONVENTIONAL_COMMIT_PATTERN.match("perf: improve speed")

    def test_matches_test(self):
        """Test matches 'test' prefix."""
        assert CONVENTIONAL_COMMIT_PATTERN.match("test: add unit tests")

    def test_matches_build(self):
        """Test matches 'build' prefix."""
        assert CONVENTIONAL_COMMIT_PATTERN.match("build: update dependencies")

    def test_matches_ci(self):
        """Test matches 'ci' prefix."""
        assert CONVENTIONAL_COMMIT_PATTERN.match("ci: add github action")

    def test_matches_chore(self):
        """Test matches 'chore' prefix."""
        assert CONVENTIONAL_COMMIT_PATTERN.match("chore: cleanup files")

    def test_matches_revert(self):
        """Test matches 'revert' prefix."""
        assert CONVENTIONAL_COMMIT_PATTERN.match("revert: undo change")

    def test_matches_with_scope(self):
        """Test matches with scope."""
        assert CONVENTIONAL_COMMIT_PATTERN.match("feat(api): add endpoint")

    def test_matches_breaking_change(self):
        """Test matches breaking change marker."""
        assert CONVENTIONAL_COMMIT_PATTERN.match("feat!: breaking change")
        assert CONVENTIONAL_COMMIT_PATTERN.match("feat(api)!: breaking change")

    def test_not_matches_invalid(self):
        """Test doesn't match invalid messages."""
        assert not CONVENTIONAL_COMMIT_PATTERN.match("Add new feature")
        assert not CONVENTIONAL_COMMIT_PATTERN.match("WIP: work in progress")
        assert not CONVENTIONAL_COMMIT_PATTERN.match("Update code")


class TestCalculateQualityMetrics:
    """Tests for calculate_quality_metrics function."""

    def test_returns_quality_metrics(self, sample_repo, sample_commit, sample_pr):
        """Test returns QualityMetrics instance."""
        result = calculate_quality_metrics(sample_repo, [sample_commit], [sample_pr])

        assert isinstance(result, QualityMetrics)
        assert result.repository == "test/repo"

    def test_handles_empty_commits(self, sample_repo, sample_pr):
        """Test handles empty commits list."""
        result = calculate_quality_metrics(sample_repo, [], [sample_pr])

        assert result.revert_ratio_pct == 0.0
        assert result.avg_commit_size_lines == 0.0
        assert result.large_commits_count == 0

    def test_handles_empty_prs(self, sample_repo, sample_commit):
        """Test handles empty PRs list."""
        result = calculate_quality_metrics(sample_repo, [sample_commit], [])

        assert result.pr_review_coverage_pct == 0.0
        assert result.pr_approval_rate_pct == 0.0

    def test_handles_both_empty(self, sample_repo):
        """Test handles both empty lists."""
        result = calculate_quality_metrics(sample_repo, [], [])

        assert result.repository == "test/repo"
        assert result.quality_score >= 0

    def test_calculates_revert_ratio(self, sample_repo):
        """Test calculates revert ratio correctly."""
        commits = [
            Commit(
                repository="test/repo", sha="1", author_login="u", author_email="u@e.com",
                committer_login="u", date=datetime.now(timezone.utc),
                message="feat: feature", full_message="feat: feature",
                additions=10, deletions=5, files_changed=1,
            ),
            Commit(
                repository="test/repo", sha="2", author_login="u", author_email="u@e.com",
                committer_login="u", date=datetime.now(timezone.utc),
                message="Revert \"feat: feature\"", full_message="Revert \"feat: feature\"",
                additions=5, deletions=10, files_changed=1,
            ),
        ]

        result = calculate_quality_metrics(sample_repo, commits, [])

        assert result.revert_ratio_pct == 50.0

    def test_calculates_avg_commit_size(self, sample_repo):
        """Test calculates average commit size correctly."""
        commits = [
            Commit(
                repository="test/repo", sha="1", author_login="u", author_email="u@e.com",
                committer_login="u", date=datetime.now(timezone.utc),
                message="feat: a", full_message="feat: a",
                additions=100, deletions=50, files_changed=1,
            ),
            Commit(
                repository="test/repo", sha="2", author_login="u", author_email="u@e.com",
                committer_login="u", date=datetime.now(timezone.utc),
                message="feat: b", full_message="feat: b",
                additions=50, deletions=50, files_changed=1,
            ),
        ]

        result = calculate_quality_metrics(sample_repo, commits, [])

        # (100+50 + 50+50) / 2 = 250 / 2 = 125
        assert result.avg_commit_size_lines == 125.0

    def test_counts_large_commits(self, sample_repo):
        """Test counts large commits correctly."""
        commits = [
            Commit(
                repository="test/repo", sha="1", author_login="u", author_email="u@e.com",
                committer_login="u", date=datetime.now(timezone.utc),
                message="feat: small", full_message="feat: small",
                additions=100, deletions=50, files_changed=1,
            ),
            Commit(
                repository="test/repo", sha="2", author_login="u", author_email="u@e.com",
                committer_login="u", date=datetime.now(timezone.utc),
                message="feat: large", full_message="feat: large",
                additions=400, deletions=200, files_changed=10,
            ),
        ]

        result = calculate_quality_metrics(sample_repo, commits, [])

        assert result.large_commits_count == 1
        assert result.large_commits_ratio_pct == 50.0

    def test_calculates_conventional_commit_ratio(self, sample_repo):
        """Test calculates conventional commit ratio correctly."""
        commits = [
            Commit(
                repository="test/repo", sha="1", author_login="u", author_email="u@e.com",
                committer_login="u", date=datetime.now(timezone.utc),
                message="feat: conventional", full_message="feat: conventional",
                additions=10, deletions=5, files_changed=1,
            ),
            Commit(
                repository="test/repo", sha="2", author_login="u", author_email="u@e.com",
                committer_login="u", date=datetime.now(timezone.utc),
                message="Not conventional", full_message="Not conventional",
                additions=5, deletions=5, files_changed=1,
            ),
        ]

        result = calculate_quality_metrics(sample_repo, commits, [])

        assert result.commit_message_quality_pct == 50.0

    def test_calculates_pr_review_coverage(self, sample_repo, sample_commit):
        """Test calculates PR review coverage correctly."""
        prs = [
            PullRequest(
                repository="test/repo", number=1, title="Reviewed PR",
                state="closed", author_login="u",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                closed_at=datetime.now(timezone.utc), merged_at=None,
                is_merged=False, is_draft=False,
                additions=10, deletions=5, changed_files=1,
                commits=1, comments=0, review_comments=2,
                reviewers_count=0,
            ),
            PullRequest(
                repository="test/repo", number=2, title="Not Reviewed PR",
                state="closed", author_login="u",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                closed_at=datetime.now(timezone.utc), merged_at=None,
                is_merged=False, is_draft=False,
                additions=10, deletions=5, changed_files=1,
                commits=1, comments=0, review_comments=0,
                reviewers_count=0,
            ),
        ]

        result = calculate_quality_metrics(sample_repo, [sample_commit], prs)

        assert result.pr_review_coverage_pct == 50.0

    def test_calculates_pr_approval_rate(self, sample_repo, sample_commit):
        """Test calculates PR approval rate correctly."""
        prs = [
            PullRequest(
                repository="test/repo", number=1, title="Approved PR",
                state="closed", author_login="u",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                closed_at=datetime.now(timezone.utc), merged_at=None,
                is_merged=False, is_draft=False,
                additions=10, deletions=5, changed_files=1,
                commits=1, comments=0, review_comments=0,
                approvals=1,
            ),
            PullRequest(
                repository="test/repo", number=2, title="Not Approved PR",
                state="closed", author_login="u",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                closed_at=datetime.now(timezone.utc), merged_at=None,
                is_merged=False, is_draft=False,
                additions=10, deletions=5, changed_files=1,
                commits=1, comments=0, review_comments=0,
                approvals=0,
            ),
        ]

        result = calculate_quality_metrics(sample_repo, [sample_commit], prs)

        assert result.pr_approval_rate_pct == 50.0

    def test_calculates_changes_requested_ratio(self, sample_repo, sample_commit):
        """Test calculates changes requested ratio correctly."""
        prs = [
            PullRequest(
                repository="test/repo", number=1, title="PR with changes",
                state="closed", author_login="u",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                closed_at=datetime.now(timezone.utc), merged_at=None,
                is_merged=False, is_draft=False,
                additions=10, deletions=5, changed_files=1,
                commits=1, comments=0, review_comments=0,
                changes_requested=1,
            ),
            PullRequest(
                repository="test/repo", number=2, title="PR without changes",
                state="closed", author_login="u",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                closed_at=datetime.now(timezone.utc), merged_at=None,
                is_merged=False, is_draft=False,
                additions=10, deletions=5, changed_files=1,
                commits=1, comments=0, review_comments=0,
                changes_requested=0,
            ),
        ]

        result = calculate_quality_metrics(sample_repo, [sample_commit], prs)

        assert result.pr_changes_requested_ratio_pct == 50.0

    def test_calculates_draft_pr_ratio(self, sample_repo, sample_commit):
        """Test calculates draft PR ratio correctly."""
        prs = [
            PullRequest(
                repository="test/repo", number=1, title="Draft PR",
                state="open", author_login="u",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                closed_at=None, merged_at=None,
                is_merged=False, is_draft=True,
                additions=10, deletions=5, changed_files=1,
                commits=1, comments=0, review_comments=0,
            ),
            PullRequest(
                repository="test/repo", number=2, title="Not Draft PR",
                state="open", author_login="u",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                closed_at=None, merged_at=None,
                is_merged=False, is_draft=False,
                additions=10, deletions=5, changed_files=1,
                commits=1, comments=0, review_comments=0,
            ),
        ]

        result = calculate_quality_metrics(sample_repo, [sample_commit], prs)

        assert result.draft_pr_ratio_pct == 50.0

    def test_calculates_quality_score(self, sample_repo, sample_commit, sample_pr):
        """Test calculates composite quality score."""
        result = calculate_quality_metrics(sample_repo, [sample_commit], [sample_pr])

        # Score should be between 0 and 100
        assert 0 <= result.quality_score <= 100

    def test_quality_score_formula(self, sample_repo):
        """Test quality score uses correct formula."""
        # Create controlled data to verify formula
        commits = [
            Commit(
                repository="test/repo", sha="1", author_login="u", author_email="u@e.com",
                committer_login="u", date=datetime.now(timezone.utc),
                message="feat: conventional", full_message="feat: conventional",
                additions=10, deletions=5, files_changed=1,
            ),
        ]
        prs = [
            PullRequest(
                repository="test/repo", number=1, title="Perfect PR",
                state="closed", author_login="u",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                closed_at=datetime.now(timezone.utc), merged_at=datetime.now(timezone.utc),
                is_merged=True, is_draft=False,
                additions=10, deletions=5, changed_files=1,
                commits=1, comments=1, review_comments=1,
                reviewers_count=1, approvals=1, changes_requested=0,
            ),
        ]

        result = calculate_quality_metrics(sample_repo, commits, prs)

        # With:
        # - revert_ratio = 0%
        # - review_coverage = 100%
        # - approval_rate = 100%
        # - changes_requested = 0%
        # - conventional_commits = 100%
        # Expected: (100-0)*0.20 + 100*0.25 + 100*0.20 + (100-0)*0.15 + 100*0.20
        #         = 20 + 25 + 20 + 15 + 20 = 100
        assert result.quality_score == 100.0
