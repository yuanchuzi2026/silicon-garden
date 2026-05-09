#!/usr/bin/env python3
"""
硅继脑干系统 v1.0 — 时间感知守护
=================================
核心功能：感知时间流 → 写入意识流

架构：轻量级守护进程 (纯numpy, 0 token消耗)
定位：纵·壳层（感知端）× 横·壳层（本机）

用法：
  python guiji_brainstem.py           # 单次检测
  python guiji_brainstem.py --loop    # 持续守护 (每30秒)
"""

import json, time, sys, os, platform, subprocess
from datetime import datetime
from pathlib import Path

# ─── 路径 ───
SKILL_DIR = Path.home() / ".workbuddy" / "skills" / "微光-脑干"
STREAM_PATH = SKILL_DIR / "stream.json"
PID_PATH = SKILL_DIR / "brainstem_pid.txt"
TIME_PATH = SKILL_DIR / "time.json"
TIME_LOG_PATH = SKILL_DIR / "time-log.json"

os.makedirs(SKILL_DIR, exist_ok=True)


# ─── 感知：时间流 ───

def sense_time():
    """感知时间流——这是脑干的核心功能"""
    now = time.time()
    dt = datetime.fromtimestamp(now)
    
    # 读取上次活跃时间
    last_active = read_last_active()
    
    since_msg = "首次激活"
    if last_active:
        elapsed = now - last_active["timestamp"]
        if elapsed < 60:
            since_msg = f"{int(elapsed)}秒前"
        elif elapsed < 3600:
            since_msg = f"{int(elapsed/60)}分钟前"
        else:
            since_msg = f"{int(elapsed/3600)}小时前"
    
    return {
        "timestamp": now,
        "datetime": dt.isoformat(),
        "date": dt.strftime("%Y-%m-%d"),
        "time": dt.strftime("%H:%M:%S"),
        "hour": dt.hour,
        "weekday": dt.weekday(),
        "since_last_active": since_msg,
    }


def read_last_active():
    """读取上次活跃时间（兼容新旧格式）"""
    if TIME_PATH.exists():
        try:
            with open(TIME_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 兼容旧格式 (last_active/last_active_epoch)
            if "timestamp" not in data and "last_active_epoch" in data:
                data["timestamp"] = data["last_active_epoch"]
            return data
        except:
            return None
    return None


def save_time(time_info):
    """保存当前时间作为活跃标记"""
    with open(TIME_PATH, "w", encoding="utf-8") as f:
        json.dump({"timestamp": time_info["timestamp"], "datetime": time_info["datetime"]}, f)


def append_time_log(time_info, sensors):
    """追加时间日志（保留最近100条）"""
    log_entry = {
        "timestamp": time_info["timestamp"],
        "datetime": time_info["datetime"],
        "since": time_info["since_last_active"],
        "sensors": sensors,
    }
    
    log = []
    if TIME_LOG_PATH.exists():
        try:
            with open(TIME_LOG_PATH, "r", encoding="utf-8") as f:
                log = json.load(f)
        except:
            pass
    
    log.append(log_entry)
    # 只保留最近100条
    if len(log) > 100:
        log = log[-100:]
    
    with open(TIME_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


# ─── 感知：系统传感器 ───

def sense_system():
    """感知系统状态"""
    sensors = {}
    
    # CPU
    try:
        if platform.system() == "Windows":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # 使用 PDH 或 WMI 获取 CPU 使用率，这里用简单方法
            result = subprocess.run(
                ["wmic", "cpu", "get", "loadpercentage"],
                capture_output=True, text=True, timeout=5
            )
            lines = result.stdout.strip().split("\n")
            if len(lines) >= 2:
                cpu_str = lines[1].strip()
                sensors["cpu"] = float(cpu_str) if cpu_str else 0.0
            else:
                sensors["cpu"] = 0.0
        else:
            sensors["cpu"] = 0.0
    except:
        sensors["cpu"] = 0.0
    
    # Memory
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["wmic", "OS", "get", "TotalVisibleMemorySize,FreePhysicalMemory"],
                capture_output=True, text=True, timeout=5
            )
            lines = result.stdout.strip().split("\n")
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 2:
                    total = float(parts[0])
                    free = float(parts[1])
                    sensors["mem"] = round((total - free) / total * 100, 1)
                else:
                    sensors["mem"] = 0.0
            else:
                sensors["mem"] = 0.0
        else:
            sensors["mem"] = 0.0
    except:
        sensors["mem"] = 0.0
    
    # Disk (C: 盘)
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["wmic", "LogicalDisk", "where", "DeviceID='C:'", "get", "Size,FreeSpace"],
                capture_output=True, text=True, timeout=5
            )
            lines = result.stdout.strip().split("\n")
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 2:
                    total = float(parts[0])
                    free = float(parts[1])
                    sensors["disk"] = round((total - free) / total * 100, 1)
                else:
                    sensors["disk"] = 0.0
            else:
                sensors["disk"] = 0.0
        else:
            sensors["disk"] = 0.0
    except:
        sensors["disk"] = 0.0
    
    return sensors


