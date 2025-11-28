"""GitHub Analyzer - Analyze GitHub repositories and export metrics.

This package provides a modular architecture for analyzing GitHub
repositories and exporting metrics to CSV files.

Modules:
- api: GitHub API client and data models
- analyzers: Data analysis logic
- exporters: CSV export functionality
- cli: Command-line interface
- config: Configuration and validation
- core: Shared exceptions and utilities

Quick Start:
    >>> from src.github_analyzer.config import AnalyzerConfig
    >>> from src.github_analyzer.cli import main
    >>> # Set GITHUB_TOKEN env var, then:
    >>> main()
"""

__version__ = "2.0.0"
__author__ = "GitHub Analyzer Team"

# Convenience imports for common usage
from src.github_analyzer.cli.main import GitHubAnalyzer, main
from src.github_analyzer.config.settings import AnalyzerConfig
from src.github_analyzer.config.validation import Repository, load_repositories

__all__ = [
    "__version__",
    "main",
    "GitHubAnalyzer",
    "AnalyzerConfig",
    "Repository",
    "load_repositories",
]
