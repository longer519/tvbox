#!/usr/bin/env bash
# 多源下载助手：按顺序尝试候选 URL，第一个「HTTP 200 + 体积达标 + 内容校验通过」的被采用；
# 全部失败时保留仓库里的旧文件，不会把已有配置刷成空壳。
#
# 用法: fetch <输出文件> <最小字节数> <最少站点数|-> <URL> [URL...]
#   <最少站点数|->  数字 = 必须是可解析的 TVBox 配置且 sites 数 > N
#                   -    = 不做内容校验（直播源 txt / jar 二进制）
#
# 为什么不用 jq 做校验：TVBox 配置允许 // 和 # 注释行（liu673cn/box 的 m.json 就有 2 行），
# jq 只认严格 JSON，会对 200 OK 的正常配置报错（exit 5）→ 三个源全被误判为失败。
# 这里改用 python3，与 build.py 的 load() 完全同口径（去 BOM / 剔注释行 / 容忍尾逗号）。
#
# 每次尝试都写进 $GITHUB_STEP_SUMMARY：Actions 原始日志需要 admin 权限才能读，
# Summary 是唯一能匿名看到的诊断出口。

SUM="${GITHUB_STEP_SUMMARY:-/dev/null}"

_valid() {   # $1=文件  $2=最少站点数
  python3 - "$1" "$2" <<'PY'
import json, sys

p, min_sites = sys.argv[1], int(sys.argv[2])
try:
    t = open(p, encoding="utf-8-sig", errors="ignore").read()
except OSError:
    sys.exit(1)

t = "\n".join(l for l in t.splitlines() if not l.strip().startswith(("//", "#")))
for cand in (t, t.replace(",}", "}").replace(",]", "]")):
    try:
        d = json.loads(cand)
    except Exception:
        continue
    if isinstance(d, dict):
        sys.exit(0 if len(d.get("sites") or []) > min_sites else 1)
sys.exit(1)
PY
}

fetch() {
  out="$1"; min="$2"; minsites="$3"; shift 3
  tmp="$(mktemp)"
  for u in "$@"; do
    code=$(curl -fsSL --retry 2 --retry-delay 2 --max-time 120 \
                -w '%{http_code}' -o "$tmp" "$u" 2>/dev/null || true)
    size=$(wc -c < "$tmp" 2>/dev/null | tr -d ' ' || echo 0)
    [ -n "$size" ] || size=0

    if [ "$code" != "200" ] || [ "$size" -lt "$min" ]; then
      echo "- ✗ \`$out\` HTTP=${code:-000} ${size}B（要求 ≥${min}B）← $u" >> "$SUM"
      continue
    fi
    if [ "$minsites" != "-" ] && ! _valid "$tmp" "$minsites"; then
      echo "- ✗ \`$out\` HTTP=200 ${size}B 但内容校验未通过（sites ≤${minsites} 或非合法配置）← $u" >> "$SUM"
      continue
    fi

    mv "$tmp" "$out"
    echo "- ✓ \`$out\` HTTP=200 ${size}B ← $u" >> "$SUM"
    return 0
  done
  rm -f "$tmp"
  echo "- ⚠️ \`$out\` 全部源失败，保留仓库旧版" >> "$SUM"
  return 1
}
