"""GitHub API client with pagination and rate limiting.

This module provides the GitHubClient class for making authenticated
requests to the GitHub REST API. It supports:
- Automatic pagination
- Rate limit tracking
- Exponential backoff for transient failures
- requests/urllib fallback

Security Notes (Feature 006):
- Token is accessed from config, never stored separately
- Token is never logged or exposed in error messages
- Content-Type headers are validated on responses (FR-006)
- API requests are audit logged in verbose mode (FR-009)
- Timeout values are validated against threshold (FR-011)
"""

from __future__ import annotations

import contextlib
import json
import logging
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from src.github_analyzer.config.settings import AnalyzerConfig
from src.github_analyzer.core.exceptions import APIError, RateLimitError
from src.github_analyzer.core.security import (
    log_api_request,
    validate_content_type,
    validate_timeout,
)

# Module logger for security warnings and verbose output
_logger = logging.getLogger(__name__)

# Try to import requests for better performance
try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


GITHUB_API_BASE = "https://api.github.com"


class GitHubClient:
    """HTTP client for GitHub REST API.

    Provides authenticated access to GitHub API with automatic
    pagination, rate limiting, and retry logic.

    Attributes:
        config: Analyzer configuration.
        rate_limit_remaining: Remaining API calls (if known).
        rate_limit_reset: Timestamp when rate limit resets.
    """

    def __init__(self, config: AnalyzerConfig) -> None:
        """Initialize client with configuration.

        Args:
            config: Analyzer configuration with token and settings.

        Note:
            Token is accessed from config, never stored separately.
        """
        self._config = config
        self._rate_limit_remaining: int | None = None
        self._rate_limit_reset: int | None = None
        self._session: Any = None

        # Feature 006 (FR-011): Validate timeout against threshold
        validate_timeout(config.timeout, logger=_logger)

        # Initialize requests session if available
        if HAS_REQUESTS:
            self._session = requests.Session()
            self._session.headers.update(self._get_headers())

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authentication.

        Returns:
            Headers dict with auth token and accept type.
        """
        return {
            "Authorization": f"token {self._config.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Analyzer/2.0",
        }

    def _update_rate_limit(self, headers: dict[str, str]) -> None:
        """Update rate limit tracking from response headers.

        Args:
            headers: Response headers from GitHub API.
        """
        remaining = headers.get("X-RateLimit-Remaining")
        reset = headers.get("X-RateLimit-Reset")

        if remaining is not None:
            with contextlib.suppress(ValueError):
                self._rate_limit_remaining = int(remaining)

        if reset is not None:
            with contextlib.suppress(ValueError):
                self._rate_limit_reset = int(reset)

    @property
    def rate_limit_remaining(self) -> int | None:
        """Return remaining API calls, if known."""
        return self._rate_limit_remaining

    @property
    def rate_limit_reset(self) -> int | None:
        """Return rate limit reset timestamp, if known."""
        return self._rate_limit_reset

    def _request_with_requests(
        self,
        url: str,
        params: dict[str, Any] | None = None,
    ) -> tuple[dict | list | None, dict[str, str]]:
        """Make request using requests library.

        Args:
            url: Full URL to request.
            params: Query parameters.

        Returns:
            Tuple of (response data, headers).

        Raises:
            APIError: On request failure.
            RateLimitError: On rate limit exceeded.
        """
        start_time = time.time()
        try:
            response = self._session.get(
                url,
                params=params,
                timeout=self._config.timeout,
            )
            response_time_ms = (time.time() - start_time) * 1000

            # Update rate limit tracking
            headers = dict(response.headers)
            self._update_rate_limit(headers)

            # Feature 006 (FR-009): Verbose API audit logging
            if self._config.verbose:
                log_api_request("GET", url, response.status_code, _logger, response_time_ms)

            # Feature 006 (FR-006): Validate Content-Type header
            validate_content_type(headers, expected="application/json", logger=_logger)

            # Check for rate limit
            if response.status_code == 403 and self._rate_limit_remaining == 0:
                raise RateLimitError(
                    "GitHub API rate limit exceeded",
                    details=f"Reset at timestamp: {self._rate_limit_reset}",
                    reset_time=self._rate_limit_reset,
                )

            # Check for errors
            if response.status_code == 404:
                return None, headers

            if not response.ok:
                raise APIError(
                    f"GitHub API error: HTTP {response.status_code}",
                    details=response.text[:200] if response.text else None,
                    status_code=response.status_code,
                )

            return response.json(), headers

        except requests.exceptions.Timeout as e:
            raise APIError(
                "Request timed out",
                details=f"Timeout after {self._config.timeout}s",
            ) from e
        except requests.exceptions.RequestException as e:
            raise APIError(
                "Network error",
                details=str(e),
            ) from e

    def _request_with_urllib(
        self,
        url: str,
        params: dict[str, Any] | None = None,
    ) -> tuple[dict | list | None, dict[str, str]]:
        """Make request using urllib (stdlib fallback).

        Args:
            url: Full URL to request.
            params: Query parameters.

        Returns:
            Tuple of (response data, headers).

        Raises:
            APIError: On request failure.
            RateLimitError: On rate limit exceeded.
        """
        request_url = url
        if params:
            request_url = f"{url}?{urlencode(params)}"

        request = Request(request_url, headers=self._get_headers())

        start_time = time.time()
        try:
            with urlopen(request, timeout=self._config.timeout) as response:
                response_time_ms = (time.time() - start_time) * 1000
                headers = dict(response.headers)
                self._update_rate_limit(headers)

                # Feature 006 (FR-009): Verbose API audit logging
                if self._config.verbose:
                    log_api_request("GET", url, response.status, _logger, response_time_ms)

                # Feature 006 (FR-006): Validate Content-Type header
                validate_content_type(headers, expected="application/json", logger=_logger)

                data = json.loads(response.read().decode("utf-8"))
                return data, headers

        except HTTPError as e:
            response_time_ms = (time.time() - start_time) * 1000
            headers = dict(e.headers) if e.headers else {}
            self._update_rate_limit(headers)

            # Feature 006 (FR-009): Log even failed requests in verbose mode
            if self._config.verbose:
                log_api_request("GET", url, e.code, _logger, response_time_ms)

            if e.code == 403 and self._rate_limit_remaining == 0:
                raise RateLimitError(
                    "GitHub API rate limit exceeded",
                    details=f"Reset at timestamp: {self._rate_limit_reset}",
                    reset_time=self._rate_limit_reset,
                ) from e

            if e.code == 404:
                return None, headers

            raise APIError(
                f"GitHub API error: HTTP {e.code}",
                details=e.reason,
                status_code=e.code,
            ) from e
        except URLError as e:
            # URLError wraps socket.timeout for timeouts
            if isinstance(e.reason, TimeoutError):
                raise APIError(
                    "Request timed out",
                    details=f"Timeout after {self._config.timeout}s",
                ) from e
            raise APIError(
                "Network error",
                details=str(e.reason),
            ) from e
        except json.JSONDecodeError as e:
            raise APIError(
                "Invalid JSON response",
                details=str(e),
            ) from e

    def _request(
        self,
        url: str,
        params: dict[str, Any] | None = None,
    ) -> tuple[dict | list | None, dict[str, str]]:
        """Make request with automatic library selection.

        Args:
            url: Full URL to request.
            params: Query parameters.

        Returns:
            Tuple of (response data, headers).
        """
        if HAS_REQUESTS and self._session:
            return self._request_with_requests(url, params)
        return self._request_with_urllib(url, params)

    def _request_with_retry(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        max_retries: int = 3,
    ) -> tuple[dict | list | None, dict[str, str]]:
        """Make request with exponential backoff retry.

        Implements T058a: Exponential backoff retry logic for transient failures.

        Args:
            url: Full URL to request.
            params: Query parameters.
            max_retries: Maximum number of retry attempts.

        Returns:
            Tuple of (response data, headers).

        Raises:
            APIError: After all retries exhausted.
            RateLimitError: On rate limit (not retried).
        """
        last_error: Exception | None = None

        for attempt in range(max_retries):
            try:
                return self._request(url, params)
            except RateLimitError:
                # Don't retry rate limits
                raise
            except APIError as e:
                last_error = e
                # Only retry on server errors (5xx)
                if e.status_code and 500 <= e.status_code < 600:
                    wait_time = (2**attempt) * 0.5  # 0.5s, 1s, 2s
                    time.sleep(wait_time)
                    continue
                raise

        raise last_error or APIError("Request failed after retries")

    def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict | list | None:
        """Make GET request to GitHub API.

        Args:
            endpoint: API endpoint path (e.g., "/repos/owner/repo/commits")
            params: Query parameters.

        Returns:
            JSON response as dict/list, or None if not found.

        Raises:
            RateLimitError: If rate limit exceeded.
            APIError: On other API errors.
        """
        url = urljoin(GITHUB_API_BASE, endpoint.lstrip("/"))
        data, _ = self._request_with_retry(url, params)
        return data

    def paginate(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict]:
        """Fetch all pages from paginated endpoint.

        Automatically handles pagination up to max_pages limit.

        Args:
            endpoint: API endpoint path.
            params: Base query parameters.

        Returns:
            List of all items from all pages.
        """
        all_items: list[dict] = []
        params = dict(params) if params else {}
        params["per_page"] = self._config.per_page

        for page in range(1, self._config.max_pages + 1):
            params["page"] = page

            url = urljoin(GITHUB_API_BASE, endpoint.lstrip("/"))
            data, _ = self._request_with_retry(url, params)

            if data is None or not isinstance(data, list):
                break

            all_items.extend(data)

            # Stop if we got fewer items than requested (last page)
            if len(data) < self._config.per_page:
                break

        return all_items

    def list_user_repos(
        self,
        affiliation: str = "owner,collaborator",
    ) -> list[dict]:
        """List repositories for the authenticated user.

        Fetches all repositories the user has access to based on affiliation.
        Supports pagination for accounts with many repositories.

        Args:
            affiliation: Filter by owner relationship. Comma-separated list
                of values: owner, collaborator, organization_member.
                Defaults to "owner,collaborator" per FR-005.

        Returns:
            List of repository dictionaries with full_name, private, description.

        Raises:
            RateLimitError: If GitHub API rate limit exceeded.
            APIError: On API errors (auth failure, network issues).
        """
        return self.paginate(
            "/user/repos",
            params={"affiliation": affiliation},
        )

    def list_org_repos(
        self,
        org: str,
        repo_type: str = "all",
    ) -> list[dict]:
        """List repositories for an organization.

        Fetches all repositories in the specified organization that the
        authenticated user can access. Supports pagination for orgs
        with many repositories (100+).

        Args:
            org: Organization name (e.g., "facebook", "microsoft").
            repo_type: Type filter: all, public, private, forks, sources.
                Defaults to "all" per FR-006.

        Returns:
            List of repository dictionaries with full_name, private, description.

        Raises:
            RateLimitError: If GitHub API rate limit exceeded.
            APIError: On API errors (404 for non-existent org, auth issues).
        """
        return self.paginate(
            f"/orgs/{org}/repos",
            params={"type": repo_type},
        )

    def search_repos(
        self,
        query: str,
        per_page: int = 100,
        max_results: int = 1000,
    ) -> dict[str, Any]:
        """Search repositories using GitHub Search API (Feature 005).

        Uses the Search API to find repositories matching the query.
        Search API has separate rate limits (30 req/min authenticated)
        from the core API (5000 req/hour).

        Args:
            query: Search query string with GitHub qualifiers.
                Examples:
                - "org:github+pushed:>2025-10-30" (org repos with recent activity)
                - "user:octocat+pushed:>2025-11-01" (user repos with recent activity)
            per_page: Results per page (max 100). Defaults to 100.
            max_results: Maximum total results to return (max 1000 due to API limit).

        Returns:
            SearchResult dict with:
            - total_count: Total matching repositories
            - incomplete_results: True if results may be incomplete
            - items: List of matching repository dicts

        Raises:
            RateLimitError: If Search API rate limit exceeded (30/min).
            APIError: On API errors.

        Note:
            Search API limits:
            - Max 1000 results per query (GitHub limitation)
            - 30 requests/minute for authenticated users
            - Results may be incomplete for large result sets
        """
        url = urljoin(GITHUB_API_BASE, "/search/repositories")
        all_items: list[dict] = []
        incomplete_results = False
        total_count = 0

        # GitHub Search API limits: max 100 per page, max 1000 total
        per_page = min(per_page, 100)
        max_results = min(max_results, 1000)
        max_pages = (max_results + per_page - 1) // per_page

        for page in range(1, max_pages + 1):
            params = {
                "q": query,
                "per_page": per_page,
                "page": page,
            }

            data, _ = self._request_with_retry(url, params)

            if data is None or not isinstance(data, dict):
                break

            total_count = data.get("total_count", 0)
            incomplete_results = incomplete_results or data.get("incomplete_results", False)
            items = data.get("items", [])

            all_items.extend(items)

            # Stop if we got fewer items than requested (last page)
            # or if we've reached max_results
            if len(items) < per_page or len(all_items) >= max_results:
                break

        # Truncate to max_results
        if len(all_items) > max_results:
            all_items = all_items[:max_results]

        return {
            "total_count": total_count,
            "incomplete_results": incomplete_results,
            "items": all_items,
        }

    def search_active_org_repos(
        self,
        org: str,
        cutoff_date: str,
        per_page: int = 100,
    ) -> dict[str, Any]:
        """Search for active repositories in an organization (Feature 005 - T024).

        Uses GitHub Search API with org: and pushed: qualifiers for efficient
        filtering of large organizations.

        Args:
            org: Organization name (e.g., "github", "microsoft").
            cutoff_date: ISO date string (YYYY-MM-DD) for activity cutoff.
            per_page: Results per page (max 100).

        Returns:
            SearchResult dict with active org repositories.

        Example:
            >>> client.search_active_org_repos("github", "2025-10-30")
            {"total_count": 28, "incomplete_results": False, "items": [...]}
        """
        query = f"org:{org}+pushed:>{cutoff_date}"
        return self.search_repos(query, per_page=per_page)

    def validate_response(
        self,
        data: dict | list | None,
        required_fields: list[str] | None = None,
    ) -> bool:
        """Validate API response has required fields.

        Implements T058b: API response validation for missing/null fields.

        Args:
            data: Response data to validate.
            required_fields: List of required field names.

        Returns:
            True if valid, False otherwise.
        """
        if data is None:
            return False

        if required_fields and isinstance(data, dict):
            for field in required_fields:
                if field not in data or data[field] is None:
                    return False

        return True

    def close(self) -> None:
        """Close the HTTP session."""
        if self._session:
            self._session.close()

    def __enter__(self) -> GitHubClient:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
