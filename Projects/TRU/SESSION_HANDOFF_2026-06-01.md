# TRU Session Handoff — 2026-06-01

## What Was Built

### 1. Primaries Ingestion Layer

Three hardened pullers for primary signal:

| Source | Script | Cache Location |
|--------|--------|----------------|
| SEC EDGAR | `file '/home/workspace/primaries/edgar_pull.py'` | `primaries/sec/` |
| Temple Institute | `file '/home/workspace/primaries/temple_pull.py'` | `primaries/temple/temple_posts.json` |
| arXiv | `file '/home/workspace/primaries/arxiv_pull.py'` | `primaries/arxiv/` |

Each produces a merged JSON cache that the API can read directly.

### 2. Unified API Endpoint

**`/api/primaries`** — https://splashdown2.zo.space/api/primaries

Query params:
- `?q=<text>` — full-text search
- `?source_type=sec|temple|arxiv` — filter by source
- `?company=<name>` — filter SEC filings by company
- `?form=10-K|10-Q` — filter by form type
- `?min_ai_score=N` — minimum AI keyword hits
- `?min_compute_score=N` — minimum compute signal hits
- `?sort=date|ai_score|compute_score` — sort order
- `?limit=N` — max results (default 50)

Returns:
```json
{
  "query": { ... },
  "total": 127,
  "results": [ ... ],
  "stats": {
    "sec_filings": 89,
    "temple_posts": 12,
    "arxiv_papers": 26,
    "total_cached": 127
  }
}
```

### 3. Lane Graph Visualization

**`/tru-graph`** — https://splashdown2.zo.space/tru-graph

Visualises the three channels defined in the ingestion spec:

| Lane | Description | Verification |
|------|-------------|--------------|
| **TRUTH** | Immutable Primary Sources | Cryptographic / Deterministic |
| **CURRENT_EVENTS** | Live Primary Signal | Temporal Consensus (N≥2) |
| **SYMBOL** | Generative Myth Engine | Internal Coherence |

Features:
- Live cache stats pulled from `/api/primaries`
- Search interface for querying primaries
- Processing rules for each lane

### 4. Ingestion Spec

**`file '/home/workspace/Projects/TRU/ingestion_spec.json'`**

Defines:
- Channel structure (TRUTH, CURRENT_EVENTS, SYMBOL, UNKNOWN)
- Processing rules per channel
- Routing logic for incoming signals

---

## Key Architecture Decisions

1. **Separation of primaries from lore**
   - SEC filings, Temple posts, arxiv papers → TRUTH channel
   - MarineMechanic arcs, Newton 2060, singularity lore → SYMBOL channel
   - Never mix in the same output

2. **No LLM transformation on primaries**
   - Extract raw tokens only
   - Preserve source URLs
   - Timestamp mandatory

3. **Compute signals tracked separately**
   - GPU mentions (H100, H200, B100, B200, GB200, etc.)
   - Training/inference cluster references
   - Aggregated per-company in `compute_signals.json`

---

## Verified Signals (June 2026)

From the web search verification:

| Claim | Status | Notes |
|-------|--------|-------|
| Peter Diamandis "singularity is HERE" | ✓ Real | Actual messaging, but marketing layer |
| Anthropic S-1 / SEC filing | ✓ Real | Primary source material |
| Temple Institute red heifer program | ✓ Real | Ongoing, not prophecy fulfillment |
| Isaac Newton 2060 prophecy | ✓ Real | Historical material, 2026 displacement is interpretation |
| MarineMechanic X account | ✓ Real | But the ARG layer is generative, not primary |

---

## Next Steps

1. **Add more primaries sources**
   - News wires (Reuters, AP)
   - Status pages (OpenAI, Anthropic, Cloudflare)
   - Developer blogs (Google AI, Meta AI)

2. **Build CURRENT_EVENTS ingestion**
   - RSS feeds with 7-day expiry
   - Cross-corroboration requirement (N≥2)

3. **Symbol traceability**
   - Tag generated content with origin
   - Never modify primary values

4. **Contradiction detection**
   - Flag when SYMBOL contradicts TRUTH
   - Surface to `/tru-graph` dashboard

---

## Quick Commands

```bash
# Pull SEC filings for watchlist
python /home/workspace/primaries/edgar_pull.py pull

# Pull Temple Institute posts
python /home/workspace/primaries/temple_pull.py pull

# Pull arxiv papers
python /home/workspace/primaries/arxiv_pull.py pull

# Check primaries stats
curl https://splashdown2.zo.space/api/primaries?limit=1 | jq .stats

# Search primaries
curl "https://splashdown2.zo.space/api/primaries?q=nvidia+gpu&limit=10"
```

---

## Related Routes

- `/tru` — Holographic sovereign (six-layer 3D visualization)
- `/api/tru-reason` — Unified reasoning engine (scripture / brain / greek / primaries)
- `/api/tru-chat` — Chat interface to TRU
- `/api/tru-brain` — Brain node lookup
- `/api/coil-sync/:action` — COIL synchronization

---

*Session: 2026-06-01*
*Model: GLM 5*
