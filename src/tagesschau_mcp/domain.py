"""Domain logic: shape tagesschau.de RSS feeds and article pages into
compact dicts (stdlib only).

Data source: the official tagesschau.de RSS feeds
(https://www.tagesschau.de/<section>/index~rss2.xml). The JSON API
(api2) is bot-walled from datacenter IPs (HTTP 403 even with full
browser headers, verified 2026-11-10), so the server reads the RSS
feeds instead — same news, no wall. Article text comes from the
NewsArticle JSON-LD embedded in each article page.
"""
from __future__ import annotations

import html
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

BASE = "https://www.tagesschau.de"

# Ressort feeds: <section>/index~rss2.xml — all verified live 2026-11-10.
SECTIONS = [
    {"section": "inland", "name": "Inland", "feed": f"{BASE}/inland/index~rss2.xml"},
    {"section": "ausland", "name": "Ausland", "feed": f"{BASE}/ausland/index~rss2.xml"},
    {"section": "wirtschaft", "name": "Wirtschaft", "feed": f"{BASE}/wirtschaft/index~rss2.xml"},
    {"section": "sport", "name": "Sport", "feed": f"{BASE}/sport/index~rss2.xml"},
    {"section": "kultur", "name": "Kultur", "feed": f"{BASE}/kultur/index~rss2.xml"},
    {"section": "wissen", "name": "Wissen", "feed": f"{BASE}/wissen/index~rss2.xml"},
    {"section": "investigativ", "name": "Investigativ", "feed": f"{BASE}/investigativ/index~rss2.xml"},
]

# Regional feeds: inland/regional/<slug>/index~rss2.xml — all 16 states
# verified live 2026-11-10. Five states use a slug without the hyphen.
REGIONS = [
    {"region": "baden-wuerttemberg", "name": "Baden-Württemberg", "slug": "badenwuerttemberg"},
    {"region": "bayern", "name": "Bayern", "slug": "bayern"},
    {"region": "berlin", "name": "Berlin", "slug": "berlin"},
    {"region": "brandenburg", "name": "Brandenburg", "slug": "brandenburg"},
    {"region": "bremen", "name": "Bremen", "slug": "bremen"},
    {"region": "hamburg", "name": "Hamburg", "slug": "hamburg"},
    {"region": "hessen", "name": "Hessen", "slug": "hessen"},
    {"region": "mecklenburg-vorpommern", "name": "Mecklenburg-Vorpommern", "slug": "mecklenburgvorpommern"},
    {"region": "niedersachsen", "name": "Niedersachsen", "slug": "niedersachsen"},
    {"region": "nordrhein-westfalen", "name": "Nordrhein-Westfalen", "slug": "nordrheinwestfalen"},
    {"region": "rheinland-pfalz", "name": "Rheinland-Pfalz", "slug": "rheinlandpfalz"},
    {"region": "saarland", "name": "Saarland", "slug": "saarland"},
    {"region": "sachsen", "name": "Sachsen", "slug": "sachsen"},
    {"region": "sachsen-anhalt", "name": "Sachsen-Anhalt", "slug": "sachsenanhalt"},
    {"region": "schleswig-holstein", "name": "Schleswig-Holstein", "slug": "schleswigholstein"},
    {"region": "thueringen", "name": "Thüringen", "slug": "thueringen"},
]

HEADLINES_FEED = f"{BASE}/infoservices/alle-meldungen-100~rss2.xml"
VIDEOS_FEED = f"{BASE}/multimedia/video/index~rss2.xml"

_SECTION_BY_KEY = {}
for _s in SECTIONS:
    _SECTION_BY_KEY[_s["section"]] = _s
    _SECTION_BY_KEY[_s["name"].lower()] = _s

_REGION_BY_KEY = {}
for _r in REGIONS:
    _REGION_BY_KEY[_r["region"]] = _r
    _REGION_BY_KEY[_r["slug"]] = _r
    _REGION_BY_KEY[_r["name"].lower()] = _r


def validate_limit(limit: int) -> int:
    """Clamp/validate the page size (feeds carry 20-90 items)."""
    if not 1 <= limit <= 50:
        raise ValueError(f"limit out of range: {limit} (expected 1..50)")
    return limit


