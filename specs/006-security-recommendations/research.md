# Research: Security Recommendations Implementation

**Feature**: 006-security-recommendations
**Date**: 2025-11-29
**Status**: Complete

## Overview

This document consolidates research findings for implementing security recommendations from the SECURITY.md audit report.

---

## 1. Output Path Validation (Path Traversal Prevention)

### Decision
Use Python's `pathlib.Path.resolve()` combined with `is_relative_to()` to validate output paths against a safe boundary (current working directory by default).

### Rationale
- `Path.resolve()` normalizes the path and resolves all symlinks
- `is_relative_to()` (Python 3.9+) provides clean containment check
- This approach handles `..`, symlinks, and absolute paths uniformly
- Standard library solution, no external dependencies

### Alternatives Considered

| Alternative | Reason Rejected |
|-------------|-----------------|
| String-based `..` checking | Incomplete: doesn't handle symlinks or normalized paths |
| `os.path.commonprefix()` | Byte-level prefix matching is incorrect for paths |
| `realpath()` + string prefix | Less Pythonic, `is_relative_to()` is cleaner |
| Chroot/sandbox | Overkill for CLI tool, requires elevated permissions |

### Implementation Pattern
```python
def validate_output_path(path: str | Path, base_dir: Path | None = None) -> Path:
    """Validate output path is within safe boundary."""
    base = (base_dir or Path.cwd()).resolve()
    resolved = Path(path).resolve()
    if not resolved.is_relative_to(base):
        raise ValidationError(f"Output path must be within {base}")
    return resolved
```

---

## 2. Dependency Version Pinning

### Decision
Pin all dependencies with exact versions (`==`) in `requirements.txt`. Use `>=` with upper bounds in `requirements-dev.txt` for development tools.

### Rationale
- Exact pinning ensures reproducible builds
- Prevents supply chain attacks via malicious updates
- Enables `pip-audit` to scan specific versions
- Development tools can be more flexible as they don't affect runtime

### Alternatives Considered

| Alternative | Reason Rejected |
|-------------|-----------------|
| `>=` ranges only | Unpredictable installs, supply chain risk |
| `~=` compatible release | Still allows minor version drift |
| Poetry/pipenv lock files | Additional tooling complexity for simple CLI |
| No pinning | Violates constitution security principle |

### Implementation
```text
# requirements.txt
requests==2.31.0

# requirements-dev.txt
-r requirements.txt
pytest>=7.0.0,<9.0.0
pytest-cov>=4.0.0,<6.0.0
ruff>=0.1.0,<1.0.0
mypy>=1.0.0,<2.0.0
```

---

## 3. CSV Formula Injection Protection

### Decision
Prefix cell values starting with formula trigger characters (`=`, `+`, `-`, `@`, `\t`, `\r`) with a single quote (`'`). Apply only to string values.

### Rationale
- Industry-standard defense (OWASP recommendation)
- Single quote is ignored by spreadsheet apps but prevents formula execution
- Maintains CSV validity and parseability
- Data is recoverable (strip leading quote)

### Alternatives Considered

| Alternative | Reason Rejected |
|-------------|-----------------|
| Double-quote escaping | Only works for some spreadsheet apps |
| Prepend `\t` character | Less universal than single quote |
| Remove dangerous characters | Data loss, unacceptable |
| Warning only | Doesn't actually protect users |

### Implementation Pattern
```python
FORMULA_TRIGGERS = frozenset('=+-@\t\r')

def escape_csv_cell(value: Any) -> str:
    """Escape cell value to prevent formula injection."""
    if not isinstance(value, str):
        return str(value)
    if value and value[0] in FORMULA_TRIGGERS:
        return "'" + value
    return value
```

### Edge Cases
- Empty strings: Return as-is
- Non-string values: Convert to string first, then check
- Already quoted values: Don't double-quote

---

## 4. Response Header Validation (Content-Type Check)

### Decision
Log warning when `Content-Type` header doesn't contain expected value (e.g., `application/json`). Do not fail the request—treat as defense-in-depth.

### Rationale
- Detects potential MitM attacks or API misconfiguration
- Non-blocking preserves availability (graceful degradation)
- Logging enables investigation without disrupting operations
- Already have structured logging in place

### Alternatives Considered

| Alternative | Reason Rejected |
|-------------|-----------------|
| Reject non-matching responses | Too aggressive, could break on edge cases |
| Ignore entirely | Misses detection opportunity |
| Custom header validation library | Overkill for simple check |

### Implementation Pattern
```python
def validate_content_type(
    headers: dict[str, str],
    expected: str = "application/json",
    logger: logging.Logger | None = None
) -> bool:
    """Validate Content-Type header matches expected value."""
    content_type = headers.get("Content-Type", "")
    if expected not in content_type:
        if logger:
            logger.warning(
                "[SECURITY] Unexpected Content-Type: %s (expected %s)",
                content_type, expected
            )
        return False
    return True
```

---

## 5. File Permission Checks

