# GitHub 网页新建「公开」仓库 — 详细步骤（中英对照）

必须选 **Public**：jsDelivr 只服务公开仓库，私有仓库无法加速。

## 快捷方式

已登录状态下浏览器直接打开：

```
https://github.com/new?name=tvbox-config&visibility=public
```

会预填仓库名与可见性，直接跳到第 3 步。

---

## 详细步骤

| # | 中文界面 | English UI | 怎么操作 |
|---|---|---|---|
| 1 | 右上角 `+` → **New repository** | In the upper-right corner, select **+**, then click **New repository** | 或直接访问 `github.com/new` |
| 2 | （可选）**Choose a template** 模板 | (Optional) Choose a template | 不选，留空 |
| 3 | **Owner** 所有者 | Use the **Owner** dropdown menu to select the account | 选你的个人账号，不要选组织 |
| 4 | **Repository name** 仓库名 | Type a name for your repository | 填 `tvbox-config`；≤100 字符，只能用 ASCII 字母、数字、`.`、`-`、`_` |
| 5 | **Description** 描述（可选） | Type an optional description | 可留空 |
| 6 | **● Public** 公开 | Choose a repository visibility → **Public** | **务必选这个**，否则 jsDelivr 用不了 |
| 7 | **不要勾选** Add a README file / Add .gitignore / Choose a license | If you're importing an existing repository, **don't choose any of these options**, as you may introduce a merge conflict | 本地已有文件，勾了会冲突 |
| 8 | （可选）GitHub Apps / Copilot prompt | (Optional) Apps / Copilot | 跳过 |
| 9 | 点 **Create repository** | Click **Create repository** | 完成 |

创建后出现的 Quick Setup 页面里，找 **"…or push an existing repository from the command line"** 这段，就是本地推送用的命令。

---

## 建库后必做：开启 Actions 写权限

否则 `sync.yml` 无法自动提交（新建仓库的 GITHUB_TOKEN 默认只读）。

| # | 中文路径 | English path |
|---|---|---|
| 1 | 仓库页 → **Settings**（设置） | Under your repository name, click **Settings** |
| 2 | 左侧栏 → **Actions** → **General** | In the left sidebar, click **Actions**, then **General** |
| 3 | 找 **Workflow permissions** → 选 **Read and write permissions** | Under **Workflow permissions**, choose **Read and write permissions** |
| 4 | 点 **Save**（保存） | Click **Save** |

可选：同页 **Actions permissions** → **Allow all actions and reusable workflows**（允许所有 action）。

---

## 推送命令

```bash
cd D:/WorkBuddy/2026-10-18-15-03-34/tvbox-config
git init
git add -A
git commit -m "init tvbox config"
git branch -M main
git remote add origin https://github.com/longer519/tvbox.git
git push -u origin main
git tag v20261019-0800 && git push --tags
```

> Windows Git Bash 若 `date` 命令不可用，tag 名手写成 `v20261019-0800` 形式即可。

---

## 最终盒子里的地址

```
https://cdn.jsdelivr.net/gh/longer519/tvbox@main/config-lite.json
```
