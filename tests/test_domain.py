"""Offline tests — parse real captured tagesschau.de RSS feeds and one
article page, no network."""
import json
import pathlib
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from tagesschau_mcp import domain as dom
from tagesschau_mcp import server as srv

FIX = pathlib.Path(__file__).resolve().parent / "fixtures"


def _rss(name):
    return dom.parse_rss((FIX / name).read_text(encoding="utf-8"))


class TestHeadlinesFixture(unittest.TestCase):
    def test_headlines_shape(self):
        out = _rss("headlines.xml")
        self.assertEqual(out["feed_title"], "tagesschau.de - Die Nachrichten der ARD")
        self.assertEqual(out["count"], 40)
        self.assertEqual(len(out["items"]), 40)

    def test_headlines_first_item(self):
        item = _rss("headlines.xml")["items"][0]
        self.assertEqual(
            item["title"],
            "Börsengang von Anthropic - umstrittener Goldrausch in San Francisco",
        )
        self.assertTrue(item["link"].startswith("https://www.tagesschau.de/ausland/"))
        self.assertEqual(item["published"], "2026-11-10T09:42:31+00:00")

    def test_headlines_all_items_complete(self):
        items = _rss("headlines.xml")["items"]
        self.assertTrue(all(i["title"] and i["link"] and i["published"] for i in items))
        self.assertTrue(all(i["link"].startswith("https://www.tagesschau.de/") for i in items))

    def test_headlines_descriptions_present(self):
        items = _rss("headlines.xml")["items"]
        self.assertTrue(all(i["description"] for i in items))


class TestSectionAndRegionFixtures(unittest.TestCase):
    def test_section_inland(self):
        out = _rss("section-inland.xml")
        self.assertEqual(out["count"], 49)
        self.assertTrue(all(i["link"].startswith("https://www.tagesschau.de/") for i in out["items"]))

    def test_videos_feed(self):
        out = _rss("videos.xml")
        self.assertEqual(out["feed_title"], "Aktuelle Videos")
        self.assertEqual(out["count"], 27)
        # Video links vary: /video/video-N, /tagesschau_in_100_sekunden/video-N,
        # /multimedia/sendung/.../video-N — all carry a video-N id.
        self.assertTrue(all("video-" in i["link"] for i in out["items"]))
        self.assertTrue(all(i["link"].startswith("https://www.tagesschau.de/") for i in out["items"]))

    def test_region_bayern(self):
        out = _rss("region-bayern.xml")
        self.assertEqual(out["count"], 34)


class TestParseErrors(unittest.TestCase):
    def test_malformed_xml(self):
        with self.assertRaises(ValueError):
            dom.parse_rss("<rss><channel><item>oops")

    def test_non_rss_document(self):
        with self.assertRaises(ValueError):
            dom.parse_rss("<html><head><title>403</title></head></html>")

    def test_empty_string(self):
        with self.assertRaises(ValueError):
            dom.parse_rss("")


class TestValidation(unittest.TestCase):
    def test_limit_bounds(self):
        self.assertEqual(dom.validate_limit(1), 1)
        self.assertEqual(dom.validate_limit(50), 50)
        with self.assertRaises(ValueError):
            dom.validate_limit(0)
        with self.assertRaises(ValueError):
            dom.validate_limit(51)

    def test_normalise_section(self):
        self.assertEqual(dom.normalise_section("inland")["section"], "inland")
        self.assertEqual(dom.normalise_section("Inland")["name"], "Inland")
        self.assertEqual(dom.normalise_section("WIRTSCHAFT")["section"], "wirtschaft")
        with self.assertRaises(ValueError):
            dom.normalise_section("dax")
        with self.assertRaises(ValueError):
            dom.normalise_section("")

    def test_sections_all_have_feeds(self):
        self.assertEqual(len(dom.SECTIONS), 7)
        for s in dom.SECTIONS:
            self.assertTrue(s["feed"].startswith("https://www.tagesschau.de/"))
            self.assertTrue(s["feed"].endswith("~rss2.xml"))

    def test_normalise_region(self):
        self.assertEqual(dom.normalise_region("bayern")["name"], "Bayern")
        self.assertEqual(dom.normalise_region("Bayern")["slug"], "bayern")
        self.assertEqual(
            dom.normalise_region("nordrhein-westfalen")["slug"], "nordrheinwestfalen"
        )
        self.assertEqual(
            dom.normalise_region("nordrheinwestfalen")["region"], "nordrhein-westfalen"
        )
        self.assertEqual(
            dom.normalise_region("Baden-Württemberg")["slug"], "badenwuerttemberg"
        )
        with self.assertRaises(ValueError):
            dom.normalise_region("bavaria")
        with self.assertRaises(ValueError):
            dom.normalise_region("")

    def test_regions_all_16_states(self):
        self.assertEqual(len(dom.REGIONS), 16)
        slugs = {r["slug"] for r in dom.REGIONS}
        self.assertEqual(len(slugs), 16)
        self.assertIn("thueringen", slugs)
        self.assertIn("schleswigholstein", slugs)