### Decision
Check file permissions using `os.stat()` and warn if world-readable (`S_IROTH`) or group-readable (`S_IRGRP`) on sensitive input files. Set restrictive permissions (`0o600`) on output files.

### Rationale
- Protects credentials on shared systems
- Uses standard Unix permission model
- Skip on Windows (different ACL model)
- Warning only—don't block operations

### Alternatives Considered

| Alternative | Reason Rejected |
|-------------|-----------------|
| Auto-fix permissions | Potentially unwanted side effect |
| Block on bad permissions | Too aggressive for CLI tool |
| Check ACLs on Windows | Complex, different security model |

### Implementation Pattern
```python
import os
import stat
import platform

def check_file_permissions(filepath: Path, logger: logging.Logger | None = None) -> bool:
    """Check if file has overly permissive permissions (Unix only)."""
    if platform.system() == "Windows":
        return True  # Skip on Windows

    try:
        mode = os.stat(filepath).st_mode
        if mode & (stat.S_IROTH | stat.S_IRGRP):
            if logger:
                logger.warning(
                    "[SECURITY] File %s has permissive permissions (mode: %o). "
                    "Consider restricting to owner-only (600).",
                    filepath, mode & 0o777
                )
            return False
        return True
    except OSError:
        return True  # Can't check, assume OK
```

---

## 6. Audit Logging (Verbose Mode)

### Decision
Add `--verbose` / `-v` CLI flag and `GITHUB_ANALYZER_VERBOSE` environment variable. When enabled, log API operations (method, endpoint, status) with masked credentials.

### Rationale
- Aids debugging and security review
- Opt-in avoids performance impact by default
- Consistent with existing token masking (`[MASKED]`)
- Uses Python's built-in logging module

### Alternatives Considered

| Alternative | Reason Rejected |
|-------------|-----------------|
| Always log | Performance overhead, noisy output |
| Separate log file | Additional complexity |
| Debug mode with full details | Risk of credential leakage |

### Implementation Pattern
```python
def log_api_request(
    method: str,
    url: str,
    status_code: int,
    logger: logging.Logger,
) -> None:
    """Log API request details (for verbose mode)."""
    # Mask any tokens that might appear in URL (shouldn't, but defense-in-depth)
    safe_url = mask_token_in_string(url)
    logger.info(
        "[API] %s %s -> %d",
        method, safe_url, status_code
    )
```

---

## 7. Timeout Warning

### Decision
Warn when timeout exceeds 60 seconds at configuration time. Configurable threshold via `GITHUB_ANALYZER_TIMEOUT_WARN_THRESHOLD`.

### Rationale
- Very long timeouts may indicate misconfiguration
- Security implication: keeps connections open longer
- Non-blocking warning educates users
- Threshold configurable for specific use cases

### Alternatives Considered

| Alternative | Reason Rejected |
|-------------|-----------------|
| Hard cap on timeout | Breaks legitimate slow-network use cases |
| Silent acceptance | Misses opportunity to warn |
| Error on high timeout | Too aggressive |

### Implementation Pattern
```python
DEFAULT_TIMEOUT_WARN_THRESHOLD = 60  # seconds

def validate_timeout(timeout: int, logger: logging.Logger | None = None) -> None:
    """Warn if timeout is unusually high."""
    threshold = int(os.environ.get(
        "GITHUB_ANALYZER_TIMEOUT_WARN_THRESHOLD",
        DEFAULT_TIMEOUT_WARN_THRESHOLD
    ))
    if timeout > threshold:
        if logger:
            logger.warning(
                "[SECURITY] Timeout of %ds exceeds recommended threshold (%ds). "
                "Long timeouts keep connections open longer.",
                timeout, threshold
            )
```

---

## Dependencies Research

### Production Dependencies (to pin)

| Package | Current | Pinned Version | Notes |
|---------|---------|----------------|-------|
| requests | >=2.28.0 | 2.31.0 | Latest stable, security patches |

### Development Dependencies (ranges acceptable)

| Package | Current | Range | Notes |
|---------|---------|-------|-------|
| pytest | >=7.0.0 | >=7.0.0,<9.0.0 | Testing framework |
| pytest-cov | >=4.0.0 | >=4.0.0,<6.0.0 | Coverage reporting |
| ruff | >=0.1.0 | >=0.1.0,<1.0.0 | Linting |
| mypy | >=1.0.0 | >=1.0.0,<2.0.0 | Type checking |

---

## Security Warning Prefix Convention

All security-related warnings will use the `[SECURITY]` prefix for easy identification and log filtering.

Examples:
- `[SECURITY] File repos.txt has permissive permissions (mode: 644)`
- `[SECURITY] Unexpected Content-Type: text/html (expected application/json)`
- `[SECURITY] Timeout of 120s exceeds recommended threshold (60s)`
- `[SECURITY] Output path traversal attempt blocked: ../../../etc/passwd`

---

## Summary

All research items are resolved. No NEEDS CLARIFICATION markers remain. Implementation can proceed to Phase 1 (Design & Contracts).
