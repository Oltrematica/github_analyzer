# Contributing to GitHub Analyzer

Thank you for your interest in contributing to GitHub Analyzer! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Commit Messages](#commit-messages)
- [Pull Requests](#pull-requests)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. Please:

- Be respectful and constructive in discussions
- Welcome newcomers and help them get started
- Focus on the issue, not the person
- Accept constructive criticism gracefully

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- A GitHub account

### Fork and Clone

1. **Fork the repository** on GitHub by clicking the "Fork" button
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/github_analyzer.git
   cd github_analyzer
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/Oltrematica/github_analyzer.git
   ```

## Development Setup

### Install Dependencies

```bash
# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install optional dependencies
pip install -r requirements.txt
```

### Verify Installation

```bash
# Run tests
pytest tests/ -v

# Run linter
ruff check src/github_analyzer/

# Run type checker
mypy src/github_analyzer/
```

## Development Workflow

### 1. Create a Feature Branch

Always create a new branch for your work:

```bash
# Sync with upstream first
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feat/your-feature-name
```

Branch naming conventions:
- `feat/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation changes
- `refactor/description` - Code refactoring
- `test/description` - Test additions or fixes

### 2. Make Your Changes

- Write clean, readable code
- Follow the code style guidelines
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest --cov=src/github_analyzer --cov-report=term-missing

# Check coverage meets threshold (95%)
pytest --cov=src/github_analyzer --cov-fail-under=95

# Run linter
ruff check src/github_analyzer/

# Run type checker
mypy src/github_analyzer/
```

### 4. Commit and Push

```bash
git add .
git commit -m "feat(scope): description"
git push origin feat/your-feature-name
```

### 5. Open a Pull Request

Go to GitHub and open a Pull Request from your branch to `main`.

## Code Style

### Python Version

- **Python 3.9+** compatibility is required
- Use features available in Python 3.9 (no walrus operator in contexts that break 3.9)

### Type Hints

All functions must have type hints:

```python
def calculate_metrics(commits: list[Commit], days: int) -> dict[str, float]:
    """Calculate quality metrics from commits.

    Args:
        commits: List of commit objects to analyze.
        days: Number of days in the analysis period.

    Returns:
        Dictionary mapping metric names to values.
    """
    ...
```

### Formatting

We use **ruff** for linting and formatting:

```bash
# Check for issues
ruff check src/github_analyzer/

# Auto-fix issues
ruff check --fix src/github_analyzer/
```

Key style rules:
- Line length: 100 characters max
- Use double quotes for strings
- Use 4 spaces for indentation
- Follow PEP 8 conventions

### Docstrings

Use Google-style docstrings for public APIs:

```python
def fetch_commits(repo: Repository, since: datetime) -> list[Commit]:
    """Fetch commits from a repository.

    Args:
        repo: Repository to fetch from.
        since: Only fetch commits after this date.

    Returns:
        List of Commit objects.

    Raises:
        APIError: If the API request fails.
        RateLimitError: If rate limit is exceeded.
    """
```

### Imports

Organize imports in this order:
1. Standard library
2. Third-party packages
3. Local imports

```python
from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING

from src.github_analyzer.api.client import GitHubClient
from src.github_analyzer.core.exceptions import APIError

if TYPE_CHECKING:
    from src.github_analyzer.config.settings import AnalyzerConfig
```

## Testing

### Test Structure

Tests mirror the source structure:

```
tests/
├── unit/
│   ├── api/
│   │   ├── test_client.py
│   │   └── test_models.py
│   ├── analyzers/
│   │   ├── test_commits.py
│   │   └── test_quality.py
│   └── config/
│       └── test_settings.py
└── integration/
    └── test_full_workflow.py
```

### Writing Tests

```python
import pytest
from unittest.mock import Mock, patch

from src.github_analyzer.analyzers.commits import CommitAnalyzer


class TestCommitAnalyzer:
    """Tests for CommitAnalyzer class."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock GitHub client."""
        return Mock()

    def test_fetches_commits_from_api(self, mock_client):
        """Test that analyzer fetches commits from the API."""
        mock_client.get_paginated.return_value = [{"sha": "abc123"}]

        analyzer = CommitAnalyzer(mock_client)
        # ... test implementation
```

### Test Requirements

- **Coverage**: Minimum 95% code coverage
- **Unit tests**: All new code must have tests
- **Mocking**: Mock external dependencies (GitHub API, file system)
- **Fixtures**: Use pytest fixtures for reusable test data
- **Naming**: Test names should describe the behavior being tested

### Running Specific Tests

```bash
# Run single test file
pytest tests/unit/api/test_client.py -v

# Run tests matching pattern
pytest -k "test_fetch" -v

# Run with verbose output
pytest tests/ -v --tb=long
```

## Commit Messages

We use **Conventional Commits** format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Code style (formatting, no logic change) |
| `refactor` | Code refactoring |
| `perf` | Performance improvement |
| `test` | Adding or updating tests |
| `build` | Build system or dependencies |
| `ci` | CI/CD configuration |
| `chore` | Maintenance tasks |
| `revert` | Revert a previous commit |

### Scope

Optional, but helpful. Common scopes:
- `api` - API client
- `cli` - Command-line interface
- `config` - Configuration
- `analyzers` - Analysis modules
- `exporters` - CSV export

### Examples

```bash
# Feature
feat(api): add retry logic for rate-limited requests

# Bug fix
fix(cli): handle empty repository list gracefully

# Documentation
docs(readme): add troubleshooting section

# Test
test(analyzers): add unit tests for quality metrics

# Breaking change (note the !)
feat(api)!: change response format for commits endpoint

BREAKING CHANGE: The commits endpoint now returns a different structure.
```

## Pull Requests

### Before Submitting

- [ ] Tests pass locally (`pytest tests/ -v`)
- [ ] Linter passes (`ruff check src/github_analyzer/`)
- [ ] Type checker passes (`mypy src/github_analyzer/`)
- [ ] Coverage is ≥95%
- [ ] Documentation is updated (if applicable)
- [ ] Commit messages follow conventions

### PR Template

When opening a PR, include:

```markdown
## Summary

Brief description of the changes.

## Changes

- Change 1
- Change 2

## Test Plan

- [ ] Unit tests added/updated
- [ ] Manual testing performed

## Related Issues

Fixes #123
```

### Review Process

1. **Automated checks** must pass (CI, linting, tests)
2. **Code review** by at least one maintainer
3. **Discussion** - respond to feedback constructively
4. **Approval** - once approved, a maintainer will merge

### After Merge

- Delete your feature branch
- Pull the latest `main` to stay updated

## Reporting Issues

### Bug Reports

Include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages (if any)

### Feature Requests

Include:
- Use case description
- Proposed solution
- Alternatives considered

### Security Issues

For security vulnerabilities, please **do not** open a public issue. Instead, contact the maintainers directly.

## Questions?

- Open an issue for discussion before starting major changes
- Check existing issues and PRs to avoid duplicates
- Be patient - maintainers review PRs as time allows

---

Thank you for contributing!
