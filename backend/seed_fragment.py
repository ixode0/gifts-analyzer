"""One-shot seed: wipe DB, load Fragment floors + Tonnel floors + local thumbs."""
import asyncio
import json
import sys
from pathlib import Path

import db
import fragment as frag
import giftstat
import thumbs
import tonnel as ton

IMG_MAP_FILE = Path(__file__).parent / "img_map.json"


def main():
    db.init_db()
    print("fetching collections...", flush=True)
    names = asyncio.run(frag.fetch_collections())
    print(f"collections: {len(names)}", flush=True)

    print("fetching fragment floors+imgs...", flush=True)
    data = asyncio.run(frag.fetch_all_data(list(names)))
    ff = sum(1 for v in data.values() if v["floor"])
    print(f"fragment floors: {ff}/{len(data)}", flush=True)

    print("fetching tonnel floors...", flush=True)
    mapping = {s: ton.to_tonnel_name(n) for s, n in names.items()}
    tnames = sorted(set(m for m in mapping.values() if m))
    tfloors = asyncio.run(ton.fetch_all_floors(tnames))
    tf = sum(1 for v in tfloors.values() if v)
    print(f"tonnel floors: {tf}/{len(tfloors)}", flush=True)

    print("downloading thumbs...", flush=True)
    img_map = {s: v["img"] for s, v in data.items() if v.get("img")}
    IMG_MAP_FILE.write_text(json.dumps(img_map))
    asyncio.run(thumbs.ensure_thumbs(img_map))
    import pathlib
    got = len(list(pathlib.Path(thumbs.IMG_DIR).glob("*.jpg"))) if thumbs.IMG_DIR.exists() else 0
    print(f"thumbs local: {got}", flush=True)

    try:
        rate = asyncio.run(giftstat.fetch_ton_rate())
    except Exception:
        rate = 0.0

    conn = db.get_conn()
    conn.execute("DELETE FROM prices")
    conn.commit()
    conn.close()
    rows = [{
        "slug": s, "name": names[s],
        "portals_floor": None,
        "tonnel_floor": tfloors.get(mapping.get(s)),
        "fragment_floor": data[s]["floor"],
    } for s in names]
    ts = db.save_snapshot(rows, rate)
    print(f"saved snapshot ts={ts}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
