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


class TestGetBoolEnv:
    """Test _get_bool_env helper function."""

    def test_returns_true_for_true_values(self) -> None:
        """Given true-like values, returns True."""
        from src.github_analyzer.config.settings import _get_bool_env

        for value in ("true", "TRUE", "True", "1", "yes", "YES", "on", "ON"):
            with patch.dict(os.environ, {"TEST_BOOL": value}):
                assert _get_bool_env("TEST_BOOL", False) is True

    def test_returns_false_for_false_values(self) -> None:
        """Given false-like values, returns False."""
        from src.github_analyzer.config.settings import _get_bool_env

        for value in ("false", "FALSE", "False", "0", "no", "NO", "off", "OFF"):
            with patch.dict(os.environ, {"TEST_BOOL": value}):
                assert _get_bool_env("TEST_BOOL", True) is False

    def test_returns_default_for_unset(self) -> None:
        """Given unset variable, returns default."""
        from src.github_analyzer.config.settings import _get_bool_env

        with patch.dict(os.environ, {}, clear=True):
            assert _get_bool_env("UNSET_VAR", True) is True
            assert _get_bool_env("UNSET_VAR", False) is False

    def test_returns_default_for_invalid(self) -> None:
        """Given invalid value, returns default."""
        from src.github_analyzer.config.settings import _get_bool_env

        with patch.dict(os.environ, {"TEST_BOOL": "invalid"}):
            assert _get_bool_env("TEST_BOOL", True) is True
            assert _get_bool_env("TEST_BOOL", False) is False


class TestGetIntEnv:
    """Test _get_int_env helper function."""

    def test_returns_integer_value(self) -> None:
        """Given valid integer string, returns integer."""
        from src.github_analyzer.config.settings import _get_int_env

        with patch.dict(os.environ, {"TEST_INT": "42"}):
            assert _get_int_env("TEST_INT", 0) == 42

    def test_returns_default_for_unset(self) -> None:
        """Given unset variable, returns default."""
        from src.github_analyzer.config.settings import _get_int_env

        with patch.dict(os.environ, {}, clear=True):
            assert _get_int_env("UNSET_VAR", 100) == 100

    def test_returns_default_for_invalid(self) -> None:
        """Given non-integer string, returns default."""
        from src.github_analyzer.config.settings import _get_int_env

        with patch.dict(os.environ, {"TEST_INT": "not_a_number"}):
            assert _get_int_env("TEST_INT", 50) == 50

    def test_returns_default_for_empty(self) -> None:
        """Given empty string, returns default."""
        from src.github_analyzer.config.settings import _get_int_env

        with patch.dict(os.environ, {"TEST_INT": ""}):
            assert _get_int_env("TEST_INT", 25) == 25


