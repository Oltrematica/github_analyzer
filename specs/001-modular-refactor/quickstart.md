# Quickstart: GitHub Analyzer (Post-Refactor)

**Feature**: 001-modular-refactor
**Date**: 2025-11-28

This guide shows how to use the GitHub Analyzer after the modular refactoring.

## Prerequisites

- Python 3.9 or higher
- GitHub Personal Access Token with `repo` scope

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/github_analyzer.git
cd github_analyzer

# (Optional) Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies (includes pytest)
pip install -r requirements-dev.txt
```

## Configuration

### 1. Set GitHub Token

**Required**: Set your GitHub token as an environment variable.

```bash
# Linux/macOS
export GITHUB_TOKEN="ghp_your_token_here"

# Windows (PowerShell)
$env:GITHUB_TOKEN="ghp_your_token_here"

# Windows (CMD)
set GITHUB_TOKEN=ghp_your_token_here
```

**For persistent configuration**, add to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

### 2. Configure Repositories

Create or edit `repos.txt` in the project root:

```text
# Add repositories to analyze (one per line)
# Supported formats:
#   owner/repo
#   https://github.com/owner/repo

facebook/react
microsoft/vscode
https://github.com/kubernetes/kubernetes
```

## Usage

### Run Analysis (Backward Compatible)

```bash
# Same as before - uses environment variable for token
python github_analyzer.py
```

The analyzer will:
1. Load configuration from environment
2. Validate repositories from `repos.txt`
3. Fetch data from GitHub API
4. Generate CSV reports in `github_export/`

### Output Files

After successful analysis, find these files in `github_export/`:

| File | Contents |
|------|----------|
| `commits_export.csv` | All commits with details |
| `pull_requests_export.csv` | PRs with metrics |
| `issues_export.csv` | Issues (excluding PRs) |
| `repository_summary.csv` | Per-repo statistics |
| `quality_metrics.csv` | Code quality scores |
| `productivity_analysis.csv` | Contributor productivity |
| `contributors_summary.csv` | Contributor overview |

## Development

### Project Structure

```
github_analyzer/
├── github_analyzer.py       # Entry point (backward compatible)
├── src/
│   └── github_analyzer/
│       ├── api/             # GitHub API client
│       ├── analyzers/       # Data analysis logic
│       ├── exporters/       # CSV generation
│       ├── cli/             # Command-line interface
│       ├── config/          # Configuration & validation
│       └── core/            # Shared exceptions
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
└── specs/                   # Feature specifications
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/github_analyzer --cov-report=html

# Run specific test file
pytest tests/unit/config/test_validation.py

# Run tests matching pattern
pytest -k "test_repository"
```

### Using Modules Directly

```python
from src.github_analyzer.config.settings import AnalyzerConfig
from src.github_analyzer.config.validation import Repository, load_repositories
from src.github_analyzer.api.client import GitHubClient
from src.github_analyzer.analyzers.commits import CommitAnalyzer

# Load config from environment
config = AnalyzerConfig.from_env()

# Validate a repository
repo = Repository.from_string("owner/repo")

# Create API client
client = GitHubClient(config)

# Analyze commits
analyzer = CommitAnalyzer(client)
commits = analyzer.fetch_and_analyze(repo, since=datetime.now() - timedelta(days=30))
```

## Troubleshooting

### "GITHUB_TOKEN environment variable not set"

Make sure you've set the environment variable in your current shell:

```bash
echo $GITHUB_TOKEN  # Should show your token (don't share this!)
```

If empty, set it again. Remember that `export` only affects the current session.

### "Invalid repository format"

Check your `repos.txt` for:
- Correct format: `owner/repo` or `https://github.com/owner/repo`
- No special characters except `-`, `_`, `.`
- No trailing spaces or invisible characters

### "Rate limit exceeded"

The GitHub API has rate limits (5,000 requests/hour for authenticated users).

Solutions:
- Wait for rate limit reset (shown in error message)
- Analyze fewer repositories at once
- Use a shorter analysis period

### Tests Fail with Network Errors

Tests should not require network access. If they do, ensure you're using the mocked fixtures:

```bash
# Tests should pass without GITHUB_TOKEN
unset GITHUB_TOKEN
pytest
```

## Migration from Previous Version

If upgrading from the monolithic version:

1. **No code changes needed** - `python github_analyzer.py` works the same
2. **Set environment variable** - Token is no longer prompted interactively
3. **Same output format** - CSV files are identical

The only user-visible change is that you must set `GITHUB_TOKEN` before running instead of entering it interactively.
