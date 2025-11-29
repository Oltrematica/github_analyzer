"""Integration tests for interactive project selection.

Tests for:
- Interactive Jira project selection when jira_projects.txt is missing
- Project listing and user selection
- Selection persistence to file
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

import pytest

from src.github_analyzer.config.settings import JiraConfig


class TestInteractiveProjectSelection:
    """Tests for interactive Jira project selection."""

    @pytest.fixture
    def jira_env(self) -> dict:
        """Jira environment variables."""
        return {
            "JIRA_URL": "https://company.atlassian.net",
            "JIRA_EMAIL": "user@company.com",
            "JIRA_API_TOKEN": "test-token",
        }

    @pytest.fixture
    def mock_projects(self) -> list:
        """Mock Jira projects list."""
        from src.github_analyzer.api.jira_client import JiraProject

        return [
            JiraProject(key="PROJ", name="Main Project", description="Main project description"),
            JiraProject(key="DEV", name="Development", description="Dev team project"),
            JiraProject(key="OPS", name="Operations", description="Ops team project"),
        ]

    def test_uses_all_projects_when_file_missing_non_interactive(
        self, tmp_path: Path, jira_env: dict, mock_projects: list
    ) -> None:
        """All projects used when jira_projects.txt is missing (non-interactive mode)."""
        from src.github_analyzer.api import jira_client as jira_module
        from src.github_analyzer.cli.main import select_jira_projects

        projects_file = tmp_path / "jira_projects.txt"
        assert not projects_file.exists()

        with mock.patch.object(jira_module, "JiraClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_projects.return_value = mock_projects

            with mock.patch.dict(os.environ, jira_env, clear=True):
                result = select_jira_projects(
                    str(projects_file),
                    jira_config=JiraConfig.from_env(),
                    interactive=False,  # Non-interactive mode for testing
                )

        # Should return all available projects
        assert len(result) == 3
        assert "PROJ" in result
        assert "DEV" in result
        assert "OPS" in result

    def test_uses_all_projects_when_file_empty_non_interactive(
        self, tmp_path: Path, jira_env: dict, mock_projects: list
    ) -> None:
        """All projects used when jira_projects.txt is empty (non-interactive mode)."""
        from src.github_analyzer.api import jira_client as jira_module
        from src.github_analyzer.cli.main import select_jira_projects

        projects_file = tmp_path / "jira_projects.txt"
        projects_file.write_text("")  # Empty file

        with mock.patch.object(jira_module, "JiraClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_projects.return_value = mock_projects

            with mock.patch.dict(os.environ, jira_env, clear=True):
                result = select_jira_projects(
                    str(projects_file),
                    jira_config=JiraConfig.from_env(),
                    interactive=False,  # Non-interactive mode for testing
                )

        # Should return all projects
        assert len(result) == 3
        assert "PROJ" in result
        assert "DEV" in result
        assert "OPS" in result

    def test_interactive_prompt_select_all(
        self, tmp_path: Path, jira_env: dict, mock_projects: list
    ) -> None:
        """Interactive prompt: user selects 'A' for all projects (FR-009a)."""
        from src.github_analyzer.api import jira_client as jira_module
        from src.github_analyzer.cli.main import select_jira_projects

        projects_file = tmp_path / "jira_projects.txt"
        assert not projects_file.exists()

        with mock.patch.object(jira_module, "JiraClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_projects.return_value = mock_projects

            with mock.patch.dict(os.environ, jira_env, clear=True):
                with mock.patch("builtins.input", return_value="A"):
                    result = select_jira_projects(
                        str(projects_file),
                        jira_config=JiraConfig.from_env(),
                        interactive=True,
                    )

        # Should return all projects
        assert len(result) == 3
        assert "PROJ" in result
        assert "DEV" in result
        assert "OPS" in result

    def test_interactive_prompt_specify_manually(
        self, tmp_path: Path, jira_env: dict, mock_projects: list
    ) -> None:
        """Interactive prompt: user specifies projects manually (FR-009a option b)."""
        from src.github_analyzer.api import jira_client as jira_module
        from src.github_analyzer.cli.main import select_jira_projects

        projects_file = tmp_path / "jira_projects.txt"
        assert not projects_file.exists()

        with mock.patch.object(jira_module, "JiraClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_projects.return_value = mock_projects

            with mock.patch.dict(os.environ, jira_env, clear=True):
                # User selects 'S' then enters "PROJ, DEV"
                with mock.patch("builtins.input", side_effect=["S", "PROJ, DEV"]):
                    result = select_jira_projects(
                        str(projects_file),
                        jira_config=JiraConfig.from_env(),
                        interactive=True,
                    )

        # Should return only specified projects
        assert result == ["PROJ", "DEV"]

    def test_interactive_prompt_quit(
        self, tmp_path: Path, jira_env: dict, mock_projects: list
    ) -> None:
        """Interactive prompt: user quits extraction."""
        from src.github_analyzer.api import jira_client as jira_module
        from src.github_analyzer.cli.main import select_jira_projects

        projects_file = tmp_path / "jira_projects.txt"
        assert not projects_file.exists()

        with mock.patch.object(jira_module, "JiraClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_projects.return_value = mock_projects

            with mock.patch.dict(os.environ, jira_env, clear=True):
                with mock.patch("builtins.input", return_value="Q"):
                    result = select_jira_projects(
                        str(projects_file),
                        jira_config=JiraConfig.from_env(),
                        interactive=True,
                    )

        # Should return empty list (skipped)
        assert result == []

    def test_existing_file_skips_prompt(
        self, tmp_path: Path, jira_env: dict
    ) -> None:
        """Existing jira_projects.txt skips interactive prompt."""
        from src.github_analyzer.cli.main import select_jira_projects

        # Create existing projects file
        projects_file = tmp_path / "jira_projects.txt"
        projects_file.write_text("PROJ\nDEV\n")

        with mock.patch.dict(os.environ, jira_env, clear=True):
            result = select_jira_projects(
                str(projects_file),
                jira_config=JiraConfig.from_env(),
            )

        # Should read from file, not prompt
        assert result == ["PROJ", "DEV"]

    def test_interactive_prompt_select_by_list_number(
        self, tmp_path: Path, jira_env: dict, mock_projects: list
    ) -> None:
        """Interactive prompt: user selects 'L' and picks from list (FR-009a)."""
        from src.github_analyzer.api import jira_client as jira_module
        from src.github_analyzer.cli.main import select_jira_projects

        projects_file = tmp_path / "jira_projects.txt"
        assert not projects_file.exists()

        with mock.patch.object(jira_module, "JiraClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_projects.return_value = mock_projects

            with mock.patch.dict(os.environ, jira_env, clear=True):
                # User selects 'L' then enters "1,3" (first and third project)
                with mock.patch("builtins.input", side_effect=["L", "1,3"]):
                    result = select_jira_projects(
                        str(projects_file),
                        jira_config=JiraConfig.from_env(),
                        interactive=True,
                    )

        # Should return projects at indices 0 and 2 (1-indexed in UI)
        assert result == ["PROJ", "OPS"]

    def test_interactive_prompt_eof_on_choice(
        self, tmp_path: Path, jira_env: dict, mock_projects: list
    ) -> None:
        """Interactive prompt: EOF on main choice returns empty list."""
        from src.github_analyzer.api import jira_client as jira_module
        from src.github_analyzer.cli.main import select_jira_projects

        projects_file = tmp_path / "jira_projects.txt"

        with mock.patch.object(jira_module, "JiraClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_projects.return_value = mock_projects

            with mock.patch.dict(os.environ, jira_env, clear=True):
                with mock.patch("builtins.input", side_effect=EOFError):
                    result = select_jira_projects(
                        str(projects_file),
                        jira_config=JiraConfig.from_env(),
                        interactive=True,
                    )

        assert result == []

    def test_interactive_prompt_eof_on_manual_input(
        self, tmp_path: Path, jira_env: dict, mock_projects: list
    ) -> None:
        """Interactive prompt: EOF on manual input returns empty list."""
        from src.github_analyzer.api import jira_client as jira_module
        from src.github_analyzer.cli.main import select_jira_projects

        projects_file = tmp_path / "jira_projects.txt"

        with mock.patch.object(jira_module, "JiraClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_projects.return_value = mock_projects

            with mock.patch.dict(os.environ, jira_env, clear=True):
                # User selects 'S', then EOF on manual input
                with mock.patch("builtins.input", side_effect=["S", EOFError()]):
                    result = select_jira_projects(
                        str(projects_file),
                        jira_config=JiraConfig.from_env(),
                        interactive=True,
                    )

        assert result == []

    def test_interactive_prompt_eof_on_list_selection(
        self, tmp_path: Path, jira_env: dict, mock_projects: list
    ) -> None:
        """Interactive prompt: EOF on list selection returns empty list."""
        from src.github_analyzer.api import jira_client as jira_module
        from src.github_analyzer.cli.main import select_jira_projects

        projects_file = tmp_path / "jira_projects.txt"

        with mock.patch.object(jira_module, "JiraClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_projects.return_value = mock_projects

            with mock.patch.dict(os.environ, jira_env, clear=True):
                # User selects 'L', then EOF on list selection input
                with mock.patch("builtins.input", side_effect=["L", EOFError()]):
                    result = select_jira_projects(
                        str(projects_file),
                        jira_config=JiraConfig.from_env(),
                        interactive=True,
                    )

        assert result == []

    def test_interactive_prompt_empty_manual_input_retries(
        self, tmp_path: Path, jira_env: dict, mock_projects: list
    ) -> None:
        """Interactive prompt: empty manual input prompts again."""
        from src.github_analyzer.api import jira_client as jira_module
        from src.github_analyzer.cli.main import select_jira_projects

        projects_file = tmp_path / "jira_projects.txt"

        with mock.patch.object(jira_module, "JiraClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_projects.return_value = mock_projects

            with mock.patch.dict(os.environ, jira_env, clear=True):
                # User selects 'S', enters empty, then valid input
                with mock.patch("builtins.input", side_effect=["S", "", "S", "PROJ"]):
                    result = select_jira_projects(
                        str(projects_file),
                        jira_config=JiraConfig.from_env(),
                        interactive=True,
                    )

        assert result == ["PROJ"]

    def test_interactive_prompt_invalid_keys_ignored(
        self, tmp_path: Path, jira_env: dict, mock_projects: list
    ) -> None:
        """Interactive prompt: invalid project keys are ignored with warning."""
        from src.github_analyzer.api import jira_client as jira_module
        from src.github_analyzer.cli.main import select_jira_projects

        projects_file = tmp_path / "jira_projects.txt"

        with mock.patch.object(jira_module, "JiraClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_projects.return_value = mock_projects

            with mock.patch.dict(os.environ, jira_env, clear=True):
                # User enters mix of valid and invalid keys
                with mock.patch("builtins.input", side_effect=["S", "PROJ, INVALID, DEV"]):
                    result = select_jira_projects(
                        str(projects_file),
                        jira_config=JiraConfig.from_env(),
                        interactive=True,
                    )

        # Only valid keys returned
        assert result == ["PROJ", "DEV"]

    def test_interactive_prompt_all_invalid_keys_retries(
        self, tmp_path: Path, jira_env: dict, mock_projects: list
    ) -> None:
        """Interactive prompt: all invalid keys prompts again."""
        from src.github_analyzer.api import jira_client as jira_module
        from src.github_analyzer.cli.main import select_jira_projects

        projects_file = tmp_path / "jira_projects.txt"

        with mock.patch.object(jira_module, "JiraClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_projects.return_value = mock_projects

            with mock.patch.dict(os.environ, jira_env, clear=True):
                # User enters all invalid, then quits
                with mock.patch("builtins.input", side_effect=["S", "INVALID, WRONG", "Q"]):
                    result = select_jira_projects(
                        str(projects_file),
                        jira_config=JiraConfig.from_env(),
                        interactive=True,
                    )

        assert result == []

    def test_interactive_prompt_invalid_list_selection_retries(
        self, tmp_path: Path, jira_env: dict, mock_projects: list
    ) -> None:
        """Interactive prompt: invalid list selection prompts again."""
        from src.github_analyzer.api import jira_client as jira_module
        from src.github_analyzer.cli.main import select_jira_projects

        projects_file = tmp_path / "jira_projects.txt"

        with mock.patch.object(jira_module, "JiraClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_projects.return_value = mock_projects

            with mock.patch.dict(os.environ, jira_env, clear=True):
                # User enters invalid selection, then quits
                with mock.patch("builtins.input", side_effect=["L", "invalid", "Q"]):
                    result = select_jira_projects(
                        str(projects_file),
                        jira_config=JiraConfig.from_env(),
                        interactive=True,
                    )

        assert result == []

    def test_interactive_prompt_invalid_choice_retries(
        self, tmp_path: Path, jira_env: dict, mock_projects: list
    ) -> None:
        """Interactive prompt: invalid choice prompts again."""
        from src.github_analyzer.api import jira_client as jira_module
        from src.github_analyzer.cli.main import select_jira_projects

        projects_file = tmp_path / "jira_projects.txt"

        with mock.patch.object(jira_module, "JiraClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_projects.return_value = mock_projects

            with mock.patch.dict(os.environ, jira_env, clear=True):
                # User enters invalid choice 'X', then 'A'
                with mock.patch("builtins.input", side_effect=["X", "A"]):
                    result = select_jira_projects(
                        str(projects_file),
                        jira_config=JiraConfig.from_env(),
                        interactive=True,
                    )

        assert len(result) == 3

    def test_no_projects_in_jira_returns_empty(
        self, tmp_path: Path, jira_env: dict
    ) -> None:
        """No projects found in Jira instance returns empty list."""
        from src.github_analyzer.api import jira_client as jira_module
        from src.github_analyzer.cli.main import select_jira_projects

        projects_file = tmp_path / "jira_projects.txt"

        with mock.patch.object(jira_module, "JiraClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_projects.return_value = []  # No projects

            with mock.patch.dict(os.environ, jira_env, clear=True):
                result = select_jira_projects(
                    str(projects_file),
                    jira_config=JiraConfig.from_env(),
                    interactive=True,
                )

        assert result == []

    def test_no_jira_config_returns_empty(self, tmp_path: Path) -> None:
        """No jira_config provided returns empty list."""
        from src.github_analyzer.cli.main import select_jira_projects

        projects_file = tmp_path / "jira_projects.txt"

        result = select_jira_projects(
            str(projects_file),
            jira_config=None,  # No config
            interactive=True,
        )

        assert result == []

    def test_file_with_projects_uses_file(
        self, tmp_path: Path, jira_env: dict, mock_projects: list
    ) -> None:
        """File with project keys uses those keys, not all available."""
        from src.github_analyzer.api import jira_client as jira_module
        from src.github_analyzer.cli.main import select_jira_projects

        # Create file with specific projects
        projects_file = tmp_path / "jira_projects.txt"
        projects_file.write_text("PROJ\n")

        with mock.patch.object(jira_module, "JiraClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_projects.return_value = mock_projects

            with mock.patch.dict(os.environ, jira_env, clear=True):
                result = select_jira_projects(
                    str(projects_file),
                    jira_config=JiraConfig.from_env(),
                )

        # Should use only file contents, not all projects
        assert result == ["PROJ"]
        # Client should NOT be called since file exists
        MockClient.assert_not_called()


class TestProjectSelectionInput:
    """Tests for project selection input parsing."""

    def test_parse_single_number(self) -> None:
        """Parses single number selection."""
        from src.github_analyzer.cli.main import parse_project_selection

        result = parse_project_selection("1", 5)
        assert result == [0]  # 0-indexed

    def test_parse_multiple_numbers(self) -> None:
        """Parses multiple comma-separated numbers."""
        from src.github_analyzer.cli.main import parse_project_selection

        result = parse_project_selection("1, 3, 5", 5)
        assert result == [0, 2, 4]

    def test_parse_range(self) -> None:
        """Parses range selection like '1-3'."""
        from src.github_analyzer.cli.main import parse_project_selection

        result = parse_project_selection("1-3", 5)
        assert result == [0, 1, 2]

    def test_parse_all(self) -> None:
        """Parses 'all' to select all projects."""
        from src.github_analyzer.cli.main import parse_project_selection

        result = parse_project_selection("all", 5)
        assert result == [0, 1, 2, 3, 4]

    def test_parse_invalid_returns_empty(self) -> None:
        """Invalid input returns empty list."""
        from src.github_analyzer.cli.main import parse_project_selection

        result = parse_project_selection("invalid", 5)
        assert result == []

    def test_parse_out_of_range_filtered(self) -> None:
        """Out of range numbers are filtered."""
        from src.github_analyzer.cli.main import parse_project_selection

        result = parse_project_selection("1, 10, 100", 5)
        assert 0 in result  # 1 is valid (0-indexed)
        assert len(result) == 1  # Only valid number


class TestProjectDisplayFormat:
    """Tests for project display formatting."""

    def test_format_project_list(self) -> None:
        """Projects are formatted for display with numbers."""
        from src.github_analyzer.api.jira_client import JiraProject
        from src.github_analyzer.cli.main import format_project_list

        projects = [
            JiraProject(key="PROJ", name="Main Project", description=""),
            JiraProject(key="DEV", name="Development", description=""),
        ]

        result = format_project_list(projects)

        assert "[1]" in result
        assert "[2]" in result
        assert "PROJ" in result
        assert "DEV" in result
        assert "Main Project" in result

    def test_format_truncates_long_descriptions(self) -> None:
        """Long descriptions are truncated."""
        from src.github_analyzer.api.jira_client import JiraProject
        from src.github_analyzer.cli.main import format_project_list

        long_desc = "A" * 200
        projects = [
            JiraProject(key="PROJ", name="Main", description=long_desc),
        ]

        result = format_project_list(projects)

        # Description should be truncated
        assert len(result) < len(long_desc) + 50


class TestGitHubInteractiveSelection:
    """Integration tests for GitHub repository interactive selection (Feature 004).

    Tests for User Story 1: Interactive Repository Selection Menu
    """

    @pytest.fixture
    def github_env(self) -> dict:
        """GitHub environment variables."""
        return {
            "GITHUB_TOKEN": "ghp_test_token_12345678901234567890",
        }

    @pytest.fixture
    def mock_repos(self) -> list:
        """Mock GitHub repository list."""
        return [
            {"full_name": "user/repo1", "private": False, "description": "First repo"},
            {"full_name": "user/repo2", "private": True, "description": "Private repo"},
            {"full_name": "user/repo3", "private": False, "description": "Third repo"},
        ]

    def test_menu_displays_when_repos_txt_missing(
        self, tmp_path: Path, github_env: dict, mock_repos: list
    ) -> None:
        """T007: Menu displays when repos.txt is missing."""
        from src.github_analyzer.cli.main import select_github_repos

        repos_file = tmp_path / "repos.txt"
        assert not repos_file.exists()

        with mock.patch.dict(os.environ, github_env, clear=True):
            # User selects 'Q' to quit immediately
            with mock.patch("builtins.input", return_value="Q"):
                with mock.patch("builtins.print") as mock_print:
                    result = select_github_repos(
                        str(repos_file),
                        github_token=github_env["GITHUB_TOKEN"],
                        interactive=True,
                    )

        # Verify menu was displayed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("[A]" in call for call in print_calls)
        assert any("[S]" in call for call in print_calls)
        assert any("[O]" in call for call in print_calls)
        assert any("[L]" in call for call in print_calls)
        assert any("[Q]" in call for call in print_calls)
        assert result == []

    def test_menu_displays_when_repos_txt_empty(
        self, tmp_path: Path, github_env: dict
    ) -> None:
        """T008: Menu displays when repos.txt is empty."""
        from src.github_analyzer.cli.main import select_github_repos

        repos_file = tmp_path / "repos.txt"
        repos_file.write_text("")  # Empty file

        with mock.patch.dict(os.environ, github_env, clear=True):
            with mock.patch("builtins.input", return_value="Q"):
                with mock.patch("builtins.print") as mock_print:
                    result = select_github_repos(
                        str(repos_file),
                        github_token=github_env["GITHUB_TOKEN"],
                        interactive=True,
                    )

        # Menu should be displayed for empty file
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("[A]" in call for call in print_calls)
        assert result == []

    def test_no_menu_when_repos_txt_has_content(
        self, tmp_path: Path, github_env: dict
    ) -> None:
        """T009: No menu when repos.txt has valid content."""
        from src.github_analyzer.cli.main import select_github_repos

        repos_file = tmp_path / "repos.txt"
        repos_file.write_text("owner/repo1\nowner/repo2\n")

        with mock.patch.dict(os.environ, github_env, clear=True):
            # No input mock needed - should not prompt
            result = select_github_repos(
                str(repos_file),
                github_token=github_env["GITHUB_TOKEN"],
                interactive=True,
            )

        # Should use repos from file
        assert result == ["owner/repo1", "owner/repo2"]

    def test_eof_returns_empty_list(
        self, tmp_path: Path, github_env: dict
    ) -> None:
        """T010: EOF/Ctrl+C returns empty list gracefully."""
        from src.github_analyzer.cli.main import select_github_repos

        repos_file = tmp_path / "repos.txt"
        assert not repos_file.exists()

        with mock.patch.dict(os.environ, github_env, clear=True):
            with mock.patch("builtins.input", side_effect=EOFError):
                result = select_github_repos(
                    str(repos_file),
                    github_token=github_env["GITHUB_TOKEN"],
                    interactive=True,
                )

        assert result == []

    def test_keyboard_interrupt_returns_empty_list(
        self, tmp_path: Path, github_env: dict
    ) -> None:
        """T010: KeyboardInterrupt returns empty list gracefully."""
        from src.github_analyzer.cli.main import select_github_repos

        repos_file = tmp_path / "repos.txt"
        assert not repos_file.exists()

        with mock.patch.dict(os.environ, github_env, clear=True):
            with mock.patch("builtins.input", side_effect=KeyboardInterrupt):
                result = select_github_repos(
                    str(repos_file),
                    github_token=github_env["GITHUB_TOKEN"],
                    interactive=True,
                )

        assert result == []

    def test_non_interactive_mode_skips_prompts(
        self, tmp_path: Path, github_env: dict
    ) -> None:
        """T011: Non-interactive mode (--quiet) skips prompts."""
        from src.github_analyzer.cli.main import select_github_repos

        repos_file = tmp_path / "repos.txt"
        assert not repos_file.exists()

        with mock.patch.dict(os.environ, github_env, clear=True):
            result = select_github_repos(
                str(repos_file),
                github_token=github_env["GITHUB_TOKEN"],
                interactive=False,  # Non-interactive mode
            )

        # Should return empty list without prompting
        assert result == []

    def test_option_q_returns_empty_list(
        self, tmp_path: Path, github_env: dict
    ) -> None:
        """T047: Option [Q] returns empty list."""
        from src.github_analyzer.cli.main import select_github_repos

        repos_file = tmp_path / "repos.txt"
        assert not repos_file.exists()

        with mock.patch.dict(os.environ, github_env, clear=True):
            with mock.patch("builtins.input", return_value="Q"):
                result = select_github_repos(
                    str(repos_file),
                    github_token=github_env["GITHUB_TOKEN"],
                    interactive=True,
                )

        assert result == []

    def test_invalid_menu_choice_reprompts(
        self, tmp_path: Path, github_env: dict
    ) -> None:
        """T048: Invalid menu choice shows error and reprompts."""
        from src.github_analyzer.cli.main import select_github_repos

        repos_file = tmp_path / "repos.txt"
        assert not repos_file.exists()

        with mock.patch.dict(os.environ, github_env, clear=True):
            # User enters invalid 'X', then 'Q'
            with mock.patch("builtins.input", side_effect=["X", "Q"]):
                result = select_github_repos(
                    str(repos_file),
                    github_token=github_env["GITHUB_TOKEN"],
                    interactive=True,
                )

        assert result == []


class TestGitHubPersonalReposSelection:
    """Integration tests for personal repos selection (Feature 004 - User Story 2)."""

    @pytest.fixture
    def github_env(self) -> dict:
        """GitHub environment variables."""
        return {
            "GITHUB_TOKEN": "ghp_test_token_12345678901234567890",
        }

    @pytest.fixture
    def mock_repos(self) -> list:
        """Mock GitHub repository list."""
        return [
            {"full_name": "user/repo1", "private": False, "description": "First repo"},
            {"full_name": "user/repo2", "private": True, "description": "Private repo"},
            {"full_name": "user/repo3", "private": False, "description": "Third repo"},
        ]

    def test_option_a_returns_all_user_repos(
        self, tmp_path: Path, github_env: dict, mock_repos: list
    ) -> None:
        """T018: Option [A] returns all user repositories."""
        import sys
        import src.github_analyzer.cli.main
        main_module = sys.modules["src.github_analyzer.cli.main"]
        from src.github_analyzer.cli.main import select_github_repos

        repos_file = tmp_path / "repos.txt"
        assert not repos_file.exists()

        # Add pushed_at to mock repos for Feature 005 activity filtering
        for repo in mock_repos:
            repo["pushed_at"] = "2025-11-28T10:00:00Z"

        with mock.patch.object(main_module, "GitHubClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.list_user_repos.return_value = mock_repos
            mock_client.close = mock.Mock()

            with mock.patch.dict(os.environ, github_env, clear=True):
                # Feature 005: "A" selects option, "Y" confirms active repos
                with mock.patch("builtins.input", side_effect=["A", "Y"]):
                    result = select_github_repos(
                        str(repos_file),
                        github_token=github_env["GITHUB_TOKEN"],
                        interactive=True,
                    )

        assert len(result) == 3
        assert "user/repo1" in result
        assert "user/repo2" in result
        assert "user/repo3" in result

    def test_option_l_displays_numbered_list(
        self, tmp_path: Path, github_env: dict, mock_repos: list
    ) -> None:
        """T019: Option [L] displays numbered list of repositories."""
        import sys
        import src.github_analyzer.cli.main
        main_module = sys.modules["src.github_analyzer.cli.main"]
        from src.github_analyzer.cli.main import select_github_repos

        repos_file = tmp_path / "repos.txt"
        assert not repos_file.exists()

        # Add pushed_at to mock repos for Feature 005 activity filtering
        for repo in mock_repos:
            repo["pushed_at"] = "2025-11-28T10:00:00Z"

        with mock.patch.object(main_module, "GitHubClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.list_user_repos.return_value = mock_repos
            mock_client.close = mock.Mock()

            with mock.patch.dict(os.environ, github_env, clear=True):
                # Feature 005: "L" selects option, "Y" confirms, then '1,3' selection
                with mock.patch("builtins.input", side_effect=["L", "Y", "1,3"]):
                    with mock.patch("builtins.print") as mock_print:
                        result = select_github_repos(
                            str(repos_file),
                            github_token=github_env["GITHUB_TOKEN"],
                            interactive=True,
                        )

        # Verify numbered list was printed
        print_calls = " ".join(str(call) for call in mock_print.call_args_list)
        assert "1." in print_calls or "[1]" in print_calls
        assert "user/repo1" in print_calls

        # Should return selected repos
        assert "user/repo1" in result
        assert "user/repo3" in result

    def test_option_l_accepts_range_selection(
        self, tmp_path: Path, github_env: dict, mock_repos: list
    ) -> None:
        """T021: Option [L] accepts '1-3' range selection."""
        import sys
        import src.github_analyzer.cli.main
        main_module = sys.modules["src.github_analyzer.cli.main"]
        from src.github_analyzer.cli.main import select_github_repos

        repos_file = tmp_path / "repos.txt"
        assert not repos_file.exists()

        # Add pushed_at to mock repos for Feature 005 activity filtering
        for repo in mock_repos:
            repo["pushed_at"] = "2025-11-28T10:00:00Z"

        with mock.patch.object(main_module, "GitHubClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.list_user_repos.return_value = mock_repos
            mock_client.close = mock.Mock()

            with mock.patch.dict(os.environ, github_env, clear=True):
                # Feature 005: "L" selects option, "Y" confirms, then "1-3" range selection
                with mock.patch("builtins.input", side_effect=["L", "Y", "1-3"]):
                    result = select_github_repos(
                        str(repos_file),
                        github_token=github_env["GITHUB_TOKEN"],
                        interactive=True,
                    )

        assert len(result) == 3

    def test_option_l_accepts_all_selection(
        self, tmp_path: Path, github_env: dict, mock_repos: list
    ) -> None:
        """T022: Option [L] accepts 'all' selection."""
        import sys
        import src.github_analyzer.cli.main
        main_module = sys.modules["src.github_analyzer.cli.main"]
        from src.github_analyzer.cli.main import select_github_repos

        repos_file = tmp_path / "repos.txt"
        assert not repos_file.exists()

        # Add pushed_at to mock repos for Feature 005 activity filtering
        for repo in mock_repos:
            repo["pushed_at"] = "2025-11-28T10:00:00Z"

        with mock.patch.object(main_module, "GitHubClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.list_user_repos.return_value = mock_repos
            mock_client.close = mock.Mock()

            with mock.patch.dict(os.environ, github_env, clear=True):
                # Feature 005: "L" selects option, "Y" confirms, then "all" selection
                with mock.patch("builtins.input", side_effect=["L", "Y", "all"]):
                    result = select_github_repos(
                        str(repos_file),
                        github_token=github_env["GITHUB_TOKEN"],
                        interactive=True,
                    )

        assert len(result) == 3


class TestGitHubOrgReposSelection:
    """Integration tests for organization repos selection (Feature 004 - User Story 3)."""

    @pytest.fixture
    def github_env(self) -> dict:
        """GitHub environment variables."""
        return {
            "GITHUB_TOKEN": "ghp_test_token_12345678901234567890",
        }

    @pytest.fixture
    def mock_org_repos(self) -> list:
        """Mock organization repository list."""
        return [
            {"full_name": "myorg/project1", "private": False, "description": "Org project 1"},
            {"full_name": "myorg/project2", "private": True, "description": "Org project 2"},
        ]

    def test_option_o_prompts_for_org_name(
        self, tmp_path: Path, github_env: dict, mock_org_repos: list
    ) -> None:
        """T029: Option [O] prompts for organization name."""
        import sys
        import src.github_analyzer.cli.main
        main_module = sys.modules["src.github_analyzer.cli.main"]
        from src.github_analyzer.cli.main import select_github_repos

        repos_file = tmp_path / "repos.txt"
        assert not repos_file.exists()

        # Add pushed_at to mock repos for Feature 005 activity filtering
        for repo in mock_org_repos:
            repo["pushed_at"] = "2025-11-28T10:00:00Z"

        with mock.patch.object(main_module, "GitHubClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.list_org_repos.return_value = mock_org_repos
            # Feature 005: Search API for org repos
            mock_client.search_active_org_repos.return_value = {
                "total_count": len(mock_org_repos),
                "incomplete_results": False,
                "items": mock_org_repos,
            }
            mock_client.close = mock.Mock()

            with mock.patch.dict(os.environ, github_env, clear=True):
                # Feature 005: "O" selects option, enters org name, "Y" confirms, then 'all'
                with mock.patch("builtins.input", side_effect=["O", "myorg", "Y", "all"]):
                    result = select_github_repos(
                        str(repos_file),
                        github_token=github_env["GITHUB_TOKEN"],
                        interactive=True,
                    )

        # Should have called list_org_repos with the org name (for total count)
        mock_client.list_org_repos.assert_called_with("myorg")
        assert len(result) == 2
        assert "myorg/project1" in result

    def test_invalid_org_name_format_shows_error(
        self, tmp_path: Path, github_env: dict
    ) -> None:
        """T031: Invalid org name format shows error."""
        import sys
        import src.github_analyzer.cli.main
        main_module = sys.modules["src.github_analyzer.cli.main"]
        from src.github_analyzer.cli.main import select_github_repos

        repos_file = tmp_path / "repos.txt"
        assert not repos_file.exists()

        with mock.patch.object(main_module, "GitHubClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.close = mock.Mock()

            with mock.patch.dict(os.environ, github_env, clear=True):
                # User enters invalid org name (starts with hyphen), then quits
                with mock.patch("builtins.input", side_effect=["O", "-invalid", "Q"]):
                    result = select_github_repos(
                        str(repos_file),
                        github_token=github_env["GITHUB_TOKEN"],
                        interactive=True,
                    )

        assert result == []


class TestGitHubManualReposSelection:
    """Integration tests for manual repos specification (Feature 004 - User Story 4)."""

    @pytest.fixture
    def github_env(self) -> dict:
        """GitHub environment variables."""
        return {
            "GITHUB_TOKEN": "ghp_test_token_12345678901234567890",
        }

    def test_option_s_prompts_for_manual_input(
        self, tmp_path: Path, github_env: dict
    ) -> None:
        """T038: Option [S] prompts for manual input."""
        import sys
        import src.github_analyzer.cli.main
        main_module = sys.modules["src.github_analyzer.cli.main"]
        from src.github_analyzer.cli.main import select_github_repos

        repos_file = tmp_path / "repos.txt"
        assert not repos_file.exists()

        with mock.patch.object(main_module, "GitHubClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.close = mock.Mock()

            with mock.patch.dict(os.environ, github_env, clear=True):
                with mock.patch("builtins.input", side_effect=["S", "owner/repo1, owner/repo2"]):
                    result = select_github_repos(
                        str(repos_file),
                        github_token=github_env["GITHUB_TOKEN"],
                        interactive=True,
                    )

        assert result == ["owner/repo1", "owner/repo2"]

    def test_valid_owner_repo_format_accepted(
        self, tmp_path: Path, github_env: dict
    ) -> None:
        """T039: Valid 'owner/repo' format accepted."""
        import sys
        import src.github_analyzer.cli.main
        main_module = sys.modules["src.github_analyzer.cli.main"]
        from src.github_analyzer.cli.main import select_github_repos

        repos_file = tmp_path / "repos.txt"
        assert not repos_file.exists()

        with mock.patch.object(main_module, "GitHubClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.close = mock.Mock()

            with mock.patch.dict(os.environ, github_env, clear=True):
                with mock.patch("builtins.input", side_effect=["S", "facebook/react"]):
                    result = select_github_repos(
                        str(repos_file),
                        github_token=github_env["GITHUB_TOKEN"],
                        interactive=True,
                    )

        assert result == ["facebook/react"]

    def test_invalid_format_shows_warning(
        self, tmp_path: Path, github_env: dict
    ) -> None:
        """T040: Invalid format shows warning."""
        import sys
        import src.github_analyzer.cli.main
        main_module = sys.modules["src.github_analyzer.cli.main"]
        from src.github_analyzer.cli.main import select_github_repos

        repos_file = tmp_path / "repos.txt"
        assert not repos_file.exists()

        with mock.patch.object(main_module, "GitHubClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.close = mock.Mock()

            with mock.patch.dict(os.environ, github_env, clear=True):
                # Enter mix of valid and invalid, should continue with valid only
                with mock.patch("builtins.input", side_effect=["S", "valid/repo, invalid-repo"]):
                    with mock.patch("builtins.print"):
                        result = select_github_repos(
                            str(repos_file),
                            github_token=github_env["GITHUB_TOKEN"],
                            interactive=True,
                        )

        # Only valid repos returned
        assert result == ["valid/repo"]

    def test_empty_input_prompts_again(
        self, tmp_path: Path, github_env: dict
    ) -> None:
        """T042: Empty input prompts again."""
        import sys
        import src.github_analyzer.cli.main
        main_module = sys.modules["src.github_analyzer.cli.main"]
        from src.github_analyzer.cli.main import select_github_repos

        repos_file = tmp_path / "repos.txt"
        assert not repos_file.exists()

        with mock.patch.object(main_module, "GitHubClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.close = mock.Mock()

            with mock.patch.dict(os.environ, github_env, clear=True):
                # Empty input, then valid
                with mock.patch("builtins.input", side_effect=["S", "", "S", "owner/repo"]):
                    result = select_github_repos(
                        str(repos_file),
                        github_token=github_env["GITHUB_TOKEN"],
                        interactive=True,
                    )

        assert result == ["owner/repo"]


class TestGitHubRepoDisplayFormat:
    """Tests for GitHub repository display formatting."""

    def test_format_repo_list(self) -> None:
        """Repositories are formatted for display with numbers."""
        from src.github_analyzer.cli.main import format_repo_list

        repos = [
            {"full_name": "user/repo1", "private": False, "description": "Description 1"},
            {"full_name": "user/repo2", "private": True, "description": "Private desc"},
        ]

        result = format_repo_list(repos)

        assert "1." in result
        assert "2." in result
        assert "user/repo1" in result
        assert "user/repo2" in result
        assert "[private]" in result  # Private marker for second repo

    def test_format_truncates_long_descriptions(self) -> None:
        """Long descriptions are truncated to 50 chars."""
        from src.github_analyzer.cli.main import format_repo_list

        long_desc = "A" * 200
        repos = [
            {"full_name": "user/repo1", "private": False, "description": long_desc},
        ]

        result = format_repo_list(repos)

        # Description should be truncated (50 chars + "...")
        assert "..." in result
        assert "A" * 51 not in result


class TestValidationPatterns:
    """Tests for validation patterns (spec Validation Patterns section)."""

    def test_validate_repo_format_valid(self) -> None:
        """Valid repo formats pass validation."""
        from src.github_analyzer.cli.main import validate_repo_format

        valid_repos = [
            "owner/repo",
            "my-org/my-repo",
            "user123/project_v2",
            "facebook/react",
            "owner.name/repo.name",
        ]

        for repo in valid_repos:
            assert validate_repo_format(repo), f"{repo} should be valid"

    def test_validate_repo_format_invalid(self) -> None:
        """Invalid repo formats fail validation."""
        from src.github_analyzer.cli.main import validate_repo_format

        invalid_repos = [
            "just-repo",
            "owner/",
            "/repo",
            "",
            "owner//repo",
        ]

        for repo in invalid_repos:
            assert not validate_repo_format(repo), f"{repo} should be invalid"

    def test_validate_org_name_valid(self) -> None:
        """Valid org names pass validation."""
        from src.github_analyzer.cli.main import validate_org_name

        valid_orgs = [
            "myorg",
            "my-organization",
            "org123",
            "a",
        ]

        for org in valid_orgs:
            assert validate_org_name(org), f"{org} should be valid"

    def test_validate_org_name_invalid(self) -> None:
        """Invalid org names fail validation."""
        from src.github_analyzer.cli.main import validate_org_name

        invalid_orgs = [
            "-invalid",
            "invalid-",
            "org--double",
            "",
            "a" * 40,  # Too long (max 39)
        ]

        for org in invalid_orgs:
            assert not validate_org_name(org), f"{org} should be invalid"
