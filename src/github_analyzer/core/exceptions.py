"""Custom exceptions for GitHub Analyzer.

This module defines the exception hierarchy used throughout the application.
All exceptions inherit from GitHubAnalyzerError to enable catching any
analyzer-related error.

Exception Hierarchy:
    GitHubAnalyzerError (base)
    ├── ConfigurationError (exit code 1)
    ├── ValidationError (exit code 1)
    └── APIError (exit code 2)
        └── RateLimitError (exit code 2)
"""

from __future__ import annotations


class GitHubAnalyzerError(Exception):
    """Base exception for all GitHub Analyzer errors.

    Attributes:
        message: Human-readable error description.
        details: Additional context for debugging (optional).
        exit_code: Process exit code when this error causes termination.
    """

    exit_code: int = 1

    def __init__(self, message: str, details: str | None = None) -> None:
        """Initialize the error.

        Args:
            message: Human-readable error description.
            details: Additional context for debugging.
        """
        self.message = message
        self.details = details
        super().__init__(message)

    def __str__(self) -> str:
        """Return string representation without exposing sensitive data."""
        if self.details:
            return f"{self.message} ({self.details})"
        return self.message


class ConfigurationError(GitHubAnalyzerError):
    """Raised when configuration is invalid or missing.

    Examples:
        - GITHUB_TOKEN environment variable not set
        - repos.txt file not found
        - Invalid configuration values
    """

    exit_code = 1


class ValidationError(GitHubAnalyzerError):
    """Raised when input validation fails.

    Examples:
        - Invalid repository format
        - Repository name contains dangerous characters
        - Token format validation failed
    """

    exit_code = 1


class APIError(GitHubAnalyzerError):
    """Raised when GitHub API communication fails.

    Examples:
        - Network connection error
        - HTTP 4xx/5xx responses
        - JSON parsing errors
    """

    exit_code = 2

    def __init__(
        self,
        message: str,
        details: str | None = None,
        status_code: int | None = None,
    ) -> None:
        """Initialize API error.

        Args:
            message: Human-readable error description.
            details: Additional context for debugging.
            status_code: HTTP status code if applicable.
        """
        super().__init__(message, details)
        self.status_code = status_code


class RateLimitError(APIError):
    """Raised when GitHub API rate limit is exceeded.

    The reset_time attribute indicates when the rate limit will reset.
    """

    exit_code = 2

    def __init__(
        self,
        message: str = "GitHub API rate limit exceeded",
        details: str | None = None,
        reset_time: int | None = None,
    ) -> None:
        """Initialize rate limit error.

        Args:
            message: Human-readable error description.
            details: Additional context for debugging.
            reset_time: Unix timestamp when rate limit resets.
        """
        super().__init__(message, details, status_code=403)
        self.reset_time = reset_time


def mask_token(value: str) -> str:  # noqa: ARG001
    """Mask a token value for safe logging.

    This function ensures that token values are never exposed in logs
    or error messages. It returns a fixed string regardless of input.

    Args:
        value: The token value to mask.

    Returns:
        A masked string that doesn't reveal the token.
    """
    # Never reveal any part of the token
    return "[MASKED]"
