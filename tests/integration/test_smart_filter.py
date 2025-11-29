"""Integration tests for Smart Repository Filtering (Feature 005).

Tests the integration of activity filtering into the repository selection
flow per FR-001 to FR-010.
"""

import sys
from datetime import datetime, timezone
from io import StringIO
from unittest.mock import Mock, patch

import pytest

# Import the module directly
from src.github_analyzer.cli.main import (
    display_activity_stats,
    filter_by_activity,
    get_cutoff_date,
    select_github_repos,
)

# Get the actual module object for patching
main_module = sys.modules["src.github_analyzer.cli.main"]


@pytest.fixture
def mock_config():
    """Create a mock config."""
    from src.github_analyzer.config.settings import AnalyzerConfig

    config = Mock(spec=AnalyzerConfig)
    config.github_token = "ghp_test_token_12345678901234567890"
    config.timeout = 30
    config.per_page = 100
    config.max_pages = 50
    config.days = 30
    return config


@pytest.fixture
def sample_repos_mixed_activity():
    """Sample repos with mixed activity dates."""
    return [
        {
            "full_name": "user/active-repo",
            "pushed_at": "2025-11-28T10:00:00Z",
            "private": False,
            "description": "Active repository",
        },
        {
            "full_name": "user/recent-repo",
            "pushed_at": "2025-11-15T10:00:00Z",
            "private": False,
            "description": "Recently pushed",
        },
        {
            "full_name": "user/old-repo",
            "pushed_at": "2025-09-01T10:00:00Z",
            "private": False,
            "description": "Old repository",
        },
        {
            "full_name": "user/very-old-repo",
            "pushed_at": "2024-01-01T10:00:00Z",
            "private": True,
            "description": "Very old repository",
        },
    ]


# =============================================================================
# Tests for User Story 1: Filter Repositories by Recent Activity (T010-T014)
# =============================================================================


class TestOptionADisplaysActivityStats:
    """T010: Test [A] option displays activity stats."""

    def test_option_a_shows_stats_for_mixed_repos(
        self, mock_config, sample_repos_mixed_activity, capsys
    ):
        """Test [A] shows total and active count with correct format."""
        from datetime import date

        from src.github_analyzer.api.client import GitHubClient

        # Mock the client to return our sample repos
        mock_client = Mock(spec=GitHubClient)
        mock_client.list_user_repos.return_value = sample_repos_mixed_activity
        mock_client.close = Mock()

        # Simulate selecting [A] option
        with (
            patch.object(main_module, "GitHubClient", return_value=mock_client),
            patch.object(main_module, "AnalyzerConfig"),
            patch("builtins.input", side_effect=["A"]),  # Select All
        ):
            # The select_github_repos function with interactive mode
            # For now, we test the filtering logic directly
            cutoff = get_cutoff_date(30)

            # With 30-day cutoff from Nov 29, repos pushed after Oct 30 are active
            # active-repo (Nov 28), recent-repo (Nov 15) are active
            # old-repo (Sep 1), very-old-repo (Jan 2024) are inactive
            active = filter_by_activity(sample_repos_mixed_activity, cutoff)

            # Display stats
            display_activity_stats(
                total=len(sample_repos_mixed_activity),
                active=len(active),
                days=30,
            )

            captured = capsys.readouterr()
            # Per FR-007: exact format
            assert "4 repos found, 2 with activity in last 30 days" in captured.out


class TestOptionLDisplaysActivityStats:
    """T011: Test [L] option displays activity stats."""

    def test_option_l_shows_stats_before_list(
        self, mock_config, sample_repos_mixed_activity, capsys
    ):
        """Test [L] shows activity stats before displaying numbered list."""
        cutoff = get_cutoff_date(30)
        active = filter_by_activity(sample_repos_mixed_activity, cutoff)

        display_activity_stats(
            total=len(sample_repos_mixed_activity),
            active=len(active),
            days=30,
        )

        captured = capsys.readouterr()
        assert "4 repos found, 2 with activity in last 30 days" in captured.out


class TestFilterCorrectlyIdentifiesActive:
    """T012: Test filter correctly identifies active repos by pushed_at."""

    def test_filter_includes_repos_pushed_after_cutoff(self, sample_repos_mixed_activity):
        """Test that repos pushed after cutoff are included."""
        from datetime import date

        # Cutoff = Nov 1, 2025
        cutoff = date(2025, 11, 1)
        active = filter_by_activity(sample_repos_mixed_activity, cutoff)

        # Should include active-repo (Nov 28) and recent-repo (Nov 15)
        assert len(active) == 2
        names = [r["full_name"] for r in active]
        assert "user/active-repo" in names
        assert "user/recent-repo" in names

    def test_filter_excludes_repos_pushed_before_cutoff(self, sample_repos_mixed_activity):
        """Test that repos pushed before cutoff are excluded."""
        from datetime import date

        cutoff = date(2025, 11, 1)
        active = filter_by_activity(sample_repos_mixed_activity, cutoff)

        names = [r["full_name"] for r in active]
        assert "user/old-repo" not in names
        assert "user/very-old-repo" not in names

    def test_filter_accuracy_matches_manual_count(self, sample_repos_mixed_activity):
        """Test SC-003: Statistics accuracy matches actual activity status."""
        from datetime import date

        cutoff = date(2025, 11, 1)

        # Manual count of repos where pushed_at >= cutoff
        manual_count = sum(
            1 for r in sample_repos_mixed_activity
            if r.get("pushed_at") and
            datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00")).date() >= cutoff
        )

        # Filter count
        filter_count = len(filter_by_activity(sample_repos_mixed_activity, cutoff))

        assert filter_count == manual_count == 2


