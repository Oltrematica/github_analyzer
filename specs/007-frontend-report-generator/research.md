# Research: Frontend Report Generator

**Feature**: 007-frontend-report-generator
**Date**: 2025-11-29
**Status**: Complete

## Research Areas

### 1. Perplexity API Integration

**Decision**: Utilizzare Perplexity Chat Completions API con modello `llama-3.1-sonar-small-128k-online`

**Rationale**:
- API REST standard compatibile con pattern esistente in `api/client.py`
- Modello "small" sufficiente per analisi metriche strutturate, costo contenuto
- Supporto nativo JSON output tramite system prompt strutturato
- Rate limit documentato: ~20 RPM per tier free, gestibile con cache 24h

**Alternatives considered**:
- OpenAI GPT-4: Costo maggiore, non necessario per task analitico
- Claude API: Overhead licensing, Perplexity più semplice per use case specifico
- Analisi locale senza AI: Perde valore qualitativo, feedback non actionable

**Implementation notes**:
```python
# Endpoint: https://api.perplexity.ai/chat/completions
# Auth: Bearer token via PERPLEXITY_API_KEY env var
# Response parsing: JSON from content field
# Cache: File-based JSON con hash dei dati input come chiave
```

### 2. Fuzzy Matching per User Mapping

**Decision**: Utilizzare `difflib.SequenceMatcher` dalla standard library

**Rationale**:
- Zero dipendenze aggiuntive (constitution principle: core con stdlib)
- Sufficiente per matching nomi/username con threshold 0.7+
- Algoritmo Ratcliff/Obershelp ben documentato e prevedibile
- Fallback manuale sempre disponibile per edge cases

**Alternatives considered**:
- `python-Levenshtein`: Performance migliore ma dipendenza esterna
- `fuzzywuzzy`: Dipendenza con C extension, overhead per use case semplice
- `rapidfuzz`: Ottimo ma non necessario per <100 utenti

**Implementation notes**:
```python
from difflib import SequenceMatcher

def fuzzy_ratio(s1: str, s2: str) -> float:
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()

# Confidence levels:
# - 1.0: email exact match
# - 0.95: username identical
# - 0.7-0.9: name fuzzy match
# - 0.6: initials + surname pattern
```

### 3. HTML Template System

**Decision**: String templating con f-strings e manual escaping, no Jinja2

**Rationale**:
- Evita dipendenza esterna per template engine
- Output HTML è statico una volta generato, no server-side rendering
- Riuso pattern di `html.escape()` per XSS prevention
- Template components come file .html con placeholder `{variable}`

**Alternatives considered**:
- Jinja2: Potente ma dipendenza extra per template statici
- Mako: Overhead simile a Jinja2
- string.Template: Meno flessibile dei f-strings

**Implementation notes**:
```python
from html import escape

def render_template(template_path: Path, context: dict) -> str:
    template = template_path.read_text()
    # Escape all user-provided values
    safe_context = {k: escape(str(v)) for k, v in context.items()}
    return template.format(**safe_context)
```

### 4. Chart.js Integration

**Decision**: Chart.js 4.x inline via CDN URL nell'HTML, configurazione JSON embedded

**Rationale**:
- Libreria standard de facto per chart web interattivi
- CDN evita bundling, HTML rimane standalone
- Configurazione dichiarativa JSON facilmente generabile da Python
- Responsive out-of-box con `maintainAspectRatio: false`

**Alternatives considered**:
- D3.js: Più potente ma curva di apprendimento ripida, overkill
- Plotly: Pesante, dipendenze multiple
- ApexCharts: Buono ma meno diffuso di Chart.js
- Chart da CSS/SVG puro: Limitato per interattività

**Implementation notes**:
```html
<!-- CDN inline nel template -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>

<!-- Config generata da Python -->
<script>
const chartConfig = {CHART_CONFIG_JSON};
new Chart(document.getElementById('myChart'), chartConfig);
</script>
```

### 5. YAML Configuration

**Decision**: Aggiungere PyYAML come dipendenza opzionale per user mapping

**Rationale**:
- YAML più leggibile di JSON per file di configurazione editati manualmente
- PyYAML è maturo, well-maintained, ampiamente usato
- Fallback a JSON se PyYAML non disponibile
- Allineato con constitution: dipendenze opzionali gracefully degraded

