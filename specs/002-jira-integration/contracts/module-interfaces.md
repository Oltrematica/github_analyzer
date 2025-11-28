# Module Interfaces: Jira Integration

**Feature**: 002-jira-integration
**Date**: 2025-11-28

## Overview

This document defines the public interfaces for new and modified modules in the Jira integration feature.

## New Modules

### api/jira_client.py

```python
"""Jira REST API client with pagination and rate limiting."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterator

from src.github_analyzer.config.settings import JiraConfig


@dataclass
class JiraProject:
    """Jira project metadata."""
    key: str
    name: str
    description: str = ""


@dataclass
class JiraIssue:
    """Jira issue with core fields."""
    key: str
    summary: str
    description: str
    status: str
    issue_type: str
    priority: str | None
    assignee: str | None
    reporter: str
    created: datetime
    updated: datetime
    resolution_date: datetime | None
    project_key: str


@dataclass
class JiraComment:
    """Jira issue comment."""
    id: str
    issue_key: str
    author: str
    created: datetime
    body: str


class JiraClient:
    """HTTP client for Jira REST API.

    Provides authenticated access to Jira API with automatic
    pagination, rate limiting, and retry logic.

    Attributes:
        config: Jira configuration.
    """

    def __init__(self, config: JiraConfig) -> None:
        """Initialize client with configuration.

        Args:
            config: Jira configuration with credentials and settings.
        """
        ...

    def test_connection(self) -> bool:
        """Test authentication and connectivity.

        Returns:
            True if connection successful, False otherwise.
        """
        ...

    def get_projects(self) -> list[JiraProject]:
        """Get all accessible projects.

        Returns:
            List of projects the authenticated user can access.

        Raises:
            JiraAuthenticationError: If credentials are invalid.
            JiraAPIError: If API request fails.
        """
        ...

    def search_issues(
        self,
        project_keys: list[str],
        since_date: datetime,
    ) -> Iterator[JiraIssue]:
        """Search issues updated since given date.

        Args:
            project_keys: List of project keys to search.
            since_date: Only return issues updated after this date.

        Yields:
            JiraIssue objects matching the criteria.

        Raises:
            JiraAPIError: If API request fails.
        """
        ...

    def get_comments(self, issue_key: str) -> list[JiraComment]:
        """Get all comments for an issue.

        Args:
            issue_key: The issue key (e.g., PROJ-123).

        Returns:
            List of comments on the issue.

        Raises:
            JiraAPIError: If API request fails.
        """
        ...
```

---

### config/settings.py (Extensions)

```python
"""Extended configuration for multi-platform support."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DataSource(Enum):
    """Supported data sources."""
    GITHUB = "github"
    JIRA = "jira"


@dataclass
class JiraConfig:
    """Configuration for Jira API access.

    Attributes:
        jira_url: Jira instance URL.
        jira_email: User email for authentication.
        jira_api_token: API token (never logged).
        jira_projects_file: Path to projects list file.
        api_version: Detected API version ("2" or "3").
    """
    jira_url: str
    jira_email: str
    jira_api_token: str
    jira_projects_file: str = "jira_projects.txt"
    api_version: str = ""

    @classmethod
    def from_env(cls) -> JiraConfig | None:
        """Load configuration from environment variables.

        Returns:
            JiraConfig if all required vars set, None otherwise.
        """
        ...

    def validate(self) -> None:
        """Validate all configuration values.

        Raises:
            ValidationError: If any value is invalid.
        """
        ...

    def __repr__(self) -> str:
        """Return string representation with masked token."""
        ...
```

---

### core/exceptions.py (Extensions)

```python
"""Extended exceptions for Jira integration."""


class JiraAPIError(Exception):
    """Base exception for Jira API errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize with message and optional status code."""
        ...


class JiraAuthenticationError(JiraAPIError):
    """Authentication failed (401)."""
    pass


class JiraPermissionError(JiraAPIError):
    """Permission denied (403)."""
    pass


class JiraNotFoundError(JiraAPIError):
    """Resource not found (404)."""
    pass


class JiraRateLimitError(JiraAPIError):
    """Rate limit exceeded (429)."""

    def __init__(
        self,
        message: str,
        retry_after: int | None = None,
    ) -> None:
        """Initialize with retry-after hint."""
        ...
```

