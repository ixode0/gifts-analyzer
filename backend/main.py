"""FastAPI: /api/collections, /api/history, /api/top. Poller every 3 min."""
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio
import json
import logging
import os
import time
from pathlib import Path

import db
import giftstat
import fragment as frag
import giftasset as ga
import portals as por
import tonnel as ton
import thumbs

IMG_MAP_FILE = Path(__file__).parent / "img_map.json"
GA_REFRESH_SECONDS = 21600  # 6 часов: 4 среза/сутки из 10 RPD
_last_ga_ts = 0
_last_ga_hist_date = ""

log = logging.getLogger("poller")
POLL_SECONDS = 180  # 3 мин по ТЗ
FRAGMENT_REFRESH_SECONDS = 1800  # полный обход Fragment каждые 30 мин
_last_fragment_ts = 0


def _merge(base: list, extra: dict, key: str) -> list:
    by_slug = {r["slug"]: r for r in base}
    for slug, val in extra.items():
        if slug in by_slug:
            by_slug[slug][key] = val
        else:
            by_slug[slug] = {"slug": slug, "name": slug, "portals_floor": None, "tonnel_floor": None, "fragment_floor": None, key: val}
    return list(by_slug.values())

app = FastAPI(title="Gifts Analyzer API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

db.init_db()


def _load_img_map() -> dict:
    try:
        return json.loads(IMG_MAP_FILE.read_text())
    except Exception:
        return {}


def _save_img_map(m: dict):
    try:
        IMG_MAP_FILE.write_text(json.dumps(m))
    except Exception:
        pass


def detect_deals(samples: dict, slug_by_tname: dict, frag_floors: dict, min_gap: float = 0.15):
    """Two signals: price gap vs 2nd cheapest of same model; tonnel price below fragment floor."""
    deals = []
    for tname, items in samples.items():
        slug = slug_by_tname.get(tname)
        if not items:
            continue
        by_model: dict = {}
        for it in items:
            by_model.setdefault(it.get("model") or "?", []).append(it)
        for model, lst in by_model.items():
            lst.sort(key=lambda x: x["price"])
            if len(lst) >= 2 and lst[1]["price"] > 0:
                gap = 1 - lst[0]["price"] / lst[1]["price"]
                if gap >= min_gap:
                    first = lst[0]
                    deals.append({
                        "slug": slug, "name": tname, "gift_num": first.get("gift_num"),
                        "model": model, "model_rarity": first.get("model_rarity"),
                        "backdrop": first.get("backdrop") or "", "price": first["price"],
                        "ref_price": lst[1]["price"], "discount_pct": round(gap * 100, 1),
                        "kind": "gap", "market": "tonnel",
                    })
        ff = (frag_floors.get(slug) or 0) if slug else 0
        p0 = items[0]["price"]
        if ff and p0 < ff * 0.95:
            deals.append({
                "slug": slug, "name": tname, "gift_num": items[0].get("gift_num"),
                "model": items[0].get("model") or "", "model_rarity": items[0].get("model_rarity"),
                "backdrop": items[0].get("backdrop") or "", "price": p0,
                "ref_price": ff, "discount_pct": round((1 - p0 / ff) * 100, 1),
                "kind": "xfloor", "market": "tonnel",
            })
    deals.sort(key=lambda d: -d["discount_pct"])
    return deals[:100]


FEES = {"fragment": 0.05, "tonnel": 0.04, "portals": 0.02, "mrkt": 0.02, "getgems": 0.02}


def _ton_rate():
    try:
        return asyncio.run(giftstat.fetch_ton_rate())
    except Exception:
        return 0.0


def _ga_match_slug(slug: str, fname: str, ga_map: dict):
    cands = [ton.to_tonnel_name(fname)] + [c for c in ga.candidates(fname)]
    for c in cands:
        if c and ga.norm(c) in ga_map:
            return ga.norm(c)
    return None


def do_giftasset_poll(force: bool = False):
    """All-market floors every 6h (4 RPD) + history backfill for top-6 (6 RPD/day)."""
    global _last_ga_ts, _last_ga_hist_date
    if not force and time.time() - _last_ga_ts < GA_REFRESH_SECONDS:
        return {"skipped": True}
    if not os.environ.get("GIFTASSET_API_KEY"):
        return {"error": "no GIFTASSET_API_KEY"}
    try:
        ga_map = asyncio.run(ga.fetch_price_list())
        try:
            names = asyncio.run(frag.fetch_collections())
        except Exception:
            names = {r["slug"]: r["name"] for r in db.distinct_slugs()}
        prev = {r["slug"]: r for r in db.latest_snapshot()}
        rows = []
        for slug, fname in names.items():
            g = ga_map.get(_ga_match_slug(slug, fname, ga_map) or "")
            p = prev.get(slug, {})
            rows.append({
                "slug": slug, "name": fname,
                "portals_floor": (g or {}).get("portals") or p.get("portals_floor"),
                "tonnel_floor": (g or {}).get("tonnel") or p.get("tonnel_floor"),
                "fragment_floor": p.get("fragment_floor"),
                "mrkt_floor": (g or {}).get("mrkt"),
                "getgems_floor": (g or {}).get("getgems"),
                "thumb_remote": p.get("thumb_remote", ""),
            })
        # brand-new collections from GiftAsset (not on Fragment yet)
        have = set(names)
        for gnorm, g in ga_map.items():
            if gnorm in [ga.norm(ton.to_tonnel_name(n) or "") for n in names.values()]:
                continue
            sims = [s for s in have]
            slug = ga.slugify(g["display"])
            if slug in have:
                continue
            have.add(slug)
            rows.append({
                "slug": slug, "name": g["display"],
                "portals_floor": g.get("portals"), "tonnel_floor": g.get("tonnel"),
                "fragment_floor": None, "mrkt_floor": g.get("mrkt"),
                "getgems_floor": g.get("getgems"), "thumb_remote": "",
            })
        ts = db.save_snapshot(rows, _ton_rate())
        _last_ga_ts = time.time()
        log.warning(f"giftasset poll ok: {len(rows)} collections ts={ts}")
        # daily history backfill for top-6 (quota: 6/day)
        today = time.strftime("%Y-%m-%d", time.gmtime())
        hist_n = 0
        if today != _last_ga_hist_date:
            priced = [r for r in rows if r["slug"] and (r["portals_floor"] or r["tonnel_floor"] or r["mrkt_floor"] or r["getgems_floor"])]
            priced.sort(key=lambda r: -min([x for x in (r["portals_floor"], r["tonnel_floor"], r["mrkt_floor"], r["getgems_floor"]) if x] or [0]))
            for r in priced[:4]:
                try:
                    h = asyncio.run(ga.fetch_history(r["name"]))
                    pts = []
                    for m, col in (("portals", "portals_floor"), ("tonnel", "tonnel_floor"), ("mrkt", "mrkt_floor"), ("getgems", "getgems_floor")):
                        for tstamp, price in h.get(m, []):
                            pts.append({"ts": tstamp, col: price})
                    # merge per-ts
                    byts: dict = {}
                    for p in pts:
                        byts.setdefault(p["ts"], {"ts": p["ts"]}).update({k: v for k, v in p.items() if k != "ts"})
                    hist_n += db.insert_backfill(r["slug"], r["name"], list(byts.values()))
                except Exception as e:
                    log.warning(f"history fail {r['slug']}: {str(e)[:120]}")
                time.sleep(8)  # не упираться в рейт-лимит GiftAsset
            _last_ga_hist_date = today
            log.warning(f"history backfill: {hist_n} points")
        return {"ok": True, "count": len(rows), "history_points": hist_n}
    except Exception as e:
        log.warning(f"giftasset poll fail: {e}")
        return {"error": str(e)[:300]}


def do_fragment_poll(force: bool = False):
    """Full market refresh: Fragment floors + Tonnel floors + thumbs. Heavy — hourly."""
    global _last_fragment_ts
    if not force and time.time() - _last_fragment_ts < FRAGMENT_REFRESH_SECONDS:
        return {"skipped": True}
    try:
        names = asyncio.run(frag.fetch_collections())
        data = asyncio.run(frag.fetch_all_data(list(names)))
        # tonnel floors (mapped names)
        mapping = {s: ton.to_tonnel_name(n) for s, n in names.items()}
        tnames = sorted(set(m for m in mapping.values() if m))
        tfloors = asyncio.run(ton.fetch_all_floors(tnames)) if tnames else {}
        inv = {m: s for s, m in mapping.items()}
        # portals floors direct (no auth, fresh)
        try:
            pfloors = asyncio.run(por.fetch_floors())
        except Exception as e:
            log.warning(f"portals floors fail: {e}")
            pfloors = {}
        # thumbs: download missing only
        img_map = _load_img_map()
        for s, v in data.items():
            if v.get("img"):
                img_map[s] = v["img"]
        _save_img_map(img_map)
        asyncio.run(thumbs.ensure_thumbs(img_map))
        all_slugs = sorted(set(names) | set(pfloors))
        rows = [{
            "slug": s, "name": names.get(s, s),
            "portals_floor": pfloors.get(s),
            "tonnel_floor": tfloors.get(mapping.get(s)),
            "fragment_floor": (data.get(s) or {}).get("floor"), "thumb_remote": img_map.get(s, ""),
        } for s in all_slugs]
        # merge with latest snapshot so transient fetch misses don't wipe prices
        prev = {r["slug"]: r for r in db.latest_snapshot()}
        for r in rows:
            p = prev.get(r["slug"], {})
            for k in ("portals_floor", "tonnel_floor", "fragment_floor", "mrkt_floor", "getgems_floor", "thumb_remote"):
                if not r.get(k) and p.get(k):
                    r[k] = p[k]
        ts = db.save_snapshot(rows, _ton_rate())
        _last_fragment_ts = time.time()
        log.warning(f"market poll ok: {len(rows)} collections ts={ts}")
        # listings samples -> deals (heaviest part, same hourly cadence)
        try:
            inv_map = {m: s for s, m in mapping.items()}
            samples = asyncio.run(ton.fetch_samples(tnames))
            frag_map = {r["slug"]: (r["fragment_floor"] or 0) for r in rows}
            deals = detect_deals(samples, inv_map, frag_map)
            if deals:
                db.save_deals(deals)
            log.warning(f"deals ok: {len(deals)}")
        except Exception as e:
            log.warning(f"deals fail: {e}")
        return {"ok": True, "count": len(rows)}
    except Exception as e:
        log.warning(f"fragment poll fail: {e}")
        return {"error": str(e)[:300]}


def do_poll():
    try:
        rows, ton_rate = asyncio.run(giftstat.fetch_snapshot())
        if rows:
            # keep previous market prices when fresh fetch has gaps
            prev = {r["slug"]: r for r in db.latest_snapshot()}
            for r in rows:
                p = prev.get(r["slug"], {})
                for k in ("portals_floor", "tonnel_floor", "fragment_floor", "mrkt_floor", "getgems_floor", "thumb_remote"):
                    if not r.get(k) and p.get(k):
                        r[k] = p[k]
            ts = db.save_snapshot(rows, ton_rate)
            log.warning(f"poll ok: {len(rows)} collections ts={ts}")
        else:
            log.warning("poll empty")
    except Exception as e:
        log.warning(f"poll fail: {e}")


scheduler = None
try:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(do_poll, "interval", seconds=POLL_SECONDS)
    scheduler.add_job(do_fragment_poll, "interval", seconds=FRAGMENT_REFRESH_SECONDS)
    scheduler.add_job(do_giftasset_poll, "interval", seconds=GA_REFRESH_SECONDS)
    scheduler.start()
except Exception as e:
    log.warning(f"scheduler disabled: {e}")


@app.get("/api/health")
def health():
    return {"ok": True, "poll_seconds": POLL_SECONDS, "giftasset_every": GA_REFRESH_SECONDS}


@app.post("/api/poll")
def poll_now():
    do_poll()
    return {"ok": True, "count": len(db.latest_snapshot())}


@app.post("/api/poll-fragment")
def poll_fragment_now():
    return do_fragment_poll(force=True)


@app.post("/api/poll-giftasset")
def poll_giftasset_now():
    return do_giftasset_poll(force=True)


@app.get("/api/collections")
def collections():
    """Latest snapshot: one row per gift (collection-level, no models)."""
    rows = db.latest_snapshot()
    img_map = _load_img_map()
    out = []
    for r in rows:
        keys = r.keys()
        pf = r["portals_floor"]
        tf = r["tonnel_floor"]
        ff = r["fragment_floor"] if "fragment_floor" in keys else None
        mf = r["mrkt_floor"] if "mrkt_floor" in keys else None
        gf = r["getgems_floor"] if "getgems_floor" in keys else None
        spread = None
        if pf and tf:
            spread = round((pf - tf) / tf * 100, 2) if tf else None
        floors = [x for x in (pf, tf, ff, mf, gf) if x]
        out.append({
            "slug": r["slug"],
            "name": r["name"],
            "portals_floor": pf,
            "tonnel_floor": tf,
            "fragment_floor": ff,
            "mrkt_floor": mf,
            "getgems_floor": gf,
            "min_floor": min(floors) if floors else None,
            "spread_pct": spread,
            "thumb": thumbs.thumb_url(r["slug"], (r["thumb_remote"] or None) if "thumb_remote" in keys else None),
            "ton_rate": r["ton_rate"],
            "ts": r["ts"],
        })
    # backfill names if db empty
    if not out:
        return {"data": [], "empty": True, "hint": "POST /api/poll-fragment to fetch first snapshot"}
    return {"data": out}


@app.get("/api/deals")
def deals(limit: int = Query(100, ge=1, le=200)):
    """Undervalued Tonnel listings: gap vs 2nd cheapest of same model + below fragment floor."""
    rows = db.latest_deals(limit)
    thumbs_by_slug = {}
    for r in db.latest_snapshot():
        keys = r.keys()
        thumbs_by_slug[r["slug"]] = thumbs.thumb_url(r["slug"], (r["thumb_remote"] or None) if "thumb_remote" in keys else None)
    for d in rows:
        d["thumb"] = thumbs_by_slug.get(d["slug"], "")
    return {"data": rows}


@app.get("/api/arbitrage")
def arbitrage(min_net_pct: float = Query(2.0)):
    """Cross-market spreads NET of taker fees. buy low -> sell high."""
    rows = db.latest_snapshot()
    out = []
    for r in rows:
        px = {m: r[m] for m in ("fragment_floor", "tonnel_floor", "portals_floor", "mrkt_floor", "getgems_floor")
              if r.keys().__contains__(m) and r[m]}
        if len(px) < 2:
            continue
        mk = {"fragment_floor": "fragment", "tonnel_floor": "tonnel", "portals_floor": "portals", "mrkt_floor": "mrkt", "getgems_floor": "getgems"}
        for bk, buy in px.items():
            for sk, sell in px.items():
                if sk == bk or sell <= buy:
                    continue
                b, s = mk[bk], mk[sk]
                cost = buy * (1 + FEES.get(b, 0.05))
                revenue = sell * (1 - FEES.get(s, 0.05))
                net = revenue - cost
                net_pct = net / cost * 100
                if net_pct >= min_net_pct:
                    out.append({
                        "slug": r["slug"], "name": r["name"],
                        "buy_market": b, "buy_price": buy,
                        "sell_market": s, "sell_price": sell,
                        "net_ton": round(net, 2), "net_pct": round(net_pct, 2),
                    })
    out.sort(key=lambda x: -x["net_pct"])
    return {"fees": FEES, "data": out[:100]}


@app.get("/api/debug-tonnel")
async def debug_tonnel(gift: str = Query("Plush Pepe")):
    import time as _t
    import json as _json
    from curl_cffi.requests import AsyncSession
    hosts = [
        "https://gifts2.tonnel.network/api/pageGifts",
        "https://rs-market.tonnel.network/api/pageGifts",
    ]
    out = []
    for host in hosts:
        t0 = _t.time()
        try:
            async with AsyncSession(impersonate="chrome") as s:
                r = await s.post(
                    host,
                    json={"page": 1, "limit": 1, "sort": _json.dumps({"price": 1}),
                          "filter": _json.dumps({"gift_name": gift, "asset": "TON"}),
                          "price_range": None, "user_auth": ""},
                    headers={"Origin": "https://market.tonnel.network", "Referer": "https://market.tonnel.network/"},
                    timeout=15,
                )
                out.append({"host": host, "status": r.status_code, "len": len(r.text),
                            "head": r.text[:120], "dt": round(_t.time() - t0, 1)})
        except Exception as e:
            out.append({"host": host, "error": f"{type(e).__name__}: {str(e)[:150]}", "dt": round(_t.time() - t0, 1)})
    return {"gift": gift, "probes": out}


@app.get("/api/history")
def history(slug: str = Query(...), days: int = Query(7, ge=1, le=90)):
    rows = db.history(slug, days)
    return {"slug": slug, "days": days, "data": rows, "count": len(rows)}


@app.get("/api/history-remote")
async def history_remote(marketplace: str = "portals", scale: str = "day", days: int = 7):
    """Proxy to Giftstat history — for backfill when local DB is young."""
    try:
        data = await giftstat.fetch_remote_history(marketplace, scale, days)
        return {"marketplace": marketplace, "scale": scale, "days": days, "data": data}
    except Exception as e:
        return {"error": str(e)[:500]}


@app.get("/api/top")
def top(period: str = Query("24h")):
    """Top movers by floor change. period: 24h (uses oldest point in last 24h)."""
    import time
    hours = 24 if period == "24h" else 168  # 24h | 7d
    since = int(time.time()) - hours * 3600
    import sqlite3
    conn = db.get_conn()
    slugs = [r["slug"] for r in conn.execute("SELECT DISTINCT slug FROM prices").fetchall()]
    res = []
    for s in slugs:
        pts = conn.execute(
            "SELECT portals_floor, tonnel_floor, fragment_floor, mrkt_floor, getgems_floor, ts FROM prices WHERE slug=? AND ts>=? ORDER BY ts ASC",
            (s, since),
        ).fetchall()
        if len(pts) < 2:
            continue
        # first market series that has data
        old, new = None, None
        for col in range(5):
            vals = [r[col] for r in pts if r[col]]
            if len(vals) >= 2:
                old, new = vals[0], vals[-1]
                break
        if old and new and old > 0:
            chg = round((new - old) / old * 100, 2)
            res.append({"slug": s, "old": old, "new": new, "change_pct": chg})
    conn.close()
    res.sort(key=lambda x: x["change_pct"], reverse=True)
    return {"period": period, "gainers": res[:20], "losers": list(reversed(res[-20:]))}
