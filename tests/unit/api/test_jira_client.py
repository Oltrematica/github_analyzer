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

    def test_search_issues_empty_project_keys(self, jira_config: JiraConfig) -> None:
        """search_issues returns immediately when project_keys is empty."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)
        since_date = datetime(2025, 11, 1, tzinfo=timezone.utc)

        with mock.patch.object(client, "_make_request") as mock_request:
            issues = list(client.search_issues([], since_date))

        assert issues == []
        mock_request.assert_not_called()


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

    def test_5xx_error_triggers_retry(self, jira_config: JiraConfig) -> None:
        """5xx errors trigger retry with exponential backoff."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)
        client._session = None  # Use urllib path

        with mock.patch("src.github_analyzer.api.jira_client.time.sleep") as mock_sleep:
            with mock.patch.object(client, "_make_request_with_urllib") as mock_urllib:
                # First 4 calls fail with 500, last succeeds
                mock_urllib.side_effect = [
                    JiraAPIError("Server error", status_code=500),
                    JiraAPIError("Server error", status_code=500),
                    JiraAPIError("Server error", status_code=500),
                    JiraAPIError("Server error", status_code=500),
                    {"key": "value"},  # Success on 5th try
                ]

                result = client._make_request("GET", "/rest/api/3/search")

                assert result == {"key": "value"}
                assert mock_urllib.call_count == 5
                assert mock_sleep.call_count == 4  # 4 sleeps for 4 retries

    def test_max_retries_exhausted_raises_last_error(self, jira_config: JiraConfig) -> None:
        """When max retries exhausted, raises last error."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)
        client._session = None

        with mock.patch("src.github_analyzer.api.jira_client.time.sleep"):
            with mock.patch.object(client, "_make_request_with_urllib") as mock_urllib:
                # All 5 calls fail with 500
                mock_urllib.side_effect = JiraAPIError("Server error", status_code=500)

                with pytest.raises(JiraAPIError) as exc_info:
                    client._make_request("GET", "/rest/api/3/search")

                assert exc_info.value.status_code == 500
                assert mock_urllib.call_count == 5

    def test_rate_limit_uses_retry_after_header(self, jira_config: JiraConfig) -> None:
        """Rate limit retries use Retry-After header value."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)
        client._session = None

        with mock.patch("src.github_analyzer.api.jira_client.time.sleep") as mock_sleep:
            with mock.patch.object(client, "_make_request_with_urllib") as mock_urllib:
                # First call returns rate limit with Retry-After, second succeeds
                mock_urllib.side_effect = [
                    JiraRateLimitError(retry_after=30),
                    {"key": "value"},
                ]

                result = client._make_request("GET", "/rest/api/3/search")

                assert result == {"key": "value"}
                # Should sleep for 30 seconds (from Retry-After)
                mock_sleep.assert_called_with(30)


class TestJiraClientRequestsPath:
    """Tests for requests library path."""

    def test_make_request_uses_requests_when_available(self, jira_config: JiraConfig) -> None:
        """When requests library is available, it is used."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        # Mock the requests session
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.text = '{"key": "value"}'
        mock_response.json.return_value = {"key": "value"}

        with mock.patch.object(client, "_session") as mock_session:
            mock_session.request.return_value = mock_response

            result = client._make_request_with_requests("GET", "https://jira.example.com/rest/api/3/search", None)

            assert result == {"key": "value"}
            mock_session.request.assert_called_once()

    def test_requests_401_raises_auth_error(self, jira_config: JiraConfig) -> None:
        """401 via requests raises JiraAuthenticationError."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        mock_response = mock.Mock()
        mock_response.status_code = 401

        with mock.patch.object(client, "_session") as mock_session:
            mock_session.request.return_value = mock_response

            with pytest.raises(JiraAuthenticationError):
                client._make_request_with_requests("GET", "https://jira.example.com/rest/api/3/search", None)

    def test_requests_403_raises_permission_error(self, jira_config: JiraConfig) -> None:
        """403 via requests raises JiraPermissionError."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        mock_response = mock.Mock()
        mock_response.status_code = 403

        with mock.patch.object(client, "_session") as mock_session:
            mock_session.request.return_value = mock_response

            with pytest.raises(JiraPermissionError):
                client._make_request_with_requests("GET", "https://jira.example.com/rest/api/3/search", None)

    def test_requests_404_raises_not_found_error(self, jira_config: JiraConfig) -> None:
        """404 via requests raises JiraNotFoundError."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        mock_response = mock.Mock()
        mock_response.status_code = 404

        with mock.patch.object(client, "_session") as mock_session:
            mock_session.request.return_value = mock_response

            with pytest.raises(JiraNotFoundError):
                client._make_request_with_requests("GET", "https://jira.example.com/rest/api/3/search", None)

    def test_requests_429_raises_rate_limit_error(self, jira_config: JiraConfig) -> None:
        """429 via requests raises JiraRateLimitError."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        mock_response = mock.Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}

        with mock.patch.object(client, "_session") as mock_session:
            mock_session.request.return_value = mock_response

            with pytest.raises(JiraRateLimitError) as exc_info:
                client._make_request_with_requests("GET", "https://jira.example.com/rest/api/3/search", None)

            assert exc_info.value.retry_after == 60

    def test_requests_429_without_retry_after(self, jira_config: JiraConfig) -> None:
        """429 via requests without Retry-After header."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        mock_response = mock.Mock()
        mock_response.status_code = 429
        mock_response.headers = {}

        with mock.patch.object(client, "_session") as mock_session:
            mock_session.request.return_value = mock_response

            with pytest.raises(JiraRateLimitError) as exc_info:
                client._make_request_with_requests("GET", "https://jira.example.com/rest/api/3/search", None)

            assert exc_info.value.retry_after is None

    def test_requests_generic_error(self, jira_config: JiraConfig) -> None:
        """Generic 4xx/5xx via requests raises JiraAPIError."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        mock_response = mock.Mock()
        mock_response.status_code = 500

        with mock.patch.object(client, "_session") as mock_session:
            mock_session.request.return_value = mock_response

            with pytest.raises(JiraAPIError) as exc_info:
                client._make_request_with_requests("GET", "https://jira.example.com/rest/api/3/search", None)

            assert exc_info.value.status_code == 500

    def test_requests_empty_response(self, jira_config: JiraConfig) -> None:
        """Empty response body via requests returns empty dict."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        mock_response = mock.Mock()
        mock_response.status_code = 204
        mock_response.text = ""

        with mock.patch.object(client, "_session") as mock_session:
            mock_session.request.return_value = mock_response

            result = client._make_request_with_requests("GET", "https://jira.example.com/rest/api/3/search", None)

            assert result == {}


