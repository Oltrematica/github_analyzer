"""Config module - Configuration and validation.

Public exports:
- AnalyzerConfig: Main configuration dataclass
- Repository: Validated repository identifier
- load_repositories: Load repos from file
- validate_token_format: Check token format
"""

from src.github_analyzer.config.settings import AnalyzerConfig
from src.github_analyzer.config.validation import (
    Repository,
    load_repositories,
    validate_token_format,
)

__all__ = [
    "AnalyzerConfig",
    "Repository",
    "load_repositories",
    "validate_token_format",
]
