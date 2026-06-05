#!/usr/bin/env python3
"""
RSS feed puller for CURRENT_EVENTS channel.
Pulls from news wires, applies 7-day expiry, requires N≥2 corroboration.

Usage:
  python rss_pull.py pull
  python rss_pull.py list
  python rss_pull.py stats
  python rss_pull.py search <query>

Data stored in: /home/workspace/primaries/current_events/rss_cache.json
"""

import json
import re
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import xml.etree.ElementTree as ET

CACHE_DIR = Path("/home/workspace/primaries/current_events")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
RSS_CACHE_FILE = CACHE_DIR / "rss_cache.json"
CORROBORATED_FILE = CACHE_DIR / "corroborated_events.json"

USER_AGENT = "TRU Research research@tru.local"

# RSS feeds for news wires and AI/tech news
RSS_FEEDS = [
    # AI/Tech focused (working feeds)
    {"name": "techcrunch_ai", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "tier": 2},
    {"name": "wired_ai", "url": "https://www.wired.com/feed/tag/ai/latest/rss", "tier": 2},
    {"name": "arstechnica_ai", "url": "https://feeds.arstechnica.com/arstechnica/technology-lab", "tier": 2},
    {"name": "openai_blog", "url": "https://openai.com/blog/rss.xml", "tier": 1},
    {"name": "google_ai_blog", "url": "https://blog.google/technology/ai/rss/", "tier": 1},
    {"name": "deepmind_blog", "url": "https://deepmind.com/blog/rss.xml", "tier": 1},
    {"name": "mit_tech_review", "url": "https://www.technologyreview.com/feed/", "tier": 2},
    {"name": "hacker_news", "url": "https://hnrss.org/frontpage", "tier": 2},
    {"name": "ai_news", "url": "https://artificialintelligence-news.com/feed/", "tier": 2},
]

EXPIRY_DAYS = 7
MIN_CORROBORATION = 2


def fetch_rss(url):
    """Fetch RSS feed content."""
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml, text/xml"})
    try:
        with urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except (HTTPError, URLError) as e:
        print(f"  error fetching {url}: {e}")
        return ""


def parse_rss(xml_content, source_name):
    """Parse RSS XML and extract items."""
    items = []
    try:
        root = ET.fromstring(xml_content)
        
        # Handle different RSS formats
        channel = root.find("channel")
        if channel is None:
            channel = root
        
        # Find all item elements
        for item in channel.findall(".//item"):
            title_elem = item.find("title")
            link_elem = item.find("link")
            desc_elem = item.find("description")
            pubdate_elem = item.find("pubDate")
            
            title = title_elem.text if title_elem is not None and title_elem.text else ""
            link = link_elem.text if link_elem is not None and link_elem.text else ""
            desc = desc_elem.text if desc_elem is not None and desc_elem.text else ""
            pubdate = pubdate_elem.text if pubdate_elem is not None and pubdate_elem.text else ""
            
            if title and link:
                # Generate a stable ID from title
                item_id = hashlib.md5(title.encode()).hexdigest()[:12]
                
                items.append({
                    "id": item_id,
                    "title": title,
                    "link": link,
                    "description": re.sub(r"<[^>]+>", "", desc)[:1000],  # Strip HTML
                    "pubdate": pubdate,
                    "source": source_name,
                    "pulled_at": datetime.now(timezone.utc).isoformat(),
                })
    except ET.ParseError as e:
        print(f"  parse error for {source_name}: {e}")
    
    return items


def extract_key_entities(title, description=""):
    """Extract named entities for corroboration matching (company names, products, key terms)."""
    # Known AI/tech entities to track
    entities = {
        "openai", "anthropic", "google", "deepmind", "meta", "microsoft", "nvidia",
        "claude", "gpt", "chatgpt", "gemini", "llama", "copilot", "midjourney",
        "stable diffusion", "dall-e", "sora", "whisper", 
        "ai", "artificial intelligence", "machine learning", "ml", "llm", 
        "transformer", "neural network", "deep learning",
        "agi", "artificial general intelligence",
        "h100", "h200", "gpu", "chip", "semiconductor",
        "training", "inference", "model", "benchmark",
    }
    
    text = f"{title} {description}".lower()
    found = set()
    
    for entity in entities:
        if entity in text:
            found.add(entity)
    
    # Also extract capitalized words (likely entities)
    caps = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", title)
    for cap in caps:
        if len(cap) > 3:
            found.add(cap.lower())
    
    return found


def find_corroboration(items):
    """Find items that appear in multiple sources (N≥2 corroboration)."""
    # Group by key entities
    entity_groups = {}
    
    for item in items:
        entities = extract_key_entities(item["title"], item.get("description", ""))
        if len(entities) >= 1:
            # Use frozenset of entities as signature
            sig = frozenset(entities)
            if sig not in entity_groups:
                entity_groups[sig] = []
            entity_groups[sig].append(item)
    
    # Find corroborated items
    corroborated = []
    seen_ids = set()
    
    for sig, group in entity_groups.items():
        if len(group) >= MIN_CORROBORATION:
            # Multiple sources mention same entities
            sources = list(set(item["source"] for item in group))
            if len(sources) >= MIN_CORROBORATION:
                # Pick the item with most entities matched
                primary = max(group, key=lambda x: len(extract_key_entities(x["title"], x.get("description", ""))))
                
                if primary["id"] not in seen_ids:
                    seen_ids.add(primary["id"])
                    corroborated.append({
                        **primary,
                        "corroboration_count": len(sources),
                        "corroboration_sources": sources,
                        "corroboration_ids": [item["id"] for item in group],
                        "matched_entities": list(sig),
                        "channel": "CURRENT_EVENTS",
                        "verified": True,
                    })
    
    return corroborated