class TestJiraClientUrllibPath:
    """Tests for urllib fallback path."""

    def test_urllib_401_raises_auth_error(self, jira_config: JiraConfig) -> None:
        """401 via urllib raises JiraAuthenticationError."""
        from urllib.error import HTTPError

        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        mock_error = HTTPError(
            url="https://jira.example.com",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=None,
        )

        with mock.patch("src.github_analyzer.api.jira_client.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = mock_error

            with pytest.raises(JiraAuthenticationError):
                client._make_request_with_urllib("GET", "https://jira.example.com/rest/api/3/search", None)

    def test_urllib_403_raises_permission_error(self, jira_config: JiraConfig) -> None:
        """403 via urllib raises JiraPermissionError."""
        from urllib.error import HTTPError

        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        mock_error = HTTPError(
            url="https://jira.example.com",
            code=403,
            msg="Forbidden",
            hdrs=None,
            fp=None,
        )

        with mock.patch("src.github_analyzer.api.jira_client.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = mock_error

            with pytest.raises(JiraPermissionError):
                client._make_request_with_urllib("GET", "https://jira.example.com/rest/api/3/search", None)

    def test_urllib_404_raises_not_found_error(self, jira_config: JiraConfig) -> None:
        """404 via urllib raises JiraNotFoundError."""
        from urllib.error import HTTPError

        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        mock_error = HTTPError(
            url="https://jira.example.com",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None,
        )

        with mock.patch("src.github_analyzer.api.jira_client.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = mock_error

            with pytest.raises(JiraNotFoundError):
                client._make_request_with_urllib("GET", "https://jira.example.com/rest/api/3/search", None)

    def test_urllib_429_raises_rate_limit_error(self, jira_config: JiraConfig) -> None:
        """429 via urllib raises JiraRateLimitError."""
        from http.client import HTTPMessage
        from io import BytesIO
        from urllib.error import HTTPError

        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        # Create mock headers with Retry-After
        headers = HTTPMessage()
        headers["Retry-After"] = "60"

        mock_error = HTTPError(
            url="https://jira.example.com",
            code=429,
            msg="Too Many Requests",
            hdrs=headers,
            fp=BytesIO(b""),
        )

        with mock.patch("src.github_analyzer.api.jira_client.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = mock_error

            with pytest.raises(JiraRateLimitError) as exc_info:
                client._make_request_with_urllib("GET", "https://jira.example.com/rest/api/3/search", None)

            assert exc_info.value.retry_after == 60

    def test_urllib_429_without_headers(self, jira_config: JiraConfig) -> None:
        """429 via urllib without headers."""
        from urllib.error import HTTPError

        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        mock_error = HTTPError(
            url="https://jira.example.com",
            code=429,
            msg="Too Many Requests",
            hdrs=None,
            fp=None,
        )

        with mock.patch("src.github_analyzer.api.jira_client.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = mock_error

            with pytest.raises(JiraRateLimitError) as exc_info:
                client._make_request_with_urllib("GET", "https://jira.example.com/rest/api/3/search", None)

            assert exc_info.value.retry_after is None

    def test_urllib_generic_http_error(self, jira_config: JiraConfig) -> None:
        """Generic HTTP error via urllib raises JiraAPIError."""
        from urllib.error import HTTPError

        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        mock_error = HTTPError(
            url="https://jira.example.com",
            code=500,
            msg="Internal Server Error",
            hdrs=None,
            fp=None,
        )

        with mock.patch("src.github_analyzer.api.jira_client.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = mock_error

            with pytest.raises(JiraAPIError) as exc_info:
                client._make_request_with_urllib("GET", "https://jira.example.com/rest/api/3/search", None)

            assert exc_info.value.status_code == 500

    def test_urllib_url_error(self, jira_config: JiraConfig) -> None:
        """URLError via urllib raises JiraAPIError."""
        from urllib.error import URLError

        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        mock_error = URLError(reason="Connection refused")

        with mock.patch("src.github_analyzer.api.jira_client.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = mock_error

            with pytest.raises(JiraAPIError) as exc_info:
                client._make_request_with_urllib("GET", "https://jira.example.com/rest/api/3/search", None)

            assert "Network error" in str(exc_info.value)

    def test_urllib_success_empty_response(self, jira_config: JiraConfig) -> None:
        """Empty response body via urllib returns empty dict."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        mock_response = mock.Mock()
        mock_response.read.return_value = b""
        mock_response.__enter__ = mock.Mock(return_value=mock_response)
        mock_response.__exit__ = mock.Mock(return_value=False)

        with mock.patch("src.github_analyzer.api.jira_client.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response

            result = client._make_request_with_urllib("GET", "https://jira.example.com/rest/api/3/search", None)

            assert result == {}


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

    def test_convert_non_dict_non_string(self, jira_config: JiraConfig) -> None:
        """Non-dict, non-string content is converted to string."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        result = client._adf_to_plain_text(12345)
        assert result == "12345"

    def test_extract_text_from_non_dict(self, jira_config: JiraConfig) -> None:
        """Non-dict ADF node returns empty string."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        result = client._extract_text_from_adf("not a dict")
        assert result == ""

    def test_extract_text_unknown_node_type(self, jira_config: JiraConfig) -> None:
        """Unknown ADF node types join content with spaces."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        adf = {
            "type": "unknownType",
            "content": [
                {"type": "text", "text": "First"},
                {"type": "text", "text": "Second"},
            ],
        }

        result = client._extract_text_from_adf(adf)
        assert result == "First Second"

    def test_extract_text_ordered_list(self, jira_config: JiraConfig) -> None:
        """Ordered list ADF nodes are formatted with bullets."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        adf = {
            "type": "orderedList",
            "content": [
                {
                    "type": "listItem",
                    "content": [{"type": "text", "text": "Item A"}],
                },
                {
                    "type": "listItem",
                    "content": [{"type": "text", "text": "Item B"}],
                },
            ],
        }

        result = client._extract_text_from_adf(adf)
        assert "- Item A" in result
        assert "- Item B" in result

    def test_extract_text_code_block(self, jira_config: JiraConfig) -> None:
        """Code block ADF nodes extract text content."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        adf = {
            "type": "codeBlock",
            "content": [{"type": "text", "text": "console.log('hello')"}],
        }

        result = client._extract_text_from_adf(adf)
        assert result == "console.log('hello')"


class TestDatetimeParsing:
    """Tests for datetime parsing."""

    def test_parse_datetime_none(self, jira_config: JiraConfig) -> None:
        """None value returns None."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)
        assert client._parse_datetime(None) is None

    def test_parse_datetime_empty_string(self, jira_config: JiraConfig) -> None:
        """Empty string returns None."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)
        assert client._parse_datetime("") is None

    def test_parse_datetime_with_milliseconds(self, jira_config: JiraConfig) -> None:
        """Parse datetime with milliseconds."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)
        result = client._parse_datetime("2025-11-28T10:30:00.123+0000")

        assert result is not None
        assert result.year == 2025
        assert result.month == 11
        assert result.day == 28

    def test_parse_datetime_with_z_suffix(self, jira_config: JiraConfig) -> None:
        """Parse datetime with Z suffix."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)
        result = client._parse_datetime("2025-11-28T10:30:00Z")

        assert result is not None
        assert result.year == 2025

    def test_parse_datetime_invalid_format(self, jira_config: JiraConfig) -> None:
        """Invalid format returns None."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)
        assert client._parse_datetime("not-a-date") is None

    def test_parse_datetime_partial_format(self, jira_config: JiraConfig) -> None:
        """Partial datetime string returns None on parse error."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)
        # Very short string that will cause IndexError
        assert client._parse_datetime("202") is None


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
