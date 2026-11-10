"""MCP server: unofficial read-only access to tagesschau.de — Germany's
most-watched TV news (ARD) — via its official RSS feeds. No key, no login."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

from . import domain as _dom
from . import http as _http

INSTRUCTIONS = """\
Unofficial read-only MCP server for tagesschau.de — the news of the ARD, \
Germany's most-watched TV news — via its official RSS feeds (no key, no \
login). Headlines, news by section (Inland, Ausland, Wirtschaft, Sport, \
Kultur, Wissen, Investigativ), regional news for all 16 Bundesländer, \
latest videos and full article text. NOTE: tagesschau.de's JSON API \
(api2) is bot-walled from datacenter IPs (HTTP 403), so this server \
reads the official RSS feeds instead — same news, no wall — and article \
text from the NewsArticle JSON-LD on each article page. Search filters \
the fetched feeds client-side (the site search page is also walled). \
Built by Mohammad Abbasi (mohammad-abbasi-sh) — https://almanibama.ir · \
https://mabbasi.ir — Germany MCP factory.\
"""


_SOURCE = "tagesschau.de"
_DISCLAIMER = "Unofficial read-only data from tagesschau.de; verify on the site before acting on it."


def _envelope() -> dict:
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": _SOURCE,
        "disclaimer": _DISCLAIMER,
    }


def _ok(payload: dict) -> str:
    return json.dumps({**_envelope(), **payload}, ensure_ascii=False)


def _err(e: Exception) -> str:
    return _ok({"error": str(e)})


mcp = FastMCP("tagesschau-mcp", instructions=INSTRUCTIONS)


def _feed(url: str, limit: int) -> dict:
    """Fetch one RSS feed and return its items, newest first, capped."""
    parsed = _dom.parse_rss(_http.fetch_feed(url))
    items = parsed["items"][:limit]
    return {
        "feed_title": parsed["feed_title"],
        "total_results": parsed["count"],
        "count": len(items),
        "items": items,
    }


@mcp.tool()
def tagesschau_headlines(limit: int = 10) -> str:
    """Top headlines from tagesschau.de (alle Meldungen), newest first. \
limit: 1..50 (default 10)."""
    try:
        lim = _dom.validate_limit(limit)
        out = _feed(_dom.HEADLINES_FEED, lim)
    except (_http.TagesschauError, ValueError) as e:
        return _err(e)
    return _ok(out)


@mcp.tool()
def tagesschau_news_by_section(section: str, limit: int = 10) -> str:
    """Newest news of one section, newest first. section: "inland", \
"ausland", "wirtschaft", "sport", "kultur", "wissen" or "investigativ". \
limit: 1..50 (default 10)."""
    try:
        lim = _dom.validate_limit(limit)
        entry = _dom.normalise_section(section)
        out = _feed(entry["feed"], lim)
    except (_http.TagesschauError, ValueError) as e:
        return _err(e)
    return _ok({"section": entry["section"], "section_name": entry["name"], **out})


@mcp.tool()
def tagesschau_search_news(query: str, limit: int = 10) -> str:
    """Search tagesschau.de news by keyword (title + description). \
query: free text, e.g. "Ukraine" or "Bundestag". limit: 1..50 \
(default 10). Searches the headlines feed plus all 7 section feeds \
client-side (the site search page is bot-walled), newest first, \
de-duplicated by link."""
    try:
        if not (query or "").strip():
            return _ok({"error": "query must not be empty"})
        lim = _dom.validate_limit(limit)
        feeds = [_dom.HEADLINES_FEED] + [s["feed"] for s in _dom.SECTIONS]
        seen: set[str] = set()
        found: list[dict] = []
        for url in feeds:
            parsed = _dom.parse_rss(_http.fetch_feed(url))
            for item in _dom.search_items(parsed["items"], query.strip()):
                if item["link"] in seen:
                    continue
                seen.add(item["link"])
                found.append(item)
        found.sort(key=lambda it: it.get("published") or "", reverse=True)
        out = {
            "query": query.strip(),
            "total_results": len(found),
            "count": min(lim, len(found)),
            "items": found[:lim],
        }
    except (_http.TagesschauError, ValueError) as e:
        return _err(e)
    return _ok(out)


@mcp.tool()
def tagesschau_get_article(url: str) -> str:
    """Full text of one tagesschau.de article: headline, description, \
publish date, author and the complete article body. url: a \
tagesschau.de article link, e.g. from tagesschau_headlines."""
    try:
        if not (url or "").strip():
            return _ok({"error": "url must not be empty"})
        article = _dom.extract_article(_http.fetch_article(url.strip()))
    except (_http.TagesschauError, ValueError) as e:
        return _err(e)
    return _ok({"url": url.strip(), **article})


@mcp.tool()
def tagesschau_latest_videos(limit: int = 10) -> str:
    """Latest tagesschau.de videos ("Aktuelle Videos"), newest first. \
limit: 1..50 (default 10)."""
    try:
        lim = _dom.validate_limit(limit)
        out = _feed(_dom.VIDEOS_FEED, lim)
    except (_http.TagesschauError, ValueError) as e:
        return _err(e)
    return _ok(out)


@mcp.tool()
def tagesschau_regional_news(region: str, limit: int = 10) -> str:
    """Newest regional news of one Bundesland, newest first. region: \
e.g. "bayern", "berlin", "nordrhein-westfalen", "hamburg", \
"thueringen" (all 16 states; German names work too). \
limit: 1..50 (default 10)."""
    try:
        lim = _dom.validate_limit(limit)
        entry = _dom.normalise_region(region)
        url = f"{_dom.BASE}/inland/regional/{entry['slug']}/index~rss2.xml"
        out = _feed(url, lim)
    except (_http.TagesschauError, ValueError) as e:
        return _err(e)
    return _ok({"region": entry["region"], "region_name": entry["name"], **out})


@mcp.tool()
def tagesschau_health() -> str:
    """Check whether tagesschau.de is reachable right now.

    Returns status ok (HTTP 200), blocked (HTTP 403/429 — bot wall or
    rate limit) or error, plus the HTTP status and the probed URL.
    One polite request; it does not fetch any listings."""
    return _ok(_http.health_check())


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    sys.exit(main())
