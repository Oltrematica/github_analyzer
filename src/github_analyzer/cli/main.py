"""Main entry point for GitHub Analyzer CLI.

This module provides the main() entry point and the GitHubAnalyzer
orchestrator class that coordinates the analysis workflow.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from src.github_analyzer.analyzers import (
    CommitAnalyzer,
    ContributorTracker,
    IssueAnalyzer,
    PullRequestAnalyzer,
    calculate_quality_metrics,
)
from src.github_analyzer.api import GitHubClient, RepositoryStats
from src.github_analyzer.cli.output import TerminalOutput
from src.github_analyzer.config import AnalyzerConfig, Repository, load_repositories
from src.github_analyzer.core.exceptions import (
    ConfigurationError,
    GitHubAnalyzerError,
    RateLimitError,
)
from src.github_analyzer.exporters import CSVExporter

if TYPE_CHECKING:
    from src.github_analyzer.api.models import Commit, Issue, PullRequest, QualityMetrics


class GitHubAnalyzer:
    """Main analyzer orchestrator.

    Coordinates the full analysis workflow:
    1. Load configuration and repositories
    2. Fetch data from GitHub API
    3. Analyze commits, PRs, issues
    4. Calculate metrics
    5. Export to CSV
    """

    def __init__(self, config: AnalyzerConfig, fetch_pr_details: bool = False) -> None:
        """Initialize analyzer with configuration.

        Args:
            config: Analyzer configuration.
            fetch_pr_details: If True, fetch full PR details (slower).
        """
        self._config = config
        self._output = TerminalOutput(verbose=config.verbose)
        self._client = GitHubClient(config)
        self._exporter = CSVExporter(config.output_dir)

        # Initialize analyzers
        self._commit_analyzer = CommitAnalyzer(self._client)
        self._pr_analyzer = PullRequestAnalyzer(self._client, fetch_details=fetch_pr_details)
        self._issue_analyzer = IssueAnalyzer(self._client)
        self._contributor_tracker = ContributorTracker()

        # Storage for results
        self._all_commits: list[Commit] = []
        self._all_prs: list[PullRequest] = []
        self._all_issues: list[Issue] = []
        self._repo_stats: list[RepositoryStats] = []
        self._quality_metrics: list[QualityMetrics] = []

    def run(self, repositories: list[Repository]) -> None:
        """Run full analysis on all repositories.

        Args:
            repositories: List of validated repositories to analyze.
        """
        since = datetime.now() - timedelta(days=self._config.days)

        self._output.log(f"Starting analysis for {len(repositories)} repositories")
        self._output.log(f"Analysis period: {self._config.days} days (since {since.date()})")

        # Analyze each repository
        for idx, repo in enumerate(repositories, 1):
            self._output.progress(idx, len(repositories), f"Analyzing {repo.full_name}")

            try:
                self._analyze_repository(repo, since)
            except RateLimitError as e:
                self._output.error("Rate limit exceeded", e.details)
                break
            except GitHubAnalyzerError as e:
                self._output.log(f"Error analyzing {repo.full_name}: {e.message}", "warning")
                continue

        # Track contributors from collected data
        self._track_contributors()

        # Generate productivity analysis
        productivity = self._contributor_tracker.generate_analysis(self._config.days)

        # Export all data
        files = self._export_all(productivity)

        # Show summary
        self._show_summary(files)

    def _analyze_repository(self, repo: Repository, since: datetime) -> None:
        """Analyze a single repository.

        Args:
            repo: Repository to analyze.
            since: Start date for analysis.
        """
        self._output.log(f"Fetching commits for {repo.full_name}", "info")
        commits = self._commit_analyzer.fetch_and_analyze(repo, since)
        self._all_commits.extend(commits)

        self._output.log(f"Fetching pull requests for {repo.full_name}", "info")
        prs = self._pr_analyzer.fetch_and_analyze(repo, since)
        self._all_prs.extend(prs)

        self._output.log(f"Fetching issues for {repo.full_name}", "info")
        issues = self._issue_analyzer.fetch_and_analyze(repo, since)
        self._all_issues.extend(issues)

        # Calculate repository stats
        commit_stats = self._commit_analyzer.get_stats(commits)
        pr_stats = self._pr_analyzer.get_stats(prs)
        issue_stats = self._issue_analyzer.get_stats(issues)

        repo_stat = RepositoryStats(
            repository=repo.full_name,
            total_commits=commit_stats["total"],
            merge_commits=commit_stats["merge_commits"],
            revert_commits=commit_stats["revert_commits"],
            total_additions=commit_stats["total_additions"],
            total_deletions=commit_stats["total_deletions"],
            unique_authors=commit_stats["unique_authors"],
            total_prs=pr_stats["total"],
            merged_prs=pr_stats["merged"],
            open_prs=pr_stats["open"],
            avg_time_to_merge_hours=pr_stats["avg_time_to_merge_hours"],
            total_issues=issue_stats["total"],
            closed_issues=issue_stats["closed"],
            open_issues=issue_stats["open"],
            bug_issues=issue_stats["bugs"],
            analysis_period_days=self._config.days,
        )
        self._repo_stats.append(repo_stat)

        # Calculate quality metrics
        quality = calculate_quality_metrics(repo, commits, prs)
        self._quality_metrics.append(quality)

        self._output.log(
            f"{repo.full_name}: {len(commits)} commits, {len(prs)} PRs, {len(issues)} issues",
            "success",
        )

    def _track_contributors(self) -> None:
        """Track contributor statistics from all data."""
        for commit in self._all_commits:
            self._contributor_tracker.record_commit(commit)

        for pr in self._all_prs:
            self._contributor_tracker.record_pr(pr)

        for issue in self._all_issues:
            self._contributor_tracker.record_issue(issue)

    def _export_all(self, productivity: list) -> list[Path]:
        """Export all data to CSV files.

        Args:
            productivity: Productivity analysis results.

        Returns:
            List of created file paths.
        """
        self._output.log("Exporting data to CSV files", "info")

        files = []
        files.append(self._exporter.export_commits(self._all_commits))
        files.append(self._exporter.export_pull_requests(self._all_prs))
        files.append(self._exporter.export_issues(self._all_issues))
        files.append(self._exporter.export_repository_summary(self._repo_stats))
        files.append(self._exporter.export_quality_metrics(self._quality_metrics))
        files.append(self._exporter.export_productivity(productivity))
        files.append(self._exporter.export_contributors(self._contributor_tracker.get_stats()))

        return files

    def _show_summary(self, files: list[Path]) -> None:
        """Show analysis summary.

        Args:
            files: List of created file paths.
        """
        commit_stats = self._commit_analyzer.get_stats(self._all_commits)
        pr_stats = self._pr_analyzer.get_stats(self._all_prs)
        issue_stats = self._issue_analyzer.get_stats(self._all_issues)

        self._output.summary({
            "repositories": len(self._repo_stats),
            "commits": commit_stats,
            "prs": pr_stats,
            "issues": issue_stats,
            "files": [str(f) for f in files],
        })

        self._output.success("Analysis complete!")

    def close(self) -> None:
        """Clean up resources."""
        self._client.close()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Analyze GitHub repositories and export metrics to CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python github_analyzer.py --days 7
  python github_analyzer.py --days 14 --output ./reports
  python github_analyzer.py --repos my_repos.txt --days 30
        """,
    )
    parser.add_argument(
        "--days", "-d",
        type=int,
        default=None,
        help="Number of days to analyze (default: 30, or GITHUB_ANALYZER_DAYS env var)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output directory for CSV files (default: github_export)",
    )
    parser.add_argument(
        "--repos", "-r",
        type=str,
        default=None,
        help="Path to repos.txt file (default: repos.txt)",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress verbose output",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Fetch full PR details (slower, includes additions/deletions per PR)",
    )
    return parser.parse_args()


