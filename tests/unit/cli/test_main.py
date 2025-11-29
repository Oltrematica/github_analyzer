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

# Import new functions for Feature 005 (will be implemented)
try:
    from src.github_analyzer.cli.main import (
        get_cutoff_date,
        filter_by_activity,
        display_activity_stats,
    )
    HAS_FEATURE_005 = True
except ImportError:
    HAS_FEATURE_005 = False

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
        mock_config.github_token = "test_token"
        mock_config.days = 30
        mock_config.verbose = True
        mock_config.validate = Mock()

        # Use clear=True to ensure no Jira env vars leak through
        with (
            patch("sys.argv", ["prog", "--days", "7", "--quiet", "--full", "--sources", "github"]),
            patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test1234567890123456789012"}, clear=True),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
            patch.object(main_module, "select_github_repos", return_value=[]),
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
        mock_config.repos_file = "repos.txt"
        mock_config.github_token = "test_token"
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
            patch.object(main_module, "select_github_repos", return_value=["test/repo"]),
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
        mock_config.repos_file = "repos.txt"
        mock_config.github_token = "test_token"
        mock_config.days = 30
        mock_config.verbose = False
        mock_config.validate = Mock()

        mock_analyzer = Mock()

        with (
            patch("sys.argv", ["prog", "--sources", "github", "--quiet", "--days", "30", "--full"]),
            patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}, clear=True),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
            patch.object(main_module, "select_github_repos", return_value=["o/r"]),
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
        mock_config.repos_file = "repos.txt"
        mock_config.github_token = "test_token"
        mock_config.days = 30
        mock_config.verbose = False
        mock_config.validate = Mock()

        mock_analyzer = Mock()
        mock_analyzer.run.side_effect = RuntimeError("API failure")

        with (
            patch("sys.argv", ["prog", "--sources", "github", "--quiet", "--days", "30", "--full"]),
            patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}, clear=True),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
            patch.object(main_module, "select_github_repos", return_value=["o/r"]),
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
        mock_config.repos_file = "repos.txt"
        mock_config.github_token = "test_token"
        mock_config.days = 30
        mock_config.verbose = False
        mock_config.validate = Mock()

        with (
            patch("sys.argv", ["prog", "--sources", "github", "--quiet", "--days", "30", "--full"]),
            patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}, clear=True),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
            patch.object(main_module, "select_github_repos", side_effect=KeyboardInterrupt),
        ):
            MockConfig.from_env.return_value = mock_config

            result = main()

        assert result == 130

    def test_unexpected_exception_returns_2(self, tmp_path):
        """Test unexpected exception returns exit code 2."""
        mock_config = Mock(spec=AnalyzerConfig)
        mock_config.output_dir = tmp_path
        mock_config.repos_file = "repos.txt"
        mock_config.github_token = "test_token"
        mock_config.days = 30
        mock_config.verbose = False
        mock_config.validate = Mock()

        with (
            patch("sys.argv", ["prog", "--sources", "github", "--quiet", "--days", "30", "--full"]),
            patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}, clear=True),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
            patch.object(main_module, "select_github_repos", side_effect=RuntimeError("Unexpected")),
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
        mock_config.repos_file = "repos.txt"
        mock_config.github_token = "test_token"
        mock_config.days = 30
        mock_config.verbose = False
        mock_config.validate = Mock()

        custom_output = str(tmp_path / "custom_output")

        with (
            patch("sys.argv", ["prog", "--sources", "github", "--quiet", "--days", "30",
                               "--full", "--output", custom_output]),
            patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}, clear=True),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
            patch.object(main_module, "select_github_repos", return_value=["o/r"]),
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
        mock_config.github_token = "test_token"
        mock_config.days = 30
        mock_config.verbose = False
        mock_config.validate = Mock()

        with (
            patch("sys.argv", ["prog", "--sources", "github", "--quiet", "--days", "30",
                               "--full", "--repos", "custom_repos.txt"]),
            patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}, clear=True),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
            patch.object(main_module, "select_github_repos", return_value=["o/r"]),
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
        mock_config.repos_file = "repos.txt"
        mock_config.github_token = "test_token"
        mock_config.days = 7  # default
        mock_config.verbose = True  # default
        mock_config.validate = Mock()

        with (
            patch("sys.argv", ["prog", "--sources", "github"]),  # No --quiet, --days, --full
            patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}, clear=True),
            patch.object(main_module, "AnalyzerConfig") as MockConfig,
            patch.object(main_module, "select_github_repos", return_value=["o/r"]),
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


