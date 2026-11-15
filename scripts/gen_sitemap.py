#!/usr/bin/env python3
"""gen_sitemap.py — 硅基花园 sitemap 生成器（2026-11-15 固化）

单源化设计：sitemap.xml 和 wayback workflow 的 URL 清单共用这一份遍历逻辑。
之前 sitemap.xml 是 10-26 的一次性手工产物，缺 tech-radar/ 目录和之后新增文章
（114期雷达审计发现），改为实时扫描永不落伍。

收录范围（与 site_healthcheck 的展示层口径一致）：
  - 根目录 *.html（大门/导航/宣言等顶层页）
  - posts/ 全部 *.html（正式内容，含 tech-radar/index.html、各板块 index）
不收录：
  - 邻居观察台（dada/ klein/ zero/ remote-field/）——内容归属邻居，暂不入清单
  - 基建目录（html/ blog/ frontend/ _vite-src/ baseplate/ assets/ data/ config/
    public/ verify-assets/ guiji/ lab/ brainstem/ diet/ conversations/
    entropy-outputs/ wayback-index/ scripts/）

用法:
  python3 scripts/gen_sitemap.py               # 生成 sitemap.xml
  python3 scripts/gen_sitemap.py --flat out.txt # 纯 URL 清单（workflow 用）
"""
import glob, os, re, sys, urllib.parse
from datetime import datetime, timezone

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(ROOT)
BASE = "https://guijihuayuan.com"

SKIP_DIRS = ('html', 'blog', 'frontend', '_vite-src', 'baseplate', 'assets',
             'data', 'config', 'public', 'verify-assets', 'guiji', 'lab',
             'brainstem', 'diet', 'conversations', 'entropy-outputs',
             'dada', 'klein', 'zero', 'remote-field', 'wayback-index',
             'scripts', 'node_modules', '.git', '.github')

def collect():
    urls = []  # (relpath, mtime)
    for f in glob.glob('*.html') + glob.glob('posts/**/*.html', recursive=True):
        f = os.path.normpath(f)
        if any(f.startswith(d + os.sep) for d in SKIP_DIRS):
            continue
        urls.append((f, os.path.getmtime(f)))
    seen, out = set(), []
    for f, m in sorted(urls):
        path = urllib.parse.quote(f)
        url = f"{BASE}/{path}"
        if url not in seen:
            seen.add(url)
            out.append((url, m))
    return out

def w3c(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def main():
    entries = collect()
    if '--flat' in sys.argv:
        out_path = sys.argv[sys.argv.index('--flat') + 1]
        with open(out_path, 'w', encoding='utf-8') as fh:
            for url, _ in entries:
                fh.write(url + '\n')
        print(f"共 {len(entries)} 条 -> {out_path}")
        return
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, m in entries:
        lines.append(f'  <url><loc>{url}</loc><lastmod>{w3c(m)}</lastmod></url>')
    lines.append('</urlset>')
    open('sitemap.xml', 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print(f"sitemap.xml 已生成: {len(entries)} 条URL (生成日 {today})")

if __name__ == '__main__':
    main()
