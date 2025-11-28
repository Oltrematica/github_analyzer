"""Unit tests for CLI argument parsing.

Tests for:
- --sources flag parsing
- Source auto-detection logic
- DataSource list handling
"""

from __future__ import annotations

import argparse
import os
from unittest import mock

import pytest

from src.github_analyzer.config.settings import DataSource


class TestSourcesArgument:
    """Tests for --sources CLI argument."""

    def test_default_sources_is_auto(self) -> None:
        """--sources defaults to 'auto'."""
        from src.github_analyzer.cli.main import parse_args

        with mock.patch("sys.argv", ["prog"]):
            args = parse_args()
        assert args.sources == "auto"

    def test_sources_github_only(self) -> None:
        """--sources github parses correctly."""
        from src.github_analyzer.cli.main import parse_args

        with mock.patch("sys.argv", ["prog", "--sources", "github"]):
            args = parse_args()
        assert args.sources == "github"

    def test_sources_jira_only(self) -> None:
        """--sources jira parses correctly."""
        from src.github_analyzer.cli.main import parse_args

        with mock.patch("sys.argv", ["prog", "--sources", "jira"]):
            args = parse_args()
        assert args.sources == "jira"

    def test_sources_both(self) -> None:
        """--sources github,jira parses correctly."""
        from src.github_analyzer.cli.main import parse_args

        with mock.patch("sys.argv", ["prog", "--sources", "github,jira"]):
            args = parse_args()
        assert args.sources == "github,jira"

    def test_sources_short_flag(self) -> None:
        """-s flag works as alias for --sources."""
        from src.github_analyzer.cli.main import parse_args

        with mock.patch("sys.argv", ["prog", "-s", "jira"]):
            args = parse_args()
        assert args.sources == "jira"


class TestParseSourcesList:
    """Tests for parse_sources_list helper function."""

    def test_parse_github(self) -> None:
        """Parses 'github' to DataSource.GITHUB."""
        from src.github_analyzer.cli.main import parse_sources_list

        result = parse_sources_list("github")
        assert result == [DataSource.GITHUB]

    def test_parse_jira(self) -> None:
        """Parses 'jira' to DataSource.JIRA."""
        from src.github_analyzer.cli.main import parse_sources_list

        result = parse_sources_list("jira")
        assert result == [DataSource.JIRA]

    def test_parse_both(self) -> None:
        """Parses 'github,jira' to both DataSources."""
        from src.github_analyzer.cli.main import parse_sources_list

        result = parse_sources_list("github,jira")
        assert DataSource.GITHUB in result
        assert DataSource.JIRA in result

    def test_parse_both_reversed(self) -> None:
        """Parses 'jira,github' to both DataSources."""
        from src.github_analyzer.cli.main import parse_sources_list

        result = parse_sources_list("jira,github")
        assert DataSource.GITHUB in result
        assert DataSource.JIRA in result

    def test_parse_with_spaces(self) -> None:
        """Parses 'github, jira' (with spaces) correctly."""
        from src.github_analyzer.cli.main import parse_sources_list

        result = parse_sources_list("github, jira")
        assert DataSource.GITHUB in result
        assert DataSource.JIRA in result

    def test_parse_invalid_raises(self) -> None:
        """Invalid source name raises ValueError."""
        from src.github_analyzer.cli.main import parse_sources_list

        with pytest.raises(ValueError, match="Unknown source"):
            parse_sources_list("invalid")

    def test_parse_case_insensitive(self) -> None:
        """Parses sources case-insensitively."""
        from src.github_analyzer.cli.main import parse_sources_list

        result = parse_sources_list("GITHUB,JIRA")
        assert DataSource.GITHUB in result
        assert DataSource.JIRA in result


class TestAutoDetectSources:
    """Tests for auto_detect_sources function."""

    def test_detect_github_only(self) -> None:
        """Detects GitHub only when GITHUB_TOKEN is set."""
        from src.github_analyzer.cli.main import auto_detect_sources

        env = {"GITHUB_TOKEN": "ghp_test123456789012345678901234567890ab"}
        with mock.patch.dict(os.environ, env, clear=True):
            result = auto_detect_sources()

        assert DataSource.GITHUB in result
        assert DataSource.JIRA not in result

    def test_detect_jira_only(self) -> None:
        """Detects Jira only when Jira credentials are set."""
        from src.github_analyzer.cli.main import auto_detect_sources

        env = {
            "JIRA_URL": "https://company.atlassian.net",
            "JIRA_EMAIL": "user@company.com",
            "JIRA_API_TOKEN": "test-token",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            result = auto_detect_sources()

        assert DataSource.JIRA in result
        assert DataSource.GITHUB not in result

    def test_detect_both(self) -> None:
        """Detects both sources when all credentials are set."""
        from src.github_analyzer.cli.main import auto_detect_sources

        env = {
            "GITHUB_TOKEN": "ghp_test123456789012345678901234567890ab",
            "JIRA_URL": "https://company.atlassian.net",
            "JIRA_EMAIL": "user@company.com",
            "JIRA_API_TOKEN": "test-token",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            result = auto_detect_sources()

        assert DataSource.GITHUB in result
        assert DataSource.JIRA in result

    def test_detect_none(self) -> None:
        """Returns empty list when no credentials are set."""
        from src.github_analyzer.cli.main import auto_detect_sources

        with mock.patch.dict(os.environ, {}, clear=True):
            result = auto_detect_sources()

        assert result == []

    def test_detect_partial_jira_credentials(self) -> None:
        """Does not detect Jira with partial credentials."""
        from src.github_analyzer.cli.main import auto_detect_sources

        env = {
            "JIRA_URL": "https://company.atlassian.net",
            # Missing JIRA_EMAIL and JIRA_API_TOKEN
        }
        with mock.patch.dict(os.environ, env, clear=True):
            result = auto_detect_sources()

        assert DataSource.JIRA not in result


class TestSourcesValidation:
    """Tests for source validation logic."""

    def test_validate_github_without_token_raises(self) -> None:
        """Raises error when github source requested but no token."""
        from src.github_analyzer.cli.main import validate_sources

        sources = [DataSource.GITHUB]
        with mock.patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GitHub.*GITHUB_TOKEN"):
                validate_sources(sources)

    def test_validate_jira_without_credentials_raises(self) -> None:
        """Raises error when jira source requested but no credentials."""
        from src.github_analyzer.cli.main import validate_sources

        sources = [DataSource.JIRA]
        with mock.patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Jira.*credentials"):
                validate_sources(sources)

    def test_validate_github_with_token_passes(self) -> None:
        """Passes validation when github source and token present."""
        from src.github_analyzer.cli.main import validate_sources

        sources = [DataSource.GITHUB]
        env = {"GITHUB_TOKEN": "ghp_test123456789012345678901234567890ab"}
        with mock.patch.dict(os.environ, env, clear=True):
            # Should not raise
            validate_sources(sources)

    def test_validate_jira_with_credentials_passes(self) -> None:
        """Passes validation when jira source and credentials present."""
        from src.github_analyzer.cli.main import validate_sources

        sources = [DataSource.JIRA]
        env = {
            "JIRA_URL": "https://company.atlassian.net",
            "JIRA_EMAIL": "user@company.com",
            "JIRA_API_TOKEN": "test-token",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            # Should not raise
            validate_sources(sources)