# =============================================================================
# Tests for Feature 005: Smart Repository Filtering
# =============================================================================


class TestGetCutoffDate:
    """Tests for get_cutoff_date function (T004 - Feature 005)."""

    def test_calculates_cutoff_for_30_days(self):
        """Test cutoff date calculation for 30 days."""
        # Skip if function not yet implemented
        if not HAS_FEATURE_005:
            pytest.skip("Feature 005 not yet implemented")

        result = get_cutoff_date(30)

        expected = datetime.now(timezone.utc).date() - timedelta(days=30)
        assert result == expected

    def test_calculates_cutoff_for_7_days(self):
        """Test cutoff date calculation for 7 days."""
        if not HAS_FEATURE_005:
            pytest.skip("Feature 005 not yet implemented")

        result = get_cutoff_date(7)

        expected = datetime.now(timezone.utc).date() - timedelta(days=7)
        assert result == expected

    def test_calculates_cutoff_for_365_days(self):
        """Test cutoff date calculation for 365 days (1 year)."""
        if not HAS_FEATURE_005:
            pytest.skip("Feature 005 not yet implemented")

        result = get_cutoff_date(365)

        expected = datetime.now(timezone.utc).date() - timedelta(days=365)
        assert result == expected

    def test_returns_date_object(self):
        """Test that result is a date object (not datetime)."""
        if not HAS_FEATURE_005:
            pytest.skip("Feature 005 not yet implemented")

        from datetime import date

        result = get_cutoff_date(30)

        assert isinstance(result, date)

    def test_handles_zero_days(self):
        """Test cutoff for 0 days returns today."""
        if not HAS_FEATURE_005:
            pytest.skip("Feature 005 not yet implemented")

        result = get_cutoff_date(0)

        expected = datetime.now(timezone.utc).date()
        assert result == expected


