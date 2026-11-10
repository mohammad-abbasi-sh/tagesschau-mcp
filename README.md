# tagesschau-mcp 📰

mcp-name: io.github.mohammad-abbasi-sh/tagesschau-mcp

Unofficial **read-only** MCP server for **[tagesschau.de](https://www.tagesschau.de)** — the news of the ARD, Germany's most-watched TV news — via its official RSS feeds. Headlines, news by section, regional news for all 16 Bundesländer, latest videos and full article text. No key, no login.

> Built by Mohammad Abbasi as part of the "Germany MCP factory" (Sepehr-style pipeline). Not affiliated with tagesschau.de or the ARD.

## For AI agents

Add to your MCP client config (stdio):

```json
{
  "mcpServers": {
    "tagesschau": {
      "command": "uvx",
      "args": ["tagesschau-mcp==0.1.0"]
    }
  }
}
```

Or run locally: `python -m tagesschau_mcp.server` (needs `mcp<2`, `httpx`).

## Tools

| Tool | Description |
|------|-------------|
| `tagesschau_headlines` | Top headlines (alle Meldungen), newest first — `limit` 1..50 |
| `tagesschau_news_by_section` | Newest news of one section — `section`: "inland", "ausland", "wirtschaft", "sport", "kultur", "wissen" or "investigativ", `limit` 1..50 |
| `tagesschau_search_news` | Search news by keyword (title + description) — `query` (e.g. "Ukraine"), `limit` 1..50 |
| `tagesschau_get_article` | Full text of one article: headline, description, publish date, author, complete body — `url` (a tagesschau.de article link) |
| `tagesschau_latest_videos` | Latest videos ("Aktuelle Videos"), newest first — `limit` 1..50 |
| `tagesschau_regional_news` | Newest regional news of one Bundesland — `region`: e.g. "bayern", "berlin", "nordrhein-westfalen" (all 16 states; German names work too), `limit` 1..50 |
| `tagesschau_health` | Reachability probe (ok / blocked / error) — one polite request |

Example output (`tagesschau_headlines`, `limit` 2):

```json
{"feed_title": "tagesschau.de - Die Nachrichten der ARD", "total_results": 40, "count": 2,
 "items": [
  {"title": "Börsengang von Anthropic - umstrittener Goldrausch in San Francisco",
   "link": "https://www.tagesschau.de/ausland/amerika/goldrausch-san-fransisco-anthropic-vor-boersengang-100.html",
   "description": "Der KI-Gigant Anthropic will an die Börse. Und damit könnten Tausende Mitarbeiter und Investoren zu Millionären werden. ...",
   "published": "2026-11-10T09:42:31+00:00"},
  {"title": "Was von den Ukraine-Gesprächen in Abu Dhabi zu erwarten ist",
   "link": "https://www.tagesschau.de/ausland/asien/ukraine-verhandlungen-abu-dhabi-104.html",
   "description": "Unterhändler Russlands und der Ukraine haben ihre Gespräche unter US-Vermittlung in Abu Dhabi aufgenommen. ...",
   "published": "2026-11-10T09:18:35+00:00"},
  ...]}
```

Notes:
- The server reads the **official RSS feeds**, not the JSON API (api2): api2 returns HTTP 403 from datacenter IPs even with full browser headers (verified 2026-11-10), while the RSS feeds answer 200 — same news, no wall.
- `tagesschau_search_news` filters the headlines feed plus all 7 section feeds client-side (the site search page is also bot-walled), de-duplicated by link, newest first.
- `tagesschau_get_article` reads the NewsArticle JSON-LD embedded in the article page (headline, description, publish date, full body). Only `www.tagesschau.de` URLs are fetched.
- Regional feeds exist for all 16 Bundesländer; five slugs have no hyphen (`badenwuerttemberg`, `mecklenburgvorpommern`, `rheinlandpfalz`, `sachsenanhalt`, `schleswigholstein`) — the tool accepts the hyphenated name anyway.
- Data: tagesschau.de public RSS feeds — no key, no login, read-only.

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

- `tests/test_domain.py` — offline, parses real captured RSS feeds + article page (30 tests)
- `tests/test_live.py` — cautious live requests against tagesschau.de (7 tests)

Tests: 37/37 green (30 offline + 7 live, 2026-11-10).

## License

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
