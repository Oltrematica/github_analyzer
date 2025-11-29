"""Tests for CLI main module."""

import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest

# Import the module directly via sys.modules to avoid __init__.py shadowing
from src.github_analyzer.cli.main import (
    GitHubAnalyzer,
    main,
    parse_args,
    prompt_int,
    prompt_yes_no,
)

# Get the actual module object
main_module = sys.modules["src.github_analyzer.cli.main"]

from src.github_analyzer.api.models import Commit, Issue, PullRequest, QualityMetrics  # noqa: E402
from src.github_analyzer.config.settings import AnalyzerConfig  # noqa: E402
from src.github_analyzer.config.validation import Repository  # noqa: E402
from src.github_analyzer.core.exceptions import (  # noqa: E402
    ConfigurationError,
    GitHubAnalyzerError,
    RateLimitError,
)


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = Mock(spec=AnalyzerConfig)
    config.github_token = "ghp_test_token_1234567890"
    config.output_dir = "/tmp/test_output"
    config.repos_file = "repos.txt"
    config.days = 30
    config.per_page = 100
    config.max_pages = 50
    config.timeout = 30
    config.verbose = True
    return config


@pytest.fixture
def sample_commit():
    """Create a sample commit."""
    return Commit(
        repository="test/repo",
        sha="abc123def456",
        author_login="user1",
        author_email="user1@test.com",
        committer_login="user1",
        date=datetime.now(timezone.utc),
        message="Test commit",
        full_message="Test commit",
        additions=100,
        deletions=50,
        files_changed=5,
    )


@pytest.fixture
def sample_pr():
    """Create a sample PR."""
    now = datetime.now(timezone.utc)
    return PullRequest(
        repository="test/repo",
        number=1,
        title="Test PR",
        state="closed",
        author_login="user1",
        created_at=now - timedelta(days=2),
        updated_at=now,
        closed_at=now,
        merged_at=now,
        is_merged=True,
        is_draft=False,
        additions=100,
        deletions=50,
        changed_files=5,
        commits=3,
        comments=2,
        review_comments=1,
    )


@pytest.fixture
def sample_issue():
    """Create a sample issue."""
    now = datetime.now(timezone.utc)
    return Issue(
        repository="test/repo",
        number=1,
        title="Test Issue",
        state="open",
        author_login="user1",
        created_at=now,
        updated_at=now,
        closed_at=None,
        labels=["bug"],
        assignees=[],
        comments=0,
    )


class TestGitHubAnalyzerInit:
    """Tests for GitHubAnalyzer initialization."""

    def test_initializes_with_config(self, mock_config, tmp_path):
        """Test analyzer initializes with config."""
        mock_config.output_dir = str(tmp_path)

        with patch.object(main_module, "GitHubClient"):
            analyzer = GitHubAnalyzer(mock_config)

        assert analyzer._config is mock_config

    def test_initializes_analyzers(self, mock_config, tmp_path):
        """Test analyzer initializes sub-analyzers."""
        mock_config.output_dir = str(tmp_path)

        with patch.object(main_module, "GitHubClient"):
            analyzer = GitHubAnalyzer(mock_config)

        assert analyzer._commit_analyzer is not None
        assert analyzer._pr_analyzer is not None
        assert analyzer._issue_analyzer is not None
        assert analyzer._contributor_tracker is not None


