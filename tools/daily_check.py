#!/usr/bin/env python3
"""每日巡检：默认只读，加 --apply 才会做白名单内的小修复。

用法：python3 tools/daily_check.py [--apply] [--state ops/state.json] > report.md
凭据读取环境变量 WP_URL / WP_USER / WP_APP_PASSWORD，不会打印。

对服务器很克制（2 核 3.8GB，曾被并发请求拖垮）：
- 所有请求串行，每次间隔 GAP 秒；
- 单个请求超过 SLOW 秒、或出现 5xx/524 累计 2 次就立刻停止后续请求，只输出已有结果；
- 每天只抽 3 个文章页 + 首页，新文章/改动文章最多检查 MAX_POSTS 篇。

--apply 只做下面这些幂等、可回滚的修复（改前备份到 ops/backups/<日期>/）：
  1. 文章里的外部链接补 target="_blank" rel="noopener"（不加 nofollow）
  2. 指向自家面板 / Telegram / GitHub 仓库的链接改走 /go/ 跳转页
  3. 封面图缺 alt 时用文章标题补上
  4. 没有分享图的文章设置默认分享图
  5. 把新增或改动的网址用 IndexNow 通知搜索引擎
其他一律只报告。
"""
import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlparse

import requests

WP_URL = os.environ.get("WP_URL", "https://main.suduwuxian.top").rstrip("/")
API = WP_URL + "/wp-json"
HOST = urlparse(WP_URL).netloc
GAP, SLOW, MAX_POSTS = 1.0, 8.0, 20
OG_MEDIA_ID, OG_URL = "857", WP_URL + "/wp-content/uploads/2026/10/suduwuxian-og-default.webp"
GO = {"https://qaz.suduwuxian.top": "panel", "https://qaz.suduwuxian.top/": "panel",
      "https://t.me/suduwuxiantop": "telegram",
      "https://github.com/suduwuxiantop/tuic-singbox-installer": "github-tuic",
      "https://github.com/suduwuxiantop/proxy-chain-examples": "github-chain"}
GO_EXPECT = {"panel": "https://qaz.suduwuxian.top", "telegram": "https://t.me/suduwuxiantop",
             "github-tuic": "https://github.com/suduwuxiantop/tuic-singbox-installer",
             "github-chain": "https://github.com/suduwuxiantop/proxy-chain-examples"}

s = requests.Session()
s.headers["User-Agent"] = "suduwuxian-daily-check/1.0"
bad_responses = 0
stopped = False
lines, fixable, changed_urls = [], [], []


def out(msg=""):
    lines.append(msg)


def get(url, auth=False, **kw):
    """限流 GET；返回 (response|None, 秒数)。"""
    global bad_responses, stopped
    if stopped:
        return None, 0
    time.sleep(GAP)
    t = time.time()
    try:
        r = s.get(url, timeout=40, allow_redirects=kw.pop("allow_redirects", True),
                  auth=(os.environ["WP_USER"], os.environ["WP_APP_PASSWORD"]) if auth else None, **kw)
    except requests.RequestException as e:
        bad_responses += 1
        stopped = bad_responses >= 2
        return None, round(time.time() - t, 2)
    dt = round(time.time() - t, 2)
    if r.status_code >= 500 or r.status_code == 524 or dt > SLOW:
        bad_responses += 1
        if bad_responses >= 2:
            stopped = True
    return r, dt


def post(path, payload):
    time.sleep(GAP)
    return requests.post(API + path, json=payload, timeout=60,
                         auth=(os.environ["WP_USER"], os.environ["WP_APP_PASSWORD"]))


def wp(path, **params):
    r, _ = get(API + path, auth=True, params=params)
    return r.json() if r is not None and r.ok else None


def check_site(day):
    out("## 一、站点可用性与速度")
    posts = wp("/wp/v2/posts", per_page=100, _fields="id,link", status="publish") or []
    n = max(len(posts), 1)
    pages = [WP_URL + "/"] + [posts[(day * 3 + k) % n]["link"] for k in range(min(3, len(posts)))]
    for u in pages:
        r, dt = get(u)
        if r is None:
            out(f"- ❌ {u} 无法访问（{dt}s）")
            continue
        warn = r.text.count("Warning</b>") + r.text.count("Fatal error")
        cache = r.headers.get("cf-cache-status", "-")
        mark = "✅" if r.status_code == 200 and not warn and dt < 3 else "⚠️"
        out(f"- {mark} {urlparse(u).path or '/'} → {r.status_code}，{dt}s，缓存 {cache}，PHP 警告 {warn}")
    r, dt = get(WP_URL + f"/?nc={int(time.time())}")
    if r is not None:
        out(f"- {'✅' if dt < 4 else '⚠️'} 首页回源（绕过缓存）{dt}s")
    return len(posts)


