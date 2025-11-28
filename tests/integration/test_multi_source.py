"""Integration tests for multi-source extraction.

Tests for:
- Source auto-detection
- Source validation
- Module function testing
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

import pytest

from src.github_analyzer.config.settings import DataSource


class TestSourceAutoDetection:
    """Tests for source auto-detection in extraction."""

    def test_auto_detects_github_when_token_present(self) -> None:
        """Auto-detection finds GitHub when token is present."""
        from src.github_analyzer.cli.main import auto_detect_sources

        env = {"GITHUB_TOKEN": "ghp_test123456789012345678901234567890ab"}
        with mock.patch.dict(os.environ, env, clear=True):
            sources = auto_detect_sources()

        assert DataSource.GITHUB in sources

    def test_auto_detects_jira_when_credentials_present(self) -> None:
        """Auto-detection finds Jira when credentials are present."""
        from src.github_analyzer.cli.main import auto_detect_sources

        env = {
            "JIRA_URL": "https://company.atlassian.net",
            "JIRA_EMAIL": "user@company.com",
            "JIRA_API_TOKEN": "test-token",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            sources = auto_detect_sources()

        assert DataSource.JIRA in sources

    def test_auto_detects_both_when_all_credentials_present(self) -> None:
        """Auto-detection finds both when all credentials present."""
        from src.github_analyzer.cli.main import auto_detect_sources

        env = {
            "GITHUB_TOKEN": "ghp_test123456789012345678901234567890ab",
            "JIRA_URL": "https://company.atlassian.net",
            "JIRA_EMAIL": "user@company.com",
            "JIRA_API_TOKEN": "test-token",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            sources = auto_detect_sources()

        assert DataSource.GITHUB in sources
        assert DataSource.JIRA in sources

    def test_auto_detects_nothing_when_no_credentials(self) -> None:
        """Auto-detection returns empty list when no credentials."""
        from src.github_analyzer.cli.main import auto_detect_sources

        with mock.patch.dict(os.environ, {}, clear=True):
            sources = auto_detect_sources()

        assert sources == []


class TestExtractionErrorHandling:
    """Tests for error handling during extraction."""

    def test_missing_github_token_raises(self) -> None:
        """Missing GitHub token raises ValueError."""
        from src.github_analyzer.cli.main import validate_sources

        with mock.patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GITHUB_TOKEN"):
                validate_sources([DataSource.GITHUB])

    def test_missing_jira_credentials_raises(self) -> None:
        """Missing Jira credentials raises ValueError."""
        from src.github_analyzer.cli.main import validate_sources

        with mock.patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Jira"):
                validate_sources([DataSource.JIRA])

    def test_partial_jira_credentials_raises(self) -> None:
        """Partial Jira credentials raises ValueError."""
        from src.github_analyzer.cli.main import validate_sources

        env = {
            "JIRA_URL": "https://company.atlassian.net",
            # Missing JIRA_EMAIL and JIRA_API_TOKEN
        }
        with mock.patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="Jira"):
                validate_sources([DataSource.JIRA])

    def test_github_with_valid_token_passes(self) -> None:
        """GitHub with valid token passes validation."""
        from src.github_analyzer.cli.main import validate_sources

        env = {"GITHUB_TOKEN": "ghp_test123456789012345678901234567890ab"}
        with mock.patch.dict(os.environ, env, clear=True):
            # Should not raise
            validate_sources([DataSource.GITHUB])

    def test_jira_with_valid_credentials_passes(self) -> None:
        """Jira with valid credentials passes validation."""
        from src.github_analyzer.cli.main import validate_sources

        env = {
            "JIRA_URL": "https://company.atlassian.net",
            "JIRA_EMAIL": "user@company.com",
            "JIRA_API_TOKEN": "test-token",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            # Should not raise
            validate_sources([DataSource.JIRA])


class TestSourcesParsing:
    """Tests for sources string parsing."""

    def test_parse_single_source_github(self) -> None:
        """Parses 'github' correctly."""
        from src.github_analyzer.cli.main import parse_sources_list

        result = parse_sources_list("github")
        assert result == [DataSource.GITHUB]

    def test_parse_single_source_jira(self) -> None:
        """Parses 'jira' correctly."""
        from src.github_analyzer.cli.main import parse_sources_list

        result = parse_sources_list("jira")
        assert result == [DataSource.JIRA]

    def test_parse_both_sources(self) -> None:
        """Parses 'github,jira' correctly."""
        from src.github_analyzer.cli.main import parse_sources_list

        result = parse_sources_list("github,jira")
        assert DataSource.GITHUB in result
        assert DataSource.JIRA in result

    def test_parse_invalid_source_raises(self) -> None:
        """Invalid source raises ValueError."""
        from src.github_analyzer.cli.main import parse_sources_list

        with pytest.raises(ValueError, match="Unknown source"):
            parse_sources_list("invalid")
