"""CLI module - Command-line interface.

Public exports:
- main: Entry point function
- GitHubAnalyzer: Main orchestrator class
- TerminalOutput: Terminal output utilities
- Colors: ANSI color codes
"""

from src.github_analyzer.cli.main import GitHubAnalyzer, main
from src.github_analyzer.cli.output import Colors, TerminalOutput

__all__ = [
    "main",
    "GitHubAnalyzer",
    "TerminalOutput",
    "Colors",
]
