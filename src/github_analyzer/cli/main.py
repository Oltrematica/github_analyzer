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
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from src.github_analyzer.analyzers import (
    CommitAnalyzer,
    ContributorTracker,
    IssueAnalyzer,
    PullRequestAnalyzer,
    calculate_quality_metrics,
)
from src.github_analyzer.api import GitHubClient, RepositoryStats
from src.github_analyzer.cli.output import TerminalOutput
from src.github_analyzer.config import AnalyzerConfig, Repository
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


# GitHub repository validation patterns (per spec Validation Patterns section)
REPO_FORMAT_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$")
ORG_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$")


def validate_repo_format(repo: str) -> bool:
    """Validate repository name format (owner/repo).

    Per spec FR-011 and Validation Patterns section:
    - Pattern: ^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$
    - Valid: owner/repo, my-org/my-repo, user123/project_v2

    Args:
        repo: Repository string to validate.

    Returns:
        True if valid format, False otherwise.
    """
    if not repo or not repo.strip():
        return False
    return bool(REPO_FORMAT_PATTERN.match(repo.strip()))


def validate_org_name(org: str) -> bool:
    """Validate organization name format.

    Per spec Validation Patterns section:
    - Pattern: ^[a-zA-Z0-9]([a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$
    - Rules: 1-39 chars, alphanumeric and hyphens, cannot start/end with hyphen
    - Double hyphens (--) are not allowed

    Args:
        org: Organization name to validate.

    Returns:
        True if valid format, False otherwise.
    """
    if not org or not org.strip():
        return False
    org = org.strip()
    if len(org) > 39:
        return False
    # Double hyphens not allowed
    if "--" in org:
        return False
    # Single character is valid
    if len(org) == 1:
        return org.isalnum()
    return bool(ORG_NAME_PATTERN.match(org))


# =============================================================================
# Feature 005: Smart Repository Filtering - Helper Functions
# =============================================================================


def get_cutoff_date(days: int) -> date:
    """Calculate activity cutoff date from number of days (Feature 005 - T007).

    Per spec FR-002: Filtering logic uses cutoff_date = today - days.
    Repos with pushed_at >= cutoff_date are considered active.

    Args:
        days: Number of days to look back from today.

    Returns:
        date object representing the cutoff date (inclusive boundary).

    Example:
        >>> get_cutoff_date(30)  # If today is 2025-11-29
        datetime.date(2025, 10, 30)
    """
    return datetime.now(timezone.utc).date() - timedelta(days=days)


def filter_by_activity(repos: list[dict], cutoff: date) -> list[dict]:
    """Filter repositories by pushed_at date (Feature 005 - T008).

    Per spec FR-002: Filters repos where pushed_at >= cutoff_date.
    Uses client-side filtering for personal repos (Search API user:
    qualifier only returns owned repos, missing collaborator access).

    Args:
        repos: List of repository dicts with 'pushed_at' field
               (ISO 8601 format: "2025-11-28T10:00:00Z").
        cutoff: Cutoff date - repos pushed on or after this date are active.

    Returns:
        List of active repositories (pushed_at >= cutoff).
        Repos without pushed_at or with null value are excluded.

    Example:
        >>> repos = [{"full_name": "user/repo", "pushed_at": "2025-11-28T10:00:00Z"}]
        >>> filter_by_activity(repos, date(2025, 11, 1))
        [{"full_name": "user/repo", "pushed_at": "2025-11-28T10:00:00Z"}]
    """
    active_repos = []

    for repo in repos:
        pushed_at_str = repo.get("pushed_at")
        if not pushed_at_str:
            # Skip repos without pushed_at (treat as inactive)
            continue

        try:
            # Parse ISO 8601 timestamp (e.g., "2025-11-28T10:00:00Z")
            pushed_at = datetime.fromisoformat(pushed_at_str.replace("Z", "+00:00"))
            repo_date = pushed_at.date()

            # Include if pushed_at >= cutoff (inclusive boundary per spec)
            if repo_date >= cutoff:
                active_repos.append(repo)
        except (ValueError, AttributeError):
            # Skip repos with invalid date format
            continue

    return active_repos


