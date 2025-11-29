"""Unit tests for security utilities.

Tests cover:
- Path traversal prevention (FR-001, FR-002, FR-013)
- CSV formula injection protection (FR-004, FR-005)
- File permission checks (FR-007, FR-008)
- Content-Type header validation (FR-006)
- API request audit logging (FR-009, FR-010)
- Timeout warning validation (FR-011)
"""

from __future__ import annotations

import logging
import os
import platform
import stat
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.github_analyzer.core.exceptions import ValidationError
from src.github_analyzer.core.security import (
    API_LOG_PREFIX,
    DEFAULT_SECURE_MODE,
    DEFAULT_TIMEOUT_WARN_THRESHOLD,
    FORMULA_TRIGGERS,
    SECURITY_LOG_PREFIX,
    check_file_permissions,
    escape_csv_formula,
    escape_csv_row,
    log_api_request,
    set_secure_permissions,
    validate_content_type,
    validate_output_path,
    validate_timeout,
)


class TestValidateOutputPath:
    """Tests for validate_output_path function (FR-001, FR-002, FR-013)."""

    def test_valid_relative_path_returns_resolved(self, tmp_path: Path) -> None:
        """Valid relative path within base returns resolved Path."""
        result = validate_output_path("subdir", base_dir=tmp_path)
        assert result == tmp_path / "subdir"
        assert result.is_absolute()

    def test_valid_nested_path_returns_resolved(self, tmp_path: Path) -> None:
        """Valid nested path within base returns resolved Path."""
        result = validate_output_path("a/b/c", base_dir=tmp_path)
        assert result == tmp_path / "a" / "b" / "c"

    def test_valid_absolute_path_within_base(self, tmp_path: Path) -> None:
        """Valid absolute path within base returns resolved Path."""
        abs_path = tmp_path / "reports"
        result = validate_output_path(str(abs_path), base_dir=tmp_path)
        assert result == abs_path

    def test_current_dir_is_valid(self, tmp_path: Path) -> None:
        """Current directory (.) is valid."""
        result = validate_output_path(".", base_dir=tmp_path)
        assert result == tmp_path

    def test_path_traversal_single_level_rejected(self, tmp_path: Path) -> None:
        """Single level path traversal (..) is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_output_path("..", base_dir=tmp_path)
        assert "Output path must be within" in str(exc_info.value)

    def test_path_traversal_multiple_levels_rejected(self, tmp_path: Path) -> None:
        """Multiple level path traversal (../../../) is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_output_path("../../../etc", base_dir=tmp_path)
        assert "Output path must be within" in str(exc_info.value)

    def test_path_traversal_hidden_in_path_rejected(self, tmp_path: Path) -> None:
        """Path traversal hidden in path (foo/../../bar) is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_output_path("foo/../../bar", base_dir=tmp_path)
        assert "Output path must be within" in str(exc_info.value)

    def test_absolute_path_outside_base_rejected(self, tmp_path: Path) -> None:
        """Absolute path outside base directory is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_output_path("/tmp/malicious", base_dir=tmp_path)
        assert "Output path must be within" in str(exc_info.value)

    def test_error_message_contains_base_directory(self, tmp_path: Path) -> None:
        """Error message format matches FR-001 specification."""
        with pytest.raises(ValidationError) as exc_info:
            validate_output_path("../escape", base_dir=tmp_path)
        # Verify error message format per FR-001
        assert str(tmp_path.resolve()) in str(exc_info.value)

    def test_symlink_resolved_before_validation(self, tmp_path: Path) -> None:
        """Symlinks are resolved before validation (FR-013)."""
        # Create a subdirectory and a symlink pointing outside
        subdir = tmp_path / "allowed"
        subdir.mkdir()
        outside = tmp_path.parent / "outside"

        # Create symlink inside allowed pointing to outside
        symlink = subdir / "escape_link"
        try:
            symlink.symlink_to(outside)
        except OSError:
            pytest.skip("Symlinks not supported on this system")

        # Symlink should be resolved and rejected since target is outside
        with pytest.raises(ValidationError):
            validate_output_path(str(symlink), base_dir=subdir)

    def test_symlink_to_valid_location_accepted(self, tmp_path: Path) -> None:
        """Symlinks pointing to valid locations are accepted (FR-013)."""
        # Create target directory inside base
        target = tmp_path / "real_dir"
        target.mkdir()

        # Create symlink pointing to target
        symlink = tmp_path / "link_to_real"
        try:
            symlink.symlink_to(target)
        except OSError:
            pytest.skip("Symlinks not supported on this system")

        # Symlink should be resolved and accepted
        result = validate_output_path(str(symlink), base_dir=tmp_path)
        assert result == target

    def test_default_base_dir_is_cwd(self) -> None:
        """Default base directory is current working directory."""
        cwd = Path.cwd()
        # A path in cwd should be valid
        result = validate_output_path(".")
        assert result == cwd

    def test_accepts_path_object(self, tmp_path: Path) -> None:
        """Function accepts Path objects as input."""
        path_obj = Path("subdir")
        result = validate_output_path(path_obj, base_dir=tmp_path)
        assert result == tmp_path / "subdir"


