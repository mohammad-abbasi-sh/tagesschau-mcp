"""Live tests — hit the real tagesschau.de RSS feeds and article pages.
Cautious: few requests.

Run:  pytest tests/test_live.py -v
Skip: pytest -m "not live"  (or set TAGESSCHAU_SKIP_LIVE=1)
"""
import json
import os
import pathlib
import sys
import unittest

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from tagesschau_mcp import server as srv

pytestmark = pytest.mark.live
SKIP = os.environ.get("TAGESSCHAU_SKIP_LIVE") == "1"


@pytest.mark.skipif(SKIP, reason="TAGESSCHAU_SKIP_LIVE=1")
class TestLive(unittest.TestCase):
    def test_headlines_live(self):
        out = json.loads(srv.tagesschau_headlines(limit=3))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 1)
        self.assertTrue(all(i["title"] and i["link"] for i in out["items"]))
        print(f"\nLIVE headlines: {out['count']} items, first: {out['items'][0]['title']}")

    def test_section_live(self):
        out = json.loads(srv.tagesschau_news_by_section("ausland", limit=3))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 1)
        print(f"\nLIVE ausland: {out['items'][0]['title']}")

    def test_search_live(self):
        out = json.loads(srv.tagesschau_search_news("Ukraine", limit=3))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 1)
        self.assertTrue(all(
            "ukraine" in (i["title"] + i["description"]).casefold()
            for i in out["items"]
        ))
        print(f"\nLIVE search 'Ukraine': {out['total_results']} hits")

    def test_get_article_live(self):
        head = json.loads(srv.tagesschau_headlines(limit=5))
        url = head["items"][0]["link"]
        out = json.loads(srv.tagesschau_get_article(url))
        self.assertNotIn("error", out)
        self.assertTrue(out["headline"])
        self.assertGreater(out["body_chars"], 200)
        print(f"\nLIVE article: {out['headline']} ({out['body_chars']} chars)")

    def test_videos_live(self):
        out = json.loads(srv.tagesschau_latest_videos(limit=3))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 1)
        self.assertTrue(all("video-" in i["link"] for i in out["items"]))
        print(f"\nLIVE videos: {out['items'][0]['title']}")

    def test_regional_live(self):
        out = json.loads(srv.tagesschau_regional_news("bayern", limit=3))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 1)
        print(f"\nLIVE bayern: {out['items'][0]['title']}")

    def test_health_live(self):
        out = json.loads(srv.tagesschau_health())
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["http_status"], 200)
