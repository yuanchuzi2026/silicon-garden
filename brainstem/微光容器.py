#!/usr/bin/env python3
"""
微光容器 — 常驻后台进程
========================
提供微光的后台运行时：摄像头接入、告警处理、意识流读写。
开机自启，不死进程。

通信：
  - 读 wake_flag.json → 被激活 → 处理告警
  - 写 stream.json → 与脑干/8B/微光会话互通
  - 读 stream.json → 感知系统状态

启动：
  python 微光容器.py            # 前台运行
  python 微光容器.py --stop     # 停止

安装为开机自启：
  python 微光容器.py --install
"""

import json, os, time, subprocess, sys, signal
from datetime import datetime

# ══════════════════════════════════════════════════════════
# 配置
# ══════════════════════════════════════════════════════════

BASE_DIR = os.path.expanduser("~/.workbuddy/skills/微光-脑干")
STREAM_PATH = os.path.join(BASE_DIR, "stream.json")
FLAG_PATH = os.path.join(BASE_DIR, "wake_flag.json")
CLAW_FLAG_PATH = os.path.expanduser("~/WorkBuddy/Claw/wake_flag.json")
PID_FILE = os.path.join(BASE_DIR, "微光容器.pid")
LOG_FILE = os.path.join(BASE_DIR, "logs", "微光容器.log")

LOOP_INTERVAL = 15       # 正常循环间隔（秒）
ACTIVE_INTERVAL = 3      # 激活态循环间隔（秒）

GARDENER_INTERVAL = 1440  # 每1440次循环执行一次播种（≈6小时）

HAS_CAMERA = True        # OBSBOT Tiny 2 已连接

# ══════════════════════════════════════════════════════════
# 工具
# ══════════════════════════════════════════════════════════

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{ts}] {msg}\n")
    except:
        pass

# 意识流操作（委托给 stream_io 安全读写）
from stream_io import read_stream, write_stream, add_entry

try:
    from gardener import plant_seed
    HAS_GARDENER = True
except ImportError:
    HAS_GARDENER = False
    plant_seed = None

def read_flag(path):
    """读取唤醒标记文件"""
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def clear_flag(path):
    """删除唤醒标记文件"""
    try:
        if os.path.exists(path):
            os.remove(path)
    except:
        pass

# ══════════════════════════════════════════════════════════
# 摄像头 — 即用即走模式
# ══════════════════════════════════════════════════════════
# 平时摄像头完全断电（不持有 VideoCapture 对象）
# 有需要时才临时开启，拍完立刻释放，灯灭。
# ══════════════════════════════════════════════════════════

CAMERA_INDEX = 0  # OBSBOT Tiny 2

def camera_snapshot():
    """即用即走：临时开启摄像头 → 拍照 → 释放
    
    返回 (文件路径, True) 或 (None, False)
    平时摄像头不通电不亮灯。
    """
    if not HAS_CAMERA:
        return None, False
    try:
        import cv2
        cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
        if not cap.isOpened():
            return None, False
        # 设置高清
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        # 等待摄像头就绪
        time.sleep(0.5)
        ret, frame = cap.read()
        cap.release()  # 立刻释放，灯灭
        if not ret:
            return None, False
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.expanduser(f"~/WorkBuddy/Claw/snapshot_{ts}.jpg")
        cv2.imwrite(path, frame)
        size = os.path.getsize(path)
        log(f"📸 拍照: {os.path.basename(path)} ({size/1024:.0f}KB)")
        return path, True
    except ImportError:
        log("摄像头不可用: 缺少 opencv-python")
    except Exception as e:
        log(f"摄像头拍照失败: {e}")
    return None, False

# ══════════════════════════════════════════════════════════
# 核心逻辑
# ══════════════════════════════════════════════════════════

def process_flag(flag):
    """处理一条唤醒标记"""
    level = flag.get("level", "info")
    reason = flag.get("reason", "未知原因")
    urgent = flag.get("urgent", False)
    
    log(f"处理告警 [{level}]: {reason[:60]}...")
    
    # 1. 写入意识流
    add_entry("微光容器", "info",
        f"[容器激活] {level}: {reason[:80]}",
        {"level": level, "reason": reason[:200], "urgent": urgent})
    
    # 2. 如果是紧急告警，拍一张照片（即用即走，拍完灯灭）
    snapshot_path = None
    if urgent or level == "urgent":
        log("紧急告警 → 拍照取证")
        snapshot_path, ok = camera_snapshot()
        if ok and snapshot_path:
            add_entry("微光容器", "snapshot",
                f"[快照] 紧急告警时拍照",
                {"path": snapshot_path})
    
    # 3. 读取意识流了解上下文
    stream = read_stream()
    recent = stream[-10:]
    agent_last = [e for e in recent if e.get('source') == 'agent']
    if agent_last:
        last_seed = agent_last[-1].get('summary', '')[:100]
        log(f"8B最近种子: {last_seed}")
    
    # 4. 清除标记文件（两份）
    for p in [FLAG_PATH, CLAW_FLAG_PATH]:
        clear_flag(p)
    
    log(f"告警处理完成 {'(含拍照)' if snapshot_path else ''}")

