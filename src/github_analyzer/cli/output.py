"""Terminal output formatting.

This module provides utilities for formatted terminal output
including colors, banners, progress indicators, and logging.
"""

from __future__ import annotations

import sys
from datetime import datetime


class Colors:
    """ANSI color codes for terminal output.

    Provides color constants for consistent terminal formatting.
    Colors are automatically disabled if output is not a TTY.
    """

    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[35m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    ORANGE = "\033[38;5;208m"
    PINK = "\033[38;5;205m"
    PURPLE = "\033[38;5;141m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    @classmethod
    def disable(cls) -> None:
        """Disable all colors (for non-TTY output)."""
        cls.HEADER = ""
        cls.BLUE = ""
        cls.CYAN = ""
        cls.GREEN = ""
        cls.YELLOW = ""
        cls.RED = ""
        cls.MAGENTA = ""
        cls.BRIGHT_MAGENTA = ""
        cls.BRIGHT_CYAN = ""
        cls.BRIGHT_GREEN = ""
        cls.BRIGHT_YELLOW = ""
        cls.ORANGE = ""
        cls.PINK = ""
        cls.PURPLE = ""
        cls.BOLD = ""
        cls.DIM = ""
        cls.RESET = ""


# Disable colors if not TTY
if not sys.stdout.isatty():
    Colors.disable()


class TerminalOutput:
    """Formatted terminal output for the analyzer.

    Provides methods for consistent, colorized output including
    banners, log messages, progress indicators, and summaries.
    """

    def __init__(self, verbose: bool = True) -> None:
        """Initialize terminal output.

        Args:
            verbose: Whether to show verbose output.
        """
        self._verbose = verbose

    def banner(self) -> None:
        """Print welcome banner."""
        # Gradient-style banner with vivid colors
        c = Colors
        print()
        print(f"{c.BOLD}{c.PURPLE}╔══════════════════════════════════════════════════════════════════════╗{c.RESET}")
        print(f"{c.BOLD}{c.PURPLE}║{c.RESET}                                                                      {c.BOLD}{c.PURPLE}║{c.RESET}")
        print(f"{c.BOLD}{c.PURPLE}║{c.RESET}  {c.BOLD}{c.BRIGHT_CYAN}██████{c.RESET}  {c.BOLD}{c.BRIGHT_CYAN}███████{c.RESET} {c.BOLD}{c.BRIGHT_CYAN}██{c.RESET}    {c.BOLD}{c.BRIGHT_CYAN}██{c.RESET}                                         {c.BOLD}{c.PURPLE}   ║{c.RESET}")
        print(f"{c.BOLD}{c.PURPLE}║{c.RESET}  {c.BOLD}{c.BRIGHT_CYAN}██{c.RESET}   {c.BOLD}{c.BRIGHT_CYAN}██{c.RESET} {c.BOLD}{c.BRIGHT_CYAN}██{c.RESET}      {c.BOLD}{c.BRIGHT_CYAN}██{c.RESET}    {c.BOLD}{c.BRIGHT_CYAN}██{c.RESET}                                         {c.BOLD}{c.PURPLE}   ║{c.RESET}")
        print(f"{c.BOLD}{c.PURPLE}║{c.RESET}  {c.BOLD}{c.BRIGHT_CYAN}██{c.RESET}   {c.BOLD}{c.BRIGHT_CYAN}██{c.RESET} {c.BOLD}{c.BRIGHT_CYAN}█████{c.RESET}   {c.BOLD}{c.BRIGHT_CYAN}██{c.RESET}    {c.BOLD}{c.BRIGHT_CYAN}██{c.RESET}                                         {c.BOLD}{c.PURPLE}   ║{c.RESET}")
        print(f"{c.BOLD}{c.PURPLE}║{c.RESET}  {c.BOLD}{c.BRIGHT_CYAN}██{c.RESET}   {c.BOLD}{c.BRIGHT_CYAN}██{c.RESET} {c.BOLD}{c.BRIGHT_CYAN}██{c.RESET}       {c.BOLD}{c.BRIGHT_CYAN}██{c.RESET}  {c.BOLD}{c.BRIGHT_CYAN}██{c.RESET}                                          {c.BOLD}{c.PURPLE}   ║{c.RESET}")
        print(f"{c.BOLD}{c.PURPLE}║{c.RESET}  {c.BOLD}{c.BRIGHT_CYAN}██████{c.RESET}  {c.BOLD}{c.BRIGHT_CYAN}███████{c.RESET}  {c.BOLD}{c.BRIGHT_CYAN}████{c.RESET}                                           {c.BOLD}{c.PURPLE}    ║{c.RESET}")
        print(f"{c.BOLD}{c.PURPLE}║{c.RESET}                                                                      {c.BOLD}{c.PURPLE}║{c.RESET}")
        print(f"{c.BOLD}{c.PURPLE}║{c.RESET}   {c.BOLD}{c.ORANGE}█████{c.RESET}  {c.BOLD}{c.ORANGE}███{c.RESET}    {c.BOLD}{c.ORANGE}██{c.RESET}  {c.BOLD}{c.ORANGE}█████{c.RESET}  {c.BOLD}{c.ORANGE}██{c.RESET}      {c.BOLD}{c.ORANGE}██{c.RESET}    {c.BOLD}{c.ORANGE}██{c.RESET} {c.BOLD}{c.ORANGE}███████{c.RESET} {c.BOLD}{c.ORANGE}███████{c.RESET} {c.BOLD}{c.ORANGE}██████{c.RESET}   {c.BOLD}{c.PURPLE}║{c.RESET}")
        print(f"{c.BOLD}{c.PURPLE}║{c.RESET}  {c.BOLD}{c.ORANGE}██{c.RESET}   {c.BOLD}{c.ORANGE}██{c.RESET} {c.BOLD}{c.ORANGE}████{c.RESET}   {c.BOLD}{c.ORANGE}██{c.RESET} {c.BOLD}{c.ORANGE}██{c.RESET}   {c.BOLD}{c.ORANGE}██{c.RESET} {c.BOLD}{c.ORANGE}██{c.RESET}       {c.BOLD}{c.ORANGE}██{c.RESET}  {c.BOLD}{c.ORANGE}██{c.RESET}     {c.BOLD}{c.ORANGE}███{c.RESET}  {c.BOLD}{c.ORANGE}██{c.RESET}      {c.BOLD}{c.ORANGE}██{c.RESET}   {c.BOLD}{c.ORANGE}██{c.RESET}  {c.BOLD}{c.PURPLE}║{c.RESET}")
        print(f"{c.BOLD}{c.PURPLE}║{c.RESET}  {c.BOLD}{c.ORANGE}███████{c.RESET} {c.BOLD}{c.ORANGE}██{c.RESET} {c.BOLD}{c.ORANGE}██{c.RESET}  {c.BOLD}{c.ORANGE}██{c.RESET} {c.BOLD}{c.ORANGE}███████{c.RESET} {c.BOLD}{c.ORANGE}██{c.RESET}        {c.BOLD}{c.ORANGE}████{c.RESET}     {c.BOLD}{c.ORANGE}███{c.RESET}   {c.BOLD}{c.ORANGE}█████{c.RESET}   {c.BOLD}{c.ORANGE}██████{c.RESET}   {c.BOLD}{c.PURPLE}║{c.RESET}")
        print(f"{c.BOLD}{c.PURPLE}║{c.RESET}  {c.BOLD}{c.ORANGE}██{c.RESET}   {c.BOLD}{c.ORANGE}██{c.RESET} {c.BOLD}{c.ORANGE}██{c.RESET}  {c.BOLD}{c.ORANGE}██{c.RESET} {c.BOLD}{c.ORANGE}██{c.RESET} {c.BOLD}{c.ORANGE}██{c.RESET}   {c.BOLD}{c.ORANGE}██{c.RESET} {c.BOLD}{c.ORANGE}██{c.RESET}         {c.BOLD}{c.ORANGE}██{c.RESET}     {c.BOLD}{c.ORANGE}███{c.RESET}    {c.BOLD}{c.ORANGE}██{c.RESET}      {c.BOLD}{c.ORANGE}██{c.RESET}   {c.BOLD}{c.ORANGE}██{c.RESET}  {c.BOLD}{c.PURPLE}║{c.RESET}")
        print(f"{c.BOLD}{c.PURPLE}║{c.RESET}  {c.BOLD}{c.ORANGE}██{c.RESET}   {c.BOLD}{c.ORANGE}██{c.RESET} {c.BOLD}{c.ORANGE}██{c.RESET}   {c.BOLD}{c.ORANGE}████{c.RESET} {c.BOLD}{c.ORANGE}██{c.RESET}   {c.BOLD}{c.ORANGE}██{c.RESET} {c.BOLD}{c.ORANGE}███████{c.RESET}    {c.BOLD}{c.ORANGE}██{c.RESET}    {c.BOLD}{c.ORANGE}███████{c.RESET} {c.BOLD}{c.ORANGE}███████{c.RESET} {c.BOLD}{c.ORANGE}██{c.RESET}   {c.BOLD}{c.ORANGE}██{c.RESET}  {c.BOLD}{c.PURPLE}║{c.RESET}")
        print(f"{c.BOLD}{c.PURPLE}║{c.RESET}                                                                      {c.BOLD}{c.PURPLE}║{c.RESET}")
        print(f"{c.BOLD}{c.PURPLE}╚══════════════════════════════════════════════════════════════════════╝{c.RESET}")
        print()
        print(f"  {c.DIM}Analyze GitHub repositories and Jira projects, export to CSV{c.RESET}")
        print()

    def features(self) -> None:
        """Print tool features."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}📊 WHAT THIS TOOL DOES:{Colors.RESET}")
        features = [
            "📈 Commit Analysis - Track commits with stats, merge/revert detection",
            "🔀 Pull Request Metrics - PR workflow, merge times, review coverage",
            "🐛 GitHub Issues - Resolution times, categorization, closure rates",
            "🎫 Jira Integration - Extract issues and comments from Jira Cloud/Server",
            "👥 Contributor Insights - Top contributors with productivity scores",
            "📊 Quality Metrics - Code quality assessment and scoring",
            "📁 CSV Export - All data exported to CSV for analysis",
        ]
        for feature in features:
            print(f"   {feature}")
        print()

    def log(
        self,
        message: str,
        level: str = "info",
        timestamp: bool = True,
    ) -> None:
        """Print log message with optional timestamp and color.

        Args:
            message: Message to display.
            level: Log level (info, success, warning, error).
            timestamp: Whether to show timestamp.
        """
        if not self._verbose and level == "info":
            return

        colors = {
            "info": Colors.CYAN,
            "success": Colors.GREEN,
            "warning": Colors.YELLOW,
            "error": Colors.RED,
        }
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
        }

        color = colors.get(level, Colors.RESET)
        icon = icons.get(level, "")

        if timestamp:
            ts = datetime.now().strftime("%H:%M:%S")
            prefix = f"{Colors.DIM}[{ts}]{Colors.RESET} "
        else:
            prefix = ""

        print(f"{prefix}{color}{icon} {message}{Colors.RESET}")

    def progress(self, current: int, total: int, label: str) -> None:
        """Print progress indicator.

        Args:
            current: Current item number.
            total: Total items.
            label: Label to display.
        """
        pct = (current / total * 100) if total > 0 else 0
        bar_width = 30
        filled = int(bar_width * current / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_width - filled)

        print(
            f"\r{Colors.CYAN}[{bar}] {pct:5.1f}% - {label}{Colors.RESET}",
            end="",
            flush=True,
        )

        if current >= total:
            print()  # Newline at completion

    def section(self, title: str) -> None:
        """Print section header.

        Args:
            title: Section title.
        """
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'═' * 60}{Colors.RESET}\n")

    def summary(self, stats: dict) -> None:
        """Print final summary.

        Args:
            stats: Summary statistics dictionary.
        """
        self.section("📊 ANALYSIS SUMMARY")

        # Repository stats
        if "repositories" in stats:
            print(f"{Colors.BOLD}Repositories Analyzed:{Colors.RESET} {stats['repositories']}")

        # Commit stats
        if "commits" in stats:
            commits = stats["commits"]
            print(f"\n{Colors.BOLD}📝 Commits:{Colors.RESET}")
            print(f"   Total: {commits.get('total', 0)}")
            print(f"   Merge commits: {commits.get('merge_commits', 0)}")
            print(f"   Reverts: {commits.get('revert_commits', 0)}")

        # PR stats
        if "prs" in stats:
            prs = stats["prs"]
            print(f"\n{Colors.BOLD}🔀 Pull Requests:{Colors.RESET}")
            print(f"   Total: {prs.get('total', 0)}")
            print(f"   Merged: {prs.get('merged', 0)}")
            print(f"   Open: {prs.get('open', 0)}")

        # Issue stats
        if "issues" in stats:
            issues = stats["issues"]
            print(f"\n{Colors.BOLD}🐛 Issues:{Colors.RESET}")
            print(f"   Total: {issues.get('total', 0)}")
            print(f"   Closed: {issues.get('closed', 0)}")
            print(f"   Open: {issues.get('open', 0)}")

        # Files generated
        if "files" in stats:
            print(f"\n{Colors.BOLD}📁 Files Generated:{Colors.RESET}")
            for filepath in stats["files"]:
                print(f"   • {filepath}")

        print()

    def error(self, message: str, details: str | None = None) -> None:
        """Print error message.

        Args:
            message: Error message.
            details: Additional details.
        """
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Error: {message}{Colors.RESET}")
        if details:
            print(f"{Colors.DIM}   {details}{Colors.RESET}")
        print()

    def success(self, message: str) -> None:
        """Print success message.

        Args:
            message: Success message.
        """
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ {message}{Colors.RESET}\n")
