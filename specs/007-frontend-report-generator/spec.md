# Feature Specification: Frontend Report Generator

**Feature Branch**: `007-frontend-report-generator`
**Created**: 2025-11-29
**Status**: Draft
**Input**: User description: "Frontend Report Generator: sistema di generazione automatica di report interattivi HTML per analisi performance team. Include: 1) Data aggregator Python che unisce export CSV GitHub e Jira, 2) User mapping interattivo Jira↔GitHub con auto-matching fuzzy e CLI/web UI per riconciliazione, 3) Integrazione Perplexity AI per insights qualitativi (team analysis, individual reports, project health), 4) Report generator HTML/CSS/JS con template modulari, Chart.js per visualizzazioni, design responsive. Output: report standalone index.html con sezioni Team Overview, Quality Metrics, Individual Reports, GitHub Metrics."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generazione Report Base (Priority: P1)

Come team lead, voglio generare un report HTML interattivo che mostri le metriche di performance del team aggregate da GitHub e Jira, per avere una visione completa delle attività in un formato presentabile.

**Why this priority**: Questo è il core della feature - senza la capacità di generare un report base, nessuna delle altre funzionalità ha senso. Fornisce valore immediato aggregando dati esistenti.

**Independent Test**: Può essere testato generando un report con dati CSV esistenti e verificando che l'HTML prodotto contenga tutte le sezioni richieste e sia navigabile.

**Acceptance Scenarios**:

1. **Given** export CSV di GitHub (commits, PRs, issues) e Jira (issues, metrics) nella directory di input, **When** eseguo il comando di generazione report, **Then** viene prodotto un file index.html standalone con tutte le sezioni (Team Overview, Quality Metrics, Individual Reports, GitHub Metrics).

2. **Given** un report generato, **When** apro il file HTML in un browser, **Then** vedo una navigazione sticky, grafici interattivi e cards KPI per ogni sezione.

3. **Given** dati per un periodo di 30 giorni, **When** genero il report, **Then** vengono calcolati automaticamente trend e confronti con il periodo precedente.

---

### User Story 2 - Mapping Utenti Jira↔GitHub (Priority: P2)

Come amministratore del sistema, voglio associare gli account Jira agli username GitHub per avere metriche unificate per ogni membro del team, gestendo casi in cui i nomi utente differiscono tra i due sistemi.

**Why this priority**: Senza mapping utenti, le metriche individuali non possono essere aggregate correttamente. È prerequisito per report individuali accurati.

**Independent Test**: Può essere testato eseguendo il processo di mapping con una lista di utenti Jira e GitHub, verificando che il sistema proponga match automatici e permetta correzioni manuali.

**Acceptance Scenarios**:

1. **Given** una lista di utenti Jira e GitHub senza mapping esistente, **When** avvio il processo di mapping, **Then** il sistema tenta auto-matching basato su email, username e nome fuzzy, mostrando candidati con punteggio di confidenza.

2. **Given** un match automatico con confidenza inferiore all'85%, **When** viene presentato all'utente, **Then** può confermare, selezionare un candidato alternativo, o inserire manualmente lo username corretto.

3. **Given** un mapping completato, **When** viene salvato, **Then** persiste in un file di configurazione YAML riutilizzabile per generazioni future.

4. **Given** un utente presente solo in Jira (es. project manager senza GitHub), **When** elaboro i dati, **Then** viene incluso nelle metriche Jira ma escluso dalle metriche GitHub senza errori.

---

### User Story 3 - Analisi AI con Perplexity (Priority: P3)

Come team lead, voglio che il report includa insights qualitativi generati da AI che analizzino i pattern nei dati e forniscano raccomandazioni actionable, per ottenere valutazioni che vadano oltre i semplici numeri.

**Why this priority**: Aggiunge valore significativo ma richiede integrazione esterna. Il report base è comunque utile senza AI.

**Independent Test**: Può essere testato inviando metriche aggregate a Perplexity API e verificando che le risposte siano JSON validi con rating, strengths, improvements e recommendations.

**Acceptance Scenarios**:

1. **Given** metriche aggregate del team, **When** genero il report con flag AI abilitato, **Then** viene inclusa una sezione "AI Analysis" con rating (A-F), punti di forza, aree di miglioramento e red flags.

2. **Given** metriche individuali per un membro del team, **When** genero il report con AI, **Then** ogni report individuale include valutazione personalizzata con confronto rispetto alla media del team.

3. **Given** assenza di API key Perplexity o errore API, **When** genero il report, **Then** le sezioni AI mostrano un placeholder appropriato senza bloccare la generazione del resto del report.

4. **Given** una generazione report recente (<24h), **When** rigenero il report con gli stessi dati, **Then** vengono usate le analisi AI in cache per evitare chiamate API duplicate.

---

