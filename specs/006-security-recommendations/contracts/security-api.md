# Internal API Contract: Security Utilities

**Module**: `src/github_analyzer/core/security.py`
**Version**: 1.0.0
**Date**: 2025-11-29

## Overview

This module provides security utilities for the GitHub Analyzer application. All functions are designed for internal use and follow the constitution's security-first principle.

---

## Path Validation API

### `validate_output_path`

Validates that an output path is within the safe boundary.

```python
def validate_output_path(
    path: str | Path,
    base_dir: Path | None = None,
) -> Path:
    """
    Validate output path is within safe boundary.

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
```

**Behavior**:
- Resolves path using `Path.resolve()` (handles symlinks)
- Checks containment using `is_relative_to()`
- Returns resolved `Path` on success
- Raises `ValidationError` on failure

---

## CSV Security API

### `escape_csv_formula`

Escapes a single cell value to prevent formula injection.

```python
def escape_csv_formula(value: Any) -> str:
    """
    Escape cell value to prevent CSV formula injection.

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
```

**Behavior**:
- Converts non-string values to string first
- Prefixes with `'` if first character is in `=+-@\t\r`
- Returns unchanged if no trigger character
- Empty strings returned as-is

### `escape_csv_row`

Escapes all values in a dictionary row.

```python
def escape_csv_row(row: dict[str, Any]) -> dict[str, str]:
    """
    Escape all values in a CSV row dictionary.

    Args:
        row: Dictionary of column names to values.

    Returns:
        Dictionary with all values escaped.

    Example:
        >>> escape_csv_row({"name": "=DROP TABLE", "count": 42})
        {"name": "'=DROP TABLE", "count": "42"}
    """
```

---

## File Permission API

### `check_file_permissions`

Checks if a file has overly permissive permissions (Unix only).

```python
def check_file_permissions(
    filepath: Path,
    logger: logging.Logger | None = None,
) -> bool:
    """
    Check if file has secure permissions (Unix only).

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
```

**Behavior**:
- Returns `True` on Windows (skipped)
- Checks for `S_IROTH` (world-readable) and `S_IRGRP` (group-readable)
- Logs `[SECURITY]` warning if permissive
- Returns `False` if warning was logged

### `set_secure_permissions`

Sets restrictive permissions on a file (Unix only).

```python
def set_secure_permissions(
    filepath: Path,
    mode: int = 0o600,
) -> bool:
    """
    Set secure permissions on a file (Unix only).

    Args:
        filepath: Path to modify.
        mode: Permission mode (default: 0o600).

    Returns:
        True if successful or on Windows.
        False on error.
    """
```

---

## Response Header API

### `validate_content_type`

Validates Content-Type header matches expected value.

```python
def validate_content_type(
    headers: dict[str, str],
    expected: str = "application/json",
    logger: logging.Logger | None = None,
) -> bool:
    """
    Validate response Content-Type header.

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
```

---

## Audit Logging API

### `log_api_request`

Logs an API request for verbose mode.

```python
def log_api_request(
    method: str,
    url: str,
    status_code: int,
    logger: logging.Logger,
    response_time_ms: float | None = None,
) -> None:
    """
    Log API request details (for verbose mode).

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
```

**Behavior**:
- Masks any tokens that might appear in URL (defense-in-depth)
- Uses `[API]` prefix for audit logs
- Includes response time if provided

---

## Timeout Validation API

### `validate_timeout`

Warns if timeout exceeds recommended threshold.

```python
def validate_timeout(
    timeout: int,
    logger: logging.Logger | None = None,
    threshold: int | None = None,
) -> None:
    """
    Warn if timeout exceeds recommended threshold.

    Args:
        timeout: Configured timeout in seconds.
        logger: Optional logger for warnings.
        threshold: Custom threshold (default: 60s or env var).

    Example:
        >>> validate_timeout(120, logger=log)
        # Logs: [SECURITY] Timeout of 120s exceeds recommended threshold (60s)
    """
```

---

## Constants

```python
# Formula injection triggers
FORMULA_TRIGGERS: frozenset[str] = frozenset("=+-@\t\r")

# Security log prefix
SECURITY_LOG_PREFIX: str = "[SECURITY]"

# API log prefix
API_LOG_PREFIX: str = "[API]"

# Default timeout warning threshold (seconds)
DEFAULT_TIMEOUT_WARN_THRESHOLD: int = 60

# Default secure file permissions
DEFAULT_SECURE_MODE: int = 0o600
```

---

## Error Types

This module raises:
- `ValidationError` (from `core.exceptions`): For path validation failures

All other issues are handled via warnings/logging to maintain availability.