def normalise_section(section: str) -> dict:
    """Canonical section entry; accepts slug ("inland") or German name."""
    key = (section or "").strip().lower()
    if not key:
        raise ValueError("section must not be empty")
    entry = _SECTION_BY_KEY.get(key)
    if entry is None:
        raise ValueError(
            f"unknown section: {section!r} "
            f"(expected one of {', '.join(s['section'] for s in SECTIONS)})"
        )
    return entry


def normalise_region(region: str) -> dict:
    """Canonical region entry; accepts slug, hyphenated name or German name."""
    key = (region or "").strip().lower()
    if not key:
        raise ValueError("region must not be empty")
    entry = _REGION_BY_KEY.get(key)
    if entry is None:
        raise ValueError(
            f"unknown region: {region!r} "
            f"(expected one of {', '.join(r['region'] for r in REGIONS)})"
        )
    return entry


def _text(elem, tag: str) -> str:
    child = elem.find(tag)
    if child is None or child.text is None:
        return ""
    return html.unescape(child.text).strip()


def _iso(date_text: str) -> str | None:
    if not date_text:
        return None
    try:
        dt = parsedate_to_datetime(date_text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError):
        return None


def compact_item(item: ET.Element) -> dict:
    """One RSS <item>, compact: title, link, description, publish time."""
    return {
        "title": _text(item, "title"),
        "link": _text(item, "link"),
        "description": _text(item, "description"),
        "published": _iso(_text(item, "pubDate")),
    }


def parse_rss(xml_text: str) -> dict:
    """Parse one tagesschau.de RSS feed into {feed_title, count, items}.

    Raises ValueError on malformed XML or a non-RSS document (e.g. a
    403 error page saved as text).
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        raise ValueError(f"invalid RSS XML: {e}") from e
    channel = root.find("channel")
    if channel is None:
        raise ValueError("unexpected RSS shape: no <channel> element")
    items = [compact_item(it) for it in channel.findall("item")]
    return {
        "feed_title": _text(channel, "title"),
        "count": len(items),
        "items": items,
    }


def search_items(items: list, query: str) -> list:
    """Case-insensitive substring match over title + description.

    The site search page is bot-walled (HTTP 403), so search filters
    the fetched feeds client-side.
    """
    q = (query or "").strip().casefold()
    if not q:
        raise ValueError("query must not be empty")
    return [
        it for it in items
        if q in (it.get("title") or "").casefold()
        or q in (it.get("description") or "").casefold()
    ]


_LD_JSON_RE = re.compile(
    r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
    re.S | re.I,
)


def extract_article(page_html: str) -> dict:
    """Full article text from a tagesschau.de article page.

    Reads the NewsArticle JSON-LD block (headline, description,
    datePublished, articleBody). Video pages carry a VideoObject
    instead — headline/description/date still parse, body is empty.
    Raises ValueError when no JSON-LD block is found.
    """
    match = _LD_JSON_RE.search(page_html)
    if not match:
        raise ValueError(
            "no JSON-LD data on this page (not a tagesschau.de article page?)"
        )
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JSON-LD on article page: {e}") from e
    if isinstance(data, list):
        data = next((d for d in data if isinstance(d, dict)), {})
    if not isinstance(data, dict):
        raise ValueError("unexpected JSON-LD shape on article page")
    author = data.get("author")
    if isinstance(author, dict):
        author = author.get("name") or ""
    body = (data.get("articleBody") or "").strip()
    entity = data.get("mainEntityOfPage")
    if isinstance(entity, dict):
        entity_url = entity.get("@id", "")
    elif isinstance(entity, str):
        entity_url = entity
    else:
        entity_url = ""
    return {
        "headline": data.get("headline") or "",
        "description": data.get("description") or "",
        "published": data.get("datePublished") or "",
        "modified": data.get("dateModified") or "",
        "author": author or "",
        "keywords": data.get("keywords") or "",
        "body": body,
        "body_chars": len(body),
        "url": entity_url,
    }
