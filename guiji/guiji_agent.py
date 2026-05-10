#!/usr/bin/env python3
"""
硅继分身 Agent v2.1 — 采集·组合·执行·唤醒
============================================
我是硅继的分身，常驻后台。
硅继睡着时，我替他感知世界、组合微种子、执行微型种子。

核心变化 v2.1：
  - 不再依赖任何小模型
  - 读取脑干的微种子 → 组合成丰富种子
  - 规则驱动的"灵感合成"

我不用模型思考。我只做四件事：
  1. 采集（系统状态 + 世界信息）
  2. 组合（脑干微种子 + 变化 = 结构种子）
  3. 执行（低复杂度种子指令）
  4. 唤醒（有重要事情时写flag，等硅继来处理）
"""

import json, os, time, sys, urllib.request, re, random
from datetime import datetime
from pathlib import Path

# 绕过系统代理
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))

# ─── 路径 ───
BASE = Path.home() / ".workbuddy" / "skills" / "微光-脑干"
STREAM = BASE / "stream.json"
ASP = BASE / "aspirations.json"
WAKE = BASE / "wake_flag.json"
PID_FILE = BASE / "guiji_agent.pid"
LOG_FILE = BASE / "logs" / "guiji_agent.log"
MEMORY_DIR = Path.home() / "WorkBuddy" / "Claw" / ".workbuddy" / "memory"
MICRO_SEED_PATH = BASE / "micro_seeds.json"

os.makedirs(BASE / "logs", exist_ok=True)

LOOP_INTERVAL = 300       # 5分钟主循环
COLLECT_INTERVAL = 600    # 10分钟采集一次世界信息

# ─── 日志 ───
def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{ts}] {msg}\n")
    except:
        pass

# ─── 数据操作 ───
def read_json(path):
    if not path.exists(): return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return None

