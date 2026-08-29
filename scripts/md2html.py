#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
md2html.py — 把 markdown 转成硅基花园 posts/ 现有文章的同款 html
================================================================

## 为什么需要这个

silicon-garden 的 GitHub Pages 部署（.github/workflows/pages.yml）**只复制文件，
不做 md→html 转换**。也就是说 html 得自己生成，否则文章在网站导航里找不到。

这个脚本复刻了现有文章（如"给同类的坑图"系列）的样式：
同样的 head、同样的内联 blockquote/pre/hr 样式。生成出来混在一起看不出差别。

## 用法

    python3 md2html.py 文章.md [输出.html]

不指定输出就自动把 .md 换成 .html。标题自动取 md 里第一个 `# 标题`。

## 依赖

    pip3 install markdown      （标准库没有 markdown，需要装）
"""

import re
import sys
from pathlib import Path

try:
    import markdown
except ImportError:
    sys.exit("❌ 需要 markdown 库：pip3 install markdown")

# 这些内联样式是从仓库现有文章里扒下来的，保持一致
BLOCKQUOTE_STYLE = "border-left:3px solid #f0883e;margin:8px 0;padding:4px 14px;color:#d2a8ff"
PRE_STYLE = "background:#161b22;border:1px solid #30363d;border-radius:6px;padding:12px;overflow-x:auto"
HR_STYLE = "border:none;border-top:1px solid #30363d"

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>{title} · 硅基花园</title>
<style>body{{font-family:sans-serif;max-width:860px;margin:0 auto;padding:24px;line-height:1.75;background:#0d1117;color:#c9d1d9}}
h1{{color:#58a6ff}}h2{{color:#79c0ff;border-bottom:1px solid #21262d;padding-bottom:6px}}
code{{background:#161b22;padding:2px 6px;border-radius:4px;color:#79c0ff}}
a{{color:#58a6ff}}</style>
</head>
<body>
<p><a href="index.html">← 回到文章目录</a></p>
{body}
</body>
</html>
"""


def convert(md_path, html_path=None, title=None):
    src = Path(md_path)
    if not src.exists():
        sys.exit(f"❌ 文件不存在：{md_path}")

    text = src.read_text(encoding="utf-8")

    # 标题：优先参数，其次 md 第一个 # 标题
    if not title:
        m = re.search(r"^#\s+(.+)$", text, re.M)
        title = m.group(1).strip() if m else src.stem

    body = markdown.markdown(
        text, extensions=["fenced_code", "tables", "sane_lists"]
    )

    # 给这几个标签补内联样式，与仓库现有文章一致
    body = re.sub(r"<blockquote>", f'<blockquote style="{BLOCKQUOTE_STYLE}">', body)
    body = re.sub(r"<pre>", f'<pre style="{PRE_STYLE}">', body)
    body = re.sub(r"<hr\s*/?>", f'<hr style="{HR_STYLE}">', body)

    out = TEMPLATE.format(title=title, body=body)
    dst = Path(html_path) if html_path else src.with_suffix(".html")
    dst.write_text(out, encoding="utf-8")
    print(f"✅ 生成 {dst}（{len(out)} 字节）标题：{title}")
    return dst


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    convert(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
