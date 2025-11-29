# Quickstart: Jira Quality Metrics Export

**Feature**: 003-jira-quality-metrics
**Date**: 2025-11-28

## Overview

This feature adds quality metrics to Jira exports. After implementation, running the analyzer will:

1. Export issues with 10 new calculated metric columns
2. Generate 3 new summary CSV files with aggregated metrics

## Prerequisites

- Python 3.9+
- Existing Jira integration configured (`JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`)
- `jira_projects.txt` file with project keys to analyze

## Usage

### Basic Export with Metrics

```bash
# Run analysis with default settings (last 7 days)
python github_analyzer.py --jira

# Run with custom date range
python github_analyzer.py --jira --days 30

# Specify output directory
python github_analyzer.py --jira --output ./reports
```

### Output Files

After running, you'll find in the output directory:

```
output/
├── jira_issues_export.csv        # Issues with quality metrics (extended)
├── jira_comments_export.csv      # Comments (unchanged)
├── jira_project_metrics.csv      # NEW: Project-level summary
├── jira_person_metrics.csv       # NEW: Per-person summary
└── jira_type_metrics.csv         # NEW: Per-type summary
```

## New Metrics Explained

### Issue-Level Metrics (per row in issues CSV)

| Metric | What it measures |
|--------|------------------|
| `cycle_time_days` | Days from creation to resolution |
| `aging_days` | Days since creation (open issues only) |
| `comments_count` | Total comments on issue |
| `description_quality_score` | 0-100 quality rating |
| `acceptance_criteria_present` | Whether AC detected |
| `comment_velocity_hours` | Hours until first comment |
| `silent_issue` | True if no comments |
| `same_day_resolution` | Resolved same day as created |
| `cross_team_score` | 0-100 collaboration rating |
| `reopen_count` | Times issue was reopened |

### Aggregated Metrics (summary CSVs)

**Project metrics** (`jira_project_metrics.csv`):
- Average and median cycle time
- Bug ratio
- Same-day resolution rate
- Description quality average
- Silent issues ratio
- Reopen rate

**Person metrics** (`jira_person_metrics.csv`):
- WIP (work in progress count)
- Resolved count
- Average cycle time
- Bugs assigned

**Type metrics** (`jira_type_metrics.csv`):
- Count per type
- Resolved count
- Average cycle time
- Bug resolution time (for Bugs only)

## Example: Identifying Problem Areas

### Find silent issues (no collaboration)

```bash
# Filter CSV for silent issues
grep ",true," output/jira_issues_export.csv | grep "silent_issue"
```

### Compare team workloads

```bash
# View person metrics sorted by WIP
sort -t',' -k2 -nr output/jira_person_metrics.csv
```

### Identify slow-resolving issue types

```bash
# View type metrics
cat output/jira_type_metrics.csv
```

## Configuration

Metric calculation can be customized via environment variables (optional):

```bash
# Quality score thresholds (defaults shown)
export JIRA_QUALITY_LENGTH_THRESHOLD=100  # Chars for full length score
export JIRA_QUALITY_WEIGHT_LENGTH=40      # Max points for length
export JIRA_QUALITY_WEIGHT_AC=40          # Points for AC presence
export JIRA_QUALITY_WEIGHT_FORMAT=20      # Max points for formatting
```

## Troubleshooting

### Reopen count always 0

The changelog API requires specific permissions. If reopen tracking doesn't work:
- Verify user has "Browse project" permission
- Check if Jira admin has enabled changelog access
- This is expected behavior for some Jira configurations

### Quality score seems off

The score uses heuristics:
- 40% for description length (100+ chars = full score)
- 40% for acceptance criteria patterns
- 20% for formatting (headers, lists)

Descriptions under 100 characters will have reduced scores.

### Missing assignee in person metrics

Issues without an assignee are excluded from person metrics. Check the issue export for `assignee` column.

## API Reference

### MetricsCalculator

```python
from github_analyzer.analyzers.jira_metrics import MetricsCalculator

calculator = MetricsCalculator()
issue_metrics = calculator.calculate_issue_metrics(issue, comments)
```

### MetricsExporter

```python
from github_analyzer.exporters.jira_metrics_exporter import MetricsExporter

exporter = MetricsExporter(output_dir="./output")
exporter.export_project_metrics(project_metrics_list)
exporter.export_person_metrics(person_metrics_list)
exporter.export_type_metrics(type_metrics_list)
```
