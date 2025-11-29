"""Tests for GitHub API client."""

from unittest.mock import Mock, patch

import pytest
from src.github_analyzer.api.client import GitHubClient
from src.github_analyzer.config.settings import AnalyzerConfig
from src.github_analyzer.core.exceptions import APIError, RateLimitError


@pytest.fixture
def mock_config():
    """Create a mock config."""
    config = Mock(spec=AnalyzerConfig)
    config.github_token = "ghp_test_token_12345678901234567890"
    config.timeout = 30
    config.per_page = 100
    config.max_pages = 50
    return config


class TestGitHubClientInit:
    """Tests for GitHubClient initialization."""

    def test_initializes_with_config(self, mock_config):
        """Test client initializes with config."""
        client = GitHubClient(mock_config)
        assert client._config is mock_config

    def test_initializes_rate_limit_tracking(self, mock_config):
        """Test initializes rate limit tracking."""
        client = GitHubClient(mock_config)
        assert client._rate_limit_remaining is None
        assert client._rate_limit_reset is None


class TestGitHubClientHeaders:
    """Tests for _get_headers method."""

    def test_includes_authorization_header(self, mock_config):
        """Test includes authorization header."""
        client = GitHubClient(mock_config)
        headers = client._get_headers()

        assert "Authorization" in headers
        assert headers["Authorization"] == f"token {mock_config.github_token}"

    def test_includes_accept_header(self, mock_config):
        """Test includes accept header for GitHub API v3."""
        client = GitHubClient(mock_config)
        headers = client._get_headers()

        assert "Accept" in headers
        assert "application/vnd.github" in headers["Accept"]

    def test_includes_user_agent(self, mock_config):
        """Test includes user agent header."""
        client = GitHubClient(mock_config)
        headers = client._get_headers()

        assert "User-Agent" in headers
        assert "GitHub-Analyzer" in headers["User-Agent"]


class TestGitHubClientUpdateRateLimit:
    """Tests for _update_rate_limit method."""

    def test_updates_remaining_from_headers(self, mock_config):
        """Test updates remaining from headers."""
        client = GitHubClient(mock_config)
        headers = {"X-RateLimit-Remaining": "4500", "X-RateLimit-Reset": "1234567890"}

        client._update_rate_limit(headers)

        assert client._rate_limit_remaining == 4500
        assert client._rate_limit_reset == 1234567890

    def test_handles_missing_headers(self, mock_config):
        """Test handles missing rate limit headers."""
        client = GitHubClient(mock_config)
        headers = {}

        client._update_rate_limit(headers)

        assert client._rate_limit_remaining is None
        assert client._rate_limit_reset is None

    def test_handles_invalid_values(self, mock_config):
        """Test handles invalid rate limit values."""
        client = GitHubClient(mock_config)
        headers = {"X-RateLimit-Remaining": "invalid", "X-RateLimit-Reset": "invalid"}

        # Should not raise
        client._update_rate_limit(headers)

        assert client._rate_limit_remaining is None


class TestGitHubClientRateLimitProperties:
    """Tests for rate limit properties."""

    def test_rate_limit_remaining_property(self, mock_config):
        """Test rate_limit_remaining property."""
        client = GitHubClient(mock_config)
        client._rate_limit_remaining = 1000

        assert client.rate_limit_remaining == 1000

    def test_rate_limit_reset_property(self, mock_config):
        """Test rate_limit_reset property."""
        client = GitHubClient(mock_config)
        client._rate_limit_reset = 1234567890

        assert client.rate_limit_reset == 1234567890


class TestGitHubClientClose:
    """Tests for close method."""

    def test_close_with_requests_session(self, mock_config):
        """Test close with requests session."""
        client = GitHubClient(mock_config)
        mock_session = Mock()
        client._session = mock_session

        client.close()

        mock_session.close.assert_called_once()

    def test_close_without_session(self, mock_config):
        """Test close without session."""
        client = GitHubClient(mock_config)
        client._session = None

        # Should not raise
        client.close()


