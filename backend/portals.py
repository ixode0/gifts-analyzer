"""Portals direct API (no auth needed for public floors).
Reversed from bleach-hub/aportalsmp + l0v3m0n3y/portalsmarket.
Base: https://portal-market.com/api
"""
import httpx

BASE = "https://portal-market.com/api"
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://portal-market.com",
    "Referer": "https://portal-market.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
}
TIMEOUT = 25.0


async def fetch_floors() -> dict:
    """Return {slug: floor_ton}. Keys are already short names (== our slugs)."""
    async with httpx.AsyncClient(timeout=TIMEOUT, headers=HEADERS) as c:
        r = await c.get(f"{BASE}/collections/floors")
        r.raise_for_status()
        data = r.json()
        fp = data.get("floorPrices", {}) if isinstance(data, dict) else {}
    out = {}
    for slug, v in fp.items():
        try:
            out[str(slug)] = float(v) if v is not None else None
        except (TypeError, ValueError):
            out[str(slug)] = None
    return out


async def fetch_config() -> dict:
    async with httpx.AsyncClient(timeout=TIMEOUT, headers=HEADERS) as c:
        r = await c.get(f"{BASE}/market/config")
        r.raise_for_status()
        return r.json()
