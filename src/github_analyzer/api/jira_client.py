"""Jira REST API client with pagination and rate limiting.

This module provides the JiraClient class for making authenticated
requests to the Jira REST API. It supports:
- Automatic pagination for large result sets
- Rate limit handling with exponential backoff
- Both Atlassian Cloud (API v3) and Server/Data Center (API v2)
- ADF (Atlassian Document Format) to plain text conversion

Security Notes:
- Token is accessed from config, never stored separately
- Token is never logged or exposed in error messages
- All authentication uses HTTPS only
"""

from __future__ import annotations

import base64
import json
import time
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from src.github_analyzer.config.settings import JiraConfig
from src.github_analyzer.core.exceptions import (
    JiraAPIError,
    JiraAuthenticationError,
    JiraNotFoundError,
    JiraPermissionError,
    JiraRateLimitError,
)

# Try to import requests for better performance
try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# Retry configuration (FR-010)
MAX_RETRIES = 5
INITIAL_RETRY_DELAY = 1  # seconds
MAX_RETRY_DELAY = 60  # seconds


@dataclass
class JiraProject:
    """Jira project metadata.

    Attributes:
        key: Project key (e.g., PROJ, DEV).
        name: Project display name.
        description: Project description (may be empty).
    """

    key: str
    name: str
    description: str = ""


