"""Tests for chatbot.core.products."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml

from chatbot.core.products import Product, ProductCatalog


@pytest.fixture
def sample_products():
    return [
        Product(
            id="p1",
            name="וילון שקוף",
            name_en="Sheer Curtain",
            category="Curtains",
            price="300 ₪",
            description="Light and airy",
            image_url="https://example.com/sheer.jpg",
            tags=["curtain", "sheer"],
        ),
        Product(
            id="p2",
            name="ספה מודרנית",
            name_en="Modern Sofa",
            category="Sofas",
            price="2500 ₪",
            tags=["sofa", "modern"],
        ),
        Product(
            id="p3",
            name="כרית נוי",
            name_en="Decorative Pillow",
            category="Accessories",
            price="80 ₪",
            in_stock=False,
        ),
    ]


@pytest.fixture
def catalog(sample_products):
    return ProductCatalog(sample_products)


def test_get_by_id(catalog):
    assert catalog.get("p1").name == "וילון שקוף"
    assert catalog.get("nonexistent") is None


def test_search_by_name(catalog):
    results = catalog.search("שקוף")
    assert len(results) == 1
    assert results[0].id == "p1"


def test_search_by_english_name(catalog):
    results = catalog.search("sofa")
    assert len(results) == 1
    assert results[0].id == "p2"


def test_search_by_tag(catalog):
    results = catalog.search("modern")
    assert len(results) == 1
    assert results[0].id == "p2"


def test_search_empty_query(catalog):
    assert catalog.search("") == []
    assert catalog.search("   ") == []


def test_search_no_match(catalog):
    assert catalog.search("nonexistent-xyz") == []


def test_by_category(catalog):
    curtains = catalog.by_category("Curtains")
    assert len(curtains) == 1
    assert curtains[0].id == "p1"


def test_by_category_case_insensitive(catalog):
    assert len(catalog.by_category("curtains")) == 1
    assert len(catalog.by_category("CURTAINS")) == 1


def test_find_mentioned(catalog):
    text = "I recommend the וילון שקוף for your living room"
    found = catalog.find_mentioned(text)
    assert len(found) == 1
    assert found[0].id == "p1"


def test_find_mentioned_english(catalog):
    text = "Check out our Modern Sofa collection"
    found = catalog.find_mentioned(text)
    assert len(found) == 1
    assert found[0].id == "p2"


def test_find_mentioned_no_duplicates(catalog):
    text = "וילון שקוף is also known as Sheer Curtain"
    found = catalog.find_mentioned(text)
    assert len(found) == 1


def test_for_system_prompt_no_markdown(catalog):
    prompt = catalog.for_system_prompt()
    assert "**" not in prompt
    assert "וילון שקוף" in prompt
    assert "(Sheer Curtain)" in prompt
    assert "300 ₪" in prompt


def test_for_system_prompt_shows_unavailable(catalog):
    prompt = catalog.for_system_prompt()
    assert "(currently unavailable)" in prompt


def test_for_system_prompt_empty():
    empty = ProductCatalog([])
    assert empty.for_system_prompt() == ""


def test_categories(catalog):
    cats = catalog.categories
    assert "Curtains" in cats
    assert "Sofas" in cats
    assert "Accessories" in cats


def test_to_dicts(catalog):
    dicts = catalog.to_dicts()
    assert len(dicts) == 3
    assert dicts[0]["id"] == "p1"
    assert isinstance(dicts[0]["tags"], list)


def test_load_from_file(tmp_path):
    data = {
        "products": [
            {"id": "t1", "name": "Test Product", "category": "Test", "price": "10"},
        ]
    }
    path = tmp_path / "test.yaml"
    with open(path, "w") as f:
        yaml.dump(data, f)

    cat = ProductCatalog.from_file(path)
    assert len(cat.products) == 1
    assert cat.products[0].id == "t1"


def test_load_empty_file(tmp_path):
    path = tmp_path / "empty.yaml"
    path.write_text("")
    cat = ProductCatalog.from_file(path)
    assert len(cat.products) == 0


def test_save_and_reload(tmp_path, monkeypatch):
    monkeypatch.setattr("chatbot.core.products.PROJECT_ROOT", tmp_path)
    products = [{"id": "s1", "name": "Saved", "category": "Cat", "price": "100"}]
    path = ProductCatalog.save("test_client", products)
    assert path.exists()

    reloaded = ProductCatalog.from_file(path)
    assert len(reloaded.products) == 1
    assert reloaded.products[0].name == "Saved"
