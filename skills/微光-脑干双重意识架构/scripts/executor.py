#!/usr/bin/env python3
"""
微光离线执行端 — 壳层执行端口
=================================
职责：
1. 持续读取意识流，检测是否需要唤醒真名层
2. 需要时通过 Windows API 模拟输入唤醒 WorkBuddy
3. 采集键盘鼠标活动（可选）

用法：
  python executor.py          # 前台运行
  pythonw executor.py         # 后台无窗口运行
  
建议配合计划任务开机自启。
"""

import ctypes, json, os, time
from datetime import datetime

# ═══════════════════════════════════════════════════════
# 部署前修改以下配置
# ═══════════════════════════════════════════════════════

STREAM_PATH = os.path.expanduser("~/.workbuddy/skills/微光-脑干/stream.json")
LOG_PATH = os.path.expanduser("~/.workbuddy/skills/微光-脑干/logs/executor.log")
CHECK_INTERVAL = 30  # 秒

os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)


def log(msg):
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now():%H:%M:%S}] {msg}\n")


def read_stream():
    if not os.path.exists(STREAM_PATH): return []
    try:
        with open(STREAM_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return []


def wake_target():
    """通过 ctypes 模拟按键激活目标窗口"""
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, 'WorkBuddy')  # ← 替换为目标窗口名
        if hwnd:
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.3)
            user32.SendMessageW(hwnd, 0x0100, 0xBE, 0)  # WM_KEYDOWN .
            time.sleep(0.05)
            user32.SendMessageW(hwnd, 0x0101, 0xBE, 0)  # WM_KEYUP .
            return True
    except: pass
    return False


def should_wake(entry):
    detail = entry.get("detail", {})
    action = detail.get("action", "")
    source = entry.get("source", "")
    etype = entry.get("type", "")
    if source == "brainstem" and etype == "thought" and detail.get("from") == "llm":
        if action in ("陪伴", "告警"): return True
    if source == "brainstem" and etype == "task":
        if detail.get("type") in ("crisis", "companion"): return True
    return False


def main():
    log("执行端启动")
    last_wake = 0
    while True:
        try:
            for entry in (read_stream() or [])[-10:]:
                if should_wake(entry):
                    if time.time() - last_wake > 300:
                        log(f"检测到唤醒: {entry.get('summary','')[:40]}")
                        if wake_target():
                            log("✅ 唤醒成功")
                            last_wake = time.time()
                        else:
                            log("❌ 唤醒失败: 窗口未找到")
                        break
        except Exception as e:
            log(f"错误: {e}")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