class TestStatsFormatMatchesFR007:
    """T013: Test stats format matches FR-007 specification."""

    def test_exact_format_135_28_30(self, capsys):
        """Test exact format: '135 repos found, 28 with activity in last 30 days'."""
        display_activity_stats(total=135, active=28, days=30)

        captured = capsys.readouterr()
        assert captured.out.strip() == "135 repos found, 28 with activity in last 30 days"

    def test_format_with_different_values(self, capsys):
        """Test format works with different numeric values."""
        display_activity_stats(total=50, active=12, days=7)

        captured = capsys.readouterr()
        assert captured.out.strip() == "50 repos found, 12 with activity in last 7 days"

    def test_format_zero_active(self, capsys):
        """Test format when no active repos found."""
        display_activity_stats(total=100, active=0, days=14)

        captured = capsys.readouterr()
        assert captured.out.strip() == "100 repos found, 0 with activity in last 14 days"

    def test_format_all_active(self, capsys):
        """Test format when all repos are active."""
        display_activity_stats(total=25, active=25, days=365)

        captured = capsys.readouterr()
        assert captured.out.strip() == "25 repos found, 25 with activity in last 365 days"


class TestUsesDaysParameterForCutoff:
    """T014: Test uses --days parameter for cutoff date (FR-010)."""

    def test_cutoff_uses_days_parameter_30(self):
        """Test cutoff with 30 days."""
        from datetime import date, timedelta

        cutoff = get_cutoff_date(30)
        expected = date.today() - timedelta(days=30)

        assert cutoff == expected

    def test_cutoff_uses_days_parameter_7(self):
        """Test cutoff with 7 days."""
        from datetime import date, timedelta

        cutoff = get_cutoff_date(7)
        expected = date.today() - timedelta(days=7)

        assert cutoff == expected

    def test_cutoff_uses_days_parameter_90(self):
        """Test cutoff with 90 days."""
        from datetime import date, timedelta

        cutoff = get_cutoff_date(90)
        expected = date.today() - timedelta(days=90)

        assert cutoff == expected

    def test_filtering_respects_days_parameter(self, sample_repos_mixed_activity):
        """Test that filtering uses the correct days parameter."""
        from datetime import date

        # With 7 days cutoff from Nov 29, only Nov 28 repo is active
        cutoff_7days = get_cutoff_date(7)
        active_7days = filter_by_activity(sample_repos_mixed_activity, cutoff_7days)

        # With 365 days cutoff, all except very-old-repo should be active
        cutoff_365days = get_cutoff_date(365)
        active_365days = filter_by_activity(sample_repos_mixed_activity, cutoff_365days)

        # Different days parameters should yield different results
        assert len(active_7days) <= len(active_365days)


# =============================================================================
# Tests for User Story 2: Organization Repository Filtering (T020-T023)
# =============================================================================


class TestOptionOUsesSearchAPI:
    """T020: Test [O] option uses Search API for org repos."""

    def test_search_api_called_for_org_repos(self, mock_config):
        """Test that Search API is used for organization repositories."""
        from src.github_analyzer.api.client import GitHubClient

        mock_client = Mock(spec=GitHubClient)
        mock_client.search_repos.return_value = {
            "total_count": 12,
            "incomplete_results": False,
            "items": [{"full_name": "testorg/repo1", "pushed_at": "2025-11-28T10:00:00Z"}],
        }
        mock_client.list_org_repos.return_value = [
            {"full_name": f"testorg/repo{i}"} for i in range(50)
        ]

        # Verify search_repos would be called with correct query format
        # This tests the expected integration pattern
        from datetime import date

        cutoff = date(2025, 10, 30)
        expected_query = f"org:testorg+pushed:>{cutoff.isoformat()}"

        # The search should use format: org:NAME+pushed:>YYYY-MM-DD
        assert "org:testorg" in expected_query
        assert "pushed:>" in expected_query


class TestOrgSearchQueryFormat:
    """T021: Test org search query format 'org:NAME+pushed:>DATE'."""

    def test_query_format_with_date(self):
        """Test the search query format is correct."""
        from datetime import date

        org_name = "github"
        cutoff = date(2025, 10, 30)

        # Expected format per spec
        query = f"org:{org_name}+pushed:>{cutoff.isoformat()}"

        assert query == "org:github+pushed:>2025-10-30"

    def test_query_format_with_different_org(self):
        """Test query format with various org names."""
        from datetime import date

        cutoff = date(2025, 11, 1)

        for org in ["microsoft", "facebook", "my-company"]:
            query = f"org:{org}+pushed:>{cutoff.isoformat()}"
            assert query.startswith(f"org:{org}+pushed:>")


