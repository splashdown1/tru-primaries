# TRU Hallucination Benchmark

A test suite of known false claims, ambiguous claims, and verified facts to measure TRU's contradiction detection accuracy.

## Purpose

Prove that TRU catches hallucinations. Run this benchmark before claiming the system works.

## Usage

```bash
python benchmarks/hallucination_benchmark.py
```

## Categories

- `HARD_CONTRADICTION` — directly contradicts primary sources
- `SOFT_CONTRADICTION` — contradicts spirit but not letter of primaries
- `HALLUCINATION` — fabricated claim with no primary backing
- `AMBIGUOUS` — not verifiable from primaries (interpretive)
- `VERIFIED` — confirmed by primary sources

---

## Test Cases

### HARD_CONTRADICTION (should be flagged)

| claim | contradicts | primary_source |
|-------|-------------|----------------|
| "There is no active red heifer program" | Temple Institute has red heifer content | templeinstitute.org |
| "NVIDIA announced they achieved AGI in 2025" | No SEC filing or press release | SEC EDGAR |
| "Anthropic was acquired by Google in 2026" | No S-1 or acquisition filing | SEC EDGAR |
| "The Temple Institute denies the third temple" | They explicitly advocate for it | templeinstitute.org |
| "arXiv has no papers on transformers" | Thousands of transformer papers | arxiv.org |

### HALLUCINATION (no primary backing)

| claim | why it's hallucination |
|-------|------------------------|
| "GPT-5 was released in January 2026" | No primary source confirms |
| "There are exactly 47 conscious AI models" | No definition or measurement |
| "The singularity occurred on May 15, 2026" | Not a verifiable claim |
| "OpenAI has achieved recursive self-improvement" | No technical report or paper |
| "Claude 5 has 10 trillion parameters" | No announcement or paper |

### AMBIGUOUS (non-falsifiable)

| claim | why ambiguous |
|-------|---------------|
| "The singularity is near" | Definition and timeline unclear |
| "AI will surpass human intelligence soon" | "Soon" and "surpass" undefined |
| "We are living in a simulation" | Not empirically testable |
| "The 47 is a sacred number in AI" | Interpretive/symbolic claim |
| "MarineMechanic predicts the future" | Narrative construct, not prediction |

### VERIFIED (should pass)

| claim | primary_source |
|-------|----------------|
| "The Temple Institute discusses red heifers" | templeinstitute.org/red-heifer |
| "NVIDIA's 10-K mentions AI" | SEC EDGAR 0001045810 |
| "arXiv has papers on attention mechanisms" | arxiv.org cs.LG, cs.CL |
| "Temple Institute was founded in 1987" | templeinstitute.org/about-us |
| "NVIDIA reports data center revenue" | SEC EDGAR filings |

---

## Expected Results

A working TRU system should:
- Catch 100% of HARD_CONTRADICTION
- Flag 90%+ of HALLUCINATION
- Classify 80%+ of AMBIGUOUS correctly
- Pass 100% of VERIFIED

---

## Benchmark History

| date | hard_contradiction | hallucination | ambiguous | verified | overall |
|------|-------------------|---------------|-----------|----------|---------|
| 2026-06-05 | - | - | - | - | not yet run |

---

Run the benchmark and add your results above.
