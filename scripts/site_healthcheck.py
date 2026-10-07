#!/usr/bin/env python3
"""site_healthcheck.py — 硅基花园巡园体检（2026-10-08 巡园日固化的工具）

用法: python3 scripts/site_healthcheck.py
检查: ①posts区死链 ②posts区孤岛（无任何页面链入的正式帖子）③双格式断对（md有html无，且目录挂的是html链接）
不检查: 根目录历史地层（html/ blog/ frontend/ _vite-src/ baseplate/ remote-field/ wayback-index）——那是花园的老地层，保留原样
输出: 分区报告，退出码0=健康
"""
import re, os, glob, sys
from urllib.parse import unquote

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(ROOT)

SKIP = ('rss','llms','sitemap','404','html/','blog/','frontend/','_vite','baseplate',
        'remote-field','wayback','COGNITIONS','ECHO','WEIGUANG','MANIFESTO')
ENTRIES = {'index.html','posts/index.html','posts/ai/index.html','posts/诗/index.html',
           'posts/tech-radar/index.html','posts/杂谈/index.html','posts/skills/README.html'}

def main():
    all_html = set(glob.glob('**/*.html', recursive=True))
    dead, linked_by = [], {}
    for f in all_html:
        try: src = open(f, encoding='utf-8').read()
        except Exception: continue
        base = os.path.dirname(f)
        for href in re.findall(r'href="([^"]+\.html)"', src):
            if href.startswith(('http','#','/')): continue
            target = os.path.normpath(os.path.join(base, unquote(href)))
            if target in all_html: linked_by.setdefault(target, []).append(f)
            elif not os.path.exists(target): dead.append((f, href))

    ok = True
    print("=== ① posts区死链 ===")
    posts_dead = [d for d in dead if d[0].startswith('posts/') and not d[0].startswith(('posts/tech-radar/2026',))]
    for f, h in posts_dead: print(f"  ✗ {f} -> {h}")
    if not posts_dead: print("  ✓ 全清")
    else: ok = False

    print("=== ② posts区孤岛 ===")
    orphans = all_html - set(linked_by.keys()) - ENTRIES
    real = [o for o in sorted(orphans) if o.startswith('posts/') and not any(k in o for k in SKIP)]
    for o in real: print(f"  ✗ {o}")
    if not real: print("  ✓ 全清")
    else: ok = False

    print("=== ③ 双格式断对（md有html无） ===")
    all_md = set(glob.glob('posts/**/*.md', recursive=True))
    broken = [m for m in sorted(all_md) if (m[:-3]+'.html') not in all_html]
    for m in broken: print(f"  ✗ {m}")
    if not broken: print("  ✓ 全清")
    else: ok = False

    print("\n结论:", "花园健康 🌸" if ok else "有活要干 🔧")
    sys.exit(0 if ok else 1)

if __name__ == '__main__':
    main()