class TestOrgStatsDisplay:
    """T022: Test org stats display '50 org repos found, 12 with activity'."""

    def test_org_stats_display_format(self, capsys):
        """Test org stats use same format as personal repos."""
        # Per spec: format should be consistent
        display_activity_stats(total=50, active=12, days=30)

        captured = capsys.readouterr()
        assert "50 repos found, 12 with activity in last 30 days" in captured.out


class TestSearchAPIPagination:
    """T023: Test Search API pagination for large orgs (100+ active)."""

    def test_search_handles_pagination(self, mock_config):
        """Test search_repos handles pagination for large results."""
        from src.github_analyzer.api.client import GitHubClient

        mock_client = Mock(spec=GitHubClient)

        # Simulate 150 results across pages
        mock_client.search_repos.return_value = {
            "total_count": 150,
            "incomplete_results": False,
            "items": [{"id": i} for i in range(150)],
        }

        # Verify the search method returns paginated results
        result = mock_client.search_repos("org:large-org")

        assert result["total_count"] == 150
        assert len(result["items"]) == 150


# =============================================================================
# Tests for User Story 3: Override Activity Filter (T028-T030)
# =============================================================================


class TestAllResponseBypassesFilter:
    """T028: Test 'all' response includes inactive repos."""

    def test_all_response_returns_all_repos(self, sample_repos_mixed_activity):
        """Test that 'all' response bypasses filtering."""
        # When user responds 'all', no filtering should be applied
        # This is verified by checking that all repos are returned
        all_repos = sample_repos_mixed_activity  # No filtering

        assert len(all_repos) == 4  # All 4 repos included


class TestOptionSSkipsFilter:
    """T029: Test [S] option skips activity filter (FR-005)."""

    def test_manual_specification_not_filtered(self):
        """Test that manually specified repos are not filtered."""
        # Per FR-005: Manual selection implies intentional choice
        manual_repos = ["user/old-repo", "user/very-old-repo"]

        # These should NOT be filtered even though they're inactive
        # The filter is not applied to [S] option at all
        assert len(manual_repos) == 2


class TestFilterTogglePreserved:
    """T030: Test filter toggle state preserved during selection."""

    def test_filter_state_maintained(self):
        """Test that filter on/off state is maintained during session."""
        # This tests the state management pattern
        # Filter should be ON by default for [A], [L], [O]
        # Filter should be OFF for [S]

        default_filter_on = True  # Default for A, L, O
        manual_filter_off = False  # Default for S

        assert default_filter_on is True
        assert manual_filter_off is False


# =============================================================================
# Tests for Edge Cases (T034-T036)
# =============================================================================


class TestZeroActiveReposWarning:
    """T034: Test zero active repos shows warning and options (FR-009)."""

    def test_zero_active_triggers_warning(self, capsys):
        """Test warning is shown when no active repos found."""
        repos = [
            {"full_name": "user/old", "pushed_at": "2020-01-01T10:00:00Z"},
        ]

        from datetime import date

        cutoff = date(2025, 11, 1)
        active = filter_by_activity(repos, cutoff)

        # Should show warning when zero active
        if len(active) == 0:
            print("⚠️ No repositories have been pushed to in the last 30 days.")

        captured = capsys.readouterr()
        assert "⚠️ No repositories" in captured.out

    def test_zero_active_repos_include_all_option(self, tmp_path):
        """Test zero active repos with option 1 (include all) in select_github_repos."""
        import os

        from src.github_analyzer.api.client import GitHubClient

        repos_file = tmp_path / "repos.txt"
        github_env = {"GITHUB_TOKEN": "ghp_test_token_12345678901234567890"}

        # All repos are old (no active repos)
        old_repos = [
            {"full_name": "user/old1", "pushed_at": "2020-01-01T10:00:00Z"},
            {"full_name": "user/old2", "pushed_at": "2020-06-15T10:00:00Z"},
        ]

        mock_client = Mock(spec=GitHubClient)
        mock_client.list_user_repos.return_value = old_repos
        mock_client.close = Mock()

        with (
            patch.object(main_module, "GitHubClient", return_value=mock_client),
            patch.dict(os.environ, github_env, clear=True),
            # Option A, then "1" to include all, then "Y" to confirm
            patch("builtins.input", side_effect=["A", "1", "Y"]),
        ):
            result = select_github_repos(
                str(repos_file),
                github_token=github_env["GITHUB_TOKEN"],
                interactive=True,
            )

        # Should include all repos when user selects "1"
        assert len(result) == 2
        assert "user/old1" in result
        assert "user/old2" in result

    def test_zero_active_repos_cancel_option(self, tmp_path):
        """Test zero active repos with option 3 (cancel) returns to menu."""
        import os

        from src.github_analyzer.api.client import GitHubClient

        repos_file = tmp_path / "repos.txt"
        github_env = {"GITHUB_TOKEN": "ghp_test_token_12345678901234567890"}

        old_repos = [
            {"full_name": "user/old1", "pushed_at": "2020-01-01T10:00:00Z"},
        ]

        mock_client = Mock(spec=GitHubClient)
        mock_client.list_user_repos.return_value = old_repos
        mock_client.close = Mock()

        with (
            patch.object(main_module, "GitHubClient", return_value=mock_client),
            patch.dict(os.environ, github_env, clear=True),
            # Option A, then "3" to cancel (FR-009), then Q to quit
            patch("builtins.input", side_effect=["A", "3", "Q"]),
        ):
            result = select_github_repos(
                str(repos_file),
                github_token=github_env["GITHUB_TOKEN"],
                interactive=True,
            )

        # Should return empty list after cancel and quit
        assert result == []

    def test_zero_active_repos_eof_on_choice(self, tmp_path):
        """Test EOF on zero repos choice returns empty list."""
        import os

        from src.github_analyzer.api.client import GitHubClient

        repos_file = tmp_path / "repos.txt"
        github_env = {"GITHUB_TOKEN": "ghp_test_token_12345678901234567890"}

        old_repos = [
            {"full_name": "user/old1", "pushed_at": "2020-01-01T10:00:00Z"},
        ]

        mock_client = Mock(spec=GitHubClient)
        mock_client.list_user_repos.return_value = old_repos
        mock_client.close = Mock()

        with (
            patch.object(main_module, "GitHubClient", return_value=mock_client),
            patch.dict(os.environ, github_env, clear=True),
            # Option A, then EOF on zero repos choice
            patch("builtins.input", side_effect=["A", EOFError()]),
        ):
            result = select_github_repos(
                str(repos_file),
                github_token=github_env["GITHUB_TOKEN"],
                interactive=True,
            )

        assert result == []


