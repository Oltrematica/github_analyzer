"""Jira quality metrics calculation module.

This module provides dataclasses and functions for calculating
quality metrics on Jira issues, including cycle time, description
quality, collaboration scores, and aggregated metrics.

Implements: FR-001 to FR-023 per spec.md
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean, median
from typing import TYPE_CHECKING

from src.github_analyzer.config.settings import (
    AC_PATTERNS,
    CROSS_TEAM_SCALE,
    DONE_STATUSES,
    QUALITY_LENGTH_THRESHOLD,
    QUALITY_WEIGHT_AC,
    QUALITY_WEIGHT_FORMAT,
    QUALITY_WEIGHT_LENGTH,
)

if TYPE_CHECKING:
    from src.github_analyzer.api.jira_client import JiraComment, JiraIssue

logger = logging.getLogger(__name__)


# =============================================================================
# Dataclasses (T003-T006)
# =============================================================================


@dataclass
class IssueMetrics:
    """Calculated quality metrics for a single Jira issue.

    Attributes:
        issue: Original JiraIssue data.
        cycle_time_days: Days from created to resolution (None if unresolved).
        aging_days: Days from created to now (None if resolved).
        comments_count: Total number of comments.
        description_quality_score: 0-100 score based on length/AC/formatting.
        acceptance_criteria_present: True if AC patterns detected.
        comment_velocity_hours: Hours from created to first comment (None if no comments).
        silent_issue: True if no comments exist.
        same_day_resolution: True if resolved on creation date.
        cross_team_score: 0-100 based on distinct comment authors.
        reopen_count: Number of times reopened (0 if not trackable).
    """

    issue: JiraIssue
    cycle_time_days: float | None
    aging_days: float | None
    comments_count: int
    description_quality_score: int
    acceptance_criteria_present: bool
    comment_velocity_hours: float | None
    silent_issue: bool
    same_day_resolution: bool
    cross_team_score: int
    reopen_count: int


@dataclass
class ProjectMetrics:
    """Aggregated quality metrics for a Jira project.

    Attributes:
        project_key: Jira project key (e.g., PROJ).
        total_issues: Total issues in export.
        resolved_count: Issues with resolution_date.
        unresolved_count: Issues without resolution_date.
        avg_cycle_time_days: Mean cycle time for resolved issues.
        median_cycle_time_days: Median cycle time for resolved issues.
        bug_count: Issues with type "Bug".
        bug_ratio_percent: (bug_count / total_issues) * 100.
        same_day_resolution_rate_percent: (same_day / resolved) * 100.
        avg_description_quality: Mean description_quality_score.
        silent_issues_ratio_percent: (silent / total) * 100.
        avg_comments_per_issue: Mean comments_count.
        avg_comment_velocity_hours: Mean comment_velocity for non-silent issues.
        reopen_rate_percent: (reopened / resolved) * 100.
    """

    project_key: str
    total_issues: int
    resolved_count: int
    unresolved_count: int
    avg_cycle_time_days: float | None
    median_cycle_time_days: float | None
    bug_count: int
    bug_ratio_percent: float
    same_day_resolution_rate_percent: float
    avg_description_quality: float
    silent_issues_ratio_percent: float
    avg_comments_per_issue: float
    avg_comment_velocity_hours: float | None
    reopen_rate_percent: float


@dataclass
class PersonMetrics:
    """Aggregated quality metrics for a Jira assignee.

    Attributes:
        assignee_name: Display name of assignee.
        wip_count: Count of open (unresolved) assigned issues.
        resolved_count: Count of resolved assigned issues.
        total_assigned: Total issues assigned.
        avg_cycle_time_days: Mean cycle time for their resolved issues.
        bug_count_assigned: Bugs assigned to this person.
    """

    assignee_name: str
    wip_count: int
    resolved_count: int
    total_assigned: int
    avg_cycle_time_days: float | None
    bug_count_assigned: int


@dataclass
class TypeMetrics:
    """Aggregated quality metrics for a Jira issue type.

    Attributes:
        issue_type: Issue type name (Bug, Story, Task, etc.).
        count: Total issues of this type.
        resolved_count: Resolved issues of this type.
        avg_cycle_time_days: Mean cycle time for resolved issues of this type.
        bug_resolution_time_avg: Same as avg_cycle_time_days when type is Bug (None otherwise).
    """

    issue_type: str
    count: int
    resolved_count: int
    avg_cycle_time_days: float | None
    bug_resolution_time_avg: float | None  # Only populated for Bug type


# =============================================================================
# Individual Metric Calculation Functions (T016-T022)
# =============================================================================


def calculate_cycle_time(
    created: datetime,
    resolution_date: datetime | None,
) -> float | None:
    """Calculate cycle time in days between creation and resolution (FR-001).

    Args:
        created: Issue creation timestamp.
        resolution_date: Resolution timestamp (None if unresolved).

    Returns:
        Cycle time in days as float (2 decimal precision), or None if unresolved.
        Returns None with warning logged if cycle time is negative.
    """
    if resolution_date is None:
        return None

    delta = resolution_date - created
    days = delta.total_seconds() / 86400  # Convert to days

    if days < 0:
        logger.warning(
            "Negative cycle time detected: created=%s, resolved=%s. Setting to None.",
            created.isoformat(),
            resolution_date.isoformat(),
        )
        return None

    return round(days, 2)


def calculate_aging(
    created: datetime,
    resolution_date: datetime | None,
    now: datetime | None = None,
) -> float | None:
    """Calculate aging in days for open issues (FR-002).

    Args:
        created: Issue creation timestamp.
        resolution_date: Resolution timestamp (None if unresolved).
        now: Current timestamp (defaults to UTC now).

    Returns:
        Aging in days as float (2 decimal precision), or None if resolved.
        Returns None with warning logged if aging is negative.
    """
    if resolution_date is not None:
        return None  # Resolved issues don't have aging

    if now is None:
        now = datetime.now(timezone.utc)

    delta = now - created
    days = delta.total_seconds() / 86400

    if days < 0:
        logger.warning(
            "Negative aging detected: created=%s, now=%s. Setting to None.",
            created.isoformat(),
            now.isoformat(),
        )
        return None

    return round(days, 2)


def detect_acceptance_criteria(description: str) -> bool:
    """Detect presence of acceptance criteria in description (FR-005).

    Uses regex patterns to identify common AC formats:
    - Given/When/Then (BDD)
    - AC: or Acceptance Criteria: headers
    - Checkbox lists (markdown)
    - Heading-based AC sections

    Args:
        description: Plain text description content.

    Returns:
        True if any AC pattern matches.
    """
    if not description:
        return False

    return any(re.search(pattern, description, re.MULTILINE) for pattern in AC_PATTERNS)


def calculate_description_quality(
    description: str,
    has_ac: bool,
) -> int:
    """Calculate description quality score 0-100 (FR-004).

    Uses balanced weighting:
    - 40% length (>100 chars = full score, linear interpolation below)
    - 40% acceptance criteria presence (boolean)
    - 20% formatting (10% headers + 10% lists)

    Args:
        description: Plain text description content.
        has_ac: Whether acceptance criteria were detected.

    Returns:
        Quality score 0-100 as integer.
    """
    score = 0

    # Length component (40 points max)
    length = len(description.strip()) if description else 0
    length_score = min(
        QUALITY_WEIGHT_LENGTH,
        int(length * QUALITY_WEIGHT_LENGTH / QUALITY_LENGTH_THRESHOLD),
    )
    score += length_score

    # AC presence component (40 points)
    if has_ac:
        score += QUALITY_WEIGHT_AC

    # Formatting component (20 points max)
    if description:
        # Check for headers (10 pts)
        has_headers = bool(re.search(r'^#+\s', description, re.MULTILINE))
        if has_headers:
            score += QUALITY_WEIGHT_FORMAT // 2

        # Check for lists (10 pts)
        has_lists = bool(re.search(r'^\s*[-*]\s', description, re.MULTILINE))
        if has_lists:
            score += QUALITY_WEIGHT_FORMAT // 2

    return min(100, score)  # Cap at 100


def calculate_comment_metrics(
    comments: list[JiraComment],
    issue_created: datetime,
) -> tuple[int, float | None, bool]:
    """Calculate comment-related metrics (FR-003, FR-006, FR-007).

    Args:
        comments: List of JiraComment objects for the issue.
        issue_created: Issue creation timestamp.

    Returns:
        Tuple of (comments_count, comment_velocity_hours, silent_issue).
    """
    comments_count = len(comments)
    silent_issue = comments_count == 0

    if silent_issue:
        return comments_count, None, silent_issue

    # Find first comment timestamp for velocity calculation
    first_comment = min(comments, key=lambda c: c.created)
    delta = first_comment.created - issue_created
    velocity_hours = round(delta.total_seconds() / 3600, 2)  # Convert to hours

    # Handle negative velocity (data error - comment before issue creation)
    if velocity_hours < 0:
        logger.warning(
            "Negative comment velocity detected. Setting to 0.",
        )
        velocity_hours = 0.0

    return comments_count, velocity_hours, silent_issue


def calculate_same_day_resolution(
    created: datetime,
    resolution_date: datetime | None,
) -> bool:
    """Check if issue was resolved same calendar day as created (FR-008).

    Compares dates in UTC timezone.

    Args:
        created: Issue creation timestamp.
        resolution_date: Resolution timestamp (None if unresolved).

    Returns:
        True if resolved on same calendar day as created.
    """
    if resolution_date is None:
        return False

    # Compare dates (ignoring time)
    return created.date() == resolution_date.date()


def calculate_cross_team_score(comments: list[JiraComment]) -> int:
    """Calculate cross-team collaboration score 0-100 (FR-009).

    Uses diminishing scale based on distinct comment authors:
    - 0 authors = 0
    - 1 author = 25
    - 2 authors = 50
    - 3 authors = 75
    - 4 authors = 90
    - 5+ authors = 100

    Args:
        comments: List of JiraComment objects for the issue.

    Returns:
        Cross-team score 0-100.
    """
    if not comments:
        return 0

    unique_authors = len({c.author for c in comments})
    return CROSS_TEAM_SCALE.get(unique_authors, 100)


def detect_reopens(changelog: list[dict]) -> int:
    """Detect number of reopens from issue changelog (FR-022).

    A reopen is when status transitions FROM a "Done" category
    TO a non-Done category.

    Args:
        changelog: List of changelog entries from Jira API.

    Returns:
        Number of reopen events detected.
    """
    reopen_count = 0

    for entry in changelog:
        items = entry.get("items", [])
        for item in items:
            if item.get("field") != "status":
                continue

            from_status = item.get("fromString", "")
            to_status = item.get("toString", "")

            # Check if transition is from Done category to non-Done
            if from_status in DONE_STATUSES and to_status not in DONE_STATUSES:
                reopen_count += 1

    return reopen_count


# =============================================================================
# Composite Metric Calculator (T023)
# =============================================================================


class MetricsCalculator:
    """Calculator for Jira quality metrics.

    Provides methods to calculate issue-level metrics and
    aggregate them into project, person, and type summaries.
    """

    def calculate_issue_metrics(
        self,
        issue: JiraIssue,
        comments: list[JiraComment],
        changelog: list[dict] | None = None,
        now: datetime | None = None,
    ) -> IssueMetrics:
        """Calculate all metrics for a single issue.

        Args:
            issue: JiraIssue object.
            comments: List of comments for the issue.
            changelog: Optional changelog for reopen detection.
            now: Current timestamp (defaults to UTC now).

        Returns:
            IssueMetrics with all calculated values.
        """
        # Calculate individual metrics
        cycle_time = calculate_cycle_time(issue.created, issue.resolution_date)
        aging = calculate_aging(issue.created, issue.resolution_date, now)

        has_ac = detect_acceptance_criteria(issue.description)
        quality_score = calculate_description_quality(issue.description, has_ac)

        comments_count, velocity, silent = calculate_comment_metrics(
            comments, issue.created
        )

        same_day = calculate_same_day_resolution(issue.created, issue.resolution_date)
        cross_team = calculate_cross_team_score(comments)

        # Reopen detection (best-effort)
        reopen_count = 0
        if changelog:
            reopen_count = detect_reopens(changelog)

        return IssueMetrics(
            issue=issue,
            cycle_time_days=cycle_time,
            aging_days=aging,
            comments_count=comments_count,
            description_quality_score=quality_score,
            acceptance_criteria_present=has_ac,
            comment_velocity_hours=velocity,
            silent_issue=silent,
            same_day_resolution=same_day,
            cross_team_score=cross_team,
            reopen_count=reopen_count,
        )

    def aggregate_project_metrics(
        self,
        issue_metrics: list[IssueMetrics],
        project_key: str,
    ) -> ProjectMetrics:
        """Aggregate issue metrics into project-level summary (FR-010 to FR-014).

        Args:
            issue_metrics: List of IssueMetrics for the project.
            project_key: Project key for the summary.

        Returns:
            ProjectMetrics with aggregated values.
        """
        total = len(issue_metrics)

        if total == 0:
            return ProjectMetrics(
                project_key=project_key,
                total_issues=0,
                resolved_count=0,
                unresolved_count=0,
                avg_cycle_time_days=None,
                median_cycle_time_days=None,
                bug_count=0,
                bug_ratio_percent=0.0,
                same_day_resolution_rate_percent=0.0,
                avg_description_quality=0.0,
                silent_issues_ratio_percent=0.0,
                avg_comments_per_issue=0.0,
                avg_comment_velocity_hours=None,
                reopen_rate_percent=0.0,
            )

        # Separate resolved and unresolved
        resolved = [m for m in issue_metrics if m.cycle_time_days is not None]
        resolved_count = len(resolved)
        unresolved_count = total - resolved_count

        # Cycle time calculations
        cycle_times = [m.cycle_time_days for m in resolved if m.cycle_time_days is not None]
        avg_cycle = round(mean(cycle_times), 2) if cycle_times else None
        median_cycle = round(median(cycle_times), 2) if cycle_times else None

        # Bug metrics
        bug_count = sum(1 for m in issue_metrics if m.issue.issue_type == "Bug")
        bug_ratio = round((bug_count / total) * 100, 2) if total > 0 else 0.0

        # Same-day resolution rate
        same_day_count = sum(1 for m in issue_metrics if m.same_day_resolution)
        same_day_rate = round((same_day_count / resolved_count) * 100, 2) if resolved_count > 0 else 0.0

        # Quality metrics
        avg_quality = round(mean(m.description_quality_score for m in issue_metrics), 2)

        # Silent issues
        silent_count = sum(1 for m in issue_metrics if m.silent_issue)
        silent_ratio = round((silent_count / total) * 100, 2)

        # Comment metrics
        avg_comments = round(mean(m.comments_count for m in issue_metrics), 2)

        # Comment velocity (excluding silent issues)
        velocities = [m.comment_velocity_hours for m in issue_metrics if m.comment_velocity_hours is not None]
        avg_velocity = round(mean(velocities), 2) if velocities else None

        # Reopen rate
        reopened_count = sum(1 for m in issue_metrics if m.reopen_count > 0)
        reopen_rate = round((reopened_count / resolved_count) * 100, 2) if resolved_count > 0 else 0.0

        return ProjectMetrics(
            project_key=project_key,
            total_issues=total,
            resolved_count=resolved_count,
            unresolved_count=unresolved_count,
            avg_cycle_time_days=avg_cycle,
            median_cycle_time_days=median_cycle,
            bug_count=bug_count,
            bug_ratio_percent=bug_ratio,
            same_day_resolution_rate_percent=same_day_rate,
            avg_description_quality=avg_quality,
            silent_issues_ratio_percent=silent_ratio,
            avg_comments_per_issue=avg_comments,
            avg_comment_velocity_hours=avg_velocity,
            reopen_rate_percent=reopen_rate,
        )

    def aggregate_person_metrics(
        self,
        issue_metrics: list[IssueMetrics],
    ) -> list[PersonMetrics]:
        """Aggregate issue metrics into per-person summaries (FR-015 to FR-018).

        Issues without assignee are excluded.

        Args:
            issue_metrics: List of IssueMetrics.

        Returns:
            List of PersonMetrics, one per unique assignee.
        """
        # Group by assignee (excluding unassigned)
        by_assignee: dict[str, list[IssueMetrics]] = {}
        for m in issue_metrics:
            assignee = m.issue.assignee
            if assignee:  # Skip unassigned issues
                if assignee not in by_assignee:
                    by_assignee[assignee] = []
                by_assignee[assignee].append(m)

        result = []
        for assignee_name, metrics in by_assignee.items():
            # Count WIP (open issues)
            wip = sum(1 for m in metrics if m.cycle_time_days is None)

            # Count resolved
            resolved_list = [m for m in metrics if m.cycle_time_days is not None]
            resolved_count = len(resolved_list)

            # Average cycle time for resolved issues
            cycle_times = [m.cycle_time_days for m in resolved_list if m.cycle_time_days is not None]
            avg_cycle = round(mean(cycle_times), 2) if cycle_times else None

            # Bug count
            bug_count = sum(1 for m in metrics if m.issue.issue_type == "Bug")

            result.append(PersonMetrics(
                assignee_name=assignee_name,
                wip_count=wip,
                resolved_count=resolved_count,
                total_assigned=len(metrics),
                avg_cycle_time_days=avg_cycle,
                bug_count_assigned=bug_count,
            ))

        return result

    def aggregate_type_metrics(
        self,
        issue_metrics: list[IssueMetrics],
    ) -> list[TypeMetrics]:
        """Aggregate issue metrics into per-type summaries (FR-019 to FR-021).

        Args:
            issue_metrics: List of IssueMetrics.

        Returns:
            List of TypeMetrics, one per unique issue type.
        """
        # Group by issue type
        by_type: dict[str, list[IssueMetrics]] = {}
        for m in issue_metrics:
            issue_type = m.issue.issue_type
            if issue_type not in by_type:
                by_type[issue_type] = []
            by_type[issue_type].append(m)

        result = []
        for issue_type, metrics in by_type.items():
            count = len(metrics)

            # Resolved issues
            resolved_list = [m for m in metrics if m.cycle_time_days is not None]
            resolved_count = len(resolved_list)

            # Average cycle time
            cycle_times = [m.cycle_time_days for m in resolved_list if m.cycle_time_days is not None]
            avg_cycle = round(mean(cycle_times), 2) if cycle_times else None

            # Bug resolution time (only for Bug type)
            bug_resolution_avg = avg_cycle if issue_type == "Bug" else None

            result.append(TypeMetrics(
                issue_type=issue_type,
                count=count,
                resolved_count=resolved_count,
                avg_cycle_time_days=avg_cycle,
                bug_resolution_time_avg=bug_resolution_avg,
            ))

        return result
