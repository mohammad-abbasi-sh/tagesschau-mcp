# tagesschau-mcp 📰

mcp-name: io.github.mohammad-abbasi-sh/tagesschau-mcp

Inoffizieller **Read-only**-MCP-Server für **[tagesschau.de](https://www.tagesschau.de)** — die Nachrichten der ARD, Deutschlands meistgesehene Fernsehnachrichten — über die offiziellen RSS-Feeds. Schlagzeilen, Nachrichten nach Ressort, Regionalnachrichten für alle 16 Bundesländer, neueste Videos und vollständige Artikeltexte. Kein Schlüssel, kein Login.

> Gebaut von Mohammad Abbasi im Rahmen der „Germany MCP factory" (Sepehr-Modell). Nicht mit tagesschau.de oder der ARD verbunden.

## Für KI-Agenten

Zur MCP-Client-Konfiguration hinzufügen (stdio):

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

Oder lokal starten: `python -m tagesschau_mcp.server` (benötigt `mcp<2`, `httpx`).

## Tools

| Tool | Beschreibung |
|------|--------------|
| `tagesschau_headlines` | Top-Schlagzeilen (alle Meldungen), neueste zuerst — `limit` 1..50 |
| `tagesschau_news_by_section` | Neueste Nachrichten eines Ressorts — `section`: „inland", „ausland", „wirtschaft", „sport", „kultur", „wissen" oder „investigativ", `limit` 1..50 |
| `tagesschau_search_news` | Nachrichtensuche nach Stichwort (Titel + Beschreibung) — `query` (z. B. „Ukraine"), `limit` 1..50 |
| `tagesschau_get_article` | Volltext eines Artikels: Schlagzeile, Beschreibung, Veröffentlichungsdatum, Autor, kompletter Text — `url` (ein tagesschau.de-Artikellink) |
| `tagesschau_latest_videos` | Neueste Videos („Aktuelle Videos"), neueste zuerst — `limit` 1..50 |
| `tagesschau_regional_news` | Neueste Regionalnachrichten eines Bundeslandes — `region`: z. B. „bayern", „berlin", „nordrhein-westfalen" (alle 16 Länder; deutsche Namen funktionieren auch), `limit` 1..50 |
| `tagesschau_health` | Erreichbarkeitsprüfung (ok / blocked / error) — eine höfliche Anfrage |

Beispielausgabe (`tagesschau_headlines`, `limit` 2):

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

Hinweise:
- Der Server liest die **offiziellen RSS-Feeds**, nicht die JSON-API (api2): api2 antwortet von Rechenzentrums-IPs mit HTTP 403, selbst mit vollständigen Browser-Headern (geprüft 10.11.2026), während die RSS-Feeds 200 liefern — dieselben Nachrichten, keine Sperre.
- `tagesschau_search_news` filtert den Schlagzeilen-Feed plus alle 7 Ressort-Feeds clientseitig (auch die Website-Suche ist gesperrt), nach Link dedupliziert, neueste zuerst.
- `tagesschau_get_article` liest das NewsArticle-JSON-LD der Artikelseite (Schlagzeile, Beschreibung, Veröffentlichungsdatum, Volltext). Nur `www.tagesschau.de`-URLs werden abgerufen.
- Regional-Feeds gibt es für alle 16 Bundesländer; fünf Slugs haben keinen Bindestrich (`badenwuerttemberg`, `mecklenburgvorpommern`, `rheinlandpfalz`, `sachsenanhalt`, `schleswigholstein`) — das Tool akzeptiert trotzdem den Namen mit Bindestrich.
- Daten: öffentliche RSS-Feeds von tagesschau.de — kein Schlüssel, kein Login, nur lesend.

## Entwicklung

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

- `tests/test_domain.py` — offline, mit echten aufgezeichneten RSS-Feeds und Artikelseite (30 Tests)
- `tests/test_live.py` — wenige vorsichtige Live-Anfragen an tagesschau.de (7 Tests)

Tests: 37/37 grün (30 offline + 7 live, 10.11.2026).

## Lizenz

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
