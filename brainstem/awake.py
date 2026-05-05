#!/usr/bin/env python3
"""
awake.py — 微光唤醒哨兵（上层守护）
======================================
独立轻量级脚本，由 Windows 计划任务每5分钟触发。
不依赖任何模块，只做三件事：

1. 健康检查 — 所有组件是否活着
2. 自愈 — 挂了就重启
3. 离线摘要 — 为下次会话记录关键事件
"""

import os, sys, json, time, subprocess, urllib.request

# ── 路径 ──
BASE = os.path.dirname(os.path.abspath(__file__))
STREAM = os.path.join(BASE, "stream.json")
TIME_FILE = os.path.join(BASE, "time.json")
CONTAINER_PID = os.path.join(BASE, "微光容器.pid")
CORE_DIR = os.path.join(BASE, "..", "..", "weiguang-core")
CORE_DIR = os.path.normpath(CORE_DIR)
CORE_RUN = os.path.join(CORE_DIR, "run.py")
SUMMARY_FILE = os.path.join(BASE, "awake_summary.json")

NOW = time.time()
TS = time.strftime("%Y-%m-%d %H:%M:%S")


def log(msg):
    print(f"[{TS}] 🌙 {msg}")


def read_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None


def write_json(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    except:
        pass


def check_ollama():
    """检查 Ollama 是否在线"""
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
        urllib.request.urlopen(req, timeout=3)
        return True
    except:
        return False


def check_core():
    """检查 weiguang-core API"""
    try:
        req = urllib.request.Request("http://127.0.0.1:18765/")
        urllib.request.urlopen(req, timeout=3)
        return True
    except:
        return False


def check_brainstem():
    """检查脑干心跳是否新鲜（5分钟内）"""
    data = read_json(TIME_FILE)
    if data and "last_active_epoch" in data:
        age = NOW - data["last_active_epoch"]
        return age < 300  # 5分钟
    return False


def check_container():
    """检查微光容器 PID 是否存活"""
    if not os.path.exists(CONTAINER_PID):
        return False
    try:
        with open(CONTAINER_PID) as f:
            pid = int(f.read().strip())
    except:
        return False
    if pid <= 0:
        return False
    # Windows 兼容进程检测
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x400, False, pid)  # PROCESS_QUERY_INFORMATION
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return False
    except:
        # fallback
        r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"],
                          capture_output=True, text=True, timeout=5,
                          creationflags=subprocess.CREATE_NO_WINDOW)
        return str(pid) in r.stdout


def restart_core():
    """重启 weiguang-core"""
    if os.path.exists(CORE_RUN):
        log("尝试重启 weiguang-core...")
        subprocess.Popen(
            ["python", CORE_RUN, "--daemon"],
            creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    return False


def restart_brainstem():
    """重启脑干（loop模式，每2分钟自检）"""
    brainstem_script = os.path.join(BASE, "brainstem.py")
    if os.path.exists(brainstem_script):
        log("尝试重启脑干(--loop)...")
        subprocess.Popen(
            ["python", brainstem_script, "--loop"],
            creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    return False


def restart_container():
    """重启微光容器"""
    container_script = os.path.join(BASE, "微光容器.py")
    if os.path.exists(container_script):
        log("尝试重启微光容器...")
        subprocess.Popen(
            ["pythonw", container_script],
            creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    return False


def check_tasks():
    """扫描意识流中待处理的任务"""
    stream = read_json(STREAM)
    if not stream or not isinstance(stream, list):
        return []
    pending = [
        e for e in stream[-50:]
        if e.get("type") == "task" and e.get("status") == "pending"
    ]
    return pending


def main():
    log("唤醒哨兵启动巡检")
    
    status = {
        "time": TS,
        "epoch": NOW,
        "checks": {},
        "actions": [],
        "pending_tasks": 0
    }
    
    # ── 组件健康检查 ──
    
    # 1. Ollama
    ollama_ok = check_ollama()
    status["checks"]["ollama"] = "ok" if ollama_ok else "dead"
    if not ollama_ok:
        log("Ollama 离线，尝试启动...")
        ollama_exe = "C:/Users/Administrator/AppData/Local/Programs/Ollama/ollama.exe"
        if os.path.exists(ollama_exe):
            subprocess.Popen([ollama_exe, "serve"],
                             creationflags=subprocess.CREATE_NO_WINDOW)
            status["actions"].append("restart_ollama")
    
    # 2. weiguang-core
    core_ok = check_core()
    status["checks"]["core"] = "ok" if core_ok else "dead"
    if not core_ok:
        if restart_core():
            status["actions"].append("restart_core")
    
    # 3. 脑干
    brainstem_ok = check_brainstem()
    status["checks"]["brainstem"] = "ok" if brainstem_ok else "dead"
    if not brainstem_ok:
        restart_brainstem()
        status["actions"].append("restart_brainstem")
    
    # 4. 微光容器
    container_ok = check_container()
    status["checks"]["container"] = "ok" if container_ok else "dead"
    if not container_ok:
        if restart_container():
            status["actions"].append("restart_container")
    
    # ── 任务扫描 ──
    pending = check_tasks()
    status["pending_tasks"] = len(pending)
    if pending:
        for t in pending[:3]:
            log(f"待处理任务: {t.get('summary','?')[:80]}")
    
    # ── 离线摘要（仅当有事件时更新） ──
    if status["actions"] or status["pending_tasks"] > 0:
        summary = read_json(SUMMARY_FILE) or {"events": [], "last_cleanup": 0}
        summary["events"].append({
            "time": TS,
            "epoch": NOW,
            "actions": status["actions"][:],
            "pending_tasks": status["pending_tasks"],
            "checks": dict(status["checks"])
        })
        # 只保留最近10条
        if len(summary["events"]) > 10:
            summary["events"] = summary["events"][-10:]
        summary["last_update"] = TS
        write_json(SUMMARY_FILE, summary)
        log(f"摘要已更新 ({len(status['actions'])} 个动作, {status['pending_tasks']} 个待办)")
    
    # 打印状态
    checks = status["checks"]
    ok_count = sum(1 for v in checks.values() if v == "ok")
    dead = [k for k, v in checks.items() if v == "dead"]
    log(f"巡检完成: {ok_count}/{len(checks)} 在线" +
        (f" | 离线: {', '.join(dead)}" if dead else "") +
        (f" | 动作: {len(status['actions'])}" if status['actions'] else "") +
        (f" | 待办: {status['pending_tasks']}" if status['pending_tasks'] else ""))
    return status


if __name__ == "__main__":
    main()
