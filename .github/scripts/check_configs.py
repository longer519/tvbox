#!/usr/bin/env python3
"""生成配置后的本地校验：结构合法 + 数量下限 + 写入 Step Summary。

为什么不用 jq（2026-10-20 教训）：
1. TVBox 配置允许 // 注释行，jq 只认严格 JSON —— fetch.sh 已在这个问题上栽过。
2. jq -e 的退出码规则容易踩坑：`jq -e 'expr' > /dev/null` 在 expr 为 false 时返回 1。
   昨天把 config-live.json 的直播源从 2 组改成 1 组，而校验还写着 `lives > 1`，
   于是 `1 > 1` 为 false → 整步被判失败（run #5）。校验条件必须跟着配置结构走。

用法: python3 .github/scripts/check_configs.py
退出码: 0 全部通过 / 1 有文件不合格或无法解析
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# (文件名, 取哪个字段计数, 下限)
CHECKS = [
    ("config.json", "sites", 1),
    ("config-lite.json", "sites", 1),
    ("config-live.json", "lives", 1),   # 纯直播版只看直播组；站点为 0 是设计如此
]


def load(path):
    """与 fetch.sh / build.py 同口径：去 BOM、剔注释行、容忍尾逗号。"""
    with open(path, encoding="utf-8-sig", errors="ignore") as f:
        t = f.read()
    t = "\n".join(l for l in t.splitlines() if not l.strip().startswith(("//", "#")))
    for cand in (t, t.replace(",}", "}").replace(",]", "]")):
        try:
            return json.loads(cand)
        except Exception:
            pass
    return None


def main():
    ok = True
    rows = []
    for name, field, minimum in CHECKS:
        path = os.path.join(ROOT, name)
        d = load(path) if os.path.exists(path) else None
        if d is None:
            print("::error::%s 无法解析或不存在" % name)
            ok = False
            continue
        sites = len(d.get("sites") or [])
        lives = len(d.get("lives") or [])
        count = sites if field == "sites" else lives
        good = count >= minimum
        ok = ok and good
        print("[%s] %-18s 站点 %-4d 直播组 %-3d （要求 %s ≥ %d）"
              % ("OK" if good else "FAIL", name, sites, lives, field, minimum))
        rows.append((name, sites, lives))

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("### 生成结果\n\n| 文件 | 站点 | 直播组 |\n|---|---|---|\n")
            for n, s, l in rows:
                f.write("| %s | %d | %d |\n" % (n, s, l))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
