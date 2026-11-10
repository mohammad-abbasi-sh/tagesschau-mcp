# tagesschau-mcp 📰

mcp-name: io.github.mohammad-abbasi-sh/tagesschau-mcp

سرور MCP غیررسمی و **فقط‌خواندنی** برای **[tagesschau.de](https://www.tagesschau.de)** — اخبار ARD، پربیننده‌ترین اخبار تلویزیونی آلمان — از طریق فیدهای رسمی RSS. تیترهای برتر، اخبار به‌تفکیک بخش، اخبار منطقه‌ای هر ۱۶ ایالت آلمان، جدیدترین ویدیوها و متن کامل مقاله‌ها. بدون کلید، بدون ورود.

> ساختهٔ محمد عباسی در چارچوب «کارخانهٔ MCP آلمان» (مدل سپهر). وابسته به tagesschau.de یا ARD نیست.

## برای ایجنت‌های هوش مصنوعی

به پیکربندی کلاینت MCP اضافه کنید (stdio):

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

یا اجرای محلی: `python -m tagesschau_mcp.server` (نیازمند `mcp<2` و `httpx`).

## ابزارها

| ابزار | توضیح |
|------|------|
| `tagesschau_headlines` | تیترهای برتر (alle Meldungen)، جدیدترین اول — `limit` ‏۱ تا ۵۰ |
| `tagesschau_news_by_section` | جدیدترین اخبار یک بخش — `section`: ‏«inland»‏، ‏«ausland»‏، ‏«wirtschaft»‏، ‏«sport»‏، ‏«kultur»‏، ‏«wissen»‏ یا ‏«investigativ»‏، `limit` ‏۱ تا ۵۰ |
| `tagesschau_search_news` | جست‌وجوی اخبار با کلیدواژه (عنوان + توضیح) — `query` (مثلاً «Ukraine»)، `limit` ‏۱ تا ۵۰ |
| `tagesschau_get_article` | متن کامل یک مقاله: تیتر، توضیح، تاریخ انتشار، نویسنده و متن کامل — `url` (لینک مقالهٔ tagesschau.de) |
| `tagesschau_latest_videos` | جدیدترین ویدیوها (Aktuelle Videos)، جدیدترین اول — `limit` ‏۱ تا ۵۰ |
| `tagesschau_regional_news` | جدیدترین اخبار منطقه‌ای یک ایالت — `region`: مثلاً «bayern»، «berlin»، «nordrhein-westfalen» (هر ۱۶ ایالت؛ نام‌های آلمانی هم کار می‌کنند)، `limit` ‏۱ تا ۵۰ |
| `tagesschau_health` | بررسی دسترسی (ok / blocked / error) — یک درخواست مؤدبانه |

نمونهٔ خروجی (`tagesschau_headlines` با `limit` برابر ۲):

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

نکته‌ها:
- سرور **فیدهای رسمی RSS** را می‌خواند، نه API جی‌سان (api2): ‏api2 از IPهای دیتاسنتر حتی با هدرهای کامل مرورگر خطای ۴۰۳ می‌دهد (بررسی‌شده در ۲۰۲۶-۱۱-۱۰)، در حالی که فیدهای RSS پاسخ ۲۰۰ می‌دهند — همان اخبار، بدون سد.
- `tagesschau_search_news` فید تیترها به‌علاوهٔ هر ۷ فید بخش را سمت کلاینت فیلتر می‌کند (صفحهٔ جست‌وجوی سایت هم مسدود است)، بدون تکرار بر اساس لینک، جدیدترین اول.
- `tagesschau_get_article` بلوک JSON-LD نوع NewsArticle در صفحهٔ مقاله را می‌خواند (تیتر، توضیح، تاریخ انتشار، متن کامل). فقط URLهای `www.tagesschau.de` دریافت می‌شوند.
- فید منطقه‌ای برای هر ۱۶ ایالت وجود دارد؛ پنج اسلاگ خط‌تیره ندارند (`badenwuerttemberg`، `mecklenburgvorpommern`، `rheinlandpfalz`، `sachsenanhalt`، `schleswigholstein`) — ابزار با این حال نام خط‌تیره‌دار را هم می‌پذیرد.
- داده‌ها: فیدهای عمومی RSS سایت tagesschau.de — بدون کلید، بدون ورود، فقط‌خواندنی.

## توسعه

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

- `tests/test_domain.py` — آفلاین، با فیدهای RSS و صفحهٔ مقالهٔ واقعی ضبط‌شده (۳۰ تست)
- `tests/test_live.py` — چند درخواست زندهٔ محتاطانه به tagesschau.de (۷ تست)

تست‌ها: ۳۷ از ۳۷ سبز (۳۰ آفلاین + ۷ زنده، ۲۰۲۶-۱۱-۱۰).

## مجوز

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
