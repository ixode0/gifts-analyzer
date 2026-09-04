"""GiftAsset API: all-market floors + history. Key via GIFTASSET_API_KEY env.
Docs: GIFT-ASSET/giftasset_mcp client.py. Budget: 10 RPD.
  - price_list (1 call = all collections x getgems/mrkt/portals/tonnel) every 6h = 4/day
  - history per top collection, rest of quota
"""
import asyncio
import os
from datetime import datetime, timezone

import httpx

BASE = "https://api.giftasset.dev"
MARKETS = ("getgems", "mrkt", "portals", "tonnel")


def _key() -> str:
    return os.environ.get("GIFTASSET_API_KEY", "")


def _headers() -> dict:
    return {"x-api-token": _key(), "Accept-Encoding": "gzip, deflate"}


def norm(name: str) -> str:
    name = name.replace("\u2019", "'").replace("'", "")
    return " ".join(name.strip().lower().split())


def candidates(fragment_plural: str) -> list:
    """All singular variants (normalized) for a Fragment plural name."""
    p = fragment_plural.replace("\u2019", "'").strip()
    out = [p]
    if p.endswith("ies"):
        out.append(p[:-3] + "y")
    if p.endswith("s") and not p.endswith("ss"):
        out.append(p[:-1])
    if p.endswith("es"):
        out.append(p[:-2])
    return [norm(c) for c in out]


def match_slugs(frag_names: dict, ga_map: dict) -> tuple:
    """Return ({slug: ga_norm_name}, [extra ga_norms not in frag])."""
    matched, used = {}, set()
    for slug, fname in frag_names.items():
        for c in candidates(fname):
            if c in ga_map:
                matched[slug] = c
                used.add(c)
                break
    extras = [k for k in ga_map if k not in used]
    return matched, extras


def slugify(display: str) -> str:
    import re as _re
    return _re.sub(r"[^a-z0-9]+", "", display.lower())


async def fetch_price_list() -> dict:
    """Return {norm_name: {market: floor, 'display': original_name}}."""
    async with httpx.AsyncClient(timeout=40, headers=_headers()) as c:
        r = await c.get(f"{BASE}/api/v1/gifts/get_gifts_price_list",
                        params={"models": "false", "premarket": "false"})
        r.raise_for_status()
        data = r.json()
        res = data.get("result", data)
        floors = res.get("collection_floors", {}) if isinstance(res, dict) else {}
    out = {}
    for display, per in floors.items():
        if not isinstance(per, dict):
            continue
        row = {"display": display}
        for m in MARKETS:
            v = per.get(m)
            try:
                row[m] = float(v) if v else None
            except (TypeError, ValueError):
                row[m] = None
        out[norm(display)] = row
    return out


def _parse_ts(s: str) -> int | None:
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return int(datetime.strptime(s, fmt).replace(tzinfo=timezone.utc).timestamp())
        except ValueError:
            continue
    return None


async def fetch_history(collection_name: str) -> dict:
    """Return {market: [(ts, price)]} merged 24h+7d for one collection."""
    async with httpx.AsyncClient(timeout=40, headers=_headers()) as c:
        r = await c.get(f"{BASE}/api/v1/gifts/get_gifts_price_list_history",
                        params={"collection_name": collection_name})
        r.raise_for_status()
        data = r.json()
        res = data.get("result", data)
    out: dict = {}
    if isinstance(res, dict):
        for _coll, per in res.items():
            if not isinstance(per, dict):
                continue
            for m in MARKETS:
                blk = per.get(m)
                if not isinstance(blk, dict):
                    continue
                pts: dict = {}
                for scale in ("24h", "7d"):
                    for ts_s, price in (blk.get(scale) or {}).items():
                        ts = _parse_ts(ts_s)
                        try:
                            p = float(price)
                        except (TypeError, ValueError):
                            continue
                        if ts and p:
                            pts[ts] = p
                if pts:
                    out[m] = sorted(pts.items())
    return out
