"""Unit tests for input validation module.

Tests cover:
- T024: Repository.from_string() with valid inputs
- T025: Repository.from_string() with URL inputs (including http→https normalization)
- T026: Repository.from_string() rejecting invalid characters
- T027: Repository.from_string() rejecting injection attempts
- T028: load_repositories() with valid file
- T029: load_repositories() deduplication
- T030: load_repositories() with missing file
"""

from __future__ import annotations

from pathlib import Path

import pytest


class TestRepositoryFromStringValid:
    """Test Repository.from_string() with valid inputs (T024)."""

    def test_parses_owner_repo_format(self) -> None:
        """Given valid owner/repo, parses correctly."""
        from src.github_analyzer.config.validation import Repository

        repo = Repository.from_string("facebook/react")

        assert repo.owner == "facebook"
        assert repo.name == "react"
        assert repo.full_name == "facebook/react"

    def test_parses_with_hyphens(self) -> None:
        """Given owner/repo with hyphens, parses correctly."""
        from src.github_analyzer.config.validation import Repository

        repo = Repository.from_string("my-org/my-repo")

        assert repo.owner == "my-org"
        assert repo.name == "my-repo"

    def test_parses_with_underscores(self) -> None:
        """Given owner/repo with underscores, parses correctly."""
        from src.github_analyzer.config.validation import Repository

        repo = Repository.from_string("my_org/my_repo")

        assert repo.owner == "my_org"
        assert repo.name == "my_repo"

    def test_parses_with_periods(self) -> None:
        """Given owner/repo with periods, parses correctly."""
        from src.github_analyzer.config.validation import Repository

        repo = Repository.from_string("my.org/my.repo")

        assert repo.owner == "my.org"
        assert repo.name == "my.repo"

    def test_parses_with_numbers(self) -> None:
        """Given owner/repo with numbers, parses correctly."""
        from src.github_analyzer.config.validation import Repository

        repo = Repository.from_string("org123/repo456")

        assert repo.owner == "org123"
        assert repo.name == "repo456"

    def test_strips_whitespace(self) -> None:
        """Given input with whitespace, strips it."""
        from src.github_analyzer.config.validation import Repository

        repo = Repository.from_string("  owner/repo  ")

        assert repo.owner == "owner"
        assert repo.name == "repo"


class TestRepositoryFromStringURL:
    """Test Repository.from_string() with URL inputs (T025)."""

    def test_parses_https_url(self) -> None:
        """Given https URL, extracts owner/repo."""
        from src.github_analyzer.config.validation import Repository

        repo = Repository.from_string("https://github.com/facebook/react")

        assert repo.owner == "facebook"
        assert repo.name == "react"

    def test_parses_http_url_normalizes_to_https(self) -> None:
        """Given http URL, normalizes and extracts owner/repo."""
        from src.github_analyzer.config.validation import Repository

        repo = Repository.from_string("http://github.com/golang/go")

        assert repo.owner == "golang"
        assert repo.name == "go"
        # Note: normalization happens internally, we just verify parsing works

    def test_parses_url_with_git_suffix(self) -> None:
        """Given URL with .git suffix, removes it."""
        from src.github_analyzer.config.validation import Repository

        repo = Repository.from_string("https://github.com/owner/repo.git")

        assert repo.owner == "owner"
        assert repo.name == "repo"

    def test_parses_url_with_trailing_slash(self) -> None:
        """Given URL with trailing slash, removes it."""
        from src.github_analyzer.config.validation import Repository

        repo = Repository.from_string("https://github.com/owner/repo/")

        assert repo.owner == "owner"
        assert repo.name == "repo"

    def test_rejects_non_github_url(self) -> None:
        """Given non-GitHub URL, raises ValidationError."""
        from src.github_analyzer.config.validation import Repository
        from src.github_analyzer.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            Repository.from_string("https://gitlab.com/owner/repo")


