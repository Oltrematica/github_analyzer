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

    def test_uses_all_projects_when_file_missing(
        self, tmp_path: Path, jira_env: dict, mock_projects: list
    ) -> None:
        """All projects used when jira_projects.txt is missing."""
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
                )

        # Should return all available projects
        assert len(result) == 3
        assert "PROJ" in result
        assert "DEV" in result
        assert "OPS" in result

    def test_uses_all_projects_when_file_empty(
        self, tmp_path: Path, jira_env: dict, mock_projects: list
    ) -> None:
        """All projects used when jira_projects.txt is empty."""
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
                )

        # Should return all projects
        assert len(result) == 3
        assert "PROJ" in result
        assert "DEV" in result
        assert "OPS" in result

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
