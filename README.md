# TRU - Truth Recursive Unit

A self-evolving knowledge engine with primaries ingestion, contradiction detection, and symbol traceability.

## What is this?

TRU is a system that separates:
- **TRUTH** - immutable primary sources (SEC filings, arxiv papers, Temple Institute posts)
- **CURRENT_EVENTS** - live telemetry with cross-corroboration
- **SYMBOL** - generative frameworks that can never modify primaries

## What's included

### Primary Data Ingestion
- `primaries/edgar_pull.py` - SEC EDGAR filings scraper
- `primaries/temple_pull.py` - Temple Institute posts scraper
- `primaries/arxiv_pull.py` - arXiv papers scraper
- `primaries/rss_pull.py` - RSS feeds with corroboration

### Contradiction Detection
- `primaries/contradiction_scanner.py` - Scans SYMBOL claims against TRUTH primaries

### Symbol Management
- `primaries/symbol_manager.py` - Manages symbol content with traceability

## Current State

As of June 2026:
- 2,364 primary sources cached
- 118 SEC filings (NVIDIA, Apple, Microsoft, Meta, etc.)
- 10 Temple Institute posts
- 2,236 arXiv papers
- 97 RSS current events

## APIs

All routes are live at: https://splashdown2.zo.space

- `GET /api/primaries` - Query primary sources
- `GET /api/current-events` - Live telemetry
- `GET /api/contradiction-report` - Contradiction scan results
- `GET /api/symbol-trace` - Symbol content traceability

## Quick Start

```bash
# Pull fresh primaries
cd primaries
python3 edgar_pull.py pull
python3 temple_pull.py pull
python3 arxiv_pull.py pull

# Run contradiction scanner
python3 contradiction_scanner.py scan

# Audit symbol content
python3 symbol_manager.py audit
```

## Documentation

See `Projects/TRU/` for full documentation.

---

Built with Zo Computer - https://splashdown2.zo.computer