class TestGitHubClientRequestWithUrllib:
    """Tests for _request_with_urllib method."""

    @patch("src.github_analyzer.api.client.urlopen")
    def test_makes_request_with_urllib(self, mock_urlopen, mock_config):
        """Test makes request with urllib."""
        mock_response = Mock()
        mock_response.read.return_value = b'{"key": "value"}'
        mock_response.headers = {"X-RateLimit-Remaining": "4000"}
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = GitHubClient(mock_config)
        client._session = None  # Force urllib

        data, headers = client._request_with_urllib("https://api.github.com/test")

        assert data == {"key": "value"}
        mock_urlopen.assert_called_once()

    @patch("src.github_analyzer.api.client.urlopen")
    def test_handles_404_returns_none(self, mock_urlopen, mock_config):
        """Test handles 404 by returning None."""
        from urllib.error import HTTPError

        mock_error = HTTPError(
            url="https://api.github.com/test",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )
        mock_urlopen.side_effect = mock_error

        client = GitHubClient(mock_config)
        client._session = None

        data, headers = client._request_with_urllib("https://api.github.com/test")

        assert data is None


class TestGitHubClientGet:
    """Tests for get method."""

    def test_get_returns_data(self, mock_config):
        """Test get returns data from API."""
        client = GitHubClient(mock_config)

        with patch.object(client, "_request_with_retry") as mock_request:
            mock_request.return_value = ({"id": 1, "name": "test"}, {})

            result = client.get("/repos/test/repo")

            assert result == {"id": 1, "name": "test"}
            mock_request.assert_called_once()

    def test_get_with_params(self, mock_config):
        """Test get passes params to request."""
        client = GitHubClient(mock_config)

        with patch.object(client, "_request_with_retry") as mock_request:
            mock_request.return_value = ({"items": []}, {})

            client.get("/search/repos", params={"q": "test"})

            call_args = mock_request.call_args
            assert "q" in str(call_args)


class TestGitHubClientPaginate:
    """Tests for paginate method."""

    def test_paginates_through_results(self, mock_config):
        """Test paginates through multiple pages."""
        mock_config.per_page = 2
        mock_config.max_pages = 10
        client = GitHubClient(mock_config)

        # First page returns 2 items (per_page), second page returns 1 (last page)
        page_results = [
            ([{"id": 1}, {"id": 2}], {}),
            ([{"id": 3}], {}),
        ]
        call_count = [0]

        def mock_request(url, params=None):  # noqa: ARG001
            result = page_results[call_count[0]]
            call_count[0] += 1
            return result

        with patch.object(client, "_request_with_retry", side_effect=mock_request):
            results = client.paginate("/repos/test/repo/commits")

            assert len(results) == 3
            assert results[0]["id"] == 1
            assert results[2]["id"] == 3

    def test_respects_max_pages(self, mock_config):
        """Test respects max_pages limit."""
        mock_config.max_pages = 2
        mock_config.per_page = 1
        client = GitHubClient(mock_config)

        # Return full pages each time (same as per_page)
        def mock_request(url, params=None):  # noqa: ARG001
            return ([{"id": params.get("page", 1)}], {})

        with patch.object(client, "_request_with_retry", side_effect=mock_request):
            results = client.paginate("/repos/test/repo/commits")

            # Should stop after max_pages
            assert len(results) == 2

    def test_handles_empty_response(self, mock_config):
        """Test handles empty response."""
        client = GitHubClient(mock_config)

        with patch.object(client, "_request_with_retry") as mock_request:
            mock_request.return_value = ([], {})

            results = client.paginate("/repos/test/repo/commits")

            assert results == []

    def test_handles_none_response(self, mock_config):
        """Test handles None response (404)."""
        client = GitHubClient(mock_config)

        with patch.object(client, "_request_with_retry") as mock_request:
            mock_request.return_value = (None, {})

            results = client.paginate("/repos/test/repo/commits")

            assert results == []


class TestGitHubClientContextManager:
    """Tests for context manager protocol."""

    def test_enter_returns_self(self, mock_config):
        """Test __enter__ returns client."""
        client = GitHubClient(mock_config)

        result = client.__enter__()

        assert result is client

    def test_exit_closes_client(self, mock_config):
        """Test __exit__ closes client."""
        client = GitHubClient(mock_config)
        mock_session = Mock()
        client._session = mock_session

        client.__exit__(None, None, None)

        mock_session.close.assert_called_once()