---

### exporters/jira_exporter.py

```python
"""Export Jira data to CSV files."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from src.github_analyzer.api.jira_client import JiraComment, JiraIssue


class JiraExporter:
    """Export Jira data to CSV format.

    Follows RFC 4180 for CSV formatting.
    """

    ISSUE_COLUMNS = [
        "key", "summary", "status", "issue_type", "priority",
        "assignee", "reporter", "created", "updated",
        "resolution_date", "project_key"
    ]

    COMMENT_COLUMNS = ["issue_key", "author", "created", "body"]

    def __init__(self, output_dir: str) -> None:
        """Initialize exporter.

        Args:
            output_dir: Directory for output files.
        """
        ...

    def export_issues(self, issues: Iterable[JiraIssue]) -> Path:
        """Export issues to CSV.

        Args:
            issues: Iterable of JiraIssue objects.

        Returns:
            Path to created CSV file.
        """
        ...

    def export_comments(self, comments: Iterable[JiraComment]) -> Path:
        """Export comments to CSV.

        Args:
            comments: Iterable of JiraComment objects.

        Returns:
            Path to created CSV file.
        """
        ...
```

---

### cli/main.py (Modifications)

```python
"""Extended CLI with multi-source support."""

from __future__ import annotations

import argparse


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser with multi-source options.

    New arguments:
        --sources: Comma-separated list of sources (github,jira)
                   Default: auto-detect from configured credentials
    """
    ...


def run_extraction(
    sources: list[DataSource],
    days: int,
    output_dir: str,
) -> int:
    """Run extraction for specified sources.

    Args:
        sources: List of data sources to query.
        days: Analysis period in days.
        output_dir: Output directory for CSV files.

    Returns:
        Exit code (0=success, 1=user error, 2=system error).
    """
    ...
```

---

### analyzers/jira_issues.py

```python
"""Jira issue analysis and aggregation."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from src.github_analyzer.api.jira_client import JiraIssue


@dataclass
class JiraProjectSummary:
    """Summary statistics for a Jira project."""
    project_key: str
    total_issues: int
    issues_by_status: dict[str, int]
    issues_by_type: dict[str, int]
    issues_by_priority: dict[str, int]


class JiraIssueAnalyzer:
    """Analyze Jira issues for reporting."""

    def summarize_by_project(
        self,
        issues: list[JiraIssue],
    ) -> list[JiraProjectSummary]:
        """Generate summary statistics by project.

        Args:
            issues: List of issues to analyze.

        Returns:
            Summary for each project.
        """
        ...
```

## Modified Modules

### Existing modules with changes:

| Module | Change Type | Description |
|--------|-------------|-------------|
| `config/settings.py` | Extended | Add `JiraConfig`, `DataSource` enum |
| `config/validation.py` | Extended | Add `validate_jira_url()`, `validate_project_key()` |
| `core/exceptions.py` | Extended | Add Jira-specific exceptions |
| `cli/main.py` | Modified | Add `--sources` flag, multi-source orchestration |
| `api/__init__.py` | Extended | Export `JiraClient` |
| `exporters/__init__.py` | Extended | Export `JiraExporter` |

## Dependency Graph

```
cli/main.py
├── config/settings.py (AnalyzerConfig, JiraConfig, DataSource)
├── api/client.py (GitHubClient) [existing]
├── api/jira_client.py (JiraClient) [new]
├── exporters/csv_exporter.py [existing]
└── exporters/jira_exporter.py [new]

api/jira_client.py
├── config/settings.py (JiraConfig)
└── core/exceptions.py (Jira*Error)

exporters/jira_exporter.py
└── api/jira_client.py (JiraIssue, JiraComment)
```

No circular dependencies introduced.
