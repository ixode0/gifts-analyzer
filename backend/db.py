"""SQLite storage. One table for collection-level floors.
Polled every 3 min. No models/backdrops in v1.
"""
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).parent / "prices.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL,
    name TEXT DEFAULT '',
    portals_floor REAL,
    tonnel_floor REAL,
    fragment_floor REAL,
    mrkt_floor REAL,
    getgems_floor REAL,
    thumb_remote TEXT DEFAULT '',
    ton_rate REAL DEFAULT 0,
    ts INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_prices_slug_ts ON prices(slug, ts);
CREATE INDEX IF NOT EXISTS idx_prices_ts ON prices(ts);
"""

MIGRATIONS = [
    "ALTER TABLE prices ADD COLUMN fragment_floor REAL",
    "ALTER TABLE prices ADD COLUMN thumb_remote TEXT",
    "ALTER TABLE prices ADD COLUMN mrkt_floor REAL",
    "ALTER TABLE prices ADD COLUMN getgems_floor REAL",
    """CREATE TABLE IF NOT EXISTS deals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT NOT NULL,
        name TEXT DEFAULT '',
        gift_num INTEGER,
        model TEXT DEFAULT '',
        model_rarity REAL,
        backdrop TEXT DEFAULT '',
        price REAL NOT NULL,
        ref_price REAL NOT NULL,
        discount_pct REAL NOT NULL,
        kind TEXT DEFAULT 'gap',
        market TEXT DEFAULT 'tonnel',
        ts INTEGER NOT NULL
    )""",
    "CREATE INDEX IF NOT EXISTS idx_deals_ts ON deals(ts)",
]


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA)
    for sql in MIGRATIONS:
        try:
            conn.execute(sql)
        except Exception:
            pass  # column already exists
    conn.commit()
    conn.close()


def save_snapshot(rows: list[dict], ton_rate: float):
    """rows: [{slug, name, portals_floor, tonnel_floor, fragment_floor}]"""
    ts = int(time.time())
    conn = get_conn()
    for r in rows:
        conn.execute(
            "INSERT INTO prices (slug, name, portals_floor, tonnel_floor, fragment_floor, mrkt_floor, getgems_floor, thumb_remote, ton_rate, ts) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (r.get("slug"), r.get("name", ""), r.get("portals_floor"), r.get("tonnel_floor"), r.get("fragment_floor"), r.get("mrkt_floor"), r.get("getgems_floor"), r.get("thumb_remote", ""), ton_rate, ts),
        )
    conn.commit()
    conn.close()
    return ts


def latest_snapshot():
    conn = get_conn()
    row = conn.execute("SELECT MAX(ts) as ts FROM prices").fetchone()
    if not row or not row["ts"]:
        conn.close()
        return []
    ts = row["ts"]
    rows = conn.execute("SELECT * FROM prices WHERE ts = ?", (ts,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def history(slug: str, days: int = 7, limit: int = 5000):
    since = int(time.time()) - days * 86400
    conn = get_conn()
    rows = conn.execute(
        "SELECT slug, name, portals_floor, tonnel_floor, fragment_floor, mrkt_floor, getgems_floor, thumb_remote, ton_rate, ts FROM prices WHERE slug = ? AND ts >= ? ORDER BY ts ASC LIMIT ?",
        (slug, since, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_backfill(slug: str, name: str, points: list):
    """points: [{ts, portals_floor, tonnel_floor, mrkt_floor, getgems_floor}]. Skip ts already present."""
    conn = get_conn()
    have = {r["ts"] for r in conn.execute("SELECT ts FROM prices WHERE slug = ?", (slug,)).fetchall()}
    n = 0
    for p in points:
        if p["ts"] in have:
            continue
        conn.execute(
            "INSERT INTO prices (slug, name, portals_floor, tonnel_floor, fragment_floor, mrkt_floor, getgems_floor, thumb_remote, ton_rate, ts) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (slug, name, p.get("portals_floor"), p.get("tonnel_floor"), None, p.get("mrkt_floor"), p.get("getgems_floor"), "", 0, p["ts"]),
        )
        n += 1
    conn.commit()
    conn.close()
    return n


def distinct_slugs():
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT slug, name FROM prices").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_deals(deals: list[dict]):
    import time as _t
    ts = int(_t.time())
    conn = get_conn()
    for d in deals:
        conn.execute(
            """INSERT INTO deals (slug, name, gift_num, model, model_rarity, backdrop, price, ref_price, discount_pct, kind, market, ts)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (d.get("slug"), d.get("name", ""), d.get("gift_num"), d.get("model", ""), d.get("model_rarity"),
             d.get("backdrop", ""), d["price"], d["ref_price"], d["discount_pct"], d.get("kind", "gap"), d.get("market", "tonnel"), ts),
        )
    conn.commit()
    conn.close()
    return ts


def latest_deals(limit: int = 100):
    conn = get_conn()
    row = conn.execute("SELECT MAX(ts) as ts FROM deals").fetchone()
    if not row or not row["ts"]:
        conn.close()
        return []
    rows = conn.execute("SELECT * FROM deals WHERE ts = ? ORDER BY discount_pct DESC LIMIT ?", (row["ts"], limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