def display_activity_stats(total: int, active: int, days: int) -> None:
    """Display repository activity statistics (Feature 005 - T009).

    Per spec FR-007: Display format is exactly:
    "{total} repos found, {active} with activity in last {days} days"

    Args:
        total: Total number of repositories.
        active: Number of active repositories (pushed in analysis period).
        days: Number of days in the analysis period.

    Example output:
        135 repos found, 28 with activity in last 30 days
    """
    print(f"{total} repos found, {active} with activity in last {days} days")


def format_repo_list(repos: list[dict]) -> str:
    """Format GitHub repositories for display.

    Per spec Display Format section:
    - N. owner/repo-name - Description (truncated to 50 chars)
    - N. owner/private-repo - [private] Description here

    Args:
        repos: List of repository dictionaries with full_name, private, description.

    Returns:
        Formatted string for terminal display.
    """
    lines = []
    for idx, repo in enumerate(repos, 1):
        full_name = repo.get("full_name", "unknown")
        is_private = repo.get("private", False)
        description = repo.get("description") or ""

        # Truncate description to 50 chars
        if len(description) > 50:
            description = description[:47] + "..."

        # Build display line
        if is_private:
            if description:
                lines.append(f"  {idx}. {full_name} - [private] {description}")
            else:
                lines.append(f"  {idx}. {full_name} - [private]")
        else:
            if description:
                lines.append(f"  {idx}. {full_name} - {description}")
            else:
                lines.append(f"  {idx}. {full_name}")

    return "\n".join(lines)


def load_github_repos_from_file(repos_file: str) -> list[str]:
    """Load repository names from repos.txt file.

    Args:
        repos_file: Path to repos.txt file.

    Returns:
        List of repository names (owner/repo format), or empty if file missing/empty.
    """
    try:
        path = Path(repos_file)
        if not path.exists():
            return []

        content = path.read_text().strip()
        if not content:
            return []

        repos = []
        for line in content.splitlines():
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue
            # Handle full URLs
            if line.startswith("http"):
                # Extract owner/repo from URL
                # https://github.com/owner/repo or https://github.com/owner/repo.git
                parts = line.rstrip("/").rstrip(".git").split("/")
                if len(parts) >= 2:
                    repos.append(f"{parts[-2]}/{parts[-1]}")
            else:
                repos.append(line)
        return repos
    except OSError:
        return []


def _handle_rate_limit(e: RateLimitError, log: Callable[[str, str], None]) -> None:
    """Handle rate limit error with wait time display (FR-008, T049).

    Per spec Edge Cases: Show wait time to user.

    Args:
        e: RateLimitError with reset_time.
        log: Logging function.
    """
    import time as time_module
    if e.reset_time:
        wait_seconds = max(0, e.reset_time - int(time_module.time()))
        log(f"Rate limit exceeded. Waiting {wait_seconds} seconds...", "warning")
    else:
        log("Rate limit exceeded. Please try again later.", "warning")