class TestEscapeCsvFormula:
    """Tests for escape_csv_formula function (FR-004, FR-005)."""

    @pytest.mark.parametrize(
        "trigger",
        list(FORMULA_TRIGGERS),
        ids=["equals", "plus", "minus", "at", "tab", "cr"],
    )
    def test_escapes_all_trigger_characters(self, trigger: str) -> None:
        """All formula trigger characters are escaped (FR-004)."""
        value = f"{trigger}MALICIOUS"
        result = escape_csv_formula(value)
        assert result == f"'{trigger}MALICIOUS"
        assert result.startswith("'")

    def test_escapes_equals_formula(self) -> None:
        """Equals sign is escaped (most common injection)."""
        result = escape_csv_formula("=SUM(A1:A10)")
        assert result == "'=SUM(A1:A10)"

    def test_escapes_plus_formula(self) -> None:
        """Plus sign is escaped."""
        result = escape_csv_formula("+1+2")
        assert result == "'+1+2"

    def test_escapes_minus_formula(self) -> None:
        """Minus sign is escaped."""
        result = escape_csv_formula("-1-2")
        assert result == "'-1-2"

    def test_escapes_at_symbol(self) -> None:
        """At symbol is escaped."""
        result = escape_csv_formula("@SUM(A1)")
        assert result == "'@SUM(A1)"

    def test_escapes_tab_character(self) -> None:
        """Tab character is escaped."""
        result = escape_csv_formula("\tvalue")
        assert result == "'\tvalue"

    def test_escapes_carriage_return(self) -> None:
        """Carriage return is escaped."""
        result = escape_csv_formula("\rvalue")
        assert result == "'\rvalue"

    def test_normal_text_unchanged(self) -> None:
        """Normal text without triggers is unchanged (FR-005)."""
        result = escape_csv_formula("Normal text")
        assert result == "Normal text"

    def test_empty_string_unchanged(self) -> None:
        """Empty string is returned as-is."""
        result = escape_csv_formula("")
        assert result == ""

    def test_none_converted_to_empty_string(self) -> None:
        """None is converted to empty string."""
        result = escape_csv_formula(None)
        assert result == ""

    def test_integer_converted_to_string(self) -> None:
        """Integer values are converted to strings."""
        result = escape_csv_formula(42)
        assert result == "42"

    def test_float_converted_to_string(self) -> None:
        """Float values are converted to strings."""
        result = escape_csv_formula(3.14)
        assert result == "3.14"

    def test_data_recoverable_after_escaping(self) -> None:
        """Original data can be recovered by stripping quote (FR-005)."""
        original = "=SUM(A1)"
        escaped = escape_csv_formula(original)
        recovered = escaped[1:] if escaped.startswith("'") else escaped
        assert recovered == original

    def test_trigger_in_middle_not_escaped(self) -> None:
        """Trigger character in middle of string is not escaped."""
        result = escape_csv_formula("foo=bar")
        assert result == "foo=bar"  # No escaping needed

    def test_multiple_triggers_only_first_matters(self) -> None:
        """Only first character determines if escaping is needed."""
        result = escape_csv_formula("=+@-")
        assert result == "'=+@-"  # Single quote prefix


class TestEscapeCsvRow:
    """Tests for escape_csv_row function."""

    def test_escapes_all_values_in_row(self) -> None:
        """All values in the row are escaped."""
        row = {"name": "=DROP TABLE", "count": 42}
        result = escape_csv_row(row)
        assert result["name"] == "'=DROP TABLE"
        assert result["count"] == "42"

    def test_preserves_normal_values(self) -> None:
        """Normal values are preserved unchanged."""
        row = {"name": "John", "email": "john@example.com"}
        result = escape_csv_row(row)
        assert result["name"] == "John"
        assert result["email"] == "john@example.com"

    def test_empty_row_returns_empty(self) -> None:
        """Empty dictionary returns empty dictionary."""
        result = escape_csv_row({})
        assert result == {}

    def test_mixed_row_handles_all_types(self) -> None:
        """Row with mixed types is handled correctly."""
        row = {"formula": "=cmd", "number": 100, "text": "hello", "none": None}
        result = escape_csv_row(row)
        assert result["formula"] == "'=cmd"
        assert result["number"] == "100"
        assert result["text"] == "hello"
        assert result["none"] == ""


