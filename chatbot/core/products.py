"""
Structured product catalog.

Loads products from a YAML file under ``config/products/<client_id>.yaml``.
Each product has a unique id, display name, category, price range,
description, and optional image URL.  The catalog is injected into the
system prompt so the LLM refers to products by their real names, and
channels can attach product images when appropriate.

Admin can edit the YAML file directly or through the admin panel.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field

from chatbot.logging_setup import logger
from chatbot.settings import PROJECT_ROOT


class Product(BaseModel):
    """A single catalog entry."""

    id: str
    name: str
    name_en: str = ""
    category: str = ""
    price: str = ""
    description: str = ""
    image_url: str = ""
    in_stock: bool = True
    tags: list[str] = Field(default_factory=list)


class ProductCatalog:
    """Holds the full product list for a client and provides lookup helpers."""

    def __init__(self, products: list[Product]) -> None:
        self.products = products
        self._by_id: dict[str, Product] = {p.id: p for p in products}
        self._by_name: dict[str, Product] = {}
        for p in products:
            self._by_name[p.name.lower()] = p
            if p.name_en:
                self._by_name[p.name_en.lower()] = p

    # ── Lookup ──────────────────────────────────────────────────────────

    def get(self, product_id: str) -> Product | None:
        return self._by_id.get(product_id)

    def search(self, query: str) -> list[Product]:
        """Simple substring search across name, name_en, category, tags."""
        q = query.lower().strip()
        if not q:
            return []
        results: list[Product] = []
        for p in self.products:
            haystack = f"{p.name} {p.name_en} {p.category} {' '.join(p.tags)}".lower()
            if q in haystack:
                results.append(p)
        return results

    def by_category(self, category: str) -> list[Product]:
        cat = category.lower().strip()
        return [p for p in self.products if p.category.lower() == cat]

    def find_mentioned(self, text: str) -> list[Product]:
        """Find products whose names appear in the given text."""
        found: list[Product] = []
        text_lower = text.lower()
        for p in self.products:
            if p.name.lower() in text_lower:
                found.append(p)
            elif p.name_en and p.name_en.lower() in text_lower:
                if p not in found:
                    found.append(p)
        return found

    def for_system_prompt(self) -> str:
        """Format the catalog for injection into the system prompt.

        Uses plain names (no markdown bold) so the LLM echoes them cleanly.
        """
        if not self.products:
            return ""
        lines = [
            "Product catalog (reference only — use these exact names when "
            "referring to products):",
            "",
            "IMPORTANT PRODUCT RULES:",
            "- When a customer asks about products, mention them by NAME only.",
            "- Do NOT list prices, full descriptions, or catalog-style tables "
            "in your text response.",
            "- The system automatically attaches product cards with prices, "
            "images, and details when you mention a product by name.",
            "- You may say general things like 'we have several options' or "
            "'I recommend X — it is great for relaxing' but keep it "
            "conversational, not a catalog dump.",
            "- If the customer specifically asks 'how much is X?', you may "
            "mention the price for THAT specific product only.",
        ]
        by_cat: dict[str, list[Product]] = {}
        for p in self.products:
            by_cat.setdefault(p.category or "Other", []).append(p)
        for cat, prods in by_cat.items():
            lines.append(f"\n{cat}:")
            for p in prods:
                parts = [f"  - {p.name}"]
                if p.name_en:
                    parts[0] += f" ({p.name_en})"
                if p.price:
                    parts.append(f"    Price: {p.price}")
                if p.description:
                    parts.append(f"    {p.description}")
                if not p.in_stock:
                    parts.append("    (currently unavailable)")
                lines.extend(parts)
        return "\n".join(lines)

    @property
    def categories(self) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for p in self.products:
            c = p.category or "Other"
            if c not in seen:
                seen.add(c)
                out.append(c)
        return out

    def to_dicts(self) -> list[dict[str, Any]]:
        return [p.model_dump() for p in self.products]

    # ── I/O ─────────────────────────────────────────────────────────────

    @classmethod
    def load(cls, client_id: str) -> ProductCatalog:
        """Load from ``config/products/<client_id>.yaml``."""
        path = PROJECT_ROOT / "config" / "products" / f"{client_id}.yaml"
        if not path.exists():
            logger.debug("No product catalog at {}", path)
            return cls([])
        return cls.from_file(path)

    @classmethod
    def from_file(cls, path: Path) -> ProductCatalog:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        raw = data.get("products", [])
        products = []
        for entry in raw:
            if isinstance(entry, dict):
                products.append(Product(**entry))
        logger.info("Loaded {} products from {}", len(products), path.name)
        return cls(products)

    @classmethod
    def save(cls, client_id: str, products: list[dict]) -> Path:
        """Save product list back to YAML."""
        path = PROJECT_ROOT / "config" / "products" / f"{client_id}.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {"products": products}
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return path