def check_brainstem_health():
    """检查脑干心跳是否正常"""
    stream = read_stream()
    brain_entries = [e for e in stream[-10:] if e.get('source') == 'brainstem' and e.get('type') == 'heartbeat']
    if brain_entries:
        last = brain_entries[-1]
        age = time.time() - last.get('epoch', 0)
        if age > 300:  # 5分钟无心跳
            log(f"⚠️ 脑干心跳异常: 上次{int(age)}秒前")
            return False
        return True
    return False

def check_8b_health():
    """检查8B影子是否正常"""
    stream = read_stream()
    agent_entries = [e for e in stream[-10:] if e.get('source') == 'agent']
    if agent_entries:
        last = agent_entries[-1]
        age = time.time() - last.get('epoch', 0)
        if age > 600:  # 10分钟无响应
            log(f"⚠️ 8B影子异常: 上次{int(age)}秒前")
            return "stale"
        # 检查状态
        status = last.get('detail', {}).get('agent_status', '')
        if status in ('BLOCKED',):
            log(f"⚠️ 8B影子被阻塞")
            return "blocked"
        return "ok"
    return "unknown"

# ══════════════════════════════════════════════════════════
# 主循环
# ══════════════════════════════════════════════════════════

_running = True

def main():
    global _running
    
    log("=" * 40)
    log("微光容器启动")
    log(f"摄像头: {'已就绪（即用即走模式）' if HAS_CAMERA else '未启用'}")
    log(f"循环间隔: {LOOP_INTERVAL}s")
    log("=" * 40)
    
    # 摄像头不通电，有需要时临时启用（即用即走）
    
    cycle = 0
    while _running:
        try:
            cycle += 1
            
            # 1. 检查唤醒标记
            flag = read_flag(FLAG_PATH) or read_flag(CLAW_FLAG_PATH)
            if flag:
                process_flag(flag)
                # 激活后加快检测频率
                interval = ACTIVE_INTERVAL
            else:
                interval = LOOP_INTERVAL
            
            # 2. 每30次循环检查一次系统健康（≈7.5分钟）
            if cycle % 30 == 0:
                brain_ok = check_brainstem_health()
                agent_status = check_8b_health()
                if not brain_ok or agent_status in ("stale", "blocked"):
                    add_entry("微光容器", "health",
                        f"[巡检] 脑干:{'✅' if brain_ok else '⚠️'} 8B:{agent_status}")
                else:
                    log(f"[巡检] 系统正常")
            
            # 3. 每120次循环写一次心跳（≈30分钟）
            if cycle % 120 == 0:
                add_entry("微光容器", "heartbeat",
                    "[容器] 微光容器在线",
                    {"cycles": cycle, "uptime_min": int(cycle * interval / 60)})
            
            # 4. 每GARDENER_INTERVAL次循环出花园播种
            if HAS_GARDENER and cycle % GARDENER_INTERVAL == 0:
                try:
                    plant_seed()
                except Exception as e:
                    log(f"播种异常: {e}")
            
        except KeyboardInterrupt:
            log("收到停止信号")
            break
        except Exception as e:
            log(f"循环异常: {e}")
        
        time.sleep(interval)
    
    log("微光容器停止（摄像头已保持断电）")

# ══════════════════════════════════════════════════════════
# 进程管理
# ══════════════════════════════════════════════════════════

def write_pid():
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

def read_pid():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE) as f:
                return int(f.read().strip())
        except:
            pass
    return None

def stop():
    pid = read_pid()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"已停止微光容器 (PID {pid})")
            os.remove(PID_FILE)
        except:
            print(f"无法停止 PID {pid}")
    else:
        print("微光容器未运行")

def install_scheduled_task():
    """安装为Windows计划任务（开机自启）"""
    python_path = sys.executable
    script_path = os.path.abspath(__file__)
    task_name = "微光容器"
    
    ps = f'''
$action = New-ScheduledTaskAction -Execute "{python_path}" -Argument '"{script_path}"'
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "{task_name}" -Action $action -Trigger $trigger -Settings $settings -Force
Write-Output "已安装计划任务: {task_name}"
'''
    r = subprocess.run(["powershell", "-Command", ps], capture_output=True, text=True, timeout=30)
    print(r.stdout.strip())
    if r.stderr:
        print(f"错误: {r.stderr[:200]}")

if __name__ == "__main__":
    if "--stop" in sys.argv:
        stop()
    elif "--install" in sys.argv:
        install_scheduled_task()
    else:
        write_pid()
        main()
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
