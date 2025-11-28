"""Unit tests for JiraConfig and DataSource.

Tests for:
- JiraConfig dataclass creation and validation
- JiraConfig.from_env() with various environment configurations
- Token masking in __repr__, __str__, to_dict
- DataSource enum values
"""

from __future__ import annotations

import os
from unittest import mock

import pytest

from src.github_analyzer.config.settings import DataSource, JiraConfig
from src.github_analyzer.core.exceptions import ValidationError


class TestDataSource:
    """Tests for DataSource enum."""

    def test_github_value(self) -> None:
        """DataSource.GITHUB has correct value."""
        assert DataSource.GITHUB.value == "github"

    def test_jira_value(self) -> None:
        """DataSource.JIRA has correct value."""
        assert DataSource.JIRA.value == "jira"

    def test_enum_members(self) -> None:
        """DataSource has exactly two members."""
        assert len(DataSource) == 2
        assert DataSource.GITHUB in DataSource
        assert DataSource.JIRA in DataSource


class TestJiraConfigCreation:
    """Tests for JiraConfig dataclass creation."""

    def test_create_with_required_fields(self) -> None:
        """JiraConfig can be created with required fields."""
        config = JiraConfig(
            jira_url="https://company.atlassian.net",
            jira_email="user@company.com",
            jira_api_token="test-token",
        )
        assert config.jira_url == "https://company.atlassian.net"
        assert config.jira_email == "user@company.com"
        assert config.jira_api_token == "test-token"

    def test_default_values(self) -> None:
        """JiraConfig has correct default values."""
        config = JiraConfig(
            jira_url="https://company.atlassian.net",
            jira_email="user@company.com",
            jira_api_token="test-token",
        )
        assert config.jira_projects_file == "jira_projects.txt"
        assert config.timeout == 30

    def test_url_trailing_slash_removed(self) -> None:
        """Trailing slash is removed from URL."""
        config = JiraConfig(
            jira_url="https://company.atlassian.net/",
            jira_email="user@company.com",
            jira_api_token="test-token",
        )
        assert config.jira_url == "https://company.atlassian.net"

    def test_whitespace_stripped(self) -> None:
        """Whitespace is stripped from all fields."""
        config = JiraConfig(
            jira_url="  https://company.atlassian.net  ",
            jira_email="  user@company.com  ",
            jira_api_token="  test-token  ",
        )
        assert config.jira_url == "https://company.atlassian.net"
        assert config.jira_email == "user@company.com"
        assert config.jira_api_token == "test-token"


class TestJiraConfigApiVersionDetection:
    """Tests for API version auto-detection."""

    def test_cloud_url_detects_v3(self) -> None:
        """Atlassian Cloud URL auto-detects API v3."""
        config = JiraConfig(
            jira_url="https://company.atlassian.net",
            jira_email="user@company.com",
            jira_api_token="test-token",
        )
        assert config.api_version == "3"

    def test_server_url_detects_v2(self) -> None:
        """On-premises URL auto-detects API v2."""
        config = JiraConfig(
            jira_url="https://jira.company.com",
            jira_email="user@company.com",
            jira_api_token="test-token",
        )
        assert config.api_version == "2"

    def test_explicit_version_preserved(self) -> None:
        """Explicit API version is preserved."""
        config = JiraConfig(
            jira_url="https://company.atlassian.net",
            jira_email="user@company.com",
            jira_api_token="test-token",
            api_version="2",
        )
        assert config.api_version == "2"