class TestRepositoryFromStringInvalidChars:
    """Test Repository.from_string() rejecting invalid characters (T026)."""

    def test_rejects_empty_string(self) -> None:
        """Given empty string, raises ValidationError."""
        from src.github_analyzer.config.validation import Repository
        from src.github_analyzer.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            Repository.from_string("")

    def test_rejects_no_slash(self) -> None:
        """Given string without slash, raises ValidationError."""
        from src.github_analyzer.config.validation import Repository
        from src.github_analyzer.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            Repository.from_string("invalid")

    def test_rejects_empty_owner(self) -> None:
        """Given empty owner, raises ValidationError."""
        from src.github_analyzer.config.validation import Repository
        from src.github_analyzer.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            Repository.from_string("/repo")

    def test_rejects_empty_repo(self) -> None:
        """Given empty repo name, raises ValidationError."""
        from src.github_analyzer.config.validation import Repository
        from src.github_analyzer.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            Repository.from_string("owner/")

    def test_rejects_multiple_slashes(self) -> None:
        """Given multiple slashes, raises ValidationError."""
        from src.github_analyzer.config.validation import Repository
        from src.github_analyzer.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            Repository.from_string("owner/repo/extra")

    def test_rejects_starting_with_hyphen(self) -> None:
        """Given name starting with hyphen, raises ValidationError."""
        from src.github_analyzer.config.validation import Repository
        from src.github_analyzer.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            Repository.from_string("-owner/repo")


class TestRepositoryFromStringInjection:
    """Test Repository.from_string() rejecting injection attempts (T027)."""

    @pytest.mark.parametrize(
        "dangerous_input",
        [
            "owner;repo",
            "owner|repo",
            "owner&repo",
            "owner$repo",
            "owner`repo",
            "owner(repo)",
            "owner{repo}",
            "owner[repo]",
            "owner<repo>",
            "owner\\repo",
            "owner'repo",
            'owner"repo',
            "../path/traversal",
            "owner/../repo",
            "owner/repo\nmalicious",
        ],
    )
    def test_rejects_injection_characters(self, dangerous_input: str) -> None:
        """Given dangerous characters, raises ValidationError."""
        from src.github_analyzer.config.validation import Repository
        from src.github_analyzer.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            Repository.from_string(dangerous_input)

    def test_rejects_path_traversal(self) -> None:
        """Given path traversal attempt, raises ValidationError."""
        from src.github_analyzer.config.validation import Repository
        from src.github_analyzer.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            Repository.from_string("owner/..%2f..%2fetc%2fpasswd")


class TestLoadRepositoriesValid:
    """Test load_repositories() with valid file (T028)."""

    def test_loads_from_file(self, temp_repos_file: Path) -> None:
        """Given valid repos.txt, loads repositories."""
        from src.github_analyzer.config.validation import load_repositories

        repos = load_repositories(temp_repos_file)

        assert len(repos) == 3
        assert repos[0].full_name == "facebook/react"
        assert repos[1].full_name == "microsoft/vscode"
        assert repos[2].full_name == "kubernetes/kubernetes"

    def test_ignores_comments(self, tmp_path: Path) -> None:
        """Given file with comments, ignores them."""
        from src.github_analyzer.config.validation import load_repositories

        repos_file = tmp_path / "repos.txt"
        repos_file.write_text(
            """# This is a comment
            owner/repo
            # Another comment
            """
        )

        repos = load_repositories(repos_file)

        assert len(repos) == 1
        assert repos[0].full_name == "owner/repo"

    def test_ignores_empty_lines(self, tmp_path: Path) -> None:
        """Given file with empty lines, ignores them."""
        from src.github_analyzer.config.validation import load_repositories

        repos_file = tmp_path / "repos.txt"
        repos_file.write_text(
            """
            owner1/repo1

            owner2/repo2

            """
        )

        repos = load_repositories(repos_file)

        assert len(repos) == 2


