# 速度无限站点运维交接（OPS）

最后更新：2026-11-24。每次开新会话（包括每天自动跑的巡检）先读本文件和 `CLAUDE.md`。和用户沟通一律用中文。**不得打印、回显或提交任何凭据。**

## 1. 站点与环境

- 网站：`https://main.suduwuxian.top`（WordPress，Hello Elementor 主题 + Elementor / Elementor Pro，SEO 用 Rank Math）。仓库：`suduwuxiantop/vpn-guide`（GitHub 放摘要版，完整版在网站）。
- 凭据在环境变量 `WP_URL` / `WP_USER` / `WP_APP_PASSWORD`（应用程序密码，HTTP Basic）。注意：用户另有别的网站用 `WP2_*`，**那些和本站无关，不要读写**。
- 服务器：宝塔面板，Nginx，PHP 8.1，**2 核 / 3.8GB**。PHP-FPM `max_children=12`（原来是 50，2026-10-25 曾被并发请求拖到全站 PHP 卡死，改小后恢复），OPcache 已装。**对服务器要克制：请求串行、有间隔、遇慢就停。**
- 前面有 Cloudflare：HTML 页面有一条缓存规则（边缘 TTL 2 小时，已排除 wp-admin、wp-json、登录 Cookie、带查询参数和 `/go/`）；静态文件另有一条。改完文章后缓存最多 2 小时才更新（`?nc=随机数` 可绕过缓存查看）。
- LiteSpeed Cache 插件还在，但服务器是 Nginx，它的页面缓存不起作用（只用它的 CSS/JS 优化）。WP Super Cache 装过后已停用并删除，不要再装。
- 站点时区 UTC+8。REST 的 `modified_after` 按站点本地时间比较。

## 2. 已完成的主要改动（便于理解现状，不要重复做）

- 9 篇新文章已发布（微软商店装 ChatGPT、Windows 装 Claude 桌面版、Mac 装 ChatGPT/Claude、安卓装 ChatGPT、Gemini 地区不可用、v2rayN 订阅教程，以及 ChatGPT / Claude / Cursor 三篇访问指南），均有配图、SEO 描述、FAQ、官方参考资料；GitHub 上是摘要版。
- 29 篇老文章的中文编码网址改为英文短网址，旧网址 301 跳转；站内正文、GitHub 摘要里的链接已同步。
- 全站元数据：重写过短或过长的 meta description；37 个页面补了默认分享图（媒体 ID 857）；独立页面的结构化数据由 Article 改为 WebPage；7 个页面的重复 H1 已去掉；文章日期不再链接到会 301 到首页的日期归档页。
- 外部链接：文章里所有外部链接新标签页打开（`target="_blank" rel="noopener"`，**不加 nofollow**）。推广类链接（自家面板、Telegram、2 个 GitHub 仓库）走本站 `/go/` 跳转：Rank Math → 重定向里有 4 条 302 规则：`go/panel`、`go/telegram`、`go/github-tuic`、`go/github-chain`。`/go/` 必须保持 302 且不被 Cloudflare 缓存，否则点击统计失真。
- 页脚（Elementor 模板 #81）新增第 4 列"加入官方社群"：频道 `t.me/qazsuduwuxiantop`、群组 `t.me/suduwuxiantop`。
- IndexNow 已开启（Rank Math 即时索引模块）。
- 发布脚本 `tools/wp_publish.py` 已内置：图片写入宽高、外部链接加属性、推广链接走 `/go/`。

## 3. 需要用户处理、助手做不了的事（巡检报告里每周最多提醒一次，不要天天催）