class TestJiraConfigFromEnv:
    """Tests for JiraConfig.from_env()."""

    def test_from_env_with_all_vars(self) -> None:
        """from_env returns config when all vars are set."""
        env = {
            "JIRA_URL": "https://company.atlassian.net",
            "JIRA_EMAIL": "user@company.com",
            "JIRA_API_TOKEN": "test-token",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            config = JiraConfig.from_env()
            assert config is not None
            assert config.jira_url == "https://company.atlassian.net"
            assert config.jira_email == "user@company.com"
            assert config.jira_api_token == "test-token"

    def test_from_env_missing_url(self) -> None:
        """from_env returns None when URL is missing."""
        env = {
            "JIRA_EMAIL": "user@company.com",
            "JIRA_API_TOKEN": "test-token",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            config = JiraConfig.from_env()
            assert config is None

    def test_from_env_missing_email(self) -> None:
        """from_env returns None when email is missing."""
        env = {
            "JIRA_URL": "https://company.atlassian.net",
            "JIRA_API_TOKEN": "test-token",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            config = JiraConfig.from_env()
            assert config is None

    def test_from_env_missing_token(self) -> None:
        """from_env returns None when token is missing."""
        env = {
            "JIRA_URL": "https://company.atlassian.net",
            "JIRA_EMAIL": "user@company.com",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            config = JiraConfig.from_env()
            assert config is None

    def test_from_env_all_missing(self) -> None:
        """from_env returns None when all vars are missing."""
        with mock.patch.dict(os.environ, {}, clear=True):
            config = JiraConfig.from_env()
            assert config is None

    def test_from_env_empty_values(self) -> None:
        """from_env returns None when values are empty strings."""
        env = {
            "JIRA_URL": "",
            "JIRA_EMAIL": "",
            "JIRA_API_TOKEN": "",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            config = JiraConfig.from_env()
            assert config is None

    def test_from_env_whitespace_only(self) -> None:
        """from_env returns None when values are whitespace only."""
        env = {
            "JIRA_URL": "   ",
            "JIRA_EMAIL": "   ",
            "JIRA_API_TOKEN": "   ",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            config = JiraConfig.from_env()
            assert config is None

    def test_from_env_with_optional_vars(self) -> None:
        """from_env respects optional environment variables."""
        env = {
            "JIRA_URL": "https://company.atlassian.net",
            "JIRA_EMAIL": "user@company.com",
            "JIRA_API_TOKEN": "test-token",
            "JIRA_PROJECTS_FILE": "custom_projects.txt",
            "JIRA_TIMEOUT": "60",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            config = JiraConfig.from_env()
            assert config is not None
            assert config.jira_projects_file == "custom_projects.txt"
            assert config.timeout == 60


class TestJiraConfigValidation:
    """Tests for JiraConfig.validate()."""

    def test_validate_valid_config(self) -> None:
        """validate() passes for valid config."""
        config = JiraConfig(
            jira_url="https://company.atlassian.net",
            jira_email="user@company.com",
            jira_api_token="test-token",
        )
        # Should not raise
        config.validate()

    def test_validate_invalid_url_http(self) -> None:
        """validate() raises for HTTP URL."""
        config = JiraConfig(
            jira_url="http://company.atlassian.net",
            jira_email="user@company.com",
            jira_api_token="test-token",
        )
        with pytest.raises(ValidationError, match="Invalid Jira URL"):
            config.validate()

    def test_validate_invalid_url_no_scheme(self) -> None:
        """validate() raises for URL without scheme."""
        config = JiraConfig(
            jira_url="company.atlassian.net",
            jira_email="user@company.com",
            jira_api_token="test-token",
        )
        with pytest.raises(ValidationError, match="Invalid Jira URL"):
            config.validate()

    def test_validate_invalid_email(self) -> None:
        """validate() raises for invalid email."""
        config = JiraConfig(
            jira_url="https://company.atlassian.net",
            jira_email="invalid-email",
            jira_api_token="test-token",
        )
        with pytest.raises(ValidationError, match="Invalid Jira email"):
            config.validate()

    def test_validate_invalid_timeout_zero(self) -> None:
        """validate() raises for zero timeout."""
        config = JiraConfig(
            jira_url="https://company.atlassian.net",
            jira_email="user@company.com",
            jira_api_token="test-token",
            timeout=0,
        )
        with pytest.raises(ValidationError, match="Invalid timeout"):
            config.validate()

    def test_validate_invalid_timeout_too_large(self) -> None:
        """validate() raises for timeout > 300."""
        config = JiraConfig(
            jira_url="https://company.atlassian.net",
            jira_email="user@company.com",
            jira_api_token="test-token",
            timeout=500,
        )
        with pytest.raises(ValidationError, match="Invalid timeout"):
            config.validate()


class TestJiraConfigTokenMasking:
    """Tests for token masking in JiraConfig representations."""

    def test_repr_masks_token(self) -> None:
        """__repr__ masks the token value."""
        config = JiraConfig(
            jira_url="https://company.atlassian.net",
            jira_email="user@company.com",
            jira_api_token="super-secret-token",
        )
        repr_str = repr(config)
        assert "super-secret-token" not in repr_str
        assert "[MASKED]" in repr_str

    def test_str_masks_token(self) -> None:
        """__str__ masks the token value."""
        config = JiraConfig(
            jira_url="https://company.atlassian.net",
            jira_email="user@company.com",
            jira_api_token="super-secret-token",
        )
        str_str = str(config)
        assert "super-secret-token" not in str_str
        assert "[MASKED]" in str_str

    def test_to_dict_masks_token(self) -> None:
        """to_dict() masks the token value."""
        config = JiraConfig(
            jira_url="https://company.atlassian.net",
            jira_email="user@company.com",
            jira_api_token="super-secret-token",
        )
        d = config.to_dict()
        assert d["jira_api_token"] == "[MASKED]"
        assert "super-secret-token" not in str(d)

    def test_to_dict_includes_all_fields(self) -> None:
        """to_dict() includes all configuration fields."""
        config = JiraConfig(
            jira_url="https://company.atlassian.net",
            jira_email="user@company.com",
            jira_api_token="test-token",
            jira_projects_file="projects.txt",
            timeout=60,
        )
        d = config.to_dict()
        assert d["jira_url"] == "https://company.atlassian.net"
        assert d["jira_email"] == "user@company.com"
        assert d["jira_projects_file"] == "projects.txt"
        assert d["timeout"] == 60
        assert "api_version" in d
