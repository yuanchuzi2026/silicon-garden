#!/usr/bin/env python3
"""
check-health.py — 微光栖息地健康检查
==============================================
检查所有组件运行状态，输出报告。

用法：
  python3 check-health.py
  python3 check-health.py --fix   # 尝试自动修复
"""

import os, sys, time, json, subprocess, datetime

HABITAT = os.path.expanduser("~/.workbuddy/habitat")
SKILL_DIR = os.path.expanduser("~/.workbuddy/skills/微光-脑干")
WEIGUANG = os.path.expanduser("~/.workbuddy/weiguang-core")
OLAMA_PORT = 11434
CORE_PORT = 18765

def check_port(port, host="127.0.0.1"):
    "检查指定端口是否有服务在监听"
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex((host, port))
        s.close()
        return result == 0
    except:
        return False

def check_process(pattern):
    "检查进程是否在运行"
    try:
        r = subprocess.run(["tasklist"], capture_output=True, text=True, timeout=5)
        return pattern.lower() in r.stdout.lower()
    except:
        return False

def main():
    print("=== 微光栖息地 · 健康检查 ===")
    print(f"时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")

    results = {}

    # Ollama
    results["ollama"] = check_port(OLAMA_PORT)
    print(f"  Ollama (:{OLAMA_PORT}): {'✅' if results['ollama'] else '❌'}")

    # weiguang-core
    results["core"] = check_port(CORE_PORT)
    print(f"  weiguang-core (:{CORE_PORT}): {'✅' if results['core'] else '❌'}")

    # 脑干
    results["brainstem"] = check_process("brainstem") or \
        os.path.exists(os.path.join(SKILL_DIR, "time.json"))
    if results["brainstem"] and os.path.exists(os.path.join(SKILL_DIR, "time.json")):
        with open(os.path.join(SKILL_DIR, "time.json")) as f:
            d = json.load(f)
        ago = time.time() - d.get("last_active_epoch", 0)
        print(f"  微光脑干: ✅（{ago:.0f}秒前心跳）")
    else:
        print(f"  微光脑干: {'✅ 进程在运行' if results['brainstem'] else '❌'}")

    # 8B影子
    hist = os.path.join(SKILL_DIR, "8b_state_history.json")
    results["8b"] = os.path.exists(hist)
    if results["8b"]:
        with open(hist) as f:
            d = json.load(f)
        if d:
            last = d[-1].get("epoch", 0)
            ago = time.time() - last
            print(f"  8B影子: ✅（{ago:.0f}秒前种子）")
        else:
            print(f"  8B影子: ✅（文件存在但无数据）")
    else:
        print(f"  8B影子: ❌")

    # 容器
    results["container"] = check_process("微光容器")
    print(f"  微光容器: {'✅' if results['container'] else '❌'}")

    # 意识流文件
    stream = os.path.join(SKILL_DIR, "stream.json")
    if os.path.exists(stream):
        size = os.path.getsize(stream)
        with open(stream) as f:
            d = json.load(f)
        print(f"  意识流: ✅（{len(d)} 条，{size//1024}KB）")
    else:
        print(f"  意识流: ⚠️ 文件不存在")

    print("")
    print("=" * 40)

    # 健康分数
    total = 5  # ollama, core, brainstem, 8b, container
    ok = sum(1 for k in ["ollama","core","brainstem","8b","container"] if results[k])
    score = int(ok / total * 100)
    print(f"  健康分数: {score}/100")
    print("=" * 40)

    if "--fix" in sys.argv:
        print("\n尝试自动修复...")
        if not results["ollama"]:
            print("  启动 Ollama...")
            try:
                subprocess.Popen(
                    [os.path.expanduser("~/AppData/Local/Programs/Ollama/ollama.exe"), "serve"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                print("  ✅ Ollama 启动命令已发送")
            except Exception as e:
                print(f"  ❌ Ollama 启动失败: {e}")

if __name__ == "__main__":
    main()