def prompt_yes_no(question: str, default: bool = False) -> bool:
    """Prompt user for yes/no answer.

    Args:
        question: Question to ask.
        default: Default value if user presses Enter.

    Returns:
        True for yes, False for no.
    """
    default_hint = "[Y/n]" if default else "[y/N]"
    try:
        answer = input(f"{question} {default_hint}: ").strip().lower()
        if not answer:
            return default
        return answer in ("y", "yes", "s", "si", "sì")
    except (EOFError, KeyboardInterrupt):
        print()
        return default


def prompt_int(question: str, default: int) -> int:
    """Prompt user for integer value.

    Args:
        question: Question to ask.
        default: Default value if user presses Enter.

    Returns:
        Integer value entered by user.
    """
    try:
        answer = input(f"{question} [{default}]: ").strip()
        if not answer:
            return default
        return int(answer)
    except ValueError:
        print(f"Invalid number, using default: {default}")
        return default
    except (EOFError, KeyboardInterrupt):
        print()
        return default


def main() -> int:
    """Main entry point for CLI.

    Returns:
        Exit code (0=success, 1=user error, 2=system error).
    """
    args = parse_args()
    output = TerminalOutput()

    try:
        # Show banner
        output.banner()
        output.features()

        # Load configuration
        output.section("⚙️ CONFIGURATION")
        output.log("Loading configuration from environment...")

        config = AnalyzerConfig.from_env()

        # Override with CLI arguments
        if args.output is not None:
            config.output_dir = args.output
        if args.repos is not None:
            config.repos_file = args.repos

        config.validate()

        # Interactive prompts for options not provided via CLI
        print()

        # Days - ask if not provided via CLI
        if args.days is not None:
            config.days = args.days
        else:
            config.days = prompt_int("How many days to analyze?", config.days)

        # Quiet mode - ask if not provided via CLI
        if args.quiet:
            config.verbose = False
        else:
            config.verbose = not prompt_yes_no("Quiet mode (less output)?", default=False)

        # Full PR details - ask if not provided via CLI
        if args.full:
            fetch_pr_details = True
        else:
            fetch_pr_details = prompt_yes_no(
                "Fetch full PR details? (slower, includes additions/deletions)",
                default=False
            )

        print()
        output.log(f"Output directory: {config.output_dir}", "info")
        output.log(f"Analysis period: {config.days} days", "info")
        output.log(f"Verbose mode: {'Yes' if config.verbose else 'No'}", "info")
        output.log(f"Full PR details: {'Yes' if fetch_pr_details else 'No'}", "info")

        # Load repositories
        output.log(f"Loading repositories from {config.repos_file}...")
        repositories = load_repositories(config.repos_file)
        output.log(f"Found {len(repositories)} repositories to analyze", "success")

        for repo in repositories:
            output.log(f"  • {repo.full_name}", "info")

        # Confirm before starting
        print()
        if not prompt_yes_no("Start analysis?", default=True):
            output.log("Analysis cancelled by user", "warning")
            return 0

        # Run analysis
        output.section("🚀 ANALYSIS")

        analyzer = GitHubAnalyzer(config, fetch_pr_details=fetch_pr_details)
        try:
            analyzer.run(repositories)
        finally:
            analyzer.close()

        return 0

    except ConfigurationError as e:
        output.error(e.message, e.details)
        return e.exit_code

    except GitHubAnalyzerError as e:
        output.error(e.message, e.details)
        return e.exit_code

    except KeyboardInterrupt:
        output.log("\nAnalysis interrupted by user", "warning")
        return 130

    except Exception as e:
        output.error(f"Unexpected error: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
