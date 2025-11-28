# GitHub Analyzer

A powerful Python command-line tool for analyzing GitHub repositories and extracting comprehensive metrics about commits, pull requests, issues, and contributor activity. Generate detailed CSV reports for productivity analysis and code quality assessment.

## Features

- **Commit Analysis** - Track commits with detailed statistics including additions, deletions, merge detection, and revert identification
- **Pull Request Metrics** - Monitor PR workflow, merge times, review coverage, and approval rates
- **Issue Tracking** - Analyze issue resolution times, categorization (bugs vs enhancements), and closure rates
- **Contributor Insights** - Identify top contributors with activity metrics and productivity scoring
- **Multi-Repository Support** - Analyze multiple repositories in a single run with aggregated statistics
- **Quality Metrics** - Assess code quality through revert ratios, review coverage, and commit message analysis
- **Productivity Scoring** - Calculate composite productivity scores for contributors across repositories
- **Zero Dependencies** - Works with Python standard library only (optional `requests` for better performance)

## Requirements

- **Python 3.9.6+**
- **GitHub Personal Access Token** with `repo` scope

## Installation

```bash
# Clone or download the project
git clone <repository-url>
cd github_analyzer

# Make the script executable (optional)
chmod +x github_analyzer.py

# Run the analyzer
python3 github_analyzer.py
```

No additional packages are required. The tool uses Python's standard library and falls back gracefully if `requests` is not installed.

## Quick Start

1. **Get a GitHub Token**
   - Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
   - Generate a new token with `repo` scope
   - Copy the token

2. **Run the Analyzer**
   ```bash
   python3 github_analyzer.py
   ```

3. **Follow the Interactive Prompts**
   - Paste your GitHub token
   - Edit `repos.txt` with repositories to analyze
   - Specify the analysis period (default: 30 days)
   - Confirm and start the analysis

4. **View Results**
   - CSV files are generated in the `github_export/` directory
   - Summary statistics are displayed in the terminal

## Configuration

### repos.txt

Create or edit the `repos.txt` file to specify which repositories to analyze:

```txt
# Add repositories to analyze (one per line)
# Format: owner/repo or full GitHub URL

facebook/react
microsoft/vscode
https://github.com/kubernetes/kubernetes

# Lines starting with # are comments
```

### Default Settings

| Setting | Default Value | Description |
|---------|---------------|-------------|
| `DEFAULT_DAYS` | 30 | Number of days to analyze |
| `DEFAULT_OUTPUT_DIR` | `github_export` | Output directory for CSV files |
| `DEFAULT_REPOS_FILE` | `repos.txt` | Repository list file |
| `PER_PAGE` | 100 | Items per API page |
| `VERBOSE` | True | Enable detailed logging |

## Output Files

The analyzer generates 7 CSV files in the `github_export/` directory:

| File | Description |
|------|-------------|
| `commits_export.csv` | All commits with author, date, changes, merge/revert status |
| `pull_requests_export.csv` | PRs with state, merge status, review metrics, time-to-merge |
| `issues_export.csv` | Issues with state, labels, assignees, time-to-close |
| `repository_summary.csv` | Per-repository aggregate statistics |
| `quality_metrics.csv` | Code quality scores and metrics per repository |
| `productivity_analysis.csv` | Per-contributor productivity metrics and scores |
| `contributors_summary.csv` | Contributor overview with commit and PR statistics |

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

## Quality Metrics Explained

The analyzer calculates several quality indicators:

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

## Usage Examples

### Analyze Last 7 Days
```bash
python3 github_analyzer.py
# Enter token, then specify 7 for days
```

### Analyze Multiple Repositories
Edit `repos.txt`:
```txt
organization/repo1
organization/repo2
organization/repo3
```

### Export for BI Tools
The generated CSV files can be imported into:
- Excel / Google Sheets
- Tableau / Power BI
- Pandas / Jupyter Notebooks
- Any SQL database

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Analyzer                          │
├─────────────────────────────────────────────────────────────┤
│  1. Load Configuration                                       │
│     ├─ Validate GitHub token                                │
│     ├─ Load repositories from repos.txt                     │
│     └─ Set analysis period                                  │
├─────────────────────────────────────────────────────────────┤
│  2. Data Collection (per repository)                        │
│     ├─ Fetch commits (paginated)                            │
│     ├─ Fetch pull requests (paginated)                      │
│     └─ Fetch issues (paginated)                             │
├─────────────────────────────────────────────────────────────┤
│  3. Analysis                                                 │
│     ├─ Calculate repository statistics                      │
│     ├─ Calculate quality metrics                            │
│     ├─ Aggregate contributor data                           │
│     └─ Generate productivity scores                         │
├─────────────────────────────────────────────────────────────┤
│  4. Export                                                   │
│     ├─ Generate 7 CSV files                                 │
│     └─ Display summary report                               │
└─────────────────────────────────────────────────────────────┘
```

## API Rate Limits

The tool monitors GitHub API rate limits:
- **Authenticated requests**: 5,000 per hour
- **Pagination**: Up to 50 pages per endpoint
- **Timeout**: 30 seconds per request

Rate limit status is displayed in the terminal during analysis.

## Error Handling

The analyzer gracefully handles:
- Invalid GitHub tokens
- Rate limit exceeded (HTTP 403)
- Repository not found (HTTP 404)
- Network timeouts
- Malformed repository URLs
- Empty repository lists
- JSON parsing errors

## Project Structure

```
github_analyzer/
├── github_analyzer.py    # Main application (1,033 lines)
├── repos.txt             # Repository configuration file
├── github_export/        # Output directory for CSV files
│   └── .gitkeep
└── README.md             # This file
```

## Use Cases

1. **Team Performance Reviews** - Generate productivity reports for sprint retrospectives
2. **Code Quality Audits** - Assess review practices and commit quality across repositories
3. **Open Source Analysis** - Analyze contributor patterns in open source projects
4. **Repository Health Checks** - Monitor issue resolution and PR merge velocity
5. **Trend Analysis** - Compare metrics over different time periods
6. **Multi-Team Reporting** - Aggregate metrics across organizational repositories

## Troubleshooting

### "Token validation failed"
- Ensure your token has `repo` scope
- Check if the token has expired
- Verify there are no extra spaces when pasting

### "Repository not found"
- Check the repository name format: `owner/repo`
- Verify you have access to private repositories with your token
- Ensure the repository exists

### "Rate limit exceeded"
- Wait for the rate limit to reset (usually 1 hour)
- Reduce the number of repositories analyzed at once
- Use a shorter analysis period

### Empty CSV files
- Check if repositories have activity in the specified period
- Verify repository names in `repos.txt` are correct
- Ensure the token has read access to the repositories

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is provided as-is for educational and analytical purposes.

## Acknowledgments

- Built using the [GitHub REST API v3](https://docs.github.com/en/rest)
- Designed for cross-platform compatibility with Python standard library
# github_analyzer