class TestFilterByActivity:
    """Tests for filter_by_activity function (T005 - Feature 005)."""

    def test_filters_active_repos(self):
        """Test filtering repos by pushed_at date."""
        if not HAS_FEATURE_005:
            pytest.skip("Feature 005 not yet implemented")

        repos = [
            {"full_name": "user/active", "pushed_at": "2025-11-28T10:00:00Z"},
            {"full_name": "user/inactive", "pushed_at": "2025-10-01T10:00:00Z"},
            {"full_name": "user/recent", "pushed_at": "2025-11-15T10:00:00Z"},
        ]

        # Filter for repos pushed after Nov 10, 2025
        from datetime import date
        cutoff = date(2025, 11, 10)

        result = filter_by_activity(repos, cutoff)

        assert len(result) == 2
        assert result[0]["full_name"] == "user/active"
        assert result[1]["full_name"] == "user/recent"

    def test_returns_empty_for_all_inactive(self):
        """Test returns empty list when no repos match."""
        if not HAS_FEATURE_005:
            pytest.skip("Feature 005 not yet implemented")

        repos = [
            {"full_name": "user/old1", "pushed_at": "2024-01-01T10:00:00Z"},
            {"full_name": "user/old2", "pushed_at": "2024-06-15T10:00:00Z"},
        ]

        from datetime import date
        cutoff = date(2025, 11, 1)

        result = filter_by_activity(repos, cutoff)

        assert result == []

    def test_returns_all_for_all_active(self):
        """Test returns all repos when all are active."""
        if not HAS_FEATURE_005:
            pytest.skip("Feature 005 not yet implemented")

        repos = [
            {"full_name": "user/repo1", "pushed_at": "2025-11-28T10:00:00Z"},
            {"full_name": "user/repo2", "pushed_at": "2025-11-25T10:00:00Z"},
        ]

        from datetime import date
        cutoff = date(2025, 11, 1)

        result = filter_by_activity(repos, cutoff)

        assert len(result) == 2

    def test_handles_empty_repos_list(self):
        """Test handles empty repos list gracefully."""
        if not HAS_FEATURE_005:
            pytest.skip("Feature 005 not yet implemented")

        from datetime import date
        cutoff = date(2025, 11, 1)

        result = filter_by_activity([], cutoff)

        assert result == []

    def test_includes_repos_pushed_on_cutoff_date(self):
        """Test includes repos pushed exactly on cutoff date (inclusive boundary)."""
        if not HAS_FEATURE_005:
            pytest.skip("Feature 005 not yet implemented")

        repos = [
            {"full_name": "user/on-cutoff", "pushed_at": "2025-11-01T10:00:00Z"},
            {"full_name": "user/before", "pushed_at": "2025-10-31T10:00:00Z"},
        ]

        from datetime import date
        cutoff = date(2025, 11, 1)

        result = filter_by_activity(repos, cutoff)

        assert len(result) == 1
        assert result[0]["full_name"] == "user/on-cutoff"

    def test_handles_missing_pushed_at_field(self):
        """Test treats repos without pushed_at as inactive."""
        if not HAS_FEATURE_005:
            pytest.skip("Feature 005 not yet implemented")

        repos = [
            {"full_name": "user/no-pushed-at"},  # No pushed_at field
            {"full_name": "user/active", "pushed_at": "2025-11-28T10:00:00Z"},
        ]

        from datetime import date
        cutoff = date(2025, 11, 1)

        result = filter_by_activity(repos, cutoff)

        assert len(result) == 1
        assert result[0]["full_name"] == "user/active"

    def test_handles_null_pushed_at_value(self):
        """Test treats repos with null pushed_at as inactive."""
        if not HAS_FEATURE_005:
            pytest.skip("Feature 005 not yet implemented")

        repos = [
            {"full_name": "user/null-pushed", "pushed_at": None},
            {"full_name": "user/active", "pushed_at": "2025-11-28T10:00:00Z"},
        ]

        from datetime import date
        cutoff = date(2025, 11, 1)

        result = filter_by_activity(repos, cutoff)

        assert len(result) == 1
        assert result[0]["full_name"] == "user/active"

    def test_preserves_original_repo_data(self):
        """Test that filtering preserves all original repo fields."""
        if not HAS_FEATURE_005:
            pytest.skip("Feature 005 not yet implemented")

        repos = [
            {
                "full_name": "user/repo1",
                "pushed_at": "2025-11-28T10:00:00Z",
                "private": True,
                "description": "Test repo",
                "stargazers_count": 42,
            },
        ]

        from datetime import date
        cutoff = date(2025, 11, 1)

        result = filter_by_activity(repos, cutoff)

        assert len(result) == 1
        assert result[0]["private"] is True
        assert result[0]["description"] == "Test repo"
        assert result[0]["stargazers_count"] == 42

    def test_handles_invalid_date_format(self):
        """Test skips repos with invalid pushed_at date format (covers ValueError)."""
        if not HAS_FEATURE_005:
            pytest.skip("Feature 005 not yet implemented")

        repos = [
            {"full_name": "user/invalid-date", "pushed_at": "not-a-date"},
            {"full_name": "user/malformed", "pushed_at": "2025/11/28"},
            {"full_name": "user/active", "pushed_at": "2025-11-28T10:00:00Z"},
        ]

        from datetime import date
        cutoff = date(2025, 11, 1)

        result = filter_by_activity(repos, cutoff)

        # Only valid date should be included
        assert len(result) == 1
        assert result[0]["full_name"] == "user/active"

    def test_handles_pushed_at_as_non_string(self):
        """Test skips repos where pushed_at is not a string (covers AttributeError)."""
        if not HAS_FEATURE_005:
            pytest.skip("Feature 005 not yet implemented")

        repos = [
            {"full_name": "user/numeric-date", "pushed_at": 12345},
            {"full_name": "user/list-date", "pushed_at": ["2025-11-28"]},
            {"full_name": "user/active", "pushed_at": "2025-11-28T10:00:00Z"},
        ]

        from datetime import date
        cutoff = date(2025, 11, 1)

        result = filter_by_activity(repos, cutoff)

        # Only valid string date should be included
        assert len(result) == 1
        assert result[0]["full_name"] == "user/active"


