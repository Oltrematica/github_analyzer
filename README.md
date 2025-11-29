# DevAnalyzer (GitHub Analyzer)

[![Tests](https://github.com/Oltrematica/github_analyzer/actions/workflows/tests.yml/badge.svg)](https://github.com/Oltrematica/github_analyzer/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/Oltrematica/github_analyzer/branch/main/graph/badge.svg)](https://codecov.io/gh/Oltrematica/github_analyzer)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful Python command-line tool for analyzing GitHub repositories and Jira projects, extracting comprehensive metrics about commits, pull requests, issues, and contributor activity. Generate detailed CSV reports for productivity analysis and code quality assessment.

![GitHub Analyzer Banner](screens/screen1.png)

## Features

### GitHub Analysis
- **Commit Analysis** - Track commits with detailed statistics including additions, deletions, merge detection, and revert identification
- **Pull Request Metrics** - Monitor PR workflow, merge times, review coverage, and approval rates
- **Issue Tracking** - Analyze issue resolution times, categorization (bugs vs enhancements), and closure rates
- **Contributor Insights** - Identify top contributors with activity metrics and productivity scoring
- **Multi-Repository Support** - Analyze multiple repositories in a single run with aggregated statistics
- **Quality Metrics** - Assess code quality through revert ratios, review coverage, and commit message analysis
- **Productivity Scoring** - Calculate composite productivity scores for contributors across repositories

### Jira Integration
- **Jira Issue Extraction** - Extract issues and comments from Jira Cloud and Server/Data Center
- **Quality Metrics** - Calculate 10 quality metrics per issue including cycle time, description quality, collaboration scores
- **Aggregated Reports** - Generate project-level, person-level, and issue-type summaries
- **Multi-Project Support** - Analyze multiple Jira projects with interactive project selection
- **Time-Based Filtering** - Filter issues by update date using JQL queries
- **Comment Tracking** - Export all issue comments with author and timestamp
- **Reopen Tracking** - Detect reopened issues via changelog API (best-effort, graceful degradation)
- **ADF Support** - Automatically converts Atlassian Document Format to plain text

### Core Features
- **Multi-Source CLI** - Use `--sources` flag to select GitHub, Jira, or both
- **Auto-Detection** - Automatically detects available sources from environment credentials
- **Zero Dependencies** - Works with Python standard library only (optional `requests` for better performance)
- **Secure Token Handling** - Tokens loaded from environment variables, never exposed in logs or error messages

## Requirements

- **Python 3.9+**
- **GitHub Personal Access Token** with `repo` scope

## Installation

```bash
# Clone or download the project
git clone <repository-url>
cd github_analyzer

# (Optional) Install development dependencies
pip install -r requirements-dev.txt

# (Optional) Install requests for better performance
pip install requests
```

No additional packages are required. The tool uses Python's standard library and falls back gracefully if `requests` is not installed.

## Quick Start

### 1. Get a GitHub Token

- Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
- Generate a new token with `repo` scope
- Copy the token

### 2. Set the Token

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

### 3. Create repos.txt

```bash
echo "facebook/react" > repos.txt
echo "microsoft/vscode" >> repos.txt
```

### 4. Run the Analyzer

```bash
# Analyze last 30 days (default)
python3 github_analyzer.py

# Analyze last 7 days
python3 github_analyzer.py --days 7

# Short form
python3 github_analyzer.py -d 7
```

### 5. View Results

CSV files are generated in the `github_export/` directory.

## Command Line Options

```
usage: github_analyzer.py [-h] [--days DAYS] [--output OUTPUT] [--repos REPOS] [--quiet]

Analyze GitHub repositories and export metrics to CSV.

optional arguments:
  -h, --help            show this help message and exit
  --days DAYS, -d DAYS  Number of days to analyze (default: 30)
  --output OUTPUT, -o OUTPUT
                        Output directory for CSV files (default: github_export)
  --repos REPOS, -r REPOS
                        Path to repos.txt file (default: repos.txt)
  --quiet, -q           Suppress verbose output
```

### Examples

```bash
# Analyze last 7 days
python3 github_analyzer.py --days 7

# Analyze with custom output directory
python3 github_analyzer.py -d 14 -o ./reports

# Use different repos file
python3 github_analyzer.py -r my_repos.txt -d 30

# Quiet mode (minimal output)
python3 github_analyzer.py -d 7 -q
```

### Analysis in Progress

The tool shows real-time progress with detailed information for each repository:

![Analysis Progress](screens/screen2.png)

## Configuration

### Environment Variables

**GitHub Configuration:**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_TOKEN` | **Yes*** | - | GitHub Personal Access Token |
| `GITHUB_ANALYZER_DAYS` | No | 30 | Number of days to analyze |
| `GITHUB_ANALYZER_OUTPUT_DIR` | No | `github_export` | Output directory for CSV files |
| `GITHUB_ANALYZER_REPOS_FILE` | No | `repos.txt` | Repository list file |
| `GITHUB_ANALYZER_VERBOSE` | No | `true` | Enable detailed logging |

**Jira Configuration:**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JIRA_URL` | **Yes*** | - | Jira instance URL (e.g., `https://company.atlassian.net`) |
| `JIRA_EMAIL` | **Yes*** | - | Jira account email |
| `JIRA_API_TOKEN` | **Yes*** | - | Jira API token |

*Required only if using that source. Auto-detection skips sources without credentials.

### How to Generate a Jira API Token

**For Jira Cloud (Atlassian Cloud):**
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click **"Create API token"**
3. Give it a descriptive name (e.g., "dev-analyzer")
4. Click **"Create"** and copy the token immediately (shown only once!)

**For Jira Server / Data Center:**
1. Go to **Profile** → **Personal Access Tokens**
2. Click **"Create token"**
3. Select appropriate permissions and create
4. Copy the generated token

**Note:** CLI arguments override environment variables.

### repos.txt Format

```txt
# Add repositories to analyze (one per line)
# Format: owner/repo or full GitHub URL

facebook/react
microsoft/vscode
https://github.com/kubernetes/kubernetes
astral-sh/ruff

# Lines starting with # are comments
# Empty lines are ignored
# Duplicates are automatically removed
```

### jira_projects.txt Format

```txt
# Add Jira project keys to analyze (one per line)
# Project keys are case-sensitive (usually uppercase)

PROJ
DEV
OPS

# Lines starting with # are comments
# Empty lines are ignored
# Duplicates are automatically removed
```

If this file is missing, the tool will prompt you interactively to select from available projects.

## Output Files

The analyzer generates CSV files in the output directory. GitHub outputs are always generated when analyzing GitHub, and Jira outputs when analyzing Jira:

**GitHub outputs (7 files):**

![Analysis Summary](screens/screen3.png)

| File | Description |
|------|-------------|
| `commits_export.csv` | All commits with author, date, changes, merge/revert status |
| `pull_requests_export.csv` | PRs with state, merge status, review metrics, time-to-merge |
| `issues_export.csv` | Issues with state, labels, assignees, time-to-close |
| `repository_summary.csv` | Per-repository aggregate statistics |
| `quality_metrics.csv` | Code quality scores and metrics per repository |
| `productivity_analysis.csv` | Per-contributor productivity metrics and scores |
| `contributors_summary.csv` | Contributor overview with commit and PR statistics |

**Jira outputs (5 files):**

| File | Description |
|------|-------------|
| `jira_issues_export.csv` | Jira issues with 12 base fields + 10 quality metrics per issue |
| `jira_comments_export.csv` | Jira issue comments with issue key, author, date, body |
| `jira_project_metrics.csv` | Aggregated metrics per project (cycle time, bug ratio, quality scores) |
| `jira_person_metrics.csv` | Per-assignee metrics (WIP count, resolved count, avg cycle time) |
| `jira_type_metrics.csv` | Per-issue-type metrics (counts, avg cycle time, bug resolution time) |

### CSV Field Details

#### commits_export.csv
```
repository, sha, short_sha, author_login, author_email, committer_login,
date, message, additions, deletions, total_changes, files_changed,
is_merge_commit, is_revert, file_types, url
```

#### pull_requests_export.csv
```
repository, number, title, state, author_login, created_at, updated_at,
closed_at, merged_at, is_merged, is_draft, time_to_merge_hours,
reviewers_count, approvals, changes_requested, url
```

#### issues_export.csv
```
repository, number, title, state, author_login, created_at, closed_at,
labels, assignees, comments_count, time_to_close_hours, is_bug,
is_enhancement, url
```

#### quality_metrics.csv
```
repository, revert_ratio_pct, avg_commit_size, large_commits_pct,
pr_review_coverage_pct, approval_rate_pct, change_request_rate_pct,
draft_prs_pct, conventional_commits_pct, quality_score
```

#### productivity_analysis.csv
```
contributor, repositories_count, total_commits, total_additions,
total_deletions, prs_opened, prs_merged, prs_reviewed, merge_rate_pct,
first_activity, last_activity, active_days, consistency_pct,
productivity_score
```

#### jira_issues_export.csv
```
key, summary, description, status, issue_type, priority, assignee, reporter,
created, updated, resolution_date, project_key,
cycle_time_days, aging_days, comments_count, description_quality_score,
acceptance_criteria_present, comment_velocity_hours, silent_issue,
same_day_resolution, cross_team_score, reopen_count
```

#### jira_project_metrics.csv
```
project_key, total_issues, resolved_count, unresolved_count,
avg_cycle_time_days, median_cycle_time_days, bug_count, bug_ratio_percent,
same_day_resolution_rate_percent, avg_description_quality,
silent_issues_ratio_percent, avg_comments_per_issue,
avg_comment_velocity_hours, reopen_rate_percent
```

#### jira_person_metrics.csv
```
assignee_name, wip_count, resolved_count, total_assigned,
avg_cycle_time_days, bug_count_assigned
```

#### jira_type_metrics.csv
```
issue_type, count, resolved_count, avg_cycle_time_days,
bug_resolution_time_avg
```

## Jira Quality Metrics Explained

The analyzer calculates 10 quality metrics for each Jira issue:

| Metric | Description | Value |
|--------|-------------|-------|
| **cycle_time_days** | Days from created to resolution | Float (empty if open) |
| **aging_days** | Days since creation for open issues | Float (empty if resolved) |
| **comments_count** | Total number of comments | Integer |
| **description_quality_score** | Quality score based on length, AC, formatting | 0-100 |
| **acceptance_criteria_present** | AC patterns detected (Given/When/Then, checkboxes) | true/false |
| **comment_velocity_hours** | Hours from creation to first comment | Float (empty if silent) |
| **silent_issue** | No comments exist | true/false |
| **same_day_resolution** | Resolved on same day as created | true/false |
| **cross_team_score** | Collaboration score based on distinct commenters | 0-100 |
| **reopen_count** | Times reopened (Done→non-Done transitions) | Integer |

### Description Quality Score Calculation

The quality score (0-100) uses balanced weighting:

| Component | Weight | Criteria |
|-----------|--------|----------|
| **Length** | 40% | Linear scale: 100+ chars = full score |
| **Acceptance Criteria** | 40% | Detected patterns: Given/When/Then, AC:, checkboxes |
| **Formatting** | 20% | Headers (10%) + Lists (10%) detected |

### Cross-Team Collaboration Score

Based on distinct comment authors:

| Authors | Score |
|---------|-------|
| 0 | 0 |
| 1 | 25 |
| 2 | 50 |
| 3 | 75 |
| 4 | 90 |
| 5+ | 100 |

## GitHub Quality Metrics Explained

The analyzer calculates several quality indicators for GitHub repositories:

| Metric | Description | Ideal |
|--------|-------------|-------|
| **Revert Ratio** | Percentage of commits that are reverts | < 5% |
| **Avg Commit Size** | Average lines changed per commit | 50-200 |
| **Large Commits** | Commits with >500 lines changed | < 10% |
| **Review Coverage** | PRs that received at least one review | > 80% |
| **Approval Rate** | PRs approved before merge | > 90% |
| **Conventional Commits** | Commits following conventional format | > 50% |
| **Quality Score** | Weighted composite score (0-100) | > 70 |

## Productivity Scoring

Contributor productivity is measured by:

- **Total Commits** - Number of commits across analyzed repositories
- **PRs Merged** - Successfully merged pull requests
- **Merge Rate** - Percentage of opened PRs that got merged
- **Active Days** - Days with at least one contribution
- **Consistency** - Regularity of contributions over the period
- **Productivity Score** - Weighted composite score

## Project Structure

```
github_analyzer/
├── github_analyzer.py          # Backward-compatible entry point
├── repos.txt                   # Repository configuration file
├── requirements.txt            # Optional dependencies (requests)
├── requirements-dev.txt        # Development dependencies (pytest, ruff)
├── pyproject.toml              # Project configuration
├── pytest.ini                  # Test configuration
├── src/
│   └── github_analyzer/        # Main package
│       ├── __init__.py         # Package exports
│       ├── api/                # GitHub API client
│       │   ├── client.py       # HTTP client with retry logic
│       │   └── models.py       # Data models (Commit, PR, Issue, etc.)
│       ├── analyzers/          # Data analysis logic
│       │   ├── commits.py      # Commit analysis
│       │   ├── pull_requests.py# PR analysis
│       │   ├── issues.py       # Issue analysis
│       │   ├── quality.py      # Quality metrics calculation
│       │   └── productivity.py # Contributor tracking
│       ├── exporters/          # CSV export functionality
│       │   └── csv_exporter.py # Export to CSV files
│       ├── cli/                # Command-line interface
│       │   ├── main.py         # Entry point and orchestrator
│       │   └── output.py       # Terminal formatting
│       ├── config/             # Configuration management
│       │   ├── settings.py     # AnalyzerConfig dataclass
│       │   └── validation.py   # Repository validation
│       └── core/               # Shared utilities
│           └── exceptions.py   # Custom exception hierarchy
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   │   └── config/             # Config tests
│   ├── integration/            # Integration tests
│   └── fixtures/               # Test fixtures
└── github_export/              # Output directory for CSV files
```

## API Rate Limits

The tool monitors GitHub API rate limits:
- **Authenticated requests**: 5,000 per hour
- **Pagination**: Up to 50 pages per endpoint
- **Timeout**: 30 seconds per request
- **Retry**: Exponential backoff for transient failures

Rate limit status is tracked automatically.

## Error Handling

The analyzer gracefully handles:
- Missing or invalid GitHub tokens
- Rate limit exceeded (HTTP 403)
- Repository not found (HTTP 404)
- Network timeouts
- Malformed repository URLs
- Empty repository lists
- Invalid input with dangerous characters (injection protection)

## Testing

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src/github_analyzer

# Run linter
ruff check src/github_analyzer/
```

## Use Cases

1. **Team Performance Reviews** - Generate productivity reports for sprint retrospectives
2. **Code Quality Audits** - Assess review practices and commit quality across repositories
3. **Open Source Analysis** - Analyze contributor patterns in open source projects
4. **Repository Health Checks** - Monitor issue resolution and PR merge velocity
5. **Trend Analysis** - Compare metrics over different time periods
6. **Multi-Team Reporting** - Aggregate metrics across organizational repositories

## Troubleshooting

### "GITHUB_TOKEN environment variable not set"
```bash
export GITHUB_TOKEN=ghp_your_token_here
```

### "Token validation failed"
- Ensure your token has `repo` scope
- Check if the token has expired
- Token must start with `ghp_`, `github_pat_`, `gho_`, or `ghs_`

### "Repository not found"
- Check the repository name format: `owner/repo`
- Verify you have access to private repositories with your token
- Ensure the repository exists

### "Rate limit exceeded"
- Wait for the rate limit to reset (usually 1 hour)
- Reduce the number of repositories analyzed at once
- Use a shorter analysis period with `--days`

### Empty CSV files
- Check if repositories have activity in the specified period
- Verify repository names in `repos.txt` are correct
- Ensure the token has read access to the repositories

### "JIRA_URL environment variable not set"
```bash
export JIRA_URL="https://yourcompany.atlassian.net"
export JIRA_EMAIL="your.email@company.com"
export JIRA_API_TOKEN="your-api-token"
```

### "Jira authentication failed"
- Verify your email matches your Jira account exactly
- Check that the API token is valid and not expired
- For Jira Cloud, ensure you're using the correct email (not username)
- For Jira Server/Data Center, verify the token has appropriate permissions

### "Jira project not found: PROJ"
- Project keys are case-sensitive (usually uppercase)
- Verify you have access to the project with your account
- Check the project key in Jira (visible in issue keys like PROJ-123)

### "Jira rate limit exceeded"
- The tool automatically retries with exponential backoff
- If persistent, wait a few minutes and retry
- Reduce the number of projects in `jira_projects.txt`
- Use a shorter analysis period with `--days`

### Jira skipped (no credentials)
- This is expected if you only have GitHub configured
- To use Jira, set all three required environment variables: `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`

### Empty Jira CSV files
- Check if projects have issues updated in the specified period
- Verify project keys in `jira_projects.txt` are correct
- Ensure your account has permission to view the projects

## Security

This project implements defense-in-depth security measures. See [SECURITY.md](SECURITY.md) for the full security analysis.

### Credential Management
- **Environment Variables Only**: All credentials (`GITHUB_TOKEN`, `JIRA_API_TOKEN`) loaded exclusively from environment variables
- **Token Masking**: Tokens are replaced with `[MASKED]` in all logs, errors, and representations
- **Token Format Validation**: GitHub tokens validated against known patterns (`ghp_`, `github_pat_`, `gho_`, `ghs_`)
- **No Persistence**: Credentials never written to disk or configuration files

### Input Validation
- **Whitelist Patterns**: Repository names and Jira project keys validated with strict regex patterns
- **Dangerous Character Rejection**: Shell metacharacters (`;|&$\`(){}[]<>`) explicitly blocked
- **Path Traversal Prevention**: `..` sequences rejected in all user inputs
- **URL Validation**: GitHub URLs normalized, Jira URLs require HTTPS
- **Length Limits**: Maximum 100 characters per component to prevent buffer attacks

### Network Security
- **HTTPS Enforced**: All API calls use HTTPS (HTTP rejected for Jira)
- **Timeout Protection**: Configurable timeouts (default 30s) prevent indefinite hangs
- **Rate Limit Handling**: Graceful handling with exponential backoff
- **Retry Logic**: Automatic retry for transient 5xx errors

### Output Security
- **CSV Formula Injection Protection**: Values starting with `=`, `+`, `-`, `@`, `TAB`, `CR` prefixed with single quote
- **Path Validation**: Output paths validated to stay within safe boundaries
- **Secure File Permissions**: Output files created with restricted permissions (owner read/write only)
- **Symlink Resolution**: All paths resolved to prevent symlink attacks

### Error Handling
- **No Secret Leakage**: Error messages never contain tokens or credentials
- **Response Truncation**: API error details truncated to 200 characters
- **Structured Exceptions**: Typed exceptions without exposing internals

### Minimal Dependencies
- **Zero Required Dependencies**: Core functionality uses Python standard library only
- **Optional `requests`**: Falls back gracefully to `urllib` if not installed

## Contributing

Contributions are welcome! Please read our **[Contributing Guide](CONTRIBUTING.md)** for detailed information on:

- Development setup and workflow
- Code style and testing requirements
- Commit message format (Conventional Commits)
- Pull request guidelines

**Quick start:**

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/github_analyzer.git
cd github_analyzer

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Run linter
ruff check src/github_analyzer/
```

We aim for **≥90% test coverage**. Open an issue for discussion before starting major changes.

## License

This project is provided as-is for educational and analytical purposes.

## Acknowledgments

- Built using the [GitHub REST API v3](https://docs.github.com/en/rest)
- Designed for cross-platform compatibility with Python standard library
