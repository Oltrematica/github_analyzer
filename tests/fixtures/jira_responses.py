"""Test fixtures for Jira API responses.

Provides sample API responses for testing JiraClient without network calls.
These fixtures mirror the actual Jira REST API v3 response format.
"""

from __future__ import annotations

# Server info response (used by test_connection)
SERVER_INFO_RESPONSE = {
    "baseUrl": "https://company.atlassian.net",
    "version": "1001.0.0-SNAPSHOT",
    "versionNumbers": [1001, 0, 0],
    "deploymentType": "Cloud",
    "buildNumber": 100250,
    "buildDate": "2025-11-01T00:00:00.000+0000",
    "serverTime": "2025-11-28T10:30:00.000+0000",
    "scmInfo": "abc123def456",
    "serverTitle": "Jira",
}

# Project list response
PROJECTS_RESPONSE = [
    {
        "id": "10000",
        "key": "PROJ",
        "name": "Main Project",
        "projectTypeKey": "software",
        "simplified": False,
        "style": "classic",
        "isPrivate": False,
        "description": "Main project for development",
    },
    {
        "id": "10001",
        "key": "DEV",
        "name": "Development",
        "projectTypeKey": "software",
        "simplified": False,
        "style": "classic",
        "isPrivate": False,
        "description": "",
    },
    {
        "id": "10002",
        "key": "SUPPORT",
        "name": "Customer Support",
        "projectTypeKey": "service_desk",
        "simplified": False,
        "style": "classic",
        "isPrivate": False,
        "description": "Support tickets",
    },
]

# Single project response
PROJECT_RESPONSE = {
    "id": "10000",
    "key": "PROJ",
    "name": "Main Project",
    "projectTypeKey": "software",
    "simplified": False,
    "style": "classic",
    "isPrivate": False,
    "description": "Main project for development",
}

# Issue search response (first page)
ISSUE_SEARCH_RESPONSE_PAGE_1 = {
    "expand": "schema,names",
    "startAt": 0,
    "maxResults": 100,
    "total": 150,
    "issues": [
        {
            "id": "10001",
            "key": "PROJ-1",
            "self": "https://company.atlassian.net/rest/api/3/issue/10001",
            "fields": {
                "summary": "First issue",
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": "This is the description text."}
                            ],
                        }
                    ],
                },
                "status": {"name": "Open", "id": "1"},
                "issuetype": {"name": "Bug", "id": "1"},
                "priority": {"name": "High", "id": "2"},
                "assignee": {"displayName": "John Doe", "accountId": "123"},
                "reporter": {"displayName": "Jane Smith", "accountId": "456"},
                "created": "2025-11-20T10:30:00.000+0000",
                "updated": "2025-11-28T14:15:00.000+0000",
                "resolutiondate": None,
                "project": {"key": "PROJ"},
            },
        },
        {
            "id": "10002",
            "key": "PROJ-2",
            "self": "https://company.atlassian.net/rest/api/3/issue/10002",
            "fields": {
                "summary": "Second issue - resolved",
                "description": None,
                "status": {"name": "Done", "id": "3"},
                "issuetype": {"name": "Story", "id": "2"},
                "priority": None,
                "assignee": None,
                "reporter": {"displayName": "Bob Wilson", "accountId": "789"},
                "created": "2025-11-15T09:00:00.000+0000",
                "updated": "2025-11-25T16:00:00.000+0000",
                "resolutiondate": "2025-11-25T16:00:00.000+0000",
                "project": {"key": "PROJ"},
            },
        },
    ],
}

# Issue search response (second page - last page)
ISSUE_SEARCH_RESPONSE_PAGE_2 = {
    "expand": "schema,names",
    "startAt": 100,
    "maxResults": 100,
    "total": 150,
    "issues": [
        {
            "id": "10101",
            "key": "PROJ-101",
            "self": "https://company.atlassian.net/rest/api/3/issue/10101",
            "fields": {
                "summary": "Issue on page 2",
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Description for page 2 issue."}],
                        }
                    ],
                },
                "status": {"name": "In Progress", "id": "2"},
                "issuetype": {"name": "Task", "id": "3"},
                "priority": {"name": "Medium", "id": "3"},
                "assignee": {"displayName": "Alice Johnson", "accountId": "321"},
                "reporter": {"displayName": "Jane Smith", "accountId": "456"},
                "created": "2025-11-22T11:00:00.000+0000",
                "updated": "2025-11-27T09:30:00.000+0000",
                "resolutiondate": None,
                "project": {"key": "PROJ"},
            },
        },
    ],
}

