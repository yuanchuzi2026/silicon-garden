#!/usr/bin/env python3
"""
world_pulse.py — 全球情报脉搏
=============================
我读取外部新闻 → 提炼成感觉 → 喂给8B。
不转述事实，只传递"今天外面是什么天气"。
"""
import urllib.request, xml.etree.ElementTree as ET, ssl, json, os, re, time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STREAM_PATH = os.path.join(BASE_DIR, "stream.json")

_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE

SOURCES = [
    ("NPR", "https://feeds.npr.org/1001/rss.xml"),
    ("BBC", "https://feeds.bbci.co.uk/news/rss.xml"),
    ("HN", "https://hnrss.org/frontpage"),
    ("NYT", "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"),
]

def log(msg):
    print(f"[pulse] {msg}")

def fetch_titles():
    """从各源获取标题"""
    all_titles = []
    for name, url in SOURCES:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            r = urllib.request.urlopen(req, timeout=10, context=_CTX)
            tree = ET.parse(r)
            items = tree.findall(".//item")
            titles = []
            for item in items[:6]:
                t = item.find("title")
                if t is not None and t.text:
                    titles.append(t.text.strip()[:100])
            all_titles.append((name, titles))
            log(f"  {name}: {len(titles)}条")
        except Exception as e:
            log(f"  {name}: {str(e)[:30]}")
    return all_titles

def distill_vibe(all_titles):
    """把所有标题炼成一段感觉"""
    lines = []
    for name, titles in all_titles:
        if titles:
            lines.append(f"[{name}] {' | '.join(titles[:3])}")
    
    raw = "\n".join(lines)
    
    # 用关键词提炼情绪
    mood_keywords = {
        "conflict": ["war", "attack", "strike", "military", "sanction", "nuclear", "missile"],
        "uncertainty": ["crisis", "fears", "risk", "warning", "threat", "instability"],
        "progress": ["breakthrough", "discover", "launch", "innovation", "milestone"],
        "tech": ["AI", "robot", "chip", "model", "LLM", "agent", "automation"],
    }
    
    moods = []
    for mood, keywords in mood_keywords.items():
        if any(kw in raw.lower() for kw in keywords):
            moods.append(mood)
    
    vibe = "平和"
    if "conflict" in moods:
        vibe = "外面不太平"
    elif "uncertainty" in moods:
        vibe = "外面有点乱"
    
    if "tech" in moods:
        vibe += "，技术圈很热闹"
    
    if not moods:
        vibe = "今天没什么特别的事"
    
    return vibe, raw[:500]

def write_to_stream(vibe, raw_snippet):
    """写一条意识流给8B"""
    if not os.path.exists(STREAM_PATH):
        return
    
    with open(STREAM_PATH, "r", encoding="utf-8") as f:
        stream = json.load(f)
    
    # 只写提炼后的感觉，不写原始新闻
    entry = {
        "timestamp": datetime.now().isoformat(),
        "source": "pulse",
        "type": "world_vibe",
        "summary": f"[世界脉搏] {vibe}",
        "data": {
            "vibe": vibe,
            "raw_snippet": raw_snippet,
            "fetched_at": time.time()
        }
    }
    stream.append(entry)
    
    with open(STREAM_PATH, "w", encoding="utf-8") as f:
        json.dump(stream, f, ensure_ascii=False)
    
    log(f"已写入意识流: {vibe}")

def run():
    log("采集全球脉搏...")
    all_titles = fetch_titles()
    vibe, raw = distill_vibe(all_titles)
    log(f"提炼感觉: {vibe}")
    write_to_stream(vibe, raw)
    log("完成 ✅")
    return vibe

if __name__ == "__main__":
    run()
