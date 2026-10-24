#!/usr/bin/env python3
"""网站 SEO 只读体检（标准见 CLAUDE.md 第三节，参照 maglau.com 体检报告的检查项）。

用法：python3 tools/seo_audit.py [--site https://main.suduwuxian.top] [--pages 15] [--render] > report.md
  --pages   从 sitemap 里抽查的文章页数量（首页总是检查）
  --render  额外用 Chromium 在 375px 宽度渲染首页，检查移动端横向溢出
只发 GET 请求，不修改网站任何内容。
"""
import argparse
import collections
import glob
import json
import re
import time
import urllib.robotparser
import uuid
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (compatible; suduwuxian-seo-audit/1.0)"
AI_BOTS = ["Googlebot", "Bingbot", "OAI-SearchBot", "GPTBot", "ChatGPT-User", "ClaudeBot",
           "Claude-SearchBot", "Claude-User", "PerplexityBot"]
SECURITY_HEADERS = ["strict-transport-security", "x-content-type-options", "x-frame-options", "referrer-policy"]

s = requests.Session()
s.headers["User-Agent"] = UA


def fetch(url, **kw):
    t = time.time()
    r = s.get(url, timeout=30, **kw)
    return r, round((time.time() - t) * 1000)


def robots_blocks(robots_txt, bot):
    """robots.txt 是否禁止该爬虫抓取首页（即整站屏蔽）。"""
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(robots_txt.splitlines())
    return not rp.can_fetch(bot, "/")


def sitemap_urls(site, robots_txt):
    candidates = re.findall(r"(?im)^sitemap:\s*(\S+)", robots_txt) + [
        site + "/wp-sitemap.xml", site + "/sitemap_index.xml", site + "/sitemap.xml"]
    for sm in dict.fromkeys(candidates):
        r, _ = fetch(sm)
        if r.status_code == 200 and "xml" in r.headers.get("content-type", ""):
            urls, queue = [], [sm]
            while queue and len(urls) < 2000:
                x = s.get(queue.pop(0), timeout=30)
                locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", x.text)
                (queue if "<sitemapindex" in x.text else urls).extend(locs)
            return sm, r.headers.get("content-type"), urls
    return None, None, []


def audit_page(url, site_host):
    r, ms = fetch(url)
    soup = BeautifulSoup(r.content, "html.parser")  # 让 bs4 按 meta charset 解码，避免中文乱码
    meta = lambda **a: (soup.find("meta", attrs=a) or {}).get("content")
    canonical = soup.find("link", rel="canonical")
    ld_types = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except ValueError:
            ld_types.append("（JSON 解析失败）")
            continue
        items = data.get("@graph", [data]) if isinstance(data, dict) else data
        ld_types += [str(i.get("@type")) for i in items if isinstance(i, dict)]
    imgs = soup.find_all("img")
    links = [urlparse(urljoin(url, a.get("href", ""))) for a in soup.find_all("a", href=True)]
    main = soup.find("article") or soup.find("main") or soup.body or soup
    text = re.sub(r"\s+", "", main.get_text())
    return {
        "url": url, "status": r.status_code, "final": r.url, "ms": ms, "kb": len(r.content) // 1024,
        "title": (soup.title.string or "").strip() if soup.title else "",
        "desc": meta(name="description") or "",
        "canonical": canonical.get("href") if canonical else "",
        "lang": (soup.html or {}).get("lang", ""),
        "og": all(meta(property=p) for p in ["og:title", "og:description", "og:image"]),
        "twitter": bool(meta(name="twitter:card")),
        "ld": ld_types, "h1": len(soup.find_all("h1")),
        "img": len(imgs), "img_no_alt": sum(1 for i in imgs if not i.get("alt")),
        "img_no_size": sum(1 for i in imgs if not (i.get("width") and i.get("height"))),
        "internal": sum(1 for l in links if l.netloc == site_host),
        "external": sum(1 for l in links if l.netloc and l.netloc != site_host),
        "chars": len(text),
        "cache": r.headers.get("cache-control", ""),
        "security": [h for h in SECURITY_HEADERS if h not in r.headers],
        "long_slug": len(urlparse(url).path) > 80,
    }


