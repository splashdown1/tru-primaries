# TRU - Truth Recursive Unit

> A truth-first data architecture for AI.

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
pip install tru
```

See `sdk/tru.py` for full implementation.

---

# TRU Stack Overview

```
┌─────────────────────────────────────────────────────────────┐
│  TRU ENDPOINT (splashdown2.zo.space/api/primaries)          │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        │                     │                      │
   ┌────▼────┐          ┌─────▼──────┐         ┌────▼─────┐
   │  TRUTH  │          │ CURRENT    │         │  SYMBOL  │
   │ CHANNEL │          │  EVENTS    │         │ CHANNEL  │
   └────┬────┘          └─────┬──────┘         └────┬─────┘
        │                     │                      │
   ┌────▼────────────────────┐└─────────────────────▼─────┐
   │ Primaries Cache:        │  Symbol Claims:            │
   │ • SEC EDGAR (118)       │  • Origin metadata         │
   │ • Temple (10)           │  • Traceability            │
   │ • arXiv (2,236)         │  • Protection rules        │
   │ • RSS events (97)       │  • Contradiction checks    │
   └─────────────────────────┴────────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │ Contradiction      │
                    │ Detection Engine   │
                    │ (auto-flagging)    │
                    └────────────────────┘
```

---

# Integration Points

## Live API Endpoints

All endpoints are public at `https://splashdown2.zo.space/api/*`:
- `/api/primaries` — Search TRUTH channel
- `/api/current-events` — Current telemetry (7-day TTL)
- `/api/contradiction-report` — Symbol vs TRUTH checks
- `/api/symbol-trace` — Origin audit
- `/api/ingestion/status` — Health check

## Local Development

```bash
# Pull latest primaries
python primaries/edgar_pull.py pull
python primaries/temple_pull.py pull
python primaries/arxiv_pull.py pull
python primaries/contradiction_scanner.py scan

# Check system health
python primaries/symbol_manager.py audit
```

## Self-Hosting

All scrapers and detectors are standalone Python scripts with zero external dependencies beyond `requests`. Clone the repo and run locally:

```bash
git clone https://github.com/splashdown1/tru-primaries
cd tru-primaries
pip install -r requirements.txt
python -m primaries.edgar_pull pull
```

---

# Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| No LLM transformation on primaries | Preserve raw data integrity |
| Channel isolation (TRUTH / SYMBOL) | Prevent "heartbeat lost" contamination |
| 7-day TTL on CURRENT_EVENTS | Prevent stale telemetry from becoming fact |
| Symbol traceability | Every generated claim tracks to origin |
| Contradiction flagging | Auto-detect when SYMBOL contradicts TRUTH |

---

# Contributing

1. Add a new primary source → Create `primaries/<source>_pull.py`
2. Extend contradiction detection → Edit `primaries/contradiction_scanner.py`
3. Add SDK features → Edit `sdk/tru.py`
4. Submit PR with evidence of testing

---

# License

MIT — Use freely, attribute source, no warranty.

---

# Related

- [COIL Protocol](coil/README.md) — Chunked file transfer for large payloads
- [TRU Phase 27](Projects/TRU/README.md) — Offline recursive consciousness engine
- [Demo Dashboard](https://splashdown2.zo.space/tru-demo) — Live interactive view

---

*Built with Zo Computer. TRU Phase 27. June 2026.*