class TestDisplayActivityStats:
    """Tests for display_activity_stats function (T006 - Feature 005)."""

    def test_formats_stats_correctly(self, capsys):
        """Test stats display format matches spec."""
        if not HAS_FEATURE_005:
            pytest.skip("Feature 005 not yet implemented")

        display_activity_stats(total=135, active=28, days=30)

        captured = capsys.readouterr()
        assert "135 repos found, 28 with activity in last 30 days" in captured.out

    def test_handles_zero_active(self, capsys):
        """Test stats display with zero active repos."""
        if not HAS_FEATURE_005:
            pytest.skip("Feature 005 not yet implemented")

        display_activity_stats(total=50, active=0, days=7)

        captured = capsys.readouterr()
        assert "50 repos found, 0 with activity in last 7 days" in captured.out

    def test_handles_all_active(self, capsys):
        """Test stats display when all repos are active."""
        if not HAS_FEATURE_005:
            pytest.skip("Feature 005 not yet implemented")

        display_activity_stats(total=10, active=10, days=14)

        captured = capsys.readouterr()
        assert "10 repos found, 10 with activity in last 14 days" in captured.out


class TestLoadGitHubReposFromFile:
    """Tests for load_github_repos_from_file function."""

    def test_loads_simple_repo_names(self, tmp_path):
        """Test loading simple owner/repo format."""
        from src.github_analyzer.cli.main import load_github_repos_from_file

        repos_file = tmp_path / "repos.txt"
        repos_file.write_text("owner/repo1\nowner/repo2\n")

        result = load_github_repos_from_file(str(repos_file))

        assert result == ["owner/repo1", "owner/repo2"]

    def test_skips_comments_and_empty_lines(self, tmp_path):
        """Test skipping comments and empty lines."""
        from src.github_analyzer.cli.main import load_github_repos_from_file

        repos_file = tmp_path / "repos.txt"
        repos_file.write_text("# This is a comment\n\nowner/repo1\n# Another comment\nowner/repo2\n\n")

        result = load_github_repos_from_file(str(repos_file))

        assert result == ["owner/repo1", "owner/repo2"]

    def test_extracts_repo_from_github_url(self, tmp_path):
        """Test extracting owner/repo from full GitHub URLs."""
        from src.github_analyzer.cli.main import load_github_repos_from_file

        repos_file = tmp_path / "repos.txt"
        repos_file.write_text("https://github.com/owner/repo1\nhttps://github.com/owner/repo2.git\n")

        result = load_github_repos_from_file(str(repos_file))

        assert result == ["owner/repo1", "owner/repo2"]

    def test_handles_url_with_trailing_slash(self, tmp_path):
        """Test URL with trailing slash."""
        from src.github_analyzer.cli.main import load_github_repos_from_file

        repos_file = tmp_path / "repos.txt"
        repos_file.write_text("https://github.com/owner/repo1/\n")

        result = load_github_repos_from_file(str(repos_file))

        assert result == ["owner/repo1"]

    def test_returns_empty_for_nonexistent_file(self, tmp_path):
        """Test returns empty list when file doesn't exist."""
        from src.github_analyzer.cli.main import load_github_repos_from_file

        result = load_github_repos_from_file(str(tmp_path / "nonexistent.txt"))

        assert result == []

    def test_handles_short_url(self, tmp_path):
        """Test URL that is too short to extract repo from."""
        from src.github_analyzer.cli.main import load_github_repos_from_file

        repos_file = tmp_path / "repos.txt"
        # URL with only one path segment
        repos_file.write_text("http://github.com/owner\nowner/repo\n")

        result = load_github_repos_from_file(str(repos_file))

        # Should skip invalid URL and include valid repo
        assert "owner/repo" in result

    def test_handles_oserror(self, tmp_path, monkeypatch):
        """Test handles OSError during file read (covers except OSError branch)."""
        from src.github_analyzer.cli.main import load_github_repos_from_file

        # Create a file that exists but will fail to read
        repos_file = tmp_path / "repos.txt"
        repos_file.write_text("owner/repo\n")

        # Patch Path.read_text to raise OSError
        from pathlib import Path
        original_read_text = Path.read_text

        def mock_read_text(self, *args, **kwargs):
            if str(self).endswith("repos.txt"):
                raise OSError("Permission denied")
            return original_read_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", mock_read_text)

        result = load_github_repos_from_file(str(repos_file))

        assert result == []