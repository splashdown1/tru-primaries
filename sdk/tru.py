"""
TRU Python SDK - Truth Recursive Unit
Simple client for querying TRU primaries and checking contradictions.

Usage:
    from tru import TRU
    
    tru = TRU()
    
    # Search primaries
    results = tru.search("nvidia AI", limit=10)
    
    # Verify a claim
    verdict = tru.verify("NVIDIA has achieved AGI")
    print(verdict.verdict)  # INSUFFICIENT_EVIDENCE
    
    # Get primaries stats
    stats = tru.stats()
    print(stats.total_cached)  # 2364
"""

import urllib.request
import urllib.parse
import json
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

DEFAULT_BASE_URL = "https://splashdown2.zo.space"


@dataclass
class SearchResult:
    source_type: str
    title: str
    snippet: str
    date: str
    source_url: str
    score: float


@dataclass
class Verdict:
    claim: str
    verdict: str
    confidence: float
    evidence_count: int
    contradiction: Optional[Dict[str, str]]


@dataclass
class Stats:
    total_cached: int
    sec_filings: int
    temple_posts: int
    arxiv_papers: int


class TRU:
    """TRU API Client"""
    
    def __init__(self, base_url: str = DEFAULT_BASE_URL):
        self.base_url = base_url.rstrip("/")
    
    def _get(self, path: str, params: Optional[Dict] = None) -> Any:
        url = f"{self.base_url}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    
    def search(self, query: str, limit: int = 10, source_type: str = "") -> List[SearchResult]:
        """Search TRU primaries for matching content."""
        params = {"q": query, "limit": limit}
        if source_type:
            params["source_type"] = source_type
        
        data = self._get("/api/primaries", params)
        
        results = []
        for item in data.get("results", []):
            results.append(SearchResult(
                source_type=item.get("source_type", ""),
                title=item.get("title", ""),
                snippet=item.get("snippet", ""),
                date=item.get("date", ""),
                source_url=item.get("source_url", ""),
                score=item.get("score", 0),
            ))
        
        return results
    
    def stats(self) -> Stats:
        """Get TRU primaries statistics."""
        data = self._get("/api/primaries", {"limit": 1})
        s = data.get("stats", {})
        return Stats(
            total_cached=s.get("total_cached", 0),
            sec_filings=s.get("sec_filings", 0),
            temple_posts=s.get("temple_posts", 0),
            arxiv_papers=s.get("arxiv_papers", 0),
        )
    
    def verify(self, claim: str) -> Verdict:
        """
        Verify a claim against TRU primaries.
        Returns a verdict with confidence and evidence.
        """
        # Run contradiction scan on-the-fly
        # For now, search for related primaries
        results = self.search(claim, limit=5)
        
        # Simple heuristic: if we find evidence, it's "SYMBOL_WITH_EVIDENCE"
        # If we find direct contradiction keywords, it's "CONTRADICTION"
        # Otherwise, it's "INSUFFICIENT_EVIDENCE"
        
        verdict = "INSUFFICIENT_EVIDENCE"
        confidence = 0.0
        contradiction = None
        
        if results:
            # Check for contradictions
            claim_lower = claim.lower()
            
            # "no X" patterns
            if "no " in claim_lower and results:
                verdict = "CONTRADICTION"
                confidence = 0.8
                contradiction = {
                    "description": f"Claim denies existence but {len(results)} primaries found",
                    "source": "TRU primaries",
                }
            elif len(results) >= 2:
                verdict = "SYMBOL_WITH_EVIDENCE"
                confidence = 0.65
            else:
                verdict = "INSUFFICIENT_EVIDENCE"
                confidence = 0.3
        
        return Verdict(
            claim=claim,
            verdict=verdict,
            confidence=confidence,
            evidence_count=len(results),
            contradiction=contradiction,
        )
    
    def contradictions(self) -> List[Dict]:
        """Get latest contradiction scan results."""
        data = self._get("/api/contradiction-report")
        return data.get("results", [])
    
    def symbol_trace(self, action: str = "list") -> Dict:
        """Query symbol traceability."""
        return self._get("/api/symbol-trace", {"action": action})
    
    def current_events(self, limit: int = 20) -> List[Dict]:
        """Get current events from RSS feeds."""
        data = self._get("/api/current-events", {"source_type": "rss", "limit": limit})
        return data.get("items", [])


# Convenience function
def verify(claim: str) -> Verdict:
    """Quick verify a claim against TRU primaries."""
    return TRU().verify(claim)


if __name__ == "__main__":
    # Demo
    tru = TRU()
    
    print("TRU Stats:")
    stats = tru.stats()
    print(f"  Total primaries: {stats.total_cached}")
    print(f"  SEC filings: {stats.sec_filings}")
    print(f"  arXiv papers: {stats.arxiv_papers}")
    print()
    
    print("Searching 'nvidia AI':")
    results = tru.search("nvidia AI", limit=3)
    for r in results:
        print(f"  [{r.source_type}] {r.title[:60]}")
    print()
    
    print("Verifying claim: 'NVIDIA has achieved AGI'")
    v = tru.verify("NVIDIA has achieved AGI")
    print(f"  Verdict: {v.verdict}")
    print(f"  Confidence: {v.confidence:.2f}")
    print(f"  Evidence: {v.evidence_count} sources")