class TestCheckFilePermissions:
    """Tests for check_file_permissions function (FR-007)."""

    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix-only test")
    def test_secure_permissions_returns_true(self, tmp_path: Path) -> None:
        """File with secure permissions (600) returns True."""
        test_file = tmp_path / "secure.txt"
        test_file.write_text("secret")
        test_file.chmod(0o600)

        result = check_file_permissions(test_file)
        assert result is True

    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix-only test")
    def test_world_readable_returns_false(self, tmp_path: Path) -> None:
        """File with world-readable permissions (644) returns False."""
        test_file = tmp_path / "permissive.txt"
        test_file.write_text("exposed")
        test_file.chmod(0o644)

        result = check_file_permissions(test_file)
        assert result is False

    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix-only test")
    def test_group_readable_returns_false(self, tmp_path: Path) -> None:
        """File with group-readable permissions (640) returns False."""
        test_file = tmp_path / "group_read.txt"
        test_file.write_text("group exposed")
        test_file.chmod(0o640)

        result = check_file_permissions(test_file)
        assert result is False

    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix-only test")
    def test_logs_warning_with_security_prefix(self, tmp_path: Path) -> None:
        """Warning is logged with [SECURITY] prefix (FR-012)."""
        test_file = tmp_path / "permissive.txt"
        test_file.write_text("exposed")
        test_file.chmod(0o644)

        logger = MagicMock(spec=logging.Logger)
        check_file_permissions(test_file, logger=logger)

        logger.warning.assert_called_once()
        call_args = logger.warning.call_args[0][0]
        assert SECURITY_LOG_PREFIX in call_args

    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix-only test")
    def test_no_warning_for_secure_file(self, tmp_path: Path) -> None:
        """No warning is logged for secure files."""
        test_file = tmp_path / "secure.txt"
        test_file.write_text("secret")
        test_file.chmod(0o600)

        logger = MagicMock(spec=logging.Logger)
        check_file_permissions(test_file, logger=logger)

        logger.warning.assert_not_called()

    @patch("src.github_analyzer.core.security.platform.system", return_value="Windows")
    def test_windows_skipped_returns_true(self, mock_system: MagicMock) -> None:
        """Windows systems are skipped (always returns True)."""
        result = check_file_permissions(Path("some/file.txt"))
        assert result is True

    def test_nonexistent_file_returns_true(self, tmp_path: Path) -> None:
        """Non-existent file returns True (graceful degradation)."""
        result = check_file_permissions(tmp_path / "nonexistent.txt")
        assert result is True


class TestSetSecurePermissions:
    """Tests for set_secure_permissions function (FR-008)."""

    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix-only test")
    def test_sets_permissions_to_600(self, tmp_path: Path) -> None:
        """Sets file permissions to 0o600 by default."""
        test_file = tmp_path / "output.csv"
        test_file.write_text("data")
        test_file.chmod(0o644)  # Start with permissive

        result = set_secure_permissions(test_file)

        assert result is True
        assert test_file.stat().st_mode & 0o777 == 0o600

    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix-only test")
    def test_custom_mode_is_respected(self, tmp_path: Path) -> None:
        """Custom mode parameter is used."""
        test_file = tmp_path / "output.csv"
        test_file.write_text("data")

        result = set_secure_permissions(test_file, mode=0o640)

        assert result is True
        assert test_file.stat().st_mode & 0o777 == 0o640

    @patch("src.github_analyzer.core.security.platform.system", return_value="Windows")
    def test_windows_skipped_returns_true(self, mock_system: MagicMock) -> None:
        """Windows systems are skipped (returns True)."""
        result = set_secure_permissions(Path("some/file.txt"))
        assert result is True

    def test_nonexistent_file_returns_false(self, tmp_path: Path) -> None:
        """Non-existent file returns False."""
        result = set_secure_permissions(tmp_path / "nonexistent.txt")
        # On Unix, this will fail; on Windows, it returns True due to skip
        if platform.system() != "Windows":
            assert result is False