class TestLoadRepositoriesDeduplication:
    """Test load_repositories() deduplication (T029)."""

    def test_deduplicates_entries(self, tmp_path: Path) -> None:
        """Given duplicate entries, deduplicates."""
        from src.github_analyzer.config.validation import load_repositories

        repos_file = tmp_path / "repos.txt"
        repos_file.write_text(
            """facebook/react
            facebook/react
            microsoft/vscode
            microsoft/vscode
            facebook/react
            """
        )

        repos = load_repositories(repos_file)

        assert len(repos) == 2
        full_names = [r.full_name for r in repos]
        assert full_names.count("facebook/react") == 1
        assert full_names.count("microsoft/vscode") == 1

    def test_deduplicates_url_and_name_format(self, tmp_path: Path) -> None:
        """Given same repo in URL and name format, deduplicates."""
        from src.github_analyzer.config.validation import load_repositories

        repos_file = tmp_path / "repos.txt"
        repos_file.write_text(
            """facebook/react
            https://github.com/facebook/react
            """
        )

        repos = load_repositories(repos_file)

        assert len(repos) == 1
        assert repos[0].full_name == "facebook/react"


class TestLoadRepositoriesMissingFile:
    """Test load_repositories() with missing file (T030)."""

    def test_raises_error_for_missing_file(self, tmp_path: Path) -> None:
        """Given non-existent file, raises ConfigurationError."""
        from src.github_analyzer.config.validation import load_repositories
        from src.github_analyzer.core.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError) as exc_info:
            load_repositories(tmp_path / "nonexistent.txt")

        assert "not found" in str(exc_info.value).lower()

    def test_raises_error_for_empty_file(self, tmp_path: Path) -> None:
        """Given empty file, raises ConfigurationError."""
        from src.github_analyzer.config.validation import load_repositories
        from src.github_analyzer.core.exceptions import ConfigurationError

        repos_file = tmp_path / "repos.txt"
        repos_file.write_text("")

        with pytest.raises(ConfigurationError) as exc_info:
            load_repositories(repos_file)

        assert "no valid repositories" in str(exc_info.value).lower()

    def test_raises_error_for_only_comments(self, tmp_path: Path) -> None:
        """Given file with only comments, raises ConfigurationError."""
        from src.github_analyzer.config.validation import load_repositories
        from src.github_analyzer.core.exceptions import ConfigurationError

        repos_file = tmp_path / "repos.txt"
        repos_file.write_text(
            """# Comment 1
            # Comment 2
            """
        )

        with pytest.raises(ConfigurationError) as exc_info:
            load_repositories(repos_file)

        assert "no valid repositories" in str(exc_info.value).lower()


class TestLoadRepositoriesFromFile:
    """Test load_repositories_from_file() function."""

    def test_loads_from_file_object(self) -> None:
        """Given file object, loads repositories."""
        from io import StringIO

        from src.github_analyzer.config.validation import load_repositories_from_file

        file_content = """facebook/react
microsoft/vscode
"""
        file = StringIO(file_content)
        repos = load_repositories_from_file(file)

        assert len(repos) == 2
        assert repos[0].full_name == "facebook/react"
        assert repos[1].full_name == "microsoft/vscode"

    def test_skips_invalid_lines(self) -> None:
        """Given file with invalid lines, skips them."""
        from io import StringIO

        from src.github_analyzer.config.validation import load_repositories_from_file

        file_content = """facebook/react
invalid-no-slash
owner/repo
"""
        file = StringIO(file_content)
        repos = load_repositories_from_file(file)

        assert len(repos) == 2

    def test_deduplicates_entries(self) -> None:
        """Given duplicates, deduplicates."""
        from io import StringIO

        from src.github_analyzer.config.validation import load_repositories_from_file

        file_content = """facebook/react
facebook/react
owner/repo
"""
        file = StringIO(file_content)
        repos = load_repositories_from_file(file)

        assert len(repos) == 2


