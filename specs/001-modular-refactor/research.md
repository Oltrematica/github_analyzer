# Research: Modular Architecture Refactoring

**Feature**: 001-modular-refactor
**Date**: 2025-11-28
**Status**: Complete

## Research Topics

### 1. Python Project Structure for CLI Tools

**Decision**: Use `src/` layout with namespace package

**Rationale**:
- `src/` layout prevents accidental imports from project root
- Namespace package (`github_analyzer`) allows clear module boundaries
- Consistent with modern Python packaging best practices (PEP 517/518)
- setuptools and pip support this layout natively

**Alternatives Considered**:
- Flat layout (all modules at root): Rejected - risk of import conflicts
- Single package without src/: Rejected - test isolation issues
- Multiple top-level packages: Rejected - unnecessary complexity

### 2. Token Security Best Practices

**Decision**: Environment variable only (`GITHUB_TOKEN`), no fallback to interactive prompt

**Rationale**:
- Environment variables are the standard for credential management
- Compatible with CI/CD systems, Docker, Kubernetes secrets
- No risk of token in shell history (unlike CLI arguments)
- `getpass` interactive input can still be exposed in process listings

**Implementation Details**:
- Use `os.environ.get("GITHUB_TOKEN")` with immediate validation
- Token format validation: check prefix (`ghp_`, `gho_`, `github_pat_`) and length
- Never log token value, even partially (no `token[:4] + "***"`)
- Error messages reference `GITHUB_TOKEN` variable name, not value

**Alternatives Considered**:
- Config file with token: Rejected - file permission risks, accidental commits
- Keyring/keychain integration: Rejected - adds dependency, platform-specific
- Interactive prompt as fallback: Rejected - security concerns with process lists

### 3. Input Validation Patterns

**Decision**: Whitelist-based validation with strict regex patterns

**Rationale**:
- Blacklist approaches miss edge cases
- GitHub repository names have well-defined constraints
- Early validation prevents API request waste

**Implementation Details**:
- Repository name pattern: `^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$`
- Reject any input containing: `; | & $ \` ( ) { } [ ] < > ..`
- URL normalization: strip protocol, `.git` suffix, trailing slashes
- Case preservation (GitHub repos are case-sensitive in API)

**Edge Cases Handled**:
- Unicode characters: Rejected (GitHub doesn't allow)
- Very long names: Check against GitHub's 100-char limit per segment
- Reserved names: `.git`, `.github` as repo names are valid

### 4. Python Testing with pytest

**Decision**: pytest with pytest-cov, parametrized tests, fixtures for mocking

**Rationale**:
- pytest is the de facto standard for Python testing
- Built-in fixtures reduce boilerplate
- pytest-cov integrates seamlessly for coverage
- Parametrized tests handle validation edge cases efficiently

**Implementation Details**:
- `conftest.py` for shared fixtures (mock API responses, sample repos)
- `unittest.mock` for API client mocking (no external dependencies)
- Response fixtures stored as JSON in `tests/fixtures/api_responses/`
- Coverage threshold: 80% (configurable in pytest.ini)

**Test Categories**:
1. Unit tests: Each module's public interface
2. Integration tests: Full analyzer flow with mocked API
3. Validation tests: Input sanitization edge cases

### 5. Module Dependency Graph

**Decision**: Strict unidirectional dependencies

```
cli → config → (none)
cli → api → config
cli → analyzers → api (models only), config
cli → exporters → analyzers (data types), config
```

**Rationale**:
- Prevents circular imports
- Each module can be tested in isolation
- Clear ownership of responsibilities

**Implementation Details**:
- `config/` has no internal dependencies (leaf module)
- `api/models.py` defines data classes used by analyzers
- `analyzers/` never import from `exporters/` or `cli/`
- `core/exceptions.py` can be imported anywhere (no dependencies)

### 6. Backward Compatibility Strategy

**Decision**: Preserve root `github_analyzer.py` as thin wrapper

**Rationale**:
- Existing users can run `python github_analyzer.py` unchanged
- Documentation and scripts don't need updates
- New package structure is internal implementation detail

**Implementation Details**:
```python
# github_analyzer.py (root)
#!/usr/bin/env python3
"""Backward-compatible entry point."""
from src.github_analyzer.cli.main import main

if __name__ == "__main__":
    main()
```

### 7. Configuration Management

**Decision**: Dataclass-based configuration with environment override

**Rationale**:
- Dataclasses provide type safety and defaults
- Environment variables override defaults cleanly
- No external configuration library needed

**Implementation Details**:
```python
@dataclass
class AnalyzerConfig:
    github_token: str  # Required, from GITHUB_TOKEN
    output_dir: str = "github_export"
    days: int = 30
    per_page: int = 100
    verbose: bool = True
    timeout: int = 30
```

- Load order: defaults → env vars → (future: CLI args)
- Validation at construction time
- Immutable after creation (frozen=True optional)

### 8. Error Handling Strategy

**Decision**: Custom exception hierarchy with error codes

**Rationale**:
- Distinguishes user errors from system errors
- Exit codes follow convention (0, 1, 2)
- Enables consistent error message formatting

**Exception Hierarchy**:
```python
class GitHubAnalyzerError(Exception):
    """Base exception for all analyzer errors."""
    exit_code: int = 1

class ConfigurationError(GitHubAnalyzerError):
    """Invalid configuration (missing token, bad repos)."""
    exit_code = 1

class ValidationError(GitHubAnalyzerError):
    """Input validation failed."""
    exit_code = 1

class APIError(GitHubAnalyzerError):
    """GitHub API communication error."""
    exit_code = 2

class RateLimitError(APIError):
    """Rate limit exceeded."""
    exit_code = 2
```

## Unresolved Items

None. All technical decisions are finalized.

## References

- [Python Packaging User Guide](https://packaging.python.org/)
- [GitHub REST API Documentation](https://docs.github.com/en/rest)
- [12-Factor App: Config](https://12factor.net/config)
- [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
