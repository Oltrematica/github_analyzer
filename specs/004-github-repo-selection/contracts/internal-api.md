# Internal API Contract: GitHub Repository Selection

**Feature**: 004-github-repo-selection
**Date**: 2025-11-29

## New Methods in GitHubClient

### `list_user_repos(affiliation: str = "owner,collaborator") -> list[dict]`

Lists repositories for the authenticated user.

**Parameters**:
- `affiliation`: Comma-separated affiliations (default: "owner,collaborator" per spec)

**Returns**: List of repository dicts with at least `full_name`, `name`, `owner.login`, `description`, `private`, `fork`

**Raises**:
- `RateLimitError`: When API rate limit is exceeded
- `APIError`: On other API failures

**Implementation Notes**:
- Uses existing `paginate()` method for automatic pagination
- Respects existing `per_page` and `max_pages` config

---

### `list_org_repos(org: str) -> list[dict]`

Lists repositories for a specific organization.

**Parameters**:
- `org`: Organization name (validated by caller)

**Returns**: List of repository dicts (same structure as `list_user_repos`)

**Raises**:
- `RateLimitError`: When API rate limit is exceeded
- `APIError`: On API failures including 404 (org not found)

**Implementation Notes**:
- Uses `type=all` to include all accessible repos
- Uses existing `paginate()` method

---

## New Function in cli/main.py

### `select_github_repos(repos_file: str, config: AnalyzerConfig, interactive: bool = True, output: TerminalOutput | None = None) -> list[str]`

Select GitHub repositories from file or interactively.

**Parameters**:
- `repos_file`: Path to repos.txt file
- `config`: Analyzer configuration (contains GitHub token)
- `interactive`: If True, prompt user when file missing/empty. If False, return empty list.
- `output`: Optional TerminalOutput for consistent logging

**Returns**: List of repository names in `owner/repo` format

**Behavior**:
1. If `repos_file` exists and has content → return repos from file
2. If `repos_file` missing/empty and `interactive=False` → return `[]`
3. If `repos_file` missing/empty and `interactive=True` → show menu:
   - [A] All personal repos → call `list_user_repos()`, return all
   - [S] Specify manually → prompt, validate format, return valid repos
   - [O] Organization repos → prompt org, call `list_org_repos()`, show selection
   - [L] Select from list → call `list_user_repos()`, show numbered list, return selected
   - [Q] Quit → return `[]`
4. On EOF/KeyboardInterrupt → return `[]`

---

## Helper Functions

### `validate_repo_format(repo: str) -> bool`

Validates repository name format.

**Pattern**: `^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$`

**Returns**: True if valid `owner/repo` format

---

### `validate_org_name(org: str) -> bool`

Validates GitHub organization name format.

**Pattern**: `^[a-zA-Z0-9]([a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$`

**Returns**: True if valid org name format

---

### `format_repo_list(repos: list[dict]) -> str`

Formats repository list for display.

**Input**: List of repository dicts from API
**Output**: Numbered list string for display

**Format**:
```
  1. owner/repo1         - Description here (if any)
  2. owner/repo2         - Another description
  3. owner/private-repo  - [private] Private repo desc
```

---

## Integration Point in main()

```python
# In main(), before GitHub analysis:
repositories = select_github_repos(
    config.repos_file,
    config,
    interactive=not args.quiet,  # Non-interactive in quiet mode
    output=output,
)

if DataSource.GITHUB in sources and repositories:
    # ... existing analysis code
```
