# Data Model: GitHub Repository Interactive Selection

**Feature**: 004-github-repo-selection
**Date**: 2025-11-29

## Entities

### GitHubRepository (Response Model)

Represents a repository returned from GitHub API.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `full_name` | `str` | Repository identifier (owner/repo) | `full_name` from API |
| `name` | `str` | Repository name | `name` from API |
| `owner` | `str` | Owner login | `owner.login` from API |
| `description` | `str \| None` | Repository description | `description` from API |
| `private` | `bool` | Private visibility | `private` from API |
| `fork` | `bool` | Is a fork | `fork` from API |

**Usage**: Display in interactive list, validate user selection.

### RepositorySelection (Internal State)

Represents user's repository selection mode.

| Value | Description | Action |
|-------|-------------|--------|
| `ALL_PERSONAL` | User chose [A] | List all personal repos (owner+collaborator) |
| `MANUAL` | User chose [S] | Accept comma-separated input |
| `ORGANIZATION` | User chose [O] | Prompt for org name, list org repos |
| `FROM_LIST` | User chose [L] | Show numbered list, accept selection |
| `QUIT` | User chose [Q] | Skip GitHub analysis |

**Note**: This is a conceptual state, not necessarily a formal enum in implementation.

## Data Flow

```
┌─────────────────┐
│   repos.txt     │──exists──▶ Load and return repos
└─────────────────┘
        │
        │ missing/empty
        ▼
┌─────────────────┐
│ Interactive Menu│
│ [A/S/O/L/Q]     │
└─────────────────┘
        │
        ├──[A]──▶ GET /user/repos?affiliation=owner,collaborator
        │                 │
        │                 ▼
        │         ┌─────────────────┐
        │         │ GitHubRepository│ (list)
        │         └─────────────────┘
        │                 │
        │                 ▼
        │         Return [full_name, ...]
        │
        ├──[S]──▶ Parse "owner/repo, owner/repo2"
        │                 │
        │                 ▼
        │         Validate format
        │                 │
        │                 ▼
        │         Return validated repos
        │
        ├──[O]──▶ Prompt for org name
        │                 │
        │                 ▼
        │         Validate org format
        │                 │
        │                 ▼
        │         GET /orgs/{org}/repos?type=all
        │                 │
        │                 ▼
        │         ┌─────────────────┐
        │         │ GitHubRepository│ (list)
        │         └─────────────────┘
        │                 │
        │                 ▼
        │         Show list, accept selection
        │                 │
        │                 ▼
        │         Return [full_name, ...]
        │
        ├──[L]──▶ GET /user/repos?affiliation=owner,collaborator
        │                 │
        │                 ▼
        │         Show numbered list
        │                 │
        │                 ▼
        │         Parse "1,3,5" or "1-3" or "all"
        │                 │
        │                 ▼
        │         Return selected [full_name, ...]
        │
        └──[Q]──▶ Return []
```

## Validation Rules

### Repository Name Format (FR-011)

```
Pattern: ^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$
Examples:
  ✓ owner/repo
  ✓ my-org/my-repo
  ✓ user123/project_v2
  ✗ just-repo (missing owner)
  ✗ owner/ (missing repo)
  ✗ /repo (missing owner)
```

### Organization Name Format (Edge Case)

```
Pattern: ^[a-zA-Z0-9]([a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$
Rules:
  - 1-39 characters
  - Alphanumeric and hyphens only
  - Cannot start or end with hyphen
Examples:
  ✓ myorg
  ✓ my-organization
  ✗ -invalid-
  ✗ org--double
```

### Selection Input Format (FR-010)

```
Formats supported:
  - Single number: "3"
  - Comma-separated: "1,3,5"
  - Range: "1-3"
  - Mixed: "1,3-5,7"
  - All: "all"
```

## State Transitions

```
START
  │
  ▼
┌─────────┐    file exists    ┌─────────┐
│ Check   │──────────────────▶│ LOADED  │──▶ END (repos from file)
│ File    │                   └─────────┘
└─────────┘
  │ missing/empty
  ▼
┌─────────┐
│ PROMPT  │◄────────────────┐
└─────────┘                 │
  │                         │
  ├─[A]─▶ API call ─▶ END   │ invalid input
  ├─[S]─▶ Manual ────▶ END  │
  │       │                 │
  │       └──invalid───────►│
  ├─[O]─▶ Org prompt        │
  │       │                 │
  │       ├─valid org─▶ API │
  │       │            │    │
  │       │            └─▶ List ─▶ END
  │       └─invalid───────►─┘
  ├─[L]─▶ API call ─▶ List ─▶ END
  │                    │
  │                    └──invalid──►─┘
  └─[Q]─▶ END (empty list)

  EOF/Ctrl+C at any prompt ─▶ END (empty list)
```