class TestGitHubAnalyzerRun:
    """Tests for GitHubAnalyzer.run method."""

    def test_run_analyzes_repositories(self, mock_config, tmp_path, sample_commit, sample_pr, sample_issue):
        """Test run analyzes all repositories."""
        mock_config.output_dir = str(tmp_path)

        with patch.object(main_module, "GitHubClient"):
            analyzer = GitHubAnalyzer(mock_config)

        # Mock the analyzers
        analyzer._commit_analyzer.fetch_and_analyze = Mock(return_value=[sample_commit])
        analyzer._commit_analyzer.get_stats = Mock(return_value={
            "total": 1, "merge_commits": 0, "revert_commits": 0,
            "total_additions": 100, "total_deletions": 50, "unique_authors": 1
        })

        analyzer._pr_analyzer.fetch_and_analyze = Mock(return_value=[sample_pr])
        analyzer._pr_analyzer.get_stats = Mock(return_value={
            "total": 1, "merged": 1, "open": 0, "closed_not_merged": 0,
            "draft": 0, "avg_time_to_merge_hours": 24.0
        })

        analyzer._issue_analyzer.fetch_and_analyze = Mock(return_value=[sample_issue])
        analyzer._issue_analyzer.get_stats = Mock(return_value={
            "total": 1, "open": 1, "closed": 0, "bugs": 1,
            "enhancements": 0, "avg_time_to_close_hours": None
        })

        with patch.object(main_module, "calculate_quality_metrics") as mock_quality:
            mock_quality.return_value = QualityMetrics(repository="test/repo")

            repos = [Repository(owner="test", name="repo")]
            analyzer.run(repos)

        # Verify analyzers were called
        analyzer._commit_analyzer.fetch_and_analyze.assert_called_once()
        analyzer._pr_analyzer.fetch_and_analyze.assert_called_once()
        analyzer._issue_analyzer.fetch_and_analyze.assert_called_once()

    def test_run_handles_rate_limit(self, mock_config, tmp_path):
        """Test run handles rate limit errors."""
        mock_config.output_dir = str(tmp_path)

        with patch.object(main_module, "GitHubClient"):
            analyzer = GitHubAnalyzer(mock_config)

        # Make commit analyzer raise rate limit
        analyzer._commit_analyzer.fetch_and_analyze = Mock(
            side_effect=RateLimitError("Rate limit exceeded")
        )

        repos = [Repository(owner="test", name="repo")]

        # Should not raise, should handle gracefully
        analyzer.run(repos)

    def test_run_handles_api_error(self, mock_config, tmp_path, sample_commit, sample_pr, sample_issue):
        """Test run handles API errors for individual repos."""
        mock_config.output_dir = str(tmp_path)

        with patch.object(main_module, "GitHubClient"):
            analyzer = GitHubAnalyzer(mock_config)

        # First repo fails, second succeeds
        call_count = [0]
        def mock_fetch(repo, since):  # noqa: ARG001
            call_count[0] += 1
            if call_count[0] == 1:
                raise GitHubAnalyzerError("API error")
            return [sample_commit]

        analyzer._commit_analyzer.fetch_and_analyze = Mock(side_effect=mock_fetch)
        analyzer._commit_analyzer.get_stats = Mock(return_value={
            "total": 1, "merge_commits": 0, "revert_commits": 0,
            "total_additions": 100, "total_deletions": 50, "unique_authors": 1
        })

        analyzer._pr_analyzer.fetch_and_analyze = Mock(return_value=[sample_pr])
        analyzer._pr_analyzer.get_stats = Mock(return_value={
            "total": 1, "merged": 1, "open": 0, "closed_not_merged": 0,
            "draft": 0, "avg_time_to_merge_hours": 24.0
        })

        analyzer._issue_analyzer.fetch_and_analyze = Mock(return_value=[sample_issue])
        analyzer._issue_analyzer.get_stats = Mock(return_value={
            "total": 1, "open": 1, "closed": 0, "bugs": 1,
            "enhancements": 0, "avg_time_to_close_hours": None
        })

        with patch.object(main_module, "calculate_quality_metrics") as mock_quality:
            mock_quality.return_value = QualityMetrics(repository="test/repo")

            repos = [
                Repository(owner="fail", name="repo"),
                Repository(owner="test", name="repo"),
            ]
            analyzer.run(repos)

        # Second repo should still be processed
        assert call_count[0] == 2


class TestGitHubAnalyzerClose:
    """Tests for GitHubAnalyzer.close method."""

    def test_close_closes_client(self, mock_config, tmp_path):
        """Test close closes the API client."""
        mock_config.output_dir = str(tmp_path)

        mock_client = Mock()
        with patch.object(main_module, "GitHubClient", return_value=mock_client):
            analyzer = GitHubAnalyzer(mock_config)
            analyzer.close()

        mock_client.close.assert_called_once()


class TestParseArgs:
    """Tests for parse_args function."""

    def test_default_values(self):
        """Test default argument values."""
        with patch("sys.argv", ["prog"]):
            args = parse_args()

        assert args.days is None
        assert args.output is None
        assert args.repos is None
        assert args.quiet is False
        assert args.full is False

    def test_days_argument(self):
        """Test --days argument."""
        with patch("sys.argv", ["prog", "--days", "7"]):
            args = parse_args()

        assert args.days == 7

    def test_short_days_argument(self):
        """Test -d argument."""
        with patch("sys.argv", ["prog", "-d", "14"]):
            args = parse_args()

        assert args.days == 14

    def test_output_argument(self):
        """Test --output argument."""
        with patch("sys.argv", ["prog", "--output", "/tmp/output"]):
            args = parse_args()

        assert args.output == "/tmp/output"

    def test_repos_argument(self):
        """Test --repos argument."""
        with patch("sys.argv", ["prog", "--repos", "my_repos.txt"]):
            args = parse_args()

        assert args.repos == "my_repos.txt"

    def test_quiet_flag(self):
        """Test --quiet flag."""
        with patch("sys.argv", ["prog", "--quiet"]):
            args = parse_args()

        assert args.quiet is True

    def test_full_flag(self):
        """Test --full flag."""
        with patch("sys.argv", ["prog", "--full"]):
            args = parse_args()

        assert args.full is True