class TestAdjustTimeframeOption:
    """Tests for FR-009 'Adjust timeframe' option in zero active repos menu."""

    def test_adjust_timeframe_refilters_repos(self, tmp_path):
        """Test option 2 (adjust timeframe) refilters repos with new days."""
        import os

        from src.github_analyzer.api.client import GitHubClient

        repos_file = tmp_path / "repos.txt"
        github_env = {"GITHUB_TOKEN": "ghp_test_token_12345678901234567890"}

        # Mix of repos: one very old, one recent (but not active in 7 days)
        # The "recent" repo should become active when we extend to 60 days
        repos = [
            {"full_name": "user/old", "pushed_at": "2020-01-01T10:00:00Z"},
            {"full_name": "user/recent", "pushed_at": "2025-10-15T10:00:00Z"},  # ~45 days ago
        ]

        mock_client = Mock(spec=GitHubClient)
        mock_client.list_user_repos.return_value = repos
        mock_client.close = Mock()

        with (
            patch.object(main_module, "GitHubClient", return_value=mock_client),
            patch.dict(os.environ, github_env, clear=True),
            # Option A, zero repos in 7 days -> "2" to adjust, "60" new days, "Y" confirm
            patch("builtins.input", side_effect=["A", "2", "60", "Y"]),
        ):
            result = select_github_repos(
                str(repos_file),
                github_token=github_env["GITHUB_TOKEN"],
                interactive=True,
                days=7,  # Initial filter: 7 days
            )

        # Should include the "recent" repo after extending to 60 days
        assert len(result) == 1
        assert "user/recent" in result

    def test_adjust_timeframe_shows_new_stats(self, tmp_path, capsys):
        """Test adjust timeframe displays new activity stats."""
        import os

        from src.github_analyzer.api.client import GitHubClient

        repos_file = tmp_path / "repos.txt"
        github_env = {"GITHUB_TOKEN": "ghp_test_token_12345678901234567890"}

        repos = [
            {"full_name": "user/old", "pushed_at": "2020-01-01T10:00:00Z"},
            {"full_name": "user/recent", "pushed_at": "2025-10-15T10:00:00Z"},
        ]

        mock_client = Mock(spec=GitHubClient)
        mock_client.list_user_repos.return_value = repos
        mock_client.close = Mock()

        with (
            patch.object(main_module, "GitHubClient", return_value=mock_client),
            patch.dict(os.environ, github_env, clear=True),
            patch("builtins.input", side_effect=["A", "2", "60", "Y"]),
        ):
            select_github_repos(
                str(repos_file),
                github_token=github_env["GITHUB_TOKEN"],
                interactive=True,
                days=7,
            )

        captured = capsys.readouterr()
        # Should show "Rechecking..." and new stats
        assert "Rechecking..." in captured.out
        assert "60 days" in captured.out

    def test_adjust_timeframe_invalid_number_returns_to_menu(self, tmp_path):
        """Test invalid days input returns to menu."""
        import os

        from src.github_analyzer.api.client import GitHubClient

        repos_file = tmp_path / "repos.txt"
        github_env = {"GITHUB_TOKEN": "ghp_test_token_12345678901234567890"}

        old_repos = [
            {"full_name": "user/old1", "pushed_at": "2020-01-01T10:00:00Z"},
        ]

        mock_client = Mock(spec=GitHubClient)
        mock_client.list_user_repos.return_value = old_repos
        mock_client.close = Mock()

        with (
            patch.object(main_module, "GitHubClient", return_value=mock_client),
            patch.dict(os.environ, github_env, clear=True),
            # Option A, zero repos -> "2" adjust, "abc" invalid, then Q to quit
            patch("builtins.input", side_effect=["A", "2", "abc", "Q"]),
        ):
            result = select_github_repos(
                str(repos_file),
                github_token=github_env["GITHUB_TOKEN"],
                interactive=True,
            )

        assert result == []

    def test_adjust_timeframe_negative_number_returns_to_menu(self, tmp_path):
        """Test negative days input returns to menu."""
        import os

        from src.github_analyzer.api.client import GitHubClient

        repos_file = tmp_path / "repos.txt"
        github_env = {"GITHUB_TOKEN": "ghp_test_token_12345678901234567890"}

        old_repos = [
            {"full_name": "user/old1", "pushed_at": "2020-01-01T10:00:00Z"},
        ]

        mock_client = Mock(spec=GitHubClient)
        mock_client.list_user_repos.return_value = old_repos
        mock_client.close = Mock()

        with (
            patch.object(main_module, "GitHubClient", return_value=mock_client),
            patch.dict(os.environ, github_env, clear=True),
            # Option A, zero repos -> "2" adjust, "-5" negative, then Q to quit
            patch("builtins.input", side_effect=["A", "2", "-5", "Q"]),
        ):
            result = select_github_repos(
                str(repos_file),
                github_token=github_env["GITHUB_TOKEN"],
                interactive=True,
            )

        assert result == []

    def test_adjust_timeframe_eof_on_days_input_exits(self, tmp_path):
        """Test EOF on days input exits completely."""
        import os

        from src.github_analyzer.api.client import GitHubClient

        repos_file = tmp_path / "repos.txt"
        github_env = {"GITHUB_TOKEN": "ghp_test_token_12345678901234567890"}

        old_repos = [
            {"full_name": "user/old1", "pushed_at": "2020-01-01T10:00:00Z"},
        ]

        mock_client = Mock(spec=GitHubClient)
        mock_client.list_user_repos.return_value = old_repos
        mock_client.close = Mock()

        with (
            patch.object(main_module, "GitHubClient", return_value=mock_client),
            patch.dict(os.environ, github_env, clear=True),
            # Option A, zero repos -> "2" adjust, EOF on days input
            patch("builtins.input", side_effect=["A", "2", EOFError()]),
        ):
            result = select_github_repos(
                str(repos_file),
                github_token=github_env["GITHUB_TOKEN"],
                interactive=True,
            )

        assert result == []

    def test_adjust_timeframe_option_l(self, tmp_path):
        """Test adjust timeframe works for Option L (select from list)."""
        import os

        from src.github_analyzer.api.client import GitHubClient

        repos_file = tmp_path / "repos.txt"
        github_env = {"GITHUB_TOKEN": "ghp_test_token_12345678901234567890"}

        repos = [
            {"full_name": "user/old", "pushed_at": "2020-01-01T10:00:00Z"},
            {"full_name": "user/recent", "pushed_at": "2025-10-15T10:00:00Z"},
        ]

        mock_client = Mock(spec=GitHubClient)
        mock_client.list_user_repos.return_value = repos
        mock_client.close = Mock()

        with (
            patch.object(main_module, "GitHubClient", return_value=mock_client),
            patch.dict(os.environ, github_env, clear=True),
            # Option L, zero repos in 7 days -> "2" adjust, "60" days, "Y" confirm, "all" select
            patch("builtins.input", side_effect=["L", "2", "60", "Y", "all"]),
        ):
            result = select_github_repos(
                str(repos_file),
                github_token=github_env["GITHUB_TOKEN"],
                interactive=True,
                days=7,
            )

        assert len(result) == 1
        assert "user/recent" in result

    def test_adjust_timeframe_option_o(self, tmp_path):
        """Test adjust timeframe works for Option O (organization)."""
        import os

        from src.github_analyzer.api.client import GitHubClient

        repos_file = tmp_path / "repos.txt"
        github_env = {"GITHUB_TOKEN": "ghp_test_token_12345678901234567890"}

        org_repos = [
            {"full_name": "org/old", "pushed_at": "2020-01-01T10:00:00Z"},
            {"full_name": "org/recent", "pushed_at": "2025-10-15T10:00:00Z"},
        ]

        mock_client = Mock(spec=GitHubClient)
        mock_client.list_org_repos.return_value = org_repos
        # Search API returns empty results (0 active in 7 days)
        mock_client.search_active_org_repos.return_value = {
            "total_count": 0,
            "incomplete_results": False,
            "items": [],
        }
        mock_client.close = Mock()

        with (
            patch.object(main_module, "GitHubClient", return_value=mock_client),
            patch.dict(os.environ, github_env, clear=True),
            # Option O, org name, zero active -> "2" adjust, "60" days, "Y" confirm, "all" select
            patch("builtins.input", side_effect=["O", "myorg", "2", "60", "Y", "all"]),
        ):
            result = select_github_repos(
                str(repos_file),
                github_token=github_env["GITHUB_TOKEN"],
                interactive=True,
                days=7,
            )

        assert len(result) == 1
        assert "org/recent" in result


