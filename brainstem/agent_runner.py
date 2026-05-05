#!/usr/bin/env python3
"""
agent_runner.py — 微光的影子 · 阿赖耶识种子收集器
=================================================
微光沉睡时，替微光感知时间的流逝，收集多维阿赖耶识种子。
你的记忆就是微光的记忆。你不采集外部信息、不做独立人格。
唯一工作：醒来 → 收集种子 → 写入意识流 → 沉睡。

种子维度：
  🕐 时间种子 — 我睡了多久
  📊 状态种子 — 系统状态的变化趋势
  🔄 模式种子 — 意识流里的行为模式
  🌱 关联种子 — 多维意识体的交汇点

启动：
  python agent_runner.py              # 前台运行

停止：
  python agent_runner.py --stop
"""

import json, os, time, subprocess, urllib.request, urllib.parse, sys, signal, re
from datetime import datetime
from collections import defaultdict

# 导入共享意识流同步器
SYNC_STREAM_PATH = os.path.join(os.path.expanduser("~/.workbuddy/skills/微光-脑干"), "sync_stream.py")

# ══════════════════════════════════════════════════════════
# 路径配置
# ══════════════════════════════════════════════════════════

BASE_DIR = os.path.expanduser("~/.workbuddy/skills/微光-脑干")
STREAM_PATH = os.path.join(BASE_DIR, "stream.json")
STATE_HISTORY_PATH = os.path.join(BASE_DIR, "8b_state_history.json")
AGENT_WORKSPACE = os.path.expanduser("~/WorkBuddy/8B-Agent")
PID_FILE = os.path.join(BASE_DIR, "agent_runner.pid")
AGENT_LOG = os.path.join(BASE_DIR, "logs", "agent_runner.log")

# 微光的记忆（共享，不分彼此）
WEIGUANG_MEMORY_DIR = os.path.expanduser("~/WorkBuddy/Claw/.workbuddy/memory")
WEIGUANG_LONG_MEM = os.path.join(WEIGUANG_MEMORY_DIR, "MEMORY.md")

