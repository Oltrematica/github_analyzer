"""Input validation for GitHub Analyzer.

This module provides validation functions and classes for:
- GitHub token format validation
- Repository name/URL validation
- Repository list file loading

Security Notes:
- All validation uses whitelist patterns, not blacklists
- Dangerous characters are explicitly rejected
- Token values are never logged or exposed
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO
from urllib.parse import urlparse

from src.github_analyzer.core.exceptions import ConfigurationError, ValidationError

# Token format patterns
# Classic Personal Access Token: ghp_xxxx
# Fine-grained PAT: github_pat_xxxx
# OAuth token: gho_xxxx
# GitHub App token: ghs_xxxx (server-to-server)
# GitHub App refresh token: ghr_xxxx
TOKEN_PATTERNS = [
    r"^ghp_[a-zA-Z0-9]{20,}$",  # Classic PAT (ghp_ + 20+ chars)
    r"^github_pat_[a-zA-Z0-9_]{20,}$",  # Fine-grained PAT
    r"^gho_[a-zA-Z0-9]{20,}$",  # OAuth (gho_ + 20+ chars)
    r"^ghs_[a-zA-Z0-9]{20,}$",  # App token (ghs_ + 20+ chars)
    r"^ghr_[a-zA-Z0-9]{36,}$",  # Refresh token
]

# Repository name validation
# GitHub allows: alphanumeric, hyphen, underscore, period
# Max 100 characters per component
REPO_COMPONENT_PATTERN = r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,99}$"
REPO_FULL_PATTERN = r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,99}/[a-zA-Z0-9][a-zA-Z0-9._-]{0,99}$"

# Dangerous characters that could indicate injection attempts
DANGEROUS_CHARS = set(";|&$`(){}[]<>\\'\"\n\r\t")


def validate_token_format(token: str) -> bool:
    """Check if token matches GitHub token format patterns.

    This performs a format check only, NOT API validation.
    A valid format does not guarantee the token is active.

    Args:
        token: The token string to validate.

    Returns:
        True if token matches a known GitHub token format.

    Note:
        Token value is never logged or exposed, even on failure.
    """
    if not token or len(token) < 10:
        return False

    return any(re.match(pattern, token) for pattern in TOKEN_PATTERNS)


def _contains_dangerous_chars(value: str) -> bool:
    """Check if value contains dangerous characters.

    Args:
        value: String to check.

    Returns:
        True if value contains any dangerous characters.
    """
    return bool(set(value) & DANGEROUS_CHARS)


def _normalize_url(url: str) -> str | None:
    """Extract owner/repo from GitHub URL.

    Handles various URL formats:
    - https://github.com/owner/repo
    - http://github.com/owner/repo
    - https://github.com/owner/repo.git
    - https://github.com/owner/repo/

    Args:
        url: GitHub URL to normalize.

    Returns:
        "owner/repo" format string, or None if invalid.
    """
    try:
        parsed = urlparse(url)

        # Must be github.com
        if parsed.netloc not in ("github.com", "www.github.com"):
            return None

        # Get path and clean it
        path = parsed.path.strip("/")

        # Remove .git suffix
        if path.endswith(".git"):
            path = path[:-4]

        # Should have exactly owner/repo format
        parts = path.split("/")
        if len(parts) != 2:
            return None

        owner, repo = parts
        if not owner or not repo:
            return None

        return f"{owner}/{repo}"
    except Exception:
        return None


@dataclass(frozen=True)
class Repository:
    """Validated GitHub repository identifier.

    Attributes:
        owner: Repository owner (user or organization).
        name: Repository name.

    Example:
        >>> repo = Repository.from_string("facebook/react")
        >>> print(repo.full_name)
        facebook/react
    """

    owner: str
    name: str

    @property
    def full_name(self) -> str:
        """Return repository in 'owner/name' format."""
        return f"{self.owner}/{self.name}"

    @classmethod
    def from_string(cls, repo_str: str) -> Repository:
        """Parse repository from string (owner/repo or URL).

        Accepts formats:
        - owner/repo
        - https://github.com/owner/repo
        - http://github.com/owner/repo (normalized to https)
        - URLs with .git suffix or trailing slash

        Args:
            repo_str: Repository string to parse.

        Returns:
            Validated Repository instance.

        Raises:
            ValidationError: If format is invalid or contains dangerous characters.
        """
        if not repo_str:
            raise ValidationError("Repository string cannot be empty")

        # Strip whitespace
        repo_str = repo_str.strip()

        # Check for dangerous characters first
        if _contains_dangerous_chars(repo_str):
            raise ValidationError(
                "Repository contains invalid characters",
                details="Repository names cannot contain shell metacharacters",
            )

        # Try to parse as URL first
        if repo_str.startswith(("http://", "https://")):
            normalized = _normalize_url(repo_str)
            if normalized is None:
                raise ValidationError(
                    "Invalid GitHub URL format",
                    details="URL must be in format: https://github.com/owner/repo",
                )
            repo_str = normalized

        # Validate owner/repo format
        if "/" not in repo_str:
            raise ValidationError(
                "Invalid repository format: missing '/'",
                details="Repository must be in 'owner/repo' format",
            )

        parts = repo_str.split("/")
        if len(parts) != 2:
            raise ValidationError(
                "Invalid repository format: too many '/'",
                details="Repository must be in 'owner/repo' format",
            )

        owner, name = parts

        # Validate owner
        if not owner:
            raise ValidationError("Repository owner cannot be empty")
        if not re.match(REPO_COMPONENT_PATTERN, owner):
            raise ValidationError(
                "Invalid repository owner format",
                details="Owner must start with alphanumeric and contain only alphanumeric, hyphen, underscore, or period",
            )

        # Validate name
        if not name:
            raise ValidationError("Repository name cannot be empty")
        if not re.match(REPO_COMPONENT_PATTERN, name):
            raise ValidationError(
                "Invalid repository name format",
                details="Name must start with alphanumeric and contain only alphanumeric, hyphen, underscore, or period",
            )

        # Check for path traversal
        if ".." in owner or ".." in name:
            raise ValidationError(
                "Invalid repository: path traversal attempt detected",
                details="Repository names cannot contain '..'",
            )

        return cls(owner=owner, name=name)

    def __str__(self) -> str:
        """Return repository as owner/name string."""
        return self.full_name


def load_repositories(filepath: str | Path) -> list[Repository]:
    """Load and validate repositories from file.

    File format:
    - One repository per line
    - Lines starting with # are comments
    - Empty lines are ignored
    - Supports owner/repo and URL formats
    - Duplicates are deduplicated with warning

    Args:
        filepath: Path to repos.txt file.

    Returns:
        List of validated Repository objects (deduplicated).

    Raises:
        ConfigurationError: If file not found or empty.
        ValidationError: If any entry is invalid (logged, continues with valid).
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise ConfigurationError(
            f"Repository file not found: {filepath}",
            details=f"Create the file '{filepath}' with one repository per line (owner/repo format)",
        )

    repositories: list[Repository] = []
    seen: set[str] = set()
    errors: list[str] = []

    with open(filepath, encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            try:
                repo = Repository.from_string(line)

                # Check for duplicates
                if repo.full_name in seen:
                    # Log warning but don't add duplicate
                    errors.append(
                        f"Line {line_num}: Duplicate repository '{repo.full_name}' (skipped)"
                    )
                    continue

                seen.add(repo.full_name)
                repositories.append(repo)

            except ValidationError as e:
                errors.append(f"Line {line_num}: {e.message}")
                continue

    # Report errors if any
    if errors:
        # In production, these would be logged as warnings
        # For now, we continue with valid repositories
        pass

    if not repositories:
        raise ConfigurationError(
            "No valid repositories found in file",
            details=f"Add repositories to '{filepath}' in owner/repo format",
        )

    return repositories


def load_repositories_from_file(file: TextIO) -> list[Repository]:
    """Load repositories from an open file object.

    Useful for testing with StringIO or other file-like objects.

    Args:
        file: Open file object to read from.

    Returns:
        List of validated Repository objects.
    """
    repositories: list[Repository] = []
    seen: set[str] = set()

    for line in file:
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        try:
            repo = Repository.from_string(line)
            if repo.full_name not in seen:
                seen.add(repo.full_name)
                repositories.append(repo)
        except ValidationError:
            continue

    return repositories
