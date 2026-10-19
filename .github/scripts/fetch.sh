#!/usr/bin/env bash
# 多源下载助手：按顺序尝试候选 URL，第一个「HTTP 200 + 体积达标 + 内容校验通过」的被采用；
# 全部失败时保留仓库里的旧文件，不会把已有配置刷成空壳。
#
# 用法: fetch <输出文件> <最小字节数> <jq过滤表达式 | -> <URL> [URL...]
#
# 之所以不用 set -e 直接串 curl：GitHub 机房 IP 到 jsDelivr 常被限流，
# 返回的可能是 {"status":403,...} 这类 JSON，jq 会以 exit 5 失败，
# 所以必须逐源打印状态码并做内容校验，而不是只看 curl 的退出码。

fetch() {
  out="$1"; min="$2"; filt="$3"; shift 3
  tmp="$(mktemp)"
  for u in "$@"; do
    code=$(curl -fsSL --retry 2 --retry-delay 2 --max-time 120 \
                -w '%{http_code}' -o "$tmp" "$u" 2>/dev/null || true)
    size=$(wc -c < "$tmp" 2>/dev/null | tr -d ' ' || echo 0)
    [ -n "$size" ] || size=0
    echo "  [$code ${size}B] $u"
    if [ "$code" = "200" ] && [ "$size" -ge "$min" ]; then
      if [ "$filt" = "-" ] || jq -e "$filt" "$tmp" >/dev/null 2>&1; then
        mv "$tmp" "$out"
        echo "  -> 采用: $u"
        echo "- \`$out\` ← $u" >> "${GITHUB_STEP_SUMMARY:-/dev/null}"
        return 0
      fi
      echo "  -> 内容校验未通过，换下一个源"
    fi
  done
  rm -f "$tmp"
  echo "  !! 全部源失败，保留仓库旧版: $out"
  echo "- ⚠️ \`$out\` 全部源失败，保留仓库旧版" >> "${GITHUB_STEP_SUMMARY:-/dev/null}"
  return 1
}