class TestGitHubClientValidateResponse:
    """Tests for validate_response method."""

    def test_returns_false_for_none(self, mock_config):
        """Test returns False for None data."""
        client = GitHubClient(mock_config)

        result = client.validate_response(None)

        assert result is False

    def test_returns_true_for_valid_data(self, mock_config):
        """Test returns True for valid data."""
        client = GitHubClient(mock_config)

        result = client.validate_response({"key": "value"})

        assert result is True

    def test_validates_required_fields(self, mock_config):
        """Test validates required fields."""
        client = GitHubClient(mock_config)

        result = client.validate_response(
            {"name": "test"},
            required_fields=["name", "id"]
        )

        assert result is False

    def test_returns_true_when_all_required_present(self, mock_config):
        """Test returns True when all required fields present."""
        client = GitHubClient(mock_config)

        result = client.validate_response(
            {"name": "test", "id": 1},
            required_fields=["name", "id"]
        )

        assert result is True

    def test_returns_false_for_null_required_field(self, mock_config):
        """Test returns False when required field is null."""
        client = GitHubClient(mock_config)

        result = client.validate_response(
            {"name": "test", "id": None},
            required_fields=["name", "id"]
        )

        assert result is False

    def test_returns_true_for_list_data(self, mock_config):
        """Test returns True for list data."""
        client = GitHubClient(mock_config)

        result = client.validate_response([{"id": 1}, {"id": 2}])

        assert result is True


class TestGitHubClientRequestWithRetry:
    """Tests for _request_with_retry method."""

    def test_returns_on_success(self, mock_config):
        """Test returns immediately on success."""
        client = GitHubClient(mock_config)

        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = ({"id": 1}, {})

            result, headers = client._request_with_retry("https://api.github.com/test")

            assert result == {"id": 1}
            assert mock_request.call_count == 1

    def test_raises_rate_limit_without_retry(self, mock_config):
        """Test raises rate limit error without retrying."""
        client = GitHubClient(mock_config)

        with patch.object(client, "_request") as mock_request:
            mock_request.side_effect = RateLimitError()

            with pytest.raises(RateLimitError):
                client._request_with_retry("https://api.github.com/test")

            assert mock_request.call_count == 1  # No retries

    def test_raises_api_error_for_4xx(self, mock_config):
        """Test raises API error for 4xx without retrying."""
        client = GitHubClient(mock_config)

        with patch.object(client, "_request") as mock_request:
            mock_request.side_effect = APIError("Bad request", status_code=400)

            with pytest.raises(APIError):
                client._request_with_retry("https://api.github.com/test")

            assert mock_request.call_count == 1  # No retries


class TestGitHubClientRequest:
    """Tests for _request method."""

    def test_falls_back_to_urllib(self, mock_config):
        """Test falls back to urllib when no session."""
        client = GitHubClient(mock_config)
        client._session = None

        with patch.object(client, "_request_with_urllib") as mock_urllib:
            mock_urllib.return_value = ({"id": 1}, {})

            result, headers = client._request("https://api.github.com/test")

            assert result == {"id": 1}
            mock_urllib.assert_called_once()

    def test_uses_requests_when_session_available(self, mock_config):
        """Test uses requests session when available."""
        # Skip if requests is not installed
        try:
            import requests  # noqa: F401
        except ImportError:
            pytest.skip("requests not installed")

        client = GitHubClient(mock_config)

        # Mock the requests session
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.headers = {"X-RateLimit-Remaining": "4000"}
        mock_response.json.return_value = {"id": 1}
        mock_session.get.return_value = mock_response
        client._session = mock_session

        result, headers = client._request("https://api.github.com/test")

        assert result == {"id": 1}
        mock_session.get.assert_called_once()


# Try to import requests for conditional tests
try:
    import requests as _requests_module

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


