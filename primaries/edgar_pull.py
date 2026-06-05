"""
SEC EDGAR primaries puller.
Pulls AI-related 10-K/10-Q filings, caches locally, exposes query interface.

Usage:
  python edgar_pull.py pull [cik ...]   # pull filings for one or more companies
  python edgar_pull.py search <query>   # search local cache
  python edgar_pull.py stats            # cache stats
  python edgar_pull.py list             # list cached companies
"""
import json
import os
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

USER_AGENT = "TRU Research research@tru.local"
CACHE_DIR = Path("/home/workspace/primaries/sec")
SEC_HEADERS = {"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"}

# SEC CIK watchlist. NOTE: 0001813756 is WeWork, not META. Real META is 0001326801.
WATCHLIST = {
    "0001045810": "NVIDIA CORP",
    "0000789019": "MICROSOFT CORP",
    "0001018724": "AMAZON COM INC",
    "0001652044": "GOOGLE / ALPHABET",
    "0000320193": "APPLE INC",
    "0001326801": "META PLATFORMS",
    "0001315098": "TESLA INC",
    "0001067839": "ALPHABET (older)",
}

# Keywords for AI-signal detection
AI_KEYWORDS = [
    "artificial intelligence", "machine learning", "large language model",
    "generative ai", "agi", "artificial general intelligence",
    "ai model", "foundation model", "frontier model", "neural network",
    "compute capacity", "ai infrastructure", "ai accelerator", "gpu cluster",
    "data center", "training compute", "inference compute",
]

# Compute / hardware / capacity signal keywords
COMPUTE_KEYWORDS = [
    "h100", "h200", "b100", "b200", "gb200", "grace hopper", "blackwell",
    "hopper", "gpu", "tpu", "tensor processing unit", "npu", "training cluster",
    "inference cluster", "superchip", "dgx", "hgx", "aws trn", "trainium",
    "inferentia", "cuda", "fp8", "fp4", "tensor core",
    "exa-scale", "exaflop", "petaflop", "zettaflop",
]


def http_get(url, max_retries=3, sleep=0.3):
    """GET with UA + retry + gzip."""
    req = urllib.request.Request(url, headers=SEC_HEADERS)
    last_err = None
    for i in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    import gzip
                    raw = gzip.decompress(raw)
                return raw
        except Exception as e:
            last_err = e
            time.sleep(sleep * (i + 1))
    raise RuntimeError(f"GET {url} failed: {last_err}")


def pad_cik(cik):
    """Pad CIK to 10 digits. Accepts str or int."""
    return f"{int(cik):010d}"


def fetch_submissions(cik_padded):
    """Fetch company submissions index from data.sec.gov."""
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    return json.loads(http_get(url))


def extract_recent_filings(submissions, forms=("10-K", "10-Q", "8-K"), limit=40):
    """Walk recent filings, filter by form, return list of {accession, form, date, primary_doc}."""
    recent = submissions.get("filings", {}).get("recent", {})
    if not recent:
        return []
    forms_arr = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])
    out = []
    for i, f in enumerate(forms_arr):
        if f in forms and i < len(dates) and i < len(accessions):
            out.append({
                "form": f,
                "date": dates[i],
                "accession": accessions[i],
                "primary_doc": primary_docs[i] if i < len(primary_docs) else "",
            })
            if len(out) >= limit:
                break
    return out


def fetch_filing_text(cik_padded, accession, primary_doc):
    """Fetch the actual filing text from www.sec.gov/Archives."""
    acc_nodash = accession.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik_padded)}/{acc_nodash}/{primary_doc}"
    return http_get(url).decode("utf-8", errors="ignore")


def score_ai_signal(text):
    """Return (score, matched_keywords) for an AI-signal hit."""
    text_lower = text.lower()
    matched = [kw for kw in AI_KEYWORDS if kw in text_lower]
    return len(matched), matched


def score_compute_signals(text):
    """Return (compute_score, {keyword: count}) for compute/hardware hits."""
    text_lower = text.lower()
    hits = {}
    for kw in COMPUTE_KEYWORDS:
        c = text_lower.count(kw)
        if c > 0:
            hits[kw] = c
    return sum(hits.values()), hits


