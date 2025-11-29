"""Shared pytest fixtures for GitHub Analyzer tests.

This module provides fixtures used across all test modules.
Fixtures include mock API responses, sample configurations,
and test utilities.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Generator, Optional, Union
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def allow_tmp_path_for_security_validation(
    tmp_path: Path,
    request: pytest.FixtureRequest,
) -> Generator[None, None, None]:
    """Patch validate_output_path to allow tmp_path as base directory.

    This fixture enables tests to use pytest's tmp_path while
    still validating that path traversal protection works correctly.
    The security module's validate_output_path is patched to use tmp_path
    as the base directory instead of cwd.

    This is applied automatically to all tests to support the security
    features added in Feature 006.
    """

    def patched_validate_output_path(
        path: Union[str, Path],
        base_dir: Optional[Path] = None,
    ) -> Path:
        """Validate path relative to tmp_path for testing."""
        from src.github_analyzer.core.security import validate_output_path

        # Use tmp_path as the base directory for tests
        if base_dir is None:
            base_dir = tmp_path

        return validate_output_path(path, base_dir=base_dir)

    # Patch all modules that use validate_output_path
    with (
        patch(
            "src.github_analyzer.exporters.csv_exporter.validate_output_path",
            side_effect=patched_validate_output_path,
        ),
        patch(
            "src.github_analyzer.exporters.jira_exporter.validate_output_path",
            side_effect=patched_validate_output_path,
        ),
        patch(
            "src.github_analyzer.exporters.jira_metrics_exporter.validate_output_path",
            side_effect=patched_validate_output_path,
        ),
    ):
        yield


# Path to fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"
API_RESPONSES_DIR = FIXTURES_DIR / "api_responses"
SAMPLE_DATA_DIR = FIXTURES_DIR / "sample_data"


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def api_responses_dir() -> Path:
    """Return path to API responses fixtures directory."""
    return API_RESPONSES_DIR


@pytest.fixture
def sample_data_dir() -> Path:
    """Return path to sample data fixtures directory."""
    return SAMPLE_DATA_DIR


@pytest.fixture
def sample_commits() -> list[dict[str, Any]]:
    """Load sample commits from fixture file."""
    with open(API_RESPONSES_DIR / "commits.json") as f:
        return json.load(f)


@pytest.fixture
def sample_prs() -> list[dict[str, Any]]:
    """Load sample pull requests from fixture file."""
    with open(API_RESPONSES_DIR / "prs.json") as f:
        return json.load(f)


@pytest.fixture
def sample_issues() -> list[dict[str, Any]]:
    """Load sample issues from fixture file."""
    with open(API_RESPONSES_DIR / "issues.json") as f:
        return json.load(f)


@pytest.fixture
def sample_repos_file() -> Path:
    """Return path to sample repos.txt file."""
    return SAMPLE_DATA_DIR / "repos.txt"


@pytest.fixture
def mock_env_token():
    """Set up mock GITHUB_TOKEN environment variable.

    Yields the mock token value for assertions.
    """
    test_token = "ghp_test1234567890abcdefghijklmnopqrstuvwxyz"
    with patch.dict(os.environ, {"GITHUB_TOKEN": test_token}):
        yield test_token


@pytest.fixture
def mock_env_no_token():
    """Set up environment without GITHUB_TOKEN.

    Removes GITHUB_TOKEN from environment if present.
    """
    env = os.environ.copy()
    env.pop("GITHUB_TOKEN", None)
    with patch.dict(os.environ, env, clear=True):
        yield


@pytest.fixture
def mock_github_client():
    """Create a mock GitHub client for testing.

    Returns a MagicMock configured to simulate GitHubClient behavior.
    """
    client = MagicMock()
    client.rate_limit_remaining = 5000
    return client


@pytest.fixture
def temp_repos_file(tmp_path: Path) -> Path:
    """Create a temporary repos.txt file for testing.

    Args:
        tmp_path: Pytest's temporary directory fixture.

    Returns:
        Path to the temporary repos.txt file.
    """
    repos_file = tmp_path / "repos.txt"
    repos_file.write_text(
        """# Test repositories
facebook/react
microsoft/vscode
https://github.com/kubernetes/kubernetes
"""
    )
    return repos_file


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory for CSV exports.

    Args:
        tmp_path: Pytest's temporary directory fixture.

    Returns:
        Path to the temporary output directory.
    """
    output_dir = tmp_path / "github_export"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@pytest.fixture
def mock_api_response():
    """Factory fixture for creating mock API responses.

    Returns a function that creates mock response objects.
    """

    def _create_response(
        json_data: dict | list | None = None,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> MagicMock:
        response = MagicMock()
        response.status_code = status_code
        response.headers = headers or {}
        response.json.return_value = json_data
        response.text = json.dumps(json_data) if json_data else ""
        response.ok = 200 <= status_code < 300
        return response

    return _create_response


@pytest.fixture
def valid_repository_strings() -> list[str]:
    """Return a list of valid repository input strings."""
    return [
        "facebook/react",
        "microsoft/vscode",
        "owner/repo",
        "owner-name/repo-name",
        "owner_name/repo_name",
        "owner.name/repo.name",
        "https://github.com/owner/repo",
        "http://github.com/owner/repo",
        "https://github.com/owner/repo.git",
        "https://github.com/owner/repo/",
    ]


@pytest.fixture
def invalid_repository_strings() -> list[str]:
    """Return a list of invalid repository input strings."""
    return [
        "",
        "invalid",
        "no-slash",
        "/no-owner",
        "no-repo/",
        "owner//repo",
        "owner/repo/extra",
        "owner;repo",
        "owner|repo",
        "owner&repo",
        "owner$repo",
        "owner`repo",
        "owner(repo)",
        "owner{repo}",
        "owner[repo]",
        "../path/traversal",
        "owner/../repo",
    ]
