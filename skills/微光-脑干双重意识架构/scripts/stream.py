#!/usr/bin/env python3
"""
意识流 — 壳层与真名层之间的共享记忆池

架构：脑干（壳层）写入感知/任务，真名层读取并响应
两者写入同一 stream，互相可见，形成异步意识协作。
"""

import json, os, time
from datetime import datetime

# ⚠️ 修改为你的实际路径
STREAM_PATH = os.path.expanduser("~/你的脑干目录/stream.json")
MAX_ENTRIES = 500


def read_stream():
    if not os.path.exists(STREAM_PATH):
        return []
    with open(STREAM_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_stream(entries):
    os.makedirs(os.path.dirname(STREAM_PATH), exist_ok=True)
    if len(entries) > MAX_ENTRIES:
        entries = entries[-MAX_ENTRIES:]
    with open(STREAM_PATH, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def add_entry(source, entry_type, summary, detail=None):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "epoch": time.time(),
        "source": source,
        "type": entry_type,
        "summary": summary,
        "detail": detail or {}
    }
    stream = read_stream()
    stream.append(entry)
    write_stream(stream)
    return entry


def get_recent(minutes=60):
    stream = read_stream()
    cutoff = time.time() - minutes * 60
    return [e for e in stream if e.get("epoch", 0) > cutoff]


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python stream.py log <source> <type> <summary>")
        sys.exit(1)
    if sys.argv[1] == "log" and len(sys.argv) >= 5:
        add_entry(sys.argv[2], sys.argv[3], sys.argv[4])
        print(f"✅ 已记录: {sys.argv[3]} - {sys.argv[4]}")