### User Story 4 - Visualizzazioni Interattive (Priority: P4)

Come stakeholder, voglio visualizzare i dati attraverso grafici interattivi (bar chart, donut, trend lines) che mi permettano di esplorare le metriche in modo intuitivo.

**Why this priority**: I grafici migliorano significativamente la leggibilità ma il report è funzionale anche con tabelle e KPI cards.

**Independent Test**: Può essere testato verificando che i grafici Chart.js si renderizzino correttamente e rispondano a hover/click per mostrare dettagli.

**Acceptance Scenarios**:

1. **Given** un report generato con dati di almeno 3 membri del team, **When** visualizzo la sezione Team Overview, **Then** vedo un bar chart comparativo task assegnati vs risolti per persona.

2. **Given** dati di quality metrics per progetto, **When** visualizzo la sezione Quality Metrics, **Then** vedo un donut chart della distribuzione per tipo issue e un bar chart del cycle time per progetto.

3. **Given** un report aperto su dispositivo mobile, **When** visualizzo i grafici, **Then** si adattano allo schermo mantenendo leggibilità e interattività touch.

---

### User Story 5 - Interfaccia CLI di Generazione (Priority: P5)

Come utente tecnico, voglio un comando CLI con opzioni configurabili per generare report con diversi parametri (periodo, fonti dati, output directory), per integrare la generazione in workflow automatizzati.

**Why this priority**: La CLI è il punto di ingresso principale ma può essere semplificata inizialmente.

**Independent Test**: Può essere testato eseguendo il comando con varie combinazioni di flag e verificando output e comportamento atteso.

**Acceptance Scenarios**:

1. **Given** i file CSV di export nella directory corrente, **When** eseguo `python -m src.github_analyzer.report_generator --period 30`, **Then** viene generato un report per gli ultimi 30 giorni nella directory di output di default.

2. **Given** un file di mapping utenti esistente, **When** eseguo il comando con `--user-mapping path/to/mapping.yaml`, **Then** viene usato quel file invece di avviare il processo interattivo.

3. **Given** il flag `--no-ai`, **When** genero il report, **Then** le sezioni AI vengono omesse e non vengono effettuate chiamate a Perplexity.

---

### Edge Cases

- Cosa succede quando un file CSV di input è vuoto o malformato?
  - Il sistema segnala l'errore specifico e prosegue con i dati disponibili
- Come gestisce il sistema utenti con account multipli (es. cambio username)?
  - Il file di mapping supporta alias multipli per utente
- Cosa succede se il periodo richiesto non ha dati sufficienti per calcolare trend?
  - I trend vengono omessi con nota esplicativa invece di mostrare dati misleading
- Come vengono gestiti i bot/automazioni (dependabot, github-actions)?
  - Vengono esclusi dai report individuali ma inclusi nei totali se configurato

## Requirements *(mandatory)*

### Functional Requirements

#### Data Aggregation
- **FR-001**: Sistema DEVE leggere e parsare file CSV di export GitHub (commits_export.csv, pull_requests_export.csv, issues_export.csv, contributors_summary.csv, repository_summary.csv, quality_metrics.csv, productivity_analysis.csv)
- **FR-001a**: CSV DEVE essere parsato con encoding UTF-8; altri encoding causano warning e skip della riga
- **FR-001b**: CSV malformato = riga con numero colonne diverso da header, o campo date/numerico non parsabile
- **FR-002**: Sistema DEVE leggere e parsare file CSV di export Jira (jira_issues_export.csv, jira_person_metrics.csv, jira_project_quality.csv, jira_quality_metrics.csv)
- **FR-003**: Sistema DEVE calcolare metriche aggregate: task totali, risolti, resolution rate, cycle time medio, WIP totale, bug count
- **FR-003a**: Formule metriche: resolution_rate = (resolved / assigned) * 100; cycle_time = media giorni da creazione a chiusura
- **FR-004**: Sistema DEVE calcolare trend confrontando il periodo corrente con il periodo precedente equivalente (stesso numero di giorni immediatamente precedenti)
- **FR-004a**: Se dati storici insufficienti per trend, campo mostra "N/A - dati insufficienti" invece di valore numerico

