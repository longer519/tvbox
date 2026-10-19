# -*- coding: utf-8 -*-
"""
验证 TVBox 配置：本地 JSON 合法性 → spider md5 → 直播源抽样 → 远端链接可达性。

用法：
    python verify.py            # 只验证本地文件与直播源
    python verify.py --remote   # 额外验证 jsDelivr / gh-proxy 上的远端链接（需先推送到 GitHub）
"""
import json, os, re, sys, subprocess, random
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
GH_PROXY = "https://gh-proxy.com/"


def sh(args, timeout=30):
    try:
        r = subprocess.run(args, capture_output=True, timeout=timeout + 10)
        return r.stdout
    except Exception:
        return b""


def code(url, timeout=12):
    if not str(url).startswith("http"):
        return 0
    b = sh(["curl", "-s", "-o", os.devnull, "-m", str(timeout), "-A", UA, "-w", "%{http_code}", url], timeout)
    try:
        return int(b.decode().strip() or 0)
    except Exception:
        return 0


def md5_url(url, timeout=180):
    import hashlib
    tmp = os.path.join(HERE, ".spider.tmp")
    c = sh(["curl", "-s", "-L", "-m", str(timeout), "-A", UA, "-o", tmp, url], timeout)
    if not os.path.exists(tmp) or os.path.getsize(tmp) == 0:
        return None, 0
    h = hashlib.md5()
    with open(tmp, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    size = os.path.getsize(tmp)
    os.remove(tmp)
    return h.hexdigest(), size


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


def parse_live(path):
    """从 m3u / txt 抽出 (频道名, url)"""
    out = []
    txt = open(path, encoding="utf-8", errors="ignore").read()
    if "#EXTM3U" in txt:
        name = ""
        for ln in txt.splitlines():
            ln = ln.strip()
            if ln.startswith("#EXTINF"):
                m = re.search(r",\s*(.+)$", ln)
                name = m.group(1) if m else ""
            elif ln.startswith("http"):
                out.append((name, ln))
    else:
        for ln in txt.splitlines():
            ln = ln.strip()
            if "," in ln and ln.count(",") >= 1:
                n, u = ln.split(",", 1)
                if u.startswith("http") and "#genre#" not in u:
                    out.append((n, u))
    return out


def check_live(path, n=8):
    items = parse_live(path)
    if not items:
        return "无法解析"
    sample = random.sample(items, min(n, len(items)))
    with ThreadPoolExecutor(max_workers=8) as ex:
        codes = list(ex.map(lambda x: code(x[1], 8), sample))
    ok = sum(1 for c in codes if c in (200, 206, 301, 302))
    return "%d/%d 可连（共 %d 频道）" % (ok, len(sample), len(items))


def main():
    remote = "--remote" in sys.argv
    repo = repo_slug()
    print("仓库: %s\n" % repo)

    ok_all = True
    spider_done = False
    for f in ("config.json", "config-lite.json", "config-live.json"):
        p = os.path.join(HERE, f)
        if not os.path.exists(p):
            print("[缺失]", f)
            ok_all = False
            continue
        try:
            cfg = json.load(open(p, encoding="utf-8"))
            print("[OK] %s  JSON 合法 | 站点 %d | 直播组 %d"
                  % (f, len(cfg.get("sites") or []), len(cfg.get("lives") or [])))
        except Exception as e:
            print("[FAIL] %s  JSON 解析失败: %s" % (f, e))
            ok_all = False
            continue

        # 三份配置共用同一个 spider，验一次即可，但不能因此跳过其余配置的 JSON 校验
        sp = (cfg.get("spider") or "").split(";")
        if (not spider_done) and len(sp) >= 3 and sp[0].startswith("http"):
            spider_done = True
            url, md5_cfg = sp[0], sp[2].strip().lower()
            if "USER/REPO" in url:
                print("      spider: 跳过（repo.conf 还是占位符 USER/REPO，填真实仓库后再验）")
            else:
                c = code(url, 40)
                print("      spider: HTTP %s  %s" % (c, url))
                if c == 200:
                    got, size = md5_url(url)
                    match = (got == md5_cfg)
                    print("      spider md5: %s | 配置声明 %s | %s（%.1f MB）"
                          % (got, md5_cfg, "一致" if match else "不一致", size / 1048576))
                    ok_all &= match
                else:
                    ok_all = False

    print()
    for f in ("live/live.txt", "live/ccsh_lite.txt", "live/bbxx365.txt"):
        p = os.path.join(HERE, f)
        if os.path.exists(p):
            print("[直播] %-22s %s" % (f, check_live(p)))
        else:
            print("[缺失] %s" % f)

    if remote:
        print()
        base = "https://cdn.jsdelivr.net/gh/%s@main" % repo
        for f in ("config.json", "config-lite.json", "config-live.json",
                  "live/live.txt", "live/ccsh_lite.txt"):
            u = "%s/%s" % (base, f)
            c = code(u)
            print("[远端] HTTP %-4s %s" % (c, u))
            ok_all &= (c == 200)
        u = "%shttps://raw.githubusercontent.com/%s/main/config.json" % (GH_PROXY, repo)
        print("[备用] HTTP %-4s %s" % (code(u), u))

    print("\n结论:", "全部通过" if ok_all else "存在问题，见上方 FAIL/不一致")


if __name__ == "__main__":
    main()