class TestPromptYesNo:
    """Tests for prompt_yes_no function."""

    def test_returns_true_for_y(self):
        """Test returns True for 'y' input."""
        with patch("builtins.input", return_value="y"):
            result = prompt_yes_no("Test?")
        assert result is True

    def test_returns_true_for_yes(self):
        """Test returns True for 'yes' input."""
        with patch("builtins.input", return_value="yes"):
            result = prompt_yes_no("Test?")
        assert result is True

    def test_returns_true_for_si(self):
        """Test returns True for 'si' input."""
        with patch("builtins.input", return_value="si"):
            result = prompt_yes_no("Test?")
        assert result is True

    def test_returns_false_for_n(self):
        """Test returns False for 'n' input."""
        with patch("builtins.input", return_value="n"):
            result = prompt_yes_no("Test?")
        assert result is False

    def test_returns_default_for_empty(self):
        """Test returns default for empty input."""
        with patch("builtins.input", return_value=""):
            result = prompt_yes_no("Test?", default=True)
        assert result is True

    def test_returns_default_on_eof(self):
        """Test returns default on EOFError."""
        with patch("builtins.input", side_effect=EOFError):
            result = prompt_yes_no("Test?", default=False)
        assert result is False

    def test_returns_default_on_interrupt(self):
        """Test returns default on KeyboardInterrupt."""
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            result = prompt_yes_no("Test?", default=True)
        assert result is True


class TestPromptInt:
    """Tests for prompt_int function."""

    def test_returns_entered_value(self):
        """Test returns entered integer value."""
        with patch("builtins.input", return_value="42"):
            result = prompt_int("Enter number:", 10)
        assert result == 42

    def test_returns_default_for_empty(self):
        """Test returns default for empty input."""
        with patch("builtins.input", return_value=""):
            result = prompt_int("Enter number:", 10)
        assert result == 10

    def test_returns_default_for_invalid(self):
        """Test returns default for invalid input."""
        with patch("builtins.input", return_value="not a number"):
            result = prompt_int("Enter number:", 10)
        assert result == 10

    def test_returns_default_on_eof(self):
        """Test returns default on EOFError."""
        with patch("builtins.input", side_effect=EOFError):
            result = prompt_int("Enter number:", 10)
        assert result == 10

    def test_returns_default_on_interrupt(self):
        """Test returns default on KeyboardInterrupt."""
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            result = prompt_int("Enter number:", 10)
        assert result == 10


class TestMain:
    """Tests for main function."""

    def test_returns_1_on_configuration_error(self):
        """Test returns 1 on ConfigurationError."""
        with (
            patch("sys.argv", ["prog"]),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
        ):
            MockConfig.from_env.side_effect = ConfigurationError("Missing token")
            result = main()

        assert result == 1

    def test_returns_2_on_unexpected_error(self):
        """Test returns 2 on unexpected error."""
        with (
            patch("sys.argv", ["prog"]),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
        ):
            MockConfig.from_env.side_effect = Exception("Unexpected error")
            result = main()

        assert result == 2

    def test_returns_130_on_keyboard_interrupt(self):
        """Test returns 130 on KeyboardInterrupt."""
        with (
            patch("sys.argv", ["prog"]),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
        ):
            MockConfig.from_env.side_effect = KeyboardInterrupt()
            result = main()

        assert result == 130

    def test_returns_0_when_cancelled(self, tmp_path):
        """Test returns 0 when user cancels analysis."""
        mock_config = Mock(spec=AnalyzerConfig)
        mock_config.output_dir = str(tmp_path)
        mock_config.repos_file = "repos.txt"
        mock_config.days = 30
        mock_config.verbose = True
        mock_config.validate = Mock()

        # Use clear=True to ensure no Jira env vars leak through
        with (
            patch("sys.argv", ["prog", "--days", "7", "--quiet", "--full", "--sources", "github"]),
            patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test1234567890123456789012"}, clear=True),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
            patch.object(main_module, "load_repositories", return_value=[]),
            patch.object(main_module, "prompt_yes_no", return_value=False),
        ):
            MockConfig.from_env.return_value = mock_config
            result = main()

        assert result == 0

    def test_handles_github_analyzer_error(self):
        """Test handles GitHubAnalyzerError."""
        with (
            patch("sys.argv", ["prog"]),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
        ):
            error = GitHubAnalyzerError("API error", "Details")
            error.exit_code = 2
            MockConfig.from_env.side_effect = error
            result = main()

        assert result == 2