@dataclass
class JiraIssue:
    """Jira issue with core fields.

    Attributes:
        key: Issue key (e.g., PROJ-123).
        summary: Issue title/summary.
        description: Issue description (plain text).
        status: Current status name.
        issue_type: Type (Bug, Story, Task, etc.).
        priority: Priority name (may be None).
        assignee: Assignee display name (None if unassigned).
        reporter: Reporter display name.
        created: Creation timestamp (UTC).
        updated: Last update timestamp (UTC).
        resolution_date: Resolution timestamp (None if unresolved).
        project_key: Parent project key.
    """

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
    """Jira issue comment.

    Attributes:
        id: Comment ID.
        issue_key: Parent issue key.
        author: Author display name.
        created: Comment timestamp (UTC).
        body: Comment content (plain text).
    """

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
        api_version: Detected API version ("2" or "3").
    """

    def __init__(self, config: JiraConfig) -> None:
        """Initialize client with configuration.

        Args:
            config: Jira configuration with credentials and settings.

        Note:
            Token is accessed from config, never stored separately.
        """
        self.config = config
        self.api_version = config.api_version or ("3" if ".atlassian.net" in config.jira_url else "2")
        self._session: Any = None

        # Initialize requests session if available
        if HAS_REQUESTS:
            self._session = requests.Session()
            self._session.headers.update(self._get_headers())

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with Basic Authentication.

        Returns:
            Headers dict with auth token and content types.
        """
        # Basic Auth: base64(email:token)
        credentials = f"{self.config.jira_email}:{self.config.jira_api_token}"
        encoded = base64.b64encode(credentials.encode()).decode()

        return {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "DevAnalyzer/1.0",
        }

    def _make_request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        """Make an API request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.).
            path: API endpoint path.
            params: Query parameters.
            data: Request body data.

        Returns:
            Parsed JSON response.

        Raises:
            JiraAuthenticationError: If credentials are invalid (401).
            JiraPermissionError: If access is denied (403).
            JiraNotFoundError: If resource not found (404).
            JiraRateLimitError: If rate limit exceeded (429).
            JiraAPIError: For other API errors.
        """
        url = urljoin(self.config.jira_url, path)

        if params:
            url = f"{url}?{urlencode(params)}"

        body = json.dumps(data).encode() if data else None

        # Retry loop with exponential backoff (FR-010)
        delay = INITIAL_RETRY_DELAY
        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                if HAS_REQUESTS and self._session:
                    return self._make_request_with_requests(method, url, body)
                else:
                    return self._make_request_with_urllib(method, url, body)

            except JiraRateLimitError as e:
                last_error = e
                # Use Retry-After if available, otherwise exponential backoff
                wait_time = e.retry_after if e.retry_after else delay
                if attempt < MAX_RETRIES - 1:
                    time.sleep(min(wait_time, MAX_RETRY_DELAY))
                    delay = min(delay * 2, MAX_RETRY_DELAY)
                else:
                    raise

            except JiraAPIError as e:
                # Only retry on 5xx errors
                if e.status_code and 500 <= e.status_code < 600:
                    last_error = e
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(delay)
                        delay = min(delay * 2, MAX_RETRY_DELAY)
                        continue
                raise

        if last_error:
            raise last_error
        raise JiraAPIError("Request failed after max retries")

    def _make_request_with_requests(
        self,
        method: str,
        url: str,
        body: bytes | None,
    ) -> Any:
        """Make request using requests library."""
        response = self._session.request(
            method=method,
            url=url,
            data=body,
            timeout=self.config.timeout,
        )

        if response.status_code == 401:
            raise JiraAuthenticationError()
        elif response.status_code == 403:
            raise JiraPermissionError()
        elif response.status_code == 404:
            raise JiraNotFoundError()
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise JiraRateLimitError(
                retry_after=int(retry_after) if retry_after else None
            )
        elif response.status_code >= 400:
            raise JiraAPIError(
                f"API request failed: {response.status_code}",
                status_code=response.status_code,
            )

        return response.json() if response.text else {}

    def _make_request_with_urllib(
        self,
        method: str,
        url: str,
        body: bytes | None,
    ) -> Any:
        """Make request using urllib (fallback)."""
        request = Request(
            url=url,
            data=body,
            headers=self._get_headers(),
            method=method,
        )

        try:
            with urlopen(request, timeout=self.config.timeout) as response:
                data = response.read().decode()
                return json.loads(data) if data else {}

        except HTTPError as e:
            if e.code == 401:
                raise JiraAuthenticationError() from e
            elif e.code == 403:
                raise JiraPermissionError() from e
            elif e.code == 404:
                raise JiraNotFoundError() from e
            elif e.code == 429:
                retry_after = e.headers.get("Retry-After") if e.headers else None
                raise JiraRateLimitError(
                    retry_after=int(retry_after) if retry_after else None
                ) from e
            else:
                raise JiraAPIError(
                    f"API request failed: {e.code}",
                    status_code=e.code,
                ) from e

        except URLError as e:
            raise JiraAPIError(f"Network error: {e.reason}") from e

    def test_connection(self) -> bool:
        """Test authentication and connectivity.

        Returns:
            True if connection successful, False otherwise.
        """
        try:
            self._make_request("GET", f"/rest/api/{self.api_version}/serverInfo")
            return True
        except JiraAPIError:
            return False

    def get_projects(self) -> list[JiraProject]:
        """Get all accessible projects.

        Returns:
            List of projects the authenticated user can access.

        Raises:
            JiraAuthenticationError: If credentials are invalid.
            JiraAPIError: If API request fails.
        """
        response = self._make_request("GET", f"/rest/api/{self.api_version}/project")

        projects = []
        for item in response:
            projects.append(
                JiraProject(
                    key=item["key"],
                    name=item.get("name", ""),
                    description=item.get("description", "") or "",
                )
            )

        return projects

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
        if not project_keys:
            return

        # Build JQL query (FR-005)
        # Quote project keys to handle reserved JQL words (e.g., "AS", "IN", "OR")
        quoted_keys = [f'"{key}"' for key in project_keys]
        projects_jql = ", ".join(quoted_keys)
        date_str = since_date.strftime("%Y-%m-%d")
        jql = f"project in ({projects_jql}) AND updated >= '{date_str}' ORDER BY updated DESC"

        # Use different endpoint/pagination based on API version
        # - Cloud (v3): GET /search/jql with cursor-based pagination (nextPageToken)
        # - Server/DC (v2): POST /search with offset-based pagination (startAt/total)
        if self.api_version == "3":
            yield from self._search_issues_cloud(jql)
        else:
            yield from self._search_issues_server(jql)

    def _search_issues_cloud(self, jql: str) -> Iterator[JiraIssue]:
        """Search issues using Jira Cloud API (v3).

        Uses GET /rest/api/3/search/jql with cursor-based pagination.
        See: https://developer.atlassian.com/changelog/#CHANGE-2046

        Args:
            jql: JQL query string.

        Yields:
            JiraIssue objects matching the criteria.
        """
        max_results = 100
        next_page_token: str | None = None

        while True:
            params: dict[str, Any] = {
                "jql": jql,
                "maxResults": max_results,
                "fields": "*all,-comment",
            }

            if next_page_token:
                params["nextPageToken"] = next_page_token

            response = self._make_request(
                "GET",
                "/rest/api/3/search/jql",
                params=params,
            )

            issues = response.get("issues", [])

            for issue_data in issues:
                yield self._parse_issue(issue_data)

            # Check if more pages (cursor-based pagination)
            if response.get("isLast", True) or not issues:
                break

            next_page_token = response.get("nextPageToken")

    def _search_issues_server(self, jql: str) -> Iterator[JiraIssue]:
        """Search issues using Jira Server/Data Center API (v2).

        Uses POST /rest/api/2/search with offset-based pagination.

        Args:
            jql: JQL query string.

        Yields:
            JiraIssue objects matching the criteria.
        """
        max_results = 100
        start_at = 0

        while True:
            # Server API uses POST with JSON body
            body = {
                "jql": jql,
                "startAt": start_at,
                "maxResults": max_results,
                "fields": ["*all", "-comment"],
            }

            response = self._make_request(
                "POST",
                "/rest/api/2/search",
                data=body,
            )

            issues = response.get("issues", [])

            for issue_data in issues:
                yield self._parse_issue(issue_data)

            # Check if more pages (offset-based pagination)
            total = response.get("total", 0)
            start_at += len(issues)

            if start_at >= total or not issues:
                break

    def _parse_issue(self, data: dict[str, Any]) -> JiraIssue:
        """Parse API response into JiraIssue.

        Args:
            data: Issue data from API response.

        Returns:
            Parsed JiraIssue object.
        """
        fields = data.get("fields", {})

        # Parse timestamps (created and updated are required, use epoch as fallback)
        epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
        created = self._parse_datetime(fields.get("created")) or epoch
        updated = self._parse_datetime(fields.get("updated")) or epoch
        resolution_date = self._parse_datetime(fields.get("resolutiondate"))

        # Handle description (may be ADF or plain text)
        description = self._adf_to_plain_text(fields.get("description"))

        # Extract nested fields safely
        status = fields.get("status", {}).get("name", "Unknown")
        issue_type = fields.get("issuetype", {}).get("name", "Unknown")

        priority_data = fields.get("priority")
        priority = priority_data.get("name") if priority_data else None

        assignee_data = fields.get("assignee")
        assignee = assignee_data.get("displayName") if assignee_data else None

        reporter_data = fields.get("reporter", {})
        reporter = reporter_data.get("displayName", "Unknown")

        project_key = fields.get("project", {}).get("key", "")

        return JiraIssue(
            key=data.get("key", ""),
            summary=fields.get("summary", ""),
            description=description,
            status=status,
            issue_type=issue_type,
            priority=priority,
            assignee=assignee,
            reporter=reporter,
            created=created,
            updated=updated,
            resolution_date=resolution_date,
            project_key=project_key,
        )

    def get_comments(self, issue_key: str) -> list[JiraComment]:
        """Get all comments for an issue.

        Args:
            issue_key: The issue key (e.g., PROJ-123).

        Returns:
            List of comments on the issue.

        Raises:
            JiraAPIError: If API request fails.
        """
        response = self._make_request(
            "GET",
            f"/rest/api/{self.api_version}/issue/{issue_key}/comment",
        )

        comments = []
        for item in response.get("comments", []):
            # Handle body (may be ADF or plain text)
            body = self._adf_to_plain_text(item.get("body"))

            author_data = item.get("author", {})
            author = author_data.get("displayName", "Unknown")

            # created is required, use epoch as fallback
            epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
            created = self._parse_datetime(item.get("created")) or epoch

            comments.append(
                JiraComment(
                    id=str(item.get("id", "")),
                    issue_key=issue_key,
                    author=author,
                    created=created,
                    body=body,
                )
            )

        return comments

    def _parse_datetime(self, value: str | None) -> datetime | None:
        """Parse Jira datetime string to datetime object.

        Args:
            value: Jira datetime string (e.g., "2025-11-28T10:30:00.000+0000").

        Returns:
            Parsed datetime in UTC, or None if value is empty/None.
        """
        if not value:
            return None

        # Jira format: "2025-11-28T10:30:00.000+0000"
        try:
            # Remove milliseconds and fix timezone format
            if "." in value:
                value = value.split(".")[0] + value[-5:]

            # Handle +0000 format (no colon)
            if value[-5:].replace("-", "+")[0] in "+-" and ":" not in value[-5:]:
                value = value[:-2] + ":" + value[-2:]

            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, IndexError):
            return None

    def _adf_to_plain_text(self, content: Any) -> str:
        """Convert ADF (Atlassian Document Format) to plain text.

        ADF is used in Jira Cloud (API v3) for rich text content.
        Server/Data Center (API v2) uses plain text strings.

        Args:
            content: ADF document dict, plain text string, or None.

        Returns:
            Plain text representation.
        """
        if content is None:
            return ""

        # API v2 returns plain text strings
        if isinstance(content, str):
            return content

        # API v3 returns ADF documents
        if not isinstance(content, dict):
            return str(content)

        # Extract text from ADF structure
        return self._extract_text_from_adf(content)

    def _extract_text_from_adf(self, node: dict[str, Any]) -> str:
        """Recursively extract text from ADF node.

        Args:
            node: ADF node dictionary.

        Returns:
            Extracted text content.
        """
        if not isinstance(node, dict):
            return ""

        node_type = node.get("type", "")
        text_parts: list[str] = []

        # Text node - extract text directly
        if node_type == "text":
            return str(node.get("text", ""))

        # Container nodes - recurse into content
        content = node.get("content", [])
        if isinstance(content, list):
            for child in content:
                child_text = self._extract_text_from_adf(child)
                if child_text:
                    text_parts.append(child_text)

        # Join based on node type
        if node_type == "paragraph":
            return " ".join(text_parts)
        elif node_type in ("bulletList", "orderedList"):
            return "\n".join(f"- {part}" for part in text_parts)
        elif node_type == "listItem" or node_type == "codeBlock":
            return " ".join(text_parts)
        elif node_type == "doc":
            return "\n\n".join(text_parts)
        else:
            return " ".join(text_parts)