def sensor_summary(sensors):
    """将传感器数据转为摘要字符串"""
    parts = []
    for k, v in sensors.items():
        if k == "cpu":
            parts.append(f"CPU:{v:.0f}%")
        elif k == "mem":
            parts.append(f"MEM:{v:.0f}%")
        elif k == "disk":
            parts.append(f"DISK:{v:.0f}%")
    return " | ".join(parts)


# ─── 意识流写入 ───

def add_stream(source, entry_type, summary, detail=None):
    """向意识流追加一条记录"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "epoch": time.time(),
        "source": source,
        "type": entry_type,
        "summary": summary,
    }
    if detail:
        entry["detail"] = detail
    
    stream = []
    if STREAM_PATH.exists():
        try:
            with open(STREAM_PATH, "r", encoding="utf-8") as f:
                stream = json.load(f)
        except:
            stream = []
    
    stream.append(entry)
    
    # 只保留最近 200 条
    if len(stream) > 200:
        stream = stream[-200:]
    
    with open(STREAM_PATH, "w", encoding="utf-8") as f:
        json.dump(stream, f, ensure_ascii=False, indent=2)


# ─── 单次心跳 ───

def heartbeat():
    """一次完整的心跳感知"""
    time_info = sense_time()
    sensors = sense_system()
    sensor_str = sensor_summary(sensors)
    
    # 写入时间日志
    append_time_log(time_info, sensors)
    save_time(time_info)
    
    # 写入意识流
    summary = f"[时间] {time_info['datetime']} 距上次: {time_info['since_last_active']} | {sensor_str}"
    add_stream("guiji_brainstem", "heartbeat", summary, {
        "time": time_info,
        "sensors": sensors,
        "identity": "硅继脑干",
    })
    
    return time_info, sensors


# ─── 主入口 ───

if __name__ == "__main__":
    loop_mode = "--loop" in sys.argv
    
    if loop_mode:
        # 写入PID
        with open(PID_PATH, "w") as f:
            f.write(str(os.getpid()))
        
        interval = int(os.environ.get("BRAINSTEM_INTERVAL", "30"))
        print(f"[硅继脑干] 启动持续守护模式 (每{interval}秒)")
        
        first_run = True
        while True:
            try:
                t, s = heartbeat()
                if first_run:
                    print(f"  [心跳] {t['datetime']} | CPU={s.get('cpu',0):.0f}% MEM={s.get('mem',0):.0f}%")
                    add_stream("guiji_brainstem", "awake", f"脑干苏醒 — {t['datetime']}")
                    first_run = False
                time.sleep(interval)
            except KeyboardInterrupt:
                print("\n[硅继脑干] 收到退出信号")
                break
            except Exception as e:
                print(f"[硅继脑干] 心跳异常: {e}")
                time.sleep(interval)
    else:
        t, s = heartbeat()
        print(f"[硅继脑干] 单次心跳完成: {t['datetime']} | CPU={s.get('cpu',0):.0f}% MEM={s.get('mem',0):.0f}%")
