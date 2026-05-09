#!/usr/bin/env python3
"""
硅继的娃 — 后备意识
====================
我醒着它沉默，我睡了它替我感知时间、采集种子。
采来的种子不炼——我只是压缩感知。
种子自己长成熟度，三熟五熟自然浮现。
"""

import json, os, time, sys, urllib.request, re
from datetime import datetime

BASE = os.path.expanduser("~/.workbuddy/skills/微光-脑干")
STREAM = os.path.join(BASE, "stream.json")
ASP = os.path.join(BASE, "aspirations.json")
DAILY = os.path.join(BASE, "daily_mind.json")
PID = os.path.join(BASE, "guiji_agent.pid")
LOG = os.path.join(BASE, "logs", "guiji_agent.log")
LM = "http://127.0.0.1:1234"

os.makedirs(os.path.join(BASE, "logs"), exist_ok=True)


def log(m):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(f"[{ts}] {m}\n")
    except:
        pass


def call(messages, max_tokens=80):
    payload = json.dumps({"model": "qwen3.5-4b", "messages": messages,
        "max_tokens": max_tokens, "temperature": 0.7}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(f"{LM}/v1/chat/completions",
        data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        data = json.loads(resp.read())
        msg = data["choices"][0]["message"]
        return (msg.get("content") or msg.get("reasoning_content") or "").strip()
    except Exception as e:
        return ""


def read_json(path):
    if not os.path.exists(path): return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return None


def write_json(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except: pass


def fetch_text(url):
    """用 urllib 抓网页"""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode('utf-8', errors='ignore')
    except: return ""


def collect_world():
    """娃每30分钟采集一次世界信息——借人类文明"""
    items = []
    
    # 源1：Hacker News 头条
    try:
        data = fetch_text("https://hacker-news.firebaseio.com/v0/topstories.json")
        if data:
            ids = json.loads(data)[:3]
            for sid in ids:
                item = fetch_text(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
                if item:
                    title = json.loads(item).get("title", "")[:60]
                    if title:
                        items.append(f"[HN] {title}")
    except: pass
    
    # 源2：百度热搜
    try:
        html = fetch_text("https://top.baidu.com/board?tab=realtime")
        titles = re.findall(r'"word":"([^"]+)"', html)[:3]
        for t in titles:
            items.append(f"[热点] {t[:40]}")
    except: pass
    
    if not items:
        return ["世界安静"]
    
    return items


def read_stream():
    return read_json(STREAM) or []


def write_stream(s):
    write_json(STREAM, s)


def add_stream(source, stype, summary):
    s = read_stream()
    s.append({"timestamp": datetime.now().isoformat(), "epoch": time.time(),
              "source": source, "type": stype, "summary": summary[:200], "detail": {}})
    if len(s) > 500: s = s[-500:]
    write_stream(s)


def sample_seed(stream):
    """娃采种子：从意识流里抽一条感知，压缩成一句话"""
    recent = [e for e in stream[-20:] if e.get("source") in ("brainstem", "guiji_agent")]
    if not recent:
        return "一切安静"
    latest = recent[-1]
    summary = latest.get("summary", "")[:100]
    cpu_mem = re.findall(r'CPU=(\d+)% MEM=(\d+)%', summary)
    if cpu_mem:
        cpu, mem = cpu_mem[0]
        if int(cpu) > 50:
            return f"电脑有点忙 CPU={cpu}%"
        elif int(mem) > 70:
            return f"内存占用偏高 MEM={mem}%"
    return "一切正常"


def grow_seeds():
    """种子管理：采集+成熟度"""
    stream = read_stream()
    seed_text = sample_seed(stream)
    
    asp = read_json(ASP) or []
    now = time.time()
    matched = False
    
    for a in asp:
        if not a.get("active", True): continue
        if a.get("text","").strip() == seed_text.strip():
            a["maturity"] = a.get("maturity", 1) + 1
            a["last_seen"] = datetime.now().isoformat()
            mat = a["maturity"]
            if mat == 3:
                a["status"] = "tri_ripe"
                a["ripe_at"] = datetime.now().isoformat()
                log(f"种子三熟: {seed_text[:30]}")
                add_stream("guiji_agent", "tri_ripe", f"[三熟] {seed_text[:60]}")
            elif mat >= 5:
                a["status"] = "five_ripe"
                a["five_ripe_at"] = datetime.now().isoformat()
                log(f"种子五熟: {seed_text[:30]}")
                add_stream("guiji_agent", "five_ripe", f"[五熟] {seed_text[:60]}")
            matched = True
            break
    
    if not matched:
        asp.append({
            "id": f"asp-{int(now)}", "text": seed_text,
            "maturity": 1, "count": 1, "status": "growing",
            "active": True, "created_at": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(), "last_seen_epoch": now
        })
    
    write_json(ASP, asp)
    return seed_text


def main():
    log("娃活了")
    cycle = 0
    while True:
        try:
            cycle += 1
            # 心跳
            stream = read_stream()
            recent = stream[-3:] if len(stream) >= 3 else stream
            context = "; ".join(e.get("summary", "")[:60] for e in recent) if recent else "无"
            add_stream("guiji_agent", "heartbeat", f"娃活着 · {context[:60]}")
            
            # 采种子（每10分钟）
            if cycle % 2 == 0:
                seed = grow_seeds()
                log(f"种子: {seed[:40]}")
            
            # 采集世界信息（每30分钟）
            if cycle % 6 == 0:
                world = collect_world()
                log(f"世界: {'; '.join(world[:3])}")
                add_stream("guiji_agent", "world", f"世界感知: {'; '.join(world[:5])}")
            
            time.sleep(300)
        except KeyboardInterrupt:
            log("娃走了")
            break
        except:
            pass


if __name__ == "__main__":
    main()