#### User Mapping
- **FR-005**: Sistema DEVE supportare auto-matching utenti basato su: email esatto (confidenza 100%), username identico (95%), nome fuzzy (70-90%), iniziali+cognome (60%)
- **FR-005a**: Fuzzy matching usa difflib.SequenceMatcher con threshold 0.7; confidenza = ratio * 0.9 per range 70-90%
- **FR-005b**: Bot detection patterns: "dependabot*", "github-actions*", "*[bot]", "renovate*"
- **FR-006**: Sistema DEVE presentare interfaccia CLI per riconciliazione manuale dei match non confermati (confidenza <85%)
- **FR-006a**: CLI interattiva mostra: [1-N] candidati ordinati per confidenza, [N] nuovo username manuale, [S] skip utente
- **FR-006b**: Se utente preme Ctrl+C durante mapping interattivo: salva mapping parziale, termina con exit code 1
- **FR-007**: Sistema DEVE persistere i mapping in formato YAML leggibile e modificabile
- **FR-008**: Sistema DEVE gestire edge cases: utenti solo-Jira, utenti solo-GitHub, bot/automazioni, account multipli
- **FR-008a**: Utenti solo-Jira: inclusi in metriche Jira, esclusi da metriche GitHub, mostrati in report con nota "No GitHub data"
- **FR-008b**: Utenti solo-GitHub: inclusi in metriche GitHub, esclusi da metriche Jira, mostrati in report con nota "No Jira data"