class TestValidateContentType:
    """Tests for validate_content_type function (FR-006)."""

    def test_matching_content_type_returns_true(self) -> None:
        """Matching Content-Type returns True."""
        headers = {"Content-Type": "application/json"}
        result = validate_content_type(headers)
        assert result is True

    def test_matching_with_charset_returns_true(self) -> None:
        """Content-Type with charset still matches."""
        headers = {"Content-Type": "application/json; charset=utf-8"}
        result = validate_content_type(headers)
        assert result is True

    def test_case_insensitive_header_lookup(self) -> None:
        """Header lookup is case-insensitive."""
        headers = {"content-type": "application/json"}
        result = validate_content_type(headers)
        assert result is True

    def test_mismatched_content_type_returns_false(self) -> None:
        """Mismatched Content-Type returns False."""
        headers = {"Content-Type": "text/html"}
        result = validate_content_type(headers)
        assert result is False

    def test_missing_content_type_returns_false(self) -> None:
        """Missing Content-Type header returns False (FR-006)."""
        headers = {"X-Request-Id": "123"}
        result = validate_content_type(headers)
        assert result is False

    def test_empty_headers_returns_false(self) -> None:
        """Empty headers returns False."""
        headers: dict[str, str] = {}
        result = validate_content_type(headers)
        assert result is False

    def test_logs_warning_on_mismatch(self) -> None:
        """Warning is logged with [SECURITY] prefix on mismatch."""
        headers = {"Content-Type": "text/html"}
        logger = MagicMock(spec=logging.Logger)

        validate_content_type(headers, logger=logger)

        logger.warning.assert_called_once()
        call_args = logger.warning.call_args[0][0]
        assert SECURITY_LOG_PREFIX in call_args
        assert "text/html" in call_args

    def test_logs_warning_on_missing_header(self) -> None:
        """Warning is logged with [SECURITY] prefix when header missing."""
        headers: dict[str, str] = {}
        logger = MagicMock(spec=logging.Logger)

        validate_content_type(headers, logger=logger)

        logger.warning.assert_called_once()
        call_args = logger.warning.call_args[0][0]
        assert SECURITY_LOG_PREFIX in call_args
        assert "Missing" in call_args

    def test_no_warning_on_match(self) -> None:
        """No warning is logged when Content-Type matches."""
        headers = {"Content-Type": "application/json"}
        logger = MagicMock(spec=logging.Logger)

        validate_content_type(headers, logger=logger)

        logger.warning.assert_not_called()

    def test_custom_expected_type(self) -> None:
        """Custom expected type can be specified."""
        headers = {"Content-Type": "text/csv"}
        result = validate_content_type(headers, expected="text/csv")
        assert result is True


class TestLogApiRequest:
    """Tests for log_api_request function (FR-009, FR-010)."""

    def test_logs_with_api_prefix(self) -> None:
        """Log message uses [API] prefix."""
        logger = MagicMock(spec=logging.Logger)

        log_api_request("GET", "https://api.github.com/repos/org/repo", 200, logger)

        logger.info.assert_called_once()
        call_args = logger.info.call_args[0][0]
        assert API_LOG_PREFIX in call_args

    def test_logs_method_url_status(self) -> None:
        """Log message includes method, URL, and status code."""
        logger = MagicMock(spec=logging.Logger)

        log_api_request("POST", "https://api.example.com/data", 201, logger)

        call_args = logger.info.call_args[0][0]
        assert "POST" in call_args
        assert "https://api.example.com/data" in call_args
        assert "201" in call_args

    def test_includes_response_time_when_provided(self) -> None:
        """Response time is included when provided."""
        logger = MagicMock(spec=logging.Logger)

        log_api_request(
            "GET", "https://api.github.com/user", 200, logger, response_time_ms=150.5
        )

        call_args = logger.info.call_args[0][0]
        assert "150ms" in call_args or "151ms" in call_args

    def test_masks_github_personal_access_token(self) -> None:
        """GitHub personal access tokens in URL are masked (FR-010)."""
        logger = MagicMock(spec=logging.Logger)
        url_with_token = "https://api.github.com/repos?token=ghp_1234567890abcdef"

        log_api_request("GET", url_with_token, 200, logger)

        call_args = logger.info.call_args[0][0]
        assert "ghp_" not in call_args
        assert "[MASKED]" in call_args

    def test_masks_github_oauth_token(self) -> None:
        """GitHub OAuth tokens in URL are masked."""
        logger = MagicMock(spec=logging.Logger)
        url_with_token = "https://api.github.com/user?access_token=gho_abcdefghijk"

        log_api_request("GET", url_with_token, 200, logger)

        call_args = logger.info.call_args[0][0]
        assert "gho_" not in call_args
        assert "[MASKED]" in call_args

    def test_masks_github_fine_grained_pat(self) -> None:
        """GitHub fine-grained PATs in URL are masked."""
        logger = MagicMock(spec=logging.Logger)
        url_with_token = "https://api.github.com/repos?token=github_pat_xxxx_yyyy"

        log_api_request("GET", url_with_token, 200, logger)

        call_args = logger.info.call_args[0][0]
        assert "github_pat_" not in call_args
        assert "[MASKED]" in call_args

    def test_masks_40_char_hex_tokens(self) -> None:
        """40-character hex strings (classic tokens) are masked."""
        logger = MagicMock(spec=logging.Logger)
        hex_token = "a" * 40
        url_with_token = f"https://api.github.com/repos?token={hex_token}"

        log_api_request("GET", url_with_token, 200, logger)

        call_args = logger.info.call_args[0][0]
        assert hex_token not in call_args
        assert "[MASKED]" in call_args