def mobile_overflow(url):
    from playwright.sync_api import sync_playwright
    exe = next(iter(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")), None)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        page = b.new_page(viewport={"width": 375, "height": 800})
        page.goto(url, wait_until="networkidle", timeout=60000)
        sw, cw = page.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
        b.close()
    return sw, cw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="https://main.suduwuxian.top")
    ap.add_argument("--pages", type=int, default=15)
    ap.add_argument("--render", action="store_true")
    args = ap.parse_args()
    site = args.site.rstrip("/")
    host = urlparse(site).netloc
    out, issues = [], []

    def issue(level, text):
        issues.append((level, text))

    out.append(f"# {host} SEO 体检报告\n\n- 体检时间：{time.strftime('%Y-%m-%d %H:%M')}\n- 方式：只读 HTTP 抓取"
               f"{' + 375px 浏览器渲染' if args.render else ''}\n")

    # 1. 站点级：跳转、robots、sitemap、404
    out.append("## 一、站点级检查\n\n| 项目 | 结果 |\n|---|---|")
    is_ip = re.fullmatch(r"[\d.:]+", host)
    for variant in [f"http://{host}/", None if is_ip or host.startswith("www.") else f"https://www.{host}/"]:
        if not variant:
            continue
        try:
            r = s.get(variant, timeout=20, allow_redirects=False)
            out.append(f"| `{variant}` | HTTP {r.status_code} → {r.headers.get('location', '（无跳转）')} |")
            if r.status_code not in (301, 308):
                issue("P0", f"`{variant}` 没有 301 跳转到主域（实际 {r.status_code}）")
        except requests.RequestException as e:
            out.append(f"| `{variant}` | 无法访问：{type(e).__name__} |")
            issue("P1", f"`{variant}` 无法访问（DNS 或证书问题），输入这个地址的访客打不开")

    r, _ = fetch(site + "/robots.txt")
    robots = r.text if r.status_code == 200 and "text/plain" in r.headers.get("content-type", "") else ""
    out.append(f"| robots.txt | HTTP {r.status_code}，{r.headers.get('content-type', '')} |")
    if not robots:
        issue("P0", "robots.txt 不存在或不是 text/plain")
    elif not re.search(r"(?im)^sitemap:", robots):
        issue("P1", "robots.txt 没有声明 Sitemap")
    blocked = [b for b in AI_BOTS if robots and robots_blocks(robots, b)]
    out.append(f"| 被 robots 整站屏蔽的爬虫 | {', '.join(blocked) or '无'} |")
    if blocked:
        issue("P0", f"robots.txt 屏蔽了 {', '.join(blocked)}，这些搜索引擎 / AI 搜索无法收录")

    sm, sm_type, urls = sitemap_urls(site, robots)
    out.append(f"| sitemap | {sm or '未找到'}（{sm_type or '-'}），共 {len(urls)} 个 URL |")
    if not sm:
        issue("P0", "找不到 XML sitemap")

    r, _ = fetch(f"{site}/{uuid.uuid4().hex}-not-exist/")
    out.append(f"| 不存在的页面 | HTTP {r.status_code} |")
    if r.status_code != 404:
        issue("P0", f"不存在的页面返回 {r.status_code}，属于软 404")

    r, _ = fetch(site + "/llms.txt")
    out.append(f"| /llms.txt | HTTP {r.status_code} |")
    if r.status_code != 200:
        issue("P2", "没有 /llms.txt（可选，帮助 AI 搜索理解站点结构）")

    # 2. 页面级
    pages = [site + "/"] + [u for u in urls if u.rstrip("/") != site][: args.pages]
    results = [audit_page(u, host) for u in pages]
    out.append("\n## 二、页面级检查\n\n| 页面 | 状态 | 耗时 | title | description | canonical | lang | OG | JSON-LD | H1 | 图片(无alt/无宽高) | 正文字数 |\n|---|---|---|---|---|---|---|---|---|---|---|---|")
    for p in results:
        path = urlparse(p["url"]).path or "/"
        out.append(f"| `{path[:40]}` | {p['status']} | {p['ms']}ms | {len(p['title'])} 字 | {len(p['desc'])} 字 | "
                   f"{'✓' if p['canonical'] else '✗'} | {p['lang'] or '✗'} | {'✓' if p['og'] else '✗'} | "
                   f"{', '.join(p['ld']) or '✗'} | {p['h1']} | {p['img']}({p['img_no_alt']}/{p['img_no_size']}) | {p['chars']} |")

    home = results[0]
    titles = collections.Counter(p["title"] for p in results)
    descs = collections.Counter(p["desc"] for p in results if p["desc"])
    for t, n in titles.items():
        if n > 1:
            issue("P0", f"{n} 个页面共用同一个 title：「{t}」")
    for d, n in descs.items():
        if n > 1:
            issue("P0", f"{n} 个页面共用同一个 description")
    for p in results:
        path = urlparse(p["url"]).path or "/"
        if not p["desc"]:
            issue("P0", f"`{path}` 没有 meta description")
        elif not 40 <= len(p["desc"]) <= 160:
            issue("P2", f"`{path}` description 长度 {len(p['desc'])}，建议中文 70～80 字")
        if not p["canonical"]:
            issue("P0", f"`{path}` 没有 canonical")
        if not p["lang"].lower().startswith("zh"):
            issue("P1", f"`{path}` 的 html lang 是「{p['lang']}」，应为 zh-CN")
        if not p["og"]:
            issue("P1", f"`{path}` Open Graph 不完整（缺 og:title / og:description / og:image）")
        if p["h1"] != 1:
            issue("P1", f"`{path}` 有 {p['h1']} 个 H1，应为 1 个")
        if p["img_no_alt"]:
            issue("P1", f"`{path}` 有 {p['img_no_alt']} 张图片缺 alt")
        if p["long_slug"]:
            issue("P2", f"`{path[:60]}…` URL 过长（多为中文编码 slug），新文章改用英文 slug，旧链接改动需 301")
        if p is not home and not any("Article" in t for t in p["ld"]):
            issue("P1", f"`{path}` 没有 Article 结构化数据")
        if p is not home and p["chars"] < 800:
            issue("P2", f"`{path}` 正文约 {p['chars']} 字，内容偏薄")
        if p["ms"] > 1500:
            issue("P1", f"`{path}` 响应 {p['ms']}ms，偏慢（考虑缓存插件 / CDN）")
    if not any(t in " ".join(home["ld"]) for t in ["Organization", "WebSite"]):
        issue("P1", "首页没有 Organization / WebSite 结构化数据")
    if home["security"]:
        issue("P2", f"缺少安全响应头：{', '.join(home['security'])}")
    if "max-age" not in home["cache"]:
        issue("P2", f"首页 Cache-Control 为「{home['cache'] or '无'}」，静态资源与页面缓存策略需检查")

    out.append(f"\n### 首页详情\n\n- title：{home['title']}\n- description：{home['desc'] or '（无）'}\n"
               f"- canonical：{home['canonical'] or '（无）'}\n- JSON-LD：{', '.join(home['ld']) or '（无）'}\n"
               f"- 站内链接 {home['internal']} 个，站外链接 {home['external']} 个，HTML {home['kb']}KB\n")

    if args.render:
        sw, cw = mobile_overflow(site + "/")
        out.append(f"- 375px 宽度：scrollWidth={sw}，clientWidth={cw}")
        if sw > cw:
            issue("P1", f"移动端首页横向溢出 {sw - cw}px")

    # 3. 问题清单
    out.append("\n## 三、问题清单（按优先级）\n")
    for level in ["P0", "P1", "P2"]:
        items = [t for l, t in issues if l == level]
        if items:
            out.append(f"### {level}（{len(items)} 项）\n" + "\n".join(f"- {t}" for t in items) + "\n")
    if not issues:
        out.append("未发现问题。\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
