"""Tonnel floors via public gifts2 API (no auth needed for browsing).
Docs: boostNT/Tonnel-Api — POST https://gifts2.tonnel.network/api/pageGifts
Requires curl_cffi (Cloudflare) — plain httpx gets 403.
"""
import asyncio
import json

from curl_cffi.requests import AsyncSession

API = "https://gifts2.tonnel.network/api/pageGifts"
HEADERS = {
    "Origin": "https://market.tonnel.network",
    "Referer": "https://market.tonnel.network/",
    "Content-Type": "application/json",
}
MANUAL = {
    "Jacks-in-the-Box": "Jack-in-the-Box",
}


def to_tonnel_name(fragment_plural: str, known: set | None = None) -> str | None:
    """Plural Fragment name -> singular Tonnel gift_name (case preserved — filter is case-sensitive)."""
    p = fragment_plural.replace("\u2019", "'").strip()
    if p in MANUAL:
        return MANUAL[p]
    cands = [p]
    if p.endswith("ies"):
        cands.append(p[:-3] + "y")
    if p.endswith("s") and not p.endswith("ss"):
        cands.append(p[:-1])
    if p.endswith("es"):
        cands.append(p[:-2])
    if known is not None:
        kl = {k.lower(): k for k in known}
        # prefer case-preserving candidate that matches known (case-insensitive)
        for c in cands:
            if c.lower() in kl:
                return c  # keep original case: "Plush Pepes" -> "Plush Pepe"
        return None
    return cands[1] if len(cands) > 1 else p


async def _floor_one(session: AsyncSession, sem: asyncio.Semaphore, gift_name: str):
    async with sem:
        try:
            body = {
                "page": 1, "limit": 1,
                "sort": json.dumps({"price": 1}),
                "filter": json.dumps({
                    "price": {"$exists": True}, "refunded": {"$ne": True},
                    "buyer": {"$exists": False}, "export_at": {"$exists": True},
                    "gift_name": gift_name, "asset": "TON",
                }),
                "price_range": None, "user_auth": "",
            }
            r = await session.post(API, json=body, headers=HEADERS, timeout=20)
            items = r.json()
            if isinstance(items, list) and items and items[0].get("price") is not None:
                return gift_name, float(items[0]["price"])
        except Exception:
            pass
        return gift_name, None


async def fetch_all_floors(gift_names: list, concurrency: int = 4) -> dict:
    """Return {gift_name: floor_ton or None}."""
    sem = asyncio.Semaphore(concurrency)
    async with AsyncSession(impersonate="chrome") as session:
        results = await asyncio.gather(*[_floor_one(session, sem, g) for g in gift_names])
    return dict(results)


def _parse_rarity(s: str | None) -> tuple[str, float | None]:
    """'Two Face (2%)' -> ('Two Face', 2.0)."""
    if not s:
        return "", None
    import re as _re
    m = _re.match(r"^(.*)\(([0-9.]+)%\)\s*$", s)
    if m:
        try:
            return m.group(1).strip(), float(m.group(2))
        except ValueError:
            pass
    return s, None


async def _sample_one(session: AsyncSession, sem: asyncio.Semaphore, gift_name: str, limit: int = 20):
    """Cheapest `limit` listings for a collection, price asc."""
    import json as _json
    async with sem:
        try:
            body = {
                "page": 1, "limit": limit,
                "sort": _json.dumps({"price": 1}),
                "filter": _json.dumps({
                    "price": {"$exists": True}, "refunded": {"$ne": True},
                    "buyer": {"$exists": False}, "export_at": {"$exists": True},
                    "gift_name": gift_name, "asset": "TON",
                }),
                "price_range": None, "user_auth": "",
            }
            r = await session.post(API, json=body, headers=HEADERS, timeout=25)
            items = r.json()
            out = []
            if isinstance(items, list):
                for it in items:
                    if not isinstance(it, dict) or it.get("price") is None:
                        continue
                    model, model_r = _parse_rarity(it.get("model"))
                    out.append({
                        "gift_name": gift_name,
                        "gift_num": it.get("gift_num"),
                        "gift_id": it.get("gift_id"),
                        "price": float(it["price"]),
                        "model": model, "model_rarity": model_r,
                        "backdrop": it.get("backdrop"),
                        "symbol": it.get("symbol"),
                    })
            return gift_name, out
        except Exception:
            return gift_name, []


async def fetch_samples(gift_names: list, limit: int = 20, concurrency: int = 3) -> dict:
    """Return {gift_name: [listings asc]}."""
    sem = asyncio.Semaphore(concurrency)
    async with AsyncSession(impersonate="chrome") as session:
        results = await asyncio.gather(*[_sample_one(session, sem, g, limit) for g in gift_names])
    return dict(results)
