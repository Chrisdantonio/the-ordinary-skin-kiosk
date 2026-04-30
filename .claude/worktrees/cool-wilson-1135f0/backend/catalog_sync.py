"""
Fetches product context from The Ordinary's immersive pop-up page.
Returns a list of lightweight product dicts that the regimen agent can pass
to Claude alongside the local catalog.
"""
import json
import re

import httpx

from log_utils import get_logger

POPUP_URL = "https://theordinary.com/en-us/the-ordinary-immersive-pop-up.html"

log = get_logger("catalog_sync")

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _extract_json_ld(html: str) -> list[dict]:
    """Pull JSON-LD Product nodes from the page HTML."""
    products = []
    for raw in re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        re.DOTALL | re.IGNORECASE,
    ):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        nodes = data if isinstance(data, list) else [data]
        for node in nodes:
            if node.get("@type") == "Product":
                products.append({
                    "name": node.get("name", ""),
                    "description": node.get("description", ""),
                    "url": node.get("url", ""),
                    "sku": node.get("sku", ""),
                    "price": (node.get("offers") or {}).get("price", ""),
                    "source": "json-ld",
                })
    return products


def _extract_shopify_products(html: str) -> list[dict]:
    """Extract products embedded in Shopify window.__st / script JSON blocks."""
    products = []
    # Shopify section renders: {"products":[...]} or product handles in data attrs
    for raw in re.findall(r'"products"\s*:\s*(\[.*?\])', html, re.DOTALL):
        try:
            items = json.loads(raw)
            for item in items:
                if isinstance(item, dict) and item.get("title"):
                    products.append({
                        "name": item.get("title", ""),
                        "description": item.get("description", "") or item.get("body_html", ""),
                        "url": f"https://theordinary.com/products/{item.get('handle', '')}",
                        "price": str((item.get("variants") or [{}])[0].get("price", "")),
                        "source": "shopify-embedded",
                    })
        except json.JSONDecodeError:
            pass
    return products


def _extract_product_titles(html: str) -> list[dict]:
    """Last-resort: pull product names from h2/h3/h4 tags with typical PDP patterns."""
    titles = re.findall(
        r'<(?:h[234]|span)[^>]+class="[^"]*(?:product[_-]title|product[_-]name)[^"]*"[^>]*>(.*?)</(?:h[234]|span)>',
        html,
        re.DOTALL | re.IGNORECASE,
    )
    return [
        {"name": re.sub(r"<[^>]+>", "", t).strip(), "source": "title-scrape"}
        for t in titles
        if re.sub(r"<[^>]+>", "", t).strip()
    ]


def fetch_popup_products(timeout: float = 8.0) -> list[dict]:
    """
    Fetch product data from The Ordinary immersive pop-up page.
    Returns an empty list on any network or parse error so the caller can
    gracefully fall back to the local catalog.
    """
    log.info(f"Fetching popup page: {POPUP_URL}")
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(POPUP_URL, headers=_HEADERS)
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        log.warning(f"HTTP error fetching popup page: {exc}")
        return []
    except Exception as exc:
        log.warning(f"Unexpected error fetching popup page: {exc}")
        return []

    html = resp.text
    log.debug(f"Fetched {len(html):,} bytes from popup page (status {resp.status_code})")

    products = _extract_json_ld(html)
    if not products:
        products = _extract_shopify_products(html)
    if not products:
        products = _extract_product_titles(html)

    log.info(
        f"Popup page extraction complete — "
        f"{len(products)} product(s) found via "
        f"{products[0]['source'] if products else 'none'}"
    )
    return products
