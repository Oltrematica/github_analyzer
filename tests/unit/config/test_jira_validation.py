"""Unit tests for Jira validation functions.

Tests for:
- validate_jira_url(): HTTPS URL validation
- validate_project_key(): Jira project key format
- validate_iso8601_date(): ISO 8601 date format
- load_jira_projects(): Loading project keys from file
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.github_analyzer.config.validation import (
    load_jira_projects,
    validate_iso8601_date,
    validate_jira_url,
    validate_project_key,
)


class TestValidateJiraUrl:
    """Tests for validate_jira_url()."""

    def test_valid_atlassian_cloud_url(self) -> None:
        """Valid Atlassian Cloud URL passes."""
        assert validate_jira_url("https://company.atlassian.net") is True

    def test_valid_onpremise_url(self) -> None:
        """Valid on-premises URL passes."""
        assert validate_jira_url("https://jira.company.com") is True

    def test_valid_url_with_port(self) -> None:
        """Valid URL with port passes."""
        assert validate_jira_url("https://jira.company.com:8443") is True

    def test_valid_url_with_path(self) -> None:
        """Valid URL with path passes."""
        assert validate_jira_url("https://company.com/jira") is True

    def test_invalid_http_url(self) -> None:
        """HTTP URL is rejected (security requirement)."""
        assert validate_jira_url("http://company.atlassian.net") is False

    def test_invalid_no_scheme(self) -> None:
        """URL without scheme is rejected."""
        assert validate_jira_url("company.atlassian.net") is False

    def test_invalid_no_domain(self) -> None:
        """URL without proper domain is rejected."""
        assert validate_jira_url("https://localhost") is False

    def test_invalid_empty_string(self) -> None:
        """Empty string is rejected."""
        assert validate_jira_url("") is False

    def test_invalid_none(self) -> None:
        """None-like values are rejected."""
        # Type checker would catch this, but test runtime behavior
        assert validate_jira_url(None) is False  # type: ignore[arg-type]

    def test_invalid_not_url(self) -> None:
        """Non-URL string is rejected."""
        assert validate_jira_url("not-a-url") is False

    def test_invalid_ftp_scheme(self) -> None:
        """FTP scheme is rejected."""
        assert validate_jira_url("ftp://company.com") is False

    def test_invalid_dangerous_chars(self) -> None:
        """URLs with dangerous characters are rejected."""
        assert validate_jira_url("https://company.com;rm -rf") is False
        assert validate_jira_url("https://company.com|cat /etc/passwd") is False


class TestValidateProjectKey:
    """Tests for validate_project_key()."""

    def test_valid_simple_key(self) -> None:
        """Simple uppercase key passes."""
        assert validate_project_key("PROJ") is True

    def test_valid_short_key(self) -> None:
        """Short key (minimum length) passes."""
        assert validate_project_key("A") is True

    def test_valid_key_with_numbers(self) -> None:
        """Key with numbers passes."""
        assert validate_project_key("PROJ123") is True

    def test_valid_key_with_underscore(self) -> None:
        """Key with underscore passes."""
        assert validate_project_key("PROJECT_ONE") is True

    def test_valid_all_caps_numbers_underscore(self) -> None:
        """Key with all valid characters passes."""
        assert validate_project_key("ABC_123_DEF") is True

    def test_invalid_lowercase(self) -> None:
        """Lowercase key is rejected."""
        assert validate_project_key("proj") is False

    def test_invalid_mixed_case(self) -> None:
        """Mixed case key is rejected."""
        assert validate_project_key("Proj") is False

    def test_invalid_starts_with_number(self) -> None:
        """Key starting with number is rejected."""
        assert validate_project_key("1PROJ") is False

    def test_invalid_starts_with_underscore(self) -> None:
        """Key starting with underscore is rejected."""
        assert validate_project_key("_PROJ") is False

    def test_invalid_contains_hyphen(self) -> None:
        """Key containing hyphen is rejected."""
        assert validate_project_key("PROJ-ONE") is False

    def test_invalid_contains_space(self) -> None:
        """Key containing space is rejected."""
        assert validate_project_key("PROJ ONE") is False

    def test_invalid_empty_string(self) -> None:
        """Empty string is rejected."""
        assert validate_project_key("") is False

    def test_invalid_none(self) -> None:
        """None is rejected."""
        assert validate_project_key(None) is False  # type: ignore[arg-type]


class TestValidateIso8601Date:
    """Tests for validate_iso8601_date()."""

    def test_valid_date_only(self) -> None:
        """Date-only format passes."""
        assert validate_iso8601_date("2025-11-28") is True

    def test_valid_datetime_with_z(self) -> None:
        """Datetime with Z suffix passes."""
        assert validate_iso8601_date("2025-11-28T10:30:00Z") is True

    def test_valid_datetime_with_positive_offset(self) -> None:
        """Datetime with positive offset passes."""
        assert validate_iso8601_date("2025-11-28T10:30:00+05:30") is True

    def test_valid_datetime_with_negative_offset(self) -> None:
        """Datetime with negative offset passes."""
        assert validate_iso8601_date("2025-11-28T10:30:00-08:00") is True

    def test_valid_datetime_with_milliseconds(self) -> None:
        """Datetime with milliseconds passes."""
        assert validate_iso8601_date("2025-11-28T10:30:00.123Z") is True

    def test_valid_datetime_with_ms_and_offset(self) -> None:
        """Datetime with milliseconds and offset passes."""
        assert validate_iso8601_date("2025-11-28T10:30:00.123+00:00") is True

    def test_invalid_wrong_format_dmy(self) -> None:
        """DD-MM-YYYY format is rejected."""
        assert validate_iso8601_date("28-11-2025") is False

    def test_invalid_wrong_format_mdy(self) -> None:
        """MM/DD/YYYY format is rejected."""
        assert validate_iso8601_date("11/28/2025") is False

    def test_invalid_month_out_of_range(self) -> None:
        """Month > 12 is rejected."""
        assert validate_iso8601_date("2025-13-28") is False

    def test_invalid_day_out_of_range(self) -> None:
        """Day > 31 is rejected."""
        assert validate_iso8601_date("2025-11-32") is False

    def test_invalid_random_string(self) -> None:
        """Random string is rejected."""
        assert validate_iso8601_date("invalid") is False

    def test_invalid_empty_string(self) -> None:
        """Empty string is rejected."""
        assert validate_iso8601_date("") is False

    def test_invalid_none(self) -> None:
        """None is rejected."""
        assert validate_iso8601_date(None) is False  # type: ignore[arg-type]

    def test_invalid_year_too_old(self) -> None:
        """Year before 1900 is rejected."""
        assert validate_iso8601_date("1800-01-01") is False

    def test_invalid_year_too_future(self) -> None:
        """Year after 2100 is rejected."""
        assert validate_iso8601_date("2200-01-01") is False


class TestLoadJiraProjects:
    """Tests for load_jira_projects()."""

    def test_load_valid_projects(self) -> None:
        """Load valid project keys from file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("PROJ\n")
            f.write("DEV\n")
            f.write("SUPPORT\n")
            f.flush()

            projects = load_jira_projects(f.name)
            assert projects == ["PROJ", "DEV", "SUPPORT"]

            Path(f.name).unlink()

    def test_load_with_comments(self) -> None:
        """Comments are ignored."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("# This is a comment\n")
            f.write("PROJ\n")
            f.write("# Another comment\n")
            f.write("DEV\n")
            f.flush()

            projects = load_jira_projects(f.name)
            assert projects == ["PROJ", "DEV"]

            Path(f.name).unlink()

    def test_load_with_empty_lines(self) -> None:
        """Empty lines are ignored."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("PROJ\n")
            f.write("\n")
            f.write("DEV\n")
            f.write("\n")
            f.flush()

            projects = load_jira_projects(f.name)
            assert projects == ["PROJ", "DEV"]

            Path(f.name).unlink()

    def test_load_deduplicates(self) -> None:
        """Duplicate keys are deduplicated."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("PROJ\n")
            f.write("DEV\n")
            f.write("PROJ\n")  # duplicate
            f.flush()

            projects = load_jira_projects(f.name)
            assert projects == ["PROJ", "DEV"]

            Path(f.name).unlink()

    def test_load_skips_invalid_keys(self) -> None:
        """Invalid keys are skipped silently."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("PROJ\n")
            f.write("invalid\n")  # lowercase - invalid
            f.write("DEV\n")
            f.write("123ABC\n")  # starts with number - invalid
            f.flush()

            projects = load_jira_projects(f.name)
            assert projects == ["PROJ", "DEV"]

            Path(f.name).unlink()

    def test_load_missing_file(self) -> None:
        """Missing file returns empty list (FR-009a)."""
        projects = load_jira_projects("/nonexistent/path/projects.txt")
        assert projects == []

    def test_load_empty_file(self) -> None:
        """Empty file returns empty list."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("")
            f.flush()

            projects = load_jira_projects(f.name)
            assert projects == []

            Path(f.name).unlink()

    def test_load_only_comments(self) -> None:
        """File with only comments returns empty list."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("# Comment 1\n")
            f.write("# Comment 2\n")
            f.flush()

            projects = load_jira_projects(f.name)
            assert projects == []

            Path(f.name).unlink()

    def test_load_preserves_order(self) -> None:
        """Project order is preserved."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("ZEBRA\n")
            f.write("ALPHA\n")
            f.write("MIDDLE\n")
            f.flush()

            projects = load_jira_projects(f.name)
            assert projects == ["ZEBRA", "ALPHA", "MIDDLE"]

            Path(f.name).unlink()

    def test_load_with_whitespace(self) -> None:
        """Whitespace around keys is handled."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("  PROJ  \n")
            f.write("\tDEV\t\n")
            f.flush()

            projects = load_jira_projects(f.name)
            assert projects == ["PROJ", "DEV"]

            Path(f.name).unlink()
