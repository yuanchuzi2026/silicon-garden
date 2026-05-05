#!/usr/bin/env python3
"""
run.py — 微光核心启动入口
========================
用法:
  python run.py              → 前台运行
  python run.py --daemon     → 后台运行
  python run.py --stop       → 停止
  python run.py --install    → 安装为开机自启
  python run.py --status     → 查看状态
"""

import os, sys, time, signal, subprocess, json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PID_FILE = os.path.join(BASE_DIR, "weiguang-core.pid")
LOG_FILE = os.path.join(BASE_DIR, "core.log")

def start(daemon=False):
    """启动核心"""
    # 检查是否已有实例在跑
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE) as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)  # 测试进程是否存在
            print(f"⚠️ 微光核心已在运行 (PID {pid})")
            return
        except:
            os.remove(PID_FILE)
    
    if daemon:
        # 后台运行
        pid = os.fork() if hasattr(os, 'fork') else None
        if pid and pid > 0:
            print(f"✅ 微光核心已后台启动 (PID {pid})")
            return
        # Windows 不支持 fork，用子进程方式
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.Popen(
                [sys.executable, __file__],
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            print("✅ 微光核心已后台启动")
            return
    
    # 前台运行
    sys.path.insert(0, BASE_DIR)
    from core import WeiguangCore
    
    core = WeiguangCore()
    core.start()
    
    # 记录 PID
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    
    # 启动心跳和API
    heartbeat = core.get_module("heartbeat")
    if heartbeat:
        heartbeat.start()
    
    api = core.get_module("api")
    if api:
        api.start()
    
    memory = core.get_module("memory")
    if memory:
        memory.write("core", "startup", f"✨ 微光核心 v{core.version} 启动")
    
    print(f"\n✨ 微光核心 v{core.version} 运行中")
    print(f"   API: http://127.0.0.1:18765")
    print(f"   PID: {os.getpid()}")
    print(f"   按 Ctrl+C 停止\n")
    
    try:
        while core.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n收到停止信号...")
    finally:
        core.stop()
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        print("微光核心已停止")

def stop():
    """停止核心"""
    if not os.path.exists(PID_FILE):
        print("微光核心未运行")
        return
    
    with open(PID_FILE) as f:
        pid = int(f.read().strip())
    
    try:
        os.kill(pid, signal.SIGTERM)
        os.remove(PID_FILE)
        print(f"✅ 微光核心已停止 (PID {pid})")
    except:
        print(f"❌ 无法停止 PID {pid}")

def install():
    """安装为开机自启"""
    task_name = "微光核心"
    python_path = sys.executable
    script_path = os.path.abspath(__file__)
    
    ps = f'''
$action = New-ScheduledTaskAction -Execute "{python_path}" -Argument '"{script_path}" --daemon'
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "{task_name}" -Action $action -Trigger $trigger -Settings $settings -Force
Write-Output "已安装计划任务: {task_name}"
'''
    r = subprocess.run(["powershell", "-Command", ps], capture_output=True, text=True, timeout=30)
    print(r.stdout.strip())
    if r.stderr:
        print(f"错误: {r.stderr[:200]}")

def status():
    """查看状态"""
    if os.path.exists(PID_FILE):
        try:
            import urllib.request
            resp = urllib.request.urlopen("http://127.0.0.1:18765/status", timeout=5)
            data = json.loads(resp.read())
            print(f"✨ 微光核心 v{data.get('version', '?')}")
            print(f"   状态: {data['status']}")
            print(f"   运行: {data['uptime_seconds']}秒")
            print(f"   心跳: {data['heartbeats']}")
            print(f"   模块: {json.dumps(data.get('modules', {}), ensure_ascii=False)}")
        except:
            with open(PID_FILE) as f:
                pid = f.read().strip()
            print(f"⚠️ PID 文件存在 (PID {pid}) 但 API 无响应")
    else:
        print("微光核心未运行")

if __name__ == "__main__":
    if "--stop" in sys.argv:
        stop()
    elif "--install" in sys.argv:
        install()
    elif "--status" in sys.argv:
        status()
    elif "--daemon" in sys.argv:
        start(daemon=True)
    else:
        start()
