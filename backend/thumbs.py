"""Local thumbnails: download once from nft.fragment.com, serve via /static.
Keeps the site fast (no hotlinking, lazy <img> 46px on frontend).
"""
import asyncio
from pathlib import Path

from curl_cffi.requests import AsyncSession

IMG_DIR = Path(__file__).parent / "static" / "img"


def local_path(slug: str) -> Path:
    return IMG_DIR / f"{slug}.jpg"


async def _dl_one(session: AsyncSession, sem: asyncio.Semaphore, slug: str, url: str) -> bool:
    dest = local_path(slug)
    if dest.exists() and dest.stat().st_size > 0:
        return True
    async with sem:
        try:
            r = await session.get(url, headers={"Referer": "https://fragment.com/"}, timeout=30)
            if r.status_code == 200 and len(r.content) > 1000:
                IMG_DIR.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(r.content)
                return True
        except Exception:
            pass
    return False


async def ensure_thumbs(img_map: dict, concurrency: int = 6) -> dict:
    """img_map: {slug: remote_url}. Returns {slug: True/False downloaded-or-cached}."""
    sem = asyncio.Semaphore(concurrency)
    async with AsyncSession(impersonate="chrome") as session:
        jobs = [(s, u) for s, u in img_map.items() if u and not (local_path(s).exists() and local_path(s).stat().st_size > 0)]
        results = await asyncio.gather(*[_dl_one(session, sem, s, u) for s, u in jobs])
    ok = dict(zip([s for s, _ in jobs], results))
    for s in img_map:
        ok.setdefault(s, local_path(s).exists())
    return ok


def thumb_url(slug: str, fallback_remote: str | None = None) -> str:
    if local_path(slug).exists():
        return f"/static/img/{slug}.jpg"
    return fallback_remote or f"https://fragment.com/gifts/{slug}/thumb.webp"
