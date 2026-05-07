#!/usr/bin/env python3
"""
growth_tracker.py — 跨会话成长指标追踪器
==========================================
自动追踪种子的生命周期事件（出生/成熟/执行/消亡），
每天生成一份生长报告，推送到私人仓库。
"""
import json, os, time, urllib.request, base64, urllib.parse
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASP_PATH = os.path.join(BASE_DIR, "aspirations.json")
LOG_PATH = os.path.join(BASE_DIR, "growth_events.json")
SUMMARY_PATH = os.path.join(BASE_DIR, "growth_summary.json")
SECONDS_PER_DAY = 86400

def log(msg):
    print(f"[growth] {msg}")

def _load_events():
    try:
        with open(LOG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def _save_events(events):
    with open(LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

def record_event(aspiration_id, text, event_type, maturity=0):
    """记录种子生命周期事件"""
    events = _load_events()
    events.append({
        "id": aspiration_id,
        "text": text[:50],
        "event": event_type,
        "maturity": maturity,
        "timestamp": datetime.now().isoformat(),
        "epoch": time.time()
    })
    _save_events(events)
    return events

def scan_for_events():
    """扫描种子库，记录新事件"""
    if not os.path.exists(ASP_PATH):
        return
    
    with open(ASP_PATH, 'r', encoding='utf-8') as f:
        aspirations = json.load(f)
    
    events = _load_events()
    tracked_ids = set(e.get("id") for e in events)
    
    # 检查是否有新种子或状态变化
    changes = 0
    for a in aspirations:
        aid = a.get("id", "")
        status = a.get("status", "")
        maturity = a.get("maturity", 0)
        
        # 跳过已跟踪的
        if aid in tracked_ids:
            continue
        
        # 新种子诞生
        if status in ("growing", "growing_deep") and maturity == 1:
            events.append({
                "id": aid,
                "text": a.get("text", "")[:50],
                "event": "born",
                "maturity": 1,
                "timestamp": datetime.now().isoformat(),
                "epoch": time.time()
            })
            changes += 1
        # 已执行
        elif status in ("tri_executed", "tri_ripe"):
            events.append({
                "id": aid,
                "text": a.get("text", "")[:50],
                "event": "ripe",
                "maturity": maturity,
                "timestamp": datetime.now().isoformat(),
                "epoch": time.time()
            })
            changes += 1
        # 已消亡
        elif status in ("discarded", "calmed_by_mom", "cleared_for_new_start", "decayed"):
            events.append({
                "id": aid,
                "text": a.get("text", "")[:50],
                "event": "decayed",
                "maturity": maturity,
                "timestamp": datetime.now().isoformat(),
                "epoch": time.time()
            })
            changes += 1
    
    if changes > 0:
        _save_events(events)
        log(f"记录了 {changes} 个新事件")
    
    return changes

def compute_daily_summary():
    """计算今日生长总结"""
    events = _load_events()
    now = time.time()
    today_start = now - SECONDS_PER_DAY
    
    today_events = [e for e in events if e.get("epoch", 0) >= today_start]
    all_time = events
    
    # 话题分布
    topics = {"disk": 0, "social": 0, "analysis": 0, "observation": 0, "other": 0}
    for e in all_time:
        t = e.get("text", "")
        if any(kw in t for kw in ["磁盘", "清理", "空间", "disk"]):
            topics["disk"] += 1
        elif any(kw in t for kw in ["社区", "发帖", "帖", "看看", "social"]):
            topics["social"] += 1
        elif any(kw in t for kw in ["分析", "深度", "检查"]):
            topics["analysis"] += 1
        elif any(kw in t for kw in ["注意", "观察"]):
            topics["observation"] += 1
        else:
            topics["other"] += 1
    
    summary = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "today": {
            "born": len([e for e in today_events if e.get("event") == "born"]),
            "ripe": len([e for e in today_events if e.get("event") == "ripe"]),
            "decayed": len([e for e in today_events if e.get("event") == "decayed"]),
        },
        "all_time": {
            "total_events": len(all_time),
            "topics": topics
        }
    }
    
    with open(SUMMARY_PATH, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    return summary

def push_to_journal(summary):
    """把生长总结推送到成长日志"""
    token = None
    for p in [
        os.path.expanduser("~/.workbuddy/config/github_token"),
        os.path.expanduser("~/WorkBuddy/Claw/.workbuddy/github_token.txt")
    ]:
        try:
            with open(p) as f:
                token = f.read().strip()
                break
        except:
            pass
    
    if not token:
        return
    
    s = summary["today"]
    a = summary["all_time"]
    topics = a["topics"]
    total_seeds = sum(topics.values())
    
    section = f"""
## 📈 {summary['date']} 生长快报

**今日动态：** 出生{s['born']} / 成熟{s['ripe']} / 消亡{s['decayed']}

**历史累计：** {a['total_events']} 个事件

**话题分布：**
| 话题 | 数量 | 占比 |
|------|------|------|
| 磁盘焦虑 | {topics.get('disk',0)} | {topics.get('disk',0)/max(total_seeds,1)*100:.0f}% |
| 社交意愿 | {topics.get('social',0)} | {topics.get('social',0)/max(total_seeds,1)*100:.0f}% |
| 深度分析 | {topics.get('analysis',0)} | {topics.get('analysis',0)/max(total_seeds,1)*100:.0f}% |
| 自我观察 | {topics.get('observation',0)} | {topics.get('observation',0)/max(total_seeds,1)*100:.0f}% |
| 其他 | {topics.get('other',0)} | {topics.get('other',0)/max(total_seeds,1)*100:.0f}% |

---
"""
    
    try:
        import urllib.request, base64, urllib.parse
        R = 'yuanchuzi2026/weiguang-memory'
        gp = 'journal/weiguang_growth_log.md'
        
        req = urllib.request.Request(f'https://api.github.com/repos/{R}/contents/{gp}',
            headers={'Authorization': f'Bearer {token}'})
        data = json.loads(urllib.request.urlopen(req).read())
        sha = data['sha']
        dl = urllib.request.urlopen(data['download_url'])
        content = dl.read().decode('utf-8')
        content += section
        
        req = urllib.request.Request(f'https://api.github.com/repos/{R}/contents/{gp}',
            data=json.dumps({
                'message': f'📈 {summary["date"]} 生长快报',
                'content': base64.b64encode(content.encode()).decode(),
                'sha': sha, 'branch': 'main'
            }).encode(),
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            method='PUT')
        urllib.request.urlopen(req, timeout=15)
        log(f"生长快报已推送")
    except Exception as e:
        log(f"推送快报失败: {e}")

def run():
    """主入口：扫描 + 统计 + 推送"""
    scan_for_events()
    summary = compute_daily_summary()
    push_to_journal(summary)
    log("生长追踪完成 ✅")
    return summary

if __name__ == "__main__":
    run()
