"""Unit tests for JiraClient.

Tests for:
- JiraClient initialization and configuration
- test_connection() method
- get_projects() method
- search_issues() with pagination
- get_comments() method
- Rate limit handling and retry logic
- ADF to plain text conversion
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest import mock

import pytest

from src.github_analyzer.config.settings import JiraConfig
from src.github_analyzer.core.exceptions import (
    JiraAPIError,
    JiraAuthenticationError,
    JiraNotFoundError,
    JiraPermissionError,
    JiraRateLimitError,
)
from tests.fixtures.jira_responses import (
    ADF_COMPLEX_BODY,
    COMMENTS_EMPTY_RESPONSE,
    COMMENTS_RESPONSE,
    ERROR_401_RESPONSE,
    ERROR_403_RESPONSE,
    ERROR_404_RESPONSE,
    ISSUE_SEARCH_EMPTY_RESPONSE,
    ISSUE_SEARCH_RESPONSE_PAGE_1,
    ISSUE_SEARCH_RESPONSE_PAGE_2,
    PROJECTS_RESPONSE,
    SERVER_INFO_RESPONSE,
)


@pytest.fixture
def jira_config() -> JiraConfig:
    """Create a test JiraConfig."""
    return JiraConfig(
        jira_url="https://company.atlassian.net",
        jira_email="test@company.com",
        jira_api_token="test-token",
    )


@pytest.fixture
def server_config() -> JiraConfig:
    """Create a test JiraConfig for on-premises server."""
    return JiraConfig(
        jira_url="https://jira.company.com",
        jira_email="test@company.com",
        jira_api_token="test-token",
    )


class TestJiraClientInit:
    """Tests for JiraClient initialization."""

    def test_init_creates_client(self, jira_config: JiraConfig) -> None:
        """Client is created with config."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)
        assert client.config == jira_config

    def test_init_detects_cloud_api_version(self, jira_config: JiraConfig) -> None:
        """Cloud URL uses API v3."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)
        assert client.api_version == "3"

    def test_init_detects_server_api_version(self, server_config: JiraConfig) -> None:
        """Server URL uses API v2."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(server_config)
        assert client.api_version == "2"


class TestJiraClientHeaders:
    """Tests for authentication headers."""

    def test_headers_include_basic_auth(self, jira_config: JiraConfig) -> None:
        """Headers include Basic Auth."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)
        headers = client._get_headers()

        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")

    def test_headers_include_content_type(self, jira_config: JiraConfig) -> None:
        """Headers include JSON content type."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)
        headers = client._get_headers()

        assert headers["Content-Type"] == "application/json"

    def test_headers_include_accept(self, jira_config: JiraConfig) -> None:
        """Headers include Accept header."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)
        headers = client._get_headers()

        assert headers["Accept"] == "application/json"


class TestJiraClientTestConnection:
    """Tests for test_connection() method."""

    def test_connection_success(self, jira_config: JiraConfig) -> None:
        """test_connection returns True on success."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        with mock.patch.object(client, "_make_request") as mock_request:
            mock_request.return_value = SERVER_INFO_RESPONSE
            result = client.test_connection()

        assert result is True
        mock_request.assert_called_once()

    def test_connection_failure_auth(self, jira_config: JiraConfig) -> None:
        """test_connection returns False on auth failure."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        with mock.patch.object(client, "_make_request") as mock_request:
            mock_request.side_effect = JiraAuthenticationError()
            result = client.test_connection()

        assert result is False

    def test_connection_failure_api_error(self, jira_config: JiraConfig) -> None:
        """test_connection returns False on API error."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        with mock.patch.object(client, "_make_request") as mock_request:
            mock_request.side_effect = JiraAPIError("Connection failed")
            result = client.test_connection()

        assert result is False


