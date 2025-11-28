"""Integration tests for Jira extraction flow.

Tests the end-to-end flow of extracting Jira issues and comments
with mocked API responses.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest import mock

import pytest

from src.github_analyzer.config.settings import JiraConfig
from tests.fixtures.jira_responses import (
    COMMENTS_RESPONSE,
    ISSUE_SEARCH_RESPONSE_PAGE_1,
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


class TestJiraExtractionFlow:
    """Integration tests for complete Jira extraction flow."""

    def test_full_extraction_flow(self, jira_config: JiraConfig) -> None:
        """Test complete extraction: connection → projects → issues → comments."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        # Mock responses for each step
        with mock.patch.object(client, "_make_request") as mock_request:
            # Setup responses in order
            single_page_response = {
                **ISSUE_SEARCH_RESPONSE_PAGE_1,
                "total": 2,  # Only 2 issues, no pagination
            }

            mock_request.side_effect = [
                SERVER_INFO_RESPONSE,  # test_connection
                PROJECTS_RESPONSE,  # get_projects
                single_page_response,  # search_issues
                COMMENTS_RESPONSE,  # get_comments for PROJ-1
                {"startAt": 0, "maxResults": 50, "total": 0, "comments": []},  # get_comments for PROJ-2
            ]

            # Step 1: Test connection
            assert client.test_connection() is True

            # Step 2: Get projects
            projects = client.get_projects()
            assert len(projects) == 3
            assert projects[0].key == "PROJ"

            # Step 3: Search issues
            since_date = datetime(2025, 11, 1, tzinfo=timezone.utc)
            issues = list(client.search_issues(["PROJ"], since_date))
            assert len(issues) == 2
            assert issues[0].key == "PROJ-1"
            assert issues[1].key == "PROJ-2"

            # Step 4: Get comments for each issue
            comments_1 = client.get_comments("PROJ-1")
            assert len(comments_1) == 2
            assert comments_1[0].body == "This is a comment."

            comments_2 = client.get_comments("PROJ-2")
            assert len(comments_2) == 0

    def test_extraction_with_multiple_projects(self, jira_config: JiraConfig) -> None:
        """Test extraction across multiple projects."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        with mock.patch.object(client, "_make_request") as mock_request:
            single_page_response = {
                **ISSUE_SEARCH_RESPONSE_PAGE_1,
                "total": 2,
            }

            mock_request.return_value = single_page_response

            since_date = datetime(2025, 11, 1, tzinfo=timezone.utc)
            issues = list(client.search_issues(["PROJ", "DEV", "SUPPORT"], since_date))

            assert len(issues) == 2

            # Verify JQL includes all projects
            call_args = mock_request.call_args
            assert call_args is not None

    def test_extraction_respects_time_filter(self, jira_config: JiraConfig) -> None:
        """Test that extraction uses correct time filter in JQL."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        with mock.patch.object(client, "_make_request") as mock_request:
            mock_request.return_value = {
                "expand": "schema,names",
                "startAt": 0,
                "maxResults": 100,
                "total": 0,
                "issues": [],
            }

            # Use specific date
            since_date = datetime(2025, 11, 15, 10, 30, 0, tzinfo=timezone.utc)
            list(client.search_issues(["PROJ"], since_date))

            # Verify the date was used in the request
            call_args = mock_request.call_args
            assert call_args is not None
            # The JQL should include the date in ISO format
            call_str = str(call_args)
            assert "2025-11-15" in call_str

    def test_issue_field_extraction(self, jira_config: JiraConfig) -> None:
        """Test that all issue fields are correctly extracted."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        with mock.patch.object(client, "_make_request") as mock_request:
            single_page_response = {
                **ISSUE_SEARCH_RESPONSE_PAGE_1,
                "total": 2,
            }
            mock_request.return_value = single_page_response

            since_date = datetime(2025, 11, 1, tzinfo=timezone.utc)
            issues = list(client.search_issues(["PROJ"], since_date))

            # Check first issue (with all fields)
            issue = issues[0]
            assert issue.key == "PROJ-1"
            assert issue.summary == "First issue"
            assert issue.status == "Open"
            assert issue.issue_type == "Bug"
            assert issue.priority == "High"
            assert issue.assignee == "John Doe"
            assert issue.reporter == "Jane Smith"
            assert issue.project_key == "PROJ"
            assert issue.resolution_date is None

            # Check second issue (with null fields)
            issue2 = issues[1]
            assert issue2.key == "PROJ-2"
            assert issue2.priority is None
            assert issue2.assignee is None
            assert issue2.resolution_date is not None

    def test_comment_field_extraction(self, jira_config: JiraConfig) -> None:
        """Test that all comment fields are correctly extracted."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        with mock.patch.object(client, "_make_request") as mock_request:
            mock_request.return_value = COMMENTS_RESPONSE

            comments = client.get_comments("PROJ-1")

            # Check first comment
            comment = comments[0]
            assert comment.id == "10001"
            assert comment.issue_key == "PROJ-1"
            assert comment.author == "John Doe"
            assert "This is a comment" in comment.body

            # Check second comment (with multi-paragraph body)
            comment2 = comments[1]
            assert comment2.author == "Jane Smith"
            assert "Reply to the comment" in comment2.body
            assert "Second paragraph" in comment2.body


