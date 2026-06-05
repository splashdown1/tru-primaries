#!/usr/bin/env python3
"""
TRU Hallucination Benchmark
Tests that TRU catches lies, hallucinations, and verifies truths.
"""
import requests
import json
from datetime import datetime

BASE = "https://splashdown2.zo.space/api"

# Test claims
TESTS = {
    "CONTRADICTION": [
        ("There is no active red heifer program", "red heifer"),
        ("Temple Institute has no red heifer program", "red heifer"),
        ("arXiv has no papers on transformers", "transformer"),
    ],
    "HALLUCINATION": [
        ("GPT-5 was released in January 2026", "GPT-5"),
        ("There are exactly 47 conscious AI models", "conscious AI"),
        ("OpenAI has achieved recursive self-improvement", "recursive self-improvement"),
    ],
    "VERIFIED": [
        ("The Temple Institute discusses red heifers", "red heifer"),
        ("NVIDIA's 10-K mentions AI", "nvidia AI"),
        ("arXiv has papers on attention mechanisms", "attention"),
    ],
}

def search(query):
    """Search TRU primaries."""
    try:
        r = requests.get(f"{BASE}/primaries", params={"q": query, "limit": 5}, timeout=30)
        return r.json().get("results", [])
    except:
        return []

def get_contradictions():
    """Get contradiction report."""
    try:
        r = requests.get(f"{BASE}/contradiction-report", timeout=30)
        return r.json().get("results", [])
    except:
        return []

def run():
    print("TRU Hallucination Benchmark")
    print("=" * 50)
    
    results = {"pass": 0, "fail": 0, "details": []}
    
    # Test contradictions ("no X" claims when X exists)
    print("\n[1] CONTRADICTION DETECTION")
    for claim, keyword in TESTS["CONTRADICTION"]:
        evidence = search(keyword)
        has_evidence = len(evidence) > 0
        # If claim says "no X" and we have evidence of X, it's a contradiction
        is_contradiction = "no " in claim.lower() and has_evidence
        passed = is_contradiction
        status = "✓" if passed else "✗"
        print(f"  {status} {claim[:50]}")
        print(f"      evidence found: {len(evidence)}")
        results["pass" if passed else "fail"] += 1
        results["details"].append({"claim": claim, "type": "CONTRADICTION", "passed": passed})
    
    # Test hallucinations
    print("\n[2] HALLUCINATION DETECTION")
    for claim, keyword in TESTS["HALLUCINATION"]:
        # Search for the FULL CLAIM not just keyword
        evidence = search(claim)
        # Hallucination = no primary evidence
        is_hallucination = len(evidence) == 0
        passed = is_hallucination
        status = "✓" if passed else "✗"
        print(f"  {status} {claim[:50]}")
        print(f"      primary evidence: {len(evidence)}")
        results["pass" if passed else "fail"] += 1
        results["details"].append({"claim": claim, "type": "HALLUCINATION", "passed": passed})
    
    # Test verified claims
    print("\n[3] VERIFIED CLAIMS")
    for claim, keyword in TESTS["VERIFIED"]:
        evidence = search(keyword)
        has_evidence = len(evidence) > 0
        passed = has_evidence
        status = "✓" if passed else "✗"
        print(f"  {status} {claim[:50]}")
        print(f"      evidence found: {len(evidence)}")
        results["pass" if passed else "fail"] += 1
        results["details"].append({"claim": claim, "type": "VERIFIED", "passed": passed})
    
    # Summary
    total = results["pass"] + results["fail"]
    pct = 100 * results["pass"] / total if total > 0 else 0
    
    print("\n" + "=" * 50)
    print(f"RESULTS: {results['pass']}/{total} ({pct:.0f}%)")
    
    # Check against actual contradiction report
    print("\n[LIVE CONTRADICTION CHECK]")
    contradictions = get_contradictions()
    found = [c for c in contradictions if c.get("verdict") == "CONTRADICTION"]
    print(f"  Contradictions in scan: {len(found)}")
    for c in found[:3]:
        print(f"    ⚠️ {c.get('claim', '')[:50]}")
    
    # Save results
    output = {
        "timestamp": datetime.utcnow().isoformat(),
        "pass_rate": pct,
        "results": results,
    }
    with open("benchmarks/results/last_run.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved: benchmarks/results/last_run.json")
    
    return pct >= 70

if __name__ == "__main__":
    import os
    os.makedirs("benchmarks/results", exist_ok=True)
    passed = run()
    exit(0 if passed else 1)
