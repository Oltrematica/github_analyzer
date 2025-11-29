# Quickstart: Security Recommendations Implementation

**Feature**: 006-security-recommendations
**Date**: 2025-11-29

## Prerequisites

- Python 3.9+
- Existing GitHub Analyzer codebase
- pytest for testing

## Implementation Order

Follow this sequence to implement the security recommendations:

### Phase 1: Core Security Module

1. **Create `src/github_analyzer/core/security.py`**
   - Implement `validate_output_path()`
   - Implement `escape_csv_formula()` and `escape_csv_row()`
   - Implement `check_file_permissions()` and `set_secure_permissions()`
   - Implement `validate_content_type()`
   - Implement `log_api_request()`
   - Implement `validate_timeout()`

2. **Write tests first (TDD per constitution)**
   - Create `tests/unit/core/test_security.py`
   - Test all edge cases documented in research.md

### Phase 2: Configuration Updates

3. **Update `src/github_analyzer/config/settings.py`**
   - Add `verbose` setting
   - Add `timeout_warn_threshold` setting
   - Add `check_file_permissions` setting

4. **Update `src/github_analyzer/cli/main.py`**
   - Add `--verbose` / `-v` flag
   - Call `validate_timeout()` at startup

### Phase 3: Integration

5. **Update `src/github_analyzer/exporters/csv_exporter.py`**
   - Use `validate_output_path()` in `__init__`
   - Apply `escape_csv_row()` in `_write_csv()`
   - Call `set_secure_permissions()` after file creation

6. **Update Jira exporters**
   - Apply same changes to `jira_exporter.py`
   - Apply same changes to `jira_metrics_exporter.py`

7. **Update API clients**
   - Add `validate_content_type()` to `client.py`
   - Add `validate_content_type()` to `jira_client.py`
   - Add `log_api_request()` calls when verbose mode enabled

### Phase 4: Dependency Pinning

8. **Update `requirements.txt`**
   ```text
   requests==2.31.0
   ```

9. **Update `requirements-dev.txt`**
   ```text
   -r requirements.txt
   pytest>=7.0.0,<9.0.0
   pytest-cov>=4.0.0,<6.0.0
   ruff>=0.1.0,<1.0.0
   mypy>=1.0.0,<2.0.0
   ```

## Quick Test

After implementation, verify with:

```bash
# Run tests
pytest tests/unit/core/test_security.py -v

# Test path validation (should fail)
python -c "
from src.github_analyzer.core.security import validate_output_path
validate_output_path('../../../etc')
"
# Expected: ValidationError

# Test CSV formula escape
python -c "
from src.github_analyzer.core.security import escape_csv_formula
print(escape_csv_formula('=SUM(A1:A10)'))
"
# Expected: '=SUM(A1:A10)

# Test verbose mode
GITHUB_ANALYZER_VERBOSE=1 python github_analyzer.py --days 1
# Expected: [API] logs visible
```

## Key Files

| File | Action | Priority |
|------|--------|----------|
| `src/github_analyzer/core/security.py` | CREATE | P1 |
| `tests/unit/core/test_security.py` | CREATE | P1 |
| `src/github_analyzer/config/settings.py` | MODIFY | P1 |
| `src/github_analyzer/exporters/csv_exporter.py` | MODIFY | P1 |
| `src/github_analyzer/api/client.py` | MODIFY | P2 |
| `requirements.txt` | MODIFY | P1 |

## Verification Checklist

- [ ] Path traversal blocked: `validate_output_path("../../../etc")` raises error
- [ ] CSV formula escaped: `=SUM` becomes `'=SUM`
- [ ] Permissions checked on Unix: world-readable repos.txt logs warning
- [ ] Content-Type validated: text/html response logs warning
- [ ] Verbose mode works: `--verbose` shows [API] logs
- [ ] Timeout warning: timeout > 60s logs warning
- [ ] Dependencies pinned: `requests==2.31.0` in requirements.txt
- [ ] All tests pass: `pytest tests/ -v`
- [ ] Coverage ≥ 80%: `pytest --cov=src/github_analyzer`