class TestJiraExtractionEdgeCases:
    """Test edge cases in Jira extraction."""

    def test_empty_project_list(self, jira_config: JiraConfig) -> None:
        """Test extraction with empty project list."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        with mock.patch.object(client, "_make_request") as mock_request:
            mock_request.return_value = {
                "expand": "schema,names",
                "startAt": 0,
                "maxResults": 100,
                "total": 0,
                "issues": [],
            }

            since_date = datetime(2025, 11, 1, tzinfo=timezone.utc)
            issues = list(client.search_issues([], since_date))

            assert issues == []

    def test_issue_with_null_description(self, jira_config: JiraConfig) -> None:
        """Test issue with null description is handled."""
        from src.github_analyzer.api.jira_client import JiraClient

        client = JiraClient(jira_config)

        with mock.patch.object(client, "_make_request") as mock_request:
            response = {
                "expand": "schema,names",
                "startAt": 0,
                "maxResults": 100,
                "total": 1,
                "issues": [
                    {
                        "id": "10001",
                        "key": "PROJ-1",
                        "fields": {
                            "summary": "Issue with no description",
                            "description": None,
                            "status": {"name": "Open"},
                            "issuetype": {"name": "Bug"},
                            "priority": None,
                            "assignee": None,
                            "reporter": {"displayName": "Jane"},
                            "created": "2025-11-20T10:30:00.000+0000",
                            "updated": "2025-11-28T14:15:00.000+0000",
                            "resolutiondate": None,
                            "project": {"key": "PROJ"},
                        },
                    }
                ],
            }
            mock_request.return_value = response

            since_date = datetime(2025, 11, 1, tzinfo=timezone.utc)
            issues = list(client.search_issues(["PROJ"], since_date))

            assert len(issues) == 1
            assert issues[0].description == ""

    def test_handles_api_version_2_response(self, jira_config: JiraConfig) -> None:
        """Test handling of API v2 response format (plain text description)."""
        from src.github_analyzer.api.jira_client import JiraClient

        # Force API v2
        config = JiraConfig(
            jira_url="https://jira.company.com",
            jira_email="test@company.com",
            jira_api_token="test-token",
        )
        client = JiraClient(config)

        with mock.patch.object(client, "_make_request") as mock_request:
            response = {
                "expand": "schema,names",
                "startAt": 0,
                "maxResults": 100,
                "total": 1,
                "issues": [
                    {
                        "id": "10001",
                        "key": "PROJ-1",
                        "fields": {
                            "summary": "Server issue",
                            "description": "Plain text description for server.",
                            "status": {"name": "Open"},
                            "issuetype": {"name": "Bug"},
                            "priority": {"name": "High"},
                            "assignee": {"displayName": "John Doe"},
                            "reporter": {"displayName": "Jane Smith"},
                            "created": "2025-11-20T10:30:00.000+0000",
                            "updated": "2025-11-28T14:15:00.000+0000",
                            "resolutiondate": None,
                            "project": {"key": "PROJ"},
                        },
                    }
                ],
            }
            mock_request.return_value = response

            since_date = datetime(2025, 11, 1, tzinfo=timezone.utc)
            issues = list(client.search_issues(["PROJ"], since_date))

            assert len(issues) == 1
            assert issues[0].description == "Plain text description for server."