def check_go():
    out("\n## 二、/go/ 跳转（必须 302、目标正确、不被缓存）")
    for name, target in GO_EXPECT.items():
        r, dt = get(f"{WP_URL}/go/{name}", allow_redirects=False)
        if r is None:
            out(f"- ❌ /go/{name} 无法访问")
            continue
        ok = r.status_code == 302 and r.headers.get("location", "").rstrip("/") == target.rstrip("/")
        cached = r.headers.get("cf-cache-status") == "HIT"
        out(f"- {'✅' if ok and not cached else '❌'} /go/{name} → {r.status_code} "
            f"{r.headers.get('location', '')}，缓存 {r.headers.get('cf-cache-status', '-')}，{dt}s")


SEARCH_BOTS = ["Googlebot", "Bingbot", "OAI-SearchBot", "Claude-SearchBot", "PerplexityBot", "ChatGPT-User", "Claude-User"]
TRAIN_BOTS = ["GPTBot", "ClaudeBot", "Google-Extended", "CCBot", "Baiduspider"]


def check_crawl(total_posts, state):
    out("\n## 三、抓取入口")
    r, _ = get(WP_URL + "/robots.txt")
    if r is not None:
        t = r.text
        rp = urllib.robotparser.RobotFileParser()
        rp.parse(t.splitlines())
        out(f"- {'✅' if 'Sitemap:' in t else '❌'} robots.txt 声明了 Sitemap")
        blocked = [b for b in SEARCH_BOTS if not rp.can_fetch(b, WP_URL + "/")]
        out(f"- {'✅' if not blocked else '❌'} 搜索类爬虫可抓取首页" + (f"（被屏蔽：{', '.join(blocked)}）" if blocked else ""))
        rules = {}
        group, in_rules = [], False
        for ln in t.splitlines():
            ln = ln.split("#")[0].strip()
            if not ln:
                continue
            k, _, v = ln.partition(":")
            k, v = k.strip().lower(), v.strip()
            if k == "user-agent":
                if in_rules:
                    group, in_rules = [], False
                group.append(v)
            elif k in ("allow", "disallow") and v == "/":
                in_rules = True
                for ua in group:
                    rules.setdefault(ua.lower(), set()).add(k)
            elif k in ("allow", "disallow"):
                in_rules = True
        only_block = [b for b in TRAIN_BOTS if rules.get(b.lower()) == {"disallow"}]
        conflict = [b for b in TRAIN_BOTS if rules.get(b.lower()) == {"allow", "disallow"}]
        out(f"- ℹ️ 被 robots.txt 屏蔽且没有放行的训练类爬虫：{', '.join(only_block) or '无'}"
            + ("（Baiduspider 被屏蔽意味着百度无法抓取）" if "Baiduspider" in only_block else ""))
        out(f"- {'⚠️' if conflict else '✅'} 同一爬虫既被 Disallow 又被 Allow（Cloudflare 托管段与 Rank Math 自定义段冲突）：{', '.join(conflict) or '无'}")
        out(f"- {'✅' if rp.can_fetch('Googlebot', WP_URL + '/go/panel') is False else 'ℹ️'} /go/ 对 Googlebot：{'已屏蔽' if not rp.can_fetch('Googlebot', WP_URL + '/go/panel') else '未屏蔽（机器人点击会计入跳转统计）'}")
        h = __import__("hashlib").sha256(t.encode()).hexdigest()[:12]
        if state.get("robots_hash") and state["robots_hash"] != h:
            out(f"- ⚠️ robots.txt 自上次巡检后发生了变化（{state['robots_hash']} → {h}），请确认是否有意")
        state["robots_hash"] = h
    r, _ = get(WP_URL + "/post-sitemap.xml")
    if r is not None:
        n = len(re.findall(r"<loc>", r.text))
        out(f"- {'✅' if n >= total_posts else '⚠️'} post-sitemap 含 {n} 个网址（已发布文章 {total_posts} 篇）")
    d = wp("/rankmath/v1/an/analyticsSummary") or {}
    sm = d.get("summary", {})
    out(f"- ℹ️ Rank Math 搜索数据：展示 {sm.get('impressions', 'n/a')}，点击 {sm.get('clicks', 'n/a')}（n/a 表示还没连接 Google）")
    return sm


