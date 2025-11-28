"""Main entry point for GitHub Analyzer CLI.

This module provides the main() entry point and the GitHubAnalyzer
orchestrator class that coordinates the analysis workflow.

Supports multiple data sources:
- GitHub: Repository analysis with commits, PRs, issues
- Jira: Issue tracking with comments and metadata
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
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
from src.github_analyzer.config.settings import DataSource, JiraConfig
from src.github_analyzer.config.validation import load_jira_projects
from src.github_analyzer.core.exceptions import (
    ConfigurationError,
    GitHubAnalyzerError,
    RateLimitError,
)
from src.github_analyzer.exporters import CSVExporter, JiraExporter

if TYPE_CHECKING:
    from src.github_analyzer.api.jira_client import JiraProject
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
        since = datetime.now(timezone.utc) - timedelta(days=self._config.days)

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
        description="Analyze GitHub repositories and Jira projects, export metrics to CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python dev_analyzer.py --days 7
  python dev_analyzer.py --sources github --days 14
  python dev_analyzer.py --sources jira --days 30
  python dev_analyzer.py --sources github,jira --output ./reports
        """,
    )
    parser.add_argument(
        "--sources", "-s",
        type=str,
        default="auto",
        help="Data sources to analyze: auto, github, jira, or github,jira (default: auto)",
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
        "--jira-projects", "-j",
        type=str,
        default=None,
        help="Path to jira_projects.txt file (default: jira_projects.txt)",
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


def parse_sources_list(sources_str: str) -> list[DataSource]:
    """Parse sources string to list of DataSource.

    Args:
        sources_str: Comma-separated source names (e.g., "github,jira").

    Returns:
        List of DataSource values.

    Raises:
        ValueError: If unknown source name.
    """
    sources = []
    for name in sources_str.lower().split(","):
        name = name.strip()
        if name == "github":
            sources.append(DataSource.GITHUB)
        elif name == "jira":
            sources.append(DataSource.JIRA)
        elif name:
            raise ValueError(f"Unknown source: {name}. Valid sources: github, jira")
    return sources


def auto_detect_sources() -> list[DataSource]:
    """Auto-detect available data sources from environment.

    Checks for credentials in environment variables:
    - GitHub: GITHUB_TOKEN
    - Jira: JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN

    Returns:
        List of DataSource values for which credentials are available.
    """
    sources = []

    # Check for GitHub token
    if os.environ.get("GITHUB_TOKEN", "").strip():
        sources.append(DataSource.GITHUB)

    # Check for Jira credentials (all required)
    jira_url = os.environ.get("JIRA_URL", "").strip()
    jira_email = os.environ.get("JIRA_EMAIL", "").strip()
    jira_token = os.environ.get("JIRA_API_TOKEN", "").strip()

    if jira_url and jira_email and jira_token:
        sources.append(DataSource.JIRA)

    return sources


def validate_sources(sources: list[DataSource]) -> None:
    """Validate that required credentials exist for sources.

    Args:
        sources: List of data sources to validate.

    Raises:
        ValueError: If credentials are missing for a requested source.
    """
    for source in sources:
        if source == DataSource.GITHUB:
            if not os.environ.get("GITHUB_TOKEN", "").strip():
                raise ValueError(
                    "GitHub source requested but GITHUB_TOKEN environment variable not set"
                )
        elif source == DataSource.JIRA:
            jira_url = os.environ.get("JIRA_URL", "").strip()
            jira_email = os.environ.get("JIRA_EMAIL", "").strip()
            jira_token = os.environ.get("JIRA_API_TOKEN", "").strip()

            if not (jira_url and jira_email and jira_token):
                raise ValueError(
                    "Jira source requested but Jira credentials incomplete. "
                    "Set JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN environment variables."
                )


def format_project_list(projects: list[JiraProject]) -> str:
    """Format Jira projects for display.

    Args:
        projects: List of JiraProject objects.

    Returns:
        Formatted string for terminal display.
    """
    lines = []
    for idx, project in enumerate(projects, 1):
        desc = project.description[:50] + "..." if len(project.description) > 50 else project.description
        if desc:
            lines.append(f"  [{idx}] {project.key} - {project.name} ({desc})")
        else:
            lines.append(f"  [{idx}] {project.key} - {project.name}")
    return "\n".join(lines)


def parse_project_selection(selection: str, max_projects: int) -> list[int]:
    """Parse project selection input to list of indices.

    Args:
        selection: User input string (e.g., "1,3,5" or "1-3" or "all").
        max_projects: Maximum number of projects available.

    Returns:
        List of 0-indexed project indices.
    """
    selection = selection.strip().lower()

    if selection == "all":
        return list(range(max_projects))

    indices = []

    for part in selection.replace(" ", "").split(","):
        try:
            if "-" in part:
                # Range selection (e.g., "1-3")
                start, end = part.split("-", 1)
                for i in range(int(start), int(end) + 1):
                    if 1 <= i <= max_projects:
                        indices.append(i - 1)  # Convert to 0-indexed
            else:
                # Single number
                num = int(part)
                if 1 <= num <= max_projects:
                    indices.append(num - 1)  # Convert to 0-indexed
        except ValueError:
            continue

    return sorted(set(indices))


def select_jira_projects(
    projects_file: str,
    jira_config: JiraConfig | None,
) -> list[str]:
    """Select Jira projects from file or use all available.

    Args:
        projects_file: Path to jira_projects.txt file.
        jira_config: Jira configuration (required to fetch available projects).

    Returns:
        List of project keys to analyze.
    """
    # Try loading from file first
    file_projects = load_jira_projects(projects_file)
    if file_projects:
        return file_projects

    # No file or empty - use all available projects
    if not jira_config:
        return []

    # Fetch available projects from Jira
    from src.github_analyzer.api.jira_client import JiraClient

    client = JiraClient(jira_config)
    available_projects = client.get_projects()

    if not available_projects:
        print("No projects found in Jira instance.")
        return []

    # Use all available projects
    all_keys = [p.key for p in available_projects]
    print(f"\nNo {projects_file} found. Using all {len(all_keys)} available Jira projects.")

    return all_keys


def run_extraction(
    sources: list[DataSource],
    output_dir: str,
    days: int,
    repos_file: str | None = None,
    jira_projects_file: str | None = None,
    verbose: bool = True,
    fetch_pr_details: bool = False,
) -> dict:
    """Run extraction for specified sources.

    Args:
        sources: List of data sources to extract from.
        output_dir: Directory for output CSV files.
        days: Number of days to analyze.
        repos_file: Path to repos.txt for GitHub.
        jira_projects_file: Path to jira_projects.txt for Jira.
        verbose: Enable verbose output.
        fetch_pr_details: Fetch full PR details for GitHub.

    Returns:
        Dictionary with extraction results.
    """
    results: dict[str, dict[str, object] | None] = {"github": None, "jira": None}

    if DataSource.GITHUB in sources:
        # Run GitHub extraction
        config = AnalyzerConfig.from_env()
        if repos_file:
            config.repos_file = repos_file
        config.output_dir = output_dir
        config.days = days
        config.verbose = verbose
        config.validate()

        repositories = load_repositories(config.repos_file)

        analyzer = GitHubAnalyzer(config, fetch_pr_details=fetch_pr_details)
        try:
            analyzer.run(repositories)
            results["github"] = {"status": "success", "repos": len(repositories)}
        finally:
            analyzer.close()

    if DataSource.JIRA in sources:
        # Run Jira extraction
        from src.github_analyzer.api.jira_client import JiraClient

        jira_config = JiraConfig.from_env()
        if not jira_config:
            raise ConfigurationError("Jira credentials not configured")

        # Get Jira projects
        projects_file = jira_projects_file or jira_config.jira_projects_file
        project_keys = select_jira_projects(projects_file, jira_config)

        if not project_keys:
            print("No Jira projects selected. Skipping Jira extraction.")
        else:
            client = JiraClient(jira_config)
            since = datetime.now(timezone.utc) - timedelta(days=days)

            # Collect issues and comments
            all_issues = list(client.search_issues(project_keys, since))
            all_comments = []
            for issue in all_issues:
                comments = client.get_comments(issue.key)
                all_comments.extend(comments)

            # Export Jira data to CSV
            jira_exporter = JiraExporter(output_dir)
            issues_file = jira_exporter.export_issues(all_issues)
            comments_file = jira_exporter.export_comments(all_comments)

            results["jira"] = {
                "status": "success",
                "issues": len(all_issues),
                "comments": len(all_comments),
                "files": [str(issues_file), str(comments_file)],
            }

    return results


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

        # Determine data sources
        if args.sources == "auto":
            sources = auto_detect_sources()
            if not sources:
                output.error("No data sources available. Set GITHUB_TOKEN or Jira credentials.")
                return 1
            output.log(f"Auto-detected sources: {', '.join(s.value for s in sources)}", "info")
        else:
            sources = parse_sources_list(args.sources)
            validate_sources(sources)
            output.log(f"Using sources: {', '.join(s.value for s in sources)}", "info")

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

        # Load GitHub repositories if GitHub source is enabled
        repositories = []
        if DataSource.GITHUB in sources:
            output.log(f"Loading repositories from {config.repos_file}...")
            repositories = load_repositories(config.repos_file)
            output.log(f"Found {len(repositories)} repositories to analyze", "success")

            for repo in repositories:
                output.log(f"  • {repo.full_name}", "info")

        # Load Jira projects if Jira source is enabled
        jira_config = None
        project_keys: list[str] = []
        if DataSource.JIRA in sources:
            jira_config = JiraConfig.from_env()
            if jira_config:
                projects_file = args.jira_projects or jira_config.jira_projects_file
                project_keys = select_jira_projects(projects_file, jira_config)
                output.log(f"Found {len(project_keys)} Jira projects to analyze", "success")
                for key in project_keys[:5]:
                    output.log(f"  • {key}", "info")
                if len(project_keys) > 5:
                    output.log(f"  ... and {len(project_keys) - 5} more", "info")

        # Confirm before starting
        print()
        if not prompt_yes_no("Start analysis?", default=True):
            output.log("Analysis cancelled by user", "warning")
            return 0

        # Run analysis
        output.section("🚀 ANALYSIS")

        # Run GitHub analysis
        if DataSource.GITHUB in sources and repositories:
            output.log("Starting GitHub analysis...", "info")
            analyzer = GitHubAnalyzer(config, fetch_pr_details=fetch_pr_details)
            try:
                analyzer.run(repositories)
            finally:
                analyzer.close()

        # Run Jira extraction
        if DataSource.JIRA in sources and jira_config and project_keys:
            output.log("Starting Jira extraction...", "info")
            from src.github_analyzer.api.jira_client import JiraClient

            client = JiraClient(jira_config)
            since = datetime.now(timezone.utc) - timedelta(days=config.days)

            # Collect issues and comments
            output.log(f"Fetching issues from {len(project_keys)} projects...", "info")
            all_issues = list(client.search_issues(project_keys, since))
            output.log(f"Found {len(all_issues)} issues", "success")

            output.log("Fetching comments...", "info")
            all_comments = []
            for issue in all_issues:
                comments = client.get_comments(issue.key)
                all_comments.extend(comments)
            output.log(f"Found {len(all_comments)} comments", "success")

            # Export Jira data to CSV
            jira_exporter = JiraExporter(config.output_dir)
            issues_file = jira_exporter.export_issues(all_issues)
            comments_file = jira_exporter.export_comments(all_comments)
            output.log(f"Exported Jira issues to {issues_file}", "success")
            output.log(f"Exported Jira comments to {comments_file}", "success")

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