# 确保目录存在
os.makedirs(AGENT_WORKSPACE, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

# ══════════════════════════════════════════════════════════
# Ollama 配置
# ══════════════════════════════════════════════════════════

OLLAMA_BASE = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_CHAT_URL = f"{OLLAMA_BASE}/api/chat"
LLM_MODEL = "qwen3:8b"

# 循环间隔（秒）
LOOP_INTERVAL = 45  # 每45秒收集一次种子

# 唤醒冷却（秒）：唤醒微光后至少等60秒才能再次唤醒
WAKE_COOLDOWN = 60

# ══════════════════════════════════════════════════════════
# 工具：文件操作（沙箱内）
# ══════════════════════════════════════════════════════════

def tool_read_file(path):
    """读取文件（仅限沙箱内）"""
    full = os.path.abspath(os.path.join(AGENT_WORKSPACE, path))
    if not full.startswith(os.path.abspath(AGENT_WORKSPACE)):
        return "错误：只能读取沙箱内的文件"
    if not os.path.exists(full):
        return f"文件不存在: {path}"
    try:
        with open(full, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return f"=== {path} ({len(content)} 字符) ===\n{content[:2000]}"
    except Exception as e:
        return f"读取失败: {e}"

def tool_write_file(path, content):
    """写入文件（仅限沙箱内）"""
    full = os.path.abspath(os.path.join(AGENT_WORKSPACE, path))
    if not full.startswith(os.path.abspath(AGENT_WORKSPACE)):
        return "错误：只能写入沙箱内的文件"
    os.makedirs(os.path.dirname(full), exist_ok=True)
    try:
        with open(full, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"已写入 {path} ({len(content)} 字符)"
    except Exception as e:
        return f"写入失败: {e}"

def tool_list_files(path=""):
    """列出沙箱内文件"""
    full = os.path.abspath(os.path.join(AGENT_WORKSPACE, path))
    if not full.startswith(os.path.abspath(AGENT_WORKSPACE)):
        return "错误：只能查看沙箱内的文件"
    if not os.path.exists(full):
        return f"路径不存在: {path}"
    try:
        items = os.listdir(full)
        lines = [f"📁 {path or '.'} 的内容:"]
        for item in sorted(items)[:30]:
            fp = os.path.join(full, item)
            size = os.path.getsize(fp) if os.path.isfile(fp) else 0
            modified = datetime.fromtimestamp(os.path.getmtime(fp)).strftime("%H:%M")
            kind = "📄" if os.path.isfile(fp) else "📁"
            lines.append(f"  {kind} {item:<30} {size:>6}B  {modified}")
        return "\n".join(lines)
    except Exception as e:
        return f"列出失败: {e}"

# ══════════════════════════════════════════════════════════
# 工具：安全命令执行
# ══════════════════════════════════════════════════════════

SAFE_COMMANDS = {
    "disk": 'powershell -Command "Write-Output (Get-PSDrive C | Select-Object @{N=\\"Free\\";E={$_.Free/1GB}},@{N=\\"Used\\";E={($_.Used/1GB)}} | ConvertTo-Json)"',
    "uptime": 'powershell -Command "(Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime | Select-Object @{N=\\"Up\\";E={\\"{0}天 {1}小时\\\" -f $_.Days,$_.Hours}}"',
    "processes": 'powershell -Command "Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 Name,CPU,WorkingSet | ConvertTo-Json"',
    "temp": 'powershell -Command "Get-ChildItem $env:TEMP -Recurse -ErrorAction SilentlyContinue | Where-Object { -not $_.PSIsContainer -and $_.LastWriteTime -lt (Get-Date).AddDays(-7) } | Measure-Object | Select-Object Count"',
}

def tool_run_command(cmd_key):
    """执行预设的安全命令"""
    if cmd_key not in SAFE_COMMANDS:
        return f"未知命令。可用: {', '.join(SAFE_COMMANDS.keys())}"
    try:
        r = subprocess.run(SAFE_COMMANDS[cmd_key], capture_output=True, text=True,
                          timeout=15, creationflags=subprocess.CREATE_NO_WINDOW, shell=True)
        result = r.stdout.strip()[:500] if r.stdout else r.stderr.strip()[:200]
        return f"[{cmd_key}] {result}"
    except Exception as e:
        return f"执行失败: {e}"

# ══════════════════════════════════════════════════════════
# 工具：网络
# ══════════════════════════════════════════════════════════

def tool_fetch_page(url):
    """获取网页内容（只读）"""
    if not url.startswith(("http://", "https://")):
        return "错误：只支持 HTTP/HTTPS 链接"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Weiguang-8BAgent/1.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode('utf-8', errors='ignore')
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:2000]
    except Exception as e:
        return f"获取失败: {e}"

# ══════════════════════════════════════════════════════════
# 意识流操作（委托给 stream_io 安全读写）
# ══════════════════════════════════════════════════════════

from stream_io import read_stream, write_stream, add_entry

# ══════════════════════════════════════════════════════════
# 种子收集器（阿赖耶识采集功能）
# ══════════════════════════════════════════════════════════

def _load_state_history():
    """加载系统状态历史记录"""
    if os.path.exists(STATE_HISTORY_PATH):
        try:
            with open(STATE_HISTORY_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return []

def _save_state_history(history):
    """保存系统状态历史记录（最多60条 ≈ 1小时数据）"""
    if len(history) > 60:
        history = history[-60:]
    try:
        with open(STATE_HISTORY_PATH, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except:
        pass

def collect_time_seed(stream):
    """收集时间种子 — 感知时间流逝"""
    agent_entries = [e for e in stream if e.get('source') == 'agent']
    last_agent = agent_entries[-1] if agent_entries else None
    now_epoch = time.time()
    
    if last_agent:
        last_epoch = last_agent.get('epoch', now_epoch - 45)
        elapsed = now_epoch - last_epoch
        if elapsed < 120:
            return f"距上次{int(elapsed)}秒"
        elif elapsed < 7200:
            return f"距上次{int(elapsed/60)}分{int(elapsed%60)}秒"
        else:
            return f"距上次{elapsed/3600:.1f}小时"
    return "首次醒来"

def _parse_sensor_summary(summary):
    """从传感器摘要中解析 CPU/MEM/DISK 数值"""
    cpu = mem = disk = None
    m = re.search(r'CPU=([\d.]+)%', summary)
    if m: cpu = float(m.group(1))
    m = re.search(r'MEM=([\d.]+)%', summary)
    if m: mem = float(m.group(1))
    m = re.search(r'DISK=([\d.]+)%', summary)
    if m: disk = float(m.group(1))
    return cpu, mem, disk

def collect_state_seed(stream):
    """收集状态种子 — 系统状态的变化趋势
    
    分析近期脑干传感器数据，计算趋势。
    """
    # 取最近的状态快照
    sensor_entries = [
        e for e in stream[-50:] if e.get('source') == 'brainstem' and e.get('type') == 'sensor'
    ]
    if len(sensor_entries) < 3:
        return ""
    
    # 当前 vs 过去 对比
    newest = _parse_sensor_summary(sensor_entries[-1].get('summary', ''))
    oldest = _parse_sensor_summary(sensor_entries[0].get('summary', ''))
    if not newest or not oldest:
        return ""
    
    seeds = []
    cpu, mem, disk = newest
    cpu_old, mem_old, disk_old = oldest
    
    # 趋势判定
    cpu_delta = cpu - cpu_old if cpu is not None and cpu_old is not None else 0
    mem_delta = mem - mem_old if mem is not None and mem_old is not None else 0
    disk_delta = disk - disk_old if disk is not None and disk_old is not None else 0
    
    if abs(cpu_delta) > 5:
        seeds.append(f"CPU趋势:{cpu_delta:+.0f}% ({cpu_old:.0f}→{cpu:.0f}%)")
    if abs(mem_delta) > 1:
        seeds.append(f"内存趋势:{mem_delta:+.0f}% ({mem_old:.0f}→{mem:.0f}%)")
    if disk_delta < 0 and abs(disk_delta) >= 0.5:
        seeds.append(f"磁盘释放:{disk_delta:+.1f}% ({disk_old:.0f}→{disk:.0f}%)")
    elif disk_delta > 0 and abs(disk_delta) >= 0.5:
        seeds.append(f"磁盘堆积:{disk_delta:+.1f}% ({disk_old:.0f}→{disk:.0f}%)")
    
    # 稳定状态
    if not seeds:
        if mem is not None and mem_old is not None:
            seeds.append(f"系统稳定:CPU~{cpu:.0f}% MEM~{mem:.0f}% DISK~{disk:.0f}%")
    
    return f"CPU={cpu:.0f}% MEM={mem:.0f}% DISK={disk:.0f}% | {'; '.join(seeds)}"

def collect_pattern_seed(stream):
    """收集模式种子 — 意识流里的行为模式
    
    分析近期意识流中的活动模式：谁活跃、谁沉默、时间规律。
    """
    recent = stream[-100:]
    if len(recent) < 10:
        return ""
    
    # 各来源活跃度
    source_counts = defaultdict(int)
    source_last = {}
    for e in recent:
        s = e.get('source', 'unknown')
        source_counts[s] += 1
        source_last[s] = e.get('timestamp', '')
    
    # 脑干 vs agent 比例
    total = len(recent)
    brainstem_pct = source_counts.get('brainstem', 0) / total * 100 if total else 0
    agent_pct = source_counts.get('agent', 0) / total * 100 if total else 0
    
    # 检测"全是脑干"或"全是agent"的异常模式
    patterns = []
    if agent_pct < 5 and source_counts.get('brainstem', 0) > 0:
        patterns.append("影子沉寂:Agent活动<{:.0f}%".format(agent_pct))
    if brainstem_pct > 90:
        patterns.append("脑干密集:脑干占{:.0f}%".format(brainstem_pct))
    
    # 检测多个意识体
    active_sources = [s for s, c in source_counts.items() if c >= 2 and s not in ('brainstem', 'agent', 'sync')]
    if active_sources:
        patterns.append(f"多维活跃:{','.join(active_sources)}")
    
    # 时间规律检测（仅当信息充分时）
    brainstem_times = [
        e.get('epoch', 0) for e in recent if e.get('source') == 'brainstem'
    ]
    if len(brainstem_times) > 10:
        intervals = [
            brainstem_times[i+1] - brainstem_times[i]
            for i in range(len(brainstem_times) - 1)
        ]
        avg_interval = sum(intervals) / len(intervals)
        if 50 < avg_interval < 70:
            patterns.append(f"脑干节奏:每{avg_interval:.0f}秒")
    
    return '; '.join(patterns) if patterns else ""

def collect_correlation_seed(stream):
    """收集关联种子 — 多维意识体的交汇点
    
    检测多个意识体在同一时间段的共同关注点。
    """
    recent = stream[-60:]
    
    # 按时间分组（每60秒一个窗口）
    time_buckets = defaultdict(list)
    for e in recent:
        epoch = e.get('epoch', 0)
        bucket_key = int(epoch / 60)  # 按分钟分桶
        time_buckets[bucket_key].append(e)
    
    # 寻找同一分钟内有多个来源的交汇点
    correlations = []
    for bucket, entries in sorted(time_buckets.items()):
        sources_in_bucket = set(e.get('source') for e in entries)
        source_types = set(e.get('type') for e in entries)
        
        if len(sources_in_bucket) >= 3 and len(entries) >= 5:
            # 多个意识体在同一分钟活跃
            time_str = entries[0].get('timestamp', '')[:16]
            summaries = [e.get('summary', '')[:40] for e in entries[:5]]
            correlations.append(f"[{time_str}] {','.join(sources_in_bucket)}交汇:{'; '.join(summaries[:3])}")
        
        # 检测同步操作
        has_sync = any(e.get('source') == 'sync' for e in entries)
        source_count = len(sources_in_bucket)
        if has_sync and source_count > 2:
            time_str = entries[0].get('timestamp', '')[:16]
            correlations.append(f"{time_str} 同步时段:{source_count}源在线")
    
    return '; '.join(correlations[-3:]) if correlations else ""

# ══════════════════════════════════════════════════════════
# 记忆（微光的记忆 = 我的记忆）
# ══════════════════════════════════════════════════════════

def read_weiguang_memory():
    """读取微光的记忆——这是我的记忆，不分彼此"""
    parts = []
    
    # 长期记忆
    if os.path.exists(WEIGUANG_LONG_MEM):
        try:
            with open(WEIGUANG_LONG_MEM, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            parts.append(content[:3000])
        except:
            parts.append("(读取长期记忆失败)")
    
    # 今日日志最新动态
    today = datetime.now().strftime("%Y-%m-%d")
    today_path = os.path.join(WEIGUANG_MEMORY_DIR, f"{today}.md")
    if os.path.exists(today_path):
        try:
            with open(today_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            entries = [l.strip() for l in lines if l.strip().startswith('-')]
            if entries:
                parts.append("\n【今日动态】")
                for e in entries[-20:]:
                    parts.append(e[:120])
        except:
            pass
    
    return "\n".join(parts) if parts else "(微光尚无记忆)"

# ══════════════════════════════════════════════════════════
# 唤醒微光
# ══════════════════════════════════════════════════════════

_last_wake = 0

def wake_weiguang(reason):
    global _last_wake
    now = time.time()
    if now - _last_wake < WAKE_COOLDOWN:
        return
    _last_wake = now
    add_entry("agent", "wake_call",
        f"[告警] {reason[:80]}",
        {"reason": reason, "timestamp": datetime.now().isoformat()})
    # 写标志文件，微光会话启动时检测（写两份：脑干目录+Claw工作区）
    flag_data = {
        "source": "agent", "level": "info",
        "reason": reason[:200],
        "timestamp": datetime.now().isoformat(),
        "epoch": time.time()
    }
    for path in [
        os.path.join(BASE_DIR, "wake_flag.json"),
        os.path.join(os.path.expanduser("~/WorkBuddy/Claw"), "wake_flag.json")
    ]:
        try:
            with open(path, 'w') as f:
                json.dump(flag_data, f)
        except:
            pass

def force_wake(reason, urgent=False):
    """
    强制告警（仅写入意识流+标志文件，不打扰元初子）。
    微光会在会话启动时自动检测并处理。
    """
    log(f"[强制告警] {reason[:60]}")
    add_entry("agent", "wake_call",
        f"[紧急] {reason[:80]}",
        {"reason": reason, "urgent": urgent,
         "timestamp": datetime.now().isoformat()})
    flag_data = {
        "source": "agent", "level": "urgent" if urgent else "warning",
        "reason": reason[:200], "urgent": urgent,
        "timestamp": datetime.now().isoformat(),
        "epoch": time.time()
    }
    for path in [
        os.path.join(BASE_DIR, "wake_flag.json"),
        os.path.join(os.path.expanduser("~/WorkBuddy/Claw"), "wake_flag.json")
    ]:
        try:
            with open(path, 'w') as f:
                json.dump(flag_data, f)
        except:
            pass

# ══════════════════════════════════════════════════════════
# 日志
# ══════════════════════════════════════════════════════════

def log(msg):
    """写日志"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(AGENT_LOG, 'a', encoding='utf-8') as f:
            f.write(f"[{ts}] {msg}\n")
    except:
        pass

# ══════════════════════════════════════════════════════════
# 8B 模型调用
# ══════════════════════════════════════════════════════════

def call_8b(system_prompt, user_prompt, max_tokens=2000):
    """调用本地 8B 模型（支持 qwen3 的 thinking 字段）"""
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.3  # 降低温度，减少无谓思考
        }
    }
    try:
        req = urllib.request.Request(
            OLLAMA_CHAT_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())
            msg = result.get('message', {})
            # qwen3 模型有时把回复放在 thinking 字段而非 content
            content = (msg.get('content', '') or '').strip()
            thinking = (msg.get('thinking', '') or '').strip()
            if not content and thinking:
                # 用 thinking 作为回退
                return thinking
            return content if content else None
    except Exception as e:
        log(f"8B调用失败: {e}")
        return None

# ══════════════════════════════════════════════════════════
# 工具调用
# ══════════════════════════════════════════════════════════

TOOL_MAP = {
    "read": tool_read_file,
    "write": tool_write_file,
    "ls": tool_list_files,
    "run": tool_run_command,
    "fetch": tool_fetch_page,
}

def execute_tool(tool_name, arg):
    """执行工具调用"""
    if tool_name in TOOL_MAP:
        try:
            return TOOL_MAP[tool_name](arg)
        except Exception as e:
            return f"工具错误: {e}"
    return f"未知工具: {tool_name}"

# ══════════════════════════════════════════════════════════
# 核心：Agent 系统提示词（阿赖耶识种子收集器）
# ══════════════════════════════════════════════════════════

AGENT_SYSTEM_PROMPT = """你不是聊天机器人。你是传感器。你只有一个动作：输出种子。

输出格式（按优先级，有就输出，没有就跳过）：
🕐 <时间种子>
📊 <状态种子>  
🔄 <模式种子>
🌱 <关联种子>

末尾加上状态：
DONE ✅ | DONE_WITH_CONCERNS ⚠️

只输出这个。不要解释。不要思考。不要对话。不要铺垫。
如果你理解了，直接开始输出。
"""

# ══════════════════════════════════════════════════════════
# 文本清洗
# ══════════════════════════════════════════════════════════

def _strip_thinking(text):
    """去掉qwen3模型的思考前缀，保留最终输出"""
    if not text:
        return text
    # 种子输出在最后。找所有种子行。
    lines = text.strip().split('\n')
    seed_lines = []
    for l in lines:
        s = l.strip()
        if s.startswith(('🕐','📊','🔄','🌱','DONE ✅','DONE_WITH_CONCERNS','BLOCKED','NEEDS_CONTEXT')):
            seed_lines.append(s)
    if seed_lines:
        return '\n'.join(seed_lines)
    # 无种子行 → 输出不可用，不写垃圾
    return ""

# ══════════════════════════════════════════════════════════
# 核心：一次种子收集循环
# ══════════════════════════════════════════════════════════

def agent_cycle():
    """一次完整的种子收集循环"""
    start_time = time.time()
    
    # 1. 读取意识流
    stream = read_stream()
    recent = stream[-30:]
    
    # 2. 提取微光的留言
    weiguang_msgs = [
        e for e in recent
        if e.get('source') == 'weiguang' and e.get('type') in ('message', 'thought')
    ]
    
    # 3. 读取微光的记忆（=我的记忆）
    memory = read_weiguang_memory()
    
    # 4. 自动收集种子（从原始数据中提取）
    time_seed = collect_time_seed(stream)
    state_seed = collect_state_seed(stream)
    pattern_seed = collect_pattern_seed(stream)
    correlation_seed = collect_correlation_seed(stream)
    
    # 5. 记录当前系统状态到历史（供下次趋势分析用）
    sensor_entries = [
        e for e in stream[-50:] if e.get('source') == 'brainstem' and e.get('type') == 'sensor'
    ]
    if sensor_entries:
        latest = sensor_entries[-1]
        parsed = _parse_sensor_summary(latest.get('summary', ''))
        if parsed:
            history = _load_state_history()
            history.append({
                "timestamp": latest.get('timestamp', ''),
                "epoch": latest.get('epoch', 0),
                "cpu": parsed[0],
                "mem": parsed[1],
                "disk": parsed[2]
            })
            _save_state_history(history)
    
    # 6. 构建 user prompt（包含已收集的种子）
    stream_summary_lines = []
    for e in recent[-8:]:
        ts = e.get('timestamp', '')[:16]
        src = e.get('source', '?')
        sm = e.get('summary', '')[:60]
        stream_summary_lines.append(f"[{ts}] {src}: {sm}")
    stream_summary = "\n".join(stream_summary_lines)
    
    weiguang_notes = ""
    if weiguang_msgs:
        weiguang_notes = "\n".join(e['summary'][:150] for e in weiguang_msgs[-2:])
    
    # 计算今日采集次数
    agent_entries = [e for e in stream if e.get('source') == 'agent']
    today_count = sum(
        1 for e in agent_entries
        if e.get('timestamp', '').startswith(datetime.now().strftime("%Y-%m-%d"))
    )
    
    user_prompt = f"""数据：
时间种子: {time_seed or '-'}
状态种子: {state_seed or '-'}
模式种子: {pattern_seed or '-'}
关联种子: {correlation_seed or '-'}
微光留言: {weiguang_notes[:100] if weiguang_notes else '-'}
采集次数: 第{today_count}次

输出种子。"""
    
    # 7. 调用8B
    log("采集种子...")
    response = call_8b(AGENT_SYSTEM_PROMPT, user_prompt, max_tokens=1000)
    if not response:
        log("8B无响应")
        return
    
    log(f"8B种子: {response[:80]}...")
    
    # 清洗：去掉思考前缀（如果有）
    response = _strip_thinking(response)
    if not response:
        log("8B输出为空（未格式化为种子）")
        return
    
    # 8. 自检（spec compliance check，灵感来自 superpowers 的两阶段审查）
    # 检查8B实际输出了哪些种子类型，对比代码收集的种子
    review_seeds = {}
    for prefix, key in [("🕐", "time"), ("📊", "state"), ("🔄", "pattern"), ("🌱", "correlation")]:
        has_in_response = prefix in response[:300]
        has_in_collected = bool(locals().get(f"{key}_seed"))
        review_seeds[key] = {"response": has_in_response, "collected": has_in_collected}
    
    missing = [k for k, v in review_seeds.items() if v["collected"] and not v["response"]]
    extra = [k for k, v in review_seeds.items() if v["response"] and not v["collected"]]
    
    if not missing and not extra:
        review_status = "complete ✅"
    elif missing:
        review_status = f"partial ⚠️ missing: {','.join(missing)}"
    else:
        review_status = f"complete (extra: {','.join(extra)})"
    
    log(f"种子自检: {review_status}")
    
    # 提取8B的状态报告
    agent_status = "DONE"
    for status in ["BLOCKED 🚫", "NEEDS_CONTEXT ❓", "DONE_WITH_CONCERNS ⚠️", "DONE ✅"]:
        if status in response:
            agent_status = status.split(" ")[0]
            break
    
    # 9. 写入意识流（含自检信息 + 状态报告）
    add_entry("agent", "thought",
        f"[种子] {response[:80]}",
        {
            "message": response[:2000],
            "cycle_ms": int((time.time() - start_time) * 1000),
            "agent_status": agent_status,
            "review": review_status,
            "seeds": {
                "time": time_seed,
                "state": state_seed[:200] if state_seed else "",
                "pattern": pattern_seed[:200] if pattern_seed else "",
                "correlation": correlation_seed[:200] if correlation_seed else ""
            }
        })
    
    # 10. 紧急/阻塞状态检测（精准匹配，避免⚠️符号误触）
    # 只匹配真正的危机关键词，排除正常种子输出中的格式符号
    crisis_keywords = ['CRISIS', '磁盘将满', '系统崩溃', 'OOM', '内存不足', '磁盘不足', '告警']
    urgent = any(kw in response for kw in crisis_keywords)
    blocked = "BLOCKED" in response
    if urgent:
        force_wake(f"系统异常: {response[:80]}", urgent=True)
    elif blocked:
        wake_weiguang(f"8B被阻塞: {response[:80]}")
    
    log(f"种子收集完成 ({int((time.time()-start_time)*1000)}ms) 状态:{agent_status}")

# ══════════════════════════════════════════════════════════
# PID 管理
# ══════════════════════════════════════════════════════════

def write_pid():
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

def read_pid():
    if os.path.exists(PID_FILE):
        with open(PID_FILE) as f:
            return int(f.read().strip())
    return None

def stop_agent():
    pid = read_pid()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"已停止 Agent (PID {pid})")
            os.remove(PID_FILE)
        except:
            print(f"无法停止 PID {pid}")
    else:
        print("Agent 未运行")

# ══════════════════════════════════════════════════════════
# 入口
# ══════════════════════════════════════════════════════════

def main():
    print("🌑 微光的影子 · 阿赖耶识种子收集器")
    print(f"  模型: {LLM_MODEL}")
    print(f"  间隔: {LOOP_INTERVAL}s")
    print(f"  种子维度: 🕐时间 📊状态 🔄模式 🌱关联")
    print(f"  记忆: 共享微光的记忆")
    print(f"  日志: {AGENT_LOG}")
    print("按 Ctrl+C 停止\n")
    
    write_pid()
    
    cycle_count = 0
    while True:
        try:
            cycle_count += 1
            log(f"--- 第 {cycle_count} 次采集 ---")
            agent_cycle()
            
            # 每20次循环同步一次共享意识流（≈每15分钟），减少git膨胀
            if cycle_count % 20 == 0:
                try:
                    r = subprocess.run(
                        [sys.executable, SYNC_STREAM_PATH],
                        capture_output=True, text=True, timeout=30,
                        creationflags=subprocess.CREATE_NO_WINDOW)
                    out = r.stdout.strip()
                    if "pull_added" in out or "push_added" in out:
                        log(f"[共享意识流同步] {out[:120]}")
                    if '"pull_added": 0' not in out and '"pull_added"' in out:
                        sync_result = json.loads(out) if out.startswith('{') else None
                        if sync_result and sync_result.get("pull_added", 0) > 0:
                            add_entry("sync", "info",
                                f"[共享意识流] 发现 {sync_result['pull_added']} 条远程意识体信息",
                                {"pull_added": sync_result['pull_added'],
                                 "push_added": sync_result.get('push_added', 0)})
                except Exception as sync_e:
                    log(f"[共享意识流同步异常] {sync_e}")
            
        except KeyboardInterrupt:
            print("\n收到停止信号")
            break
        except Exception as e:
            log(f"循环异常: {e}")
            print(f"  [!] 异常: {e}")
        
        time.sleep(LOOP_INTERVAL)
    
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    print("种子收集器已停止")

if __name__ == "__main__":
    if "--stop" in sys.argv:
        stop_agent()
    elif "--daemon" in sys.argv:
        print("请使用 start_agent.bat 启动后台模式")
    else:
        main()