class TestAnalyzerConfigValidate:
    """Test AnalyzerConfig.validate method."""

    def test_valid_config_passes(self, mock_env_token: str) -> None:
        """Given valid config, validate passes."""
        from src.github_analyzer.config.settings import AnalyzerConfig

        config = AnalyzerConfig.from_env()
        # Should not raise
        config.validate()

    def test_invalid_token_format_raises(self) -> None:
        """Given invalid token format, raises ValidationError."""
        from src.github_analyzer.config.settings import AnalyzerConfig
        from src.github_analyzer.core.exceptions import ValidationError

        with patch.dict(os.environ, {"GITHUB_TOKEN": "invalid_token_format"}):
            config = AnalyzerConfig.from_env()
            with pytest.raises(ValidationError) as exc_info:
                config.validate()

            assert "token" in str(exc_info.value).lower()

    def test_zero_days_raises(self, mock_env_token: str) -> None:
        """Given days=0, raises ValidationError."""
        from src.github_analyzer.config.settings import AnalyzerConfig
        from src.github_analyzer.core.exceptions import ValidationError

        config = AnalyzerConfig.from_env()
        object.__setattr__(config, "days", 0)

        with pytest.raises(ValidationError) as exc_info:
            config.validate()

        assert "days" in str(exc_info.value).lower()

    def test_negative_days_raises(self, mock_env_token: str) -> None:
        """Given negative days, raises ValidationError."""
        from src.github_analyzer.config.settings import AnalyzerConfig
        from src.github_analyzer.core.exceptions import ValidationError

        config = AnalyzerConfig.from_env()
        object.__setattr__(config, "days", -5)

        with pytest.raises(ValidationError) as exc_info:
            config.validate()

        assert "days" in str(exc_info.value).lower()

    def test_days_over_365_raises(self, mock_env_token: str) -> None:
        """Given days > 365, raises ValidationError."""
        from src.github_analyzer.config.settings import AnalyzerConfig
        from src.github_analyzer.core.exceptions import ValidationError

        config = AnalyzerConfig.from_env()
        object.__setattr__(config, "days", 400)

        with pytest.raises(ValidationError) as exc_info:
            config.validate()

        assert "days" in str(exc_info.value).lower()

    def test_per_page_zero_raises(self, mock_env_token: str) -> None:
        """Given per_page=0, raises ValidationError."""
        from src.github_analyzer.config.settings import AnalyzerConfig
        from src.github_analyzer.core.exceptions import ValidationError

        config = AnalyzerConfig.from_env()
        object.__setattr__(config, "per_page", 0)

        with pytest.raises(ValidationError) as exc_info:
            config.validate()

        assert "per_page" in str(exc_info.value).lower()

    def test_per_page_over_100_raises(self, mock_env_token: str) -> None:
        """Given per_page > 100, raises ValidationError."""
        from src.github_analyzer.config.settings import AnalyzerConfig
        from src.github_analyzer.core.exceptions import ValidationError

        config = AnalyzerConfig.from_env()
        object.__setattr__(config, "per_page", 150)

        with pytest.raises(ValidationError) as exc_info:
            config.validate()

        assert "per_page" in str(exc_info.value).lower()

    def test_zero_timeout_raises(self, mock_env_token: str) -> None:
        """Given timeout=0, raises ValidationError."""
        from src.github_analyzer.config.settings import AnalyzerConfig
        from src.github_analyzer.core.exceptions import ValidationError

        config = AnalyzerConfig.from_env()
        object.__setattr__(config, "timeout", 0)

        with pytest.raises(ValidationError) as exc_info:
            config.validate()

        assert "timeout" in str(exc_info.value).lower()

    def test_timeout_over_300_raises(self, mock_env_token: str) -> None:
        """Given timeout > 300, raises ValidationError."""
        from src.github_analyzer.config.settings import AnalyzerConfig
        from src.github_analyzer.core.exceptions import ValidationError

        config = AnalyzerConfig.from_env()
        object.__setattr__(config, "timeout", 500)

        with pytest.raises(ValidationError) as exc_info:
            config.validate()

        assert "timeout" in str(exc_info.value).lower()


class TestAnalyzerConfigToDict:
    """Test AnalyzerConfig.to_dict method."""

    def test_returns_dict_with_all_fields(self, mock_env_token: str) -> None:
        """Given config, to_dict returns all fields."""
        from src.github_analyzer.config.settings import AnalyzerConfig

        config = AnalyzerConfig.from_env()
        result = config.to_dict()

        assert "github_token" in result
        assert "output_dir" in result
        assert "repos_file" in result
        assert "days" in result
        assert "per_page" in result
        assert "verbose" in result
        assert "timeout" in result
        assert "max_pages" in result

    def test_masks_token_in_dict(self, mock_env_token: str) -> None:
        """Given config, to_dict masks token."""
        from src.github_analyzer.config.settings import AnalyzerConfig

        config = AnalyzerConfig.from_env()
        result = config.to_dict()

        assert result["github_token"] == "[MASKED]"
        assert mock_env_token not in str(result)

    def test_preserves_other_values(self, mock_env_token: str) -> None:
        """Given config, to_dict preserves non-token values."""
        from src.github_analyzer.config.settings import AnalyzerConfig

        config = AnalyzerConfig.from_env()
        result = config.to_dict()

        assert result["output_dir"] == config.output_dir
        assert result["repos_file"] == config.repos_file
        assert result["days"] == config.days
        assert result["per_page"] == config.per_page
        assert result["verbose"] == config.verbose
        assert result["timeout"] == config.timeout
        assert result["max_pages"] == config.max_pages