class TestJiraUrlValidation:
    """Tests for validate_jira_url function."""

    def test_valid_atlassian_url(self) -> None:
        """Given valid Atlassian Cloud URL, returns True."""
        from src.github_analyzer.config.validation import validate_jira_url

        assert validate_jira_url("https://company.atlassian.net") is True

    def test_valid_onprem_url(self) -> None:
        """Given valid on-premises URL, returns True."""
        from src.github_analyzer.config.validation import validate_jira_url

        assert validate_jira_url("https://jira.company.com") is True

    def test_rejects_http(self) -> None:
        """Given HTTP URL, returns False."""
        from src.github_analyzer.config.validation import validate_jira_url

        assert validate_jira_url("http://jira.company.com") is False

    def test_rejects_empty(self) -> None:
        """Given empty string, returns False."""
        from src.github_analyzer.config.validation import validate_jira_url

        assert validate_jira_url("") is False

    def test_rejects_invalid_url(self) -> None:
        """Given invalid URL, returns False."""
        from src.github_analyzer.config.validation import validate_jira_url

        assert validate_jira_url("not-a-url") is False

    def test_rejects_no_host(self) -> None:
        """Given URL without host, returns False."""
        from src.github_analyzer.config.validation import validate_jira_url

        assert validate_jira_url("https://") is False

    def test_rejects_localhost_no_dot(self) -> None:
        """Given URL without dot in host, returns False."""
        from src.github_analyzer.config.validation import validate_jira_url

        assert validate_jira_url("https://localhost") is False

    def test_rejects_dangerous_chars(self) -> None:
        """Given URL with dangerous characters, returns False."""
        from src.github_analyzer.config.validation import validate_jira_url

        assert validate_jira_url("https://jira.company.com;rm -rf /") is False


class TestJiraProjectKeyValidation:
    """Tests for validate_project_key function."""

    def test_valid_simple_key(self) -> None:
        """Given simple uppercase key, returns True."""
        from src.github_analyzer.config.validation import validate_project_key

        assert validate_project_key("PROJ") is True

    def test_valid_key_with_numbers(self) -> None:
        """Given key with numbers, returns True."""
        from src.github_analyzer.config.validation import validate_project_key

        assert validate_project_key("PROJ123") is True

    def test_valid_key_with_underscore(self) -> None:
        """Given key with underscore, returns True."""
        from src.github_analyzer.config.validation import validate_project_key

        assert validate_project_key("PROJ_TEST") is True

    def test_rejects_lowercase(self) -> None:
        """Given lowercase key, returns False."""
        from src.github_analyzer.config.validation import validate_project_key

        assert validate_project_key("proj") is False

    def test_rejects_starting_with_number(self) -> None:
        """Given key starting with number, returns False."""
        from src.github_analyzer.config.validation import validate_project_key

        assert validate_project_key("1PROJ") is False

    def test_rejects_empty(self) -> None:
        """Given empty string, returns False."""
        from src.github_analyzer.config.validation import validate_project_key

        assert validate_project_key("") is False


class TestISO8601Validation:
    """Tests for validate_iso8601_date function."""

    def test_valid_date_only(self) -> None:
        """Given valid date only, returns True."""
        from src.github_analyzer.config.validation import validate_iso8601_date

        assert validate_iso8601_date("2025-11-28") is True

    def test_valid_datetime_with_z(self) -> None:
        """Given valid datetime with Z, returns True."""
        from src.github_analyzer.config.validation import validate_iso8601_date

        assert validate_iso8601_date("2025-11-28T10:30:00Z") is True

    def test_valid_datetime_with_offset(self) -> None:
        """Given valid datetime with offset, returns True."""
        from src.github_analyzer.config.validation import validate_iso8601_date

        assert validate_iso8601_date("2025-11-28T10:30:00+00:00") is True

    def test_valid_datetime_with_milliseconds(self) -> None:
        """Given valid datetime with milliseconds, returns True."""
        from src.github_analyzer.config.validation import validate_iso8601_date

        assert validate_iso8601_date("2025-11-28T10:30:00.123Z") is True

    def test_rejects_wrong_format(self) -> None:
        """Given wrong date format, returns False."""
        from src.github_analyzer.config.validation import validate_iso8601_date

        assert validate_iso8601_date("28-11-2025") is False

    def test_rejects_invalid_string(self) -> None:
        """Given invalid string, returns False."""
        from src.github_analyzer.config.validation import validate_iso8601_date

        assert validate_iso8601_date("invalid") is False

    def test_rejects_empty(self) -> None:
        """Given empty string, returns False."""
        from src.github_analyzer.config.validation import validate_iso8601_date

        assert validate_iso8601_date("") is False

    def test_rejects_invalid_month(self) -> None:
        """Given invalid month, returns False."""
        from src.github_analyzer.config.validation import validate_iso8601_date

        assert validate_iso8601_date("2025-13-28") is False

    def test_rejects_invalid_day(self) -> None:
        """Given invalid day, returns False."""
        from src.github_analyzer.config.validation import validate_iso8601_date

        assert validate_iso8601_date("2025-11-32") is False


