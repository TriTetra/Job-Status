"""Portfolio crawler: only public sites, whole-word technologies, real project blocks."""

import socket

import pytest

from careeros.evidence import portfolio
from careeros.evidence.portfolio import PortfolioCrawlError, PortfolioCrawler, check_url, find_technologies


def _resolve_to(monkeypatch, ip):
    monkeypatch.setattr(portfolio.socket, "getaddrinfo",
                        lambda host, port, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port))])


@pytest.mark.parametrize("ip", ["127.0.0.1", "10.0.1.5", "172.18.0.3", "192.168.1.1", "169.254.169.254", "0.0.0.0"])
def test_private_and_internal_addresses_are_refused(monkeypatch, ip):
    _resolve_to(monkeypatch, ip)
    with pytest.raises(PortfolioCrawlError, match="public"):
        check_url("https://careeros-db")


@pytest.mark.parametrize("url, message", [
    ("ftp://me.dev", "website address"),
    ("https://me.dev:8000", "ports"),
    ("https://user:pw@me.dev", "login"),
])
def test_odd_urls_are_refused(monkeypatch, url, message):
    _resolve_to(monkeypatch, "93.184.216.34")
    with pytest.raises(PortfolioCrawlError, match=message):
        check_url(url)


def test_public_address_passes_and_scheme_is_added(monkeypatch):
    _resolve_to(monkeypatch, "93.184.216.34")
    assert check_url("me.dev") == "https://me.dev"


class _Resp:
    def __init__(self, status=200, html="", location=None, ctype="text/html; charset=utf-8"):
        self.status_code = status
        self.headers = {"content-type": ctype, **({"location": location} if location else {})}
        self.is_redirect = location is not None
        self.encoding = "utf-8"
        self._body = html.encode()

    def iter_content(self, n):
        yield self._body

    def close(self):
        pass


class _HTTP:
    def __init__(self, pages):
        self.pages, self.requested = pages, []

    def get(self, url, **kwargs):
        assert kwargs["allow_redirects"] is False
        self.requested.append(url)
        return self.pages[url]


def _crawler(pages, blocked=()):
    def check(url):
        if any(b in url for b in blocked):
            raise PortfolioCrawlError("Only public websites can be added.")
        return url
    return PortfolioCrawler(http=_HTTP(pages), url_check=check)


def test_redirect_to_an_internal_address_is_refused():
    crawler = _crawler({"https://me.dev": _Resp(302, location="http://169.254.169.254/latest")},
                       blocked=["169.254"])
    assert "public" in crawler.crawl("https://me.dev")["error"]


def test_whole_words_only():
    found = find_technologies("Built at Google with digital tools; javascript and Golang, Rust services. "
                              "Python, React and Node.js. Some rust on the bike.")
    assert "Git" not in found and "Java" not in found          # "digital", "javascript"
    assert {"JavaScript", "Go", "Rust", "Python", "React", "Node.js"} <= set(found)


def test_rust_the_word_is_not_rust_the_language():
    assert "Rust" not in find_technologies("Old bikes rust in the rain, a lot of filler text here.")


FILLER = "<p>" + "I build things for the web and like clean code. " * 6 + "</p>"
HOME = f"""<html><body>
<nav><a href="/projects">Projects</a><a href="https://other.site/work">elsewhere</a></nav>
<section class="about-me"><p>I am a backend engineer working with Python and PostgreSQL.</p></section>
<section class="network-stats"><h2>Network uptime</h2></section>
<div class="framework-list"><h3>Frameworks I like</h3></div>
{FILLER}
<script>var x = "kubernetes";</script>
</body></html>"""
PROJECTS = """<html><body><h1>Projects</h1>
<article class="project-card"><h3>Ledger API</h3><p>Double-entry ledger in FastAPI and Redis.</p></article>
<div class="projects"><h2>Projects</h2></div>
<li id="work-2"><h4>Vision Drone</h4><p>YOLOv8 on a Raspberry Pi.</p></li>
</body></html>"""


def test_crawl_reads_linked_project_page_and_real_project_blocks():
    crawler = _crawler({"https://me.dev": _Resp(html=HOME), "https://me.dev/projects": _Resp(html=PROJECTS)})
    out = crawler.crawl("https://me.dev")

    assert crawler.http.requested == ["https://me.dev", "https://me.dev/projects"]  # other hosts not followed
    names = [p["name"] for p in out["projects"]]
    assert names == ["Ledger API", "Vision Drone"]        # not "Network uptime", "Frameworks I like", "Projects"
    assert set(out["projects"][0]["technologies"]) == {"FastAPI", "Redis"}
    assert "Kubernetes" not in out["technologies"]        # script text ignored
    assert {"Python", "PostgreSQL", "YOLOv8"} <= set(out["technologies"])
    assert out["about"].startswith("I am a backend engineer")
    assert out["pages"] == 2


def test_javascript_only_site_gets_a_clear_message():
    shell = '<html><body><div id="root"></div><script src="/app.js"></script></body></html>'
    out = _crawler({"https://me.dev": _Resp(html=shell)}).crawl("https://me.dev")
    assert "JavaScript" in out["error"]


def test_failed_crawl_saves_nothing():
    from tests.unit.test_evidence import SKILLS, FakeSession

    class Broken:
        def crawl(self, url):
            return {"error": "The website could not be reached."}

    session = FakeSession(SKILLS)
    with pytest.raises(PortfolioCrawlError):
        portfolio.sync_portfolio_evidence("user_1", "https://me.dev", session, crawler=Broken())
    assert session.added == [] and session.commits == 0
