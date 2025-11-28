"""Tests for CLI output formatting."""

import pytest
from io import StringIO
from unittest.mock import patch

from src.github_analyzer.cli.output import Colors, TerminalOutput


class TestColors:
    """Tests for Colors class."""

    def test_has_color_constants(self):
        """Test has color constants defined."""
        # Test some representative colors
        assert hasattr(Colors, 'RED')
        assert hasattr(Colors, 'GREEN')
        assert hasattr(Colors, 'BLUE')
        assert hasattr(Colors, 'CYAN')
        assert hasattr(Colors, 'YELLOW')
        assert hasattr(Colors, 'RESET')
        assert hasattr(Colors, 'BOLD')

    def test_disable_method(self):
        """Test disable method sets all to empty."""
        # Save originals
        original_red = Colors.RED
        original_reset = Colors.RESET

        try:
            Colors.disable()
            assert Colors.RED == ""
            assert Colors.GREEN == ""
            assert Colors.BLUE == ""
            assert Colors.RESET == ""
            assert Colors.BOLD == ""
        finally:
            # Restore for other tests
            Colors.RED = original_red
            Colors.RESET = original_reset


class TestTerminalOutputInit:
    """Tests for TerminalOutput initialization."""

    def test_initializes_with_default_verbose(self):
        """Test initializes with verbose=True by default."""
        output = TerminalOutput()
        assert output._verbose is True

    def test_initializes_with_verbose_false(self):
        """Test initializes with verbose=False."""
        output = TerminalOutput(verbose=False)
        assert output._verbose is False


class TestTerminalOutputBanner:
    """Tests for banner method."""

    def test_banner_prints_output(self, capsys):
        """Test banner prints something."""
        output = TerminalOutput()
        output.banner()

        captured = capsys.readouterr()
        # Should contain parts of the banner
        assert len(captured.out) > 0


class TestTerminalOutputFeatures:
    """Tests for features method."""

    def test_features_prints_list(self, capsys):
        """Test features prints feature list."""
        output = TerminalOutput()
        output.features()

        captured = capsys.readouterr()
        # Check for some expected content
        assert "Commit Analysis" in captured.out or "commit" in captured.out.lower()


class TestTerminalOutputLog:
    """Tests for log method."""

    def test_log_info_when_verbose(self, capsys):
        """Test log prints info when verbose."""
        output = TerminalOutput(verbose=True)
        output.log("Test message", level="info")

        captured = capsys.readouterr()
        assert "Test message" in captured.out

    def test_log_info_silent_when_not_verbose(self, capsys):
        """Test log suppresses info when not verbose."""
        output = TerminalOutput(verbose=False)
        output.log("Test message", level="info")

        captured = capsys.readouterr()
        assert captured.out == ""

    def test_log_error_always_prints(self, capsys):
        """Test log always prints error level."""
        output = TerminalOutput(verbose=False)
        output.log("Error message", level="error")

        captured = capsys.readouterr()
        assert "Error message" in captured.out

    def test_log_success_always_prints(self, capsys):
        """Test log always prints success level."""
        output = TerminalOutput(verbose=False)
        output.log("Success message", level="success")

        captured = capsys.readouterr()
        assert "Success message" in captured.out

    def test_log_warning_always_prints(self, capsys):
        """Test log always prints warning level."""
        output = TerminalOutput(verbose=False)
        output.log("Warning message", level="warning")

        captured = capsys.readouterr()
        assert "Warning message" in captured.out

    def test_log_without_timestamp(self, capsys):
        """Test log without timestamp."""
        output = TerminalOutput(verbose=True)
        output.log("Test message", level="info", timestamp=False)

        captured = capsys.readouterr()
        assert "Test message" in captured.out
        # No timestamp means no brackets with time
        # Just verify message appears


class TestTerminalOutputProgress:
    """Tests for progress method."""

    def test_progress_shows_percentage(self, capsys):
        """Test progress shows percentage."""
        output = TerminalOutput()
        output.progress(50, 100, "Processing")

        captured = capsys.readouterr()
        assert "50" in captured.out

    def test_progress_completes_at_100(self, capsys):
        """Test progress prints newline at completion."""
        output = TerminalOutput()
        output.progress(100, 100, "Done")

        captured = capsys.readouterr()
        assert captured.out.endswith("\n")

    def test_progress_handles_zero_total(self, capsys):
        """Test progress handles zero total gracefully."""
        output = TerminalOutput()
        # Should not raise
        output.progress(0, 0, "Empty")

        captured = capsys.readouterr()
        assert "0" in captured.out


class TestTerminalOutputSection:
    """Tests for section method."""

    def test_section_prints_title(self, capsys):
        """Test section prints title."""
        output = TerminalOutput()
        output.section("Test Section")

        captured = capsys.readouterr()
        assert "Test Section" in captured.out

    def test_section_includes_dividers(self, capsys):
        """Test section includes visual dividers."""
        output = TerminalOutput()
        output.section("Test")

        captured = capsys.readouterr()
        assert "═" in captured.out


class TestTerminalOutputSummary:
    """Tests for summary method."""

    def test_summary_prints_repositories(self, capsys):
        """Test summary prints repository count."""
        output = TerminalOutput()
        output.summary({"repositories": 5})

        captured = capsys.readouterr()
        assert "5" in captured.out
        assert "Repositories" in captured.out or "repositories" in captured.out.lower()

    def test_summary_prints_commits(self, capsys):
        """Test summary prints commit stats."""
        output = TerminalOutput()
        stats = {
            "commits": {
                "total": 100,
                "merge_commits": 10,
                "revert_commits": 5,
            }
        }
        output.summary(stats)

        captured = capsys.readouterr()
        assert "100" in captured.out

    def test_summary_prints_prs(self, capsys):
        """Test summary prints PR stats."""
        output = TerminalOutput()
        stats = {
            "prs": {
                "total": 20,
                "merged": 15,
                "open": 5,
            }
        }
        output.summary(stats)

        captured = capsys.readouterr()
        assert "20" in captured.out

    def test_summary_prints_issues(self, capsys):
        """Test summary prints issue stats."""
        output = TerminalOutput()
        stats = {
            "issues": {
                "total": 30,
                "closed": 25,
                "open": 5,
            }
        }
        output.summary(stats)

        captured = capsys.readouterr()
        assert "30" in captured.out

    def test_summary_prints_files(self, capsys):
        """Test summary prints generated files."""
        output = TerminalOutput()
        stats = {
            "files": [
                "/path/to/file1.csv",
                "/path/to/file2.csv",
            ]
        }
        output.summary(stats)

        captured = capsys.readouterr()
        assert "file1.csv" in captured.out
        assert "file2.csv" in captured.out


class TestTerminalOutputError:
    """Tests for error method."""

    def test_error_prints_message(self, capsys):
        """Test error prints message."""
        output = TerminalOutput()
        output.error("Something went wrong")

        captured = capsys.readouterr()
        assert "Something went wrong" in captured.out
        assert "Error" in captured.out or "❌" in captured.out

    def test_error_prints_details(self, capsys):
        """Test error prints details when provided."""
        output = TerminalOutput()
        output.error("Error occurred", "Additional info here")

        captured = capsys.readouterr()
        assert "Error occurred" in captured.out
        assert "Additional info here" in captured.out


class TestTerminalOutputSuccess:
    """Tests for success method."""

    def test_success_prints_message(self, capsys):
        """Test success prints message."""
        output = TerminalOutput()
        output.success("Operation completed!")

        captured = capsys.readouterr()
        assert "Operation completed!" in captured.out
        assert "✅" in captured.out