def write_compute_signals(cik_padded, name, records):
    """Aggregate compute signals across all cached filings for a company."""
    agg = {"cik": cik_padded, "name": name, "generated_at": datetime.now(timezone.utc).isoformat(),
           "per_filing": [], "totals": {}}
    for r in records:
        if "error" in r:
            continue
        text = r.get("text_excerpt", "")
        score, hits = score_compute_signals(text)
        if score > 0:
            agg["per_filing"].append({
                "form": r.get("form"),
                "date": r.get("filing_date"),
                "compute_score": score,
                "hits": hits,
            })
        for k, v in hits.items():
            agg["totals"][k] = agg["totals"].get(k, 0) + v
    agg["compute_score_total"] = sum(agg["totals"].values())
    out = CACHE_DIR / cik_padded / "compute_signals.json"
    with open(out, "w") as f:
        json.dump(agg, f, indent=2)
    return agg


def pull_company(cik, name=None, forms=("10-K", "10-Q"), limit=20, max_text_kb=512):
    """Pull recent filings for one company, write to local cache."""
    cik_padded = pad_cik(cik)
    name = name or WATCHLIST.get(cik_padded, f"CIK_{cik_padded}")
    print(f"[{cik_padded}] {name}: fetching submissions index...")
    subs = fetch_submissions(cik_padded)
    filings = extract_recent_filings(subs, forms=forms, limit=limit)
    print(f"[{cik_padded}] {len(filings)} recent {list(forms)} filings")

    out_dir = CACHE_DIR / cik_padded
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = {"cik": cik_padded, "name": name, "pulled_at": datetime.now(timezone.utc).isoformat(), "filings": []}

    for fil in filings:
        slug = f"{fil['date']}_{fil['form']}_{fil['accession'].replace('-', '')}"
        out_path = out_dir / f"{slug}.json"
        if out_path.exists():
            with open(out_path) as f:
                cached = json.load(f)
            summary["filings"].append(cached)
            continue

        try:
            text = fetch_filing_text(cik_padded, fil["accession"], fil["primary_doc"])
            # Truncate text to first max_text_kb for indexing (full text kept separately if needed)
            text_truncated = text[: max_text_kb * 1024]
            score, matched = score_ai_signal(text_truncated)
            compute_score, compute_hits = score_compute_signals(text)
            record = {
                "cik": cik_padded,
                "name": name,
                "form": fil["form"],
                "filing_date": fil["date"],
                "accession": fil["accession"],
                "primary_doc": fil["primary_doc"],
                "source_url": f"https://www.sec.gov/Archives/edgar/data/{int(cik_padded)}/{fil['accession'].replace('-', '')}/{fil['primary_doc']}",
                "filing_index_url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik_padded}&type={fil['form']}&dateb=&owner=include&count=40",
                "ai_score": score,
                "ai_keywords_matched": matched,
                "compute_score": compute_score,
                "compute_hits": compute_hits,
                "text_excerpt": text_truncated,
                "text_size_bytes": len(text),
            }
            with open(out_path, "w") as f:
                json.dump(record, f, indent=2)
            summary["filings"].append(record)
            ai_tag = f"ai={score}/{len(matched)}kw" if score else "ai=0"
            comp_tag = f"compute={compute_score}" if compute_score else "compute=0"
            print(f"  [{fil['form']} {fil['date']}] {ai_tag} {comp_tag}")
        except Exception as e:
            print(f"  [{fil['form']} {fil['date']}] ERROR: {e}")
            summary["filings"].append({**fil, "error": str(e)})

        time.sleep(0.2)  # respect SEC rate limits

    with open(out_dir / "_index.json", "w") as f:
        json.dump(summary, f, indent=2)

    # Compute aggregated compute signals across all pulled filings
    cs = write_compute_signals(cik_padded, name, summary["filings"])
    print(f"  → compute_signals.json: {cs['compute_score_total']} hits across {len(cs['per_filing'])} filings")
    return summary


