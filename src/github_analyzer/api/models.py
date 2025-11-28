"""Data models for GitHub API responses.

This module defines dataclasses for all GitHub API entities used
by the analyzer: commits, pull requests, issues, and aggregate stats.

All models are designed to be immutable and provide computed properties
for derived values like time calculations and status flags.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


def _parse_datetime(value: str | datetime | None) -> datetime | None:
    """Parse datetime from ISO format string or return as-is.

    Args:
        value: ISO format datetime string or datetime object.

    Returns:
        Parsed datetime or None.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        # Handle GitHub's ISO format: 2025-01-15T10:30:00Z
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _safe_get(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely get nested value from dict.

    Args:
        data: Dictionary to search.
        *keys: Keys to traverse.
        default: Default value if not found.

    Returns:
        Value at nested path or default.
    """
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current if current is not None else default


@dataclass
class Commit:
    """Processed commit data from GitHub API.

    Attributes:
        repository: Repository full name (owner/repo).
        sha: Full commit SHA.
        author_login: GitHub login of author.
        author_email: Email of author.
        committer_login: GitHub login of committer.
        date: Commit date.
        message: First line of commit message.
        full_message: Complete commit message.
        additions: Lines added.
        deletions: Lines deleted.
        files_changed: Number of files changed.
        file_types: Count of files by extension.
        url: GitHub URL for commit.
    """

    repository: str
    sha: str
    author_login: str
    author_email: str
    committer_login: str
    date: datetime
    message: str
    full_message: str
    additions: int
    deletions: int
    files_changed: int
    file_types: dict[str, int] = field(default_factory=dict)
    url: str = ""

    @property
    def short_sha(self) -> str:
        """Return first 7 characters of SHA."""
        return self.sha[:7]

    @property
    def total_changes(self) -> int:
        """Return total lines changed (additions + deletions)."""
        return self.additions + self.deletions

    @property
    def is_merge_commit(self) -> bool:
        """Check if this is a merge commit."""
        return self.message.lower().startswith("merge")

    @property
    def is_revert(self) -> bool:
        """Check if this is a revert commit."""
        return self.message.lower().startswith("revert")

    @classmethod
    def from_api_response(cls, data: dict[str, Any], repository: str) -> Commit:
        """Create Commit from GitHub API response.

        Args:
            data: Raw API response for a commit.
            repository: Repository full name.

        Returns:
            Processed Commit instance.
        """
        commit_data = data.get("commit", {})
        author_data = commit_data.get("author", {})
        stats = data.get("stats", {})
        files = data.get("files", [])

        # Count file types
        file_types: dict[str, int] = {}
        for f in files:
            filename = f.get("filename", "")
            ext = filename.rsplit(".", 1)[-1] if "." in filename else "no_extension"
            file_types[ext] = file_types.get(ext, 0) + 1

        message = commit_data.get("message", "")
        first_line = message.split("\n")[0] if message else ""

        return cls(
            repository=repository,
            sha=data.get("sha", ""),
            author_login=_safe_get(data, "author", "login", default="unknown"),
            author_email=author_data.get("email", ""),
            committer_login=_safe_get(data, "committer", "login", default="unknown"),
            date=_parse_datetime(author_data.get("date")) or datetime.now(),
            message=first_line,
            full_message=message,
            additions=stats.get("additions", 0),
            deletions=stats.get("deletions", 0),
            files_changed=len(files),
            file_types=file_types,
            url=data.get("html_url", ""),
        )


@dataclass
class PullRequest:
    """Processed pull request data from GitHub API.

    Attributes:
        repository: Repository full name.
        number: PR number.
        title: PR title.
        state: PR state (open/closed).
        author_login: Author's GitHub login.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
        closed_at: Close timestamp (if closed).
        merged_at: Merge timestamp (if merged).
        is_merged: Whether PR was merged.
        is_draft: Whether PR is a draft.
        additions: Lines added.
        deletions: Lines deleted.
        changed_files: Number of files changed.
        commits: Number of commits.
        comments: Number of comments.
        review_comments: Number of review comments.
        labels: List of label names.
        reviewers_count: Number of requested reviewers.
        approvals: Number of approvals (from reviews).
        changes_requested: Number of change requests.
        base_branch: Target branch.
        head_branch: Source branch.
        url: GitHub URL for PR.
    """

    repository: str
    number: int
    title: str
    state: str
    author_login: str
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    merged_at: datetime | None
    is_merged: bool
    is_draft: bool
    additions: int
    deletions: int
    changed_files: int
    commits: int
    comments: int
    review_comments: int
    labels: list[str] = field(default_factory=list)
    reviewers_count: int = 0
    approvals: int = 0
    changes_requested: int = 0
    base_branch: str = ""
    head_branch: str = ""
    url: str = ""

    @property
    def time_to_merge_hours(self) -> float | None:
        """Calculate hours from creation to merge."""
        if self.merged_at is None:
            return None
        delta = self.merged_at - self.created_at
        return delta.total_seconds() / 3600

    @classmethod
    def from_api_response(cls, data: dict[str, Any], repository: str) -> PullRequest:
        """Create PullRequest from GitHub API response.

        Args:
            data: Raw API response for a PR.
            repository: Repository full name.

        Returns:
            Processed PullRequest instance.
        """
        labels = [label.get("name", "") for label in data.get("labels", [])]
        reviewers = data.get("requested_reviewers", [])

        return cls(
            repository=repository,
            number=data.get("number", 0),
            title=data.get("title", ""),
            state=data.get("state", "open"),
            author_login=_safe_get(data, "user", "login", default="unknown"),
            created_at=_parse_datetime(data.get("created_at")) or datetime.now(),
            updated_at=_parse_datetime(data.get("updated_at")) or datetime.now(),
            closed_at=_parse_datetime(data.get("closed_at")),
            merged_at=_parse_datetime(data.get("merged_at")),
            is_merged=data.get("merged_at") is not None,
            is_draft=data.get("draft", False),
            additions=data.get("additions", 0),
            deletions=data.get("deletions", 0),
            changed_files=data.get("changed_files", 0),
            commits=data.get("commits", 0),
            comments=data.get("comments", 0),
            review_comments=data.get("review_comments", 0),
            labels=labels,
            reviewers_count=len(reviewers),
            base_branch=_safe_get(data, "base", "ref", default=""),
            head_branch=_safe_get(data, "head", "ref", default=""),
            url=data.get("html_url", ""),
        )


@dataclass
class Issue:
    """Processed issue data from GitHub API.

    Attributes:
        repository: Repository full name.
        number: Issue number.
        title: Issue title.
        state: Issue state (open/closed).
        author_login: Author's GitHub login.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
        closed_at: Close timestamp (if closed).
        comments: Number of comments.
        labels: List of label names.
        assignees: List of assignee logins.
        url: GitHub URL for issue.
    """

    repository: str
    number: int
    title: str
    state: str
    author_login: str
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    comments: int
    labels: list[str] = field(default_factory=list)
    assignees: list[str] = field(default_factory=list)
    url: str = ""

    @property
    def time_to_close_hours(self) -> float | None:
        """Calculate hours from creation to close."""
        if self.closed_at is None:
            return None
        delta = self.closed_at - self.created_at
        return delta.total_seconds() / 3600

    @property
    def is_bug(self) -> bool:
        """Check if any label contains 'bug'."""
        return any("bug" in label.lower() for label in self.labels)

    @property
    def is_enhancement(self) -> bool:
        """Check if any label contains 'enhancement' or 'feature'."""
        return any(
            "enhancement" in label.lower() or "feature" in label.lower()
            for label in self.labels
        )

    @classmethod
    def from_api_response(cls, data: dict[str, Any], repository: str) -> Issue:
        """Create Issue from GitHub API response.

        Args:
            data: Raw API response for an issue.
            repository: Repository full name.

        Returns:
            Processed Issue instance.
        """
        labels = [label.get("name", "") for label in data.get("labels", [])]
        assignees = [
            assignee.get("login", "") for assignee in data.get("assignees", [])
        ]

        return cls(
            repository=repository,
            number=data.get("number", 0),
            title=data.get("title", ""),
            state=data.get("state", "open"),
            author_login=_safe_get(data, "user", "login", default="unknown"),
            created_at=_parse_datetime(data.get("created_at")) or datetime.now(),
            updated_at=_parse_datetime(data.get("updated_at")) or datetime.now(),
            closed_at=_parse_datetime(data.get("closed_at")),
            comments=data.get("comments", 0),
            labels=labels,
            assignees=assignees,
            url=data.get("html_url", ""),
        )


@dataclass
class RepositoryStats:
    """Aggregate statistics for a repository.

    Attributes:
        repository: Repository full name.
        total_commits: Total number of commits.
        merge_commits: Number of merge commits.
        revert_commits: Number of revert commits.
        total_additions: Total lines added.
        total_deletions: Total lines deleted.
        unique_authors: Number of unique commit authors.
        total_prs: Total number of PRs.
        merged_prs: Number of merged PRs.
        open_prs: Number of open PRs.
        avg_time_to_merge_hours: Average time to merge PRs.
        total_issues: Total number of issues.
        closed_issues: Number of closed issues.
        open_issues: Number of open issues.
        bug_issues: Number of bug issues.
        analysis_period_days: Days analyzed.
    """

    repository: str
    total_commits: int = 0
    merge_commits: int = 0
    revert_commits: int = 0
    total_additions: int = 0
    total_deletions: int = 0
    unique_authors: int = 0
    total_prs: int = 0
    merged_prs: int = 0
    open_prs: int = 0
    avg_time_to_merge_hours: float | None = None
    total_issues: int = 0
    closed_issues: int = 0
    open_issues: int = 0
    bug_issues: int = 0
    analysis_period_days: int = 30

    @property
    def regular_commits(self) -> int:
        """Return non-merge, non-revert commits."""
        return self.total_commits - self.merge_commits - self.revert_commits

    @property
    def net_lines(self) -> int:
        """Return net line change (additions - deletions)."""
        return self.total_additions - self.total_deletions

    @property
    def pr_merge_rate(self) -> float:
        """Return PR merge rate as percentage."""
        if self.total_prs == 0:
            return 0.0
        return (self.merged_prs / self.total_prs) * 100

    @property
    def issue_close_rate(self) -> float:
        """Return issue close rate as percentage."""
        if self.total_issues == 0:
            return 0.0
        return (self.closed_issues / self.total_issues) * 100


@dataclass
class QualityMetrics:
    """Code quality metrics for a repository.

    Attributes:
        repository: Repository full name.
        revert_ratio_pct: Percentage of commits that are reverts.
        avg_commit_size_lines: Average lines changed per commit.
        large_commits_count: Number of large commits (>500 lines).
        large_commits_ratio_pct: Percentage of large commits.
        pr_review_coverage_pct: Percentage of PRs with reviews.
        pr_approval_rate_pct: Percentage of PRs with approvals.
        pr_changes_requested_ratio_pct: Percentage of PRs with changes requested.
        draft_pr_ratio_pct: Percentage of draft PRs.
        commit_message_quality_pct: Percentage of conventional commits.
        quality_score: Weighted composite score (0-100).
    """

    repository: str
    revert_ratio_pct: float = 0.0
    avg_commit_size_lines: float = 0.0
    large_commits_count: int = 0
    large_commits_ratio_pct: float = 0.0
    pr_review_coverage_pct: float = 0.0
    pr_approval_rate_pct: float = 0.0
    pr_changes_requested_ratio_pct: float = 0.0
    draft_pr_ratio_pct: float = 0.0
    commit_message_quality_pct: float = 0.0
    quality_score: float = 0.0


@dataclass
class ContributorStats:
    """Statistics for a single contributor.

    Used to track contributor activity across multiple repositories.
    """

    login: str
    repositories: set[str] = field(default_factory=set)
    commits: int = 0
    additions: int = 0
    deletions: int = 0
    prs_opened: int = 0
    prs_merged: int = 0
    prs_reviewed: int = 0
    issues_opened: int = 0
    issues_closed: int = 0
    first_activity: datetime | None = None
    last_activity: datetime | None = None
    commit_days: set[str] = field(default_factory=set)
    commit_sizes: list[int] = field(default_factory=list)


@dataclass
class ProductivityAnalysis:
    """Productivity analysis for a contributor.

    Generated from ContributorStats with calculated metrics.
    """

    contributor: str
    repositories: str  # Comma-separated
    repositories_count: int
    total_commits: int
    total_additions: int
    total_deletions: int
    net_lines: int
    avg_commit_size: float
    prs_opened: int
    prs_merged: int
    pr_merge_rate_pct: float
    prs_reviewed: int
    issues_opened: int
    issues_closed: int
    active_days: int
    commits_per_active_day: float
    first_activity: str  # ISO datetime
    last_activity: str  # ISO datetime
    activity_span_days: int
    consistency_pct: float
    productivity_score: float