@pytest.mark.skipif(not HAS_REQUESTS, reason="requests library not installed")
class TestGitHubClientRequestWithRequests:
    """Tests for _request_with_requests method."""

    def test_makes_request_successfully(self, mock_config):
        """Test makes request with requests library."""
        client = GitHubClient(mock_config)

        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.headers = {"X-RateLimit-Remaining": "4000", "X-RateLimit-Reset": "1234567890"}
        mock_response.json.return_value = {"id": 1}
        mock_session.get.return_value = mock_response
        client._session = mock_session

        result, headers = client._request_with_requests("https://api.github.com/test")

        assert result == {"id": 1}
        assert headers["X-RateLimit-Remaining"] == "4000"

    def test_handles_404_returns_none(self, mock_config):
        """Test handles 404 by returning None."""
        client = GitHubClient(mock_config)

        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.ok = False
        mock_response.headers = {}
        mock_session.get.return_value = mock_response
        client._session = mock_session

        result, headers = client._request_with_requests("https://api.github.com/test")

        assert result is None

    def test_handles_rate_limit_403(self, mock_config):
        """Test handles rate limit 403."""
        import requests

        client = GitHubClient(mock_config)
        client._rate_limit_remaining = 0

        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.ok = False
        mock_response.headers = {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1234567890"}
        mock_session.get.return_value = mock_response
        client._session = mock_session

        with pytest.raises(RateLimitError) as exc_info:
            client._request_with_requests("https://api.github.com/test")

        assert exc_info.value.reset_time == 1234567890

    def test_handles_generic_error(self, mock_config):
        """Test handles generic HTTP error."""
        import requests

        client = GitHubClient(mock_config)

        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.ok = False
        mock_response.headers = {}
        mock_response.text = "Internal Server Error"
        mock_session.get.return_value = mock_response
        client._session = mock_session

        with pytest.raises(APIError) as exc_info:
            client._request_with_requests("https://api.github.com/test")

        assert "500" in str(exc_info.value)

    def test_handles_timeout(self, mock_config):
        """Test handles timeout exception."""
        import requests

        client = GitHubClient(mock_config)

        mock_session = Mock()
        mock_session.get.side_effect = requests.exceptions.Timeout("Request timed out")
        client._session = mock_session

        with pytest.raises(APIError) as exc_info:
            client._request_with_requests("https://api.github.com/test")

        assert "timed out" in str(exc_info.value).lower()

    def test_handles_request_exception(self, mock_config):
        """Test handles RequestException."""
        import requests

        client = GitHubClient(mock_config)

        mock_session = Mock()
        mock_session.get.side_effect = requests.exceptions.RequestException("Connection error")
        client._session = mock_session

        with pytest.raises(APIError) as exc_info:
            client._request_with_requests("https://api.github.com/test")

        assert "Network error" in str(exc_info.value)


class TestGitHubClientUrllibErrors:
    """Tests for _request_with_urllib error handling."""

    @patch("src.github_analyzer.api.client.urlopen")
    def test_handles_url_error(self, mock_urlopen, mock_config):
        """Test handles URLError."""
        from urllib.error import URLError

        mock_urlopen.side_effect = URLError("Connection refused")

        client = GitHubClient(mock_config)
        client._session = None

        with pytest.raises(APIError) as exc_info:
            client._request_with_urllib("https://api.github.com/test")

        assert "Network error" in str(exc_info.value)

    @patch("src.github_analyzer.api.client.urlopen")
    def test_handles_timeout_error(self, mock_urlopen, mock_config):
        """Test handles TimeoutError wrapped in URLError."""
        import socket
        from urllib.error import URLError

        # urllib wraps socket.timeout in URLError
        mock_urlopen.side_effect = URLError(socket.timeout("Request timed out"))

        client = GitHubClient(mock_config)
        client._session = None

        with pytest.raises(APIError) as exc_info:
            client._request_with_urllib("https://api.github.com/test")

        assert "timed out" in str(exc_info.value).lower()

    @patch("src.github_analyzer.api.client.urlopen")
    def test_handles_json_decode_error(self, mock_urlopen, mock_config):
        """Test handles JSONDecodeError."""
        mock_response = Mock()
        mock_response.read.return_value = b"not valid json {"
        mock_response.headers = {}
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = GitHubClient(mock_config)
        client._session = None

        with pytest.raises(APIError) as exc_info:
            client._request_with_urllib("https://api.github.com/test")

        assert "Invalid JSON" in str(exc_info.value)

    @patch("src.github_analyzer.api.client.urlopen")
    def test_handles_rate_limit_403(self, mock_urlopen, mock_config):
        """Test handles rate limit 403."""
        from urllib.error import HTTPError

        mock_error = HTTPError(
            url="https://api.github.com/test",
            code=403,
            msg="Forbidden",
            hdrs={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1234567890"},
            fp=None,
        )
        mock_urlopen.side_effect = mock_error

        client = GitHubClient(mock_config)
        client._session = None

        with pytest.raises(RateLimitError) as exc_info:
            client._request_with_urllib("https://api.github.com/test")

        assert "rate limit" in str(exc_info.value).lower()

    @patch("src.github_analyzer.api.client.urlopen")
    def test_handles_generic_http_error(self, mock_urlopen, mock_config):
        """Test handles generic HTTP error."""
        from urllib.error import HTTPError

        mock_error = HTTPError(
            url="https://api.github.com/test",
            code=500,
            msg="Internal Server Error",
            hdrs={},
            fp=None,
        )
        mock_urlopen.side_effect = mock_error

        client = GitHubClient(mock_config)
        client._session = None

        with pytest.raises(APIError) as exc_info:
            client._request_with_urllib("https://api.github.com/test")

        assert "500" in str(exc_info.value)

    @patch("src.github_analyzer.api.client.urlopen")
    def test_builds_url_with_params(self, mock_urlopen, mock_config):
        """Test builds URL with query parameters."""
        mock_response = Mock()
        mock_response.read.return_value = b'{"key": "value"}'
        mock_response.headers = {}
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = GitHubClient(mock_config)
        client._session = None

        client._request_with_urllib(
            "https://api.github.com/test",
            params={"page": 1, "per_page": 100}
        )

        # Verify URL was called with params
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert "page=1" in request.full_url
        assert "per_page=100" in request.full_url


class TestGitHubClientListUserRepos:
    """Tests for list_user_repos method (T003)."""

    def test_lists_user_repos_with_owner_collaborator_affiliation(self, mock_config):
        """Test list_user_repos uses owner,collaborator affiliation."""
        client = GitHubClient(mock_config)

        mock_repos = [
            {"full_name": "user/repo1", "private": False, "description": "Repo 1"},
            {"full_name": "user/repo2", "private": True, "description": "Repo 2"},
        ]

        with patch.object(client, "paginate") as mock_paginate:
            mock_paginate.return_value = mock_repos

            result = client.list_user_repos()

            assert result == mock_repos
            mock_paginate.assert_called_once()
            call_args = mock_paginate.call_args
            assert call_args[0][0] == "/user/repos"
            params = call_args[1].get("params", call_args[0][1] if len(call_args[0]) > 1 else {})
            assert params.get("affiliation") == "owner,collaborator"

    def test_lists_user_repos_with_custom_affiliation(self, mock_config):
        """Test list_user_repos accepts custom affiliation."""
        client = GitHubClient(mock_config)

        with patch.object(client, "paginate") as mock_paginate:
            mock_paginate.return_value = []

            client.list_user_repos(affiliation="owner")

            call_args = mock_paginate.call_args
            params = call_args[1].get("params", call_args[0][1] if len(call_args[0]) > 1 else {})
            assert params.get("affiliation") == "owner"

    def test_lists_user_repos_returns_empty_list(self, mock_config):
        """Test list_user_repos returns empty list when no repos."""
        client = GitHubClient(mock_config)

        with patch.object(client, "paginate") as mock_paginate:
            mock_paginate.return_value = []

            result = client.list_user_repos()

            assert result == []

    def test_lists_user_repos_handles_rate_limit(self, mock_config):
        """Test list_user_repos propagates RateLimitError."""
        client = GitHubClient(mock_config)

        with patch.object(client, "paginate") as mock_paginate:
            mock_paginate.side_effect = RateLimitError("Rate limit exceeded")

            with pytest.raises(RateLimitError):
                client.list_user_repos()

    def test_lists_user_repos_handles_api_error(self, mock_config):
        """Test list_user_repos propagates APIError."""
        client = GitHubClient(mock_config)

        with patch.object(client, "paginate") as mock_paginate:
            mock_paginate.side_effect = APIError("Unauthorized", status_code=401)

            with pytest.raises(APIError):
                client.list_user_repos()


class TestGitHubClientSearchRepos:
    """Tests for search_repos method (T003 - Feature 005)."""

    def test_search_repos_returns_search_result(self, mock_config):
        """Test search_repos returns proper SearchResult structure."""
        client = GitHubClient(mock_config)

        mock_response = {
            "total_count": 2,
            "incomplete_results": False,
            "items": [
                {"id": 1, "full_name": "org/repo1", "pushed_at": "2025-11-28T10:00:00Z"},
                {"id": 2, "full_name": "org/repo2", "pushed_at": "2025-11-25T15:30:00Z"},
            ]
        }

        with patch.object(client, "_request_with_retry") as mock_request:
            mock_request.return_value = (mock_response, {})

            result = client.search_repos("org:testorg+pushed:>2025-10-30")

            assert result["total_count"] == 2
            assert result["incomplete_results"] is False
            assert len(result["items"]) == 2
            assert result["items"][0]["full_name"] == "org/repo1"

    def test_search_repos_builds_correct_url(self, mock_config):
        """Test search_repos calls correct endpoint with query params."""
        client = GitHubClient(mock_config)

        mock_response = {"total_count": 0, "incomplete_results": False, "items": []}

        with patch.object(client, "_request_with_retry") as mock_request:
            mock_request.return_value = (mock_response, {})

            client.search_repos("org:github+pushed:>2025-10-30", per_page=50)

            call_args = mock_request.call_args
            url = call_args[0][0]
            params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("params", {})

            assert "search/repositories" in url
            assert params.get("q") == "org:github+pushed:>2025-10-30"
            assert params.get("per_page") == 50

    def test_search_repos_paginates_for_large_results(self, mock_config):
        """Test search_repos paginates when results exceed per_page."""
        mock_config.per_page = 2
        client = GitHubClient(mock_config)

        # Simulate 3 results across 2 pages
        page1 = {
            "total_count": 3,
            "incomplete_results": False,
            "items": [
                {"id": 1, "full_name": "org/repo1"},
                {"id": 2, "full_name": "org/repo2"},
            ]
        }
        page2 = {
            "total_count": 3,
            "incomplete_results": False,
            "items": [
                {"id": 3, "full_name": "org/repo3"},
            ]
        }

        call_count = [0]
        def mock_request(url, params=None):  # noqa: ARG001
            call_count[0] += 1
            if call_count[0] == 1:
                return (page1, {})
            return (page2, {})

        with patch.object(client, "_request_with_retry", side_effect=mock_request):
            result = client.search_repos("org:test", per_page=2)

            assert len(result["items"]) == 3
            assert call_count[0] == 2

    def test_search_repos_handles_empty_results(self, mock_config):
        """Test search_repos handles empty results."""
        client = GitHubClient(mock_config)

        mock_response = {"total_count": 0, "incomplete_results": False, "items": []}

        with patch.object(client, "_request_with_retry") as mock_request:
            mock_request.return_value = (mock_response, {})

            result = client.search_repos("org:empty")

            assert result["total_count"] == 0
            assert result["items"] == []

    def test_search_repos_respects_max_results(self, mock_config):
        """Test search_repos stops at max_results limit."""
        client = GitHubClient(mock_config)

        # Return more than max_results
        mock_response = {
            "total_count": 1500,
            "incomplete_results": False,
            "items": [{"id": i} for i in range(100)]
        }

        with patch.object(client, "_request_with_retry") as mock_request:
            mock_request.return_value = (mock_response, {})

            result = client.search_repos("org:large", max_results=50)

            # Should truncate to max_results
            assert len(result["items"]) <= 50

    def test_search_repos_handles_rate_limit(self, mock_config):
        """Test search_repos propagates RateLimitError."""
        client = GitHubClient(mock_config)

        with patch.object(client, "_request_with_retry") as mock_request:
            mock_request.side_effect = RateLimitError(
                "Search API rate limit exceeded",
                reset_time=1234567890
            )

            with pytest.raises(RateLimitError) as exc_info:
                client.search_repos("org:test")

            assert exc_info.value.reset_time == 1234567890

    def test_search_repos_preserves_incomplete_results_flag(self, mock_config):
        """Test search_repos preserves incomplete_results from API."""
        client = GitHubClient(mock_config)

        mock_response = {
            "total_count": 1000,
            "incomplete_results": True,  # API indicates partial results
            "items": [{"id": 1}]
        }

        with patch.object(client, "_request_with_retry") as mock_request:
            mock_request.return_value = (mock_response, {})

            result = client.search_repos("org:large")

            assert result["incomplete_results"] is True


class TestGitHubClientListOrgRepos:
    """Tests for list_org_repos method (T004)."""

    def test_lists_org_repos(self, mock_config):
        """Test list_org_repos fetches repos for organization."""
        client = GitHubClient(mock_config)

        mock_repos = [
            {"full_name": "myorg/repo1", "private": False, "description": "Org Repo 1"},
            {"full_name": "myorg/repo2", "private": True, "description": "Org Repo 2"},
        ]

        with patch.object(client, "paginate") as mock_paginate:
            mock_paginate.return_value = mock_repos

            result = client.list_org_repos("myorg")

            assert result == mock_repos
            mock_paginate.assert_called_once()
            call_args = mock_paginate.call_args
            assert call_args[0][0] == "/orgs/myorg/repos"

    def test_lists_org_repos_uses_type_all(self, mock_config):
        """Test list_org_repos uses type=all by default."""
        client = GitHubClient(mock_config)

        with patch.object(client, "paginate") as mock_paginate:
            mock_paginate.return_value = []

            client.list_org_repos("myorg")

            call_args = mock_paginate.call_args
            params = call_args[1].get("params", call_args[0][1] if len(call_args[0]) > 1 else {})
            assert params.get("type") == "all"

    def test_lists_org_repos_with_custom_type(self, mock_config):
        """Test list_org_repos accepts custom type parameter."""
        client = GitHubClient(mock_config)

        with patch.object(client, "paginate") as mock_paginate:
            mock_paginate.return_value = []

            client.list_org_repos("myorg", repo_type="public")

            call_args = mock_paginate.call_args
            params = call_args[1].get("params", call_args[0][1] if len(call_args[0]) > 1 else {})
            assert params.get("type") == "public"

    def test_lists_org_repos_returns_empty_list(self, mock_config):
        """Test list_org_repos returns empty list when no repos."""
        client = GitHubClient(mock_config)

        with patch.object(client, "paginate") as mock_paginate:
            mock_paginate.return_value = []

            result = client.list_org_repos("empty-org")

            assert result == []

    def test_lists_org_repos_handles_org_not_found(self, mock_config):
        """Test list_org_repos handles 404 for non-existent org."""
        client = GitHubClient(mock_config)

        with patch.object(client, "paginate") as mock_paginate:
            mock_paginate.side_effect = APIError("Not Found", status_code=404)

            with pytest.raises(APIError) as exc_info:
                client.list_org_repos("nonexistent-org")

            assert exc_info.value.status_code == 404

    def test_lists_org_repos_handles_rate_limit(self, mock_config):
        """Test list_org_repos propagates RateLimitError."""
        client = GitHubClient(mock_config)

        with patch.object(client, "paginate") as mock_paginate:
            mock_paginate.side_effect = RateLimitError("Rate limit exceeded")

            with pytest.raises(RateLimitError):
                client.list_org_repos("myorg")

    def test_lists_org_repos_handles_pagination(self, mock_config):
        """Test list_org_repos handles pagination for 100+ repos."""
        mock_config.per_page = 50
        mock_config.max_pages = 10
        client = GitHubClient(mock_config)

        # Simulate 150 repos (3 pages)
        mock_repos = [{"full_name": f"myorg/repo{i}"} for i in range(150)]

        with patch.object(client, "paginate") as mock_paginate:
            mock_paginate.return_value = mock_repos

            result = client.list_org_repos("myorg")

            assert len(result) == 150
            mock_paginate.assert_called_once()
