#!/usr/bin/env python3
"""
Contradiction scanner for TRU.
Compares SYMBOL channel claims against TRUTH channel primaries.
Flags contradictions and confidence gaps.

Usage:
  python contradiction_scanner.py scan
  python contradiction_scanner.py status
  python contradiction_scanner.py list

Output: /home/workspace/Projects/TRU/cache/contradiction_report.json
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

PRIMARIES_DIR = Path("/home/workspace/primaries")
SYMBOL_DIR = PRIMARIES_DIR / "symbol"
CACHE_DIR = Path("/home/workspace/Projects/TRU/cache")
OUTPUT_FILE = CACHE_DIR / "contradiction_report.json"

# Keywords that indicate temporal/event claims
TEMPORAL_KEYWORDS = [
    "has happened", "is happening", "will happen", "occurred", "announced",
    "launched", "released", "deployed", "achieved", "completed", "started",
]

# Keywords that indicate factual claims  
FACTUAL_KEYWORDS = [
    "is the", "are the", "was the", "were the", "has", "have", 
    "exists", "located", "contains", "consists of",
]

VERDICTS = {
    "VERIFIED": "claim confirmed by primary source",
    "CORROBORATED": "claim supported by multiple primaries",
    "SYMBOL_WITH_EVIDENCE": "symbolic claim has primary backing",
    "NON_FALSIFIABLE": "claim is metaphorical/speculative, not verifiable",
    "CONTRADICTION": "claim contradicts primary source",
    "INSUFFICIENT_EVIDENCE": "no primary sources found to verify",
}


def load_primaries():
    """Load all TRUTH channel data."""
    primaries = {"sec": [], "temple": [], "arxiv": [], "current_events": []}
    
    # SEC filings
    sec_file = PRIMARIES_DIR / "sec" / "sec_merged.json"
    if sec_file.exists():
        with open(sec_file) as f:
            primaries["sec"] = json.load(f)
    
    # Temple posts
    temple_file = PRIMARIES_DIR / "temple" / "temple_posts.json"
    if temple_file.exists():
        with open(temple_file) as f:
            primaries["temple"] = json.load(f)
    
    # arxiv papers
    arxiv_file = PRIMARIES_DIR / "arxiv" / "arxiv_papers.json"
    if arxiv_file.exists():
        with open(arxiv_file) as f:
            primaries["arxiv"] = json.load(f)
    
    # Current events
    events_file = PRIMARIES_DIR / "current_events" / "rss_cache.json"
    if events_file.exists():
        with open(events_file) as f:
            primaries["current_events"] = json.load(f)
    
    return primaries


def load_symbol_claims():
    """Load SYMBOL channel claims."""
    claims = []
    
    # Check for symbol content
    claims_file = SYMBOL_DIR / "symbol_claims.json"
    if claims_file.exists():
        try:
            with open(claims_file) as fp:
                data = json.load(fp)
                if isinstance(data, list):
                    claims.extend(data)
        except Exception as e:
            print(f"[scanner] error loading symbol claims: {e}")
    
    # Return defaults if no claims found
    if not claims:
        return defaults()
    
    return claims


def defaults():
    """Default SYMBOL claims for testing."""
    return [
        {
            "id": "SYM-001",
            "claim": "The red heifer program is actively monitored in Shiloh",
            "category": "temple",
            "source": "MarineMechanic narrative",
            "type": "event",
        },
        {
            "id": "SYM-002", 
            "claim": "Anthropic was acquired in 2026",
            "category": "ai_industry",
            "source": "speculative interpretation",
            "type": "factual",
        },
        {
            "id": "SYM-003",
            "claim": "NVIDIA has achieved AGI",
            "category": "ai_technology",
            "source": "singularity discourse",
            "type": "factual",
        },
        {
            "id": "SYM-004",
            "claim": "The singularity is here",
            "category": "ai_technology",
            "source": "Diamandis messaging",
            "type": "interpretive",
        },
        {
            "id": "SYM-005",
            "claim": "Newton predicted the end times in 2060",
            "category": "prophecy",
            "source": "historical interpretation",
            "type": "interpretive",
        },
    ]


def search_primaries(primaries, query):
    """Search primary sources for evidence."""
    results = []
    query_lower = query.lower()
    keywords = re.findall(r'\w+', query_lower)
    
    # Search SEC
    for item in primaries.get("sec", []):
        text = json.dumps(item).lower()
        matches = sum(1 for k in keywords if k in text)
        if matches >= 2:
            results.append({
                "source": "sec_edgar",
                "type": "filing",
                "company": item.get("company", ""),
                "url": item.get("url", ""),
                "relevance": matches / len(keywords),
            })
    
    # Search Temple
    for item in primaries.get("temple", []):
        text = (item.get("title", "") + " " + item.get("content", "")).lower()
        matches = sum(1 for k in keywords if k in text)
        if matches >= 2:
            results.append({
                "source": "temple_institute",
                "type": "post",
                "title": item.get("title", ""),
                "url": item.get("link", item.get("url", "")),
                "relevance": matches / len(keywords),
            })
    
    # Search arxiv
    for item in primaries.get("arxiv", []):
        text = (item.get("title", "") + " " + item.get("summary", "")).lower()
        matches = sum(1 for k in keywords if k in text)
        if matches >= 2:
            results.append({
                "source": "arxiv",
                "type": "paper",
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "relevance": matches / len(keywords),
            })
    
    return sorted(results, key=lambda x: x["relevance"], reverse=True)


def classify_claim(claim_text, claim_type):
    """Determine if a claim can be verified."""
    claim_lower = claim_text.lower()
    
    # Check for temporal claims
    for kw in TEMPORAL_KEYWORDS:
        if kw in claim_lower:
            return "temporal"
    
    # Check for factual claims
    for kw in FACTUAL_KEYWORDS:
        if kw in claim_lower:
            return "factual"
    
    # Default based on metadata
    return claim_type if claim_type else "interpretive"


def verify_claim(claim, primaries):
    """Verify a single claim against primaries."""
    claim_text = claim.get("claim", "")
    claim_id = claim.get("id", "unknown")
    claim_type = claim.get("type", "interpretive")
    category = claim.get("category", "general")
    
    classified_type = classify_claim(claim_text, claim_type)
    evidence = search_primaries(primaries, claim_text)
    
    verdict = "INSUFFICIENT_EVIDENCE"
    confidence = 0.0
    contradiction = None
    
    # Check for contradictions FIRST before any other verdicts
    claim_lower = claim_text.lower()
    
    # Explicit contradiction patterns
    # "no X" claims when primaries contain X
    if "no active" in claim_lower and "red heifer" in claim_lower:
        temple_evidence = [e for e in evidence if e["source"] == "temple_institute"]
        if temple_evidence:
            for item in primaries.get("temple", []):
                content = item.get("content", "").lower()
                if "red heifer" in content:
                    contradiction = {
                        "description": "Claim contradicts Temple Institute primary sources about red heifer program",
                        "primary_source": "templeinstitute.org",
                    }
                    verdict = "CONTRADICTION"
                    confidence = 0.85
                    break
    
    # "no X" when X exists in SEC
    if "no X" in claim_lower:
        pass  # placeholder for future logic
    
    # Acquisition check (SEC would have S-1)
    if "acquired" in claim_lower or "acquisition" in claim_lower:
        sec_evidence = [e for e in evidence if e["source"] == "sec_edgar"]
        s1_filings = [e for e in sec_evidence if "s-1" in str(e).lower()]
        if not s1_filings and "anthropic" in claim_lower:
            # Search SEC specifically for Anthropic S-1
            for item in primaries.get("sec", []):
                if "anthropic" in str(item).lower():
                    evidence.append({
                        "source": "sec_edgar",
                        "type": "s-1_check",
                        "note": "Anthropic S-1 exists - check acquisition status",
                        "url": item.get("url", ""),
                        "relevance": 0.9,
                    })
    
    # AGI claims
    if "agi" in claim_lower or "achieved" in claim_lower:
        if "nvidia" in claim_lower:
            # Check SEC filings for AGI claims
            for item in primaries.get("sec", []):
                if item.get("company", "").lower() == "nvidia corp":
                    content = json.dumps(item).lower()
                    if "agi" in content and "achieved" not in content:
                        contradiction = {
                            "description": "NVIDIA filings mention AGI research but no 'achieved AGI' claim found",
                            "primary_source": "SEC 10-K/10-Q filings",
                        }
                        verdict = "CONTRADICTION"
                        break
    
    # Temple/heifer claims
    if "red heifer" in claim_lower or "shiloh" in claim_lower:
        if verdict != "CONTRADICTION":  # Don't override contradiction
            temple_evidence = [e for e in evidence if e["source"] == "temple_institute"]
            if temple_evidence:
                # Check if claim says "no red heifer" while evidence shows content
                if "no red heifer" in claim_lower or "no heifer" in claim_lower:
                    verdict = "CONTRADICTION"
                    confidence = 0.9
                    contradiction = {
                        "description": "Claim denies red heifer program but Temple Institute has active content",
                        "primary_source": "Temple Institute posts",
                    }
                # Check for number contradictions
                number_match = re.search(r'(\d+)\s+(?:red\s+)?heifer', claim_lower)
                if number_match:
                    claimed_count = int(number_match.group(1))
                    # Search temple content for actual numbers
                # Check for "actively monitored" language
                for item in primaries.get("temple", []):
                    content = item.get("content", "").lower()
                    if "red heifer" in content:
                        if "shiloh" in content:
                            verdict = "CORROBORATED"
                            confidence = 0.85
                        elif "monitor" not in content:
                            verdict = "VERIFIED"
                            confidence = 0.7
    
    # Singularity claims - interpretive by nature
    if "singularity" in claim_lower:
        verdict = "NON_FALSIFIABLE"
        confidence = 0.5
        classified_type = "interpretive"
    
    # Prophecy claims - interpretive
    if "prophecy" in claim_lower or "predicted" in claim_lower:
        verdict = "NON_FALSIFIABLE"
        confidence = 0.6
        classified_type = "interpretive"
    
    # Set default verdicts based on evidence
    if verdict == "INSUFFICIENT_EVIDENCE" and evidence:
        if len(evidence) >= 2:
            verdict = "SYMBOL_WITH_EVIDENCE"
            confidence = 0.65
        else:
            verdict = "INSUFFICIENT_EVIDENCE"
            confidence = 0.3
    
    return {
        "claim_id": claim_id,
        "claim": claim_text,
        "category": category,
        "type": classified_type,
        "verdict": verdict,
        "verdict_description": VERDICTS.get(verdict, ""),
        "confidence": confidence,
        "evidence": evidence[:5],
        "contradiction": contradiction,
    }


def scan():
    """Run contradiction scan."""
    print("[scanner] loading primaries...")
    primaries = load_primaries()
    
    total_primaries = (
        len(primaries.get("sec", [])) +
        len(primaries.get("temple", [])) +
        len(primaries.get("arxiv", []))
    )
    print(f"[scanner] loaded {total_primaries} primary sources")
    
    print("[scanner] loading symbol claims...")
    claims = load_symbol_claims()
    print(f"[scanner] loaded {claims.len() if hasattr(claims, 'len') else len(claims)} symbol claims")
    
    results = []
    summary = {
        "total": len(claims),
        "verified": 0,
        "corroborated": 0,
        "symbol_with_evidence": 0,
        "non_falsifiable": 0,
        "contradiction": 0,
        "insufficient_evidence": 0,
    }
    
    print("[scanner] verifying claims...")
    for claim in claims:
        result = verify_claim(claim, primaries)
        results.append(result)
        
        # Update summary
        v = result["verdict"]
        if v in summary:
            summary[v] = summary.get(v, 0) + 1
        summary[v.lower()] = summary.get(v.lower(), 0) + 1
    
    # Sort by confidence
    results.sort(key=lambda x: x["confidence"], reverse=True)
    
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "primaries_loaded": total_primaries,
        "summary": summary,
        "results": results,
    }
    
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"[scanner] done: {summary['contradiction']} contradictions found")
    print(f"[scanner] report: {OUTPUT_FILE}")
    return report


def status():
    """Show scanner status."""
    if not OUTPUT_FILE.exists():
        print("No report found. Run 'scan' first.")
        return
    
    with open(OUTPUT_FILE) as f:
        report = json.load(f)
    
    print(f"Last scan: {report.get('generated_at', 'unknown')}")
    print(f"Primaries loaded: {report.get('primaries_loaded', 0)}")
    print(f"\nSummary:")
    s = report.get("summary", {})
    print(f"  Total claims: {s.get('total', 0)}")
    print(f"  Verified: {s.get('verified', 0)}")
    print(f"  Corroborated: {s.get('corroborated', 0)}")
    print(f"  Symbol with evidence: {s.get('symbol_with_evidence', 0)}")
    print(f"  Non-falsifiable: {s.get('non_falsifiable', 0)}")
    print(f"  Contradictions: {s.get('contradiction', 0)}")
    print(f"  Insufficient evidence: {s.get('insufficient_evidence', 0)}")


def list_results():
    """List scan results."""
    if not OUTPUT_FILE.exists():
        print("No report found. Run 'scan' first.")
        return
    
    with open(OUTPUT_FILE) as f:
        report = json.load(f)
    
    results = report.get("results", [])
    print(f"Results ({len(results)} claims):\n")
    
    for r in results:
        v = r["verdict"]
        c = r["confidence"]
        marker = "⚠️" if v == "CONTRADICTION" else "✓" if v in ["VERIFIED", "CORROBORATED"] else "?"
        print(f"  {marker} [{v}] {r['claim'][:60]}")
        print(f"     confidence: {c:.2f} | type: {r['type']}")
        if r.get("contradiction"):
            print(f"     ⚠️ {r['contradiction']['description']}")
        print()


if __name__ == "__main__":
    import sys
    
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    
    if cmd == "scan":
        scan()
    elif cmd == "status":
        status()
    elif cmd == "list":
        list_results()
    else:
        print(f"Unknown command: {cmd}")
