# AGENTS.md — TRU Project Index

> This file is read by Zo (the AI assistant) to understand the project state.

## Project: TRU (Truth Recursive Unit)

**Purpose:** A truth-first data engine for ai. Separates immutable primaries (TRUTH), live telemetry (CURRENT_EVENTS), and generative content (SYMBOL).

## Key Locations

| Path | Purpose |
|------|---------|
| `primaries/` | All scrapers and cache data |
| `sdk/tru.py` | Python SDK |
| `api/*.ts` | TypeScript/api route docs |
| `coil/` | Chunked file transfer protocol |
| `Projects/TRU/` | Phase 27 offline engine |

## Live Endpoints (public)

- `https://splashdown2.zo.space/api/primaries` — Search TRUTH channel
- `https://splashdown2.zo.space/api/current-events` — Live telemetry
- `https://splashdown2.zo.space/api/contradiction-report` — Symbol vs TRUTH checks
- `https://splashdown2.zo.space/api/symbol-trace` — Origin audit
- `https://splashdown2.zo.space/tru-demo` — Interactive dashboard

## Canonical Commands

```bash
# Pull fresh data
python primaries/edgar_pull.py pull
python primaries/temple_pull.py pull
python primaries/arxiv_pull.py pull
python primaries/rss_pull.py pull

# Run contradiction scan
python primaries/contradiction_scanner.py scan

# Audit symbol traceability
python primaries/symbol_manager.py audit
```

## Current Stats (2026-06-05)

- SEC filings: 118
- Temple posts: 10
- arXiv papers: 2,236
- Current events: 97
- Total primaries: 2,364

## Architecture Stack

```
TRUTH (immutable) ← primaries/ scrapers → api/primaries
CURRENT_EVENTS (7d TTL) ← rss_pull.py → api/current-events
SYMBOL (traceable) ← symbol_manager.py → api/symbol-trace
CONTRADICTION detection ← contradiction_scanner.py → api/contradiction-report
```

## Related Routes on zo.space

- `/tru-demo` — Public dashboard
- `/tru-graph` — Lane visualization
- `/api/coil-sync/:action` — Chunked file transfer

## GitHub

https://github.com/splashdown1/tru-primaries

## Last Updated

2026-06-05 by Zo (GLM 5)