# =============================================================================
# Tests for Jira integration in CLI (Feature 003)
# =============================================================================


class TestJiraIntegrationInCLI:
    """Tests for Jira extraction flow with quality metrics in CLI."""

    def test_jira_extraction_full_flow(self, tmp_path):
        """Test complete Jira extraction with metrics calculation and export."""
        from datetime import datetime, timezone

        from src.github_analyzer.api.jira_client import JiraComment, JiraIssue

        # Create mock config
        mock_config = Mock(spec=AnalyzerConfig)
        mock_config.output_dir = tmp_path
        mock_config.days = 30
        mock_config.verbose = False
        mock_config.validate = Mock()

        # Create mock Jira config
        mock_jira_config = Mock()
        mock_jira_config.base_url = "https://test.atlassian.net"

        # Create test issue
        test_issue = JiraIssue(
            key="PROJ-1",
            summary="Test issue",
            description="Test description with details",
            status="Done",
            issue_type="Bug",
            priority="High",
            assignee="John Doe",
            reporter="Jane Smith",
            created=datetime(2025, 11, 1, 10, 0, 0, tzinfo=timezone.utc),
            updated=datetime(2025, 11, 15, 10, 0, 0, tzinfo=timezone.utc),
            resolution_date=datetime(2025, 11, 15, 10, 0, 0, tzinfo=timezone.utc),
            project_key="PROJ",
        )

        # Create test comment
        test_comment = JiraComment(
            id="1",
            issue_key="PROJ-1",
            author="Alice",
            created=datetime(2025, 11, 2, 10, 0, 0, tzinfo=timezone.utc),
            body="Test comment",
        )

        # Mock JiraClient
        mock_client = Mock()
        mock_client.search_issues.return_value = iter([test_issue])
        mock_client.get_comments.return_value = [test_comment]
        mock_client.get_issue_changelog.return_value = []

        with (
            patch("sys.argv", ["prog", "--sources", "jira", "--quiet", "--days", "30", "--full"]),
            patch.dict(
                os.environ,
                {
                    "JIRA_URL": "https://test.atlassian.net",
                    "JIRA_EMAIL": "test@example.com",
                    "JIRA_API_TOKEN": "test_token",
                },
                clear=True,
            ),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
            patch.object(main_module, "JiraConfig") as MockJiraConfig,
            patch.object(main_module, "select_jira_projects", return_value=["PROJ"]),
            patch.object(main_module, "prompt_yes_no", return_value=True),
            patch(
                "src.github_analyzer.api.jira_client.JiraClient",
                return_value=mock_client,
            ),
        ):
            MockConfig.from_env.return_value = mock_config
            MockJiraConfig.from_env.return_value = mock_jira_config

            result = main()

        assert result == 0

        # Verify CSV files were created
        assert (tmp_path / "jira_issues_export.csv").exists()
        assert (tmp_path / "jira_comments_export.csv").exists()
        assert (tmp_path / "jira_project_metrics.csv").exists()
        assert (tmp_path / "jira_person_metrics.csv").exists()
        assert (tmp_path / "jira_type_metrics.csv").exists()

    def test_jira_extraction_with_multiple_issues(self, tmp_path):
        """Test Jira extraction with multiple issues across projects."""
        from datetime import datetime, timezone

        from src.github_analyzer.api.jira_client import JiraComment, JiraIssue

        mock_config = Mock(spec=AnalyzerConfig)
        mock_config.output_dir = tmp_path
        mock_config.days = 30
        mock_config.verbose = False
        mock_config.validate = Mock()

        mock_jira_config = Mock()
        mock_jira_config.base_url = "https://test.atlassian.net"

        # Create multiple test issues
        issues = [
            JiraIssue(
                key="PROJ-1",
                summary="Bug fix",
                description="Fix critical bug",
                status="Done",
                issue_type="Bug",
                priority="Critical",
                assignee="John",
                reporter="Jane",
                created=datetime(2025, 11, 1, 10, 0, 0, tzinfo=timezone.utc),
                updated=datetime(2025, 11, 10, 10, 0, 0, tzinfo=timezone.utc),
                resolution_date=datetime(2025, 11, 10, 10, 0, 0, tzinfo=timezone.utc),
                project_key="PROJ",
            ),
            JiraIssue(
                key="PROJ-2",
                summary="New feature",
                description="## Description\n\nImplement feature\n\n## Acceptance Criteria\n\n- [ ] Test",
                status="Open",
                issue_type="Story",
                priority="Medium",
                assignee="Alice",
                reporter="Bob",
                created=datetime(2025, 11, 5, 10, 0, 0, tzinfo=timezone.utc),
                updated=datetime(2025, 11, 15, 10, 0, 0, tzinfo=timezone.utc),
                resolution_date=None,
                project_key="PROJ",
            ),
            JiraIssue(
                key="OTHER-1",
                summary="Task",
                description="Do something",
                status="Done",
                issue_type="Task",
                priority="Low",
                assignee=None,
                reporter="Admin",
                created=datetime(2025, 11, 1, 10, 0, 0, tzinfo=timezone.utc),
                updated=datetime(2025, 11, 1, 18, 0, 0, tzinfo=timezone.utc),
                resolution_date=datetime(2025, 11, 1, 18, 0, 0, tzinfo=timezone.utc),
                project_key="OTHER",
            ),
        ]

        comments = {
            "PROJ-1": [
                JiraComment(
                    id="1",
                    issue_key="PROJ-1",
                    author="Alice",
                    created=datetime(2025, 11, 2, 10, 0, 0, tzinfo=timezone.utc),
                    body="Looking into this",
                ),
                JiraComment(
                    id="2",
                    issue_key="PROJ-1",
                    author="Bob",
                    created=datetime(2025, 11, 3, 10, 0, 0, tzinfo=timezone.utc),
                    body="Fixed",
                ),
            ],
            "PROJ-2": [],
            "OTHER-1": [],
        }

        mock_client = Mock()
        mock_client.search_issues.return_value = iter(issues)
        mock_client.get_comments.side_effect = lambda key: comments.get(key, [])
        mock_client.get_issue_changelog.return_value = []

        with (
            patch("sys.argv", ["prog", "--sources", "jira", "--quiet", "--days", "30", "--full"]),
            patch.dict(
                os.environ,
                {
                    "JIRA_URL": "https://test.atlassian.net",
                    "JIRA_EMAIL": "test@example.com",
                    "JIRA_API_TOKEN": "test_token",
                },
                clear=True,
            ),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
            patch.object(main_module, "JiraConfig") as MockJiraConfig,
            patch.object(main_module, "select_jira_projects", return_value=["PROJ", "OTHER"]),
            patch.object(main_module, "prompt_yes_no", return_value=True),
            patch(
                "src.github_analyzer.api.jira_client.JiraClient",
                return_value=mock_client,
            ),
        ):
            MockConfig.from_env.return_value = mock_config
            MockJiraConfig.from_env.return_value = mock_jira_config

            result = main()

        assert result == 0

        # Verify all files created
        assert (tmp_path / "jira_issues_export.csv").exists()
        assert (tmp_path / "jira_project_metrics.csv").exists()

        # Verify project metrics has 2 projects
        import csv

        with open(tmp_path / "jira_project_metrics.csv") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 2
        project_keys = {row["project_key"] for row in rows}
        assert project_keys == {"PROJ", "OTHER"}

    def test_jira_extraction_handles_empty_results(self, tmp_path):
        """Test Jira extraction handles no issues gracefully."""
        mock_config = Mock(spec=AnalyzerConfig)
        mock_config.output_dir = tmp_path
        mock_config.days = 30
        mock_config.verbose = False
        mock_config.validate = Mock()

        mock_jira_config = Mock()
        mock_jira_config.base_url = "https://test.atlassian.net"

        mock_client = Mock()
        mock_client.search_issues.return_value = iter([])

        with (
            patch("sys.argv", ["prog", "--sources", "jira", "--quiet", "--days", "30", "--full"]),
            patch.dict(
                os.environ,
                {
                    "JIRA_URL": "https://test.atlassian.net",
                    "JIRA_EMAIL": "test@example.com",
                    "JIRA_API_TOKEN": "test_token",
                },
                clear=True,
            ),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
            patch.object(main_module, "JiraConfig") as MockJiraConfig,
            patch.object(main_module, "select_jira_projects", return_value=["PROJ"]),
            patch.object(main_module, "prompt_yes_no", return_value=True),
            patch(
                "src.github_analyzer.api.jira_client.JiraClient",
                return_value=mock_client,
            ),
        ):
            MockConfig.from_env.return_value = mock_config
            MockJiraConfig.from_env.return_value = mock_jira_config

            result = main()

        assert result == 0
        # Files should still be created (with headers only)
        assert (tmp_path / "jira_issues_export.csv").exists()

    def test_jira_extraction_with_changelog_for_reopens(self, tmp_path):
        """Test Jira extraction retrieves changelog for reopen detection."""
        from datetime import datetime, timezone

        from src.github_analyzer.api.jira_client import JiraIssue

        mock_config = Mock(spec=AnalyzerConfig)
        mock_config.output_dir = tmp_path
        mock_config.days = 30
        mock_config.verbose = False
        mock_config.validate = Mock()

        mock_jira_config = Mock()
        mock_jira_config.base_url = "https://test.atlassian.net"

        test_issue = JiraIssue(
            key="PROJ-1",
            summary="Reopened issue",
            description="This issue was reopened",
            status="Done",
            issue_type="Bug",
            priority="High",
            assignee="John",
            reporter="Jane",
            created=datetime(2025, 11, 1, 10, 0, 0, tzinfo=timezone.utc),
            updated=datetime(2025, 11, 15, 10, 0, 0, tzinfo=timezone.utc),
            resolution_date=datetime(2025, 11, 15, 10, 0, 0, tzinfo=timezone.utc),
            project_key="PROJ",
        )

        # Changelog showing Done -> Open -> Done (1 reopen)
        changelog = [
            {
                "items": [
                    {"field": "status", "fromString": "Open", "toString": "Done"}
                ]
            },
            {
                "items": [
                    {"field": "status", "fromString": "Done", "toString": "Open"}
                ]
            },
            {
                "items": [
                    {"field": "status", "fromString": "Open", "toString": "Done"}
                ]
            },
        ]

        mock_client = Mock()
        mock_client.search_issues.return_value = iter([test_issue])
        mock_client.get_comments.return_value = []
        mock_client.get_issue_changelog.return_value = changelog

        with (
            patch("sys.argv", ["prog", "--sources", "jira", "--quiet", "--days", "30", "--full"]),
            patch.dict(
                os.environ,
                {
                    "JIRA_URL": "https://test.atlassian.net",
                    "JIRA_EMAIL": "test@example.com",
                    "JIRA_API_TOKEN": "test_token",
                },
                clear=True,
            ),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
            patch.object(main_module, "JiraConfig") as MockJiraConfig,
            patch.object(main_module, "select_jira_projects", return_value=["PROJ"]),
            patch.object(main_module, "prompt_yes_no", return_value=True),
            patch(
                "src.github_analyzer.api.jira_client.JiraClient",
                return_value=mock_client,
            ),
        ):
            MockConfig.from_env.return_value = mock_config
            MockJiraConfig.from_env.return_value = mock_jira_config

            result = main()

        assert result == 0

        # Verify changelog was called
        mock_client.get_issue_changelog.assert_called_once_with("PROJ-1")

        # Verify reopen_count in export
        import csv

        with open(tmp_path / "jira_issues_export.csv") as f:
            reader = csv.DictReader(f)
            row = next(reader)
        assert row["reopen_count"] == "1"


