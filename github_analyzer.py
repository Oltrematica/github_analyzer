#!/usr/bin/env python3
"""GitHub Repository Analyzer - Backward Compatible Entry Point.

This script provides backward compatibility with the original
github_analyzer.py interface. The recommended entry point is now
dev_analyzer.py which supports multiple data sources.

For the new modular API, use:
    from src.github_analyzer.cli import main
    from src.github_analyzer.config import AnalyzerConfig
    from src.github_analyzer.api import GitHubClient
    ...

Usage:
    Set GITHUB_TOKEN environment variable, then run:
    $ python github_analyzer.py

    For multi-source analysis, use dev_analyzer.py instead:
    $ python dev_analyzer.py --sources github,jira --days 7

Output:
    - commits_export.csv: All commits from all repositories
    - pull_requests_export.csv: All PRs from all repositories
    - issues_export.csv: All issues from all repositories
    - contributors_summary.csv: Summary by contributor
    - repository_summary.csv: Summary by repository
    - quality_metrics.csv: Quality metrics by repository
    - productivity_analysis.csv: Productivity analysis by author
"""

import sys

# Import main from modular structure
from src.github_analyzer.cli.main import main

if __name__ == "__main__":
    sys.exit(main())
