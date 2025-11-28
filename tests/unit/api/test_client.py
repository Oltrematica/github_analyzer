"""Tests for GitHub API client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

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

        def mock_request(url, params=None):
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
        def mock_request(url, params=None):
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
