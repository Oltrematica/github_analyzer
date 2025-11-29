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

# Issue search response (first page) - new /search/jql format
ISSUE_SEARCH_RESPONSE_PAGE_1 = {
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
    "nextPageToken": "token123",
    "isLast": False,
}

# Issue search response (second page - last page) - new /search/jql format
ISSUE_SEARCH_RESPONSE_PAGE_2 = {
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
    "nextPageToken": None,
    "isLast": True,
}

# Empty search response - new /search/jql format
ISSUE_SEARCH_EMPTY_RESPONSE = {
    "issues": [],
    "nextPageToken": None,
    "isLast": True,
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


# =============================================================================
# Quality Metrics Test Fixtures (Feature 003)
# =============================================================================

# Issue with high quality description (has AC, headers, lists, long text)
ISSUE_HIGH_QUALITY = {
    "id": "10050",
    "key": "PROJ-50",
    "self": "https://company.atlassian.net/rest/api/3/issue/10050",
    "fields": {
        "summary": "Implement user authentication",
        "description": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 2},
                    "content": [{"type": "text", "text": "Description"}],
                },
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "As a user, I want to be able to log in to the application securely so that my data is protected. "
                            "This feature should support OAuth2 and traditional username/password authentication methods. "
                            "The implementation must follow security best practices including rate limiting and account lockout.",
                        }
                    ],
                },
                {
                    "type": "heading",
                    "attrs": {"level": 2},
                    "content": [{"type": "text", "text": "Acceptance Criteria"}],
                },
                {
                    "type": "bulletList",
                    "content": [
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {"type": "text", "text": "Given a valid username and password, When the user submits login, Then they are authenticated"}
                                    ],
                                }
                            ],
                        },
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {"type": "text", "text": "Given invalid credentials, When login attempted 5 times, Then account is locked"}
                                    ],
                                }
                            ],
                        },
                    ],
                },
            ],
        },
        "status": {"name": "Done", "id": "3"},
        "issuetype": {"name": "Story", "id": "2"},
        "priority": {"name": "High", "id": "2"},
        "assignee": {"displayName": "John Doe", "accountId": "123"},
        "reporter": {"displayName": "Jane Smith", "accountId": "456"},
        "created": "2025-11-01T09:00:00.000+0000",
        "updated": "2025-11-15T16:00:00.000+0000",
        "resolutiondate": "2025-11-15T16:00:00.000+0000",
        "project": {"key": "PROJ"},
    },
}

# Issue with poor quality description (short, no AC, no formatting)
ISSUE_LOW_QUALITY = {
    "id": "10051",
    "key": "PROJ-51",
    "self": "https://company.atlassian.net/rest/api/3/issue/10051",
    "fields": {
        "summary": "Fix bug",
        "description": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Something is broken."}],
                }
            ],
        },
        "status": {"name": "Open", "id": "1"},
        "issuetype": {"name": "Bug", "id": "1"},
        "priority": {"name": "Medium", "id": "3"},
        "assignee": None,
        "reporter": {"displayName": "Bob Wilson", "accountId": "789"},
        "created": "2025-11-20T10:00:00.000+0000",
        "updated": "2025-11-20T10:00:00.000+0000",
        "resolutiondate": None,
        "project": {"key": "PROJ"},
    },
}

# Issue with no description
ISSUE_NO_DESCRIPTION = {
    "id": "10052",
    "key": "PROJ-52",
    "self": "https://company.atlassian.net/rest/api/3/issue/10052",
    "fields": {
        "summary": "Quick task",
        "description": None,
        "status": {"name": "Done", "id": "3"},
        "issuetype": {"name": "Task", "id": "3"},
        "priority": {"name": "Low", "id": "4"},
        "assignee": {"displayName": "Alice Johnson", "accountId": "321"},
        "reporter": {"displayName": "John Doe", "accountId": "123"},
        "created": "2025-11-10T08:00:00.000+0000",
        "updated": "2025-11-10T17:00:00.000+0000",
        "resolutiondate": "2025-11-10T17:00:00.000+0000",
        "project": {"key": "PROJ"},
    },
}

