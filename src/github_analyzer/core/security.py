"""Security utilities for GitHub Analyzer.

This module provides security functions for input validation, output sanitization,
and audit logging. All functions follow the constitution's security-first principle.

Public exports:
- validate_output_path: Prevent path traversal attacks
- escape_csv_formula: Prevent CSV formula injection
- escape_csv_row: Escape all values in a CSV row
- check_file_permissions: Warn about overly permissive files
- set_secure_permissions: Set restrictive file permissions
- validate_content_type: Validate API response headers
- log_api_request: Audit log for API calls (verbose mode)
- validate_timeout: Warn about excessive timeout values

Constants:
- FORMULA_TRIGGERS: Characters that trigger formula injection
- SECURITY_LOG_PREFIX: Prefix for security warnings
- API_LOG_PREFIX: Prefix for API audit logs
- DEFAULT_TIMEOUT_WARN_THRESHOLD: Default timeout warning threshold
- DEFAULT_SECURE_MODE: Default secure file permission mode
"""

from __future__ import annotations

import logging
import os
import platform
import re
import stat
from pathlib import Path
from typing import Any

from src.github_analyzer.core.exceptions import ValidationError

# Formula injection triggers (=, +, -, @, TAB, CR)
FORMULA_TRIGGERS: frozenset[str] = frozenset("=+-@\t\r")

# Security log prefix for warnings
SECURITY_LOG_PREFIX: str = "[SECURITY]"

# API log prefix for audit logs
API_LOG_PREFIX: str = "[API]"

# Default timeout warning threshold (seconds)
DEFAULT_TIMEOUT_WARN_THRESHOLD: int = 60

# Default secure file permissions (owner read/write only)
DEFAULT_SECURE_MODE: int = 0o600

# Environment variable for timeout warning threshold
TIMEOUT_THRESHOLD_ENV_VAR: str = "GITHUB_ANALYZER_TIMEOUT_WARN_THRESHOLD"

# Pattern to match potential tokens in URLs (defense-in-depth)
_TOKEN_PATTERN: re.Pattern[str] = re.compile(
    r"(ghp_[a-zA-Z0-9]+|gho_[a-zA-Z0-9]+|github_pat_[a-zA-Z0-9_]+|"
    r"[a-f0-9]{40}|Bearer\s+[^\s]+)",
    re.IGNORECASE,
)


def validate_output_path(
    path: str | Path,
    base_dir: Path | None = None,
) -> Path:
    """Validate output path is within safe boundary.

    Resolves the path (including symlinks) and checks it's within the
    allowed base directory to prevent path traversal attacks.

    Args:
        path: The path to validate (string or Path).
        base_dir: Safe boundary directory. Defaults to current working directory.

    Returns:
        Resolved Path object if valid.

    Raises:
        ValidationError: If path is outside safe boundary.

    Example:
        >>> validate_output_path("./reports")
        PosixPath('/home/user/project/reports')

        >>> validate_output_path("../../../etc")
        ValidationError: Output path must be within /home/user/project
    """
    if base_dir is None:
        base_dir = Path.cwd()

    # Resolve both paths to handle symlinks (FR-013)
    resolved_base = base_dir.resolve()

    # Convert path to Path object
    path_obj = Path(path)

    # For relative paths, resolve against the base directory
    if not path_obj.is_absolute():
        resolved_path = (resolved_base / path_obj).resolve()
    else:
        resolved_path = path_obj.resolve()

    # Check if path is within safe boundary
    try:
        resolved_path.relative_to(resolved_base)
    except ValueError as err:
        raise ValidationError(f"Output path must be within {resolved_base}") from err

    return resolved_path


def escape_csv_formula(value: Any) -> str:
    """Escape cell value to prevent CSV formula injection.

    Prefixes values starting with formula trigger characters (=, +, -, @, TAB, CR)
    with a single quote to prevent spreadsheet applications from interpreting
    them as formulas.

    Args:
        value: Cell value to escape.

    Returns:
        Escaped string value.

    Example:
        >>> escape_csv_formula("=SUM(A1:A10)")
        "'=SUM(A1:A10)"

        >>> escape_csv_formula("Normal text")
        "Normal text"

        >>> escape_csv_formula(42)
        "42"
    """
    # Convert to string first
    str_value = str(value) if value is not None else ""

    # Empty strings returned as-is
    if not str_value:
        return str_value

    # Check if first character is a formula trigger
    if str_value[0] in FORMULA_TRIGGERS:
        return f"'{str_value}"

    return str_value


def escape_csv_row(row: dict[str, Any]) -> dict[str, str]:
    """Escape all values in a CSV row dictionary.

    Applies formula injection protection to every value in the row.

    Args:
        row: Dictionary of column names to values.

    Returns:
        Dictionary with all values escaped.

    Example:
        >>> escape_csv_row({"name": "=DROP TABLE", "count": 42})
        {"name": "'=DROP TABLE", "count": "42"}
    """
    return {key: escape_csv_formula(value) for key, value in row.items()}


