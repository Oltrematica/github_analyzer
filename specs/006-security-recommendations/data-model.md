# Data Model: Security Recommendations

**Feature**: 006-security-recommendations
**Date**: 2025-11-29

## Overview

This feature primarily adds security utilities and validations. It does not introduce new persistent data entities, but defines several value objects and configuration additions.

---

## Value Objects

### SafePath

Represents a validated file system path that has passed security checks.

| Attribute | Type | Description |
|-----------|------|-------------|
| `resolved_path` | `Path` | Fully resolved absolute path |
| `base_boundary` | `Path` | The safe boundary directory |
| `is_output` | `bool` | True if this is an output path |

**Validation Rules**:
- Path must resolve to a location within `base_boundary`
- Path traversal sequences (`..`) are resolved and checked
- Symbolic links are resolved before boundary check

**State Transitions**: None (immutable value object)

---

### SecurityWarning

Represents a security-related warning to be logged or displayed.

| Attribute | Type | Description |
|-----------|------|-------------|
| `category` | `str` | Warning category (e.g., "PERMISSION", "HEADER", "TIMEOUT") |
| `message` | `str` | Human-readable warning message |
| `severity` | `str` | One of: "INFO", "WARNING", "ERROR" |
| `context` | `dict[str, Any]` | Additional context (file path, header value, etc.) |

**Categories**:
- `PERMISSION`: File permission issues
- `HEADER`: Unexpected response headers
- `TIMEOUT`: Timeout configuration warnings
- `PATH`: Path traversal or validation issues

---

## Configuration Additions

### SecurityConfig (additions to existing Config)

| Setting | Type | Default | Env Variable |
|---------|------|---------|--------------|
| `verbose` | `bool` | `False` | `GITHUB_ANALYZER_VERBOSE` |
| `timeout_warn_threshold` | `int` | `60` | `GITHUB_ANALYZER_TIMEOUT_WARN_THRESHOLD` |
| `output_file_mode` | `int` | `0o600` | N/A (hardcoded for security) |
| `check_file_permissions` | `bool` | `True` | `GITHUB_ANALYZER_CHECK_PERMISSIONS` |

**Configuration Precedence** (per constitution):
1. CLI arguments (`--verbose`)
2. Environment variables
3. Config file (if implemented)
4. Defaults

---

## CSV Export Modifications

### Cell Escaping

All CSV cell values are processed through formula injection protection:

| Trigger Character | Escape Method |
|-------------------|---------------|
| `=` (equals) | Prefix with `'` |
| `+` (plus) | Prefix with `'` |
| `-` (minus) | Prefix with `'` |
| `@` (at) | Prefix with `'` |
| `\t` (tab) | Prefix with `'` |
| `\r` (carriage return) | Prefix with `'` |

**Data Integrity**: Original value recoverable by stripping leading `'` when first character is a formula trigger.

---

## File Permission Model (Unix)

### Permission Checks

| File Type | Expected Mode | Warning Condition |
|-----------|---------------|-------------------|
| Input files (repos.txt) | `0o600` or `0o400` | World-readable (`S_IROTH`) or group-readable (`S_IRGRP`) |
| Output CSV files | `0o600` | Created with owner-only permissions |

### Platform Behavior

| Platform | Behavior |
|----------|----------|
| Linux/macOS | Full permission checking |
| Windows | Permission checks skipped (different ACL model) |

---

## API Response Validation

### Content-Type Expectations

| API | Expected Content-Type | Action on Mismatch |
|-----|----------------------|-------------------|
| GitHub API | `application/json` | Log warning, continue |
| Jira API | `application/json` | Log warning, continue |

**Note**: Validation is defense-in-depth; responses are still processed to maintain availability.

---

## Relationships

```text
SecurityConfig ──────────────┐
                             │
                             ▼
┌─────────────────────────────────────────────┐
│              SecurityUtilities               │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │  SafePath   │  │  validate_headers()  │  │
│  └─────────────┘  └──────────────────────┘  │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │ escape_csv()│  │ check_permissions()  │  │
│  └─────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────┘
         │                     │
         ▼                     ▼
┌─────────────────┐    ┌─────────────────┐
│   CSVExporter   │    │   API Clients   │
│   (modified)    │    │   (modified)    │
└─────────────────┘    └─────────────────┘
```

---

## Summary

This feature adds security utilities without introducing new persistent entities. The primary data structures are:
- `SafePath`: Validated file system path
- `SecurityWarning`: Structured warning information
- Configuration additions for security settings

All changes maintain backward compatibility with existing data models and exports.
