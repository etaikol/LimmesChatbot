"""
Lightweight web scraper for one-shot ingestion.

For each URL, fetches the page, strips scripts/styles, and writes a clean
text file into a target directory (default: `data/scraped/`).

Use this when a client gives you a website but no PDFs:

    from chatbot.tools.scraper import scrape_to_data_dir
    scrape_to_data_dir(["https://example.com/about"])
    # then run `python -m scripts.ingest` to embed it.

The scraper is intentionally simple — no JS rendering. If a target site is
JS-heavy, swap to `playwright` (pip install playwright; playwright install).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import urlparse

import httpx

from chatbot.exceptions import IngestionError
from chatbot.logging_setup import logger
from chatbot.settings import get_settings

DEFAULT_HEADERS = {
    "User-Agent": (
        "LimmesChatbot/1.0 (+https://github.com) "
        "Mozilla/5.0 (compatible) Python-httpx"
    ),
    "Accept": "text/html,application/xhtml+xml",
}


class WebScraper:
    """Fetch + clean a list of URLs."""

    def __init__(
        self,
        timeout: float = 20.0,
        headers: Optional[dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> None:
        self.client = httpx.Client(
            timeout=timeout,
            headers=headers or DEFAULT_HEADERS,
            follow_redirects=follow_redirects,
        )

    def __enter__(self) -> "WebScraper":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self.client.close()

    # ── Public ──────────────────────────────────────────────────────────────

    def fetch(self, url: str) -> str:
        """Fetch a single URL and return cleaned text."""
        logger.info("Scraping {}", url)
        try:
            resp = self.client.get(url)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise IngestionError(f"Failed to fetch {url}: {e}") from e

        return self._clean(resp.text)

    def fetch_all(self, urls: Iterable[str]) -> dict[str, str]:
        """Fetch many URLs. Returns {url: text}, skipping failures."""
        out: dict[str, str] = {}
        for url in urls:
            try:
                out[url] = self.fetch(url)
            except IngestionError as e:
                logger.warning("Skipping {}: {}", url, e)
        return out

    # ── Cleaning ────────────────────────────────────────────────────────────

    @staticmethod
    def _clean(html: str) -> str:
        try:
            from bs4 import BeautifulSoup
        except ImportError as e:
            raise IngestionError(
                "Scraper requires beautifulsoup4. Install: pip install beautifulsoup4"
            ) from e

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # Collapse blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text


# ── High-level helper ───────────────────────────────────────────────────────


def scrape_to_data_dir(
    urls: Iterable[str],
    target_dir: Optional[Path] = None,
    prefix: str = "scraped",
) -> list[Path]:
    """Scrape URLs and write each to its own .txt file under `data/<prefix>/`.

    Returns the list of written paths.
    """
    target_dir = target_dir or (get_settings().data_dir / prefix)
    target_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    with WebScraper() as scraper:
        results = scraper.fetch_all(urls)

    for url, text in results.items():
        filename = _safe_filename(url) + ".txt"
        path = target_dir / filename
        path.write_text(f"# {url}\n\n{text}", encoding="utf-8")
        written.append(path)
        logger.info("Wrote {}", path)

    return written


def _safe_filename(url: str) -> str:
    parsed = urlparse(url)
    parts = [parsed.netloc, parsed.path]
    raw = "_".join(p.strip("/").replace("/", "_") for p in parts if p)
    raw = re.sub(r"[^a-zA-Z0-9_.-]+", "_", raw).strip("_")
    return raw or "page"
