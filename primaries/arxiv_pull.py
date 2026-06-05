"""
arxiv RSS puller for primaries cache.
Pulls recent papers from arxiv RSS feeds, caches locally.

Usage:
  python arxiv_pull.py pull [--categories cs.LG,cs.AI,cs.CL] [--days 30]
  python arxiv_pull.py list [--category cs.LG] [--limit 20]
  python arxiv_pull.py search <query>
  python arxiv_pull.py stats
"""

import json
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CACHE_DIR = Path("/home/workspace/primaries/arxiv")
USER_AGENT = "TRU Research research@tru.local"

DEFAULT_CATEGORIES = ["cs.LG", "cs.AI", "cs.CL", "cs.NE", "stat.ML"]


def fetch_rss(category: str) -> str:
    urls = [
        f"http://export.arxiv.org/rss/{category}",
        f"https://export.arxiv.org/rss/{category}",
    ]
    for url in urls:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8")
        except (HTTPError, URLError):
            continue
    print(f"[arxiv] fetch error for {category}")
    return ""


def parse_rss(xml_text: str, category: str) -> List[Dict]:
    papers = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return papers

    for item in root.findall(".//item"):
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "")
        desc = item.findtext("description", "")

        arxiv_id = ""
        if link:
            m = re.search(r"(\d{4}\.\d{4,5})", link)
            if m:
                arxiv_id = m.group(1)

        abstract = ""
        if desc:
            m = re.search(r"Abstract:\s*(.*)", desc, re.DOTALL)
            if m:
                abstract = m.group(1).strip()

        categories = [c.text for c in item.findall("category") if c.text]
        papers.append(
            {
                "arxiv_id": arxiv_id,
                "title": title,
                "abstract": abstract,
                "link": link,
                "category": category,
                "categories": categories,
                "pulled_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    return papers


def _load_category_index(out_dir: Path) -> List[Dict]:
    index_path = out_dir / "_index.json"
    if not index_path.exists():
        return []
    try:
        with open(index_path) as f:
            idx = json.load(f)
        return idx.get("papers", [])
    except Exception:
        return []


def _write_merge_cache() -> None:
    merged = []
    seen = set()
    for cat_dir in CACHE_DIR.iterdir() if CACHE_DIR.exists() else []:
        if not cat_dir.is_dir() or cat_dir.name.startswith("_"):
            continue
        for fp in cat_dir.glob("*.json"):
            if fp.name.startswith("_"):
                continue
            try:
                with open(fp) as f:
                    paper = json.load(f)
            except Exception:
                continue
            pid = paper.get("arxiv_id") or paper.get("id") or fp.stem
            if not pid or pid in seen:
                continue
            seen.add(pid)
            merged.append(
                {
                    "id": pid,
                    "title": paper.get("title", ""),
                    "authors": paper.get("authors", []),
                    "abstract": paper.get("abstract", ""),
                    "categories": paper.get("categories", [paper.get("category") or cat_dir.name]),
                    "published": paper.get("published") or paper.get("pulled_at", ""),
                    "updated": paper.get("updated") or paper.get("pulled_at", ""),
                    "link": paper.get("link") or f"https://arxiv.org/abs/{pid}",
                    "source_type": "arxiv",
                }
            )
    merged.sort(key=lambda p: p.get("published", ""), reverse=True)
    with open(CACHE_DIR / "arxiv_papers.json", "w") as f:
        json.dump(merged, f, indent=2)


def pull_category(category: str, days: int = 30) -> Dict:
    print(f"[arxiv] pulling {category}...")
    xml_text = fetch_rss(category)
    if not xml_text:
        return {"category": category, "count": 0, "papers": []}

    papers = parse_rss(xml_text, category)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    print(f"[arxiv] {category}: {len(papers)} papers")
    out_dir = CACHE_DIR / category.replace("/", "_")
    out_dir.mkdir(parents=True, exist_ok=True)

    for paper in papers:
        if not paper["arxiv_id"]:
            continue
        out_path = out_dir / f"{paper['arxiv_id']}.json"
        try:
            with open(out_path, "w") as f:
                json.dump(paper, f, indent=2)
        except Exception:
            pass

    index_path = out_dir / "_index.json"
    index = {
        "category": category,
        "pulled_at": datetime.now(timezone.utc).isoformat(),
        "count": len(papers),
        "cutoff_days": days,
        "papers": [{k: p[k] for k in ["arxiv_id", "title", "link"]} for p in papers],
    }
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)

    return index


def pull(categories: Optional[List[str]] = None, days: int = 30):
    categories = categories or DEFAULT_CATEGORIES
    results = []
    for cat in categories:
        results.append(pull_category(cat, days))
        time.sleep(1)

    total = sum(r["count"] for r in results)
    print(f"[arxiv] done: {total} papers across {len(categories)} categories")

    meta_path = CACHE_DIR / "_meta.json"
    meta = {
        "pulled_at": datetime.now(timezone.utc).isoformat(),
        "categories": categories,
        "total": total,
        "cutoff_days": days,
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    _write_merge_cache()
    return results


def list_papers(category: Optional[str] = None, limit: int = 20):
    papers = []
    for cat_dir in CACHE_DIR.iterdir():
        if not cat_dir.is_dir() or cat_dir.name.startswith("_"):
            continue
        if category and cat_dir.name != category.replace("/", "_"):
            continue
        index_path = cat_dir / "_index.json"
        if not index_path.exists():
            continue
        with open(index_path) as f:
            idx = json.load(f)
        papers.extend(idx.get("papers", []))

    papers = sorted(papers, key=lambda p: p.get("arxiv_id", ""), reverse=True)
    for p in papers[:limit]:
        print(f"  · [{p.get('arxiv_id', '?')}] {p.get('title', '?')[:60]}")

    return papers[:limit]


def search(query: str, limit: int = 10):
    q = query.lower()
    matches = []
    for cat_dir in CACHE_DIR.iterdir():
        if not cat_dir.is_dir() or cat_dir.name.startswith("_"):
            continue
        for fp in cat_dir.glob("*.json"):
            if fp.name.startswith("_"):
                continue
            try:
                with open(fp) as f:
                    paper = json.load(f)
            except Exception:
                continue
            text = f"{paper.get('title','')} {paper.get('abstract','')}".lower()
            if q in text:
                paper["match_score"] = text.count(q)
                matches.append(paper)

    matches = sorted(matches, key=lambda p: p.get("match_score", 0), reverse=True)
    for m in matches[:limit]:
        print(f"  · [{m.get('arxiv_id','?')}] {m.get('title','?')[:60]}")

    return matches[:limit]


def stats():
    if not CACHE_DIR.exists():
        print("No arxiv cache found.")
        return

    total = 0
    for cat_dir in CACHE_DIR.iterdir():
        if not cat_dir.is_dir() or cat_dir.name.startswith("_"):
            continue
        count = len([p for p in cat_dir.glob("*.json") if not p.name.startswith("_")])
        cat_name = cat_dir.name.replace("_", "/")
        print(f"  {cat_name}: {count} papers")
        total += count

    print(f"Total: {total} papers")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="arxiv RSS puller for primaries")
    sub = parser.add_subparsers(dest="cmd", required=True)

    pull_p = sub.add_parser("pull")
    pull_p.add_argument("--categories", help="comma-separated categories")
    pull_p.add_argument("--days", type=int, default=30)

    list_p = sub.add_parser("list")
    list_p.add_argument("--category")
    list_p.add_argument("--limit", type=int, default=20)

    search_p = sub.add_parser("search")
    search_p.add_argument("query")
    search_p.add_argument("--limit", type=int, default=10)

    sub.add_parser("stats")

    args = parser.parse_args()

    if args.cmd == "pull":
        cats = args.categories.split(",") if args.categories else None
        pull(cats, args.days)
    elif args.cmd == "list":
        list_papers(args.category, args.limit)
    elif args.cmd == "search":
        search(args.query, args.limit)
    elif args.cmd == "stats":
        stats()


if __name__ == "__main__":
    main()
