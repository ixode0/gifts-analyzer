"""One-shot deals computation: tonnel samples -> detect -> save."""
import asyncio
import json
import sys

import db
import main
import tonnel as ton

with open("/tmp/tonnel_mapping.json") as f:
    MAPPING = json.load(f)  # slug -> tonnel name


def run():
    db.init_db()
    tnames = sorted(set(m for m in MAPPING.values() if m))
    print(f"sampling {len(tnames)} collections...", flush=True)
    samples = asyncio.run(ton.fetch_samples(tnames, limit=20))
    print("samples done", flush=True)
    inv = {m: s for s, m in MAPPING.items()}
    prev = {r["slug"]: (r["fragment_floor"] or 0) for r in db.latest_snapshot()}
    deals = main.detect_deals(samples, inv, prev)
    print(f"deals: {len(deals)}", flush=True)
    if deals:
        db.save_deals(deals)
        for d in deals[:10]:
            print(f"{d['discount_pct']}% {d['name']} #{d['gift_num']} {d['model']} {d['price']} vs {d['ref_price']} [{d['kind']}]", flush=True)


if __name__ == "__main__":
    sys.exit(run())
