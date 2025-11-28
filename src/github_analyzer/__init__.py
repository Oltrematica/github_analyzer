"""DevAnalyzer - Analyze GitHub repositories and Jira projects, export metrics.

This package provides a modular architecture for analyzing development
data from GitHub and Jira, exporting metrics to CSV files.

Modules:
- api: GitHub and Jira API clients and data models
- analyzers: Data analysis logic
- exporters: CSV export functionality
- cli: Command-line interface
- config: Configuration and validation
- core: Shared exceptions and utilities

Quick Start:
    >>> from src.github_analyzer.config import AnalyzerConfig, JiraConfig
    >>> from src.github_analyzer.cli import main
    >>> # Set GITHUB_TOKEN and/or Jira env vars, then:
    >>> main()
"""

__version__ = "2.0.0"
__author__ = "GitHub Analyzer Team"

# Convenience imports for common usage
from src.github_analyzer.analyzers.jira_issues import JiraIssueAnalyzer
from src.github_analyzer.api.jira_client import JiraClient, JiraComment, JiraIssue, JiraProject
from src.github_analyzer.cli.main import GitHubAnalyzer, main
from src.github_analyzer.config.settings import AnalyzerConfig, DataSource, JiraConfig
from src.github_analyzer.config.validation import Repository, load_repositories
from src.github_analyzer.exporters.jira_exporter import JiraExporter

__all__ = [
    "__version__",
    "main",
    "GitHubAnalyzer",
    "AnalyzerConfig",
    "JiraConfig",
    "DataSource",
    "Repository",
    "load_repositories",
    "JiraClient",
    "JiraIssue",
    "JiraComment",
    "JiraProject",
    "JiraIssueAnalyzer",
    "JiraExporter",
]