1. **Google Search Console / Bing 验证与提交站点地图**（当前 Rank Math 分析模块没连 Google，看不到任何搜索数据）。用户把验证标记 `<meta name="google-site-verification" ...>` 发来后，助手可通过 Elementor 自定义代码（位置 elementor_head）加到站点里并验证。
2. 在宝塔看服务器日志，确认 Googlebot / bingbot 有没有来过。
3. Cloudflare：关闭"电子邮件地址混淆"（会破坏 5 篇搭建教程里的示例邮箱）、添加安全响应头（X-Content-Type-Options、X-Frame-Options、Referrer-Policy）。
4. Rank Math 后台：关闭 Slack 增强分享（去掉首页"Written by"标签）；robots.txt 里 `User-agent: *` 组加 `Disallow: /go/`（避免机器人点击计入跳转统计）。
5. 更换 WordPress 应用程序密码（历史上有一次命令写错，密码被拆开尝试解析，虽然没发出去，但建议换）。
6. **频道与群组标签**：t.me/suduwuxiantop 实际是群组（12 members），t.me/qazsuduwuxiantop 是频道（7 subscribers），但 51 篇文章结尾和 GitHub 摘要里写的是"Telegram 频道：t.me/suduwuxiantop"。用户尚未决定是否统一改正；要改还需用户在 Rank Math 里再加一条 `go/channel`（302 → `https://t.me/qazsuduwuxiantop`）。
7. GitHub 仓库的 About 描述和 Topics（API 改不了，需用户在页面设置，内容见 launch kit）。
8. 是否停用用不上的插件（Angie、无障碍插件、Easy TOC 等，影响回源速度）：用户未决定，**助手不得自行停用**。
9. robots.txt 冲突：Cloudflare 托管段对 GPTBot、ClaudeBot、Google-Extended、CCBot 等写了 `Disallow: /`，Rank Math 自定义段又写了 `Allow: /`；Baiduspider 只被屏蔽。是否有意需用户确认。

## 4. 每日巡检规范

运行：`pip install requests` 后 `python3 tools/daily_check.py --apply`（默认只读；`--apply` 才做白名单修复）。脚本限流（串行、间隔 1 秒、每天只抽首页 + 3 篇文章，单次超过 8 秒或累计 2 次 5xx/524 就停止）。

### 4.1 可以自动修复（幂等、可回滚）

1. 文章里的外部链接补 `target="_blank" rel="noopener"`，推广链接改走 `/go/`；
2. 封面图缺 alt 时用文章标题补上；
3. 没有分享图的文章设置默认分享图（媒体 ID 857）；
4. 新增或改动的网址通过 IndexNow 提交（每天最多 20 个）；
5. 脚本报告里"SEO 描述不在 60～125 字符"的文章：会话根据正文撰写一条 70～90 字的描述，用 `POST /rankmath/v1/updateMeta`（`meta.rank_math_description`）写入。只限报告里列出的文章，不得编造正文没有的说法。

所有改正文的操作都先备份到 `ops/backups/<日期>/<文章ID>.json`（WordPress 的"修订版本"也能回滚）。

### 4.2 只报告，不自动改

站点速度与缓存状态、`/go/` 异常、robots.txt 变化、站内死链和跳转链接、H1 数量、正文图片缺宽高、Rank Math 搜索数据变化。需要用户决定的事项只写进报告，说明建议做法。

### 4.3 禁止

- 安装、停用、删除插件；改 WordPress 设置、主题、Elementor 模板和页面（页脚 #81、首页、定价、下载、帮助、B2B 等）；改 Rank Math 的重定向、robots、全局设置；改 Cloudflare / DNS / 服务器；
- 发布新文章、删除任何内容、改文章正文里的文字（4.1 之外）；
- 并发请求、爬全站、重复重试；中途停止后不要再试；
- 打印或提交凭据；
- 给用户加"每日必做"的任务。

## 5. 日志与回滚

- 每天把当日报告的摘要（5～10 行：状态、修了什么、需要用户的事）追加到 `ops/LOG.md`，状态写入 `ops/state.json`（脚本自动更新），一起提交推送。提交作者和格式见 `CLAUDE.md` 第六节，提交信息用 `docs: 每日巡检 YYYY-MM-DD`。
- 回滚：文章用 `ops/backups` 里的原文或 WordPress 修订版本；分享图和 alt 在 Rank Math / 媒体库里改回；Elementor 页脚等的旧数据此前保存在已被清理的临时目录，如需回滚请让用户用 Elementor 的历史记录。
- 巡检出现"中途停止"或连续 5xx/524：不要继续请求，在报告第一行写明，并提醒用户先看宝塔里的 PHP 慢日志和 Nginx 错误日志。