def inspect_posts(since, apply, day):
    out("\n## 四、新增和改动的文章")
    posts = wp("/wp/v2/posts", per_page=MAX_POSTS, status="publish", orderby="modified", order="desc",
               context="edit", modified_after=since, _fields="id,slug,link,title,modified,content,featured_media") or []
    if not posts:
        out("- 自上次巡检（%s）以来没有新增或改动的文章。" % since)
        return
    Path(f"ops/backups/{day}").mkdir(parents=True, exist_ok=True)
    for p in posts:
        raw = p["content"]["raw"]
        title = re.sub(r"<[^>]+>", "", p["title"]["rendered"])
        issues, new = [], raw
        parts = re.split(r"(<script\b.*?</script>|<style\b.*?</style>)", raw, flags=re.S | re.I)
        for i in range(0, len(parts), 2):
            def decorate(m):
                attrs = m.group(1)
                h = re.search(r'href="(https?://[^"]+)"', attrs)
                if not h:
                    return m.group(0)
                url = h.group(1)
                if url in GO:
                    attrs = attrs.replace(f'href="{url}"', f'href="{WP_URL}/go/{GO[url]}"')
                    url = f"{WP_URL}/go/{GO[url]}"
                if urlparse(url).netloc.endswith(HOST) and "/go/" not in url:
                    return f"<a {attrs}>"
                if "target=" not in attrs:
                    attrs += ' target="_blank"'
                if "noopener" not in attrs:
                    attrs += ' rel="noopener"'
                return f"<a {attrs}>"
            parts[i] = re.sub(r"<a\s([^>]*?)>", decorate, parts[i])
        new = "".join(parts)
        if new != raw:
            issues.append("外部/推广链接属性可自动修复")
        r, _ = get(p["link"])
        desc = re.search(r'<meta name="description" content="([^"]*)"', r.text) if r is not None else None
        dl = len(desc.group(1)) if desc else 0
        if not 60 <= dl <= 125:
            issues.append(f"SEO 描述 {dl} 字符（应 60～125，需要人工/会话撰写）")
        if r is not None and 'property="og:image"' not in r.text:
            issues.append("缺分享图（可自动设置默认图）")
        if r is not None and len(re.findall(r"<h1[\s>]", r.text)) != 1:
            issues.append("H1 数量不是 1")
        if re.search(r"<img(?![^>]*\bwidth=)[^>]*uploads/", raw):
            issues.append("正文图片缺宽高属性（只报告）")
        if p["featured_media"]:
            m = wp(f"/wp/v2/media/{p['featured_media']}", _fields="id,alt_text")
            if m is not None and not (m.get("alt_text") or "").strip():
                issues.append("封面图缺 alt（可自动补）")
                fixable.append(("alt", p["featured_media"], title))
        for u in sorted(set(re.findall(r'href="(%s/[^"#?]+)"' % re.escape(WP_URL), raw)))[:12]:
            if "/go/" in u:
                continue
            rr, _ = get(u, allow_redirects=False)
            if rr is not None and rr.status_code >= 400:
                issues.append(f"站内链接 {rr.status_code}：{u}")
            elif rr is not None and rr.status_code in (301, 302, 308):
                issues.append(f"站内链接发生跳转：{u} → {rr.headers.get('location', '')}（可改成最终网址）")
        out(f"- {'✅' if not issues else '⚠️'} [{p['id']}] {title[:36]}（{p['modified']}）")
        for i in issues:
            out(f"    - {i}")
        if apply:
            if new != raw:
                Path(f"ops/backups/{day}/{p['id']}.json").write_text(json.dumps({"id": p["id"], "content": raw}, ensure_ascii=False))
                post(f"/wp/v2/posts/{p['id']}", {"content": new})
                out("    - 🔧 已修复链接属性 / 推广链接走 /go/")
            if r is not None and 'property="og:image"' not in r.text:
                post("/rankmath/v1/updateMeta", {"objectType": "post", "objectID": p["id"], "meta": {
                    "rank_math_facebook_image": OG_URL, "rank_math_facebook_image_id": OG_MEDIA_ID,
                    "rank_math_twitter_use_facebook": "on"}})
                out("    - 🔧 已设置默认分享图")
            changed_urls.append(p["link"])
    if apply:
        for kind, mid, title in fixable:
            if kind == "alt":
                post(f"/wp/v2/media/{mid}", {"alt_text": title})
                out(f"- 🔧 封面图 {mid} 已补 alt：{title[:30]}")
        if changed_urls:
            res = post("/rankmath/v1/in/submitUrls", {"urls": "\n".join(changed_urls[:20])})
            out(f"- 🔧 IndexNow 提交 {len(changed_urls[:20])} 个网址：HTTP {res.status_code}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--state", default="ops/state.json")
    args = ap.parse_args()
    if not (os.environ.get("WP_USER") and os.environ.get("WP_APP_PASSWORD")):
        sys.exit("请先设置 WP_USER 和 WP_APP_PASSWORD 环境变量")
    # 站点时区是 UTC+8，REST 的 modified_after 按站点本地时间比较，所以这里统一用本地时间
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(hours=8)
    day = now.strftime("%Y-%m-%d")
    sp = Path(args.state)
    state = json.loads(sp.read_text()) if sp.exists() else {}
    since = state.get("last_run", (now - datetime.timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S"))
    out(f"# 每日巡检 {day}（{'含自动修复' if args.apply else '只读'}）\n")
    total = check_site(now.timetuple().tm_yday)
    check_go()
    sm = check_crawl(total, state)
    if not stopped:
        inspect_posts(since, args.apply, day)
    if stopped:
        out("\n> ⛔ 请求出现多次超时或 5xx，已按规则停止后续检查，请先排查服务器。")
    out("\n## 摘要\n- 异常请求计数：%d；是否中途停止：%s" % (bad_responses, "是" if stopped else "否"))
    print("\n".join(lines))
    if args.apply or not sp.exists():
        sp.parent.mkdir(parents=True, exist_ok=True)
        hist = state.get("history", [])[-29:]
        hist.append({"day": day, "impressions": sm.get("impressions"), "clicks": sm.get("clicks"), "bad": bad_responses})
        sp.write_text(json.dumps({"last_run": now.strftime("%Y-%m-%dT%H:%M:%S"), "robots_hash": state.get("robots_hash"), "history": hist}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
