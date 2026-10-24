#!/usr/bin/env python3
"""按 CLAUDE.md 第一节的硬性要求检查文章（完整版）。

用法：python3 tools/check_article.py articles/xxx.md [...]
有不合格项时退出码为 1。
"""
import re
import sys
from pathlib import Path


def check(path: Path):
    text = path.read_text(encoding="utf-8")
    body = text.split("## 参考资料")[0]
    refs = text.split("## 参考资料")[1].split("## 相关阅读")[0] if "## 参考资料" in text else ""
    images = re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", text)
    internal = re.findall(r"\]\(([a-z0-9-]+\.md)\)", body)
    faq = text.split("## 常见问题\n")[1].split("\n## ")[0] if "## 常见问题\n" in text else ""
    title = text.splitlines()[0].lstrip("# ")
    # 搜索结果标题按显示宽度截断：汉字和全角标点算 1，英文数字和空格算 0.5
    width = sum(0.5 if ord(c) < 128 else 1 for c in title)
    sources = set(re.findall(r"\]\((https?://[^)]+)\)", refs))

    problems = []
    if len(images) < 3:
        problems.append(f"配图 {len(images)} 张，少于 3 张")
    for alt, src in images:
        if len(alt) < 8:
            problems.append(f"图片 alt 太短：{src}")
        if not (path.parent / src).exists():
            problems.append(f"图片不存在：{src}")
    if len(sources) < 3:
        problems.append("参考资料外部来源少于 3 条")
    if len(set(internal)) < 3:
        problems.append(f"正文站内互链 {len(set(internal))} 处，少于 3 处")
    for target in set(re.findall(r"\]\(([a-z0-9-]+\.md)\)", text)):
        if not (path.parent / target).exists():
            problems.append(f"站内链接失效：{target}")
    if faq.count("**") // 2 < 3:
        problems.append("常见问题少于 3 个")
    if not re.search(r"作者：.+最后更新：\d{4}-\d{2}-\d{2}", text):
        problems.append("缺少作者与最后更新日期")
    desc = re.search(r"<!-- description: (.+?) -->", text)
    if not desc:
        problems.append("缺少 <!-- description: ... --> SEO 描述")
    elif not 50 <= len(desc.group(1)) <= 130:
        problems.append(f"SEO 描述 {len(desc.group(1))} 字符，建议中文 70～80 字")
    if "**简短回答**" not in text:
        problems.append("开头缺少简短回答")
    if width > 36:
        problems.append(f"标题显示宽度 {width:g}，超过 36（约 36 个汉字宽），搜索结果里会被截断")

    status = "✅" if not problems else "❌"
    print(f"{status} {path.name}：图 {len(images)} · 来源 {len(sources)} · "
          f"互链 {len(set(internal))} · FAQ {faq.count('**') // 2} · 标题宽度 {width:g}")
    for p in problems:
        print(f"    - {p}")
    return not problems


if __name__ == "__main__":
    ok = all([check(Path(p)) for p in sys.argv[1:]])
    sys.exit(0 if ok else 1)
