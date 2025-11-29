# Security Analysis Report

**Application**: GitHub Analyzer / Dev Analyzer
**Version**: 2.0
**Analysis Date**: 2025-11-29
**Analyst**: Security Audit (Automated)

---

## Executive Summary

This document provides a comprehensive security analysis of the GitHub Analyzer application. The application is a CLI tool that:
- Fetches data from GitHub and Jira REST APIs
- Processes repository, commit, PR, and issue information
- Exports analysis results to CSV files

**Overall Security Posture**: **GOOD** with minor improvements recommended

The codebase demonstrates security-aware design with:
- Proper credential handling via environment variables
- Token masking in logs and error messages
- Input validation with whitelist patterns
- HTTPS enforcement for Jira connections
- Protection against common injection attacks

---

## Table of Contents

1. [Credential & Secret Management](#1-credential--secret-management)
2. [Input Validation & Sanitization](#2-input-validation--sanitization)
3. [Network & API Security](#3-network--api-security)
4. [File Operations Security](#4-file-operations-security)
5. [Error Handling & Information Disclosure](#5-error-handling--information-disclosure)
6. [Dependency Security](#6-dependency-security)
7. [Identified Vulnerabilities](#7-identified-vulnerabilities)
8. [Recommendations](#8-recommendations)
9. [Security Checklist](#9-security-checklist)

---

## 1. Credential & Secret Management

### 1.1 GitHub Token Handling

**Location**: `src/github_analyzer/config/settings.py`

**Implementation**:
```python
# Token loaded from environment variable only
token = os.environ.get("GITHUB_TOKEN", "").strip()
```

**Positive Findings**:
- Token is **NEVER** stored in code or configuration files
- Token is loaded exclusively from `GITHUB_TOKEN` environment variable
- Token value is **NEVER** logged or printed
- `mask_token()` function replaces token with `[MASKED]` in all representations

**Token Masking** (`src/github_analyzer/core/exceptions.py:124-137`):
```python
def mask_token(value: str) -> str:
    """Mask a token value for safe logging."""
    return "[MASKED]"  # Never reveal any part of the token
```

**Security Grade**: **A**

### 1.2 Jira Credentials Handling

**Location**: `src/github_analyzer/config/settings.py`, `src/github_analyzer/api/jira_client.py`

**Credentials Involved**:
- `JIRA_URL` - Jira instance URL
- `JIRA_EMAIL` - User email for authentication
- `JIRA_API_TOKEN` - API token

**Implementation**:
```python
# JiraConfig loads from environment
jira_url = os.environ.get("JIRA_URL", "").strip()
jira_email = os.environ.get("JIRA_EMAIL", "").strip()
jira_api_token = os.environ.get("JIRA_API_TOKEN", "").strip()
```

**Positive Findings**:
- All Jira credentials loaded from environment variables
- API token masked in `__repr__` and `__str__` methods
- `to_dict()` method returns masked token for safe logging
- Basic Auth credentials sent only over HTTPS

**Security Grade**: **A**

### 1.3 Token Format Validation

**Location**: `src/github_analyzer/config/validation.py:30-36`

**Patterns Validated**:
```python
TOKEN_PATTERNS = [
    r"^ghp_[a-zA-Z0-9]{20,}$",     # Classic PAT
    r"^github_pat_[a-zA-Z0-9_]{20,}$",  # Fine-grained PAT
    r"^gho_[a-zA-Z0-9]{20,}$",     # OAuth
    r"^ghs_[a-zA-Z0-9]{20,}$",     # App token
    r"^ghr_[a-zA-Z0-9]{36,}$",     # Refresh token
]
```

**Analysis**: Format validation ensures tokens match expected GitHub patterns, preventing use of arbitrary strings that could indicate configuration errors.

**Security Grade**: **A**

---

## 2. Input Validation & Sanitization

### 2.1 Repository Name Validation

**Location**: `src/github_analyzer/config/validation.py`

**Implementation**:

**Dangerous Character Detection** (line 46-47):
```python
DANGEROUS_CHARS = set(";|&$`(){}[]<>\\'\"\n\r\t")
```

**Whitelist Pattern** (line 42-43):
```python
REPO_COMPONENT_PATTERN = r"^[a-zA-Z0-9.][a-zA-Z0-9._-]{0,99}$"
REPO_FULL_PATTERN = r"^[a-zA-Z0-9.][a-zA-Z0-9._-]{0,99}/[a-zA-Z0-9.][a-zA-Z0-9._-]{0,99}$"
```

**Path Traversal Protection** (line 223-228):
```python
if ".." in owner or ".." in name:
    raise ValidationError(
        "Invalid repository: path traversal attempt detected",
        details="Repository names cannot contain '..'",
    )
```

**Positive Findings**:
- Uses **whitelist** approach (not blacklist)
- Explicitly blocks shell metacharacters
- Prevents path traversal attacks
- Validates URL format for GitHub URLs
- Maximum length enforcement (100 chars per component)

**Security Grade**: **A**

### 2.2 Jira Project Key Validation

**Location**: `src/github_analyzer/config/validation.py:346`

```python
JIRA_PROJECT_KEY_PATTERN = r"^[A-Z][A-Z0-9_]*$"
```

**Analysis**: Strict pattern allowing only uppercase letters, digits, and underscores starting with a letter.

**Security Grade**: **A**

### 2.3 URL Validation

**Location**: `src/github_analyzer/config/validation.py:349-392`

**Jira URL Validation**:
- Enforces **HTTPS only** (HTTP rejected)
- Validates host presence
- Requires at least one dot in hostname
- Checks for dangerous characters

```python
if parsed.scheme != "https":
    return False  # FR-019: HTTPS mandatory
```

**GitHub URL Normalization**:
- Validates against `github.com` or `www.github.com`
- Extracts owner/repo from path
- Handles `.git` suffix

**Security Grade**: **A**

### 2.4 ISO 8601 Date Validation

**Location**: `src/github_analyzer/config/validation.py:425-481`

**Implementation**: Validates date format and range (1900-2100) to prevent injection via malformed dates.

**Security Grade**: **A**

---

## 3. Network & API Security

### 3.1 HTTPS Enforcement

**GitHub API**:
- Hardcoded base URL: `https://api.github.com`
- No configuration option to use HTTP

**Jira API**:
- HTTPS **enforced** via `validate_jira_url()` (line 378)
- Rejects any `http://` URLs

**Security Grade**: **A**

### 3.2 Authentication Headers

**GitHub** (`src/github_analyzer/api/client.py:71-81`):
```python
def _get_headers(self) -> dict[str, str]:
    return {
        "Authorization": f"token {self._config.github_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GitHub-Analyzer/2.0",
    }
```

**Jira** (`src/github_analyzer/api/jira_client.py:149-164`):
```python
def _get_headers(self) -> dict[str, str]:
    credentials = f"{self.config.jira_email}:{self.config.jira_api_token}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {
        "Authorization": f"Basic {encoded}",
        ...
    }
```

**Analysis**:
- Credentials sent only in Authorization header
- Not logged or exposed in error messages
- Uses standard authentication schemes

**Security Grade**: **A**

### 3.3 Rate Limiting Handling

**Implementation**:
- Tracks `X-RateLimit-Remaining` and `X-RateLimit-Reset`
- Raises dedicated `RateLimitError` exception
- Displays wait time to user without exposing internal details

**Security Grade**: **A**

### 3.4 Retry Logic with Exponential Backoff

**GitHub** (`src/github_analyzer/api/client.py:255-294`):
```python
for attempt in range(max_retries):
    # Only retry on 5xx errors
    if e.status_code and 500 <= e.status_code < 600:
        wait_time = (2**attempt) * 0.5  # 0.5s, 1s, 2s
        time.sleep(wait_time)
```

**Jira** (`src/github_analyzer/api/jira_client.py:198-231`):
- Max retries: 5
- Initial delay: 1s
- Max delay: 60s
- Respects `Retry-After` header

**Analysis**: Protects against transient failures without overwhelming servers.

**Security Grade**: **A**

### 3.5 Timeout Configuration

Both clients implement configurable timeouts (default 30s, max 300s):

```python
timeout=self._config.timeout  # Used in all requests
```

**Analysis**: Prevents indefinite hangs from slow/unresponsive servers.

**Security Grade**: **A**

---

## 4. File Operations Security

### 4.1 Output Directory Creation

**Location**: `src/github_analyzer/exporters/csv_exporter.py:41-42`

```python
self._output_dir = Path(output_dir)
self._output_dir.mkdir(parents=True, exist_ok=True)
```

**Analysis**:
- Uses `pathlib.Path` for safe path handling
- Creates directories with default permissions
- No explicit path traversal protection on output_dir (see Recommendations)

**Security Grade**: **B+**

### 4.2 File Writing

**CSV Export** (`csv_exporter.py:44-65`):
```python
with open(filepath, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
```

**Analysis**:
- Uses `with` statement for proper resource cleanup
- Explicit UTF-8 encoding
- Uses Python's csv module (handles escaping)
- No direct string interpolation in file operations

**Security Grade**: **A**

### 4.3 Repository File Reading

**Location**: `src/github_analyzer/config/validation.py:237-307`

```python
with open(filepath, encoding="utf-8") as f:
    for line_num, line in enumerate(f, 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Validate each line
```

**Analysis**:
- Reads line by line (memory efficient)
- Validates each repository entry
- Skips comments and empty lines
- Reports line numbers for errors

**Security Grade**: **A**

---

## 5. Error Handling & Information Disclosure

### 5.1 Exception Hierarchy

**Location**: `src/github_analyzer/core/exceptions.py`

**Design**:
```
GitHubAnalyzerError (base)
├── ConfigurationError (exit code 1)
├── ValidationError (exit code 1)
└── APIError (exit code 2)
    └── RateLimitError (exit code 2)

JiraAPIError
├── JiraAuthenticationError (401)
├── JiraPermissionError (403)
├── JiraNotFoundError (404)
└── JiraRateLimitError (429)
```

**Analysis**: Well-structured hierarchy allows catching specific errors without exposing internal details.

**Security Grade**: **A**

### 5.2 Error Message Content

**Positive Findings**:
- Token values **NEVER** appear in error messages
- API responses truncated to 200 chars in error details
- Generic error messages for authentication failures
- Stack traces not exposed to users

**Example** (`client.py:151-155`):
```python
raise APIError(
    f"GitHub API error: HTTP {response.status_code}",
    details=response.text[:200] if response.text else None,
    status_code=response.status_code,
)
```

**Security Grade**: **A**

### 5.3 Logging Security

**Location**: `src/github_analyzer/analyzers/jira_metrics.py`

```python
logger.warning(
    "Negative cycle time detected: created=%s, resolved=%s. Setting to None.",
    created.isoformat(),
    resolution_date.isoformat(),
)
```

**Analysis**:
- No secrets logged
- Logs contain only operational data
- Uses Python's logging module

**Security Grade**: **A**

---

## 6. Dependency Security

### 6.1 External Dependencies

**Required**:
- Python 3.9+ (standard library)

**Optional**:
- `requests` - HTTP client (falls back to urllib if not available)

**Analysis**:
- Minimal dependency footprint reduces attack surface
- Graceful fallback to stdlib when `requests` unavailable
- No usage of deprecated or known-vulnerable packages

**Recommendation**: Add a `requirements.txt` or `pyproject.toml` with pinned versions.

**Security Grade**: **B+**

---

## 7. Identified Vulnerabilities

### 7.1 Low Severity

#### L1: No Output Path Validation
**Location**: `src/github_analyzer/exporters/csv_exporter.py`
**Issue**: The output directory path is not validated against path traversal.
**Risk**: Low - User-controlled via CLI argument, local execution only.
**Remediation**: Add path normalization and validate against base directory.

```python
# Recommended fix
output_path = Path(output_dir).resolve()
if not output_path.is_relative_to(Path.cwd()):
    raise ValidationError("Output path must be within current directory")
```

#### L2: User Input Echo in Terminal
**Location**: `src/github_analyzer/cli/main.py`
**Issue**: User input from `input()` is printed back without sanitization.
**Risk**: Low - Terminal escape sequence injection (limited impact in CLI context).
**Remediation**: Strip control characters from user input before display.

#### L3: No Certificate Pinning
**Location**: `src/github_analyzer/api/client.py`, `jira_client.py`
**Issue**: SSL certificate validation uses system CA store without pinning.
**Risk**: Low - MitM attack requires CA compromise or network position.
**Remediation**: For high-security environments, implement certificate pinning.

### 7.2 Informational

#### I1: GitHub Token in Memory
**Issue**: GitHub token remains in memory during execution.
**Risk**: Informational - Standard for authentication tokens.
**Note**: Cannot be avoided for API authentication; token is not persisted.

#### I2: No Rate Limit Precheck
**Issue**: Rate limit state not checked before starting analysis.
**Note**: Could improve UX by checking remaining quota at startup.

---

## 8. Recommendations

### 8.1 High Priority

1. **Add output path validation**
   - Validate output directory is not outside intended scope
   - Prevent path traversal in file export

2. **Pin dependency versions**
   - Create `requirements.txt` with pinned versions
   - Consider using `pip-audit` for vulnerability scanning

### 8.2 Medium Priority

3. **Add security headers check for responses**
   ```python
   # Check for expected Content-Type
   content_type = headers.get("Content-Type", "")
   if "application/json" not in content_type:
       logger.warning("Unexpected content type: %s", content_type)
   ```

4. **Implement request timeout override warning**
   - Warn if timeout > 60s is configured
   - Document security implications of long timeouts

5. **Add file permission checks**
   - Warn if sensitive files (e.g., repos.txt) are world-readable
   - Set restrictive permissions on output files

### 8.3 Low Priority

6. **Consider adding Content Security Policy for CSV**
   - Escape special characters that could trigger formula injection in spreadsheets
   - Prefix cells starting with `=`, `+`, `-`, `@` with a single quote

7. **Add token rotation reminder**
   - Log info message about token age if detectable
   - Document recommended token rotation schedule

8. **Implement audit logging**
   - Log API calls (without tokens) for debugging
   - Optional verbose mode for security auditing

---

## 9. Security Checklist

### Authentication & Authorization
- [x] Credentials loaded from environment variables
- [x] Tokens never logged or exposed in errors
- [x] Token format validation before use
- [x] Secure token masking in all representations
- [x] Basic Auth only over HTTPS

### Input Validation
- [x] Whitelist validation patterns
- [x] Dangerous character rejection
- [x] Path traversal prevention
- [x] URL scheme validation (HTTPS enforced)
- [x] Maximum length enforcement

### Network Security
- [x] HTTPS enforced for all API calls
- [x] Timeout configuration
- [x] Rate limit handling
- [x] Retry with exponential backoff
- [x] Proper error handling for network failures

### Data Protection
- [x] No sensitive data in logs
- [x] Error messages sanitized
- [x] CSV properly escaped via csv module
- [x] UTF-8 encoding enforced

### Code Quality
- [x] Type hints throughout
- [x] Structured exception handling
- [x] Resource cleanup with context managers
- [x] No eval/exec usage
- [x] No shell command injection vectors

---

## Appendix A: Files Analyzed

| File | Lines | Security Relevant |
|------|-------|-------------------|
| `src/github_analyzer/config/settings.py` | 436 | High - Credential handling |
| `src/github_analyzer/config/validation.py` | 526 | High - Input validation |
| `src/github_analyzer/api/client.py` | 552 | High - API communication |
| `src/github_analyzer/api/jira_client.py` | 685 | High - API communication |
| `src/github_analyzer/core/exceptions.py` | 241 | Medium - Error handling |
| `src/github_analyzer/cli/main.py` | 1438 | Medium - User input |
| `src/github_analyzer/exporters/csv_exporter.py` | 399 | Medium - File operations |
| `src/github_analyzer/exporters/jira_exporter.py` | 201 | Medium - File operations |
| `src/github_analyzer/cli/output.py` | 255 | Low - Terminal output |
| `src/github_analyzer/analyzers/jira_metrics.py` | 642 | Low - Data processing |

---

## Appendix B: Security Headers

The following security-relevant headers are handled:

| Header | Usage |
|--------|-------|
| `Authorization` | Token/Basic Auth transmission |
| `X-RateLimit-Remaining` | Rate limit tracking |
| `X-RateLimit-Reset` | Rate limit reset timestamp |
| `Retry-After` | Retry timing (Jira 429 responses) |
| `Content-Type` | Response format verification |

---

## Appendix C: Environment Variables

| Variable | Purpose | Security Notes |
|----------|---------|----------------|
| `GITHUB_TOKEN` | GitHub API authentication | Never logged, masked in output |
| `JIRA_URL` | Jira instance URL | HTTPS enforced |
| `JIRA_EMAIL` | Jira auth email | Logged in error context |
| `JIRA_API_TOKEN` | Jira API token | Never logged, masked in output |

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-29 | 1.0 | Initial security analysis |

---

*This security analysis was performed based on static code review. Dynamic testing (penetration testing, fuzzing) is recommended for production deployments.*