#### AI Integration
- **FR-009**: Sistema DEVE integrare Perplexity API (endpoint: https://api.perplexity.ai/chat/completions, model: llama-3.1-sonar-large-128k-online)
- **FR-010**: Sistema DEVE generare prompt strutturati con metriche contestuali per team, individui e progetti
- **FR-011**: Sistema DEVE parsare risposte AI in formato JSON strutturato (rating, strengths, improvements, red_flags, recommendations)
- **FR-011a**: Campi JSON obbligatori: rating (A-F con +/-), strengths (1-5 items), improvements (1-5 items), summary (string)
- **FR-011b**: Campi JSON opzionali: red_flags (0-3 items), recommendations (0-4 items)
- **FR-012**: Sistema DEVE implementare cache delle risposte AI con TTL configurabile (default 24h)
- **FR-012a**: Cache key = hash SHA256 dei dati metriche input; file format: ai_cache_{hash}.json
- **FR-013**: Sistema DEVE graceful degradation se API non disponibile: sezione mostra "🤖 Analisi AI non disponibile - API key mancante o servizio non raggiungibile"
- **FR-013a**: Sistema DEVE, in caso di rate limit API (HTTP 429) durante generazione, presentare prompt interattivo: [W] attendi con backoff esponenziale (max 5 min), [S] prosegui senza AI
- **FR-013b**: Per errori API transitori (HTTP 500, 503): retry automatico con backoff esponenziale (1s, 2s, 4s), max 3 tentativi, poi skip
- **FR-013c**: Per errore autenticazione (HTTP 401): abort immediato con messaggio "PERPLEXITY_API_KEY non valida o scaduta"

#### Report Generation
- **FR-014**: Sistema DEVE generare file HTML standalone con CSS/JS inline (no dipendenze esterne eccetto CDN Chart.js)
- **FR-014a**: Se CDN Chart.js non raggiungibile: report mostra tabelle dati al posto dei grafici con nota "Grafici non disponibili - CDN non raggiungibile"
- **FR-015**: Sistema DEVE includere sezioni: Header, Team Overview, Quality Metrics, Individual Reports, GitHub Metrics, Footer
- **FR-015a**: Section IDs per deep linking: #header, #team-overview, #quality-metrics, #individual-reports, #github-metrics, #footer
- **FR-016**: Sistema DEVE generare configurazioni Chart.js per grafici interattivi
- **FR-016a**: Tipi grafici: bar chart (task assigned vs resolved), donut chart (issue type distribution), horizontal bar (cycle time per project)
- **FR-016b**: Interazioni grafici: hover mostra tooltip con valore, click su legenda toggle visibilità serie
- **FR-017**: Sistema DEVE supportare navigazione sticky con deep linking (#section-name)
- **FR-017a**: Sticky nav: position fixed, top 0, z-index 100, background opaco, collassa in hamburger menu sotto 768px
- **FR-018**: Sistema DEVE essere responsive (breakpoints: 576px, 768px, 992px, 1200px, 1600px)
- **FR-018a**: Comportamento breakpoints: <576px single column, 576-768px 2 columns cards, 768-992px sidebar nav, >992px full layout
- **FR-018b**: Zero-state handling: sezione senza dati mostra messaggio "Nessun dato disponibile per questo periodo" invece di spazio vuoto
- **FR-018c**: Single member edge case: grafici comparativi mostrano solo bar singola con label, no comparative ranking

#### CLI Interface
- **FR-019**: Sistema DEVE accettare parametri: --period (giorni), --output (directory), --sources (github,jira), --user-mapping (file), --ai/--no-ai, --config (file)
- **FR-019a**: Parametri di default: --period=30, --output=./frontend/reports/{date}/, --sources=github,jira, --ai=true
- **FR-019b**: Il parametro --sources DEVE essere case-insensitive e accettare valori comma-separated (es. "GitHub,Jira" o "github")
- **FR-020**: Sistema DEVE fornire output progress durante generazione multi-fase con indicatori [1/5], [2/5], etc.
- **FR-020a**: Exit codes: 0=successo, 1=errore utente (argomenti invalidi, file mancanti), 2=errore sistema (API failure, IO error)

#### Security
- **FR-021**: Token PERPLEXITY_API_KEY DEVE essere caricato SOLO da variabile d'ambiente, MAI hardcoded
- **FR-022**: Token API NON DEVE essere loggato, stampato, o esposto in messaggi di errore
- **FR-023**: Sistema DEVE validare --output path contro path traversal attacks (riuso validate_output_path da core/security.py)
- **FR-024**: Sistema DEVE applicare html.escape() a TUTTI i valori user-provided renderizzati nel report HTML (prevenzione XSS)
- **FR-025**: Sistema DEVE usare yaml.safe_load() per parsing di user_mapping.yaml (prevenzione code injection)
- **FR-026**: Messaggi di errore NON DEVONO esporre path interni del sistema, stack traces, o dettagli di configurazione

#### Accessibility
- **FR-027**: Report HTML DEVE supportare navigazione da tastiera per tutti gli elementi interattivi (Tab, Enter, Escape)
- **FR-028**: Grafici Chart.js DEVONO includere attributi aria-label con descrizione testuale dei dati
- **FR-029**: Palette colori DEVE rispettare WCAG 2.1 AA contrast ratio (minimo 4.5:1 per testo normale)
- **FR-030**: Sistema DEVE rispettare prefers-reduced-motion: grafici disabilitano animazioni se preferenza attiva

#### Error Handling & Recovery
- **FR-031**: Se file CSV mancante: sistema continua con fonti disponibili, logga warning, report mostra sezione vuota con nota
- **FR-032**: Se file CSV malformato (encoding errato, colonne mancanti): sistema logga errore specifico per riga, skippa righe invalide, continua parsing
- **FR-033**: Se --user-mapping file non esiste: sistema avvia processo interattivo di mapping (fallback)
- **FR-034**: Se --output directory non ha permessi scrittura: sistema termina con exit code 1 e messaggio chiaro
- **FR-035**: Se AI response JSON malformato: sistema logga warning, usa placeholder "Analisi non disponibile", continua generazione
- **FR-036**: Se AI analysis parziale (alcuni membri ok, altri falliti): sistema include analisi disponibili, mostra placeholder per falliti

### Key Entities

- **TeamMember**: Rappresenta un membro del team con identità unificata (jira_id, github_username, display_name, email, aliases), metriche aggregate da entrambe le fonti, e analisi AI associata. Scala supportata: fino a 30 membri per report.
- **Project**: Rappresenta un progetto/repository con metriche di qualità (cycle_time, bug_ratio, reopen_rate, silent_issues_ratio). Scala supportata: 12 mesi di storico dati.
- **UserMapping**: Configurazione di associazione tra identità Jira e GitHub con punteggio di confidenza e metodo di match
- **ReportData**: Struttura dati completa per la generazione del template (meta, team, members[], projects[], ai_insights)
- **AIInsight**: Output strutturato da Perplexity (rating, strengths[], improvements[], red_flags[], recommendations[], summary)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Report generato in meno di 2 minuti per team fino a 30 membri e 12 mesi di dati (escluso tempo chiamate AI)
- **SC-002**: Auto-matching utenti raggiunge accuratezza ≥80% su dataset con naming conventions standard
- **SC-003**: Report HTML si carica in meno di 3 secondi su connessione standard e pesa meno di 2MB
- **SC-004**: Grafici interattivi funzionano su browser moderni (Chrome, Firefox, Safari, Edge ultimi 2 anni)
- **SC-005**: Report è navigabile e leggibile su dispositivi con larghezza minima 320px
- **SC-006**: 90% degli utenti riesce a generare un report al primo tentativo seguendo la documentazione
- **SC-007**: Analisi AI fornisce insights actionable (rating + almeno 2 raccomandazioni concrete) per ogni entità analizzata

## Clarifications

### Session 2025-11-29

- Q: Come deve comportarsi il sistema quando l'API Perplexity raggiunge il rate limit durante la generazione? → A: Richiede conferma interattiva all'utente (attendere o proseguire senza AI)
- Q: Qual è la scala massima di dati che il sistema deve supportare? → A: Medium team - max 30 membri, 12 mesi di dati

## Assumptions

- I file CSV di export GitHub e Jira sono già generati dal sistema esistente (github_analyzer e jira_client)
- Gli utenti hanno familiarità con l'uso di CLI per tool di sviluppo
- L'API key Perplexity è fornita dall'utente come variabile d'ambiente
- Il browser target supporta ES6+ e CSS Grid/Flexbox
- Il periodo di default per i report è 30 giorni
- La lingua di default per i report è italiano