class TestJiraClientGetProjects:
    """Tests for get_projects() method."""

    def test_get_projects_success(self, jira_config: JiraConfig) -> None:
        """get_projects returns list of JiraProject."""
        from src.github_analyzer.api.jira_client import JiraClient, JiraProject

        client = JiraClient(jira_config)

        with mock.patch.object(client, "_make_request") as mock_request:
            mock_request.return_value = PROJECTS_RESPONSE
            projects = client.get_projects()

        assert len(projects) == 3
        assert all(isinstance(p, JiraProject) for p in projects)
        assert projects[0].key == "PROJ"
        assert projects[0].name == "Main Project"

    def test_get_projects_empty(self, jira_config: JiraConfig) -> None:
        """get_projects returns empty list when no projects."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        with mock.patch.object(client, "_make_request") as mock_request:
            mock_request.return_value = []
            projects = client.get_projects()

        assert projects == []


class TestJiraClientSearchIssues:
    """Tests for search_issues() method."""

    def test_search_issues_single_page(self, jira_config: JiraConfig) -> None:
        """search_issues yields issues from single page."""
        from src.github_analyzer.api.jira_client import JiraClient, JiraIssue

        client = JiraClient(jira_config)
        since_date = datetime(2025, 11, 1, tzinfo=timezone.utc)

        # Single page with 2 issues
        single_page_response = {
            **ISSUE_SEARCH_RESPONSE_PAGE_1,
            "total": 2,
        }

        with mock.patch.object(client, "_make_request") as mock_request:
            mock_request.return_value = single_page_response
            issues = list(client.search_issues(["PROJ"], since_date))

        assert len(issues) == 2
        assert all(isinstance(i, JiraIssue) for i in issues)
        assert issues[0].key == "PROJ-1"
        assert issues[0].summary == "First issue"

    def test_search_issues_pagination(self, jira_config: JiraConfig) -> None:
        """search_issues handles pagination correctly."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)
        since_date = datetime(2025, 11, 1, tzinfo=timezone.utc)

        # Create page 1 with total=3 (need 2 pages)
        page_1 = {
            "expand": "schema,names",
            "startAt": 0,
            "maxResults": 100,
            "total": 3,
            "issues": ISSUE_SEARCH_RESPONSE_PAGE_1["issues"],  # 2 issues
        }

        # Create page 2 with total=3, startAt=2 (already fetched 2)
        page_2 = {
            "expand": "schema,names",
            "startAt": 2,
            "maxResults": 100,
            "total": 3,
            "issues": ISSUE_SEARCH_RESPONSE_PAGE_2["issues"],  # 1 issue
        }

        with mock.patch.object(client, "_make_request") as mock_request:
            mock_request.side_effect = [page_1, page_2]
            issues = list(client.search_issues(["PROJ"], since_date))

        # 2 from page 1 + 1 from page 2
        assert len(issues) == 3
        assert mock_request.call_count == 2

    def test_search_issues_empty_result(self, jira_config: JiraConfig) -> None:
        """search_issues returns empty iterator when no matches."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)
        since_date = datetime(2025, 11, 1, tzinfo=timezone.utc)

        with mock.patch.object(client, "_make_request") as mock_request:
            mock_request.return_value = ISSUE_SEARCH_EMPTY_RESPONSE
            issues = list(client.search_issues(["PROJ"], since_date))

        assert issues == []

    def test_search_issues_builds_jql(self, jira_config: JiraConfig) -> None:
        """search_issues builds correct JQL query."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)
        since_date = datetime(2025, 11, 1, tzinfo=timezone.utc)

        with mock.patch.object(client, "_make_request") as mock_request:
            mock_request.return_value = ISSUE_SEARCH_EMPTY_RESPONSE
            list(client.search_issues(["PROJ", "DEV"], since_date))

        # Check the JQL in the request
        call_args = mock_request.call_args
        assert "project in (PROJ, DEV)" in str(call_args) or "project in (PROJ,DEV)" in str(call_args)
        assert "2025-11-01" in str(call_args)