# Issue resolved same day (created and resolved same calendar day)
ISSUE_SAME_DAY_RESOLVED = {
    "id": "10053",
    "key": "PROJ-53",
    "self": "https://company.atlassian.net/rest/api/3/issue/10053",
    "fields": {
        "summary": "Hot fix",
        "description": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Critical production issue that needs immediate attention."}],
                }
            ],
        },
        "status": {"name": "Done", "id": "3"},
        "issuetype": {"name": "Bug", "id": "1"},
        "priority": {"name": "Critical", "id": "1"},
        "assignee": {"displayName": "John Doe", "accountId": "123"},
        "reporter": {"displayName": "Support Team", "accountId": "support"},
        "created": "2025-11-25T09:00:00.000+0000",
        "updated": "2025-11-25T14:00:00.000+0000",
        "resolutiondate": "2025-11-25T14:00:00.000+0000",
        "project": {"key": "PROJ"},
    },
}

# Issue with long cycle time (14 days)
ISSUE_LONG_CYCLE_TIME = {
    "id": "10054",
    "key": "PROJ-54",
    "self": "https://company.atlassian.net/rest/api/3/issue/10054",
    "fields": {
        "summary": "Complex refactoring",
        "description": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Major refactoring of the authentication module."}],
                }
            ],
        },
        "status": {"name": "Done", "id": "3"},
        "issuetype": {"name": "Story", "id": "2"},
        "priority": {"name": "Medium", "id": "3"},
        "assignee": {"displayName": "Jane Smith", "accountId": "456"},
        "reporter": {"displayName": "Product Manager", "accountId": "pm"},
        "created": "2025-11-01T10:00:00.000+0000",
        "updated": "2025-11-15T10:00:00.000+0000",
        "resolutiondate": "2025-11-15T10:00:00.000+0000",
        "project": {"key": "PROJ"},
    },
}

# Issue still open (for aging calculation)
ISSUE_OPEN_AGING = {
    "id": "10055",
    "key": "PROJ-55",
    "self": "https://company.atlassian.net/rest/api/3/issue/10055",
    "fields": {
        "summary": "Ongoing investigation",
        "description": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Investigating intermittent performance issues."}],
                }
            ],
        },
        "status": {"name": "In Progress", "id": "2"},
        "issuetype": {"name": "Task", "id": "3"},
        "priority": {"name": "High", "id": "2"},
        "assignee": {"displayName": "Bob Wilson", "accountId": "789"},
        "reporter": {"displayName": "Operations", "accountId": "ops"},
        "created": "2025-11-01T09:00:00.000+0000",  # Old issue for aging test
        "updated": "2025-11-28T09:00:00.000+0000",
        "resolutiondate": None,
        "project": {"key": "PROJ"},
    },
}

# Comments for testing cross-team score (multiple authors)
COMMENTS_MULTIPLE_AUTHORS = {
    "startAt": 0,
    "maxResults": 50,
    "total": 5,
    "comments": [
        {
            "id": "20001",
            "author": {"displayName": "John Doe", "accountId": "123"},
            "body": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Started working on this."}]}]},
            "created": "2025-11-02T10:00:00.000+0000",
            "updated": "2025-11-02T10:00:00.000+0000",
        },
        {
            "id": "20002",
            "author": {"displayName": "Jane Smith", "accountId": "456"},
            "body": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Code review feedback."}]}]},
            "created": "2025-11-03T14:00:00.000+0000",
            "updated": "2025-11-03T14:00:00.000+0000",
        },
        {
            "id": "20003",
            "author": {"displayName": "Bob Wilson", "accountId": "789"},
            "body": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "QA tested, all good."}]}]},
            "created": "2025-11-04T09:00:00.000+0000",
            "updated": "2025-11-04T09:00:00.000+0000",
        },
        {
            "id": "20004",
            "author": {"displayName": "Alice Johnson", "accountId": "321"},
            "body": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Security review complete."}]}]},
            "created": "2025-11-05T11:00:00.000+0000",
            "updated": "2025-11-05T11:00:00.000+0000",
        },
        {
            "id": "20005",
            "author": {"displayName": "John Doe", "accountId": "123"},  # Same author as first
            "body": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Merged to main."}]}]},
            "created": "2025-11-06T16:00:00.000+0000",
            "updated": "2025-11-06T16:00:00.000+0000",
        },
    ],
}