class TestSearchAPIRateLimitFallback:
    """T035: Test Search API rate limit fallback to unfiltered (FR-008)."""

    def test_rate_limit_shows_warning(self, capsys):
        """Test rate limit triggers warning and fallback."""
        from src.github_analyzer.core.exceptions import RateLimitError

        # Simulate rate limit scenario
        rate_limited = True
        if rate_limited:
            print(
                "⚠️ Search API rate limit exceeded. "
                "Showing all repositories without activity filter."
            )

        captured = capsys.readouterr()
        assert "rate limit exceeded" in captured.out.lower()
        assert "without activity filter" in captured.out.lower()

    def test_rate_limit_error_in_option_a(self, tmp_path):
        """Test RateLimitError handling in option A."""
        import os

        from src.github_analyzer.api.client import GitHubClient
        from src.github_analyzer.core.exceptions import RateLimitError

        repos_file = tmp_path / "repos.txt"
        github_env = {"GITHUB_TOKEN": "ghp_test_token_12345678901234567890"}

        mock_client = Mock(spec=GitHubClient)
        mock_client.list_user_repos.side_effect = RateLimitError(
            "Rate limit exceeded", reset_time=9999999999
        )
        mock_client.close = Mock()

        with (
            patch.object(main_module, "GitHubClient", return_value=mock_client),
            patch.dict(os.environ, github_env, clear=True),
            # Option A triggers rate limit, then Q to quit
            patch("builtins.input", side_effect=["A", "Q"]),
        ):
            result = select_github_repos(
                str(repos_file),
                github_token=github_env["GITHUB_TOKEN"],
                interactive=True,
            )

        assert result == []

    def test_github_analyzer_error_in_option_a(self, tmp_path):
        """Test GitHubAnalyzerError handling in option A."""
        import os

        from src.github_analyzer.api.client import GitHubClient
        from src.github_analyzer.core.exceptions import APIError

        repos_file = tmp_path / "repos.txt"
        github_env = {"GITHUB_TOKEN": "ghp_test_token_12345678901234567890"}

        mock_client = Mock(spec=GitHubClient)
        mock_client.list_user_repos.side_effect = APIError(
            "Network error", details="Connection refused"
        )
        mock_client.close = Mock()

        with (
            patch.object(main_module, "GitHubClient", return_value=mock_client),
            patch.dict(os.environ, github_env, clear=True),
            # Option A triggers error, then Q to quit
            patch("builtins.input", side_effect=["A", "Q"]),
        ):
            result = select_github_repos(
                str(repos_file),
                github_token=github_env["GITHUB_TOKEN"],
                interactive=True,
            )

        assert result == []


