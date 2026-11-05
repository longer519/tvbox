#!/usr/bin/env python3
"""Generate LibreTV SourceList subscriptions from the self-hosted TVBox config.

Run after build.py / sync.yml to refresh the LibreTV subscription files:
    python libretv/make_sources.py
"""
import io
import json
import os
import re
from urllib.parse import urlsplit, urlunsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "libretv")

CDN = "https://cdn.jsdelivr.net/gh/longer519/tvbox@main"
LIVE_M3U = CDN + "/live/live.m3u"

# Sources verified working as Apple CMS JSON API (2026-11-05).
RECOMMENDED = [
    "https://cj.lziapi.com/api.php/provide/vod",
    "https://ffzy.tv/api.php/provide/vod",
    "https://api.apibdzy.com/api.php/provide/vod",
    "https://hhzyapi.com/api.php/provide/vod",
]

ADULT_HINTS = (
    "成人", "麻豆", "色", "黄", "辣", "老色逼", "精品下", "魔法",
    "越南", "91", "玉兔", "av", "sapi", "xml.php", "apijson",
)
ADULT_HOSTS = (
    "lbapi9.com", "fhapi9.com", "madouse.la", "jingpinx.com",
    "semaozy.net", "apilj.com", "91md.me", "vnzyz.com",
    "apilsbzy1.com", "wmcj8.com", "pgxdy.com", "dadiapi.com",
)
NAME_MAP = {
    "cj.lziapi.com": "量子资源",
    "ffzy.tv": "非凡资源",
    "cj.ffzyapi.com": "非凡备用",
    "api.apibdzy.com": "百度采集",
    "hhzyapi.com": "火狐采集",
    "www.huyaapi.com": "虎牙采集",
    "155api.com": "155资源",
    "jkunzyapi.com": "jkun资源",
    "slapibf.com": "森林资源",
    "api.ddapi.cc": "滴滴资源",
    "lzizy1.com": "量子备用",
    "suoniapi.com": "索尼资源",
}


def normalize(url: str) -> str:
    """Strip trailing slash + query so LibreTV can append its own CMS params."""
    p = urlsplit(url.strip())
    path = p.path.rstrip("/")
    return urlunsplit((p.scheme, p.netloc, path, "", ""))


def label(name: str) -> str:
    return re.sub(r"[\s]+", " ", name).strip()


def clean_sites(cfg: dict) -> list:
    out, seen = [], set()
    for s in cfg.get("sites", []):
        if s.get("type") not in (1, "1"):
            continue
        api = s.get("api", "")
        if not isinstance(api, str) or not api.startswith(("http://", "https://")):
            continue
        if "api.php/provide/vod" not in api and "apijson_vod.php" not in api:
            continue
        name = label(s.get("name", ""))
        if any(h.lower() in (name + api).lower() for h in ADULT_HINTS):
            continue
        u = normalize(api)
        host = urlsplit(u).netloc
        if any(h in host for h in ADULT_HOSTS) or u.startswith("http://"):
            continue
        if u in seen:
            continue
        seen.add(u)
        out.append({"name": NAME_MAP.get(host, name or host), "url": u})
    return out


def write(name: str, obj: dict) -> None:
    p = os.path.join(OUT, name)
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("wrote", p)


def main() -> None:
    with io.open(os.path.join(ROOT, "config-lite.json"), encoding="utf-8") as f:
        cfg = json.load(f)

    all_sites = clean_sites(cfg)
    by_url = {s["url"]: s for s in all_sites}
    for u in RECOMMENDED:
        host = urlsplit(u).netloc
        by_url.setdefault(u, {"name": NAME_MAP.get(host, host), "url": u})
    picked = [by_url[u] for u in RECOMMENDED]
    live = [{"name": "自建直播 live.m3u（稳定·自托管）", "url": LIVE_M3U}]

    write("sources.json", {
        "name": "longer519 稳定源 · 推荐（影视+直播）",
        "version": 2,
        "sources": picked,
        "liveSources": live,
    })
    write("sources-full.json", {
        "name": "longer519 稳定源 · 全量可选",
        "version": 2,
        "sources": list(by_url.values()),
        "liveSources": live,
    })
    write("sources-live.json", {
        "name": "longer519 稳定源 · 纯直播",
        "version": 2,
        "liveSources": live,
    })
    print("recommended=%d full=%d" % (len(picked), len(by_url)))


if __name__ == "__main__":
    main()
