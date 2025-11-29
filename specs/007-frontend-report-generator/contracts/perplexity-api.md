# API Contract: Perplexity AI Integration

**Feature**: 007-frontend-report-generator
**Date**: 2025-11-29
**Status**: Complete

## Overview

Integrazione con Perplexity Chat Completions API per generare analisi qualitative delle metriche del team.

## External API: Perplexity

### Endpoint

```
POST https://api.perplexity.ai/chat/completions
```

### Authentication

```
Authorization: Bearer {PERPLEXITY_API_KEY}
```

Environment variable: `PERPLEXITY_API_KEY`

### Request Schema

```json
{
  "model": "llama-3.1-sonar-large-128k-online",
  "messages": [
    {
      "role": "system",
      "content": "string - system prompt defining response format"
    },
    {
      "role": "user",
      "content": "string - metrics data and analysis request"
    }
  ],
  "max_tokens": 1024,
  "temperature": 0.2
}
```

### Response Schema

```json
{
  "id": "string",
  "model": "string",
  "object": "chat.completion",
  "created": 1234567890,
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "string - JSON response from AI"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 123,
    "completion_tokens": 456,
    "total_tokens": 579
  }
}
```

### Error Responses

| Status | Description | Handling |
|--------|-------------|----------|
| 401 | Invalid API key | Abort with clear error message |
| 429 | Rate limit exceeded | Interactive prompt: wait or skip |
| 500 | Server error | Retry with backoff, then skip |
| 503 | Service unavailable | Retry with backoff, then skip |

## Internal API Contracts

### PerplexityClient

```python
class PerplexityClient:
    """Client for Perplexity AI API integration."""

    def __init__(
        self,
        api_key: str | None = None,  # Falls back to env var
        cache_dir: Path | None = None,
        cache_ttl_hours: int = 24
    ) -> None: ...

    def analyze_team(
        self,
        metrics: TeamStats,
        member_metrics: list[dict]
    ) -> AIInsight | None:
        """
        Generate AI analysis for team performance.

        Args:
            metrics: Aggregated team statistics
            member_metrics: List of member metric summaries

        Returns:
            AIInsight if successful, None if API unavailable

        Raises:
            RateLimitError: When rate limit hit (caller handles interactively)
        """
        ...

    def analyze_member(
        self,
        member: TeamMember,
        team_averages: dict
    ) -> AIInsight | None:
        """
        Generate AI analysis for individual team member.

        Args:
            member: Team member with metrics
            team_averages: Team average metrics for comparison

        Returns:
            AIInsight if successful, None if API unavailable
        """
        ...

    def analyze_project(
        self,
        project: Project
    ) -> AIInsight | None:
        """
        Generate AI analysis for project health.

        Args:
            project: Project with quality metrics

        Returns:
            AIInsight if successful, None if API unavailable
        """
        ...
```

### Prompt Templates

#### Team Analysis Prompt

```python
TEAM_ANALYSIS_SYSTEM = """
Sei un esperto di engineering management e DevOps metrics.
Analizza i dati forniti e rispondi SOLO in formato JSON strutturato.
Usa italiano. Sii conciso e actionable.

Formato risposta richiesto:
{
  "rating": "B+",  // A, A-, B+, B, B-, C+, C, C-, D, F
  "strengths": ["punto 1", "punto 2", "punto 3"],
  "improvements": ["area 1", "area 2", "area 3"],
  "red_flags": ["flag 1"],  // solo se critici, max 3
  "recommendations": ["azione 1", "azione 2"],
  "summary": "Valutazione complessiva in 2-3 frasi."
}
"""

TEAM_ANALYSIS_USER = """
Analizza le seguenti metriche del team di sviluppo:

**Metriche Team:**
- Resolution rate: {resolution_rate}%
- Cycle time medio: {cycle_time} giorni
- Bug resolution time: {bug_time} giorni
- WIP totale: {wip_count} task

**Breakdown per membro:**
{member_breakdown}

**Trend vs periodo precedente:**
{trends}

Fornisci analisi strutturata secondo il formato richiesto.
"""
```

#### Member Analysis Prompt

```python
MEMBER_ANALYSIS_USER = """
Valuta le performance di {member_name}:

**Metriche personali:**
- Task assegnati: {assigned}
- Task risolti: {resolved}
- Cycle time: {cycle_time} giorni
- WIP corrente: {wip}
- Bug gestiti: {bugs}

**Confronto con media team:**
- Cycle time medio team: {team_avg_cycle}
- Resolution rate medio: {team_avg_resolution}%

Fornisci valutazione individuale secondo il formato richiesto.
"""
```

### Response Parsing

