# Frontend Report Generator

Sistema di generazione automatica di report interattivi per l'analisi delle performance del team, basato su dati GitHub e Jira con analisi AI tramite Perplexity.

## Indice

1. [Architettura del Sistema](#architettura-del-sistema)
2. [Fonti Dati](#fonti-dati)
3. [Integrazione Perplexity AI](#integrazione-perplexity-ai)
4. [User Mapping (Jira ↔ GitHub)](#user-mapping-jira--github)
5. [Struttura del Report](#struttura-del-report)
6. [Requisiti di Design](#requisiti-di-design)
7. [Configurazione](#configurazione)
8. [Workflow di Generazione](#workflow-di-generazione)
9. [API e Formati Dati](#api-e-formati-dati)

---

## Architettura del Sistema

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PIPELINE DI GENERAZIONE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────────┐   │
│  │   GitHub     │    │    Jira      │    │     User Mapping             │   │
│  │   Export     │    │   Export     │    │   (riconciliazione utenti)   │   │
│  │   (CSV)      │    │   (CSV)      │    │                              │   │
│  └──────┬───────┘    └──────┬───────┘    └──────────────┬───────────────┘   │
│         │                   │                           │                    │
│         └───────────────────┼───────────────────────────┘                    │
│                             │                                                │
│                             ▼                                                │
│                  ┌──────────────────────┐                                    │
│                  │   Data Aggregator    │                                    │
│                  │   (Python Script)    │                                    │
│                  └──────────┬───────────┘                                    │
│                             │                                                │
│         ┌───────────────────┼───────────────────┐                            │
│         │                   │                   │                            │
│         ▼                   ▼                   ▼                            │
│  ┌─────────────┐   ┌──────────────┐    ┌──────────────────┐                  │
│  │ Dati        │   │ Dati         │    │  Perplexity AI   │                  │
│  │ Deterministici │   │ Calcolati    │    │  (Analisi)       │                  │
│  │ (metriche)  │   │ (trend)      │    │                  │                  │
│  └──────┬──────┘   └──────┬───────┘    └────────┬─────────┘                  │
│         │                 │                     │                            │
│         └─────────────────┼─────────────────────┘                            │
│                           │                                                  │
│                           ▼                                                  │
│                ┌─────────────────────┐                                       │
│                │   Report Generator  │                                       │
│                │   (HTML/CSS/JS)     │                                       │
│                └─────────────────────┘                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Fonti Dati

### Dati GitHub (Deterministici)

I seguenti file CSV vengono generati dal `github_analyzer`:

| File | Descrizione | Campi Chiave |
|------|-------------|--------------|
| `commits_export.csv` | Tutti i commit dei repository | author, repo, date, message, additions, deletions |
| `pull_requests_export.csv` | Tutte le PR | author, repo, state, created_at, merged_at, review_time |
| `issues_export.csv` | Tutte le issue | author, repo, state, labels, created_at, closed_at |
| `contributors_summary.csv` | Riepilogo per contributor | author, commits, prs_opened, prs_merged, issues_closed |
| `repository_summary.csv` | Riepilogo per repository | repo, commits, prs, issues, contributors |
| `quality_metrics.csv` | Metriche di qualità | repo, code_churn, review_coverage, bug_ratio |
| `productivity_analysis.csv` | Analisi produttività | author, daily_output, consistency_score, peak_hours |

### Dati Jira (Deterministici)

I seguenti file CSV vengono generati dall'integrazione Jira:

| File | Descrizione | Campi Chiave |
|------|-------------|--------------|
| `jira_issues_export.csv` | Tutte le issue Jira | key, assignee, status, type, priority, created, resolved |
| `jira_person_metrics.csv` | Metriche per persona | assignee, assigned, resolved, wip, cycle_time, bugs |
| `jira_project_quality.csv` | Qualità per progetto | project, cycle_time, bug_ratio, reopen_rate, silent_issues |
| `jira_quality_metrics.csv` | Metriche qualitative | description_quality, comment_velocity, same_day_rate |

### Dati Calcolati (Runtime)

Il generatore calcola automaticamente:

- **Trend temporali**: confronto con periodo precedente (es. +15% commit rispetto al mese scorso)
- **Ranking**: classifiche per produttività, velocità, qualità
- **Correlazioni**: es. relazione tra PR review time e bug rate
- **Aggregazioni cross-source**: metriche combinate GitHub + Jira

---

## Integrazione Perplexity AI

### Configurazione

```bash
# Variabile d'ambiente richiesta
export PERPLEXITY_API_KEY="pplx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### Utilizzo nel Sistema

Perplexity viene utilizzato per generare **insights qualitativi** che non possono essere derivati puramente dai dati:

#### 1. Analisi del Team

```python
# Prompt di esempio per analisi team
prompt = f"""
Analizza le seguenti metriche del team di sviluppo:
- Resolution rate: {resolution_rate}%
- Cycle time medio: {cycle_time} giorni
- Bug resolution time: {bug_time} giorni
- WIP totale: {wip_count} task

Fornisci:
1. Valutazione complessiva (A/B/C/D/F)
2. 3-5 punti di forza
3. 3-5 aree di miglioramento
4. 2-3 red flag da monitorare
5. Raccomandazioni concrete per il prossimo sprint
"""
```

#### 2. Analisi Individuale

```python
# Prompt per valutazione singolo membro
prompt = f"""
Valuta le performance di {member_name}:
- Task assegnati: {assigned}
- Task risolti: {resolved}
- Cycle time: {cycle_time} giorni
- WIP corrente: {wip}
- Bug gestiti: {bugs}

Confronta con la media del team:
- Cycle time medio team: {team_avg_cycle}
- Resolution rate medio: {team_avg_resolution}%

Fornisci:
1. Rating (A/B/C/D/F con +/-)
2. Punti di forza specifici
3. Aree di miglioramento
4. Red flag (se presenti)
5. Consiglio personalizzato
"""
```

#### 3. Analisi Progetti

```python
# Prompt per analisi progetto
prompt = f"""
Analizza lo stato di salute del progetto {project_name}:
- Issues totali: {total_issues}
- Cycle time: {cycle_time} giorni
- Bug ratio: {bug_ratio}%
- Reopen rate: {reopen_rate}%
- Silent issues: {silent_ratio}%

Identifica:
1. Criticità immediate
2. Rischi potenziali
3. Best practice osservate
4. Suggerimenti per miglioramento
"""
```

### Rate Limiting e Caching

```python
# Configurazione consigliata
PERPLEXITY_CONFIG = {
    "model": "llama-3.1-sonar-small-128k-online",  # o sonar-medium per analisi complesse
    "max_tokens": 1024,
    "temperature": 0.2,  # bassa per output consistenti
    "rate_limit_rpm": 20,  # requests per minute
    "cache_ttl_hours": 24,  # cache risultati per evitare chiamate duplicate
}
```

### Output Atteso da Perplexity

Per ogni sezione del report, Perplexity genera JSON strutturato:

```json
{
  "rating": "B+",
  "strengths": [
    "Resolution rate alto: 89%",
    "WIP contenuto - buona gestione del flusso"
  ],
  "improvements": [
    "Cycle time Alexandru da investigare",
    "Bug resolution time troppo elevato"
  ],
  "red_flags": [
    "Cycle time 31gg per Alexandru - possibili blocchi"
  ],
  "recommendations": [
    "Implementare daily standup più frequenti",
    "Ridurre WIP limit a 2 per developer"
  ],
  "summary": "Il team mostra buona produttività..."
}
```

---

## User Mapping (Jira ↔ GitHub)

### Il Problema

Gli utenti in Jira e GitHub hanno spesso identificativi diversi:

| Jira | GitHub | Note |
|------|--------|------|
| `Mircha Emanuel D'Angelo` | `mircha` | Nome completo vs username |
| `Alexandru Ungureanu` | `alexu` | Username abbreviato |
| `massimo.mandolini@company.com` | `mmandolini` | Email vs username |

### Soluzione: Sistema di Mapping Interattivo

#### 1. File di Configurazione Mapping

```yaml
# frontend/config/user_mapping.yaml
mappings:
  - jira_display_name: "Mircha Emanuel D'Angelo"
    jira_account_id: "712020:abc123"
    jira_email: "mircha@oltrematica.com"
    github_username: "mircha"
    github_id: 12345678
    aliases:
      - "Mircha D'Angelo"
      - "mircha.dangelo"

  - jira_display_name: "Alexandru Ungureanu"
    jira_account_id: "712020:def456"
    jira_email: "alexandru@oltrematica.com"
    github_username: "alexu"
    github_id: 23456789
    aliases:
      - "Alex Ungureanu"

# Mappings non confermati (da verificare)
unconfirmed:
  - jira_name: "setek"
    possible_github_matches:
      - username: "setek-user"
        confidence: 0.85
      - username: "setekdev"
        confidence: 0.72
```

#### 2. Algoritmo di Auto-Matching

Il sistema tenta automaticamente di associare gli utenti usando:

```python
def auto_match_users(jira_users: list, github_users: list) -> dict:
    """
    Algoritmo di matching con punteggio di confidenza.

    Strategie (in ordine di priorità):
    1. Email esatto match (confidenza: 1.0)
    2. Username identico (confidenza: 0.95)
    3. Nome/cognome fuzzy match (confidenza: 0.7-0.9)
    4. Iniziali + cognome (confidenza: 0.6)
    5. Pattern comuni (es. nome.cognome) (confidenza: 0.5)
    """
    matches = {}

    for jira_user in jira_users:
        candidates = []

        # Strategia 1: Email match
        if jira_user.email in github_emails:
            candidates.append({
                "github": github_by_email[jira_user.email],
                "confidence": 1.0,
                "method": "email_exact"
            })

        # Strategia 2: Username identico
        if jira_user.name.lower() in github_usernames:
            candidates.append({
                "github": jira_user.name.lower(),
                "confidence": 0.95,
                "method": "username_exact"
            })

        # Strategia 3: Fuzzy matching su nome
        for gh_user in github_users:
            similarity = fuzzy_ratio(jira_user.display_name, gh_user.name)
            if similarity > 0.7:
                candidates.append({
                    "github": gh_user.username,
                    "confidence": similarity * 0.9,
                    "method": "name_fuzzy"
                })

        matches[jira_user.id] = sorted(candidates, key=lambda x: -x["confidence"])

    return matches
```

#### 3. Interfaccia di Riconciliazione (CLI)

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
  [3] s.tek          (confidenza: 45%) - 0 commits
  [N] Nuovo - inserisci username manualmente
  [S] Skip - ignora questo utente
  [?] Mostra dettagli attività

Scelta [1-3/N/S/?]: 2

✓ Mapping salvato: setek (Jira) → setekdev (GitHub)

─────────────────────────────────────────────────────────────────────
[2/3] Jira: "Matteo Catoni" (6 task)
─────────────────────────────────────────────────────────────────────
Nessun candidato automatico trovato.

  [N] Inserisci username GitHub manualmente
  [S] Skip - questo utente non ha account GitHub
  [L] Lista tutti gli utenti GitHub disponibili

Scelta [N/S/L]: N
Username GitHub: mcatoni

✓ Mapping salvato: Matteo Catoni (Jira) → mcatoni (GitHub)
```

#### 4. Interfaccia Web di Riconciliazione (Opzionale)

Per un'esperienza più user-friendly, il sistema può generare una pagina HTML interattiva:

```html
<!-- frontend/mapping/index.html -->
<div class="mapping-container">
  <h2>Riconciliazione Utenti Jira ↔ GitHub</h2>

  <div class="mapping-card unconfirmed">
    <div class="jira-user">
      <img src="jira-avatar.png" />
      <span>setek</span>
      <small>1 task in Jira</small>
    </div>

    <div class="arrow">→</div>

    <div class="github-candidates">
      <div class="candidate selected" data-confidence="85">
        <img src="gh-avatar.png" />
        <span>setek-user</span>
        <small>3 commits, 2 PRs</small>
        <span class="confidence">85%</span>
      </div>
      <div class="candidate" data-confidence="72">
        <img src="gh-avatar2.png" />
        <span>setekdev</span>
        <small>15 commits, 8 PRs</small>
        <span class="confidence">72%</span>
      </div>
    </div>

    <button class="confirm-btn">Conferma</button>
  </div>
</div>
```

#### 5. Gestione dei Casi Edge

```python
# Casi speciali da gestire
EDGE_CASES = {
    # Utenti senza account GitHub (es. project manager)
    "no_github": {
        "action": "include_jira_only",
        "report_section": "jira_metrics"
    },

    # Utenti senza attività Jira (es. contributor esterni)
    "no_jira": {
        "action": "include_github_only",
        "report_section": "github_metrics"
    },

    # Bot/automazioni
    "bots": {
        "patterns": ["dependabot", "github-actions", "jira-automation"],
        "action": "exclude_from_individual_reports",
        "include_in_totals": False
    },

    # Account multipli stesso utente
    "multiple_accounts": {
        "action": "merge_metrics",
        "primary_selection": "most_active"
    }
}
```

---

## Struttura del Report

### Sezioni Principali

```
REPORT STRUCTURE
├── Header
│   ├── Titolo e periodo
│   ├── Data generazione
│   └── Fonti dati utilizzate
│
├── Team Overview (Panoramica)
│   ├── KPI Cards (task totali, risolti, resolution rate, cycle time)
│   ├── Team Members Grid (cards cliccabili)
│   ├── Charts comparativi
│   │   ├── Task Assegnati vs Risolti (bar chart)
│   │   ├── Cycle Time per Persona (horizontal bar)
│   │   ├── WIP Distribution (donut)
│   │   └── Bug Distribution (bar)
│   ├── Rankings
│   │   ├── Produttività (per task risolti)
│   │   └── Velocità (per cycle time)
│   └── AI Analysis (Perplexity)
│       ├── Punti di Forza
│       ├── Aree di Miglioramento
│       └── Red Flags
│
├── Quality Metrics (Metriche Qualità)
│   ├── Project Quality Table
│   ├── Cycle Time per Progetto (chart)
│   ├── Issue Type Distribution (donut)
│   ├── Metriche per Tipo Issue (table)
│   ├── Red Flag Alerts
│   └── Indicatori Salute Backlog
│
├── Individual Reports (per ogni membro)
│   ├── Member Header (avatar, nome, ruolo, rating AI)
│   ├── Personal KPI Cards
│   ├── AI Analysis personalizzata
│   │   ├── Punti di Forza
│   │   ├── Aree di Miglioramento
│   │   └── Red Flags
│   └── Valutazione Complessiva AI
│
├── GitHub Metrics (se dati disponibili)
│   ├── Commit Activity
│   ├── PR Metrics
│   ├── Code Review Stats
│   └── Repository Health
│
└── Footer
    ├── Data generazione
    ├── Fonti dati
    └── Disclaimer AI
```

### Navigazione

- **Sticky navigation bar** con tab per ogni sezione
- **Deep linking** via hash (#section-name)
- **Keyboard navigation** (frecce, numeri)
- **Mobile-responsive** con hamburger menu

---

## Requisiti di Design

### Principi Guida

1. **Wow Factor**: Il report deve impressionare a prima vista
2. **Data Storytelling**: I dati devono raccontare una storia
3. **Actionable Insights**: Ogni metrica deve suggerire un'azione
4. **Accessibility**: WCAG 2.1 AA compliance
5. **Performance**: Tempo di caricamento < 2s

### Specifiche Visive

```css
/* Palette colori */
:root {
  /* Primary gradient */
  --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

  /* Semantic colors */
  --success: #48bb78;
  --warning: #ed8936;
  --danger: #f56565;
  --info: #4299e1;

  /* Member colors (distintivi per persona) */
  --color-member-1: #667eea;  /* Primary/Lead */
  --color-member-2: #48bb78;  /* Green */
  --color-member-3: #ed8936;  /* Orange */
  --color-member-4: #9f7aea;  /* Purple */
  --color-member-5: #38b2ac;  /* Teal */

  /* Backgrounds */
  --bg-gradient: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  --bg-card: #ffffff;
  --bg-hover: #f8faff;

  /* Typography */
  --font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-size-base: 16px;
  --line-height: 1.6;
}

/* Effetti */
.card {
  border-radius: 20px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.08);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 20px 60px rgba(0,0,0,0.12);
}

/* Animazioni */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}
```

### Charts (Chart.js)

```javascript
// Configurazione globale Chart.js
Chart.defaults.font.family = "'Segoe UI', sans-serif";
Chart.defaults.responsive = true;
Chart.defaults.maintainAspectRatio = false;

// Stile bar chart
const barChartConfig = {
  borderRadius: 8,
  borderSkipped: false,
  maxBarThickness: 50,
};

// Stile donut chart
const donutChartConfig = {
  cutout: '60%',
  borderWidth: 0,
  hoverOffset: 10,
};
```

### Responsive Breakpoints

```css
/* Mobile first */
@media (min-width: 576px) { /* Small */ }
@media (min-width: 768px) { /* Medium */ }
@media (min-width: 992px) { /* Large */ }
@media (min-width: 1200px) { /* XL */ }
@media (min-width: 1600px) { /* XXL - container max-width */ }
```

---

## Configurazione

### Variabili d'Ambiente

```bash
# Obbligatorie
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
export JIRA_BASE_URL="https://company.atlassian.net"
export JIRA_EMAIL="user@company.com"
export JIRA_API_TOKEN="xxxxxxxxxxxxxxxxxxxxxxxx"
export PERPLEXITY_API_KEY="pplx-xxxxxxxxxxxxxxxxxxxxxxxx"

# Opzionali
export REPORT_OUTPUT_DIR="./frontend/reports"
export REPORT_PERIOD_DAYS=30
export PERPLEXITY_MODEL="llama-3.1-sonar-small-128k-online"
export USER_MAPPING_FILE="./frontend/config/user_mapping.yaml"
```

### File di Configurazione Report

```yaml
# frontend/config/report_config.yaml
report:
  title: "Team Performance Report"
  subtitle: "Oltrematica Development Team"
  language: "it"  # it, en
  period_days: 30

sections:
  team_overview:
    enabled: true
    show_rankings: true
    show_ai_analysis: true

  quality_metrics:
    enabled: true
    projects_to_include: "all"  # o lista specifica

  individual_reports:
    enabled: true
    members_to_include: "all"  # o lista specifica
    min_tasks_for_report: 3

  github_metrics:
    enabled: true
    repos_to_include: "all"

ai_analysis:
  provider: "perplexity"
  generate_for:
    - team_overview
    - individual_reports
    - project_analysis
  cache_results: true
  cache_ttl_hours: 24

design:
  theme: "gradient"  # gradient, minimal, dark
  member_colors: "auto"  # auto-assign o configurazione manuale
  charts_library: "chartjs"
  animations: true
```

---

## Workflow di Generazione

### Comando Principale

```bash
# Genera report completo
python -m src.github_analyzer.report_generator \
  --period 30 \
  --output ./frontend/reports/$(date +%Y-%m-%d)/

# Con opzioni
python -m src.github_analyzer.report_generator \
  --period 30 \
  --sources github,jira \
  --ai-analysis \
  --user-mapping ./frontend/config/user_mapping.yaml \
  --output ./frontend/reports/latest/
```

### Fasi di Generazione

```
FASE 1: Data Collection (10-30s)
├── Fetch GitHub data via API
├── Fetch Jira data via API
├── Load cached data if available
└── Validate data completeness

FASE 2: User Mapping (interattivo se necessario)
├── Load existing mappings
├── Auto-match new users
├── Prompt for unconfirmed mappings
└── Save updated mapping file

FASE 3: Data Processing (5-10s)
├── Merge GitHub + Jira data per user
├── Calculate aggregated metrics
├── Compute trends vs previous period
└── Generate rankings

FASE 4: AI Analysis (30-60s)
├── Prepare prompts with context
├── Call Perplexity API for each section
├── Parse and validate AI responses
└── Cache results

FASE 5: Report Generation (2-5s)
├── Load HTML template
├── Inject data into template
├── Generate charts configuration
├── Bundle CSS/JS
└── Write output files

FASE 6: Output
├── index.html (report principale)
├── data.json (dati raw per debugging)
├── ai_insights.json (cache AI responses)
└── assets/ (CSS, JS, images)
```

---

## API e Formati Dati

### Formato JSON per Template

```json
{
  "meta": {
    "generated_at": "2025-11-29T10:30:00Z",
    "period_start": "2025-10-29",
    "period_end": "2025-11-28",
    "sources": ["github", "jira"]
  },

  "team": {
    "name": "Oltrematica Development Team",
    "total_members": 4,
    "kpis": {
      "total_tasks": 82,
      "resolved_tasks": 73,
      "resolution_rate": 89.0,
      "avg_cycle_time": 10.5,
      "total_bugs": 8,
      "wip_total": 9
    }
  },

  "members": [
    {
      "id": "mircha",
      "name": "Mircha Emanuel D'Angelo",
      "role": "Tech Lead",
      "color": "#667eea",
      "jira_id": "712020:abc123",
      "github_username": "mircha",
      "metrics": {
        "assigned": 47,
        "resolved": 44,
        "wip": 3,
        "cycle_time": 5.87,
        "bugs": 4,
        "resolution_rate": 93.6
      },
      "github_metrics": {
        "commits": 156,
        "prs_opened": 23,
        "prs_merged": 21,
        "reviews_given": 45
      },
      "ai_analysis": {
        "rating": "A",
        "strengths": ["..."],
        "improvements": ["..."],
        "red_flags": [],
        "summary": "..."
      }
    }
  ],

  "projects": [
    {
      "key": "PM",
      "name": "Pescara Multiservice",
      "issues_count": 50,
      "cycle_time": 8.88,
      "bug_ratio": 14,
      "same_day_rate": 38.1,
      "silent_issues_ratio": 68,
      "reopen_rate": 7.14
    }
  ],

  "ai_insights": {
    "team_analysis": {
      "rating": "B+",
      "strengths": ["..."],
      "improvements": ["..."],
      "red_flags": ["..."],
      "recommendations": ["..."]
    }
  }
}
```

### Perplexity API Request

```python
import requests

def call_perplexity(prompt: str) -> dict:
    response = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers={
            "Authorization": f"Bearer {os.environ['PERPLEXITY_API_KEY']}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.1-sonar-small-128k-online",
            "messages": [
                {
                    "role": "system",
                    "content": """Sei un esperto di engineering management e DevOps metrics.
                    Analizza i dati forniti e rispondi in formato JSON strutturato.
                    Usa italiano. Sii conciso e actionable."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1024,
            "temperature": 0.2
        }
    )
    return response.json()
```

---

## Directory Structure Finale

```
frontend/
├── README.md                    # Questo file
├── config/
│   ├── report_config.yaml      # Configurazione report
│   └── user_mapping.yaml       # Mapping utenti Jira↔GitHub
│
├── templates/
│   ├── report.html             # Template principale
│   ├── components/
│   │   ├── header.html
│   │   ├── navigation.html
│   │   ├── team_overview.html
│   │   ├── quality_metrics.html
│   │   ├── member_report.html
│   │   └── footer.html
│   └── partials/
│       ├── stat_card.html
│       ├── chart_container.html
│       └── highlight_card.html
│
├── assets/
│   ├── css/
│   │   ├── main.css
│   │   ├── components.css
│   │   ├── charts.css
│   │   └── responsive.css
│   ├── js/
│   │   ├── main.js
│   │   ├── charts.js
│   │   └── navigation.js
│   └── images/
│       └── logo.svg
│
├── reports/                     # Output generati
│   ├── latest/                  # Symlink all'ultimo report
│   └── 2025-11-29/
│       ├── index.html
│       ├── data.json
│       └── ai_insights.json
│
├── mapping/                     # Tool di riconciliazione
│   ├── index.html              # UI web per mapping
│   └── mapping_cli.py          # CLI per mapping
│
└── example/                     # Esempi e mock data
    ├── index.html              # Report di esempio
    ├── team_stats.json
    ├── team_comparison.json
    └── tasks.json
```

---

## Prossimi Passi

1. **Implementare il generatore Python** in `src/github_analyzer/report_generator/`
2. **Creare il sistema di user mapping** con CLI e UI web
3. **Integrare Perplexity API** per analisi AI
4. **Sviluppare i template HTML** modulari
5. **Testare con dati reali** e iterare sul design
6. **Documentare API** per estensioni future
