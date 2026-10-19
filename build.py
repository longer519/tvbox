# -*- coding: utf-8 -*-
"""
合并上游 TVBox 配置 + 直播源，生成三份配置：
  config.json       完整版（含 spider jar）
  config-lite.json  精简版（免 jar，老盒子主力）
  config-live.json  纯直播版（0 影视站点，只要看电视时用）

用法：
    python build.py              # 只合并，不探测
    python build.py --probe      # 并发探测站点 API，剔除失活站点（Actions 用）
    python build.py --lite-max 20

仓库坐标来源优先级：环境变量 GITHUB_REPOSITORY  >  repo.conf  >  占位符
"""
import json, os, re, sys, hashlib, subprocess
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
BASE_UPSTREAM = os.path.join(HERE, "upstream_99188.json")
EXTRA_UPSTREAM = os.path.join(HERE, "upstream_m.json")
JAR_PATH = os.path.join(HERE, "jar", "pg.jar")

GH_PROXY = "https://gh-proxy.com/"
JSDELIVR = "https://cdn.jsdelivr.net/gh/{repo}@{ref}/{path}"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"


def repo_slug():
    r = os.environ.get("GITHUB_REPOSITORY")
    if r and "/" in r:
        return r
    p = os.path.join(HERE, "repo.conf")
    if os.path.exists(p):
        for ln in open(p, encoding="utf-8"):
            ln = ln.strip()
            if ln and not ln.startswith("#") and "/" in ln:
                return ln
    return "USER/REPO"


def load(path):
    t = open(path, encoding="utf-8", errors="ignore").read().lstrip("\ufeff")
    t = "\n".join(l for l in t.splitlines() if not l.strip().startswith(("//", "#")))
    for cand in (t, t.replace(",}", "}").replace(",]", "]")):
        try:
            return json.loads(cand)
        except Exception:
            pass
    raise SystemExit("无法解析: " + path)


def code(url, timeout=10):
    if not str(url).startswith("http"):
        return 0
    try:
        r = subprocess.run(["curl", "-s", "-o", os.devnull, "-m", str(timeout),
                            "-A", UA, "-w", "%{http_code}", url],
                           capture_output=True, timeout=timeout + 6)
        return int(r.stdout.decode().strip() or 0)
    except Exception:
        return 0