class TestValidateTimeout:
    """Tests for validate_timeout function (FR-011)."""

    def test_normal_timeout_no_warning(self) -> None:
        """Normal timeout (< threshold) generates no warning."""
        logger = MagicMock(spec=logging.Logger)

        validate_timeout(30, logger=logger)

        logger.warning.assert_not_called()

    def test_high_timeout_logs_warning(self) -> None:
        """High timeout (> threshold) logs warning with [SECURITY] prefix."""
        logger = MagicMock(spec=logging.Logger)

        validate_timeout(120, logger=logger)

        logger.warning.assert_called_once()
        call_args = logger.warning.call_args[0][0]
        assert SECURITY_LOG_PREFIX in call_args
        assert "120" in call_args

    def test_threshold_boundary_no_warning(self) -> None:
        """Timeout exactly at threshold generates no warning."""
        logger = MagicMock(spec=logging.Logger)

        validate_timeout(DEFAULT_TIMEOUT_WARN_THRESHOLD, logger=logger)

        logger.warning.assert_not_called()

    def test_custom_threshold_respected(self) -> None:
        """Custom threshold parameter is used."""
        logger = MagicMock(spec=logging.Logger)

        # 45s is above custom threshold of 30s
        validate_timeout(45, logger=logger, threshold=30)

        logger.warning.assert_called_once()

    def test_env_var_threshold_override(self) -> None:
        """Environment variable overrides default threshold."""
        logger = MagicMock(spec=logging.Logger)

        with patch.dict(os.environ, {"GITHUB_ANALYZER_TIMEOUT_WARN_THRESHOLD": "30"}):
            validate_timeout(45, logger=logger)

        logger.warning.assert_called_once()

    def test_invalid_env_var_uses_default(self) -> None:
        """Invalid environment variable value falls back to default."""
        logger = MagicMock(spec=logging.Logger)

        with patch.dict(os.environ, {"GITHUB_ANALYZER_TIMEOUT_WARN_THRESHOLD": "invalid"}):
            # 50s is below default threshold of 60s
            validate_timeout(50, logger=logger)

        logger.warning.assert_not_called()

    def test_no_logger_no_error(self) -> None:
        """Function works without logger (no error raised)."""
        # Should not raise any exception
        validate_timeout(120, logger=None)


class TestSecurityConstants:
    """Tests for security constants."""

    def test_formula_triggers_contains_all_characters(self) -> None:
        """FORMULA_TRIGGERS contains all required characters (FR-004)."""
        assert "=" in FORMULA_TRIGGERS
        assert "+" in FORMULA_TRIGGERS
        assert "-" in FORMULA_TRIGGERS
        assert "@" in FORMULA_TRIGGERS
        assert "\t" in FORMULA_TRIGGERS
        assert "\r" in FORMULA_TRIGGERS
        assert len(FORMULA_TRIGGERS) == 6

    def test_security_log_prefix_format(self) -> None:
        """SECURITY_LOG_PREFIX has correct format."""
        assert SECURITY_LOG_PREFIX == "[SECURITY]"

    def test_api_log_prefix_format(self) -> None:
        """API_LOG_PREFIX has correct format."""
        assert API_LOG_PREFIX == "[API]"

    def test_default_timeout_threshold(self) -> None:
        """DEFAULT_TIMEOUT_WARN_THRESHOLD is 60 seconds."""
        assert DEFAULT_TIMEOUT_WARN_THRESHOLD == 60

    def test_default_secure_mode(self) -> None:
        """DEFAULT_SECURE_MODE is 0o600."""
        assert DEFAULT_SECURE_MODE == 0o600