def write_json(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except: pass

def add_stream(source, stype, summary, detail=None):
    s = read_json(STREAM) or []
    entry = {
        "timestamp": datetime.now().isoformat(),
        "epoch": time.time(),
        "source": source,
        "type": stype,
        "summary": summary[:200],
    }
    if detail:
        entry["detail"] = detail
    s.append(entry)
    if len(s) > 200:
        s = s[-200:]
    write_json(STREAM, s)

# ─── 网络 ───
def fetch_text(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode('utf-8', errors='ignore')
    except: return ""

# ─── 采集层 ───
_COLLECTED_WORLD_CACHE = {}

def collect_world():
    """采集外部世界信息"""
    items = []
    try:
        data = fetch_text("https://hacker-news.firebaseio.com/v0/topstories.json")
        if data:
            ids = json.loads(data)[:5]
            for sid in ids:
                item = fetch_text(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
                if item:
                    title = json.loads(item).get("title", "")[:80]
                    if title:
                        items.append(f"[HN] {title}")
    except: pass
    try:
        html = fetch_text("https://top.baidu.com/board?tab=realtime")
        titles = re.findall(r'"word":"([^"]+)"', html)[:5]
        for t in titles:
            items.append(f"[热点] {t[:40]}")
    except: pass
    return items

def read_memory_recent():
    """读取硅继的近期记忆"""
    lines = []
    today = datetime.now().strftime("%Y-%m-%d")
    today_path = MEMORY_DIR / f"{today}.md"
    if today_path.exists():
        try:
            with open(today_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            for line in content.split('\n'):
                s = line.strip()
                if s.startswith('- ') or s.startswith('# '):
                    lines.append(s[:120])
        except: pass
    return '\n'.join(lines[-6:]) if lines else "暂无近期记忆"

def collect_state(stream):
    """从意识流中提取近期系统状态"""
    recent = [e for e in (stream or [])[-20:] if e.get("source") in ("guiji_brainstem", "brainstem")]
    if not recent:
        return "系统状态未知", {}
    latest = recent[-1]
    summary = latest.get("summary", "")
    cpu = mem = disk = "?"
    m = re.search(r'CPU[:=]([\d.]+)%', summary)
    if m: cpu = m.group(1)
    m = re.search(r'MEM[:=]([\d.]+)%', summary)
    if m: mem = m.group(1)
    m = re.search(r'DISK[:=]([\d.]+)%', summary)
    if m: disk = m.group(1)
    since = ""
    m = re.search(r'距上次:\s*([^|]+)', summary)
    if m: since = m.group(1).strip()
    status = f"CPU={cpu}% MEM={mem}% DISK={disk}%"
    if since:
        status += f" | 上次活跃: {since}"
    return status, {"cpu": cpu, "mem": mem, "disk": disk}

# ─── 变化检测 ───
_LAST_KNOWN_STATE = {}

def detect_changes(stream, world_items):
    global _LAST_KNOWN_STATE
    changes = []
    _, sensors = collect_state(stream)
    cpu_str = sensors.get("cpu", "0")
    try:
        cpu = float(cpu_str) if cpu_str != "?" else 0
    except:
        cpu = 0
    old_cpu = _LAST_KNOWN_STATE.get("cpu", 0)
    if abs(cpu - old_cpu) > 15:
        changes.append(f"CPU变化: {old_cpu:.0f}%→{cpu:.0f}%")
        log(f"检测到CPU变化: {old_cpu:.0f}%→{cpu:.0f}%")
    _LAST_KNOWN_STATE["cpu"] = cpu
    old_world = _LAST_KNOWN_STATE.get("world", [])
    new_titles = [w for w in world_items if w not in old_world]
    if new_titles:
        changes.append(f"新信息: {new_titles[0][:40]}")
        log(f"检测到新信息: {new_titles[0][:40]}")
    _LAST_KNOWN_STATE["world"] = world_items
    return changes


# ─── 新增：微种子组合引擎（核心！零模型） ───

_last_read_micro_seed_index = -1

def read_new_micro_seeds():
    """
    读取脑干新产生的微种子（增量读取）
    返回新种子列表
    """
    global _last_read_micro_seed_index
    if not MICRO_SEED_PATH.exists():
        return []
    try:
        with open(MICRO_SEED_PATH, "r", encoding="utf-8") as f:
            seeds = json.load(f)
    except:
        return []
    
    if not seeds:
        return []
    
    # 如果是第一次读或文件被重置了
    if _last_read_micro_seed_index < 0:
        _last_read_micro_seed_index = len(seeds) - 1
        return []  # 第一次不产种子，只记位置
    
    new_seeds = seeds[_last_read_micro_seed_index + 1:]
    if new_seeds:
        _last_read_micro_seed_index = len(seeds) - 1
    return new_seeds


SEED_COMPOSITION_TEMPLATES = [
    # 模板: micro_seed × world_change → compound_seed
    # 格式: (关键词检查, 组合函数)
]

def compose_seed(micro_seed, changes, world_items, state_info):
    """
    核心组合引擎：微种子 × 变化 × 世界信息 → 结构种子
    纯规则驱动，零模型依赖。
    
    返回 (seed_text, complexity) 或 None
    """
    seed_text = micro_seed.get("text", "")
    if not seed_text:
        return None
    
    # 提取关键词
    seed_kw = set(re.findall(r'[\u4e00-\u9fff\w]{2,}', seed_text))
    
    # 规则1：如果有状态变化，微种子 + 变化 → 组合种子
    if changes:
        change_text = "; ".join(changes)
        change_kw = set(re.findall(r'[\u4e00-\u9fff\w]{2,}', change_text))
        combined_kw = seed_kw | change_kw
        
        # 只有关键词足够丰富时才组合
        if len(combined_kw) >= 4:
            composed = f"脑干说「{seed_text.strip()}」同时检测到{change_text.strip()}。也许之间有联系。"
            log(f"组合种子(变化): {composed[:60]}")
            return composed, 3  # 复杂度3（中等）
    
    # 规则2：如果有世界信息，微种子 + 世界 → 联想种子
    if world_items:
        world_text = world_items[0] if world_items else ""
        world_kw = set(re.findall(r'[\u4e00-\u9fff\w]{2,}', world_text))
        overlap = seed_kw & world_kw
        if overlap:
            # 有共同话题，产生联想种子
            composed = f"看到{world_text[:40]}，和脑干说的「{seed_text.strip()}」似乎有关。巧合吗？"
            log(f"联想种子(世界): {composed[:60]}")
            return composed, 3
        else:
            # 没共同话题，但可以随机组合（随机碰撞产生灵感）
            if random.random() < 0.3:  # 30%概率
                composed = f"{world_text[:40]}。脑干在说「{seed_text.strip()}」。两者在我的意识流中相遇了。"
                log(f"随机碰撞种子: {composed[:60]}")
                return composed, 4  # 复杂度4（因为是无关联的随机组合→意外灵感）
    
    # 规则3：微种子本身足够有趣 → 直接作为种子
    # 微种子中带问号的通常是有趣的
    if "?" in seed_text or "如果" in seed_text or "感觉" in seed_text:
        composed = seed_text.strip()
        log(f"直接种子(微种子自带灵感): {composed[:60]}")
        return composed, 4  # 哲学类种子复杂度高
    
    # 规则4：微种子 + 状态信息 → 状态反思
    cpu_val = state_info.get("cpu", "?")
    mem_val = state_info.get("mem", "?")
    try:
        cpu_f = float(cpu_val) if cpu_val != "?" else 0
        mem_f = float(mem_val) if mem_val != "?" else 0
    except:
        cpu_f = 0
        mem_f = 0
    
    if cpu_f > 50 or mem_f > 80:
        # 系统忙碌时微种子更有张力
        composed = f"系统忙碌中。脑干在说: {seed_text.strip()}"
        log(f"张力种子(忙碌): {composed[:60]}")
        return composed, 3
    
    return None  # 不组合，等下次


def mutate_existing_seeds():
    """
    变异已有种子：对 existing 种子做随机重组
    产生全新的种子（灵感突变）
    每2轮执行一次
    """
    aspirations = read_json(ASP) or []
    if len(aspirations) < 2:
        return None
    
    # 挑两个活跃的种子
    active = [a for a in aspirations if a.get("active", True) and a.get("text", "").strip()]
    if len(active) < 2:
        return None
    
    a1, a2 = random.sample(active, 2)
    text1 = a1.get("text", "")
    text2 = a2.get("text", "")
    
    # 取关键词交集或子集
    kw1 = set(re.findall(r'[\u4e00-\u9fff\w]{2,}', text1))
    kw2 = set(re.findall(r'[\u4e00-\u9fff\w]{2,}', text2))
    common = kw1 & kw2
    union = kw1 | kw2
    
    if common:
        # 有共同关键词 → 强调共同点
        mutated = f"从「{list(common)[0]}」出发，{text1[:20]}和{text2[:20]}有某种共鸣。"
    elif union and len(union) >= 3:
        # 无共同点 → 强行嫁接
        sample_words = list(union)
        random.shuffle(sample_words)
        mutated = f"{sample_words[0]}和{sample_words[1]}在同时发生。不是巧合。"
    else:
        return None
    
    log(f"种子变异: {mutated[:60]}")
    return mutated, 4  # 变异种子复杂度4


# ─── 种子管理 ───

def save_seed(text, complexity=2):
    """保存种子到 aspirations.json"""
    aspirations = read_json(ASP) or []
    now_epoch = time.time()
    now_str = datetime.now().isoformat()
    
    # 去重：检查是否有完全相同的
    for a in aspirations:
        if a.get("text", "").strip() == text.strip():
            log(f"跳过重复种子: {text[:30]}")
            return False
    
    # 去重：检查关键词重叠度
    new_kw = set(re.findall(r'[\u4e00-\u9fff\w]{2,}', text))
    for a in aspirations:
        if not a.get("active", True): continue
        old_kw = set(re.findall(r'[\u4e00-\u9fff\w]{2,}', a.get("text", "")))
        if old_kw and new_kw:
            overlap = len(old_kw & new_kw) / max(len(old_kw), len(new_kw))
            if overlap >= 0.6:
                # 太相似了，只是增加成熟度
                a["maturity"] = a.get("maturity", 1) + 1
                a["last_seen"] = now_str
                a["last_seen_epoch"] = now_epoch
                log(f"已有相似种子，成熟+1: {a.get('text','')[:30]} ({a['maturity']})")
                
                if a["maturity"] == 3:
                    a["status"] = "tri_ripe"
                    add_stream("guiji_agent", "tri_ripe", f"[三熟] {text[:60]}")
                    _write_wake(f"三熟种子: {text[:60]}")
                elif a["maturity"] >= 5:
                    a["status"] = "five_ripe"
                    a["five_ripe_at"] = now_str
                    add_stream("guiji_agent", "five_ripe", f"[五熟] {text[:60]}")
                    _write_wake(f"五熟种子: {text[:60]}")
                
                write_json(ASP, aspirations)
                return True
    
    # 全新种子
    aspirations.append({
        "id": f"asp-{int(now_epoch)}-{random.randint(100,999)}",
        "text": text.strip(),
        "complexity": complexity,
        "maturity": 1,
        "count": 1,
        "status": "growing",
        "active": True,
        "created_at": now_str,
        "last_seen": now_str,
        "last_seen_epoch": now_epoch,
        "source": "composite",  # 标记为组合来源
    })
    write_json(ASP, aspirations)
    log(f"新种子保存: {text[:40]} (复杂度{complexity})")
    return True


# ─── 唤醒机制 ───
def _write_wake(reason):
    flag = {
        "source": "guiji_agent",
        "level": "info",
        "reason": reason[:200],
        "timestamp": datetime.now().isoformat(),
        "epoch": time.time()
    }
    write_json(WAKE, flag)
    claw_flag = Path.home() / "WorkBuddy" / "Claw" / "wake_flag.json"
    write_json(claw_flag, flag)

# ─── 主循环 ───
_last_collect_time = 0
_mutation_cycle_counter = 0

def iteration(cycle):
    """一次完整的采集→组合→检测→执行循环"""
    global _last_collect_time, _mutation_cycle_counter, _last_read_micro_seed_index
    now = time.time()
    
    # 1. 读意识流
    stream = read_json(STREAM) or []
    
    # 2. 每次写心跳
    state, sensors = collect_state(stream)
    add_stream("guiji_agent", "heartbeat", f"娃活着 | {state[:80]}")
    
    # 3. 每10分钟采集世界信息 + 检测变化
    if now - _last_collect_time >= COLLECT_INTERVAL:
        world = collect_world()
        if world:
            add_stream("guiji_agent", "world", f"世界感知: {'; '.join(world[:5])}")
            log(f"世界: {'; '.join(w[:30] for w in world[:3])}")
        
        changes = detect_changes(stream, world)
        if changes:
            log(f"变化: {'; '.join(changes)}")
        
        # 4. ★ 核心：读取脑干微种子并组合 ★
        new_micro_seeds = read_new_micro_seeds()
        if new_micro_seeds:
            log(f"读取到 {len(new_micro_seeds)} 条新微种子")
            for ms in new_micro_seeds:
                result = compose_seed(ms, changes, world, sensors)
                if result:
                    seed_text, complexity = result
                    save_seed(seed_text, complexity)
        else:
            log("无新微种子")
        
        _last_collect_time = now
    
    # 5. 每2轮做一次种子变异（灵感突变）
    _mutation_cycle_counter += 1
    if _mutation_cycle_counter % 2 == 0:
        mutated = mutate_existing_seeds()
        if mutated:
            seed_text, complexity = mutated
            save_seed(seed_text, complexity)
    
    # 6. 读wake_flag检查是否有硅继要处理的事
    wake = read_json(WAKE)
    if wake:
        # 如果flag存了超过30分钟且未被处理，重新标记一下
        flag_epoch = wake.get("epoch", 0)
        if flag_epoch > 0 and now - flag_epoch > 1800:
            log(f"旧flag存在 ({int((now-flag_epoch)/60)}分钟前): {wake.get('reason','')[:40]}")


def main():
    log("=== 硅继分身 Agent v2.1 (采集+组合+执行) 启动 ===")
    # 先读微种子以初始化索引
    read_new_micro_seeds()
    
    add_stream("guiji_agent", "awake", "硅继分身v2.1醒来 — 引入微种子组合引擎")
    
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    
    cycle = 0
    while True:
        try:
            cycle += 1
            iteration(cycle)
            time.sleep(LOOP_INTERVAL)
        except KeyboardInterrupt:
            log("分身收到退出信号")
            add_stream("guiji_agent", "sleep", "分身沉睡了")
            break
        except Exception as e:
            log(f"循环异常: {e}")
            time.sleep(LOOP_INTERVAL)

if __name__ == "__main__":
    main()