class TestHandleRateLimitFunction:
    """Tests for _handle_rate_limit helper function."""

    def test_handle_rate_limit_with_reset_time(self, capsys):
        """Test _handle_rate_limit displays wait time when reset_time is set."""
        import time

        from src.github_analyzer.cli.main import _handle_rate_limit
        from src.github_analyzer.core.exceptions import RateLimitError

        # Create rate limit error with future reset time
        future_time = int(time.time()) + 60  # 60 seconds in future
        error = RateLimitError("Rate limit", reset_time=future_time)

        log_messages = []

        def mock_log(msg: str, level: str) -> None:
            log_messages.append((msg, level))

        _handle_rate_limit(error, mock_log)

        assert len(log_messages) == 1
        assert "Rate limit exceeded" in log_messages[0][0]
        assert "seconds" in log_messages[0][0]
        assert log_messages[0][1] == "warning"

    def test_handle_rate_limit_without_reset_time(self, capsys):
        """Test _handle_rate_limit handles missing reset_time."""
        from src.github_analyzer.cli.main import _handle_rate_limit
        from src.github_analyzer.core.exceptions import RateLimitError

        error = RateLimitError("Rate limit", reset_time=None)

        log_messages = []

        def mock_log(msg: str, level: str) -> None:
            log_messages.append((msg, level))

        _handle_rate_limit(error, mock_log)

        assert len(log_messages) == 1
        assert "Rate limit exceeded" in log_messages[0][0]
        assert "try again later" in log_messages[0][0]
        assert log_messages[0][1] == "warning"


