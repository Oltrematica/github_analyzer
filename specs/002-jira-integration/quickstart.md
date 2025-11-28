# Quickstart: Jira Integration

**Feature**: 002-jira-integration
**Date**: 2025-11-28

## Prerequisites

- Python 3.9+
- Jira account with API token
- (Optional) GitHub token for combined extraction

## Setup

### 1. Generate Jira API Token

**For Atlassian Cloud:**
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name (e.g., "dev-analyzer")
4. Copy the token (shown only once)

**For Jira Server/Data Center:**
1. Go to Profile → Personal Access Tokens
2. Create new token with appropriate permissions
3. Copy the token

### 2. Set Environment Variables

```bash
# Required for Jira
export JIRA_URL="https://yourcompany.atlassian.net"
export JIRA_EMAIL="your.email@company.com"
export JIRA_API_TOKEN="your-api-token"

# Optional: GitHub (if using both sources)
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
```

### 3. Configure Projects (Optional)

Create `jira_projects.txt` in the project root:

```text
# One project key per line
PROJ
DEV
SUPPORT
```

If this file is missing, the tool will prompt you interactively.

## Usage

### Basic Usage (Both Sources)

```bash
# Extract last 7 days from both GitHub and Jira
python dev_analyzer.py --days 7

# Or use the legacy entrypoint (same behavior)
python github_analyzer.py --days 7
```

### Single Source

```bash
# Jira only
python dev_analyzer.py --days 7 --sources jira

# GitHub only (backward compatible)
python dev_analyzer.py --days 7 --sources github
```

### Output Files

After running, you'll find these files in `github_export/`:

**GitHub exports** (unchanged):
- `commits_export.csv`
- `pull_requests_export.csv`
- `issues_export.csv`
- `contributors_summary.csv`
- `repository_summary.csv`

**Jira exports** (new):
- `jira_issues_export.csv`
- `jira_comments_export.csv`

## Example Workflow

```bash
# 1. Set up environment
export JIRA_URL="https://mycompany.atlassian.net"
export JIRA_EMAIL="dev@mycompany.com"
export JIRA_API_TOKEN="ATATT3x..."
export GITHUB_TOKEN="ghp_..."

# 2. Create project list
echo "BACKEND" > jira_projects.txt
echo "FRONTEND" >> jira_projects.txt

# 3. Run extraction
python dev_analyzer.py --days 30

# 4. Check output
ls -la github_export/
cat github_export/jira_issues_export.csv | head -5
```

## Troubleshooting

### "JIRA_URL environment variable not set"

Ensure all three Jira variables are set:
```bash
echo $JIRA_URL
echo $JIRA_EMAIL
echo $JIRA_API_TOKEN
```

### "Authentication failed"

1. Verify your email matches your Jira account
2. Check that the API token is valid and not expired
3. For Cloud, ensure you're using `email:token` format
4. For Server, verify the token has appropriate permissions

### "Project not found: PROJ"

1. Verify the project key is correct (case-sensitive, uppercase)
2. Check that your account has access to the project
3. Try listing available projects:
   ```bash
   python dev_analyzer.py --list-jira-projects
   ```

### "Rate limit exceeded"

The tool will automatically retry with backoff. If persistent:
1. Wait a few minutes and retry
2. Reduce the time range (`--days`)
3. Reduce the number of projects in `jira_projects.txt`

### Jira skipped (no credentials)

This is expected behavior. If you only have GitHub configured, Jira extraction is skipped with an informational message. To use Jira, set the required environment variables.

## CSV Output Reference

### jira_issues_export.csv

| Column | Description | Example |
|--------|-------------|---------|
| key | Issue key | PROJ-123 |
| summary | Issue title | Fix login bug |
| status | Current status | In Progress |
| issue_type | Issue type | Bug |
| priority | Priority level | High |
| assignee | Assigned user | John Doe |
| reporter | Creator | Jane Smith |
| created | Creation date | 2025-11-20T10:30:00Z |
| updated | Last update | 2025-11-28T14:15:00Z |
| resolution_date | Resolution date | 2025-11-27T16:00:00Z |
| project_key | Project key | PROJ |

### jira_comments_export.csv

| Column | Description | Example |
|--------|-------------|---------|
| issue_key | Parent issue | PROJ-123 |
| author | Comment author | John Doe |
| created | Comment date | 2025-11-21T09:00:00Z |
| body | Comment text | Fixed in PR #456 |

## Next Steps

- Run `/speckit.tasks` to generate implementation tasks
- See [research.md](./research.md) for technical decisions
- See [contracts/jira-api.md](./contracts/jira-api.md) for API details
