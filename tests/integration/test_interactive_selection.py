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
