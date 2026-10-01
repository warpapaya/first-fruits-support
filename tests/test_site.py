import functools
import threading
import unittest
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.links, self.ids, self.tags, self.text = [], set(), [], []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "a":
            self.links.append(attrs.get("href", ""))

    def handle_data(self, data):
        self.text.append(data)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


class SupportSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = {name: Page((ROOT / name).read_text(encoding="utf-8"))
                     for name in ("index.html", "privacy.html")}
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0),
            functools.partial(QuietHandler, directory=str(ROOT)))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}/"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_support_and_privacy_are_served_as_utf8_html(self):
        for route in ("", "index.html", "privacy.html"):
            with self.subTest(route=route), urlopen(self.base + route, timeout=2) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers.get_content_type(), "text/html")
                self.assertIn("First Fruits", response.read().decode("utf-8"))

    def test_navigation_targets_exist_and_fragments_resolve(self):
        for name, page in self.pages.items():
            for link in page.links:
                with self.subTest(page=name, link=link):
                    self.assertTrue(link, "empty link prevents navigation")
                    target = urlsplit(link)
                    if target.scheme:
                        self.assertIn(target.scheme, ("https", "mailto"))
                        continue
                    resolved = urlsplit(urljoin(name, link))
                    destination = ROOT / unquote(resolved.path)
                    self.assertTrue(destination.is_file(), f"broken local link: {link}")
                    if resolved.fragment:
                        self.assertIn(unquote(resolved.fragment), Page(destination.read_text()).ids)
                    with urlopen(urljoin(self.base + name, link), timeout=2) as response:
                        self.assertEqual(response.status, 200)
        self.assertIn("privacy.html", self.pages["index.html"].links)
        self.assertIn("index.html", self.pages["privacy.html"].links)

    def test_both_pages_have_accessible_structure_mobile_viewport_and_contact(self):
        for name, page in self.pages.items():
            with self.subTest(page=name):
                self.assertEqual(len([tag for tag, _ in page.tags if tag == "h1"]), 1)
                self.assertTrue(any(tag == "html" and attrs.get("lang") == "en" for tag, attrs in page.tags))
                self.assertTrue(any(tag == "meta" and attrs.get("name") == "viewport"
                    and "width=device-width" in attrs.get("content", "") for tag, attrs in page.tags))
                self.assertIn("mailto:petie@petieclark.com", page.links)

    def test_emergency_access_and_local_deletion_guidance_remain_available(self):
        support = " ".join(self.pages["index.html"].text).lower()
        privacy = " ".join(self.pages["privacy.html"].text).lower()
        self.assertIn("emergency release selected apps", support)
        self.assertIn("works offline", support)
        self.assertIn("never paywalled", support)
        self.assertIn("delete journal data", support)
        self.assertIn("delete journal data", privacy)


if __name__ == "__main__":
    unittest.main()