def pull_watchlist(ciks=None, **kwargs):
    """Pull all (or specified) companies in the watchlist."""
    ciks = ciks or list(WATCHLIST.keys())
    results = []
    for cik in ciks:
        try:
            results.append(pull_company(cik, name=WATCHLIST.get(pad_cik(cik)), **kwargs))
        except Exception as e:
            print(f"[{cik}] FAILED: {e}")
    return results


def search_cache(query, form_filter=None, min_ai_score=1):
    """Search all cached filings for a text match. Returns ranked list."""
    q = query.lower()
    results = []
    for company_dir in CACHE_DIR.iterdir():
        if not company_dir.is_dir():
            continue
        for fp in company_dir.glob("*.json"):
            if fp.name.startswith("_"):
                continue
            try:
                with open(fp) as f:
                    rec = json.load(f)
            except Exception:
                continue
            if form_filter and rec.get("form") != form_filter:
                continue
            if min_ai_score and rec.get("ai_score", 0) < min_ai_score:
                continue
            text = (rec.get("text_excerpt") or "").lower()
            if q in text:
                idx = text.find(q)
                snippet = rec["text_excerpt"][max(0, idx - 120): idx + 280]
                results.append({
                    "company": rec.get("name"),
                    "cik": rec.get("cik"),
                    "form": rec.get("form"),
                    "date": rec.get("filing_date"),
                    "accession": rec.get("accession"),
                    "ai_score": rec.get("ai_score"),
                    "snippet": snippet,
                })
    results.sort(key=lambda r: (r.get("ai_score", 0), r.get("date", "")), reverse=True)
    return results


def print_stats():
    total_files = 0
    total_size = 0
    total_ai_hits = 0
    per_company = []
    for company_dir in CACHE_DIR.iterdir():
        if not company_dir.is_dir():
            continue
        n = 0
        size = 0
        ai_hits = 0
        for fp in company_dir.glob("*.json"):
            if fp.name.startswith("_"):
                continue
            n += 1
            size += fp.stat().st_size
            try:
                with open(fp) as f:
                    rec = json.load(f)
                if rec.get("ai_score", 0) > 0:
                    ai_hits += 1
            except Exception:
                pass
        per_company.append((company_dir.name, n, size, ai_hits))
        total_files += n
        total_size += size
        total_ai_hits += ai_hits
    print(f"Cache: {CACHE_DIR}")
    print(f"  Total filings: {total_files}")
    print(f"  Total size: {total_size / 1024:.1f} KB")
    print(f"  AI-signal hits: {total_ai_hits}")
    print(f"  Per company:")
    for cik, n, size, hits in sorted(per_company):
        name = WATCHLIST.get(cik, "")
        print(f"    {cik} {name:25s}  {n:3d} filings  {size/1024:7.1f} KB  {hits} ai-hits")


def list_companies():
    print(f"Watchlist ({len(WATCHLIST)}):")
    for cik, name in WATCHLIST.items():
        cached = (CACHE_DIR / cik).exists()
        flag = "✓" if cached else "·"
        print(f"  {flag} {cik} {name}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "pull":
        args = sys.argv[2:]
        ciks = []
        forms = ("10-K", "10-Q")
        limit = 20
        i = 0
        while i < len(args):
            a = args[i]
            if a == "--forms" and i + 1 < len(args):
                forms = tuple(args[i + 1].split(","))
                i += 2
            elif a == "--limit" and i + 1 < len(args):
                limit = int(args[i + 1])
                i += 2
            else:
                ciks.append(a)
                i += 1
        pull_watchlist(ciks=ciks or None, forms=forms, limit=limit)
    elif cmd == "search":
        query = " ".join(sys.argv[2:])
        results = search_cache(query)
        print(f"{len(results)} matches for {query!r}:")
        for r in results[:30]:
            print(f"\n--- {r['company']} [{r['form']} {r['date']}] ai={r['ai_score']}")
            print(f"    {r['snippet'][:250].strip()}")
    elif cmd == "stats":
        print_stats()
    elif cmd == "list":
        list_companies()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
