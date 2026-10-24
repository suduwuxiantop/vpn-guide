#!/usr/bin/env python3
"""把 articles/ 里的完整版文章发布到 WordPress。

用法：
  python3 tools/wp_publish.py [--status publish] [--category 名称 ...] [--tag 名称 ...] [--dry-run] slug [slug ...]

- 凭据读取环境变量 WP_URL / WP_USER / WP_APP_PASSWORD（应用程序密码，Basic Auth），不会打印。
- 文中 ![alt](../images/<slug>/x.webp) 会上传到媒体库（同名已存在则复用），写入 alt 和说明，
  并把 cover.webp 设为特色图片。
- 指向其他 .md 的链接改写为站内链接：已在本次发布的用本次网址，GitHub 摘要版里有原文链接的用原文链接，
  否则用 GitHub 链接。跑两遍，保证本次发布的文章之间互链都是站内地址。
- 同一 slug 已存在时更新原文章，不重复发。
- 摘要版（含"完整内容请阅读原文"）会被拒绝发布，避免把摘要覆盖到网站上。
- 检测到 Rank Math / Yoast 时尝试写入 SEO 描述，写不进去会在输出里提示。
"""
import argparse
import os
import re
import sys
from pathlib import Path

import markdown
import requests

ROOT = Path(__file__).resolve().parent.parent
WP_URL = os.environ.get("WP_URL", "https://main.suduwuxian.top").rstrip("/")
GITHUB_BLOB = "https://github.com/suduwuxiantop/vpn-guide/blob/main/articles/"
SUMMARY_MARK = "完整内容请阅读原文"


def site_url_of(article: Path):
    if not article.exists():
        return None
    m = re.search(r"\((https://main\.suduwuxian\.top/[^)\s]+)\)", article.read_text(encoding="utf-8"))
    return m.group(1) if m else None


def short_answer(text):
    custom = re.search(r"<!-- description: (.+?) -->", text)
    if custom:
        return custom.group(1).strip()
    m = re.search(r"\*\*简短回答\*\*[：:](.+)", text)
    plain = re.sub(r"\*\*|`|\[([^\]]+)\]\([^)]+\)", r"\1", m.group(1) if m else "").strip()
    # meta description 控制在 80 个字符左右，尽量在句号处截断
    if len(plain) <= 80:
        return plain
    cut = plain[:80]
    for mark in "。；，":
        if mark in cut[40:]:
            return cut[: cut.rfind(mark)] + "。"
    return cut + "…"


