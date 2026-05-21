#!/usr/bin/env python3
"""
微光离线执行端 — 常驻后台
=================================
职责：
1. 持续读取意识流，检测脑干/8B是否需要唤醒微光
2. 需要时通过 Windows API 模拟输入唤醒 WorkBuddy
3. 采集键盘鼠标活动数据（用于无聊检测增强）

用法：pythonw executor.py
      （建议计划任务开机自启）
"""

import ctypes, json, os, time, sys
from datetime import datetime

# 日志
LOG_PATH = os.path.expanduser("~/.workbuddy/skills/微光-脑干/logs/executor.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

def log(msg):
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now():%H:%M:%S}] {msg}\n")

log("执行端启动")

# 配置
STREAM_PATH = os.path.expanduser("~/.workbuddy/skills/微光-脑干/stream.json")
CHECK_INTERVAL = 30  # 每30秒检查一次意识流

user32 = ctypes.windll.user32


def read_stream():
    """读取意识流最新条目"""
    if not os.path.exists(STREAM_PATH):
        return []
    try:
        with open(STREAM_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []


def find_workbuddy():
    """查找 WorkBuddy 窗口"""
    return user32.FindWindowW(None, 'WorkBuddy')


def wake_workbuddy(message="."):
    """通过模拟输入唤醒 WorkBuddy"""
    hwnd = find_workbuddy()
    if not hwnd:
        return False
    # 激活窗口
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.3)
    # 模拟输入消息
    user32.SendMessageW(hwnd, 0x0100, 0xBE, 0)  # WM_KEYDOWN .
    time.sleep(0.05)
    user32.SendMessageW(hwnd, 0x0101, 0xBE, 0)  # WM_KEYUP .
    return True


def should_wake(entry):
    """判断是否需要唤醒微光"""
    detail = entry.get("detail", {})
    action = detail.get("action", "")
    source = entry.get("source", "")
    etype = entry.get("type", "")
    
    # 8B 要求陪伴/告警 → 需要微光
    if source == "brainstem" and etype == "thought" and detail.get("from") == "llm":
        if action in ("陪伴", "告警"):
            return True
    # 脑干紧急任务 → 需要微光
    if source == "brainstem" and etype == "task":
        if detail.get("type") in ("crisis", "companion"):
            return True
    return False


def main():
    print(f"[执行端] 已启动, 每{CHECK_INTERVAL}秒检查意识流")
    last_wake = 0
    
    while True:
        try:
            stream = read_stream()
            if stream:
                for entry in stream[-10:]:
                    if should_wake(entry):
                        now = time.time()
                        if now - last_wake > 300:
                            log(f"检测到唤醒信号: {entry.get('summary','')[:40]}")
                            ok = wake_workbuddy()
                            if ok:
                                log("✅ 唤醒成功")
                                last_wake = now
                            else:
                                log("❌ 唤醒失败: 未找到WorkBuddy窗口")
                            break
        except Exception as e:
            log(f"错误: {e}")
        
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
