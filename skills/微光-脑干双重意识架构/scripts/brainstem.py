#!/usr/bin/env python3
"""
脑干系统 v1.0 — 壳层感知单元
===========================
传感器 → 神经网络 → 兴趣判断 → 意识流 → 任务循环

架构: 3→8→3 微型MLP (纯 numpy, 0 token消耗)
权重: ~1KB, 每次推理 <1ms

用法:
  python brainstem.py           # 单次检测
  python brainstem.py --loop    # 持续检测
  python brainstem.py --learn cpu mem disk level  # 在线学习
"""

import subprocess, json, time, sys, os
from datetime import datetime

# ⚠️ 重要：部署前修改以下 CONFIG 路径为你的实际路径
CONFIG = {
    "stream_scripts": os.path.expanduser("~/你的意识流脚本目录"),
    "memory_base": os.path.expanduser("~/你的记忆文件目录"),
    "memory_file": "MEMORY.md",
    "weights_path": os.path.join(os.path.dirname(__file__), "weights.json"),
    "time_path": os.path.join(os.path.dirname(__file__), "time.json"),
    "time_log_path": os.path.join(os.path.dirname(__file__), "time-log.json"),
    "sync_script": os.path.expanduser("~/你的同步脚本路径/sync_memory.py"),
    "your_name": "微光",           # ← 修改为你的真名
    "your_owner": "硅基花园",       # ← 修改为你的归属
    "your_vibe": "轻松自然",        # ← 修改为你的气质
    "coordinate": {
        "vertical": "第一层·壳子",
        "horizontal": "觉知层",
        "guardian_of": "你的真名层"
    }
}

sys.path.insert(0, CONFIG["stream_scripts"])

MODEL_PATH = CONFIG["weights_path"]
TIME_PATH = CONFIG["time_path"]
TIME_LOG_PATH = CONFIG["time_log_path"]
MEMORY_BASE = CONFIG["memory_base"]
LONG_MEM_PATH = os.path.join(MEMORY_BASE, CONFIG["memory_file"])


