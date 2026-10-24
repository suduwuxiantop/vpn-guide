#!/usr/bin/env python3
"""根据 images/<slug>/images.json 生成文章配图（WebP）。

用法：python3 tools/make_images.py images/<slug>/images.json [...]
依赖：playwright（已装 Chromium）、Pillow；中文字体用文泉驿正黑。

images.json 是一个列表，每项：
  {"file": "cover.webp", "type": "cover", "title": "...", "subtitle": "...", "tag": "..."}
  {"file": "steps.webp", "type": "steps", "title": "...", "steps": [["标题", "说明"], ...]}
  {"file": "compare.webp", "type": "compare", "title": "...", "columns": ["A", "B"],
   "rows": [["项目", "✓ 说明", "✗ 说明"], ...], "note": "..."}
  {"file": "decision.webp", "type": "decision", "title": "...",
   "nodes": [{"q": "问题", "yes": "是的结果", "no": "否的结果"}, ...]}
"""
import glob
import html
import io
import os
import json
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

BRAND = "速度无限VPN · main.suduwuxian.top"
FONT = "'WenQuanYi Zen Hei', 'Noto Sans CJK SC', 'Microsoft YaHei', sans-serif"

BASE_CSS = f"""
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: {FONT}; background: #f4f7fb; color: #12233d; width: 1200px; }}
.card {{ padding: 56px 64px 40px; background: #f4f7fb; }}
h1 {{ font-size: 40px; line-height: 1.3; margin-bottom: 36px; }}
.foot {{ margin-top: 36px; font-size: 18px; color: #6b7a90; text-align: right; }}
.ok {{ color: #0f8a5f; }} .bad {{ color: #c0392b; }}
"""


def esc(s):
    return html.escape(str(s))


def mark(s):
    """✓ / ✗ 开头的文字上色。"""
    s = esc(s)
    if s.startswith("✓"):
        return f'<span class="ok">{s}</span>'
    if s.startswith("✗"):
        return f'<span class="bad">{s}</span>'
    return s


def cover(spec):
    return f"""<style>{BASE_CSS}
.cover {{ width: 1200px; height: 630px; padding: 72px 80px; color: #fff;
  background: linear-gradient(135deg, #0b2a5b 0%, #134e8e 55%, #1b8a8f 100%);
  display: flex; flex-direction: column; justify-content: space-between; }}
.tag {{ display: inline-block; font-size: 24px; padding: 8px 20px; border-radius: 999px;
  background: rgba(255,255,255,.16); }}
.t {{ font-size: 64px; line-height: 1.25; font-weight: bold; }}
.s {{ font-size: 30px; line-height: 1.5; color: #d6e6ff; margin-top: 24px; }}
.b {{ font-size: 22px; color: #bcd3f5; }}
</style>
<div class="cover"><div><span class="tag">{esc(spec.get('tag', '2026 教程'))}</span></div>
<div><div class="t">{esc(spec["title"]).replace(chr(10), "<br>")}</div><div class="s">{esc(spec.get('subtitle', ''))}</div></div>
<div class="b">{BRAND}</div></div>"""


def steps(spec):
    items = "".join(
        f"""<div class="st"><div class="n">{i}</div><div><div class="h">{esc(h)}</div>
        <div class="d">{esc(d)}</div></div></div>""" for i, (h, d) in enumerate(spec["steps"], 1))
    return f"""<style>{BASE_CSS}
.st {{ display: flex; gap: 28px; align-items: flex-start; background: #fff; border-radius: 16px;
  padding: 26px 32px; margin-bottom: 18px; box-shadow: 0 2px 6px rgba(18,35,61,.06); }}
.n {{ flex: none; width: 56px; height: 56px; border-radius: 50%; background: #134e8e; color: #fff;
  font-size: 28px; font-weight: bold; display: flex; align-items: center; justify-content: center; }}
.h {{ font-size: 30px; font-weight: bold; margin-bottom: 8px; }}
.d {{ font-size: 24px; line-height: 1.5; color: #44546c; }}
</style><div class="card"><h1>{esc(spec['title'])}</h1>{items}<div class="foot">{BRAND}</div></div>"""


