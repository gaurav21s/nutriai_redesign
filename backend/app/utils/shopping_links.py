"""Shopping link generation utilities."""

from __future__ import annotations

import urllib.parse


def generate_amazon_link(ingredient: str, affiliate_code: str) -> str:
    params = {
        "k": ingredient,
        "linkCode": "ll2",
        "tag": affiliate_code,
    }
    return f"https://www.amazon.com/s?{urllib.parse.urlencode(params)}"


def generate_blinkit_link(ingredient: str) -> str:
    params = {"q": ingredient}
    return f"https://blinkit.com/s/?{urllib.parse.urlencode(params)}"


def build_shopping_links(ingredients: list[str], affiliate_code: str) -> dict[str, dict[str, str]]:
    links: dict[str, dict[str, str]] = {}
    for ingredient in ingredients:
        normalized = ingredient.strip()
        if not normalized:
            continue
        links[normalized] = {
            "amazon": generate_amazon_link(normalized, affiliate_code),
            "blinkit": generate_blinkit_link(normalized),
        }
    return links