def apply_expiry(items):
    """Remove items older than EXPIRY_DAYS."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=EXPIRY_DAYS)
    fresh = []
    
    for item in items:
        try:
            # Try to parse pubdate
            if item.get("pubdate"):
                # Try various date formats
                for fmt in [
                    "%a, %d %b %Y %H:%M:%S %z",
                    "%a, %d %b %Y %H:%M:%S GMT",
                    "%Y-%m-%dT%H:%M:%SZ",
                    "%Y-%m-%dT%H:%M:%S%z",
                ]:
                    try:
                        dt = datetime.strptime(item["pubdate"], fmt)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        if dt > cutoff:
                            fresh.append(item)
                        break
                    except ValueError:
                        continue
                else:
                    # Couldn't parse date, use pulled_at
                    if item.get("pulled_at"):
                        pulled = datetime.fromisoformat(item["pulled_at"].replace("Z", "+00:00"))
                        if pulled > cutoff:
                            fresh.append(item)
            else:
                # No pubdate, check pulled_at
                if item.get("pulled_at"):
                    pulled = datetime.fromisoformat(item["pulled_at"].replace("Z", "+00:00"))
                    if pulled > cutoff:
                        fresh.append(item)
        except Exception:
            # If we can't parse, keep it (will be filtered next pull)
            fresh.append(item)
    
    return fresh


def pull():
    """Pull all RSS feeds and build corroborated events."""
    print("[rss] pulling feeds...")
    
    all_items = []
    
    for feed in RSS_FEEDS:
        print(f"[rss] {feed['name']}...")
        xml = fetch_rss(feed["url"])
        if xml:
            items = parse_rss(xml, feed["name"])
            print(f"  {len(items)} items")
            all_items.extend(items)
    
    print(f"[rss] total items: {len(all_items)}")
    
    # Apply 7-day expiry
    fresh_items = apply_expiry(all_items)
    print(f"[rss] after expiry filter: {len(fresh_items)}")
    
    # Find corroborated events
    corroborated = find_corroboration(fresh_items)
    print(f"[rss] corroborated (N≥{MIN_CORROBORATION}): {len(corroborated)}")
    
    # Save raw cache
    cache_doc = {
        "pulled_at": datetime.now(timezone.utc).isoformat(),
        "total_items": len(fresh_items),
        "feeds": [{"name": f["name"], "url": f["url"]} for f in RSS_FEEDS],
        "items": fresh_items,
    }
    with open(RSS_CACHE_FILE, "w") as f:
        json.dump(cache_doc, f, indent=2)
    
    # Save corroborated events
    corrob_doc = {
        "pulled_at": datetime.now(timezone.utc).isoformat(),
        "count": len(corroborated),
        "min_corroboration": MIN_CORROBORATION,
        "expiry_days": EXPIRY_DAYS,
        "items": corroborated,
    }
    with open(CORROBORATED_FILE, "w") as f:
        json.dump(corrob_doc, f, indent=2)
    
    print(f"[rss] done: {len(corroborated)} corroborated events")
    return corroborated


def list_items():
    """List cached items."""
    if not RSS_CACHE_FILE.exists():
        print("No cache found. Run 'pull' first.")
        return []
    
    with open(RSS_CACHE_FILE) as f:
        doc = json.load(f)
    
    print(f"Cached items: {doc.get('total_items', 0)}")
    print(f"Corroborated: {len(doc.get('items', []))}")
    
    if CORROBORATED_FILE.exists():
        with open(CORROBORATED_FILE) as f:
            corrob = json.load(f)
        print(f"\nCorroborated events ({corrob.get('count', 0)}):")
        for item in corrob.get("items", [])[:20]:
            print(f"  [{item.get('corroboration_count', 0)}] {item['title'][:70]}")
            print(f"      sources: {', '.join(item.get('corroboration_sources', []))}")
    
    return doc.get("items", [])


def stats():
    """Show cache stats."""
    if not RSS_CACHE_FILE.exists():
        print("No cache found.")
        return
    
    with open(RSS_CACHE_FILE) as f:
        doc = json.load(f)
    
    items = doc.get("items", [])
    print(f"Total items: {len(items)}")
    print(f"Feeds: {len(doc.get('feeds', []))}")
    print(f"Last pull: {doc.get('pulled_at', 'unknown')}")
    
    # Source breakdown
    sources = {}
    for item in items:
        src = item.get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1
    
    print("\nBy source:")
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"  {src}: {count}")
    
    if CORROBORATED_FILE.exists():
        with open(CORROBORATED_FILE) as f:
            corrob = json.load(f)
        print(f"\nCorroborated events: {corrob.get('count', 0)}")


def search(query):
    """Search cached items."""
    if not RSS_CACHE_FILE.exists():
        print("No cache found. Run 'pull' first.")
        return []
    
    with open(RSS_CACHE_FILE) as f:
        doc = json.load(f)
    
    items = doc.get("items", [])
    query_lower = query.lower()
    
    results = []
    for item in items:
        text = f"{item.get('title', '')} {item.get('description', '')}".lower()
        if query_lower in text:
            results.append(item)
    
    print(f"Found {len(results)} matches for '{query}':")
    for r in results[:10]:
        print(f"\n  [{r.get('source', '?')}] {r['title'][:80]}")
        if r.get("pubdate"):
            print(f"    {r['pubdate'][:30]}")
        print(f"    {r.get('link', '')[:80]}")
    
    return results


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"
    
    if cmd == "pull":
        pull()
    elif cmd == "list":
        list_items()
    elif cmd == "stats":
        stats()
    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: python rss_pull.py search <query>")
        else:
            search(" ".join(sys.argv[2:]))
    else:
        print(f"Unknown command: {cmd}")
