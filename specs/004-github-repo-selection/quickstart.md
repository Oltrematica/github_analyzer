# Quickstart: GitHub Repository Interactive Selection

**Feature**: 004-github-repo-selection
**Date**: 2025-11-29

## Overview

This feature adds interactive repository selection when `repos.txt` is missing or empty. Users can:
- Analyze all personal repositories
- Specify repositories manually
- Select from an organization's repositories
- Pick from a numbered list of their repositories

## Usage Examples

### Scenario 1: No repos.txt, Interactive Selection

```bash
# Ensure repos.txt doesn't exist
rm -f repos.txt

# Run with GitHub source (will trigger interactive menu)
python github_analyzer.py --sources github

# Output:
# repos.txt not found or empty.
# Found 23 accessible repositories:
#   1. myuser/project-alpha      - Alpha project description
#   2. myuser/project-beta       - [private] Beta project
#   3. otheruser/collab-repo     - Collaborative work
#   ...
#
# Options:
#   [A] Analyze ALL accessible repositories
#   [S] Specify repository names manually (owner/repo format)
#   [O] Analyze organization repositories
#   [L] Select from list by number (e.g., 1,3,5 or 1-3)
#   [Q] Quit/Skip GitHub analysis
#
# Your choice [A/S/O/L/Q]:
```

### Scenario 2: Select All Personal Repos

```bash
# At the prompt:
Your choice [A/S/O/L/Q]: A

# Output:
# Using all 23 repositories.
# Starting GitHub analysis...
```

### Scenario 3: Manual Specification

```bash
# At the prompt:
Your choice [A/S/O/L/Q]: S
Enter repository names (comma-separated, owner/repo format): myuser/project-alpha, otherorg/public-repo

# Output:
# Selected 2 repositories: myuser/project-alpha, otherorg/public-repo
# Starting GitHub analysis...
```

### Scenario 4: Organization Repositories

```bash
# At the prompt:
Your choice [A/S/O/L/Q]: O
Enter organization name: mycompany

# Output:
# Found 47 repositories in 'mycompany':
#   1. mycompany/backend-api     - Main backend service
#   2. mycompany/frontend-app    - React frontend
#   ...
#
# Select repositories (e.g., 1,3,5 or 1-3 or 'all'): 1-5

# Output:
# Selected 5 repositories.
# Starting GitHub analysis...
```

### Scenario 5: Select from Numbered List

```bash
# At the prompt:
Your choice [A/S/O/L/Q]: L
Enter selection (e.g., 1,3,5 or 1-3 or 'all'): 1,3,7-10

# Output:
# Selected 7 repositories: ...
# Starting GitHub analysis...
```

### Scenario 6: Non-Interactive Mode (--quiet)

```bash
# With --quiet flag and no repos.txt
python github_analyzer.py --sources github --quiet

# Output:
# No repos.txt found. Skipping GitHub analysis in non-interactive mode.
```

### Scenario 7: Using repos.txt (Existing Behavior)

```bash
# Create repos.txt
echo "myuser/project-alpha" > repos.txt
echo "myuser/project-beta" >> repos.txt

# Run analyzer - no interactive prompt
python github_analyzer.py --sources github

# Output:
# Loading repositories from repos.txt...
# Found 2 repositories.
# Starting GitHub analysis...
```

## Error Handling

### Invalid Organization Name

```bash
Your choice [A/S/O/L/Q]: O
Enter organization name: --invalid--

# Output:
# Invalid organization name format. Names must be alphanumeric with hyphens, 1-39 chars.
# Enter organization name:
```

### Organization Not Found

```bash
Your choice [A/S/O/L/Q]: O
Enter organization name: nonexistent-org-xyz

# Output:
# Could not access organization 'nonexistent-org-xyz'. Check the name and your permissions.
# Enter organization name (or 'Q' to go back):
```

### Invalid Repository Format

```bash
Your choice [A/S/O/L/Q]: S
Enter repository names (comma-separated, owner/repo format): just-a-repo, valid/repo

# Output:
# Warning: Invalid format ignored: just-a-repo (must be owner/repo)
# Selected 1 repository: valid/repo
```

### Rate Limit

```bash
# If rate limited during repository listing:
# Output:
# GitHub API rate limit exceeded. Waiting 45 seconds...
# (Progress indicator)
# Resuming...
```

### Ctrl+C / EOF

```bash
# At any prompt, pressing Ctrl+C or Ctrl+D:
# Output:
# GitHub analysis skipped.
```

## Testing Quick Check

```bash
# Run unit tests for new functionality
pytest tests/unit/api/test_github_client.py -v -k "list_user_repos or list_org_repos"

# Run integration tests for interactive selection
pytest tests/integration/test_interactive_selection.py -v -k "github"
```
