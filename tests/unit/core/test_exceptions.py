"""Tests for custom exceptions."""


from src.github_analyzer.core.exceptions import (
    APIError,
    ConfigurationError,
    GitHubAnalyzerError,
    RateLimitError,
    ValidationError,
    mask_token,
)


class TestGitHubAnalyzerError:
    """Tests for base GitHubAnalyzerError."""

    def test_creates_with_message(self):
        """Test creates error with message."""
        error = GitHubAnalyzerError("Test error")
        assert error.message == "Test error"
        assert error.details is None

    def test_creates_with_message_and_details(self):
        """Test creates error with message and details."""
        error = GitHubAnalyzerError("Test error", "More info")
        assert error.message == "Test error"
        assert error.details == "More info"

    def test_str_without_details(self):
        """Test string representation without details."""
        error = GitHubAnalyzerError("Test error")
        assert str(error) == "Test error"

    def test_str_with_details(self):
        """Test string representation with details."""
        error = GitHubAnalyzerError("Test error", "More info")
        assert str(error) == "Test error (More info)"

    def test_default_exit_code(self):
        """Test default exit code is 1."""
        error = GitHubAnalyzerError("Test error")
        assert error.exit_code == 1

    def test_is_exception(self):
        """Test inherits from Exception."""
        error = GitHubAnalyzerError("Test error")
        assert isinstance(error, Exception)


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_inherits_from_base(self):
        """Test inherits from GitHubAnalyzerError."""
        error = ConfigurationError("Config error")
        assert isinstance(error, GitHubAnalyzerError)

    def test_exit_code(self):
        """Test exit code is 1."""
        error = ConfigurationError("Config error")
        assert error.exit_code == 1

    def test_can_be_caught_as_base(self):
        """Test can be caught as base exception."""
        try:
            raise ConfigurationError("Test")
        except GitHubAnalyzerError as e:
            assert e.message == "Test"


class TestValidationError:
    """Tests for ValidationError."""

    def test_inherits_from_base(self):
        """Test inherits from GitHubAnalyzerError."""
        error = ValidationError("Validation error")
        assert isinstance(error, GitHubAnalyzerError)

    def test_exit_code(self):
        """Test exit code is 1."""
        error = ValidationError("Validation error")
        assert error.exit_code == 1


class TestAPIError:
    """Tests for APIError."""

    def test_inherits_from_base(self):
        """Test inherits from GitHubAnalyzerError."""
        error = APIError("API error")
        assert isinstance(error, GitHubAnalyzerError)

    def test_exit_code(self):
        """Test exit code is 2."""
        error = APIError("API error")
        assert error.exit_code == 2

    def test_creates_with_status_code(self):
        """Test creates with status code."""
        error = APIError("API error", status_code=404)
        assert error.status_code == 404

    def test_status_code_default_none(self):
        """Test status code defaults to None."""
        error = APIError("API error")
        assert error.status_code is None

    def test_creates_with_all_params(self):
        """Test creates with all parameters."""
        error = APIError("API error", "Details", 500)
        assert error.message == "API error"
        assert error.details == "Details"
        assert error.status_code == 500


class TestRateLimitError:
    """Tests for RateLimitError."""

    def test_inherits_from_api_error(self):
        """Test inherits from APIError."""
        error = RateLimitError()
        assert isinstance(error, APIError)

    def test_exit_code(self):
        """Test exit code is 2."""
        error = RateLimitError()
        assert error.exit_code == 2

    def test_default_message(self):
        """Test default message."""
        error = RateLimitError()
        assert "rate limit" in error.message.lower()

    def test_default_status_code(self):
        """Test default status code is 403."""
        error = RateLimitError()
        assert error.status_code == 403

    def test_creates_with_reset_time(self):
        """Test creates with reset time."""
        error = RateLimitError(reset_time=1234567890)
        assert error.reset_time == 1234567890

    def test_reset_time_default_none(self):
        """Test reset time defaults to None."""
        error = RateLimitError()
        assert error.reset_time is None

    def test_creates_with_custom_message(self):
        """Test creates with custom message."""
        error = RateLimitError("Custom message")
        assert error.message == "Custom message"


class TestMaskToken:
    """Tests for mask_token function."""

    def test_masks_token(self):
        """Test masks token value."""
        result = mask_token("ghp_secret_token_12345")
        assert result == "[MASKED]"

    def test_masks_any_value(self):
        """Test masks any string value."""
        result = mask_token("any_value")
        assert result == "[MASKED]"

    def test_masks_empty_string(self):
        """Test masks empty string."""
        result = mask_token("")
        assert result == "[MASKED]"

    def test_never_exposes_input(self):
        """Test never exposes any part of input."""
        token = "ghp_super_secret_token_value"
        result = mask_token(token)
        assert token not in result
        assert "ghp" not in result
        assert "secret" not in result