def check_file_permissions(
    filepath: Path,
    logger: logging.Logger | None = None,
) -> bool:
    """Check if file has secure permissions (Unix only).

    Warns if the file is readable by group or world users, which could
    expose sensitive data on shared systems.

    Args:
        filepath: Path to check.
        logger: Optional logger for warnings.

    Returns:
        True if permissions are secure or on Windows.
        False if permissions are too permissive.

    Example:
        >>> check_file_permissions(Path("repos.txt"), logger)
        # If world-readable: logs warning, returns False
        # If owner-only: returns True
    """
    # Skip on Windows (different ACL model)
    if platform.system() == "Windows":
        return True

    try:
        file_stat = filepath.stat()
        mode = file_stat.st_mode

        # Check for world-readable or group-readable
        is_world_readable = bool(mode & stat.S_IROTH)
        is_group_readable = bool(mode & stat.S_IRGRP)

        if is_world_readable or is_group_readable:
            if logger:
                permission_str = oct(mode)[-3:]
                logger.warning(
                    f"{SECURITY_LOG_PREFIX} File '{filepath}' has permissive "
                    f"permissions ({permission_str}). Consider using mode 600 "
                    "for sensitive files."
                )
            return False

        return True
    except OSError:
        # File doesn't exist or can't be accessed - graceful degradation
        return True


def set_secure_permissions(
    filepath: Path,
    mode: int = DEFAULT_SECURE_MODE,
) -> bool:
    """Set secure permissions on a file (Unix only).

    Args:
        filepath: Path to modify.
        mode: Permission mode (default: 0o600).

    Returns:
        True if successful or on Windows.
        False on error.
    """
    # Skip on Windows (different ACL model)
    if platform.system() == "Windows":
        return True

    try:
        filepath.chmod(mode)
        return True
    except OSError:
        # Graceful degradation - don't fail if permissions can't be set
        return False


def validate_content_type(
    headers: dict[str, str],
    expected: str = "application/json",
    logger: logging.Logger | None = None,
) -> bool:
    """Validate response Content-Type header.

    Checks if the Content-Type header contains the expected value.
    Logs a security warning if the header is missing or doesn't match.

    Args:
        headers: Response headers dictionary.
        expected: Expected Content-Type value.
        logger: Optional logger for warnings.

    Returns:
        True if Content-Type contains expected value.
        False otherwise (warning logged if logger provided).

    Example:
        >>> validate_content_type({"Content-Type": "application/json"}, logger=log)
        True

        >>> validate_content_type({"Content-Type": "text/html"}, logger=log)
        # Logs: [SECURITY] Unexpected Content-Type: text/html (expected application/json)
        False
    """
    # Case-insensitive header lookup
    content_type = None
    for key, value in headers.items():
        if key.lower() == "content-type":
            content_type = value
            break

    # Check for missing header (FR-006)
    if content_type is None:
        if logger:
            logger.warning(
                f"{SECURITY_LOG_PREFIX} Missing Content-Type header "
                f"(expected {expected})"
            )
        return False

    # Check if expected type is in Content-Type (handles charset, etc.)
    if expected in content_type:
        return True

    if logger:
        logger.warning(
            f"{SECURITY_LOG_PREFIX} Unexpected Content-Type: {content_type} "
            f"(expected {expected})"
        )
    return False


def _mask_url_tokens(url: str) -> str:
    """Mask any tokens that might appear in a URL.

    Defense-in-depth: Even though tokens shouldn't be in URLs,
    this provides an extra layer of protection.

    Args:
        url: URL string to mask.

    Returns:
        URL with any token-like strings replaced with [MASKED].
    """
    return _TOKEN_PATTERN.sub("[MASKED]", url)


def log_api_request(
    method: str,
    url: str,
    status_code: int,
    logger: logging.Logger,
    response_time_ms: float | None = None,
) -> None:
    """Log API request details (for verbose mode).

    Logs the HTTP method, URL (with tokens masked), and response status.
    Used for audit logging and debugging.

    Args:
        method: HTTP method (GET, POST, etc.).
        url: Request URL (tokens will be masked).
        status_code: Response status code.
        logger: Logger instance.
        response_time_ms: Optional response time in milliseconds.

    Example:
        >>> log_api_request("GET", "https://api.github.com/repos/org/repo", 200, log)
        # Logs: [API] GET https://api.github.com/repos/org/repo -> 200
    """
    # Mask any tokens that might appear in the URL (defense-in-depth)
    safe_url = _mask_url_tokens(url)

    if response_time_ms is not None:
        logger.info(
            f"{API_LOG_PREFIX} {method} {safe_url} -> {status_code} ({response_time_ms:.0f}ms)"
        )
    else:
        logger.info(f"{API_LOG_PREFIX} {method} {safe_url} -> {status_code}")


def validate_timeout(
    timeout: int,
    logger: logging.Logger | None = None,
    threshold: int | None = None,
) -> None:
    """Warn if timeout exceeds recommended threshold.

    Logs a security warning if the configured timeout is unusually long,
    which could indicate misconfiguration or security concerns.

    Args:
        timeout: Configured timeout in seconds.
        logger: Optional logger for warnings.
        threshold: Custom threshold. Defaults to GITHUB_ANALYZER_TIMEOUT_WARN_THRESHOLD
                   env var or DEFAULT_TIMEOUT_WARN_THRESHOLD (60s).

    Example:
        >>> validate_timeout(120, logger=log)
        # Logs: [SECURITY] Timeout of 120s exceeds recommended threshold (60s)
    """
    # Determine threshold
    if threshold is None:
        env_threshold = os.environ.get(TIMEOUT_THRESHOLD_ENV_VAR)
        if env_threshold:
            try:
                threshold = int(env_threshold)
            except ValueError:
                threshold = DEFAULT_TIMEOUT_WARN_THRESHOLD
        else:
            threshold = DEFAULT_TIMEOUT_WARN_THRESHOLD

    # Warn if timeout exceeds threshold
    if timeout > threshold and logger:
        logger.warning(
            f"{SECURITY_LOG_PREFIX} Timeout of {timeout}s exceeds recommended "
            f"threshold ({threshold}s). Long timeouts may have security implications."
        )