# =============================================================================
# Tests for GitHub analyzer run in main()
# =============================================================================


class TestGitHubAnalyzerInMain:
    """Tests for GitHub analyzer flow in main()."""

    def test_github_analysis_full_flow(self, tmp_path):
        """Test complete GitHub analysis flow in main()."""
        mock_config = Mock(spec=AnalyzerConfig)
        mock_config.output_dir = tmp_path
        mock_config.days = 30
        mock_config.verbose = False
        mock_config.validate = Mock()

        mock_analyzer = Mock()

        with (
            patch("sys.argv", ["prog", "--sources", "github", "--quiet", "--days", "30", "--full"]),
            patch.dict(
                os.environ,
                {
                    "GITHUB_TOKEN": "test_token",
                },
                clear=True,
            ),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
            patch.object(main_module, "load_repositories", return_value=[Repository(owner="test", name="repo")]),
            patch.object(main_module, "prompt_yes_no", return_value=True),
            patch.object(main_module, "GitHubAnalyzer", return_value=mock_analyzer) as MockAnalyzer,
        ):
            MockConfig.from_env.return_value = mock_config

            result = main()

        assert result == 0
        # Verify analyzer was created and used
        MockAnalyzer.assert_called_once()
        mock_analyzer.run.assert_called_once()
        mock_analyzer.close.assert_called_once()

    def test_github_analysis_calls_close_on_success(self, tmp_path):
        """Test GitHub analyzer close is called after successful run."""
        mock_config = Mock(spec=AnalyzerConfig)
        mock_config.output_dir = tmp_path
        mock_config.days = 30
        mock_config.verbose = False
        mock_config.validate = Mock()

        mock_analyzer = Mock()

        with (
            patch("sys.argv", ["prog", "--sources", "github", "--quiet", "--days", "30", "--full"]),
            patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}, clear=True),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
            patch.object(main_module, "load_repositories", return_value=[Repository(owner="o", name="r")]),
            patch.object(main_module, "prompt_yes_no", return_value=True),
            patch.object(main_module, "GitHubAnalyzer", return_value=mock_analyzer),
        ):
            MockConfig.from_env.return_value = mock_config

            main()

        # close should always be called via finally
        mock_analyzer.close.assert_called_once()

    def test_github_analysis_calls_close_on_exception(self, tmp_path):
        """Test GitHub analyzer close is called even when run() raises."""
        mock_config = Mock(spec=AnalyzerConfig)
        mock_config.output_dir = tmp_path
        mock_config.days = 30
        mock_config.verbose = False
        mock_config.validate = Mock()

        mock_analyzer = Mock()
        mock_analyzer.run.side_effect = RuntimeError("API failure")

        with (
            patch("sys.argv", ["prog", "--sources", "github", "--quiet", "--days", "30", "--full"]),
            patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}, clear=True),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
            patch.object(main_module, "load_repositories", return_value=[Repository(owner="o", name="r")]),
            patch.object(main_module, "prompt_yes_no", return_value=True),
            patch.object(main_module, "GitHubAnalyzer", return_value=mock_analyzer),
        ):
            MockConfig.from_env.return_value = mock_config

            result = main()

        # close should still be called via finally
        mock_analyzer.close.assert_called_once()
        # Should return error code for unexpected exception
        assert result == 2


