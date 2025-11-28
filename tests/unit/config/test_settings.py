"""Unit tests for configuration settings module.

Tests cover:
- T014: AnalyzerConfig.from_env() loading from environment
- T015: Token format validation including whitespace stripping
- T016: Missing token error handling
- T017: Token never appears in exception messages
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest


class TestAnalyzerConfigFromEnv:
    """Test AnalyzerConfig.from_env() classmethod (T014)."""

    def test_loads_token_from_environment(self, mock_env_token: str) -> None:
        """Given GITHUB_TOKEN is set, config loads successfully."""
        from src.github_analyzer.config.settings import AnalyzerConfig

        config = AnalyzerConfig.from_env()

        assert config.github_token == mock_env_token

    def test_uses_default_values(self, mock_env_token: str) -> None:
        """Given only token is set, other values use defaults."""
        from src.github_analyzer.config.settings import AnalyzerConfig

        config = AnalyzerConfig.from_env()

        assert config.output_dir == "github_export"
        assert config.repos_file == "repos.txt"
        assert config.days == 30
        assert config.per_page == 100
        assert config.verbose is True
        assert config.timeout == 30
        assert config.max_pages == 50

    def test_loads_optional_settings_from_env(self) -> None:
        """Given optional env vars are set, config loads them."""
        from src.github_analyzer.config.settings import AnalyzerConfig

        env = {
            "GITHUB_TOKEN": "ghp_test1234567890abcdefghijklmnopqrstuvwxyz",
            "GITHUB_ANALYZER_OUTPUT_DIR": "custom_output",
            "GITHUB_ANALYZER_DAYS": "60",
            "GITHUB_ANALYZER_VERBOSE": "false",
        }
        with patch.dict(os.environ, env, clear=True):
            config = AnalyzerConfig.from_env()

        assert config.output_dir == "custom_output"
        assert config.days == 60
        assert config.verbose is False


class TestTokenFormatValidation:
    """Test token format validation (T015)."""

    def test_strips_whitespace_from_token(self) -> None:
        """Given token with whitespace, whitespace is stripped."""
        from src.github_analyzer.config.settings import AnalyzerConfig

        token_with_whitespace = "  ghp_test1234567890abcdefghijklmnopqrstuvwxyz  \n"
        with patch.dict(os.environ, {"GITHUB_TOKEN": token_with_whitespace}):
            config = AnalyzerConfig.from_env()

        # Token should be stripped
        assert config.github_token == token_with_whitespace.strip()
        assert not config.github_token.startswith(" ")
        assert not config.github_token.endswith(" ")
        assert "\n" not in config.github_token

    def test_validates_token_format_classic(self) -> None:
        """Given classic token format (ghp_), validation passes."""
        from src.github_analyzer.config.validation import validate_token_format

        assert validate_token_format("ghp_abcdefghijklmnopqrstuvwxyz123456") is True

    def test_validates_token_format_fine_grained(self) -> None:
        """Given fine-grained token format (github_pat_), validation passes."""
        from src.github_analyzer.config.validation import validate_token_format

        assert validate_token_format("github_pat_abcdefghijklmnopqrstuvwxyz") is True

    def test_validates_token_format_oauth(self) -> None:
        """Given OAuth token format (gho_), validation passes."""
        from src.github_analyzer.config.validation import validate_token_format

        assert validate_token_format("gho_abcdefghijklmnopqrstuvwxyz123456") is True

    def test_rejects_invalid_token_format(self) -> None:
        """Given invalid token format, validation fails."""
        from src.github_analyzer.config.validation import validate_token_format

        assert validate_token_format("invalid_token") is False
        assert validate_token_format("") is False
        assert validate_token_format("gh_tooshort") is False


class TestMissingTokenError:
    """Test missing token error handling (T016)."""

    def test_raises_error_when_token_not_set(self, mock_env_no_token: None) -> None:
        """Given GITHUB_TOKEN is not set, ConfigurationError is raised."""
        from src.github_analyzer.config.settings import AnalyzerConfig
        from src.github_analyzer.core.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError) as exc_info:
            AnalyzerConfig.from_env()

        assert "GITHUB_TOKEN" in str(exc_info.value)
        assert "environment variable" in str(exc_info.value).lower()

    def test_raises_error_when_token_empty(self) -> None:
        """Given GITHUB_TOKEN is empty string, ConfigurationError is raised."""
        from src.github_analyzer.config.settings import AnalyzerConfig
        from src.github_analyzer.core.exceptions import ConfigurationError

        with patch.dict(os.environ, {"GITHUB_TOKEN": ""}):
            with pytest.raises(ConfigurationError) as exc_info:
                AnalyzerConfig.from_env()

        assert "GITHUB_TOKEN" in str(exc_info.value)

    def test_raises_error_when_token_only_whitespace(self) -> None:
        """Given GITHUB_TOKEN is only whitespace, ConfigurationError is raised."""
        from src.github_analyzer.config.settings import AnalyzerConfig
        from src.github_analyzer.core.exceptions import ConfigurationError

        with patch.dict(os.environ, {"GITHUB_TOKEN": "   \n\t  "}):
            with pytest.raises(ConfigurationError) as exc_info:
                AnalyzerConfig.from_env()

        assert "GITHUB_TOKEN" in str(exc_info.value)


class TestTokenNeverInExceptions:
    """Test that token values never appear in exceptions (T017)."""

    def test_token_not_in_validation_error_message(self) -> None:
        """Given invalid token, error message does not contain token value."""
        from src.github_analyzer.config.settings import AnalyzerConfig
        from src.github_analyzer.core.exceptions import ValidationError

        invalid_token = "invalid_secret_token_12345"
        with patch.dict(os.environ, {"GITHUB_TOKEN": invalid_token}):
            try:
                config = AnalyzerConfig.from_env()
                config.validate()
            except ValidationError as e:
                error_message = str(e)
                assert invalid_token not in error_message
                # Also check partial token doesn't appear
                assert "invalid_secret" not in error_message
                assert "12345" not in error_message

    def test_token_not_in_config_repr(self, mock_env_token: str) -> None:
        """Given config object, repr does not contain token value."""
        from src.github_analyzer.config.settings import AnalyzerConfig

        config = AnalyzerConfig.from_env()

        repr_str = repr(config)
        assert mock_env_token not in repr_str
        # Check that token is masked
        assert "[MASKED]" in repr_str or "***" in repr_str

    def test_token_not_in_config_str(self, mock_env_token: str) -> None:
        """Given config object, str does not contain token value."""
        from src.github_analyzer.config.settings import AnalyzerConfig

        config = AnalyzerConfig.from_env()

        str_repr = str(config)
        assert mock_env_token not in str_repr

    def test_exception_details_do_not_leak_token(self) -> None:
        """Given exception with details, token does not appear in any field."""
        from src.github_analyzer.core.exceptions import ConfigurationError

        token = "ghp_supersecrettoken123456789"

        # Create exception that might accidentally include token
        error = ConfigurationError(
            message="Authentication failed",
            details="Check your GITHUB_TOKEN configuration",
        )

        # Verify token not in any string representation
        assert token not in str(error)
        assert token not in repr(error)
        assert token not in error.message
        assert error.details is None or token not in error.details