**Alternatives considered**:
- JSON only: Meno user-friendly per editing manuale
- TOML: Meno diffuso, stdlib solo in Python 3.11+
- INI: Troppo limitato per strutture nested

**Implementation notes**:
```python
try:
    import yaml
    def load_mapping(path: Path) -> dict:
        return yaml.safe_load(path.read_text())
except ImportError:
    import json
    def load_mapping(path: Path) -> dict:
        return json.loads(path.read_text())
```

### 6. CSV Parsing Strategy

**Decision**: Riutilizzare strutture esistenti, parsing lazy con generatori

**Rationale**:
- CSV già prodotti da `exporters/csv_exporter.py` con schema noto
- Generatori per memoria efficiente con file grandi (12 mesi dati)
- Type conversion esplicita per date e numerici
- Gestione errori per righe malformate (skip + log)

**Alternatives considered**:
- pandas: Overkill, dipendenza pesante
- csv.DictReader: Già usato nel progetto, mantenere consistenza

**Implementation notes**:
```python
def parse_csv_lazy(path: Path) -> Iterator[dict]:
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                yield transform_row(row)
            except ValueError as e:
                logger.warning(f"Skipping malformed row: {e}")
```

### 7. Trend Calculation

**Decision**: Confronto period-over-period con stesso numero di giorni

**Rationale**:
- Semantica chiara: se period=30, confronta ultimi 30gg vs 30gg precedenti
- Percentuale variazione: `((current - previous) / previous) * 100`
- Gestione divisione per zero con fallback a "N/A" o "new"

**Alternatives considered**:
- Moving average: Più complesso, non richiesto dalla spec
- YoY comparison: Richiede più storico

**Implementation notes**:
```python
def calculate_trend(current: float, previous: float) -> dict:
    if previous == 0:
        return {"value": current, "trend": "new", "pct": None}
    pct = ((current - previous) / previous) * 100
    trend = "up" if pct > 0 else "down" if pct < 0 else "stable"
    return {"value": current, "trend": trend, "pct": round(pct, 1)}
```

### 8. Interactive Rate Limit Handling

**Decision**: CLI prompt con `input()` per scelta utente, timeout opzionale

**Rationale**:
- Spec richiede interattività (clarification Q1)
- Simple `input()` per CLI, no dipendenze UI
- Opzioni chiare: [W]ait / [S]kip
- Backoff esponenziale se utente sceglie wait

**Alternatives considered**:
- Auto-retry silenzioso: Non allineato con spec (richiesta interattiva)
- Abort completo: Troppo drastico, perde lavoro fatto

**Implementation notes**:
```python
def handle_rate_limit() -> str:
    print("\n⚠️  Rate limit raggiunto per Perplexity API")
    print("[W] Attendi e riprova (backoff automatico)")
    print("[S] Prosegui senza le sezioni AI rimanenti")
    choice = input("Scelta [W/S]: ").strip().upper()
    return choice if choice in ('W', 'S') else 'S'
```

## Dependencies Summary

### Required (già presenti)
- Python 3.9+
- requests (opzionale, già in requirements.txt)

### New Required
- PyYAML>=6.0 (per user mapping config)

### Frontend (CDN, no install)
- Chart.js 4.4.1

## Security Considerations

1. **Perplexity API Key**: Solo via `PERPLEXITY_API_KEY` env var, mai loggato
2. **HTML Output**: Escape di tutti i valori user-provided con `html.escape()`
3. **Path Validation**: Riuso `validate_output_path()` da `core/security.py`
4. **YAML Parsing**: Uso `yaml.safe_load()` per prevenire code injection

## Performance Estimates

| Operation | Estimated Time | Notes |
|-----------|---------------|-------|
| CSV parsing (12 mesi) | ~5s | Lazy loading, generatori |
| User mapping auto-match | ~1s | <30 utenti, O(n²) accettabile |
| Trend calculations | ~2s | Aggregazioni in memoria |
| Perplexity API calls | ~30-60s | 3-5 calls (team + membri), cached |
| HTML generation | ~3s | Template rendering + inline assets |
| **Total (no cache)** | **~70-90s** | Sotto target 2 min |
| **Total (with cache)** | **~15s** | AI results cached |
