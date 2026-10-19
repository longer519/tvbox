# 把本地仓库推到 GitHub（Windows 三种方式）

> 目标仓库：https://github.com/longer519/tvbox （Public、空仓库、默认分支 main）
> 本地仓库：`D:\WorkBuddy\2026-10-18-15-03-34\tvbox-config`（已 commit 3 次、15 个文件、14MB）

---

## 为什么 CMD 里那几条命令会失败

### 1. 路径写法不是 CMD 的写法

```
cd /d/WorkBuddy/2026-10-18-15-03-34/tvbox-config     ← 错
```

`/d/...` 是 Git Bash（Linux 风格）的路径。CMD 里 `/d` 是 `cd` 的**切换盘符开关**，
CMD 把 `/WorkBuddy/...` 当成一个名字叫 `/WorkBuddy/...` 的目录去找，找不到 → 「命令语法不正确」。

CMD 正确写法（二选一）：

```cmd
cd /d "D:\WorkBuddy\2026-10-18-15-03-34\tvbox-config"
```

```cmd
D:
cd \WorkBuddy\2026-10-18-15-03-34\tvbox-config
```

### 2. 这台机器根本没装 Git

截图里的 `'git' 不是内部或外部命令` 就是这个原因。

验证一下：

```cmd
where git
```

没有输出 = 没装。WorkBuddy 里能跑 git，用的是它自带的便携版：

```
D:\Program Files\WorkBuddy\resources\vendor\PortableGit\cmd\git.exe
```

这个目录不在系统 PATH 里，所以 CMD 看不见。

---

## 方式 A：CMD + WorkBuddy 自带 Git（零安装，推荐先试）

**逐行**粘贴执行，不要合并成一行。第一行的 `set` 只对当前这个 CMD 窗口有效，关掉就失效。

```cmd
set "PATH=D:\Program Files\WorkBuddy\resources\vendor\PortableGit\cmd;%PATH%"
```

```cmd
cd /d "D:\WorkBuddy\2026-10-18-15-03-34\tvbox-config"
```

```cmd
git --version
```

看到 `git version 2.55.0.windows.3` 说明挂载成功，继续：

```cmd
git remote add origin https://github.com/longer519/tvbox.git
```

```cmd
git push -u origin main
```

**第一次 push 会弹窗**：「Git Credential Manager」窗口 → 选 **Sign in with your browser** →
浏览器里登录 GitHub → 点 Authorize。这一步必须开着梯子。

成功后再打标签：

```cmd
git tag v20261019-0900
```

```cmd
git push --tags
```

### 如果弹不出登录窗口、报 `could not read Username`

改用 PAT（个人访问令牌）直接写进地址：

1. 浏览器开 https://github.com/settings/tokens?type=beta
2. **Generate new token** → 名字随意 → Expiration 选 90 days
3. Repository access → **Only select repositories** → 选 `tvbox`
4. Permissions → Repository permissions → **Contents: Read and write**
5. Generate → 复制 `github_pat_xxxxx`（只显示一次）

```cmd
git remote set-url origin https://github_pat_你的令牌@github.com/longer519/tvbox.git
```

```cmd
git push -u origin main
```

---

## 方式 B：浏览器上传（完全不用命令行）

适合不想碰 CMD。15 个文件一次拖完。

1. 浏览器打开 https://github.com/longer519/tvbox/upload/main
2. 另开一个资源管理器窗口，进 `D:\WorkBuddy\2026-10-18-15-03-34\tvbox-config`
3. 菜单 **查看 → 显示 → 勾选「隐藏的项目」**（否则看不到 `.github` 文件夹）
4. **只拖这些**（千万别拖 `.git` 文件夹）：

   ```
   .github\           ← 整个文件夹（里面是 workflows\sync.yml）
   jar\               ← 整个文件夹（pg.jar 12MB，未超 25MB 单文件上限）
   live\              ← 整个文件夹（3 个 txt）
   README.md
   build.py
   verify.py
   config.json
   config-lite.json
   repo.conf
   probe_cache.json
   upstream_99188.json
   upstream_m.json
   GITHUB新建仓库-中英对照.md
   ```

5. 页面底部 Commit changes，说明填 `init`，点 **Commit changes**

> 如果 `.github` 文件夹拖不上去（部分浏览器不认隐藏目录），手动补一个：
> **Add file → Create new file** → 文件名框输入 `.github/workflows/sync.yml`（输 `/` 会自动建目录）
> → 把本地 `sync.yml` 内容粘进去 → Commit。

---

## 方式 C：装 Git for Windows 或 GitHub Desktop（一次装好长期可用）

- 装 Git for Windows：https://git-scm.com/download/win —— 一路默认，
  安装选项里保持 **Git from the command line and also from 3rd-party software**。
  装完**重开** CMD，`git --version` 就有输出了，之后方式 A 的后半段直接可用。
- 或装 GitHub Desktop：https://desktop.github.com —— 全图形化，
  **File → Add local repository** 选 `vbox-config` 文件夹 → 右上 **Publish repository** →
  **取消勾选 Keep this code private** → Publish。

---

## 推完之后

1. 仓库页 **Settings → Actions → General → Workflow permissions**
   → 选 **Read and write permissions** → **Save**
   （不设这步，每 6 小时的自动同步会卡在提交那一步）

2. 告诉我一声，我跑远端验证：
   - `https://cdn.jsdelivr.net/gh/longer519/tvbox@main/config-lite.json`
   - `https://cdn.jsdelivr.net/gh/longer519/tvbox@main/config.json`
   - spider jar：`https://gh-proxy.com/https://raw.githubusercontent.com/longer519/tvbox/main/jar/pg.jar`
     （md5 应为 `7c8f662c4d1ed4351e02691c15ed24a2`）

3. 盒子配置地址填：

   ```
   https://cdn.jsdelivr.net/gh/longer519/tvbox@main/config-lite.json
   ```

## 小抄：CMD 和 Git Bash 的差别

| 用途 | CMD | Git Bash |
|---|---|---|
| 切盘符 | `D:` | `cd /d` |
| 进目录 | `cd /d "D:\a\b"` 或 `cd \a\b` | `cd /d/a/b` |
| 反斜杠 | 必须 `\` | `/` 或 `\` 都行 |
| 串命令 | `&&` 可用 | `&&` 可用 |
| 变量 | `%PATH%` | `$PATH` / `${PATH}` |
| 找命令在哪 | `where git` | `which git` |

PowerShell 额外注意：Windows PowerShell 5.1 **不支持 `&&`**，要用 `;` 或分行。
