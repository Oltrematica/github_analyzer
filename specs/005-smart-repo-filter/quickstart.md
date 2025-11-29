# Quickstart: Smart Repository Filtering

**Feature**: 005-smart-repo-filter
**Date**: 2025-11-29

## Overview

Smart Repository Filtering automatically shows activity statistics and filters repositories based on recent push activity. This helps you focus on actively maintained projects when analyzing large numbers of repositories.

## Basic Usage

### Automatic Filtering (Default)

When you select repositories via [A], [L], or [O] options, the system automatically shows activity statistics:

```bash
$ python github_analyzer.py --sources github --days 30

No repos.txt found. Please select repositories:

Options:
  [A] Analyze ALL accessible repositories
  [S] Specify repository names manually (owner/repo format)
  [O] Analyze organization repositories
  [L] Select from list by number (e.g., 1,3,5 or 1-3)
  [Q] Quit/Skip GitHub analysis

Your choice [A/S/O/L/Q]: A

Fetching repositories...
135 repos found, 28 with activity in last 30 days

Proceed with 28 active repositories? [Y/n/all]: Y
```

### View All Repositories

To include inactive repositories, respond with `all` at the prompt:

```
135 repos found, 28 with activity in last 30 days

Proceed with 28 active repositories? [Y/n/all]: all

Proceeding with all 135 repositories (including inactive)...
```

### Organization Repositories

For large organizations, filtering is especially useful:

```
Your choice [A/S/O/L/Q]: O
Enter organization name: microsoft

Searching for active repositories...
523 org repos found, 87 with activity in last 30 days

Proceed with 87 active repositories? [Y/n/all]: Y
```

## Command-Line Options

### Adjust Analysis Period

The `--days` parameter controls both the analysis period AND the activity filter:

```bash
# Last 7 days activity
$ python github_analyzer.py --sources github --days 7

# Last 90 days activity
$ python github_analyzer.py --sources github --days 90
```

### Skip Interactive Mode

Use `--quiet` to skip prompts (requires repos.txt):

```bash
$ python github_analyzer.py --sources github --quiet
```

## Manual Specification (No Filter)

Option [S] bypasses the activity filter - manual selection implies intentional choice:

```
Your choice [A/S/O/L/Q]: S
Enter repositories (comma-separated, owner/repo format):
facebook/react, torvalds/linux

Proceeding with 2 manually specified repositories...
```

## Edge Cases

### Zero Active Repositories

If no repositories have activity in the period:

```
135 repos found, 0 with activity in last 7 days

⚠️  No repositories have been pushed to in the last 7 days.
Options:
  [1] Include all 135 repositories anyway
  [2] Adjust timeframe (currently 7 days)
  [3] Cancel

Your choice: 2
Enter new timeframe in days: 30

Rechecking...
135 repos found, 28 with activity in last 30 days
```

### Rate Limit Handling

If the Search API rate limit is exceeded:

```
Searching for active repositories...
⚠️  Search API rate limit exceeded. Showing all repositories without activity filter.
    Try again in 45 seconds for filtered results.

523 org repos found (activity filter unavailable)
Proceed with all 523 repositories? [Y/n]:
```

### Large Organizations (500+ repos)

For very large organizations, search is paginated automatically:

```
Searching for active repositories...
Fetching page 1 of active repos...
Fetching page 2 of active repos...

1247 org repos, 156 with activity in last 30 days
```

## Configuration Summary

| Setting | Source | Description |
|---------|--------|-------------|
| Activity period | `--days` | Days to look back for activity |
| Filter enabled | Default ON | Automatic for [A], [L], [O] options |
| Filter disabled | User choice | Select "all" or use [S] option |

## Verification Steps

After implementation, verify these scenarios work:

1. **US1**: Select [A] or [L], see activity statistics displayed
2. **US2**: Select [O], enter org name, see org-specific stats
3. **US3**: Select [S], enter repos manually, no filter applied
4. **Edge**: Test with `--days 1` on inactive repos, see zero-result handling
5. **Edge**: Rate limit (mock test), see fallback to unfiltered mode
