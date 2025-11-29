# Implementation Plan: Frontend Report Generator

**Branch**: `007-frontend-report-generator` | **Date**: 2025-11-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-frontend-report-generator/spec.md`

## Summary

Sistema di generazione automatica di report HTML interattivi per l'analisi delle performance del team di sviluppo. Aggrega dati da export CSV GitHub e Jira, implementa mapping utenti cross-platform con auto-matching fuzzy, integra Perplexity AI per insights qualitativi, e genera report standalone con visualizzazioni Chart.js responsive.

## Technical Context

**Language/Version**: Python 3.9+ (come da constitution, leveraging type hints)
**Primary Dependencies**:
- Standard library: csv, json, pathlib, re, datetime, statistics, difflib (fuzzy matching)
- Optional: requests (già presente), PyYAML (per user mapping config)
- Frontend: Chart.js 4.x (CDN inline), vanilla CSS/JS

**Storage**:
- Input: CSV files (export esistenti GitHub/Jira)
- Output: HTML standalone, JSON (data.json, ai_insights.json)
- Config: YAML (user_mapping.yaml)

**Testing**: pytest (già configurato nel progetto)
**Target Platform**: CLI Python, output HTML per browser moderni
**Project Type**: Single project (estensione di github_analyzer esistente)
**Performance Goals**: <2 min generazione per 30 membri/12 mesi (escluso AI), <3s caricamento HTML
**Constraints**: HTML <2MB, minimo 320px larghezza, no dipendenze esterne nell'HTML output
**Scale/Scope**: Max 30 team members, 12 mesi storico dati

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Modular Architecture | ✅ PASS | Nuovo modulo `report_generator/` con sottmoduli separati (data_aggregator, user_mapping, ai_client, html_generator) |
| II. Security First | ✅ PASS | Token Perplexity via env var, validazione path output (riuso security.py), escape HTML |
| III. Test-Driven Development | ✅ PASS | Test per ogni modulo, mock per Perplexity API |
| IV. Configuration over Hardcoding | ✅ PASS | Config YAML per report, CLI args per parametri runtime |
| V. Graceful Error Handling | ✅ PASS | Partial failures (file mancanti), AI fallback con prompt interattivo |

**Gate Status**: ✅ ALL PASS - Proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/007-frontend-report-generator/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── perplexity-api.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/github_analyzer/
├── report_generator/           # NEW: Report generation module
│   ├── __init__.py
│   ├── cli.py                  # CLI entry point (--period, --output, etc.)
│   ├── data_aggregator.py      # CSV parsing and metrics aggregation
│   ├── user_mapping.py         # Jira↔GitHub user reconciliation
│   ├── ai_client.py            # Perplexity API integration with cache
│   ├── html_generator.py       # Template rendering and HTML output
│   ├── models.py               # Data classes (TeamMember, ReportData, etc.)
│   └── templates/              # HTML template files
│       ├── report.html         # Main template
│       └── components/         # Reusable components
│           ├── header.html
│           ├── team_overview.html
│           ├── quality_metrics.html
│           ├── member_report.html
│           └── footer.html
│
├── api/                        # Existing
├── analyzers/                  # Existing
├── cli/                        # Existing (may add report subcommand)
├── config/                     # Existing
├── core/                       # Existing (riuso security.py)
└── exporters/                  # Existing

frontend/                       # NEW: Frontend assets and output
├── config/
│   ├── report_config.yaml      # Report configuration
│   └── user_mapping.yaml       # User mapping storage
├── assets/
│   ├── css/
│   │   └── report.css          # Compiled/inlined in output
│   └── js/
│       └── charts.js           # Chart.js configurations
└── reports/                    # Generated reports output
    └── latest/                 # Symlink to most recent

tests/
├── unit/
│   └── report_generator/
│       ├── test_data_aggregator.py
│       ├── test_user_mapping.py
│       ├── test_ai_client.py
│       └── test_html_generator.py
└── integration/
    └── test_report_generation.py
```

**Structure Decision**: Estensione del progetto esistente con nuovo modulo `report_generator/` seguendo la struttura modulare già in uso. Il frontend assets folder è separato per chiarezza ma l'output finale è HTML standalone.

## Complexity Tracking

> Nessuna violazione della constitution rilevata. Non sono necessarie giustificazioni.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| - | - | - |