class TestSearch(unittest.TestCase):
    def test_search_case_insensitive(self):
        items = _rss("headlines.xml")["items"]
        self.assertEqual(len(dom.search_items(items, "Ukraine")), 5)
        self.assertEqual(len(dom.search_items(items, "ukraine")), 5)
        self.assertEqual(len(dom.search_items(items, "UKRAINE")), 5)

    def test_search_no_hits(self):
        items = _rss("headlines.xml")["items"]
        self.assertEqual(dom.search_items(items, "zzzzqqq"), [])

    def test_search_empty_raises(self):
        with self.assertRaises(ValueError):
            dom.search_items([], "  ")


class TestArticleExtraction(unittest.TestCase):
    def test_article_fixture(self):
        html_text = (FIX / "article-ukraine.html").read_text(encoding="utf-8")
        out = dom.extract_article(html_text)
        self.assertEqual(
            out["headline"],
            "Was von den Ukraine-Gesprächen in Abu Dhabi zu erwarten ist",
        )
        self.assertEqual(out["published"], "2026-11-10T09:18:35.607Z")
        self.assertEqual(out["author"], "tagesschau.de")
        self.assertEqual(out["body_chars"], 6428)
        self.assertTrue(out["body"].startswith("Unterhändler Russlands"))
        self.assertTrue(out["url"].startswith("https://www.tagesschau.de/"))

    def test_article_no_json_ld(self):
        with self.assertRaises(ValueError):
            dom.extract_article("<html><body>no data here</body></html>")


class TestServerOffline(unittest.TestCase):
    """Tool functions with the HTTP layer mocked to the fixtures."""

    def _mock_feeds(self, mapping):
        def fake_fetch(url):
            return mapping[url]
        return mock.patch.object(srv._http, "fetch_feed", side_effect=fake_fetch)

    def test_headlines_tool(self):
        xml = (FIX / "headlines.xml").read_text(encoding="utf-8")
        with self._mock_feeds({dom.HEADLINES_FEED: xml}):
            out = json.loads(srv.tagesschau_headlines(limit=3))
        self.assertNotIn("error", out)
        self.assertEqual(out["count"], 3)
        self.assertEqual(out["total_results"], 40)
        self.assertEqual(out["source"], "tagesschau.de")
        self.assertIn("fetched_at", out)

    def test_section_tool(self):
        xml = (FIX / "section-inland.xml").read_text(encoding="utf-8")
        with self._mock_feeds({dom.SECTIONS[0]["feed"]: xml}):
            out = json.loads(srv.tagesschau_news_by_section("inland", limit=2))
        self.assertNotIn("error", out)
        self.assertEqual(out["section"], "inland")
        self.assertEqual(out["count"], 2)

    def test_section_tool_unknown(self):
        out = json.loads(srv.tagesschau_news_by_section("dax", limit=2))
        self.assertIn("error", out)
        self.assertIn("unknown section", out["error"])

    def test_search_tool(self):
        xml = (FIX / "headlines.xml").read_text(encoding="utf-8")
        feeds = {dom.HEADLINES_FEED: xml}
        feeds.update({s["feed"]: xml for s in dom.SECTIONS})
        with self._mock_feeds(feeds):
            out = json.loads(srv.tagesschau_search_news("Ukraine", limit=10))
        self.assertNotIn("error", out)
        self.assertEqual(out["query"], "Ukraine")
        self.assertEqual(out["total_results"], 5)
        self.assertEqual(out["count"], 5)

    def test_search_tool_empty_query(self):
        out = json.loads(srv.tagesschau_search_news("   "))
        self.assertIn("error", out)

    def test_get_article_tool(self):
        html_text = (FIX / "article-ukraine.html").read_text(encoding="utf-8")
        with mock.patch.object(srv._http, "fetch_article", return_value=html_text):
            out = json.loads(
                srv.tagesschau_get_article(
                    "https://www.tagesschau.de/ausland/asien/ukraine-verhandlungen-abu-dhabi-104.html"
                )
            )
        self.assertNotIn("error", out)
        self.assertEqual(out["body_chars"], 6428)
        self.assertIn("Abu Dhabi", out["headline"])

    def test_get_article_tool_rejects_other_hosts(self):
        out = json.loads(srv.tagesschau_get_article("https://example.com/news.html"))
        self.assertIn("error", out)

    def test_videos_tool(self):
        xml = (FIX / "videos.xml").read_text(encoding="utf-8")
        with self._mock_feeds({dom.VIDEOS_FEED: xml}):
            out = json.loads(srv.tagesschau_latest_videos(limit=5))
        self.assertNotIn("error", out)
        self.assertEqual(out["count"], 5)
        self.assertEqual(out["total_results"], 27)

    def test_regional_tool(self):
        xml = (FIX / "region-bayern.xml").read_text(encoding="utf-8")
        url = f"{dom.BASE}/inland/regional/bayern/index~rss2.xml"
        with self._mock_feeds({url: xml}):
            out = json.loads(srv.tagesschau_regional_news("Bayern", limit=3))
        self.assertNotIn("error", out)
        self.assertEqual(out["region"], "bayern")
        self.assertEqual(out["count"], 3)

    def test_regional_tool_unknown(self):
        out = json.loads(srv.tagesschau_regional_news("bavaria", limit=3))
        self.assertIn("error", out)
        self.assertIn("unknown region", out["error"])


if __name__ == "__main__":
    unittest.main()
