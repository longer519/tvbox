# 自用 TVBox 配置仓库（Android 4.4 老盒子专用）

影视点播 + 电视直播，GitHub 自建托管，国内走 jsDelivr / gh-proxy 访问。
每 6 小时自动同步上游影视配置与直播源。

---

## 一、装哪个 APK

| 盒子系统 | ABI | 装哪个 |
|---|---|---|
| **Android 4.4（本方案目标）** | armeabi-v7a（32 位） | **`java32.apk`** |
| Android 5.0+（64 位固件） | arm64-v8a | `java64.apk` |
| Android 5.0+（32 位固件） | armeabi-v7a | `java32.apk` |
| 需要 python 类源（网盘/学习） | 64 位 | `python64.apk` |

- `java64/python64` 的 minSdk 是 21（Android 5.0），**4.4 盒子装不上**（报 INSTALL_FAILED_OLDER_SDK）。
- 影视仓 v6.x 需 Android 6.0+，4.4 也装不了。
- 装法：APK 拷 U 盘 → 盒子文件管理器安装；或用 ADB：`adb connect <盒子IP>:5555 && adb install java32.apk`

---

## 二、配置地址（填进「设置 → 配置地址」）

仓库坐标已固定为 `longer519/tvbox`，直接复制下面的地址即可。

| 用途 | 地址 |
|---|---|
| **主力（老盒子首选）** | `https://cdn.jsdelivr.net/gh/longer519/tvbox@main/config-lite.json` |
| **纯看电视（0 影视站点）** | `https://cdn.jsdelivr.net/gh/longer519/tvbox@main/config-live.json` |
| 完整版（含 spider 站点） | `https://cdn.jsdelivr.net/gh/longer519/tvbox@main/config.json` |
| 备用通道（TLS1.2） | `https://gh-proxy.com/https://raw.githubusercontent.com/longer519/tvbox/main/config.json` |
| 回滚（换历史 tag） | 把地址里的 `@main` 改成 `@v20261019-1320` 这类历史 tag |

三档怎么选：

- **`config-lite.json`** —— 影视 + 直播都要，20 个免 jar 站点，最通用
- **`config-live.json`** —— 只看电视，0 个影视站点，**只含 1 组直播源**（`live/live.txt`，约 320 个中文频道：央视 / 卫视 / 地方台），界面最干净
- **`config.json`** —— 站点最多（含 spider 型），性能好的设备用

> 少数 TVBox 版本在 `sites` 为空时首页会显示「暂无数据」或空白，**直播页仍可正常用**。
> 若首页异常，换回 `config-lite.json` 即可。`config-live.json` 里的 ① 与 ③ 本质是同一上游源
> （自托管副本 + 上游直链），只是互为冗余，不是两套不同内容。

**为什么主力走 jsDelivr**：实测 jsDelivr 在 TLS 1.0/1.1 下仍可握手，而 raw.githubusercontent.com 强制 TLS 1.2 —— Android 4.4 有 TLS1.2 但默认不启用，老盒子直连 raw 极易握手失败。jsDelivr 同时在国内有节点。

**为什么 spider 走 gh-proxy**：jsDelivr 会屏蔽 `.jar`（返回 403），所以 `config.json` 里的 spider 字段写的是指向 gh-proxy 的**绝对 URL**，不走 jsDelivr。`config-lite.json` 不依赖 jar，最稳。

### 如果盒子里的内容比网站上旧（jsDelivr 分支缓存）

`@main` 是**分支引用**，jsDelivr 各边缘节点独立失效，刚同步完的头几分钟到几小时里，个别节点仍可能吐上一版内容（最长 12 小时会自愈）。三种处理办法：

| 办法 | 地址 | 特点 |
|---|---|---|
| **① 等** | 不变 | 下一两次打开配置时大概率已刷新；workflow 每次同步都会 purge + 校验，会加速自愈 |
| **② 换最新 tag** | `https://cdn.jsdelivr.net/gh/longer519/tvbox@v20261019-1320/config-lite.json` | tag 指向不可变提交，**内容永远新鲜**；代价是每次同步 tag 会变，需要改地址 |
| **③ 换 gh-proxy 直连 raw** | `https://gh-proxy.com/https://raw.githubusercontent.com/longer519/tvbox/main/config-lite.json` | 永远新鲜、无缓存；代价是依赖第三方代理，且要求设备支持 TLS 1.2 |

日常保持 `@main` 不动即可 —— 只有急着看新内容时才临时换成 ② 或 ③，下次同步后再换回来。

> 2026-10-19 20:20 那次同步后实测：`@main` 有约 20 分钟陈旧期，purge 后两个配置文件已恢复一致，直播源文件随后自愈。

### 直播源单独使用（不装 TVBox / 给别的播放器）

`config-live.json` 里那唯一一组直播源，就是仓库里的 **`live/live.txt`**（自托管副本，上游 `Supprise0901/TVBox_live`，约 320 个中文频道，格式为 `频道名,http地址`，每 6 小时随同步自动更新）：

