"""Jira issue analysis module.

This module provides the JiraIssueAnalyzer class for calculating
aggregate statistics from Jira issues.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.github_analyzer.api.jira_client import JiraIssue


class JiraIssueAnalyzer:
    """Analyze Jira issues for summary statistics.

    Provides aggregate statistics grouped by various dimensions:
    - Issue type (Bug, Story, Task, etc.)
    - Status (To Do, In Progress, Done, etc.)
    - Priority (Critical, High, Medium, Low)
    - Project
    """

    def get_stats(self, issues: list[JiraIssue]) -> dict:
        """Calculate aggregate statistics for issues.

        Args:
            issues: List of JiraIssue objects.

        Returns:
            Dictionary with aggregate statistics including:
            - total: Total number of issues
            - resolved: Number of resolved issues
            - unresolved: Number of unresolved issues
            - by_type: Count by issue type
            - by_status: Count by status
            - by_priority: Count by priority
            - by_project: Count by project
        """
        if not issues:
            return {
                "total": 0,
                "resolved": 0,
                "unresolved": 0,
                "by_type": {},
                "by_status": {},
                "by_priority": {},
                "by_project": {},
            }

        # Count totals
        resolved = sum(1 for i in issues if i.resolution_date is not None)
        unresolved = len(issues) - resolved

        # Group by dimensions
        by_type: dict[str, int] = defaultdict(int)
        by_status: dict[str, int] = defaultdict(int)
        by_priority: dict[str, int] = defaultdict(int)
        by_project: dict[str, int] = defaultdict(int)

        for issue in issues:
            by_type[issue.issue_type] += 1
            by_status[issue.status] += 1
            by_priority[issue.priority or "Unset"] += 1
            by_project[issue.project_key] += 1

        return {
            "total": len(issues),
            "resolved": resolved,
            "unresolved": unresolved,
            "by_type": dict(by_type),
            "by_status": dict(by_status),
            "by_priority": dict(by_priority),
            "by_project": dict(by_project),
        }

    def get_project_summary(self, issues: list[JiraIssue]) -> dict[str, dict]:
        """Get summary statistics per project.

        Args:
            issues: List of JiraIssue objects.

        Returns:
            Dictionary mapping project key to statistics including:
            - total: Total issues in project
            - resolved: Number resolved
            - unresolved: Number unresolved
            - resolution_rate: Percentage resolved
            - bugs: Number of bug issues
        """
        if not issues:
            return {}

        # Group issues by project
        projects: dict[str, list[JiraIssue]] = defaultdict(list)
        for issue in issues:
            projects[issue.project_key].append(issue)

        # Calculate summary per project
        result = {}
        for project_key, project_issues in projects.items():
            total = len(project_issues)
            resolved = sum(1 for i in project_issues if i.resolution_date is not None)
            bugs = sum(1 for i in project_issues if i.issue_type == "Bug")

            result[project_key] = {
                "total": total,
                "resolved": resolved,
                "unresolved": total - resolved,
                "resolution_rate": (resolved / total * 100) if total > 0 else 0.0,
                "bugs": bugs,
            }

        return result