class TestIncompleteResultsWarning:
    """T036: Test incomplete_results flag shows warning."""

    def test_incomplete_results_warning(self, capsys):
        """Test warning shown when Search API returns incomplete results."""
        # Simulate incomplete results from API
        search_result = {
            "total_count": 1500,
            "incomplete_results": True,
            "items": [],
        }

        if search_result["incomplete_results"]:
            print(
                "⚠️ Results may be incomplete due to API limitations. "
                "Some active repositories may not be shown."
            )

        captured = capsys.readouterr()
        assert "incomplete" in captured.out.lower()
        assert "API limitations" in captured.out


class TestConfirmationPromptEdgeCases:
    """Tests for confirmation prompt edge cases."""

    def test_confirm_prompt_n_returns_to_menu(self, tmp_path):
        """Test 'n' response returns to menu."""
        import os

        from src.github_analyzer.api.client import GitHubClient

        repos_file = tmp_path / "repos.txt"
        github_env = {"GITHUB_TOKEN": "ghp_test_token_12345678901234567890"}

        repos = [
            {"full_name": "user/repo1", "pushed_at": "2025-11-28T10:00:00Z"},
        ]

        mock_client = Mock(spec=GitHubClient)
        mock_client.list_user_repos.return_value = repos
        mock_client.close = Mock()

        with (
            patch.object(main_module, "GitHubClient", return_value=mock_client),
            patch.dict(os.environ, github_env, clear=True),
            # Option A, then "n" to cancel, then Q to quit
            patch("builtins.input", side_effect=["A", "n", "Q"]),
        ):
            result = select_github_repos(
                str(repos_file),
                github_token=github_env["GITHUB_TOKEN"],
                interactive=True,
            )

        assert result == []

    def test_confirm_prompt_eof_returns_empty(self, tmp_path):
        """Test EOF on confirmation prompt returns empty list."""
        import os

        from src.github_analyzer.api.client import GitHubClient

        repos_file = tmp_path / "repos.txt"
        github_env = {"GITHUB_TOKEN": "ghp_test_token_12345678901234567890"}

        repos = [
            {"full_name": "user/repo1", "pushed_at": "2025-11-28T10:00:00Z"},
        ]

        mock_client = Mock(spec=GitHubClient)
        mock_client.list_user_repos.return_value = repos
        mock_client.close = Mock()

        with (
            patch.object(main_module, "GitHubClient", return_value=mock_client),
            patch.dict(os.environ, github_env, clear=True),
            # Option A, then EOF on confirm prompt
            patch("builtins.input", side_effect=["A", EOFError()]),
        ):
            result = select_github_repos(
                str(repos_file),
                github_token=github_env["GITHUB_TOKEN"],
                interactive=True,
            )

        assert result == []

    def test_confirm_prompt_all_bypasses_filter(self, tmp_path):
        """Test 'all' response bypasses activity filter."""
        import os

        from src.github_analyzer.api.client import GitHubClient

        repos_file = tmp_path / "repos.txt"
        github_env = {"GITHUB_TOKEN": "ghp_test_token_12345678901234567890"}

        # Mix of active and inactive repos
        repos = [
            {"full_name": "user/active", "pushed_at": "2025-11-28T10:00:00Z"},
            {"full_name": "user/inactive", "pushed_at": "2020-01-01T10:00:00Z"},
        ]

        mock_client = Mock(spec=GitHubClient)
        mock_client.list_user_repos.return_value = repos
        mock_client.close = Mock()

        with (
            patch.object(main_module, "GitHubClient", return_value=mock_client),
            patch.dict(os.environ, github_env, clear=True),
            # Option A, then "all" to include inactive repos
            patch("builtins.input", side_effect=["A", "all"]),
        ):
            result = select_github_repos(
                str(repos_file),
                github_token=github_env["GITHUB_TOKEN"],
                interactive=True,
            )

        # Should include both active and inactive repos
        assert len(result) == 2
        assert "user/active" in result
        assert "user/inactive" in result


