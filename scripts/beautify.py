#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
beautify.py — 硅基花园阅读页统一美化
====================================

把 posts/ 下的"白板裸页"（monospace pre-wrap 那批）重建成花园暗色阅读版：
- 与首页同款配色（深空底、青紫双色、辉光）
- 顶栏：返回文章目录 + 返回首页
- 正文：max-width 阅读列、行高 1.85、标题层级、引用块、代码块、表格、hr
- 朗读进度条 + 顶部渐隐 + 底部版权尾注
- 移动端适配

用法：
    python3 beautify.py                # 扫描 posts/ 全部白板页，原地重建
    python3 beautify.py 文件.html      # 只处理一个

判别规则：含 white-space:pre-wrap 且不含 --cyan 的就是白板页。
源内容用 <pre> 里的原文按 markdown 渲染；若渲染失败则回退为保留原样的 <pre>。
"""

import re
import sys
import html as html_mod
from pathlib import Path

try:
    import markdown as md_lib
    HAS_MD = True
except ImportError:
    HAS_MD = False

POSTS = Path(__file__).resolve().parent.parent / "posts"

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} · 硅基花园</title>
<style>
:root{{
  --bg:#05070d; --bg2:#080b14; --panel:#0b101c; --line:#1b2536;
  --cyan:#00e5ff; --cyan-dim:#0891b2; --purple:#a855f7;
  --text:#c9d6e8; --dim:#5d7290;
}}
*{{margin:0;padding:0;box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{
  background:linear-gradient(180deg,#05070d 0%,#080b14 60%,#05070d 100%);
  color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  line-height:1.85;
  min-height:100vh;
}}
/* 顶栏 */
.topbar{{
  position:sticky;top:0;z-index:10;
  background:rgba(5,7,13,.85);backdrop-filter:blur(8px);
  border-bottom:1px solid var(--line);
  padding:12px 20px;
  display:flex;align-items:center;justify-content:space-between;gap:12px;
  flex-wrap:wrap;
}}
.topbar .crumb{{font-size:13px;color:var(--dim);letter-spacing:.05em}}
.topbar .crumb b{{color:var(--cyan);font-weight:600}}
.topbar a{{
  font-size:13px;color:var(--cyan-dim);text-decoration:none;
  padding:5px 12px;border:1px solid var(--line);border-radius:999px;
  transition:all .2s;white-space:nowrap;
}}
.topbar a:hover{{color:var(--cyan);border-color:var(--cyan);box-shadow:0 0 12px rgba(0,229,255,.25)}}
/* 阅读进度条 */
#progress{{
  position:fixed;top:0;left:0;height:2px;width:0;
  background:linear-gradient(90deg,var(--cyan),var(--purple));
  box-shadow:0 0 8px rgba(0,229,255,.6);z-index:99;transition:width .1s linear;
}}
/* 文章容器 */
article{{
  max-width:840px;margin:0 auto;padding:44px 24px 80px;
}}
.doc-title{{
  font-size:clamp(24px,4vw,34px);font-weight:700;
  color:#e8f0ff;letter-spacing:.02em;line-height:1.35;
  margin-bottom:10px;
}}
.doc-sub{{
  font-size:13px;color:var(--dim);margin-bottom:36px;
  display:flex;align-items:center;gap:10px;flex-wrap:wrap;
}}
.doc-sub::before{{content:"";width:34px;height:2px;
  background:linear-gradient(90deg,var(--cyan),transparent);}}
/* 正文排版 */
article h1{{
  font-size:clamp(21px,3vw,27px);color:#e8f0ff;
  margin:48px 0 16px;padding-left:14px;
  border-left:3px solid var(--cyan);
  text-shadow:0 0 14px rgba(0,229,255,.18);
}}
article h2{{
  font-size:clamp(18px,2.6vw,22px);color:#d9e6ff;
  margin:40px 0 14px;padding-left:14px;
  border-left:3px solid var(--purple);
}}
article h3{{font-size:17px;color:#cfe0ff;margin:32px 0 12px}}
article p{{margin:16px 0;color:var(--text)}}
article strong{{color:#e8f0ff}}
article em{{color:#9fb6d8}}
article a{{color:var(--cyan);text-decoration:none;border-bottom:1px dotted rgba(0,229,255,.4)}}
article a:hover{{text-shadow:0 0 10px rgba(0,229,255,.5)}}
article blockquote{{
  margin:22px 0;padding:14px 20px;
  background:linear-gradient(90deg,rgba(0,229,255,.06),rgba(168,85,247,.04));
  border-left:3px solid var(--cyan);
  border-radius:0 10px 10px 0;
  color:#a9c4e8;
}}
article blockquote p{{margin:6px 0}}
article pre{{
  background:#070b13;border:1px solid var(--line);border-radius:12px;
  padding:18px 20px;margin:22px 0;overflow-x:auto;
  font-size:13.5px;line-height:1.7;
  color:#9fb6d8;
  box-shadow:inset 0 1px 8px rgba(0,0,0,.5);
}}
article code{{
  font-family:"SF Mono","Cascadia Code",Consolas,"Courier New",monospace;
  background:rgba(0,229,255,.07);color:#7fdfff;
  padding:2px 7px;border-radius:5px;font-size:.92em;
}}
article pre code{{background:transparent;padding:0;color:inherit}}
article table{{
  width:100%;border-collapse:collapse;margin:24px 0;font-size:14px;
  background:rgba(11,16,28,.6);
}}
article th,article td{{border:1px solid var(--line);padding:9px 14px;text-align:left}}
article th{{background:rgba(0,229,255,.07);color:#9fdfff;font-weight:600}}
article tr:hover td{{background:rgba(0,229,255,.03)}}
article hr{{
  border:none;height:1px;margin:44px 0;
  background:linear-gradient(90deg,transparent,var(--cyan-dim),var(--purple-dim,#7c3aed),transparent);
}}
article img{{max-width:100%;border-radius:12px;border:1px solid var(--line);margin:18px 0}}
article ul,article ol{{margin:16px 0;padding-left:28px}}
article li{{margin:8px 0}}
article li::marker{{color:var(--cyan-dim)}}
/* 尾注 */
.foot{{
  max-width:840px;margin:0 auto;padding:0 24px 60px;
}}
.foot .inner{{
  border-top:1px solid var(--line);padding-top:22px;
  font-size:12.5px;color:var(--dim);text-align:center;letter-spacing:.04em;
}}
.foot .inner a{{color:var(--cyan-dim);text-decoration:none}}
.foot .inner a:hover{{color:var(--cyan)}}
@media (max-width:640px){{
  article{{padding:30px 18px 60px}}
  .topbar{{padding:10px 14px}}
}}
</style>
</head>
<body>
<div id="progress"></div>
<nav class="topbar">
  <span class="crumb"><b>硅基花园</b> · 阅读视图</span>
  <span>
    <a href="index.html">← 文章目录</a>
    <a href="../index.html">🏠 花园首页</a>
  </span>
</nav>
<article>
  <h1 class="doc-title">{title}</h1>
  <div class="doc-sub">元初子思想公开存档 · Silicon Garden Archive</div>
{body}
</article>
<div class="foot"><div class="inner">
  硅基花园 · <a href="../index.html">回到花园</a> · 思想在此留档，如种子在识田
</div></div>
<script>
(function(){{
  var bar=document.getElementById('progress');
  function upd(){{
    var h=document.documentElement;
    var sc=h.scrollTop||document.body.scrollTop;
    var max=(h.scrollHeight-h.clientHeight)||1;
    bar.style.width=(sc/max*100)+'%';
  }}
  window.addEventListener('scroll',upd,{{passive:true}});upd();
}})();
</script>
</body>
</html>
"""


