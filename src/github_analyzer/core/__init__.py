"""Core module - Shared exceptions and utilities.

Public exports:
- GitHubAnalyzerError: Base exception class
- ConfigurationError: Configuration-related errors
- ValidationError: Input validation errors
- APIError: API communication errors
- RateLimitError: Rate limit exceeded
- mask_token: Token masking utility
"""

from src.github_analyzer.core.exceptions import (
    APIError,
    ConfigurationError,
    GitHubAnalyzerError,
    RateLimitError,
    ValidationError,
    mask_token,
)

__all__ = [
    "GitHubAnalyzerError",
    "ConfigurationError",
    "ValidationError",
    "APIError",
    "RateLimitError",
    "mask_token",
]