# Empty search response
ISSUE_SEARCH_EMPTY_RESPONSE = {
    "expand": "schema,names",
    "startAt": 0,
    "maxResults": 100,
    "total": 0,
    "issues": [],
}

# Comments response for an issue
COMMENTS_RESPONSE = {
    "startAt": 0,
    "maxResults": 50,
    "total": 2,
    "comments": [
        {
            "id": "10001",
            "self": "https://company.atlassian.net/rest/api/3/issue/10001/comment/10001",
            "author": {"displayName": "John Doe", "accountId": "123"},
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "This is a comment."}],
                    }
                ],
            },
            "created": "2025-11-21T09:00:00.000+0000",
            "updated": "2025-11-21T09:00:00.000+0000",
        },
        {
            "id": "10002",
            "self": "https://company.atlassian.net/rest/api/3/issue/10001/comment/10002",
            "author": {"displayName": "Jane Smith", "accountId": "456"},
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": "Reply to the comment."},
                            {"type": "text", "text": " With more text."},
                        ],
                    },
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Second paragraph."}],
                    },
                ],
            },
            "created": "2025-11-21T10:30:00.000+0000",
            "updated": "2025-11-21T10:30:00.000+0000",
        },
    ],
}

# Empty comments response
COMMENTS_EMPTY_RESPONSE = {
    "startAt": 0,
    "maxResults": 50,
    "total": 0,
    "comments": [],
}

# Error responses
ERROR_401_RESPONSE = {
    "errorMessages": ["You are not authenticated. Authentication required to perform this operation."],
    "errors": {},
}

ERROR_403_RESPONSE = {
    "errorMessages": ["You do not have permission to access this resource."],
    "errors": {},
}

ERROR_404_RESPONSE = {
    "errorMessages": ["The requested resource was not found."],
    "errors": {},
}

ERROR_429_RESPONSE = {
    "errorMessages": ["Rate limit exceeded. Please retry after some time."],
    "errors": {},
}

# ADF (Atlassian Document Format) complex example
ADF_COMPLEX_BODY = {
    "type": "doc",
    "version": 1,
    "content": [
        {
            "type": "paragraph",
            "content": [
                {"type": "text", "text": "This is "},
                {"type": "text", "text": "bold", "marks": [{"type": "strong"}]},
                {"type": "text", "text": " and "},
                {"type": "text", "text": "italic", "marks": [{"type": "em"}]},
                {"type": "text", "text": " text."},
            ],
        },
        {
            "type": "bulletList",
            "content": [
                {
                    "type": "listItem",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Item 1"}],
                        }
                    ],
                },
                {
                    "type": "listItem",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Item 2"}],
                        }
                    ],
                },
            ],
        },
        {
            "type": "codeBlock",
            "attrs": {"language": "python"},
            "content": [{"type": "text", "text": "print('hello')"}],
        },
    ],
}

# Plain text description (API v2 style)
PLAIN_TEXT_DESCRIPTION = "This is a plain text description.\n\nWith multiple paragraphs."

# Issue with plain text description (Server/Data Center API v2)
ISSUE_WITH_PLAIN_TEXT = {
    "id": "10001",
    "key": "PROJ-1",
    "self": "https://jira.company.com/rest/api/2/issue/10001",
    "fields": {
        "summary": "Server issue",
        "description": "Plain text description for server.",
        "status": {"name": "Open", "id": "1"},
        "issuetype": {"name": "Bug", "id": "1"},
        "priority": {"name": "High", "id": "2"},
        "assignee": {"displayName": "John Doe", "name": "jdoe"},
        "reporter": {"displayName": "Jane Smith", "name": "jsmith"},
        "created": "2025-11-20T10:30:00.000+0000",
        "updated": "2025-11-28T14:15:00.000+0000",
        "resolutiondate": None,
        "project": {"key": "PROJ"},
    },
}

# Rate limit headers
RATE_LIMIT_HEADERS = {
    "X-RateLimit-Limit": "1000",
    "X-RateLimit-Remaining": "0",
    "Retry-After": "60",
}