# Comments with single author (low cross-team score)
COMMENTS_SINGLE_AUTHOR = {
    "startAt": 0,
    "maxResults": 50,
    "total": 2,
    "comments": [
        {
            "id": "20010",
            "author": {"displayName": "John Doe", "accountId": "123"},
            "body": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Working on it."}]}]},
            "created": "2025-11-02T10:00:00.000+0000",
            "updated": "2025-11-02T10:00:00.000+0000",
        },
        {
            "id": "20011",
            "author": {"displayName": "John Doe", "accountId": "123"},
            "body": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Done."}]}]},
            "created": "2025-11-03T14:00:00.000+0000",
            "updated": "2025-11-03T14:00:00.000+0000",
        },
    ],
}

# Changelog response for reopen detection (FR-022)
CHANGELOG_WITH_REOPEN = {
    "startAt": 0,
    "maxResults": 100,
    "total": 4,
    "values": [
        {
            "id": "30001",
            "author": {"displayName": "John Doe", "accountId": "123"},
            "created": "2025-11-01T10:00:00.000+0000",
            "items": [
                {"field": "status", "fieldtype": "jira", "from": "1", "fromString": "Open", "to": "2", "toString": "In Progress"}
            ],
        },
        {
            "id": "30002",
            "author": {"displayName": "John Doe", "accountId": "123"},
            "created": "2025-11-05T16:00:00.000+0000",
            "items": [
                {"field": "status", "fieldtype": "jira", "from": "2", "fromString": "In Progress", "to": "3", "toString": "Done"}
            ],
        },
        {
            "id": "30003",
            "author": {"displayName": "QA Team", "accountId": "qa"},
            "created": "2025-11-06T09:00:00.000+0000",
            "items": [
                {"field": "status", "fieldtype": "jira", "from": "3", "fromString": "Done", "to": "2", "toString": "In Progress"}  # REOPEN
            ],
        },
        {
            "id": "30004",
            "author": {"displayName": "John Doe", "accountId": "123"},
            "created": "2025-11-07T14:00:00.000+0000",
            "items": [
                {"field": "status", "fieldtype": "jira", "from": "2", "fromString": "In Progress", "to": "3", "toString": "Done"}
            ],
        },
    ],
}

# Changelog without reopens
CHANGELOG_NO_REOPEN = {
    "startAt": 0,
    "maxResults": 100,
    "total": 2,
    "values": [
        {
            "id": "30010",
            "author": {"displayName": "Alice Johnson", "accountId": "321"},
            "created": "2025-11-10T10:00:00.000+0000",
            "items": [
                {"field": "status", "fieldtype": "jira", "from": "1", "fromString": "Open", "to": "2", "toString": "In Progress"}
            ],
        },
        {
            "id": "30011",
            "author": {"displayName": "Alice Johnson", "accountId": "321"},
            "created": "2025-11-10T17:00:00.000+0000",
            "items": [
                {"field": "status", "fieldtype": "jira", "from": "2", "fromString": "In Progress", "to": "3", "toString": "Done"}
            ],
        },
    ],
}

# Empty changelog
CHANGELOG_EMPTY = {
    "startAt": 0,
    "maxResults": 100,
    "total": 0,
    "values": [],
}

# Description with checkbox-style AC
DESCRIPTION_WITH_CHECKBOX_AC = """
## User Story
As a developer, I want to implement the login feature.

## Acceptance Criteria
- [ ] User can enter username
- [x] User can enter password
- [ ] Login button is enabled when both fields have values
"""

# Description with Given/When/Then AC
DESCRIPTION_WITH_GWT_AC = """
Feature: User Authentication

Given a registered user
When they enter valid credentials
Then they should be logged in successfully

Given an unregistered user
When they try to login
Then they should see an error message
"""

# Set of sample issues for aggregation testing
ISSUES_FOR_AGGREGATION = [
    ISSUE_HIGH_QUALITY,
    ISSUE_LOW_QUALITY,
    ISSUE_NO_DESCRIPTION,
    ISSUE_SAME_DAY_RESOLVED,
    ISSUE_LONG_CYCLE_TIME,
    ISSUE_OPEN_AGING,
]