# =============================================================================
# Tests for error handling in main()
# =============================================================================


class TestMainErrorHandling:
    """Tests for error handling in main()."""

    def test_keyboard_interrupt_returns_130(self, tmp_path):
        """Test KeyboardInterrupt returns exit code 130."""
        mock_config = Mock(spec=AnalyzerConfig)
        mock_config.output_dir = tmp_path
        mock_config.days = 30
        mock_config.verbose = False
        mock_config.validate = Mock()

        with (
            patch("sys.argv", ["prog", "--sources", "github", "--quiet", "--days", "30", "--full"]),
            patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}, clear=True),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
            patch.object(main_module, "load_repositories", side_effect=KeyboardInterrupt),
        ):
            MockConfig.from_env.return_value = mock_config

            result = main()

        assert result == 130

    def test_unexpected_exception_returns_2(self, tmp_path):
        """Test unexpected exception returns exit code 2."""
        mock_config = Mock(spec=AnalyzerConfig)
        mock_config.output_dir = tmp_path
        mock_config.days = 30
        mock_config.verbose = False
        mock_config.validate = Mock()

        with (
            patch("sys.argv", ["prog", "--sources", "github", "--quiet", "--days", "30", "--full"]),
            patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}, clear=True),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
            patch.object(main_module, "load_repositories", side_effect=RuntimeError("Unexpected")),
        ):
            MockConfig.from_env.return_value = mock_config

            result = main()

        assert result == 2

    def test_configuration_error_returns_exit_code(self, tmp_path):
        """Test ConfigurationError returns its exit code."""
        from src.github_analyzer.core.exceptions import ConfigurationError

        with (
            patch("sys.argv", ["prog", "--sources", "github", "--quiet"]),
            patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}, clear=True),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
        ):
            error = ConfigurationError("Missing config", "Details")
            error.exit_code = 1
            MockConfig.from_env.side_effect = error

            result = main()

        assert result == 1