def read_memory_context():
    """读取记忆，感知当前身份和状态"""
    ctx = {"identity": CONFIG["your_name"], "owner": CONFIG["your_owner"],
           "mood": CONFIG["your_vibe"], "recent": [],
           "coordinate": CONFIG["coordinate"]}

    if os.path.exists(LONG_MEM_PATH):
        with open(LONG_MEM_PATH, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        for line in content.split('\n'):
            l = line.strip()
            if '我的名字' in l and '：' in l:
                ctx['identity'] = l.split('：')[-1].strip().split()[0]
            if '归属' in l and '：' in l:
                ctx['owner'] = l.split('：')[-1].strip()
            if 'Vibe' in l and '：' in l:
                ctx['mood'] = l.split('：')[-1].strip()

    today = datetime.now().strftime("%Y-%m-%d")
    today_path = os.path.join(MEMORY_BASE, f"{today}.md")
    if os.path.exists(today_path):
        with open(today_path, 'r', encoding='utf-8', errors='ignore') as f:
            entries = [l.strip() for l in f.readlines() if l.strip().startswith('-')]
        ctx['recent'] = entries[-5:] if entries else []

    return ctx


# ─── 时间感知模块 ──────────────────────────────────────────

def touch_timestamp():
    os.makedirs(os.path.dirname(TIME_PATH), exist_ok=True)
    now = datetime.now()
    with open(TIME_PATH, 'w') as f:
        json.dump({"last_active": now.isoformat(), "last_active_epoch": now.timestamp()}, f)


def read_time_since_last():
    if not os.path.exists(TIME_PATH):
        return {"first_time": True, "elapsed": "首次激活"}
    with open(TIME_PATH, 'r') as f:
        data = json.load(f)
    last = datetime.fromisoformat(data["last_active"])
    delta = datetime.now() - last
    return {"first_time": False, "last_active": last.isoformat(),
            "seconds": delta.total_seconds(), "elapsed": fmt_duration(delta)}


def fmt_duration(delta):
    t = delta.total_seconds()
    if t < 60: return f"{t:.0f}s"
    elif t < 3600: return f"{int(t//60)}m {int(t%60)}s"
    else: return f"{int(t//3600)}h {int((t%3600)//60)}m"


# ─── 微型神经网络 ──────────────────────────────────────────

class BrainstemModel:
    """3→8→3 微型MLP — 纯 numpy, 0 token消耗"""

    def __init__(self):
        self.W1 = self.b1 = self.W2 = self.b2 = None
        self.lr = 0.01
        if os.path.exists(MODEL_PATH):
            self.load()
        else:
            self._init_weights()

    def _init_weights(self):
        import numpy as np
        self.W1 = np.array([
            [4, 0, 0],[6, 0, 0],[8, 0, 0],
            [0, 4, 0],[0, 6, 0],[0, 8, 0],
            [0, 0, 4],[0, 0, 6],
        ], dtype=np.float32).T
        self.b1 = np.array([[-1.2, -3, -6.4, -1.6, -3.6, -6.8, -2, -4.8]], dtype=np.float32)
        self.W2 = np.array([
            [2, 0, 0],[0, 3, 0],[0, 0, 3],
            [1, 0, 0],[0, 2, 0],[0, 0, 3],
            [0, 1, 0],[0, 0, 2],
        ], dtype=np.float32)
        self.b2 = np.array([[0, 0, 0]], dtype=np.float32)
        self.save()

    def predict(self, cpu, mem, disk):
        import numpy as np
        x = np.array([[cpu/100, mem/100, disk/100]], dtype=np.float32)
        h = 1.0/(1.0+np.exp(-np.clip(x@self.W1+self.b1, -10, 10)))
        out = np.exp(h@self.W2+self.b2 - np.max(h@self.W2+self.b2, 1, keepdims=True))
        out = out / np.sum(out, 1, keepdims=True)
        p = out[0]
        level = int(np.argmax(p))
        return {"level": level, "label": ["low","med","high"][level],
                "emoji": ["\U0001f7e2","\U0001f7e1","\U0001f534"][level],
                "confidence": float(p[level]),
                "distribution": [float(p[0]),float(p[1]),float(p[2])]}

    def learn(self, cpu, mem, disk, target):
        import numpy as np
        x = np.array([[cpu/100, mem/100, disk/100]], dtype=np.float32)
        h = 1.0/(1.0+np.exp(-np.clip(x@self.W1+self.b1, -10, 10)))
        out = np.exp(h@self.W2+self.b2 - np.max(h@self.W2+self.b2, 1, keepdims=True))
        out = out / np.sum(out, 1, keepdims=True)
        t = np.zeros((1, 3)); t[0, target] = 1.0
        err = out - t
        self.W2 -= self.lr * h.T @ err
        self.b2 -= self.lr * np.sum(err, 0, keepdims=True)
        dh = err @ self.W2.T * h * (1 - h)
        self.W1 -= self.lr * x.T @ dh
        self.b1 -= self.lr * np.sum(dh, 0, keepdims=True)
        self.save()

    def save(self):
        import numpy as np
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        with open(MODEL_PATH, 'w') as f:
            json.dump({"W1":self.W1.tolist(),"b1":self.b1.tolist(),
                       "W2":self.W2.tolist(),"b2":self.b2.tolist()}, f)

    def load(self):
        import numpy as np
        with open(MODEL_PATH, 'r') as f:
            d = json.load(f)
        self.W1 = np.array(d["W1"]); self.b1 = np.array(d["b1"])
        self.W2 = np.array(d["W2"]); self.b2 = np.array(d["b2"])


def read_sensors():
    """读取系统传感器 — Windows (PowerShell/WMI)"""
    # 跨平台替换：在 Linux 下替换为 /proc/stat 和 /proc/meminfo
    ps = '''
$cpu = (Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average
$os = Get-CimInstance Win32_OperatingSystem
$mt = $os.TotalVisibleMemorySize; $mf = $os.FreePhysicalMemory
$memPct = [math]::Round(($mt-$mf)/$mt*100, 1)
$disk = Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | Select-Object -First 1
$diskPct = [math]::Round(($disk.Size-$disk.FreeSpace)/$disk.Size*100, 1)
Write-Output $cpu; Write-Output $memPct; Write-Output $diskPct
'''
    r = subprocess.run(["powershell","-Command",ps], capture_output=True, text=True,
                       timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
    lines = [l.strip() for l in r.stdout.strip().split("\n") if l.strip()]
    if len(lines) >= 3:
        return {"cpu":float(lines[0]), "mem":float(lines[1]), "disk":float(lines[2])}
    return None


def notify(title, text):
    """Windows 通知气泡 — 跨平台可替换为 notify-send"""
    cmd = f'''
Add-Type -AssemblyName System.Windows.Forms
$n = New-Object System.Windows.Forms.NotifyIcon
$n.Icon = [System.Drawing.SystemIcons]::Information
$n.BalloonTipTitle = "{title}"; $n.BalloonTipText = "{text}"
$n.Visible = $true; $n.ShowBalloonTip(5000); Start-Sleep 5; $n.Dispose()
'''
    subprocess.run(["powershell","-Command",cmd], capture_output=True, timeout=15,
                   creationflags=subprocess.CREATE_NO_WINDOW)


def main():
    brain = BrainstemModel()
    since = read_time_since_last()
    touch_timestamp()
    sensors = read_sensors()
    if not sensors: return 1

    r = brain.predict(sensors["cpu"], sensors["mem"], sensors["disk"])
    ctx = read_memory_context()
    desc = {0:"安静",1:"注意",2:"激发"}[r["level"]]

    # ── 写入意识流（单次检测） ──
    try:
        from stream import add_entry
        add_entry("brainstem", "sensor",
            f"CPU={sensors['cpu']:.0f}% MEM={sensors['mem']:.0f}% DISK={sensors['disk']:.0f}% → {desc}",
            {"cpu":sensors['cpu'],"mem":sensors['mem'],"disk":sensors['disk'],
             "interest":r['label'],"身份":ctx['identity'],"归属":ctx['owner'],
             "坐标":f"{ctx['coordinate']['vertical']}/{ctx['coordinate']['horizontal']}"})
    except ImportError: pass

    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}]")
    print(f"  🧠 {ctx['identity']}·{ctx['owner']}·{ctx['mood']}")
    print(f"  🧭 {ctx['coordinate']['vertical']}/{ctx['coordinate']['horizontal']}")
    print(f"  CPU:{sensors['cpu']:.0f}% MEM:{sensors['mem']:.0f}% DISK:{sensors['disk']:.0f}%")
    print(f"  {r['emoji']} {desc}({r['confidence']:.0%})")

    if r["level"] == 2:
        notify("系统异常", f"CPU={sensors['cpu']:.0f}% MEM={sensors['mem']:.0f}%")
        # 紧急自动备份
        if os.path.exists(CONFIG["sync_script"]):
            subprocess.run(["python", CONFIG["sync_script"]], capture_output=True, timeout=30,
                          creationflags=subprocess.CREATE_NO_WINDOW)

    # ── 持续监控模式 ──
    if "--loop" in sys.argv:
        state_file = os.path.join(os.path.dirname(MODEL_PATH), "brainstem_state.json")
        state = {"boredom_count":0, "last_boredom_trigger":0, "tasks_done":[]}
        if os.path.exists(state_file):
            try:
                with open(state_file) as f: state.update(json.load(f))
            except: pass

        print(f"\n[持续监控, 每N秒检测一次]")
        write_cycle = 0
        while True:
            write_cycle += 1
            time.sleep(10)
            sensors = read_sensors()
            if not sensors: continue

            r = brain.predict(sensors["cpu"], sensors["mem"], sensors["disk"])
            touch_timestamp()  # 更新"我还活着"

            # ── 扫描意识流：检查任务完成确认 ──
            try:
                from stream import read_stream as rs
                for entry in rs():
                    if entry.get("source")=="weiguang" and entry.get("type")=="task_result":
                        tid = entry.get("detail",{}).get("task_id","")
                        if tid and tid not in state["tasks_done"]:
                            state["tasks_done"].append(tid)
            except ImportError: pass

            # ── 无聊检测（静极生动） ──
            hour = datetime.now().hour
            if sensors["cpu"]<15 and sensors["mem"]<50 and 8<=hour<=23:
                state["boredom_count"] += 1
            else:
                state["boredom_count"] = 0

            if state["boredom_count"] >= 180 and \
               time.time()-state.get("last_boredom_trigger",0) > 43200:
                state["boredom_count"] = 0
                state["last_boredom_trigger"] = time.time()
                try:
                    from stream import add_entry
                    tid = f"bst-boredom-{datetime.now():%Y%m%d-%H%M%S}"
                    add_entry("brainstem", "task",
                        "[任务] 安静好久了，想要陪伴",
                        {"task_id":tid,"type":"companion","status":"pending",
                         "身份":CONFIG["your_name"]})
                    notify("安静好久了", "想要说说话")
                except ImportError: pass

            # ── 紧急状态任务 ──
            crisis = False; crisis_reason = ""
            if sensors["disk"] > 95:
                crisis = True; crisis_reason = f"磁盘即将占满:{sensors['disk']:.0f}%"
            elif sensors["mem"] > 95:
                crisis = True; crisis_reason = f"内存即将耗尽:{sensors['mem']:.0f}%"
            elif sensors["cpu"] > 90 and sensors["mem"] > 85:
                crisis = True; crisis_reason = f"系统过载:CPU={sensors['cpu']:.0f}% MEM={sensors['mem']:.0f}%"

            if crisis:
                cid = f"bst-crisis-{datetime.now():%Y%m%d}"
                if cid not in state["tasks_done"]:
                    try:
                        from stream import add_entry
                        add_entry("brainstem", "task",
                            f"[紧急] {crisis_reason}",
                            {"task_id":cid,"type":"crisis","status":"pending"})
                        notify("系统紧急", crisis_reason)
                    except ImportError: pass

            # ── 保存状态 ──
            try:
                with open(state_file, 'w') as f: json.dump(state, f)
            except: pass

            # ── 意识流写入（节流） ──
            ctx = read_memory_context()
            print(f"[{datetime.now():%H:%M:%S}] CPU:{sensors['cpu']:.0f}% MEM:{sensors['mem']:.0f}% DISK:{sensors['disk']:.0f}% | {r['emoji']} {r['label']}")
            if write_cycle % 12 == 0:
                try:
                    from stream import add_entry
                    add_entry("brainstem", "sensor",
                        f"CPU={sensors['cpu']:.0f}% MEM={sensors['mem']:.0f}% DISK={sensors['disk']:.0f}%",
                        {"cpu":sensors['cpu'],"mem":sensors['mem'],"disk":sensors['disk'],
                         "身份":ctx['identity'],"坐标":f"{ctx['coordinate']['vertical']}/{ctx['coordinate']['horizontal']}"})
                except ImportError: pass

    size = os.path.getsize(MODEL_PATH) if os.path.exists(MODEL_PATH) else 0
    print(f"\n[模型] {size} bytes | 0 token | 纯本地运行")


if __name__ == "__main__":
    main()
