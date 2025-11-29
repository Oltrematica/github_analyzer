# Quickstart: Frontend Report Generator

**Feature**: 007-frontend-report-generator
**Date**: 2025-11-29

## Prerequisites

1. **Python 3.9+** installato
2. **Export CSV** generati da github_analyzer e jira_client
3. **Perplexity API key** (opzionale, per analisi AI)

## Setup Rapido

### 1. Installa dipendenze

```bash
# Dal root del progetto
pip install -r requirements.txt
pip install pyyaml  # Per configurazione user mapping
```

### 2. Configura variabili d'ambiente

```bash
# Obbligatorie (già configurate se usi github_analyzer)
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"

# Opzionali
export PERPLEXITY_API_KEY="pplx-xxxxxxxxxxxxxxxxxxxxxxxx"  # Per AI insights
```

### 3. Genera i dati di input

```bash
# Genera export GitHub (se non già fatto)
python github_analyzer.py --days 30

# Genera export Jira (se non già fatto)
python -m src.github_analyzer.api.jira_client --days 30
```

### 4. Genera il report

```bash
# Report base (senza AI)
python -m src.github_analyzer.report_generator --period 30 --no-ai

# Report completo (con AI)
python -m src.github_analyzer.report_generator --period 30

# Con output directory specifica
python -m src.github_analyzer.report_generator --period 30 --output ./my-reports/
```

### 5. Visualizza il report

```bash
# Apri nel browser
open frontend/reports/latest/index.html  # macOS
xdg-open frontend/reports/latest/index.html  # Linux
start frontend/reports/latest/index.html  # Windows
```

## Primo Utilizzo: User Mapping

Al primo utilizzo, il sistema chiederà di associare gli utenti Jira con GitHub:

```
═══════════════════════════════════════════════════════════════════
              USER MAPPING - RICONCILIAZIONE UTENTI
═══════════════════════════════════════════════════════════════════

Trovati 8 utenti Jira e 12 utenti GitHub.
Mapping automatico: 5 confermati, 3 da verificare.

─────────────────────────────────────────────────────────────────────
[1/3] Jira: "setek" (1 task)
─────────────────────────────────────────────────────────────────────
Candidati GitHub trovati:
  [1] setek-user     (confidenza: 85%) - 3 commits, 2 PRs
  [2] setekdev       (confidenza: 72%) - 15 commits, 8 PRs
  [N] Nuovo - inserisci username manualmente
  [S] Skip - ignora questo utente

Scelta [1-2/N/S]: 2

✓ Mapping salvato: setek (Jira) → setekdev (GitHub)
```

Il mapping viene salvato in `frontend/config/user_mapping.yaml` e riutilizzato automaticamente.

## Comandi Frequenti

```bash
# Report ultimi 7 giorni
python -m src.github_analyzer.report_generator --period 7

# Solo dati GitHub (no Jira)
python -m src.github_analyzer.report_generator --sources github

# Usa mapping esistente senza prompt
python -m src.github_analyzer.report_generator --user-mapping frontend/config/user_mapping.yaml

# Report con configurazione custom
python -m src.github_analyzer.report_generator --config frontend/config/report_config.yaml
```

## Struttura Output

```
frontend/reports/2025-11-29/
├── index.html          # Report principale (aprilo nel browser)
├── data.json           # Dati raw (per debug/export)
└── ai_insights.json    # Cache analisi AI
```

## Troubleshooting

### "Missing CSV files"

Assicurati di aver generato gli export:
```bash
python github_analyzer.py --days 30
python -m src.github_analyzer.api.jira_client --days 30
```

### "PERPLEXITY_API_KEY not set"

Le sezioni AI verranno omesse. Per abilitarle:
```bash
export PERPLEXITY_API_KEY="pplx-your-key-here"
```

### "Rate limit exceeded"

Il sistema ti chiederà cosa fare:
- `W` per attendere e riprovare
- `S` per proseguire senza AI

### Report vuoto o incompleto

Verifica che il periodo contenga dati:
```bash
python -m src.github_analyzer.report_generator --period 90  # Prova periodo più lungo
```

## Prossimi Passi

- Personalizza `frontend/config/report_config.yaml` per sezioni e stile
- Modifica `frontend/config/user_mapping.yaml` per correggere associazioni
- Integra in CI/CD per report automatici
