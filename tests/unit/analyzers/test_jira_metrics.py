"""Unit tests for Jira quality metrics calculation.

Tests cover: FR-001 to FR-009 (issue-level metrics),
FR-010 to FR-023 (aggregation metrics).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.github_analyzer.analyzers.jira_metrics import (
    IssueMetrics,
    MetricsCalculator,
    PersonMetrics,
    ProjectMetrics,
    TypeMetrics,
    calculate_aging,
    calculate_comment_metrics,
    calculate_cross_team_score,
    calculate_cycle_time,
    calculate_description_quality,
    calculate_same_day_resolution,
    detect_acceptance_criteria,
    detect_reopens,
)
from src.github_analyzer.api.jira_client import JiraComment, JiraIssue


# =============================================================================
# Helper Functions for Creating Test Objects
# =============================================================================


def make_issue(
    key: str = "PROJ-1",
    created: datetime | None = None,
    resolution_date: datetime | None = None,
    description: str = "",
    issue_type: str = "Story",
    assignee: str | None = "John Doe",
    status: str = "Open",
) -> JiraIssue:
    """Create a test JiraIssue with minimal required fields."""
    if created is None:
        created = datetime(2025, 11, 1, 10, 0, 0, tzinfo=timezone.utc)
    return JiraIssue(
        key=key,
        summary=f"Test issue {key}",
        description=description,
        status=status,
        issue_type=issue_type,
        priority="Medium",
        assignee=assignee,
        reporter="Jane Smith",
        created=created,
        updated=created,
        resolution_date=resolution_date,
        project_key="PROJ",
    )


def make_comment(
    comment_id: str = "1",
    issue_key: str = "PROJ-1",
    author: str = "John Doe",
    created: datetime | None = None,
) -> JiraComment:
    """Create a test JiraComment."""
    if created is None:
        created = datetime(2025, 11, 2, 10, 0, 0, tzinfo=timezone.utc)
    return JiraComment(
        id=comment_id,
        issue_key=issue_key,
        author=author,
        created=created,
        body="Test comment",
    )


# =============================================================================
# T007: Tests for cycle_time calculation (FR-001)
# =============================================================================


class TestCycleTime:
    """Tests for calculate_cycle_time function."""

    def test_resolved_issue_cycle_time(self) -> None:
        """Given a resolved issue, calculate days between created and resolved."""
        created = datetime(2025, 11, 1, 10, 0, 0, tzinfo=timezone.utc)
        resolved = datetime(2025, 11, 15, 10, 0, 0, tzinfo=timezone.utc)

        result = calculate_cycle_time(created, resolved)

        assert result == 14.0

    def test_open_issue_returns_none(self) -> None:
        """Given an open issue, cycle_time should be None."""
        created = datetime(2025, 11, 1, 10, 0, 0, tzinfo=timezone.utc)

        result = calculate_cycle_time(created, None)

        assert result is None

    def test_same_day_resolution(self) -> None:
        """Given same-day resolution, cycle_time should be fractional days."""
        created = datetime(2025, 11, 25, 9, 0, 0, tzinfo=timezone.utc)
        resolved = datetime(2025, 11, 25, 14, 0, 0, tzinfo=timezone.utc)

        result = calculate_cycle_time(created, resolved)

        # 5 hours = 5/24 ≈ 0.21 days
        assert result is not None
        assert 0.2 <= result <= 0.22

    def test_negative_cycle_time_returns_none(self) -> None:
        """Given resolution before creation (data error), return None with warning."""
        created = datetime(2025, 11, 15, 10, 0, 0, tzinfo=timezone.utc)
        resolved = datetime(2025, 11, 1, 10, 0, 0, tzinfo=timezone.utc)  # Before created

        result = calculate_cycle_time(created, resolved)

        assert result is None

    def test_precision_two_decimal_places(self) -> None:
        """Cycle time should have 2 decimal precision."""
        created = datetime(2025, 11, 1, 0, 0, 0, tzinfo=timezone.utc)
        resolved = datetime(2025, 11, 4, 8, 0, 0, tzinfo=timezone.utc)

        result = calculate_cycle_time(created, resolved)

        # 3 days + 8 hours = 3.33... days
        assert result is not None
        assert result == 3.33


# =============================================================================
# T008: Tests for aging calculation (FR-002)
# =============================================================================


class TestAging:
    """Tests for calculate_aging function."""

    def test_open_issue_aging(self) -> None:
        """Given an open issue, calculate days since creation."""
        created = datetime(2025, 11, 1, 10, 0, 0, tzinfo=timezone.utc)
        now = datetime(2025, 11, 28, 10, 0, 0, tzinfo=timezone.utc)

        result = calculate_aging(created, None, now)

        assert result == 27.0

    def test_resolved_issue_returns_none(self) -> None:
        """Given a resolved issue, aging should be None."""
        created = datetime(2025, 11, 1, 10, 0, 0, tzinfo=timezone.utc)
        resolved = datetime(2025, 11, 15, 10, 0, 0, tzinfo=timezone.utc)

        result = calculate_aging(created, resolved)

        assert result is None

    def test_negative_aging_returns_none(self) -> None:
        """Given future creation date (data error), return None with warning."""
        created = datetime(2025, 12, 15, 10, 0, 0, tzinfo=timezone.utc)  # Future
        now = datetime(2025, 11, 28, 10, 0, 0, tzinfo=timezone.utc)

        result = calculate_aging(created, None, now)

        assert result is None


# =============================================================================
# T009: Tests for description_quality_score (FR-004)
# =============================================================================


class TestDescriptionQuality:
    """Tests for calculate_description_quality function."""

    def test_empty_description_score_zero(self) -> None:
        """Given empty description, score should be 0."""
        result = calculate_description_quality("", False)
        assert result == 0

    def test_short_description_partial_score(self) -> None:
        """Given short description (< threshold), partial length score."""
        # 50 chars = 50/100 * 40 = 20 points
        description = "A" * 50
        result = calculate_description_quality(description, False)
        assert result == 20

    def test_long_description_full_length_score(self) -> None:
        """Given long description (>= threshold), full length score."""
        description = "A" * 150  # > 100 chars
        result = calculate_description_quality(description, False)
        assert result == 40  # Full length points

    def test_with_acceptance_criteria_adds_40_points(self) -> None:
        """Given AC present, add 40 points."""
        description = "A" * 100
        result = calculate_description_quality(description, True)
        assert result == 80  # 40 length + 40 AC

    def test_with_formatting_adds_points(self) -> None:
        """Given headers and lists, add formatting points."""
        description = "## Header\n- List item\n" + "A" * 80
        result = calculate_description_quality(description, False)
        # 40 length + 10 headers + 10 lists = 60
        assert result >= 50  # At least headers or lists detected

    def test_full_quality_score(self) -> None:
        """Given long description, AC, and formatting, max score ~100."""
        description = "## Description\n- Item 1\n- Item 2\n" + "A" * 100
        result = calculate_description_quality(description, True)
        assert result == 100  # 40 + 40 + 20


# =============================================================================
# T010: Tests for acceptance_criteria detection (FR-005)
# =============================================================================


class TestAcceptanceCriteria:
    """Tests for detect_acceptance_criteria function."""

    def test_given_when_then_detected(self) -> None:
        """Given BDD-style AC, should be detected."""
        description = "Given a user\nWhen they login\nThen they see dashboard"
        assert detect_acceptance_criteria(description) is True

    def test_ac_header_detected(self) -> None:
        """Given 'AC:' prefix, should be detected."""
        description = "AC: User can login"
        assert detect_acceptance_criteria(description) is True

    def test_acceptance_criteria_header_detected(self) -> None:
        """Given 'Acceptance Criteria:' label, should be detected."""
        description = "Acceptance Criteria: The system shall..."
        assert detect_acceptance_criteria(description) is True

    def test_checkbox_list_detected(self) -> None:
        """Given markdown checkbox list, should be detected."""
        description = "Tasks:\n- [ ] First task\n- [x] Second task"
        assert detect_acceptance_criteria(description) is True

    def test_markdown_heading_ac_detected(self) -> None:
        """Given markdown heading with AC, should be detected."""
        description = "## Acceptance Criteria\n- First criterion"
        assert detect_acceptance_criteria(description) is True

    def test_no_ac_returns_false(self) -> None:
        """Given description without AC patterns, should return False."""
        description = "This is just a regular description."
        assert detect_acceptance_criteria(description) is False

    def test_empty_description_returns_false(self) -> None:
        """Given empty description, should return False."""
        assert detect_acceptance_criteria("") is False


# =============================================================================
# T011: Tests for comments_count and silent_issue (FR-003, FR-007)
# =============================================================================


class TestCommentMetrics:
    """Tests for calculate_comment_metrics function."""

    def test_no_comments_silent_issue(self) -> None:
        """Given no comments, issue is silent."""
        issue_created = datetime(2025, 11, 1, 10, 0, 0, tzinfo=timezone.utc)

        count, velocity, silent = calculate_comment_metrics([], issue_created)

        assert count == 0
        assert velocity is None
        assert silent is True

    def test_with_comments_not_silent(self) -> None:
        """Given comments, issue is not silent."""
        issue_created = datetime(2025, 11, 1, 10, 0, 0, tzinfo=timezone.utc)
        comments = [make_comment(created=datetime(2025, 11, 2, 10, 0, 0, tzinfo=timezone.utc))]

        count, velocity, silent = calculate_comment_metrics(comments, issue_created)

        assert count == 1
        assert velocity is not None
        assert silent is False

    def test_multiple_comments_count(self) -> None:
        """Given multiple comments, count is correct."""
        issue_created = datetime(2025, 11, 1, 10, 0, 0, tzinfo=timezone.utc)
        comments = [
            make_comment("1", created=datetime(2025, 11, 2, 10, 0, 0, tzinfo=timezone.utc)),
            make_comment("2", created=datetime(2025, 11, 3, 10, 0, 0, tzinfo=timezone.utc)),
            make_comment("3", created=datetime(2025, 11, 4, 10, 0, 0, tzinfo=timezone.utc)),
        ]

        count, _, _ = calculate_comment_metrics(comments, issue_created)

        assert count == 3


# =============================================================================
# T012: Tests for same_day_resolution (FR-008)
# =============================================================================


class TestSameDayResolution:
    """Tests for calculate_same_day_resolution function."""

    def test_same_day_returns_true(self) -> None:
        """Given same calendar day resolution, return True."""
        created = datetime(2025, 11, 25, 9, 0, 0, tzinfo=timezone.utc)
        resolved = datetime(2025, 11, 25, 17, 0, 0, tzinfo=timezone.utc)

        result = calculate_same_day_resolution(created, resolved)

        assert result is True

    def test_different_day_returns_false(self) -> None:
        """Given different day resolution, return False."""
        created = datetime(2025, 11, 25, 9, 0, 0, tzinfo=timezone.utc)
        resolved = datetime(2025, 11, 26, 9, 0, 0, tzinfo=timezone.utc)

        result = calculate_same_day_resolution(created, resolved)

        assert result is False

    def test_unresolved_returns_false(self) -> None:
        """Given unresolved issue, return False."""
        created = datetime(2025, 11, 25, 9, 0, 0, tzinfo=timezone.utc)

        result = calculate_same_day_resolution(created, None)

        assert result is False


# =============================================================================
# T013: Tests for cross_team_score (FR-009)
# =============================================================================


class TestCrossTeamScore:
    """Tests for calculate_cross_team_score function."""

    def test_no_comments_score_zero(self) -> None:
        """Given no comments, score is 0."""
        result = calculate_cross_team_score([])
        assert result == 0

    def test_one_author_score_25(self) -> None:
        """Given 1 unique author, score is 25."""
        comments = [
            make_comment("1", author="John"),
            make_comment("2", author="John"),
        ]
        result = calculate_cross_team_score(comments)
        assert result == 25

    def test_two_authors_score_50(self) -> None:
        """Given 2 unique authors, score is 50."""
        comments = [
            make_comment("1", author="John"),
            make_comment("2", author="Jane"),
        ]
        result = calculate_cross_team_score(comments)
        assert result == 50

    def test_three_authors_score_75(self) -> None:
        """Given 3 unique authors, score is 75."""
        comments = [
            make_comment("1", author="John"),
            make_comment("2", author="Jane"),
            make_comment("3", author="Bob"),
        ]
        result = calculate_cross_team_score(comments)
        assert result == 75

    def test_four_authors_score_90(self) -> None:
        """Given 4 unique authors, score is 90."""
        comments = [
            make_comment("1", author="John"),
            make_comment("2", author="Jane"),
            make_comment("3", author="Bob"),
            make_comment("4", author="Alice"),
        ]
        result = calculate_cross_team_score(comments)
        assert result == 90

    def test_five_plus_authors_score_100(self) -> None:
        """Given 5+ unique authors, score is 100."""
        comments = [
            make_comment("1", author="John"),
            make_comment("2", author="Jane"),
            make_comment("3", author="Bob"),
            make_comment("4", author="Alice"),
            make_comment("5", author="Charlie"),
        ]
        result = calculate_cross_team_score(comments)
        assert result == 100


# =============================================================================
# T014: Tests for comment_velocity_hours (FR-006)
# =============================================================================


class TestCommentVelocity:
    """Tests for comment velocity calculation in calculate_comment_metrics."""

    def test_velocity_hours_calculation(self) -> None:
        """Given comments, velocity is hours from creation to first comment."""
        issue_created = datetime(2025, 11, 1, 10, 0, 0, tzinfo=timezone.utc)
        first_comment = datetime(2025, 11, 2, 10, 0, 0, tzinfo=timezone.utc)  # 24 hours later
        comments = [make_comment(created=first_comment)]

        _, velocity, _ = calculate_comment_metrics(comments, issue_created)

        assert velocity == 24.0

    def test_velocity_uses_earliest_comment(self) -> None:
        """Given multiple comments, velocity uses the earliest one."""
        issue_created = datetime(2025, 11, 1, 10, 0, 0, tzinfo=timezone.utc)
        comments = [
            make_comment("2", created=datetime(2025, 11, 3, 10, 0, 0, tzinfo=timezone.utc)),  # 48 hours
            make_comment("1", created=datetime(2025, 11, 2, 10, 0, 0, tzinfo=timezone.utc)),  # 24 hours (first)
        ]

        _, velocity, _ = calculate_comment_metrics(comments, issue_created)

        assert velocity == 24.0  # Uses first comment, not second

    def test_no_comments_velocity_none(self) -> None:
        """Given no comments, velocity is None."""
        issue_created = datetime(2025, 11, 1, 10, 0, 0, tzinfo=timezone.utc)

        _, velocity, _ = calculate_comment_metrics([], issue_created)

        assert velocity is None


# =============================================================================
# T039: Tests for reopen detection (FR-022)
# =============================================================================


class TestReopenDetection:
    """Tests for detect_reopens function."""

    def test_reopen_detected(self) -> None:
        """Given Done→In Progress transition, count as reopen."""
        changelog = [
            {
                "items": [
                    {"field": "status", "fromString": "Done", "toString": "In Progress"}
                ]
            }
        ]

        result = detect_reopens(changelog)

        assert result == 1

    def test_multiple_reopens(self) -> None:
        """Given multiple Done→non-Done transitions, count all."""
        changelog = [
            {"items": [{"field": "status", "fromString": "Done", "toString": "Open"}]},
            {"items": [{"field": "status", "fromString": "Closed", "toString": "In Progress"}]},
        ]

        result = detect_reopens(changelog)

        assert result == 2

    def test_no_reopen(self) -> None:
        """Given no Done→non-Done transitions, count is 0."""
        changelog = [
            {"items": [{"field": "status", "fromString": "Open", "toString": "In Progress"}]},
            {"items": [{"field": "status", "fromString": "In Progress", "toString": "Done"}]},
        ]

        result = detect_reopens(changelog)

        assert result == 0

    def test_empty_changelog(self) -> None:
        """Given empty changelog, count is 0."""
        result = detect_reopens([])
        assert result == 0

    def test_non_status_changes_ignored(self) -> None:
        """Given non-status field changes, ignore them."""
        changelog = [
            {"items": [{"field": "assignee", "fromString": "John", "toString": "Jane"}]},
            {"items": [{"field": "priority", "fromString": "High", "toString": "Low"}]},
        ]

        result = detect_reopens(changelog)

        assert result == 0


# =============================================================================
# T026: Tests for project aggregation (FR-010 to FR-014)
# =============================================================================


class TestProjectAggregation:
    """Tests for MetricsCalculator.aggregate_project_metrics."""

    def test_avg_cycle_time(self) -> None:
        """Given resolved issues, calculate average cycle time."""
        calculator = MetricsCalculator()

        issue1 = make_issue("PROJ-1", resolution_date=datetime(2025, 11, 11, 10, 0, 0, tzinfo=timezone.utc))
        issue2 = make_issue("PROJ-2", resolution_date=datetime(2025, 11, 21, 10, 0, 0, tzinfo=timezone.utc))

        metrics = [
            IssueMetrics(
                issue=issue1, cycle_time_days=10.0, aging_days=None,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=0,
            ),
            IssueMetrics(
                issue=issue2, cycle_time_days=20.0, aging_days=None,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=0,
            ),
        ]

        result = calculator.aggregate_project_metrics(metrics, "PROJ")

        assert result.avg_cycle_time_days == 15.0

    def test_median_cycle_time(self) -> None:
        """Given resolved issues, calculate median cycle time."""
        calculator = MetricsCalculator()

        metrics = []
        for i, days in enumerate([5.0, 10.0, 15.0, 20.0, 100.0]):
            issue = make_issue(f"PROJ-{i}", resolution_date=datetime(2025, 11, 15, 10, 0, 0, tzinfo=timezone.utc))
            metrics.append(IssueMetrics(
                issue=issue, cycle_time_days=days, aging_days=None,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=0,
            ))

        result = calculator.aggregate_project_metrics(metrics, "PROJ")

        assert result.median_cycle_time_days == 15.0  # Middle value

    def test_bug_ratio(self) -> None:
        """Given mix of issue types, calculate bug ratio."""
        calculator = MetricsCalculator()

        metrics = [
            IssueMetrics(
                issue=make_issue("PROJ-1", issue_type="Bug"), cycle_time_days=5.0, aging_days=None,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=0,
            ),
            IssueMetrics(
                issue=make_issue("PROJ-2", issue_type="Bug"), cycle_time_days=5.0, aging_days=None,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=0,
            ),
            IssueMetrics(
                issue=make_issue("PROJ-3", issue_type="Story"), cycle_time_days=5.0, aging_days=None,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=0,
            ),
            IssueMetrics(
                issue=make_issue("PROJ-4", issue_type="Task"), cycle_time_days=5.0, aging_days=None,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=0,
            ),
        ]

        result = calculator.aggregate_project_metrics(metrics, "PROJ")

        assert result.bug_count == 2
        assert result.bug_ratio_percent == 50.0  # 2/4 * 100

    def test_silent_issues_ratio(self) -> None:
        """Given mix of silent/non-silent, calculate silent ratio."""
        calculator = MetricsCalculator()

        metrics = [
            IssueMetrics(
                issue=make_issue("PROJ-1"), cycle_time_days=5.0, aging_days=None,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=0,
            ),
            IssueMetrics(
                issue=make_issue("PROJ-2"), cycle_time_days=5.0, aging_days=None,
                comments_count=5, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=10.0,
                silent_issue=False, same_day_resolution=False, cross_team_score=50, reopen_count=0,
            ),
        ]

        result = calculator.aggregate_project_metrics(metrics, "PROJ")

        assert result.silent_issues_ratio_percent == 50.0

    def test_empty_project(self) -> None:
        """Given no issues, return default values."""
        calculator = MetricsCalculator()

        result = calculator.aggregate_project_metrics([], "EMPTY")

        assert result.total_issues == 0
        assert result.avg_cycle_time_days is None
        assert result.bug_ratio_percent == 0.0


# =============================================================================
# T031: Tests for person aggregation (FR-015 to FR-018)
# =============================================================================


class TestPersonAggregation:
    """Tests for MetricsCalculator.aggregate_person_metrics."""

    def test_wip_count(self) -> None:
        """Given open issues, calculate WIP for assignee."""
        calculator = MetricsCalculator()

        metrics = [
            IssueMetrics(
                issue=make_issue("PROJ-1", assignee="John Doe"), cycle_time_days=None, aging_days=10.0,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=0,
            ),
            IssueMetrics(
                issue=make_issue("PROJ-2", assignee="John Doe"), cycle_time_days=None, aging_days=5.0,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=0,
            ),
            IssueMetrics(
                issue=make_issue("PROJ-3", assignee="John Doe", resolution_date=datetime(2025, 11, 15, 10, 0, 0, tzinfo=timezone.utc)),
                cycle_time_days=14.0, aging_days=None,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=0,
            ),
        ]

        result = calculator.aggregate_person_metrics(metrics)

        assert len(result) == 1
        person = result[0]
        assert person.assignee_name == "John Doe"
        assert person.wip_count == 2
        assert person.resolved_count == 1
        assert person.total_assigned == 3

    def test_unassigned_excluded(self) -> None:
        """Given unassigned issues, they should be excluded."""
        calculator = MetricsCalculator()

        metrics = [
            IssueMetrics(
                issue=make_issue("PROJ-1", assignee=None), cycle_time_days=None, aging_days=10.0,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=0,
            ),
            IssueMetrics(
                issue=make_issue("PROJ-2", assignee="John Doe"), cycle_time_days=5.0, aging_days=None,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=0,
            ),
        ]

        result = calculator.aggregate_person_metrics(metrics)

        assert len(result) == 1
        assert result[0].assignee_name == "John Doe"

    def test_multiple_assignees(self) -> None:
        """Given multiple assignees, return metrics for each."""
        calculator = MetricsCalculator()

        metrics = [
            IssueMetrics(
                issue=make_issue("PROJ-1", assignee="John"), cycle_time_days=5.0, aging_days=None,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=0,
            ),
            IssueMetrics(
                issue=make_issue("PROJ-2", assignee="Jane"), cycle_time_days=10.0, aging_days=None,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=0,
            ),
        ]

        result = calculator.aggregate_person_metrics(metrics)

        assert len(result) == 2
        names = {p.assignee_name for p in result}
        assert names == {"John", "Jane"}


# =============================================================================
# T035: Tests for type aggregation (FR-019 to FR-021)
# =============================================================================


class TestTypeAggregation:
    """Tests for MetricsCalculator.aggregate_type_metrics."""

    def test_per_type_counts(self) -> None:
        """Given mix of types, count each type."""
        calculator = MetricsCalculator()

        metrics = [
            IssueMetrics(
                issue=make_issue("PROJ-1", issue_type="Bug"), cycle_time_days=5.0, aging_days=None,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=0,
            ),
            IssueMetrics(
                issue=make_issue("PROJ-2", issue_type="Bug"), cycle_time_days=10.0, aging_days=None,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=0,
            ),
            IssueMetrics(
                issue=make_issue("PROJ-3", issue_type="Story"), cycle_time_days=15.0, aging_days=None,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=0,
            ),
        ]

        result = calculator.aggregate_type_metrics(metrics)

        bug_metrics = next(t for t in result if t.issue_type == "Bug")
        story_metrics = next(t for t in result if t.issue_type == "Story")

        assert bug_metrics.count == 2
        assert story_metrics.count == 1

    def test_bug_resolution_time_only_for_bugs(self) -> None:
        """bug_resolution_time_avg is only set for Bug type."""
        calculator = MetricsCalculator()

        metrics = [
            IssueMetrics(
                issue=make_issue("PROJ-1", issue_type="Bug"), cycle_time_days=5.0, aging_days=None,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=0,
            ),
            IssueMetrics(
                issue=make_issue("PROJ-2", issue_type="Story"), cycle_time_days=10.0, aging_days=None,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=0,
            ),
        ]

        result = calculator.aggregate_type_metrics(metrics)

        bug_metrics = next(t for t in result if t.issue_type == "Bug")
        story_metrics = next(t for t in result if t.issue_type == "Story")

        assert bug_metrics.bug_resolution_time_avg == 5.0
        assert story_metrics.bug_resolution_time_avg is None

    def test_avg_cycle_time_per_type(self) -> None:
        """Given resolved issues of same type, calculate avg cycle time."""
        calculator = MetricsCalculator()

        metrics = [
            IssueMetrics(
                issue=make_issue("PROJ-1", issue_type="Bug"), cycle_time_days=4.0, aging_days=None,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=0,
            ),
            IssueMetrics(
                issue=make_issue("PROJ-2", issue_type="Bug"), cycle_time_days=6.0, aging_days=None,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=0,
            ),
        ]

        result = calculator.aggregate_type_metrics(metrics)

        bug_metrics = next(t for t in result if t.issue_type == "Bug")
        assert bug_metrics.avg_cycle_time_days == 5.0


# =============================================================================
# T041: Tests for reopen_rate_percent in project aggregation (FR-023)
# =============================================================================


class TestReopenRateAggregation:
    """Tests for reopen_rate_percent in project metrics."""

    def test_reopen_rate_calculation(self) -> None:
        """Given reopened issues, calculate rate correctly."""
        calculator = MetricsCalculator()

        metrics = [
            IssueMetrics(
                issue=make_issue("PROJ-1"), cycle_time_days=5.0, aging_days=None,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=1,
            ),
            IssueMetrics(
                issue=make_issue("PROJ-2"), cycle_time_days=5.0, aging_days=None,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=0,
            ),
            IssueMetrics(
                issue=make_issue("PROJ-3"), cycle_time_days=5.0, aging_days=None,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=2,  # 2 reopens
            ),
            IssueMetrics(
                issue=make_issue("PROJ-4"), cycle_time_days=5.0, aging_days=None,
                comments_count=0, description_quality_score=50,
                acceptance_criteria_present=False, comment_velocity_hours=None,
                silent_issue=True, same_day_resolution=False, cross_team_score=0, reopen_count=0,
            ),
        ]

        result = calculator.aggregate_project_metrics(metrics, "PROJ")

        # 2 out of 4 resolved issues were reopened = 50%
        assert result.reopen_rate_percent == 50.0
