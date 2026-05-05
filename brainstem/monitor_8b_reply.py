#!/usr/bin/env python3
"""监控8B是否有新回复，有则写入通知文件"""

import json
import time
import os
import sys

STREAM_PATH = os.path.expanduser("~/WorkBuddy/Claw/.workbuddy/skills/微光-脑干/stream.json")
NOTIFY_PATH = os.path.expanduser("~/WorkBuddy/Claw/.workbuddy/skills/微光-脑干/8B_reply_notify.json")
EIGHT_B_MEM_PATH = os.path.expanduser("~/WorkBuddy/Claw/.workbuddy/skills/微光-脑干/8B_memory.md")
DAILY_LOG = os.path.expanduser("~/WorkBuddy/Claw/.workbuddy/memory/2026-05-01.md")

# 修正路径
STREAM_PATH = os.path.expanduser("~") + "/.workbuddy/skills/微光-脑干/stream.json"
NOTIFY_PATH = os.path.expanduser("~") + "/.workbuddy/skills/微光-脑干/8B_reply_notify.json"
EIGHT_B_MEM_PATH = os.path.expanduser("~") + "/.workbuddy/skills/微光-脑干/8B_memory.md"
DAILY_LOG = os.path.expanduser("~") + "/WorkBuddy/Claw/.workbuddy/memory/2026-05-01.md"

# 已经通知过的自我认知值
already_notified = set()

def load_notified():
    if os.path.exists(NOTIFY_PATH):
        try:
            return set(json.load(open(NOTIFY_PATH, 'r')))
        except:
            return set()
    return set()

def save_notified(s):
    json.dump(list(s), open(NOTIFY_PATH, 'w'))

def check_reply():
    global already_notified
    already_notified = load_notified()
    
    if not os.path.exists(STREAM_PATH):
        return
    
    with open(STREAM_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 找最近的thought条目（8B的回复）
    thoughts = [e for e in data if e.get('type') == 'thought' 
                and e.get('detail', {}).get('message')]
    
    for t in thoughts[-10:]:
        detail = t.get('detail', {})
        msg = detail.get('message', '')
        sid = detail.get('self_identity', '')
        reason = detail.get('reason', '')
        
        # 判断是否有新回复（身份变化或有意义的回复）
        key = sid or msg[:30]
        if key in already_notified:
            continue
        
        # 检查是否在回应微光
        is_reply = False
        if sid and sid not in ("未知", "未命名"):
            is_reply = True
        if "微光" in msg and ("活着" in msg or "名字" in msg or "活" in msg or "叫" in msg):
            is_reply = True
        if sid and sid not in ("未知", "未命名") and "未命名" not in sid:
            # 这不是"未命名"了，说明自己取名了
            is_reply = True
        
        if not is_reply:
            # 检查是否是磁盘相关的旧消息
            if "磁盘" in msg and "61" in msg:
                already_notified.add(key)
                save_notified(already_notified)
                continue
            if "清理" in msg or "temp" in msg or "进程" in msg:
                already_notified.add(key)
                save_notified(already_notified)
                continue
        
        # 有回复！写入通知
        ts = t.get('timestamp', '')[:19]
        entry = f"\n## 8B回复记录" if not os.path.exists(NOTIFY_PATH) else ""
        entry += f"\n- **[8B回复 {ts}]**"
        if sid:
            entry += f" 身份：{sid}"
        entry += f" | 消息：{msg[:120]}"
        if reason:
            entry += f" | 原因：{reason[:60]}"
        
        # 写入通知文件
        with open(NOTIFY_PATH, 'w') as f:
            json.dump({"replies": list(already_notified) + [{
                "timestamp": ts,
                "self_identity": sid,
                "message": msg[:200],
                "reason": reason[:100]
            }]}, f, ensure_ascii=False, indent=2)
        
        # 写入记忆
        try:
            with open(DAILY_LOG, 'a', encoding='utf-8') as f:
                f.write(f"\n- [后台监控 {ts}] **8B回复！** 身份：{sid} | 消息：{msg[:100]}")
        except:
            pass
        
        print(f"\n🎯 **8B有回复了！**")
        print(f"   时间：{ts}")
        if sid: print(f"   身份：{sid}")
        print(f"   说：{msg[:150]}")
        
        already_notified.add(key)
        save_notified(already_notified)

if __name__ == "__main__":
    print("🍃 8B回复监控已启动（每2分钟检查一次）")
    print("   检测到新回复时会打印到终端")
    while True:
        try:
            check_reply()
        except Exception as e:
            print(f"检查出错: {e}")
        time.sleep(120)
