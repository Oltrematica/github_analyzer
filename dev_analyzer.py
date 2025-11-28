#!/usr/bin/env python3
"""DevAnalyzer - Multi-platform development data extraction tool.

This is the primary entry point for analyzing GitHub repositories and Jira projects.
Supports multiple data sources with auto-detection of available credentials.

Usage:
    python dev_analyzer.py --sources auto --days 7
    python dev_analyzer.py --sources github --days 14
    python dev_analyzer.py --sources jira --days 30
    python dev_analyzer.py --sources github,jira --output ./reports

Environment Variables:
    GitHub:
        GITHUB_TOKEN: GitHub Personal Access Token (required for GitHub)

    Jira:
        JIRA_URL: Jira instance URL (e.g., https://company.atlassian.net)
        JIRA_EMAIL: User email for authentication
        JIRA_API_TOKEN: Jira API token

For more information, run with --help.
"""

from __future__ import annotations

import sys

from src.github_analyzer.cli.main import main

if __name__ == "__main__":
    sys.exit(main())
