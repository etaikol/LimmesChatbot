"""
Scrape one or more URLs into `data/scraped/` (or any folder you choose).

Examples:
    python -m scripts.scrape --url https://www.limmes.co.il/
    python -m scripts.scrape --client limmes          # uses scrape_urls from YAML
    python -m scripts.scrape --url https://a.com --url https://b.com --out data/refs
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from chatbot.core.profile import ClientConfig
from chatbot.exceptions import ChatbotError
from chatbot.logging_setup import logger, setup_logging
from chatbot.settings import get_settings
from chatbot.tools.scraper import scrape_to_data_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Scrape URLs into the data directory.")
    parser.add_argument(
        "--url", action="append", default=[], help="URL to scrape (repeatable)"
    )
    parser.add_argument(
        "--client",
        help="Client id — uses scrape_urls from config/clients/<id>.yaml",
    )
    parser.add_argument(
        "--out",
        help="Output directory (default: data/scraped/)",
    )
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    setup_logging(level="DEBUG" if args.debug else settings.log_level)
    settings.ensure_dirs()

    urls: list[str] = list(args.url)

    if args.client:
        try:
            client = ClientConfig.load(args.client)
            urls.extend(client.scrape_urls)
        except ChatbotError as e:
            logger.error("{}", e)
            return 1

    if not urls:
        print("[error] no URLs supplied. Use --url or --client.")
        return 1

    out_dir = Path(args.out).expanduser().resolve() if args.out else None
    written = scrape_to_data_dir(urls, target_dir=out_dir)

    print(f"\nWrote {len(written)} file(s):")
    for p in written:
        print(f"  - {p}")
    print("\nNext: python -m scripts.ingest")
    return 0


if __name__ == "__main__":
    sys.exit(main())