class TestLoadJiraProjects:
    """Tests for load_jira_projects function."""

    def test_loads_from_file(self, tmp_path: Path) -> None:
        """Given valid file, loads projects."""
        from src.github_analyzer.config.validation import load_jira_projects

        projects_file = tmp_path / "jira_projects.txt"
        projects_file.write_text("""PROJ
DEV
OPS
""")

        projects = load_jira_projects(projects_file)

        assert len(projects) == 3
        assert "PROJ" in projects
        assert "DEV" in projects
        assert "OPS" in projects

    def test_returns_empty_for_missing_file(self, tmp_path: Path) -> None:
        """Given missing file, returns empty list."""
        from src.github_analyzer.config.validation import load_jira_projects

        projects = load_jira_projects(tmp_path / "nonexistent.txt")

        assert projects == []

    def test_ignores_comments(self, tmp_path: Path) -> None:
        """Given file with comments, ignores them."""
        from src.github_analyzer.config.validation import load_jira_projects

        projects_file = tmp_path / "jira_projects.txt"
        projects_file.write_text("""# Comment
PROJ
# Another comment
""")

        projects = load_jira_projects(projects_file)

        assert len(projects) == 1
        assert "PROJ" in projects

    def test_deduplicates_entries(self, tmp_path: Path) -> None:
        """Given duplicates, deduplicates."""
        from src.github_analyzer.config.validation import load_jira_projects

        projects_file = tmp_path / "jira_projects.txt"
        projects_file.write_text("""PROJ
PROJ
DEV
""")

        projects = load_jira_projects(projects_file)

        assert len(projects) == 2

    def test_validates_format(self, tmp_path: Path) -> None:
        """Given invalid keys, skips them."""
        from src.github_analyzer.config.validation import load_jira_projects

        projects_file = tmp_path / "jira_projects.txt"
        projects_file.write_text("""PROJ
lowercase
123INVALID
VALID
""")

        projects = load_jira_projects(projects_file)

        assert len(projects) == 2
        assert "PROJ" in projects
        assert "VALID" in projects


class TestNormalizeUrl:
    """Tests for _normalize_url function."""

    def test_normalizes_http_to_https(self) -> None:
        """Given http URL, normalizes to https."""
        from src.github_analyzer.config.validation import _normalize_url

        result = _normalize_url("http://github.com/owner/repo")
        assert result == "owner/repo"

    def test_removes_www(self) -> None:
        """Given URL with www, handles it."""
        from src.github_analyzer.config.validation import _normalize_url

        result = _normalize_url("https://www.github.com/owner/repo")
        assert result == "owner/repo"

    def test_handles_exception(self) -> None:
        """Given malformed URL, returns None."""
        from src.github_analyzer.config.validation import _normalize_url

        # This should not raise, just return None
        result = _normalize_url("not://valid")
        assert result is None

    def test_rejects_url_with_extra_path(self) -> None:
        """Given URL with extra path segments, returns None."""
        from src.github_analyzer.config.validation import _normalize_url

        result = _normalize_url("https://github.com/owner/repo/extra/path")
        assert result is None
