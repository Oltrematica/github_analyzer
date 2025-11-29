"""Core module - Shared exceptions and utilities.

Public exports:
- GitHubAnalyzerError: Base exception class
- ConfigurationError: Configuration-related errors
- ValidationError: Input validation errors
- APIError: API communication errors
- RateLimitError: Rate limit exceeded
- mask_token: Token masking utility

Security utilities:
- validate_output_path: Prevent path traversal attacks
- escape_csv_formula: Prevent CSV formula injection
- escape_csv_row: Escape all values in a CSV row
- check_file_permissions: Warn about overly permissive files
- set_secure_permissions: Set restrictive file permissions
- validate_content_type: Validate API response headers
- log_api_request: Audit log for API calls
- validate_timeout: Warn about excessive timeout values

Security constants:
- FORMULA_TRIGGERS: Characters that trigger formula injection
- SECURITY_LOG_PREFIX: Prefix for security warnings
- API_LOG_PREFIX: Prefix for API audit logs
- DEFAULT_TIMEOUT_WARN_THRESHOLD: Default timeout warning threshold
- DEFAULT_SECURE_MODE: Default secure file permission mode
"""

from src.github_analyzer.core.exceptions import (
    APIError,
    ConfigurationError,
    GitHubAnalyzerError,
    RateLimitError,
    ValidationError,
    mask_token,
)
from src.github_analyzer.core.security import (
    API_LOG_PREFIX,
    DEFAULT_SECURE_MODE,
    DEFAULT_TIMEOUT_WARN_THRESHOLD,
    FORMULA_TRIGGERS,
    SECURITY_LOG_PREFIX,
    check_file_permissions,
    escape_csv_formula,
    escape_csv_row,
    log_api_request,
    set_secure_permissions,
    validate_content_type,
    validate_output_path,
    validate_timeout,
)

__all__ = [
    # Exceptions
    "GitHubAnalyzerError",
    "ConfigurationError",
    "ValidationError",
    "APIError",
    "RateLimitError",
    "mask_token",
    # Security functions
    "validate_output_path",
    "escape_csv_formula",
    "escape_csv_row",
    "check_file_permissions",
    "set_secure_permissions",
    "validate_content_type",
    "log_api_request",
    "validate_timeout",
    # Security constants
    "FORMULA_TRIGGERS",
    "SECURITY_LOG_PREFIX",
    "API_LOG_PREFIX",
    "DEFAULT_TIMEOUT_WARN_THRESHOLD",
    "DEFAULT_SECURE_MODE",
]
