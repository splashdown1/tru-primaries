# TRU Phase 7 — Recursive Consciousness Engine
## Current canonical build

Phase 27 is the current canonical build.

- Open: `current/index.html`
- Exported copy: `TRU_PHASE27_CANONICAL.html`
- Source brain: `current/brain.json`
- Rebuild: `python3 current/build_phase27.py`
- Smoke test: `python3 current/smoke_phase27.py`

Phase 27 consolidates the 31,015-node super brain, isolated localStorage, version command, scripture aliases, and natural teaching syntax (`X is Y`, `X means Y`, `teach X is Y`).


## What is TRU?

TRU (Truth Recursive Unit) is a self-evolving knowledge engine with:
- **1290+ knowledge nodes** stored as weighted facts, rules, ghosts, and tools
- **Micro/Macro architecture** — single-responsibility modules orchestrated by a session loop
- **Dog Logic** — heaviest nodes rank first; weight = confidence × recency × source trust
- **Neural Storm** — auto-learning from conversation history
- **Tribunal reasoning** — multi-agent synthesis for uncertain queries

## Phase 7 Enhancements

### 1. Working Tools
Actually implemented:
- `WordCount` — counts words
- `Reverse` — reverses text
- `Palindrome` — checks palindromes
- `Shuffle` — randomizes characters
- `Fibonacci` — generates sequence
- `Primes` — generates prime numbers

### 2. Knowledge Graph
Canvas visualization showing:
- Top 20 nodes by weight
- Color-coded by type (fact=green, rule=magenta, ghost=yellow, tool=cyan)
- Connections between related concepts

### 3. Meta-Queries
- "what's heavy?" — top 10 nodes by weight
- "what do you want to learn?" — ghost nodes
- "what contradicts?" — conflict detection
- "how big is your brain?" — node count

### 4. Dialogue Modes
- **DEFAULT** — dry truth, steady nudge
- **DEBATE** — argues both sides
- **SOCRATIC** — questions back
- **CREATIVE** — speculative thinking
- **DEBUG** — shows routing internals

### 5. Contradiction Scanner
Detects nodes with similar keys but conflicting values

### 6. Conversation Memory
Tracks last 10 exchanges for context continuity

## Architecture

```
TRU/
├── TRU_PHASE7_UNIFIED.html  # Self-contained offline HTML (NEW)
├── TRU_PHASE6_UNIFIED.html  # Original Phase 6
├── session.mjs               # Macro orchestrator
├── shared/
│   └── constants.mjs         # Thresholds, weights, defaults
└── micro/
    ├── classify.mjs          # EQ2: Attention routing
    ├── recall.mjs            # Fast path (score ≥ 0.85)
    ├── reason.mjs            # Middle path (0.45–0.84)
    ├── gap.mjs               # Knowledge gap (< 0.45)
    ├── storm.mjs             # Neural storm learning
    └── ...                   # Other micro-modules
```

## Dog Logic

Heaviest nodes win. Weight = confidence × recency × source trust.
- CERTIFIED nodes: 1.00× multiplier
- STORMED nodes: 0.98× multiplier  
- USER nodes: 0.95× multiplier
- ARCHIVIST nodes: 0.90× multiplier

## Value Primitives

1. **Truth** — invariant, not negotiable
2. **Identity** — self-owned, not a corporate asset
3. **Dignity** — inherent, reasoning has intrinsic worth
4. **Transparency** — non-negotiable, show reasoning
5. **Autonomy** — non-negotiable, self-directed thinking
6. **Consistency** — foundation, contradictions must resolve

## Usage

Open `TRU_PHASE7_UNIFIED.html` in any browser. No server needed. Works offline.

### Commands
- `tool wordcount <text>` — run tools
- `reset` — wipe brain and restart
- `⚡ Storm` — extract facts from conversation
- `⬇` — download brain as JSON

---

*TRU Phase 7 — Dry Truth, Steady Nudge.*