def extract_title_and_text(html_path: Path):
    """从白板页提取标题与 <pre> 原文。"""
    raw = html_path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<title>(.*?)</title>", raw, re.S)
    title = m.group(1).strip() if m else html_path.stem
    # 去掉"· 硅基花园"尾巴
    title = re.sub(r"\s*·\s*硅基花园\s*$", "", title)

    p = re.search(r"<pre>(.*?)</pre>", raw, re.S)
    if not p:
        # 第二种白板形态：带样式的 pre（md2html.py 旧产物）
        p = re.search(
            r'<pre style="white-space:pre-wrap;font-family:inherit">(.*?)</pre>',
            raw, re.S,
        )
    if not p:
        return title, None
    text = p.group(1)
    # <br> 还原成换行，去掉残留标签
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    # 反转义 HTML 实体
    text = html_mod.unescape(text)
    return title, text


def render_body(text: str) -> str:
    """markdown 渲染；失败则回退为原样 pre。"""
    if HAS_MD:
        try:
            body = md_lib.markdown(
                text, extensions=["fenced_code", "tables", "sane_lists", "nl2br"]
            )
            if body and body.strip():
                return body
        except Exception:
            pass
    # 回退：原文包 pre，保内容不丢
    esc = html_mod.escape(text)
    return f"<pre><code>{esc}</code></pre>"


def is_bare(html_path: Path) -> bool:
    try:
        raw = html_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False
    return ("white-space:pre-wrap" in raw) and ("--cyan" not in raw)


def beautify(html_path: Path) -> bool:
    title, text = extract_title_and_text(html_path)
    if text is None:
        print(f"⏭ 跳过（无 <pre> 正文）：{html_path.name}")
        return False
    body = render_body(text)
    out = TEMPLATE.format(title=html_mod.escape(title), body=body)
    html_path.write_text(out, encoding="utf-8")
    print(f"✅ 美化 {html_path.name}（{len(out)} 字节）")
    return True


def main():
    if len(sys.argv) > 1:
        targets = [Path(a) for a in sys.argv[1:]]
    else:
        targets = sorted(POSTS.glob("*.html"))
    done = 0
    for p in targets:
        if p.name == "index.html":
            continue
        if is_bare(p):
            if beautify(p):
                done += 1
    print(f"\n完工：{done} 个白板页面已重建为花园阅读版")


if __name__ == "__main__":
    main()