def select_github_repos(
    repos_file: str,
    github_token: str,
    interactive: bool = True,
    output: TerminalOutput | None = None,
    days: int = 30,
) -> list[str]:
    """Select GitHub repositories from file or interactively (Feature 004 + 005).

    Per spec FR-001 to FR-014 (Feature 004) and Feature 005 Smart Filtering:
    - Display interactive menu when repos.txt is missing or empty
    - Options: [A] All personal, [S] Specify manually, [O] Organization,
               [L] Select from list, [Q] Quit/Skip
    - Apply activity filtering for [A], [L], [O] options (Feature 005)
    - Display activity statistics per FR-007
    - Confirmation prompt with [Y/n/all] per FR-006

    Args:
        repos_file: Path to repos.txt file.
        github_token: GitHub API token for API calls.
        interactive: If True, prompt user when file is missing/empty.
                    If False (--quiet mode), skip prompts per FR-013.
        output: Optional TerminalOutput for consistent logging.
        days: Analysis period in days for activity filtering (default 30).

    Returns:
        List of repository names (owner/repo format) to analyze.
    """
    # Helper for consistent output
    def log(msg: str, level: str = "info") -> None:
        if output:
            output.log(msg, level)
        else:
            print(msg)

    # Try loading from file first (FR-001)
    file_repos = load_github_repos_from_file(repos_file)
    if file_repos:
        return file_repos

    # No file or empty - need to prompt or skip
    if not interactive:
        # FR-013, FR-014: Non-interactive mode skips prompts
        log("No repos.txt found. Skipping GitHub analysis in non-interactive mode.", "info")
        return []

    # Display menu per FR-002
    print("\nOptions:")
    print("  [A] Analyze ALL accessible repositories")
    print("  [S] Specify repository names manually (owner/repo format)")
    print("  [O] Analyze organization repositories")
    print("  [L] Select from list by number (e.g., 1,3,5 or 1-3)")
    print("  [Q] Quit/Skip GitHub analysis")

    # Create client for API calls - use provided token
    config = AnalyzerConfig(github_token=github_token)
    client = GitHubClient(config)

    try:
        while True:
            try:
                choice = input("\nYour choice [A/S/O/L/Q]: ").strip().upper()
            except (EOFError, KeyboardInterrupt):
                # FR-004: Handle EOF/KeyboardInterrupt gracefully
                log("GitHub analysis skipped.", "warning")
                return []

            if choice == "A":
                # FR-005: List all user repos with activity filtering (Feature 005)
                log("Fetching your repositories...", "info")
                try:
                    repos = client.list_user_repos()
                    if not repos:
                        log("No repositories found for your account.", "warning")
                        continue

                    # Feature 005: Apply activity filtering
                    cutoff = get_cutoff_date(days)
                    active_repos = filter_by_activity(repos, cutoff)

                    # Display activity statistics (FR-007)
                    display_activity_stats(total=len(repos), active=len(active_repos), days=days)

                    # Handle zero active repos (FR-009)
                    if not active_repos:
                        print(f"⚠️ No repositories have been pushed to in the last {days} days.")
                        try:
                            zero_choice = input("Options: [1] Include all repos, [2] Cancel: ").strip()
                        except (EOFError, KeyboardInterrupt):
                            return []
                        if zero_choice == "1":
                            active_repos = repos
                        else:
                            continue

                    # Confirmation prompt (FR-006)
                    try:
                        confirm = input(f"Proceed with {len(active_repos)} active repositories? [Y/n/all]: ").strip().lower()
                    except (EOFError, KeyboardInterrupt):
                        log("GitHub analysis skipped.", "warning")
                        return []

                    if confirm == "n":
                        continue  # Return to menu
                    elif confirm == "all":
                        # Use all repos (bypass filter)
                        repo_names = [r["full_name"] for r in repos]
                    else:
                        # Default (Y or Enter): use active repos only
                        repo_names = [r["full_name"] for r in active_repos]

                    log(f"Using {len(repo_names)} repositories.", "success")
                    return repo_names
                except RateLimitError as e:
                    _handle_rate_limit(e, log)
                    continue
                except GitHubAnalyzerError as e:
                    log(f"Error fetching repositories: {e.message}", "error")
                    continue

            elif choice == "S":
                # FR-009: Manual specification
                try:
                    manual_input = input("Enter repository names (owner/repo, comma-separated): ").strip()
                except (EOFError, KeyboardInterrupt):
                    log("GitHub analysis skipped.", "warning")
                    return []

                if not manual_input:
                    log("No repositories entered.", "warning")
                    continue

                # Parse and validate (FR-011, FR-012)
                manual_repos = [r.strip() for r in manual_input.split(",") if r.strip()]
                valid_repos = [r for r in manual_repos if validate_repo_format(r)]
                invalid_repos = [r for r in manual_repos if not validate_repo_format(r)]

                if invalid_repos:
                    log(f"Invalid repository format ignored: {', '.join(invalid_repos)}", "warning")

                if valid_repos:
                    log(f"Selected {len(valid_repos)} repositories: {', '.join(valid_repos)}", "success")
                    return valid_repos
                else:
                    log("No valid repository names entered. Try again.", "warning")

            elif choice == "O":
                # FR-006: Organization repos with Search API filtering (Feature 005)
                try:
                    org_name = input("Enter organization name: ").strip()
                except (EOFError, KeyboardInterrupt):
                    log("GitHub analysis skipped.", "warning")
                    return []

                if not validate_org_name(org_name):
                    log("Invalid organization name format.", "warning")
                    continue

                log(f"Fetching repositories for organization '{org_name}'...", "info")
                try:
                    # Feature 005: Use Search API for efficient org filtering
                    cutoff = get_cutoff_date(days)
                    cutoff_str = cutoff.isoformat()

                    # Get total org repos count for stats
                    all_org_repos = client.list_org_repos(org_name)
                    total_count = len(all_org_repos)

                    if total_count == 0:
                        log(f"No repositories found in organization '{org_name}'.", "warning")
                        continue

                    # Get active repos via Search API
                    search_result = client.search_active_org_repos(org_name, cutoff_str)
                    active_repos = search_result.get("items", [])
                    incomplete = search_result.get("incomplete_results", False)

                    # Display activity statistics (FR-007)
                    display_activity_stats(total=total_count, active=len(active_repos), days=days)

                    # Warn if results may be incomplete
                    if incomplete:
                        print("⚠️ Results may be incomplete due to API limitations.")

                    # Handle zero active repos (FR-009)
                    if not active_repos:
                        print(f"⚠️ No organization repositories have been pushed to in the last {days} days.")
                        try:
                            zero_choice = input("Options: [1] Show all repos, [2] Cancel: ").strip()
                        except (EOFError, KeyboardInterrupt):
                            return []
                        if zero_choice == "1":
                            active_repos = all_org_repos
                        else:
                            continue

                    # Confirmation prompt (FR-006)
                    try:
                        confirm = input(f"Show {len(active_repos)} active repositories for selection? [Y/n/all]: ").strip().lower()
                    except (EOFError, KeyboardInterrupt):
                        log("GitHub analysis skipped.", "warning")
                        return []

                    if confirm == "n":
                        continue  # Return to menu
                    elif confirm == "all":
                        # Show all repos (bypass filter)
                        display_repos = all_org_repos
                    else:
                        # Default (Y or Enter): show active repos only
                        display_repos = active_repos

                    log(f"Showing {len(display_repos)} repositories:", "info")
                    print(format_repo_list(display_repos))

                    # Ask for selection
                    try:
                        selection_input = input("\nSelect (e.g., 1,3,5 or 1-3 or 'all'): ").strip()
                    except (EOFError, KeyboardInterrupt):
                        log("GitHub analysis skipped.", "warning")
                        return []

                    indices = parse_project_selection(selection_input, len(display_repos))
                    if indices:
                        selected = [display_repos[i]["full_name"] for i in indices]
                        log(f"Selected {len(selected)} repositories.", "success")
                        return selected
                    else:
                        log("Invalid selection.", "warning")

                except RateLimitError:
                    # Feature 005 FR-008: Fallback to unfiltered mode on rate limit
                    log("⚠️ Search API rate limit exceeded. Showing all repositories without activity filter.", "warning")
                    try:
                        all_org_repos = client.list_org_repos(org_name)
                        if all_org_repos:
                            log(f"Showing {len(all_org_repos)} repositories (unfiltered):", "info")
                            print(format_repo_list(all_org_repos))
                            selection_input = input("\nSelect (e.g., 1,3,5 or 1-3 or 'all'): ").strip()
                            indices = parse_project_selection(selection_input, len(all_org_repos))
                            if indices:
                                selected = [all_org_repos[i]["full_name"] for i in indices]
                                log(f"Selected {len(selected)} repositories.", "success")
                                return selected
                    except (EOFError, KeyboardInterrupt, GitHubAnalyzerError):
                        pass
                    continue
                except GitHubAnalyzerError as e:
                    if "404" in str(e):
                        log(f"Organization '{org_name}' not found or not accessible.", "warning")
                    else:
                        log(f"Error fetching organization repos: {e.message}", "error")
                    continue

            elif choice == "L":
                # FR-010: Select from personal list with activity filtering (Feature 005)
                log("Fetching your repositories...", "info")
                try:
                    repos = client.list_user_repos()
                    if not repos:
                        log("No repositories found for your account.", "warning")
                        continue

                    # Feature 005: Apply activity filtering
                    cutoff = get_cutoff_date(days)
                    active_repos = filter_by_activity(repos, cutoff)

                    # Display activity statistics (FR-007)
                    display_activity_stats(total=len(repos), active=len(active_repos), days=days)

                    # Handle zero active repos (FR-009)
                    if not active_repos:
                        print(f"⚠️ No repositories have been pushed to in the last {days} days.")
                        try:
                            zero_choice = input("Options: [1] Show all repos, [2] Cancel: ").strip()
                        except (EOFError, KeyboardInterrupt):
                            return []
                        if zero_choice == "1":
                            active_repos = repos
                        else:
                            continue

                    # Confirmation prompt (FR-006) - ask before showing list
                    try:
                        confirm = input(f"Show {len(active_repos)} active repositories for selection? [Y/n/all]: ").strip().lower()
                    except (EOFError, KeyboardInterrupt):
                        log("GitHub analysis skipped.", "warning")
                        return []

                    if confirm == "n":
                        continue  # Return to menu
                    elif confirm == "all":
                        # Show all repos (bypass filter)
                        display_repos = repos
                    else:
                        # Default (Y or Enter): show active repos only
                        display_repos = active_repos

                    log(f"Showing {len(display_repos)} repositories:", "info")
                    print(format_repo_list(display_repos))

                    try:
                        selection_input = input("\nSelect (e.g., 1,3,5 or 1-3 or 'all'): ").strip()
                    except (EOFError, KeyboardInterrupt):
                        log("GitHub analysis skipped.", "warning")
                        return []

                    indices = parse_project_selection(selection_input, len(display_repos))
                    if indices:
                        selected = [display_repos[i]["full_name"] for i in indices]
                        log(f"Selected {len(selected)} repositories.", "success")
                        return selected
                    else:
                        log("Invalid selection. Try again.", "warning")

                except RateLimitError as e:
                    _handle_rate_limit(e, log)
                    continue
                except GitHubAnalyzerError as e:
                    log(f"Error fetching repositories: {e.message}", "error")
                    continue

            elif choice == "Q":
                log("GitHub analysis skipped.", "warning")
                return []

            else:
                log("Invalid choice. Please enter A, S, O, L, or Q.", "warning")

    finally:
        client.close()


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
    interactive: bool = True,
    output: TerminalOutput | None = None,
) -> list[str]:
    """Select Jira projects from file or interactively (FR-009, FR-009a).

    Args:
        projects_file: Path to jira_projects.txt file.
        jira_config: Jira configuration (required to fetch available projects).
        interactive: If True, prompt user when file is missing/empty.
                    If False, use all available projects automatically.
        output: Optional TerminalOutput for consistent logging.

    Returns:
        List of project keys to analyze.
    """
    # Helper for consistent output
    def log(msg: str, level: str = "info") -> None:
        if output:
            output.log(msg, level)
        else:
            print(msg)

    # Try loading from file first (FR-009)
    file_projects = load_jira_projects(projects_file)
    if file_projects:
        return file_projects

    # No file or empty - need to prompt or use all (FR-009a)
    if not jira_config:
        return []

    # Fetch available projects from Jira
    from src.github_analyzer.api.jira_client import JiraClient

    client = JiraClient(jira_config)
    available_projects = client.get_projects()

    if not available_projects:
        log("No projects found in Jira instance.", "warning")
        return []

    all_keys = [p.key for p in available_projects]

    # Non-interactive mode: use all projects automatically
    if not interactive:
        log(f"No {projects_file} found. Using all {len(all_keys)} available Jira projects.", "info")
        return all_keys

    # Interactive mode: prompt user per FR-009a
    log(f"{projects_file} not found or empty.", "info")
    log(f"Found {len(available_projects)} accessible Jira projects:", "info")
    print(format_project_list(available_projects))  # Project list always uses print for formatting
    print("\nOptions:")
    print("  [A] Analyze ALL accessible projects")
    print("  [S] Specify project keys manually (comma-separated)")
    print("  [L] Select from list by number (e.g., 1,3,5 or 1-3)")
    print("  [Q] Quit/Skip Jira extraction")

    while True:
        try:
            choice = input("\nYour choice [A/S/L/Q]: ").strip().upper()
        except (EOFError, KeyboardInterrupt):
            log("Jira extraction skipped.", "warning")
            return []

        if choice == "A":
            log(f"Using all {len(all_keys)} projects.", "success")
            return all_keys

        elif choice == "S":
            try:
                manual_input = input("Enter project keys (comma-separated): ").strip()
            except (EOFError, KeyboardInterrupt):
                log("Jira extraction skipped.", "warning")
                return []

            if not manual_input:
                log("No projects entered.", "warning")
                continue

            # Parse and validate manual input
            manual_keys = [k.strip().upper() for k in manual_input.split(",") if k.strip()]
            valid_keys = [k for k in manual_keys if k in all_keys]
            invalid_keys = [k for k in manual_keys if k not in all_keys]

            if invalid_keys:
                log(f"Invalid project keys ignored: {', '.join(invalid_keys)}", "warning")

            if valid_keys:
                log(f"Selected {len(valid_keys)} projects: {', '.join(valid_keys)}", "success")
                return valid_keys
            else:
                log("No valid project keys entered. Try again.", "warning")

        elif choice == "L":
            try:
                selection_input = input("Enter selection (e.g., 1,3,5 or 1-3 or 'all'): ").strip()
            except (EOFError, KeyboardInterrupt):
                log("Jira extraction skipped.", "warning")
                return []

            indices = parse_project_selection(selection_input, len(available_projects))
            if indices:
                selected_keys = [available_projects[i].key for i in indices]
                log(f"Selected {len(selected_keys)} projects: {', '.join(selected_keys)}", "success")
                return selected_keys
            else:
                log("Invalid selection. Try again.", "warning")

        elif choice == "Q":
            log("Jira extraction skipped.", "warning")
            return []

        else:
            log("Invalid choice. Please enter A, S, L, or Q.", "warning")


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
        repositories: list[Repository] = []
        if DataSource.GITHUB in sources:
            # Use interactive selection (Feature 004 + 005)
            # select_github_repos handles: file loading, empty/missing file prompts
            # Feature 005: Pass days parameter for activity filtering
            interactive = not args.quiet if hasattr(args, "quiet") else True
            repo_names = select_github_repos(
                repos_file=config.repos_file,
                github_token=config.github_token,
                interactive=interactive,
                output=output,
                days=config.days,  # Feature 005: Activity filtering period
            )

            # Convert string names to Repository objects
            for name in repo_names:
                repositories.append(Repository.from_string(name))

            if repositories:
                output.log(f"Found {len(repositories)} repositories to analyze", "success")
                for repo in repositories:
                    output.log(f"  • {repo.full_name}", "info")
            else:
                output.log("No GitHub repositories selected", "warning")

        # Load Jira projects if Jira source is enabled
        jira_config = None
        project_keys: list[str] = []
        if DataSource.JIRA in sources:
            jira_config = JiraConfig.from_env()
            if jira_config:
                projects_file = args.jira_projects or jira_config.jira_projects_file
                project_keys = select_jira_projects(projects_file, jira_config, output=output)
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

        # Run Jira extraction with quality metrics (Feature 003)
        if DataSource.JIRA in sources and jira_config and project_keys:
            output.log("Starting Jira extraction...", "info")
            from src.github_analyzer.analyzers.jira_metrics import IssueMetrics, MetricsCalculator
            from src.github_analyzer.api.jira_client import JiraClient, JiraComment
            from src.github_analyzer.exporters.jira_metrics_exporter import JiraMetricsExporter

            client = JiraClient(jira_config)
            since = datetime.now(timezone.utc) - timedelta(days=config.days)

            # Collect issues and comments
            output.log(f"Fetching issues from {len(project_keys)} projects...", "info")
            all_issues = list(client.search_issues(project_keys, since))
            output.log(f"Found {len(all_issues)} issues", "success")

            output.log("Fetching comments...", "info")
            all_comments = []
            issue_comments_map: dict[str, list[JiraComment]] = {}  # Map issue key to comments
            for issue in all_issues:
                comments = client.get_comments(issue.key)
                all_comments.extend(comments)
                issue_comments_map[issue.key] = comments
            output.log(f"Found {len(all_comments)} comments", "success")

            # Calculate quality metrics for each issue (Feature 003)
            output.log("Calculating quality metrics...", "info")
            calculator = MetricsCalculator()
            issue_metrics = []
            for issue in all_issues:
                comments = issue_comments_map.get(issue.key, [])
                # Best-effort changelog retrieval (gracefully handles 403/404)
                changelog = client.get_issue_changelog(issue.key)
                metrics = calculator.calculate_issue_metrics(issue, comments, changelog)
                issue_metrics.append(metrics)
            output.log(f"Calculated metrics for {len(issue_metrics)} issues", "success")

            # Export Jira data to CSV with metrics
            jira_exporter = JiraExporter(config.output_dir)
            metrics_exporter = JiraMetricsExporter(config.output_dir)

            # Export issues with embedded metrics (extended CSV)
            issues_file = jira_exporter.export_issues_with_metrics(issue_metrics)
            comments_file = jira_exporter.export_comments(all_comments)
            output.log(f"Exported Jira issues to {issues_file}", "success")
            output.log(f"Exported Jira comments to {comments_file}", "success")

            # Export aggregated metrics (project, person, type summaries)
            # Group issues by project for project-level aggregation
            issues_by_project: dict[str, list[IssueMetrics]] = {}
            for m in issue_metrics:
                proj_key = m.issue.project_key
                if proj_key not in issues_by_project:
                    issues_by_project[proj_key] = []
                issues_by_project[proj_key].append(m)

            project_metrics = [
                calculator.aggregate_project_metrics(metrics, proj_key)
                for proj_key, metrics in issues_by_project.items()
            ]
            person_metrics = calculator.aggregate_person_metrics(issue_metrics)
            type_metrics = calculator.aggregate_type_metrics(issue_metrics)

            project_file = metrics_exporter.export_project_metrics(project_metrics)
            person_file = metrics_exporter.export_person_metrics(person_metrics)
            type_file = metrics_exporter.export_type_metrics(type_metrics)

            output.log(f"Exported project metrics to {project_file}", "success")
            output.log(f"Exported person metrics to {person_file}", "success")
            output.log(f"Exported type metrics to {type_file}", "success")

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