# =============================================================================
# Tests for CLI argument overrides
# =============================================================================


class TestCLIArgumentOverrides:
    """Tests for CLI argument overrides in main()."""

    def test_output_argument_overrides_config(self, tmp_path):
        """Test --output argument overrides config output_dir."""
        mock_config = Mock(spec=AnalyzerConfig)
        mock_config.output_dir = "/default/output"
        mock_config.days = 30
        mock_config.verbose = False
        mock_config.validate = Mock()

        custom_output = str(tmp_path / "custom_output")

        with (
            patch("sys.argv", ["prog", "--sources", "github", "--quiet", "--days", "30",
                               "--full", "--output", custom_output]),
            patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}, clear=True),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
            patch.object(main_module, "load_repositories", return_value=[Repository(owner="o", name="r")]),
            patch.object(main_module, "prompt_yes_no", return_value=True),
            patch.object(main_module, "GitHubAnalyzer") as MockAnalyzer,
        ):
            MockConfig.from_env.return_value = mock_config

            main()

        # Config output_dir should be overridden
        assert mock_config.output_dir == custom_output

    def test_repos_argument_overrides_config(self, tmp_path):
        """Test --repos argument overrides config repos_file."""
        mock_config = Mock(spec=AnalyzerConfig)
        mock_config.output_dir = tmp_path
        mock_config.repos_file = "default_repos.txt"
        mock_config.days = 30
        mock_config.verbose = False
        mock_config.validate = Mock()

        with (
            patch("sys.argv", ["prog", "--sources", "github", "--quiet", "--days", "30",
                               "--full", "--repos", "custom_repos.txt"]),
            patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}, clear=True),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
            patch.object(main_module, "load_repositories", return_value=[Repository(owner="o", name="r")]),
            patch.object(main_module, "prompt_yes_no", return_value=True),
            patch.object(main_module, "GitHubAnalyzer") as MockAnalyzer,
        ):
            MockConfig.from_env.return_value = mock_config

            main()

        # Config repos_file should be overridden
        assert mock_config.repos_file == "custom_repos.txt"

    def test_auto_detect_sources_with_no_sources_returns_error(self, tmp_path):
        """Test auto-detect with no available sources returns exit code 1."""
        mock_config = Mock(spec=AnalyzerConfig)
        mock_config.output_dir = tmp_path
        mock_config.days = 30
        mock_config.verbose = False
        mock_config.validate = Mock()

        with (
            patch("sys.argv", ["prog", "--sources", "auto", "--quiet"]),
            patch.dict(os.environ, {}, clear=True),  # No tokens
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
            patch.object(main_module, "auto_detect_sources", return_value=set()),
        ):
            MockConfig.from_env.return_value = mock_config

            result = main()

        assert result == 1

    def test_interactive_prompts_when_no_cli_args(self, tmp_path):
        """Test interactive prompts are used when CLI args not provided."""
        mock_config = Mock(spec=AnalyzerConfig)
        mock_config.output_dir = tmp_path
        mock_config.days = 7  # default
        mock_config.verbose = True  # default
        mock_config.validate = Mock()

        with (
            patch("sys.argv", ["prog", "--sources", "github"]),  # No --quiet, --days, --full
            patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}, clear=True),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
            patch.object(main_module, "load_repositories", return_value=[Repository(owner="o", name="r")]),
            patch.object(main_module, "prompt_int", return_value=14) as mock_prompt_int,
            patch.object(main_module, "prompt_yes_no", side_effect=[False, True, True]) as mock_prompt_yn,
            patch.object(main_module, "GitHubAnalyzer") as MockAnalyzer,
        ):
            MockConfig.from_env.return_value = mock_config

            result = main()

        # prompt_int should be called for days
        mock_prompt_int.assert_called_once()
        # prompt_yes_no called: quiet mode, full PR details, start analysis
        assert mock_prompt_yn.call_count == 3
        assert result == 0

    def test_many_jira_projects_shows_truncated_list(self, tmp_path):
        """Test more than 5 Jira projects shows truncated list."""
        from datetime import datetime, timezone

        from src.github_analyzer.api.jira_client import JiraIssue

        mock_config = Mock(spec=AnalyzerConfig)
        mock_config.output_dir = tmp_path
        mock_config.days = 30
        mock_config.verbose = False
        mock_config.validate = Mock()

        mock_jira_config = Mock()
        mock_jira_config.base_url = "https://test.atlassian.net"
        mock_jira_config.jira_projects_file = "jira_projects.txt"

        # 7 projects (more than 5)
        project_keys = ["PROJ1", "PROJ2", "PROJ3", "PROJ4", "PROJ5", "PROJ6", "PROJ7"]

        test_issue = JiraIssue(
            key="PROJ1-1",
            summary="Test",
            description="Test",
            status="Done",
            issue_type="Task",
            priority="Medium",
            assignee="Test",
            reporter="Test",
            created=datetime(2025, 11, 1, tzinfo=timezone.utc),
            updated=datetime(2025, 11, 1, tzinfo=timezone.utc),
            resolution_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
            project_key="PROJ1",
        )

        mock_client = Mock()
        mock_client.search_issues.return_value = iter([test_issue])
        mock_client.get_comments.return_value = []
        mock_client.get_issue_changelog.return_value = []

        with (
            patch("sys.argv", ["prog", "--sources", "jira", "--quiet", "--days", "30", "--full"]),
            patch.dict(
                os.environ,
                {
                    "JIRA_URL": "https://test.atlassian.net",
                    "JIRA_EMAIL": "test@example.com",
                    "JIRA_API_TOKEN": "test_token",
                },
                clear=True,
            ),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
            patch.object(main_module, "JiraConfig") as MockJiraConfig,
            patch.object(main_module, "select_jira_projects", return_value=project_keys),
            patch.object(main_module, "prompt_yes_no", return_value=True),
            patch("src.github_analyzer.api.jira_client.JiraClient", return_value=mock_client),
        ):
            MockConfig.from_env.return_value = mock_config
            MockJiraConfig.from_env.return_value = mock_jira_config

            result = main()

        assert result == 0