def md5sum(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def site_endpoint(s):
    """返回该站点可用于探活的地址；jar 型站点无法探测，返回 None"""
    t = str(s.get("type"))
    if t in ("0", "1", "4"):
        u = str(s.get("api") or "")
        return u if u.startswith("http") else None
    return None


def merge_sites(base, extra):
    seen, out = set(), []
    for s in base:
        k = str(s.get("key") or s.get("name"))
        if k in seen:
            continue
        seen.add(k)
        out.append(s)
    for s in extra:
        k = str(s.get("key") or s.get("name"))
        if k in seen:
            continue
        # 只补充不依赖 spider 的站点，避免引入第二个 jar
        if str(s.get("type")) not in ("0", "1", "4"):
            continue
        seen.add(k)
        out.append(s)
    return out


def trim(s):
    """去掉老 App 可能不认 / 拖慢解析的字段"""
    keep = ("key", "name", "type", "api", "searchable", "quickSearch",
            "filterable", "changeable", "indexs", "ext", "playerType", "jar", "style")
    o = {k: v for k, v in s.items() if k in keep}
    ext = o.get("ext")
    if isinstance(ext, str) and len(ext) > 4000:   # 超大 filter 会让老盒子卡死
        o["ext"] = ""
    return o


def main():
    probe = "--probe" in sys.argv
    lite_max = 20
    if "--lite-max" in sys.argv:
        lite_max = int(sys.argv[sys.argv.index("--lite-max") + 1])

    repo = repo_slug()
    base = load(BASE_UPSTREAM)
    extra = load(EXTRA_UPSTREAM) if os.path.exists(EXTRA_UPSTREAM) else {"sites": []}

    sites = [trim(s) for s in merge_sites(base.get("sites", []), extra.get("sites", []))]

    # ---- 探活（可选）----
    alive_map = {}
    if probe:
        targets = [(i, site_endpoint(s)) for i, s in enumerate(sites)]
        idxs = [i for i, u in targets if u]
        urls = [u for _, u in targets if u]
        with ThreadPoolExecutor(max_workers=16) as ex:
            codes = list(ex.map(lambda u: code(u, 9), urls))
        ok = (200, 201, 301, 302, 401, 403, 405, 500, 502)
        for i, c in zip(idxs, codes):
            alive_map[i] = c in ok
        print("探活: %d/%d 个可探测站点存活" % (sum(alive_map.values()), len(idxs)))
        cache = {}
        for i, s in enumerate(sites):
            u = site_endpoint(s)
            if u:
                cache[u] = alive_map.get(i, False)
        json.dump(cache, open(os.path.join(HERE, "probe_cache.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)

    def keep_site(i, s):
        if not probe:
            return True
        if site_endpoint(s) is None:      # jar 型站点无法探测，保留
            return True
        return alive_map.get(i, False)

    full_sites = [s for i, s in enumerate(sites) if keep_site(i, s)]
    # jar 型站点排后面，避免首屏等待 spider 下载
    full_sites.sort(key=lambda s: 0 if str(s.get("type")) in ("0", "1", "4") else 1)

    lite_sites = [s for i, s in enumerate(sites)
                  if str(s.get("type")) in ("0", "1", "4") and keep_site(i, s)][:lite_max]

    # ---- spider：绝对 URL + 真实 md5 ----
    spider = ""
    if os.path.exists(JAR_PATH):
        sp_md5 = md5sum(JAR_PATH)
        raw = "https://raw.githubusercontent.com/%s/main/jar/pg.jar" % repo
        spider = "%s%s;md5;%s" % (GH_PROXY, raw, sp_md5)
        print("spider md5 =", sp_md5)
    else:
        print("警告: 未找到 jar/pg.jar，spider 将留空（精简版不受影响）")

    # ---- lives：按实测存活率排序（2026-10-19 实测）----
    # live.txt 8/8；ccsh_lite.txt 3/8（含运营商内网源）；bbxx365 4/8 但体量大，只进完整版
    def J(path):
        return JSDELIVR.format(repo=repo, ref="main", path=path)

    lite_lives = [
        {"name": "① 直播·稳定（live.txt 自托管）", "type": 0, "url": J("live/live.txt"), "epg": "", "logo": ""},
        {"name": "② 直播·扩充(1709)", "type": 0, "url": J("live/ccsh_lite.txt"), "epg": "", "logo": ""},
        {"name": "③ 备用·上游直链", "type": 0,
         "url": "https://cdn.jsdelivr.net/gh/Supprise0901/TVBox_live@main/live.txt", "epg": "", "logo": ""},
    ]
    full_lives = lite_lives + [
        {"name": "④ iptv365(2万频道)", "type": 0, "url": J("live/bbxx365.txt"), "epg": "", "logo": ""},
        {"name": "⑤ 备用·CCSH全量", "type": 0,
         "url": "https://cdn.jsdelivr.net/gh/CCSH/IPTV@HEAD/live.txt", "epg": "", "logo": ""},
    ]

    def build(ss, with_spider, lv):
        cfg = {
            "spider": spider if with_spider else "",
            "wallpaper": "https://cdn.jsdelivr.net/gh/qist/tvbox@master/favicon.ico",
            "sites": ss,
            "parses": (extra.get("parses") or base.get("parses") or []),
            "lives": lv,
        }
        return cfg

    # ---- 纯直播版：0 影视站点，只保留 ① live.txt 这一组（2026-10-19 用户要求）----
    # live.txt 是自托管副本，来源 Supprise0901/TVBox_live，约 320 个中文频道（央视/卫视/地方台），
    # 实测抽样 7-8/8 可连，是三组里最稳的；其余两组（ccsh_lite / 上游直链）不再进纯直播版。
    live_lives = [lite_lives[0]]
    live_only = build([], False, live_lives)
    live_only["parses"] = []      # 纯直播不需要解析接口，减小体积

    full = build(full_sites, True, full_lives)
    lite = build(lite_sites, False, lite_lives)

    for name, cfg in (("config.json", full), ("config-lite.json", lite),
                      ("config-live.json", live_only)):
        with open(os.path.join(HERE, name), "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=1)
        print("写出 %s: %d 站点 / %d 直播源" % (name, len(cfg["sites"]), len(cfg["lives"])))


if __name__ == "__main__":
    main()
