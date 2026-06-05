#!/usr/bin/env python3
"""
Temple Institute scraper for primaries cache.
Scrapes red heifer related content from templeinstitute.org.

Usage:
  python temple_pull.py pull
  python temple_pull.py list
  python temple_pull.py stats
  python temple_pull.py search <query>

Data stored in: /home/workspace/primaries/temple/
"""

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CACHE_DIR = Path("/home/workspace/primaries/temple")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = "TRU Research research@tru.local"

SEARCH_QUERIES = [
    "red heifer",
    "red heifer shiloh",
    "parah adumah",
    "third temple",
    "temple sacrifice",
]


def fetch(url):
    """Fetch URL content with proper headers."""
    req = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except (HTTPError, URLError) as e:
        print(f"  error fetching {url}: {e}")
        return ""


def strip_html(html):
    html = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<[^>]+>", " ", html)
    html = re.sub(r"\s+", " ", html)
    return html.strip()


def extract_posts_from_search(html):
    """Extract post URLs from search results page."""
    urls = re.findall(r'<a[^>]+href="([^"]+)"[^>]*class="[^"]*post-title[^"]*"', html, re.IGNORECASE)
    if not urls:
        urls = re.findall(r'<a[^>]+href="(https://templeinstitute\.org/[^"]+)"[^>]*>', html)
    seen = set()
    filtered = []
    for u in urls:
        if u not in seen and "templeinstitute.org" in u:
            seen.add(u)
            filtered.append(u)
    return filtered


def extract_post_content(html, url):
    """Extract title, date, and content from a post page."""
    title_match = re.search(r'<h1[^>]*class="[^"]*entry-title[^"]*"[^>]*>([^<]+)</h1>', html, re.IGNORECASE)
    if not title_match:
        title_match = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else "Unknown"

    date_match = re.search(r'<time[^>]*datetime="([^"]+)"', html, re.IGNORECASE)
    if not date_match:
        date_match = re.search(r'class="[^"]*date[^"]*"[^>]*>([^<]+)<', html, re.IGNORECASE)
    date_str = date_match.group(1).strip() if date_match else ""

    # Fixed: extract content from entry-content div more robustly
    # Find the entry-content div start
    content_start = re.search(r'<div[^>]*class="[^"]*entry-content[^"]*"[^>]*>', html, re.IGNORECASE)
    if content_start:
        # Get everything after the entry-content div opening tag
        remaining = html[content_start.end():]
        # Find the end of the content - either </article> or a closing div that's likely the end
        # Use a simpler approach: just extract text from the remaining HTML
        content = strip_html(remaining[:50000])
    else:
        # Fallback: try to get content from article or main
        article_match = re.search(r'<article[^>]*>(.*?)</article>', html, re.DOTALL | re.IGNORECASE)
        if article_match:
            content = strip_html(article_match.group(1))
        else:
            content = ""
    
    return {
        "title": title,
        "date": date_str,
        "url": url,
        "content": content[:50000],
        "pulled_at": datetime.now(timezone.utc).isoformat(),
        "source_type": "temple",
    }


def _write_merge_cache(posts):
    merged = []
    seen = set()
    for p in posts:
        key = p.get("url")
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(
            {
                "id": key,
                "title": p.get("title", ""),
                "content": p.get("content", ""),
                "published": p.get("date", ""),
                "updated": p.get("pulled_at", ""),
                "link": p.get("url", ""),
                "source_type": "temple",
            }
        )
    merged.sort(key=lambda p: p.get("published", ""), reverse=True)
    with open(CACHE_DIR / "temple_posts.json", "w") as f:
        json.dump(merged, f, indent=2)


def pull():
    """Pull all red heifer related content."""
    print("[temple] pulling from templeinstitute.org...")

    all_posts = {}

    for query in SEARCH_QUERIES:
        print(f"[temple] searching: {query}")
        search_url = f"https://templeinstitute.org/?s={query.replace(' ', '+')}"
        html = fetch(search_url)
        if not html:
            continue

        post_urls = extract_posts_from_search(html)
        print(f"  found {len(post_urls)} potential posts")

        for url in post_urls[:10]:
            if url in all_posts:
                continue

            print(f"  fetching: {url}")
            post_html = fetch(url)
            if post_html:
                post = extract_post_content(post_html, url)
                if post["content"]:
                    all_posts[url] = post
            time.sleep(0.5)

    posts = list(all_posts.values())
    _write_merge_cache(posts)

    print(f"[temple] done: {len(all_posts)} posts cached to {CACHE_DIR / 'temple_posts.json'}")
    return all_posts


def list_posts():
    """List cached posts."""
    cache_file = CACHE_DIR / "temple_posts.json"
    if not cache_file.exists():
        print("No cache found. Run 'pull' first.")
        return []

    with open(cache_file) as f:
        posts = json.load(f)

    print(f"Cached posts: {len(posts)}")
    for p in posts[:20]:
        print(f"  · {p['title'][:60]}")
        if p.get('published'):
            print(f"    {p['published'][:10]}")

    return posts


def stats():
    """Show cache stats."""
    cache_file = CACHE_DIR / "temple_posts.json"
    if not cache_file.exists():
        print("No cache found.")
        return

    with open(cache_file) as f:
        posts = json.load(f)

    total_chars = sum(len(p.get('content', '')) for p in posts)
    print(f"Total posts: {len(posts)}")
    print(f"Total content: {total_chars:,} chars")
    print(f"Cache file: {cache_file}")


def search(query):
    """Search cached posts."""
    cache_file = CACHE_DIR / "temple_posts.json"
    if not cache_file.exists():
        print("No cache found. Run 'pull' first.")
        return []

    with open(cache_file) as f:
        posts = json.load(f)

    query_lower = query.lower()
    results = []

    for p in posts:
        text = (p.get('title', '') + ' ' + p.get('content', '')).lower()
        if query_lower in text:
            results.append({
                'title': p['title'],
                'date': p.get('published', ''),
                'url': p['link'],
                'snippet': p['content'][:200] + '...' if len(p['content']) > 200 else p['content']
            })

    print(f"Found {len(results)} matches for '{query}':")
    for r in results[:10]:
        print(f"\n  · {r['title']}")
        if r['date']:
            print(f"    {r['date'][:10]}")
        print(f"    {r['snippet'][:100]}")

    return results


if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"

    if cmd == "pull":
        pull()
    elif cmd == "list":
        list_posts()
    elif cmd == "stats":
        stats()
    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: python temple_pull.py search <query>")
        else:
            search(" ".join(sys.argv[2:]))
    else:
        print(f"Unknown command: {cmd}")
