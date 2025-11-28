"""Configuration settings for GitHub Analyzer.

This module provides the AnalyzerConfig dataclass for managing
application configuration. Configuration is loaded from environment
variables to ensure security of credentials.

Security Notes:
- Tokens are NEVER logged, printed, or exposed in error messages
- Token values are masked in string representations
- Token is loaded from GITHUB_TOKEN environment variable only
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from src.github_analyzer.core.exceptions import ConfigurationError, ValidationError, mask_token


def _get_bool_env(key: str, default: bool) -> bool:
    """Get boolean value from environment variable.

    Args:
        key: Environment variable name.
        default: Default value if not set.

    Returns:
        Boolean value from environment or default.
    """
    value = os.environ.get(key, "").lower()
    if value in ("true", "1", "yes", "on"):
        return True
    if value in ("false", "0", "no", "off"):
        return False
    return default


def _get_int_env(key: str, default: int) -> int:
    """Get integer value from environment variable.

    Args:
        key: Environment variable name.
        default: Default value if not set or invalid.

    Returns:
        Integer value from environment or default.
    """
    value = os.environ.get(key, "")
    try:
        return int(value) if value else default
    except ValueError:
        return default


@dataclass
class AnalyzerConfig:
    """Immutable configuration for the GitHub Analyzer.

    All configuration is loaded from environment variables.
    The github_token is required and must be set via GITHUB_TOKEN.

    Attributes:
        github_token: GitHub Personal Access Token (required).
        output_dir: Directory for CSV output files.
        repos_file: Path to repository list file.
        days: Number of days to analyze.
        per_page: Items per API page (1-100).
        verbose: Enable verbose output.
        timeout: HTTP request timeout in seconds.
        max_pages: Maximum pages to fetch per endpoint.

    Example:
        >>> config = AnalyzerConfig.from_env()
        >>> print(config.days)
        30
    """

    github_token: str
    output_dir: str = "github_export"
    repos_file: str = "repos.txt"
    days: int = 30
    per_page: int = 100
    verbose: bool = True
    timeout: int = 30
    max_pages: int = 50
    _validated: bool = field(default=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        # Strip whitespace from token
        object.__setattr__(self, "github_token", self.github_token.strip())

    @classmethod
    def from_env(cls) -> AnalyzerConfig:
        """Load configuration from environment variables.

        Required environment variables:
            GITHUB_TOKEN: GitHub Personal Access Token

        Optional environment variables:
            GITHUB_ANALYZER_OUTPUT_DIR: Output directory (default: github_export)
            GITHUB_ANALYZER_REPOS_FILE: Repository file (default: repos.txt)
            GITHUB_ANALYZER_DAYS: Analysis period in days (default: 30)
            GITHUB_ANALYZER_PER_PAGE: Items per page (default: 100)
            GITHUB_ANALYZER_VERBOSE: Enable verbose output (default: true)
            GITHUB_ANALYZER_TIMEOUT: Request timeout (default: 30)
            GITHUB_ANALYZER_MAX_PAGES: Max pages to fetch (default: 50)

        Returns:
            AnalyzerConfig instance with values from environment.

        Raises:
            ConfigurationError: If GITHUB_TOKEN is not set or empty.
        """
        # Get token from environment
        token = os.environ.get("GITHUB_TOKEN", "").strip()

        if not token:
            raise ConfigurationError(
                "GITHUB_TOKEN environment variable not set",
                details="Set the GITHUB_TOKEN environment variable with your GitHub Personal Access Token. "
                "See: https://github.com/settings/tokens",
            )

        return cls(
            github_token=token,
            output_dir=os.environ.get("GITHUB_ANALYZER_OUTPUT_DIR", "github_export"),
            repos_file=os.environ.get("GITHUB_ANALYZER_REPOS_FILE", "repos.txt"),
            days=_get_int_env("GITHUB_ANALYZER_DAYS", 30),
            per_page=_get_int_env("GITHUB_ANALYZER_PER_PAGE", 100),
            verbose=_get_bool_env("GITHUB_ANALYZER_VERBOSE", True),
            timeout=_get_int_env("GITHUB_ANALYZER_TIMEOUT", 30),
            max_pages=_get_int_env("GITHUB_ANALYZER_MAX_PAGES", 50),
        )

    def validate(self) -> None:
        """Validate all configuration values.

        Validates:
            - Token format (prefix and minimum length)
            - days is positive and <= 365
            - per_page is between 1 and 100
            - timeout is positive and <= 300

        Raises:
            ValidationError: If any value is invalid.
        """
        from src.github_analyzer.config.validation import validate_token_format

        # Validate token format (never include token in error)
        if not validate_token_format(self.github_token):
            raise ValidationError(
                "Invalid GitHub token format",
                details="Token should start with 'ghp_', 'gho_', or 'github_pat_' prefix",
            )

        # Validate days
        if self.days <= 0:
            raise ValidationError(
                f"Invalid days value: {self.days}",
                details="Days must be a positive integer",
            )
        if self.days > 365:
            raise ValidationError(
                f"Days value too large: {self.days}",
                details="Maximum analysis period is 365 days",
            )

        # Validate per_page
        if self.per_page < 1 or self.per_page > 100:
            raise ValidationError(
                f"Invalid per_page value: {self.per_page}",
                details="per_page must be between 1 and 100 (GitHub API limit)",
            )

        # Validate timeout
        if self.timeout <= 0:
            raise ValidationError(
                f"Invalid timeout value: {self.timeout}",
                details="Timeout must be a positive integer",
            )
        if self.timeout > 300:
            raise ValidationError(
                f"Timeout value too large: {self.timeout}",
                details="Maximum timeout is 300 seconds",
            )

        object.__setattr__(self, "_validated", True)

    def __repr__(self) -> str:
        """Return string representation with masked token."""
        return (
            f"AnalyzerConfig("
            f"github_token={mask_token(self.github_token)!r}, "
            f"output_dir={self.output_dir!r}, "
            f"repos_file={self.repos_file!r}, "
            f"days={self.days}, "
            f"per_page={self.per_page}, "
            f"verbose={self.verbose}, "
            f"timeout={self.timeout}, "
            f"max_pages={self.max_pages})"
        )

    def __str__(self) -> str:
        """Return user-friendly string representation."""
        return (
            f"GitHub Analyzer Config:\n"
            f"  Token: {mask_token(self.github_token)}\n"
            f"  Output: {self.output_dir}\n"
            f"  Repos file: {self.repos_file}\n"
            f"  Period: {self.days} days\n"
            f"  Verbose: {self.verbose}"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary with masked token.

        Returns:
            Dictionary representation safe for logging.
        """
        return {
            "github_token": mask_token(self.github_token),
            "output_dir": self.output_dir,
            "repos_file": self.repos_file,
            "days": self.days,
            "per_page": self.per_page,
            "verbose": self.verbose,
            "timeout": self.timeout,
            "max_pages": self.max_pages,
        }
