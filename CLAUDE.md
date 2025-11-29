# github_analyzer Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-11-28

## Active Technologies
- Python 3.9+ (per constitution, leveraging type hints) + Standard library (urllib, json, csv, os, re); optional: requests (002-jira-integration)
- CSV files for export (same as existing GitHub exports) (002-jira-integration)
- Python 3.9+ (per constitution, leveraging type hints) + Standard library only (urllib, json, csv, os, re, datetime, statistics); optional: requests (already used in jira_client.py) (003-jira-quality-metrics)
- Python 3.9+ (as per constitution, leveraging type hints) + Standard library only (urllib, json); optional: requests (existing pattern) (004-github-repo-selection)
- N/A (repos.txt file is input, not storage) (004-github-repo-selection)
- Python 3.9+ (per constitution, leveraging type hints) + Standard library (urllib, json); optional: requests (already in codebase) (005-smart-repo-filter)
- N/A (in-memory filtering during selection) (005-smart-repo-filter)

- Python 3.9+ (as per constitution, leveraging type hints) + Standard library only (urllib, json, csv, os, re); optional: requests (001-modular-refactor)

## Project Structure

```text
src/
tests/
```

## Commands

```bash
# Run tests
pytest tests/ -v

# Run tests with coverage
pytest --cov=src/github_analyzer --cov-report=term-missing

# Run linter
ruff check src/github_analyzer/

# Run the analyzer
python github_analyzer.py --days 7
```

## Code Style

Python 3.9+ (as per constitution, leveraging type hints): Follow standard conventions

## Recent Changes
- 005-smart-repo-filter: Added Python 3.9+ (per constitution, leveraging type hints) + Standard library (urllib, json); optional: requests (already in codebase)
- 004-github-repo-selection: Added Python 3.9+ (as per constitution, leveraging type hints) + Standard library only (urllib, json); optional: requests (existing pattern)
- 003-jira-quality-metrics: Added Python 3.9+ (per constitution, leveraging type hints) + Standard library only (urllib, json, csv, os, re, datetime, statistics); optional: requests (already used in jira_client.py)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