class WP:
    def __init__(self, dry_run):
        self.dry = dry_run
        self.s = requests.Session()
        self.s.auth = (os.environ.get("WP_USER", ""), os.environ.get("WP_APP_PASSWORD", ""))
        self.api = WP_URL + "/wp-json"

    def get(self, path, **params):
        r = self.s.get(self.api + path, params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def post(self, path, **kw):
        r = self.s.post(self.api + path, timeout=120, **kw)
        if r.status_code >= 300:
            sys.exit(f"POST {path} 失败：HTTP {r.status_code} {r.text[:300]}")
        return r.json()

    def term_ids(self, taxonomy, names):
        ids = []
        for name in names:
            found = [t for t in self.get(f"/wp/v2/{taxonomy}", search=name, per_page=100) if t["name"] == name]
            if not found:
                sys.exit(f"{taxonomy} 里没有「{name}」，请先在后台创建或换一个已有名称")
            ids.append(found[0]["id"])
        return ids

    def upload_image(self, path: Path, media_slug, alt, caption):
        if self.dry:
            return -1 if path.stem == "cover" else 0, f"https://example.invalid/{media_slug}{path.suffix}"
        existing = self.get("/wp/v2/media", slug=media_slug)
        if existing:
            return existing[0]["id"], existing[0]["source_url"]
        media = self.post("/wp/v2/media", data=path.read_bytes(), headers={
            "Content-Disposition": f'attachment; filename="{media_slug}{path.suffix}"',
            "Content-Type": "image/webp" if path.suffix == ".webp" else "image/png"})
        self.post(f"/wp/v2/media/{media['id']}", json={"alt_text": alt, "caption": caption, "slug": media_slug})
        return media["id"], media["source_url"]


def build_post(wp: WP, slug, published_urls):
    path = ROOT / "articles" / f"{slug}.md"
    text = path.read_text(encoding="utf-8")
    if SUMMARY_MARK in text:
        sys.exit(f"{slug} 是摘要版，不能发布到网站。请先恢复完整版（git log 里找）。")

    title_match = re.match(r"#\s+(.+)\n", text)
    title, body = title_match.group(1).strip(), text[title_match.end():]
    body = re.sub(r"<!-- description: .+? -->\n", "", body)

    featured = 0

    def replace_image(m):
        nonlocal featured
        alt, src = m.group(1), m.group(2)
        img = (path.parent / src).resolve()
        caption_match = re.search(re.escape(m.group(0)) + r"\n\n\*图：(.+?)\*", body)
        media_id, url = wp.upload_image(img, f"{slug}-{img.stem}", alt,
                                        caption_match.group(1) if caption_match else "")
        if img.stem == "cover":
            featured = media_id
        return f"![{alt}]({url})"

    body = re.sub(r"!\[([^\]]*)\]\((\.\./images/[^)]+)\)", replace_image, body)

    def fix_link(m):
        label, target = m.group(1), m.group(2)
        url = published_urls.get(target[:-3]) or site_url_of(path.parent / target) or GITHUB_BLOB + target
        return f"[{label}]({url})"

    body = re.sub(r"\[([^\]]+)\]\(([a-z0-9-]+\.md)\)", fix_link, body)
    html = markdown.markdown(body, extensions=["tables", "fenced_code", "sane_lists"])
    html = html.replace("<img ", '<img loading="lazy" decoding="async" ')
    return {"title": title, "slug": slug, "content": html, "excerpt": short_answer(text),
            "featured_media": featured}


def set_seo_meta(wp: WP, post_id, description, namespaces):
    """尽量写入 SEO 插件的描述字段；插件没开放 REST 写入时返回 False。"""
    if "rankmath/v1" in namespaces:
        r = wp.s.post(wp.api + "/rankmath/v1/updateMeta", timeout=30, json={
            "objectType": "post", "objectID": post_id, "meta": {"rank_math_description": description}})
        return r.status_code < 300
    if "yoast/v1" in namespaces:
        r = wp.s.post(f"{wp.api}/wp/v2/posts/{post_id}", timeout=30,
                      json={"meta": {"_yoast_wpseo_metadesc": description}})
        return r.status_code < 300 and r.json().get("meta", {}).get("_yoast_wpseo_metadesc") == description
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="+")
    ap.add_argument("--status", default="draft", choices=["draft", "publish", "pending"])
    ap.add_argument("--category", action="append", default=[])
    ap.add_argument("--tag", action="append", default=[])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.dry_run and not (os.environ.get("WP_USER") and os.environ.get("WP_APP_PASSWORD")):
        sys.exit("请先设置 WP_USER 和 WP_APP_PASSWORD 环境变量")

    wp = WP(args.dry_run)
    # dry-run 完全离线，只预览转换结果
    namespaces = [] if args.dry_run else wp.get("/").get("namespaces", [])
    categories = [] if args.dry_run else wp.term_ids("categories", args.category)
    tags = [] if args.dry_run else wp.term_ids("tags", args.tag)
    published_urls = {}

    for slug in args.slugs * (1 if args.dry_run else 2):
        post = build_post(wp, slug, published_urls)
        post["status"] = args.status
        if categories:
            post["categories"] = categories
        if tags:
            post["tags"] = tags
        if args.dry_run:
            print(f"[预览] {post['title']}\n  slug={slug} 特色图片={post['featured_media']}\n  描述={post['excerpt']}\n")
            continue
        existing = wp.get("/wp/v2/posts", slug=slug, status="any", context="edit")
        result = wp.post(f"/wp/v2/posts/{existing[0]['id']}" if existing else "/wp/v2/posts", json=post)
        if slug not in published_urls:
            seo = set_seo_meta(wp, result["id"], post["excerpt"], namespaces)
            print(f"{'已更新' if existing else '已创建'}（{args.status}）：{post['title']}\n  {result['link']}"
                  f"\n  SEO 描述：{'已写入' if seo else '未写入（插件未开放 REST，需后台手动填写或用摘要）'}")
        published_urls[slug] = result["link"]


if __name__ == "__main__":
    main()
