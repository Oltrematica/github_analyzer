# github_analyzer Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-11-28

## Active Technologies

- Python 3.9+ (as per constitution, leveraging type hints) + Standard library only (urllib, json, csv, os, re); optional: requests (001-modular-refactor)

## Project Structure

```text
src/
tests/
```

## Commands

```bash
# Run tests
pytest tests/ -v

# Run tests with coverage
pytest --cov=src/github_analyzer --cov-report=term-missing

# Run linter
ruff check src/github_analyzer/

# Run the analyzer
python github_analyzer.py --days 7
```

## Code Style

Python 3.9+ (as per constitution, leveraging type hints): Follow standard conventions

## Recent Changes

- 001-modular-refactor: Added Python 3.9+ (as per constitution, leveraging type hints) + Standard library only (urllib, json, csv, os, re); optional: requests

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
