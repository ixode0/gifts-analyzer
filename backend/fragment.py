"""Fragment parser: collections list + floor prices.
Works without API keys — plain HTML scraping of fragment.com.
"""
import asyncio
import re

import httpx

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
TIMEOUT = 25.0


async def fetch_collections() -> dict:
    """Return {slug: name} parsed from fragment.com/gifts filter list."""
    async with httpx.AsyncClient(timeout=TIMEOUT, headers={"User-Agent": UA}) as c:
        r = await c.get("https://fragment.com/gifts")
        r.raise_for_status()
        pairs = re.findall(r'data-keywords="([^"]+)"\s+data-value="([a-z0-9]+)"', r.text)
    seen: dict = {}
    for name, slug in pairs:
        if slug not in seen:
            seen[slug] = name.strip()
    return seen


async def _floor_one(client: httpx.AsyncClient, sem: asyncio.Semaphore, slug: str):
    async with sem:
        try:
            r = await client.get(f"https://fragment.com/gifts/{slug}?filter=sale&sort=price_asc")
            m = re.search(r'tm-grid-item-value tm-value icon-before icon-ton">([0-9,]+)</div>', r.text)
            img = re.search(r'<img src="(https://nft\.fragment\.com/gift/[^"]+\.(?:medium\.jpg|thumb\.webp))"', r.text)
            floor = float(m.group(1).replace(",", "")) if m else None
            return slug, {"floor": floor, "img": img.group(1) if img else None}
        except Exception:
            pass
        return slug, {"floor": None, "img": None}


async def fetch_all_data(slugs: list, concurrency: int = 8) -> dict:
    """Return {slug: {floor, img}} for sale listings on Fragment."""
    import httpx as _httpx  # local import to keep module light
    sem = asyncio.Semaphore(concurrency)
    async with _httpx.AsyncClient(timeout=TIMEOUT, headers={"User-Agent": UA}) as client:
        results = await asyncio.gather(*[_floor_one(client, sem, s) for s in slugs])
    return dict(results)


async def fetch_all_floors(slugs: list, concurrency: int = 8) -> dict:
    """Return {slug: floor_ton or None} for sale listings on Fragment."""
    data = await fetch_all_data(slugs, concurrency)
    return {s: v["floor"] for s, v in data.items()}


def thumb_url(slug: str) -> str:
    return f"https://fragment.com/gifts/{slug}/thumb.webp"