| 通道 | 地址 | 特点 |
|---|---|---|
| **jsDelivr（推荐）** | `https://cdn.jsdelivr.net/gh/longer519/tvbox@main/live/live.txt` | 国内有节点，TLS1.0 也能握手；可能有几分钟缓存延迟 |
| raw 原站 | `https://raw.githubusercontent.com/longer519/tvbox/main/live/live.txt` | 永远新鲜；要求 TLS 1.2 |
| gh-proxy 代理 raw | `https://gh-proxy.com/https://raw.githubusercontent.com/longer519/tvbox/main/live/live.txt` | 永远新鲜；依赖第三方代理 |
| 上游原版 | `https://cdn.jsdelivr.net/gh/Supprise0901/TVBox_live@main/live/live.txt` | 不经过本仓库，同步时差与本仓库一致 |

VLC / PotPlayer / 完美解码都能直接打开这个 txt。注意 `#genre#` 是分组标记行，部分播放器需要选「播放列表 / M3U 式导入」才能识别。

> 该源由上游 `Supprise0901/TVBox_live` 维护，是 TVBox 生态里最活跃的中文直播 txt 之一；2026-10-19 实测抽样 8 个频道 7–8 个可连。失效是常态，仓库每 6 小时会自动拉最新版替换，所以**不要**把这个 txt 下载到本地长期用，直接用上面的链接才会持续拿到更新。

---

## 三、文件内容

| 文件 | 说明 |
|---|---|
| `config.json` | 完整版：约 56 站点（含 spider 型）+ 5 组直播 |
| `config-lite.json` | 精简版：**20 个免 jar 站点 + 3 组直播**，老盒子主力 |
| `config-live.json` | 纯直播版：**0 影视站点 + 2 组直播**，491 字节 |
| `live/live.txt` | 直播主源，319 频道（实测 7/8 可连） |
| `live/ccsh_lite.txt` | 直播扩充，1709 频道（部分为运营商内网源，跨网不可用） |
| `live/bbxx365.txt` | iptv365 全量，2 万频道（体量大，仅完整版引用） |
| `jar/pg.jar` | 自托管 spider，11.7 MB，md5 已写入配置 |
| `build.py` | 合并/探活/生成三份配置 |
| `verify.py` | 验证 JSON、spider md5、直播源抽样 |
| `probe_cache.json` | 上次站点探活结果 |

---

## 四、自动化

`.github/workflows/sync.yml`：每 6 小时（UTC 0/6/12/18 点，即北京 8/14/20/2 点）
1. 拉取 `qist/tvbox@master/99188.json` 与 `liu673cn/box@main/m.json`
2. 拉取三个直播源，中文频道数校验失败则回滚上一版
3. `python3 build.py --probe --lite-max 20`：探活并剔除失效站点
4. 提交 + 打 tag `vYYYYMMDD-HHMM`（用于回滚）
5. `POST https://purge.jsdelivr.net/...` 刷新 jsDelivr 缓存，**并用 raw 与 CDN 的 md5 比对校验**，不一致则 30 秒后重试（最多 5 轮），仍不一致只告警并给出 tag 兜底地址

**每个上游文件都按 raw → gh-proxy → jsDelivr 的顺序回退**（`.github/scripts/fetch.sh`），
逐个打印 HTTP 码与体积，全部失败时保留仓库旧版，不会提交空壳。
2026-10-19 首跑失败就是 jsDelivr 对 GitHub 机房 IP 返回错误 JSON 导致的，已如此修正。

上游摘除或返回空壳时不会提交坏版本 —— 校验失败即保留上一版。

---

## 五、自建步骤（从零复现）

```bash
# 1. GitHub 网页新建「公开」仓库（jsDelivr 要求公开），记下 用户名/仓库名
# 2. 写入仓库坐标
echo "longer519/tvbox" > repo.conf

# 3. 拉取上游 + 生成配置
python build.py --probe --lite-max 20

# 4. 本地验证
python verify.py

# 5. 推送
git init && git add -A
git commit -m "init tvbox config"
git branch -M main
git remote add origin https://github.com/longer519/tvbox.git
git push -u origin main
git tag v$(date -u +%Y%m%d-%H%M) && git push --tags

# 6. 等 1-2 分钟让 jsDelivr 首次缓存，然后远程验证
python verify.py --remote
```

---

## 六、已知风险与兜底

1. **spider 第三方托管**：gh-proxy / ghfast 随时可能失效 → 兜底用 `config-lite.json`（不依赖 jar）
2. **直播源**：小时级失效；本仓库多源冗余 + 6 小时同步；ccsh 源含运营商内网地址，跨网可能播不了，主用 `live.txt`
3. **上游删库**：Actions 有校验，坏版本不入库；出问题切历史 tag
4. **TLS**：若 jsDelivr 日后禁用 TLS1.0，4.4 盒子需改用备用通道或本地导入
5. **本地导入兜底**：TVBox 自带局域网服务 `http://<盒子IP>:9978`，手机/电脑浏览器打开上传 json 即可，完全绕过 https
