"""Fetch floors from Giftstat public API (no key).
Endpoints (from teleton giftstat plugin):
  GET /current/collections
  GET /current/collections/floor?marketplace=portals|tonnel
  GET /history/collections/floor?marketplace=portals&scale=day|hour
  GET /current/ton-rate
"""
import httpx

API_BASE = "https://api.giftstat.app"
TIMEOUT = 20.0


async def _get(path: str, params: dict | None = None):
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r = await c.get(f"{API_BASE}{path}", params=params or {})
        r.raise_for_status()
        return r.json()


async def fetch_ton_rate() -> float:
    try:
        data = await _get("/current/ton-rate")
        # shape varies: {"rate": x} / {"ton_rate": x} / {"data": ...}
        if isinstance(data, dict):
            for k in ("rate", "ton_rate", "price", "usd"):
                if k in data and isinstance(data[k], (int, float)):
                    return float(data[k])
            d = data.get("data")
            if isinstance(d, dict):
                for k in ("rate", "ton_rate", "price"):
                    if k in d and isinstance(d[k], (int, float)):
                        return float(d[k])
        if isinstance(data, (int, float)):
            return float(data)
    except Exception:
        pass
    return 0.0


def _norm_floor_payload(data) -> dict:
    """Return {slug: floor} from various Giftstat shapes."""
    out: dict = {}
    items = data
    if isinstance(data, dict):
        for k in ("data", "result", "items", "collections"):
            if k in data and isinstance(data[k], list):
                items = data[k]
                break
    if not isinstance(items, list):
        return out
    for it in items:
        if not isinstance(it, dict):
            continue
        slug = it.get("slug") or it.get("collection") or it.get("id")
        floor = it.get("floor") or it.get("floor_price") or it.get("floorPrice") or it.get("price")
        # nested: {"collection": {"slug": ...}, "floor": ...}
        if isinstance(it.get("collection"), dict):
            slug = it["collection"].get("slug", slug)
        if slug is None:
            continue
        try:
            out[str(slug)] = float(floor) if floor is not None else None
        except (TypeError, ValueError):
            out[str(slug)] = None
    return out


def _norm_collections(data) -> dict:
    """Return {slug: name}."""
    out: dict = {}
    items = data
    if isinstance(data, dict):
        for k in ("data", "result", "items", "collections"):
            if k in data and isinstance(data[k], list):
                items = data[k]
                break
    if not isinstance(items, list):
        return out
    for it in items:
        if not isinstance(it, dict):
            continue
        slug = it.get("slug") or it.get("id")
        name = it.get("name") or it.get("title") or str(slug)
        if slug:
            out[str(slug)] = str(name)
    return out


async def fetch_snapshot():
    """Returns rows: [{slug, name, portals_floor, tonnel_floor}]"""
    collections = await _get("/current/collections", {"limit": 200})
    names = _norm_collections(collections)

    portals = await _get("/current/collections/floor", {"marketplace": "portals", "limit": 200})
    tonnel = await _get("/current/collections/floor", {"marketplace": "tonnel", "limit": 200})
    pf = _norm_floor_payload(portals)
    tf = _norm_floor_payload(tonnel)

    slugs = set(names) | set(pf) | set(tf)
    rows = []
    for s in sorted(slugs):
        rows.append({
            "slug": s,
            "name": names.get(s, s),
            "portals_floor": pf.get(s),
            "tonnel_floor": tf.get(s),
        })
    ton_rate = await fetch_ton_rate()
    return rows, ton_rate


async def fetch_remote_history(marketplace: str = "portals", scale: str = "day", days: int = 7):
    """Fallback when local DB is empty — proxy to Giftstat history."""
    return await _get("/history/collections/floor", {
        "marketplace": marketplace, "scale": scale, "days": days, "limit": 200,
    })