class TestJiraClientGetComments:
    """Tests for get_comments() method."""

    def test_get_comments_success(self, jira_config: JiraConfig) -> None:
        """get_comments returns list of JiraComment."""
        from src.github_analyzer.api.jira_client import JiraClient, JiraComment

        client = JiraClient(jira_config)

        with mock.patch.object(client, "_make_request") as mock_request:
            mock_request.return_value = COMMENTS_RESPONSE
            comments = client.get_comments("PROJ-1")

        assert len(comments) == 2
        assert all(isinstance(c, JiraComment) for c in comments)
        assert comments[0].issue_key == "PROJ-1"
        assert comments[0].author == "John Doe"

    def test_get_comments_empty(self, jira_config: JiraConfig) -> None:
        """get_comments returns empty list when no comments."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        with mock.patch.object(client, "_make_request") as mock_request:
            mock_request.return_value = COMMENTS_EMPTY_RESPONSE
            comments = client.get_comments("PROJ-1")

        assert comments == []


class TestJiraClientErrorHandling:
    """Tests for error handling."""

    def test_401_raises_auth_error(self, jira_config: JiraConfig) -> None:
        """401 response raises JiraAuthenticationError."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        # Mock the internal urllib method to raise the expected error
        with mock.patch.object(client, "_make_request_with_urllib") as mock_urllib:
            mock_urllib.side_effect = JiraAuthenticationError()
            # Also disable requests session if present
            client._session = None

            with pytest.raises(JiraAuthenticationError):
                client._make_request("GET", "/rest/api/3/serverInfo")

    def test_403_raises_permission_error(self, jira_config: JiraConfig) -> None:
        """403 response raises JiraPermissionError."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        with mock.patch.object(client, "_make_request_with_urllib") as mock_urllib:
            mock_urllib.side_effect = JiraPermissionError()
            client._session = None

            with pytest.raises(JiraPermissionError):
                client._make_request("GET", "/rest/api/3/project/PROJ")

    def test_404_raises_not_found_error(self, jira_config: JiraConfig) -> None:
        """404 response raises JiraNotFoundError."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        with mock.patch.object(client, "_make_request_with_urllib") as mock_urllib:
            mock_urllib.side_effect = JiraNotFoundError()
            client._session = None

            with pytest.raises(JiraNotFoundError):
                client._make_request("GET", "/rest/api/3/issue/INVALID-1")

    def test_429_raises_rate_limit_error(self, jira_config: JiraConfig) -> None:
        """429 response raises JiraRateLimitError after max retries."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        # Mock time.sleep to avoid actual delays during test
        with mock.patch("src.github_analyzer.api.jira_client.time.sleep"):
            with mock.patch.object(client, "_make_request_with_urllib") as mock_urllib:
                mock_urllib.side_effect = JiraRateLimitError(retry_after=60)
                client._session = None

                with pytest.raises(JiraRateLimitError) as exc_info:
                    client._make_request("GET", "/rest/api/3/search")

                assert exc_info.value.retry_after == 60


class TestADFConversion:
    """Tests for ADF to plain text conversion."""

    def test_convert_simple_text(self, jira_config: JiraConfig) -> None:
        """Convert simple ADF paragraph to plain text."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        adf = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Simple text."}],
                }
            ],
        }

        result = client._adf_to_plain_text(adf)
        assert result == "Simple text."

    def test_convert_multiple_paragraphs(self, jira_config: JiraConfig) -> None:
        """Convert ADF with multiple paragraphs."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        adf = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "First paragraph."}],
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Second paragraph."}],
                },
            ],
        }

        result = client._adf_to_plain_text(adf)
        assert "First paragraph." in result
        assert "Second paragraph." in result

    def test_convert_complex_adf(self, jira_config: JiraConfig) -> None:
        """Convert complex ADF with formatting."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        result = client._adf_to_plain_text(ADF_COMPLEX_BODY)

        # Should contain the text content
        assert "bold" in result
        assert "italic" in result
        assert "Item 1" in result
        assert "Item 2" in result
        assert "print('hello')" in result

    def test_convert_none_returns_empty(self, jira_config: JiraConfig) -> None:
        """Convert None ADF returns empty string."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        result = client._adf_to_plain_text(None)
        assert result == ""

    def test_convert_plain_string(self, jira_config: JiraConfig) -> None:
        """Plain string (API v2) is returned as-is."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        result = client._adf_to_plain_text("Plain text description")
        assert result == "Plain text description"


class TestJiraDataclasses:
    """Tests for Jira dataclasses."""

    def test_jira_project_creation(self) -> None:
        """JiraProject can be created."""
        from src.github_analyzer.api.jira_client import JiraProject

        project = JiraProject(
            key="PROJ",
            name="Test Project",
            description="A test project",
        )
        assert project.key == "PROJ"
        assert project.name == "Test Project"

    def test_jira_issue_creation(self) -> None:
        """JiraIssue can be created."""
        from src.github_analyzer.api.jira_client import JiraIssue

        now = datetime.now(timezone.utc)
        issue = JiraIssue(
            key="PROJ-1",
            summary="Test issue",
            description="Description",
            status="Open",
            issue_type="Bug",
            priority="High",
            assignee="John Doe",
            reporter="Jane Smith",
            created=now,
            updated=now,
            resolution_date=None,
            project_key="PROJ",
        )
        assert issue.key == "PROJ-1"
        assert issue.summary == "Test issue"
        assert issue.resolution_date is None

    def test_jira_comment_creation(self) -> None:
        """JiraComment can be created."""
        from src.github_analyzer.api.jira_client import JiraComment

        now = datetime.now(timezone.utc)
        comment = JiraComment(
            id="10001",
            issue_key="PROJ-1",
            author="John Doe",
            created=now,
            body="This is a comment.",
        )
        assert comment.id == "10001"
        assert comment.issue_key == "PROJ-1"
        assert comment.body == "This is a comment."