```python
def parse_ai_response(content: str) -> AIInsight:
    """
    Parse AI response content into AIInsight.

    Args:
        content: Raw response content from API

    Returns:
        Parsed AIInsight object

    Raises:
        ValueError: If response is not valid JSON or missing required fields
    """
    # Extract JSON from response (may be wrapped in markdown code blocks)
    json_match = re.search(r'\{[\s\S]*\}', content)
    if not json_match:
        raise ValueError("No JSON found in response")

    data = json.loads(json_match.group())

    # Validate required fields
    required = ['rating', 'strengths', 'improvements', 'summary']
    missing = [f for f in required if f not in data]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    # Convert rating to numeric
    rating_map = {
        'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0, 'B-': 2.7,
        'C+': 2.3, 'C': 2.0, 'C-': 1.7, 'D': 1.0, 'F': 0.0
    }

    return AIInsight(
        rating=data['rating'],
        rating_numeric=rating_map.get(data['rating'], 2.0),
        strengths=data['strengths'][:5],
        improvements=data['improvements'][:5],
        red_flags=data.get('red_flags', [])[:3],
        recommendations=data.get('recommendations', [])[:4],
        summary=data['summary'],
        generated_at=datetime.now(),
        model="llama-3.1-sonar-large-128k-online",
        prompt_hash=compute_hash(content)
    )
```

### Caching Contract

```python
class AICache:
    """File-based cache for AI responses."""

    def __init__(self, cache_dir: Path, ttl_hours: int = 24) -> None: ...

    def get(self, prompt_hash: str) -> AIInsight | None:
        """Get cached insight if exists and not expired."""
        ...

    def set(self, prompt_hash: str, insight: AIInsight) -> None:
        """Store insight in cache."""
        ...

    def compute_hash(self, metrics_data: dict) -> str:
        """Compute deterministic hash from input metrics."""
        ...
```

Cache file format: `{cache_dir}/ai_cache_{prompt_hash}.json`

### Rate Limit Handling

```python
class RateLimitError(Exception):
    """Raised when Perplexity API rate limit is hit."""

    def __init__(self, retry_after: int | None = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after}s")


def handle_rate_limit_interactive() -> Literal['wait', 'skip']:
    """
    Interactive prompt for rate limit handling.

    Returns:
        'wait' to retry with backoff, 'skip' to continue without AI
    """
    print("\n⚠️  Rate limit raggiunto per Perplexity API")
    print("[W] Attendi e riprova (backoff automatico)")
    print("[S] Prosegui senza le sezioni AI rimanenti")

    while True:
        choice = input("Scelta [W/S]: ").strip().upper()
        if choice in ('W', 'S'):
            return 'wait' if choice == 'W' else 'skip'
        print("Scelta non valida. Inserisci W o S.")
```

## CLI Contract

### Report Generator CLI

```python
@click.command()
@click.option('--period', '-p', default=30, help='Analysis period in days')
@click.option('--output', '-o', type=click.Path(), help='Output directory')
@click.option('--sources', '-s', default='github,jira', help='Data sources (comma-separated)')
@click.option('--user-mapping', '-m', type=click.Path(exists=True), help='User mapping YAML file')
@click.option('--ai/--no-ai', default=True, help='Enable/disable AI analysis')
@click.option('--config', '-c', type=click.Path(exists=True), help='Report config YAML')
def generate_report(
    period: int,
    output: str | None,
    sources: str,
    user_mapping: str | None,
    ai: bool,
    config: str | None
) -> None:
    """Generate interactive HTML performance report."""
    ...
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | User error (invalid args, missing files) |
| 2 | System error (API failure, IO error) |

### Progress Output

```
📊 Report Generator v1.0.0
══════════════════════════════════════════════════════

[1/5] Loading CSV data...
      ✓ commits_export.csv (1,234 records)
      ✓ pull_requests_export.csv (456 records)
      ✓ jira_issues_export.csv (789 records)

[2/5] Processing user mappings...
      ✓ 5 confirmed mappings loaded
      ⚠ 2 unconfirmed mappings require attention
      → Running interactive reconciliation...

[3/5] Aggregating metrics...
      ✓ Team stats calculated
      ✓ Individual metrics computed
      ✓ Trends calculated (vs previous 30 days)

[4/5] Generating AI insights...
      ✓ Team analysis complete
      ✓ Member analysis: 4/4 complete
      ✓ Project analysis: 2/2 complete

[5/5] Generating HTML report...
      ✓ Template rendered
      ✓ Charts configured
      ✓ Assets inlined

══════════════════════════════════════════════════════
✅ Report generated successfully!

   Output: ./frontend/reports/2025-11-29/index.html
   Size: 1.2 MB
   Time: 45 seconds
```