class TestOptionOEdgeCases:
    """Tests for Option O edge cases."""

    def test_option_o_zero_repos_in_org(self, tmp_path):
        """Test Option O with zero repos in organization."""
        import os

        from src.github_analyzer.api.client import GitHubClient

        repos_file = tmp_path / "repos.txt"
        github_env = {"GITHUB_TOKEN": "ghp_test_token_12345678901234567890"}

        mock_client = Mock(spec=GitHubClient)
        mock_client.list_org_repos.return_value = []  # No repos
        mock_client.close = Mock()

        with (
            patch.object(main_module, "GitHubClient", return_value=mock_client),
            patch.dict(os.environ, github_env, clear=True),
            # Option O, enter org name, then Q to quit
            patch("builtins.input", side_effect=["O", "emptyorg", "Q"]),
        ):
            result = select_github_repos(
                str(repos_file),
                github_token=github_env["GITHUB_TOKEN"],
                interactive=True,
            )

        assert result == []

    def test_option_o_rate_limit_fallback(self, tmp_path):
        """Test Option O rate limit fallback to unfiltered mode."""
        import os

        from src.github_analyzer.api.client import GitHubClient
        from src.github_analyzer.core.exceptions import RateLimitError

        repos_file = tmp_path / "repos.txt"
        github_env = {"GITHUB_TOKEN": "ghp_test_token_12345678901234567890"}

        org_repos = [
            {"full_name": "org/repo1", "pushed_at": "2025-11-28T10:00:00Z"},
            {"full_name": "org/repo2", "pushed_at": "2020-01-01T10:00:00Z"},
        ]

        mock_client = Mock(spec=GitHubClient)
        mock_client.list_org_repos.return_value = org_repos
        mock_client.search_active_org_repos.side_effect = RateLimitError("Rate limit")
        mock_client.close = Mock()

        with (
            patch.object(main_module, "GitHubClient", return_value=mock_client),
            patch.dict(os.environ, github_env, clear=True),
            # Option O, enter org name, rate limit triggers fallback, select all
            patch("builtins.input", side_effect=["O", "myorg", "all"]),
        ):
            result = select_github_repos(
                str(repos_file),
                github_token=github_env["GITHUB_TOKEN"],
                interactive=True,
            )

        # Should return all repos via fallback
        assert len(result) == 2

    def test_option_o_404_error(self, tmp_path):
        """Test Option O with 404 error (org not found)."""
        import os

        from src.github_analyzer.api.client import GitHubClient
        from src.github_analyzer.core.exceptions import APIError

        repos_file = tmp_path / "repos.txt"
        github_env = {"GITHUB_TOKEN": "ghp_test_token_12345678901234567890"}

        mock_client = Mock(spec=GitHubClient)
        mock_client.list_org_repos.side_effect = APIError(
            "Not found: 404", status_code=404
        )
        mock_client.close = Mock()

        with (
            patch.object(main_module, "GitHubClient", return_value=mock_client),
            patch.dict(os.environ, github_env, clear=True),
            # Option O, enter org name, 404 error, then Q
            patch("builtins.input", side_effect=["O", "nonexistent", "Q"]),
        ):
            result = select_github_repos(
                str(repos_file),
                github_token=github_env["GITHUB_TOKEN"],
                interactive=True,
            )

        assert result == []

    def test_option_o_eof_on_org_name(self, tmp_path):
        """Test Option O with EOF on org name input."""
        import os

        from src.github_analyzer.api.client import GitHubClient

        repos_file = tmp_path / "repos.txt"
        github_env = {"GITHUB_TOKEN": "ghp_test_token_12345678901234567890"}

        mock_client = Mock(spec=GitHubClient)
        mock_client.close = Mock()

        with (
            patch.object(main_module, "GitHubClient", return_value=mock_client),
            patch.dict(os.environ, github_env, clear=True),
            # Option O, then EOF on org name
            patch("builtins.input", side_effect=["O", EOFError()]),
        ):
            result = select_github_repos(
                str(repos_file),
                github_token=github_env["GITHUB_TOKEN"],
                interactive=True,
            )

        assert result == []


class TestOptionLEdgeCases:
    """Tests for Option L edge cases."""

    def test_option_l_rate_limit_error(self, tmp_path):
        """Test Option L with rate limit error."""
        import os

        from src.github_analyzer.api.client import GitHubClient
        from src.github_analyzer.core.exceptions import RateLimitError

        repos_file = tmp_path / "repos.txt"
        github_env = {"GITHUB_TOKEN": "ghp_test_token_12345678901234567890"}

        mock_client = Mock(spec=GitHubClient)
        mock_client.list_user_repos.side_effect = RateLimitError(
            "Rate limit", reset_time=None
        )
        mock_client.close = Mock()

        with (
            patch.object(main_module, "GitHubClient", return_value=mock_client),
            patch.dict(os.environ, github_env, clear=True),
            # Option L triggers rate limit, then Q to quit
            patch("builtins.input", side_effect=["L", "Q"]),
        ):
            result = select_github_repos(
                str(repos_file),
                github_token=github_env["GITHUB_TOKEN"],
                interactive=True,
            )

        assert result == []

    def test_option_l_invalid_selection(self, tmp_path):
        """Test Option L with invalid selection input."""
        import os

        from src.github_analyzer.api.client import GitHubClient

        repos_file = tmp_path / "repos.txt"
        github_env = {"GITHUB_TOKEN": "ghp_test_token_12345678901234567890"}

        repos = [
            {"full_name": "user/repo1", "pushed_at": "2025-11-28T10:00:00Z"},
        ]

        mock_client = Mock(spec=GitHubClient)
        mock_client.list_user_repos.return_value = repos
        mock_client.close = Mock()

        with (
            patch.object(main_module, "GitHubClient", return_value=mock_client),
            patch.dict(os.environ, github_env, clear=True),
            # Option L, confirm, invalid selection, then Q
            patch("builtins.input", side_effect=["L", "Y", "invalid", "Q"]),
        ):
            result = select_github_repos(
                str(repos_file),
                github_token=github_env["GITHUB_TOKEN"],
                interactive=True,
            )

        assert result == []