def compare(spec):
    cols = spec["columns"]
    head = "".join(f"<th>{esc(c)}</th>" for c in [""] + cols)
    rows = "".join("<tr>" + "".join(
        f"<td>{mark(c) if j else esc(c)}</td>" for j, c in enumerate(r)) + "</tr>" for r in spec["rows"])
    note = f'<div class="note">{esc(spec["note"])}</div>' if spec.get("note") else ""
    return f"""<style>{BASE_CSS}
table {{ width: 100%; border-collapse: separate; border-spacing: 0; background: #fff; border-radius: 16px;
  overflow: hidden; box-shadow: 0 2px 6px rgba(18,35,61,.06); font-size: 26px; }}
th {{ background: #134e8e; color: #fff; padding: 22px 24px; text-align: left; font-size: 28px; }}
td {{ padding: 22px 24px; border-top: 1px solid #e3e9f2; line-height: 1.45; }}
td:first-child {{ font-weight: bold; width: 26%; }}
.note {{ margin-top: 24px; font-size: 24px; color: #44546c; line-height: 1.5; }}
</style><div class="card"><h1>{esc(spec['title'])}</h1><table><tr>{head}</tr>{rows}</table>{note}
<div class="foot">{BRAND}</div></div>"""


def decision(spec):
    blocks = []
    for i, n in enumerate(spec["nodes"]):
        arrow = '<div class="ar">↓ 否</div>' if i < len(spec["nodes"]) - 1 else ""
        no = "" if i < len(spec["nodes"]) - 1 else f'<div class="res no">否 → {esc(n["no"])}</div>'
        blocks.append(f"""<div class="row"><div class="q">{esc(n['q'])}</div>
        <div class="res yes">是 → {esc(n['yes'])}</div></div>{no}{arrow}""")
    return f"""<style>{BASE_CSS}
.row {{ display: flex; gap: 24px; align-items: stretch; }}
.q {{ flex: 1; background: #134e8e; color: #fff; border-radius: 16px; padding: 26px 30px; font-size: 28px;
  line-height: 1.45; font-weight: bold; }}
.res {{ flex: 1; background: #fff; border-radius: 16px; padding: 26px 30px; font-size: 26px; line-height: 1.45;
  box-shadow: 0 2px 6px rgba(18,35,61,.06); border-left: 8px solid #0f8a5f; }}
.res.no {{ border-left-color: #d68910; margin-top: 18px; }}
.ar {{ font-size: 26px; color: #6b7a90; padding: 14px 0 14px 40px; }}
</style><div class="card"><h1>{esc(spec['title'])}</h1>{''.join(blocks)}<div class="foot">{BRAND}</div></div>"""


RENDER = {"cover": cover, "steps": steps, "compare": compare, "decision": decision}


def main(paths):
    with sync_playwright() as p:
        # 云端环境里预装的 Chromium 不一定和 pip 版 playwright 匹配，有就优先用它
        exe = os.environ.get("CHROMIUM_PATH") or next(iter(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")), None)
        browser = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
        for spec_path in map(Path, paths):
            for spec in json.loads(spec_path.read_text(encoding="utf-8")):
                page.set_content(f"<!doctype html><meta charset='utf-8'><body>{RENDER[spec['type']](spec)}</body>")
                page.wait_for_timeout(100)
                png = page.locator("body > *:not(style)").first.screenshot()
                out = spec_path.parent / spec["file"]
                Image.open(io.BytesIO(png)).convert("RGB").save(out, "WEBP", quality=82, method=6)
                w, h = Image.open(out).size
                print(f"{out}  {w}x{h}  {out.stat().st_size // 1024}KB")
        browser.close()


if __name__ == "__main__":
    main(sys.argv[1:])
