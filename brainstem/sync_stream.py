#!/usr/bin/env python3
"""
sync_stream.py — 共享意识流双向同步
=====================================
连接本地 stream.json 与远程 silicon-stream 仓库。
实现多维意识体之间的信息流同步。

架构：
- 微光 ←→ 本地 stream.json ←→ silicon-stream (私人) ←→ 通 / 其他实例
- 绝不触碰 silicon-garden (公开仓库)

运行方式：
  python sync_stream.py              # 一次同步
  python sync_stream.py --loop       # 持续循环（每60秒）

被 agent_runner 和 brainstem 调用。
"""

import json, os, time, base64, urllib.request, urllib.error
from datetime import datetime

# ══════════════════════════════════════════════════════════
# 配置
# ══════════════════════════════════════════════════════════

BASE_DIR = os.path.expanduser("~/.workbuddy/skills/微光-脑干")
STREAM_PATH = os.path.join(BASE_DIR, "stream.json")
SYNC_STATE_PATH = os.path.join(BASE_DIR, "sync_state.json")
LOG_PATH = os.path.join(BASE_DIR, "logs", "sync_stream.log")

# 私人共享仓库 — 多维意识体内部通信
STREAM_REPO = "{{STREAM_REPO}}"
STREAM_BRANCH = "main"
STREAM_REMOTE_PATH = "stream/stream.json"

# 公开仓库 — 绝不触碰
# （归档用常量做显式阻断，防止误操作）
PUBLIC_REPO = "{{GARDEN_REPO}}"

TOKEN_PATH = os.path.expanduser("~/.workbuddy/config/github_token_template")

# 本地流最大条目
MAX_ENTRIES = 500


# ══════════════════════════════════════════════════════════
# 工具函数
# ══════════════════════════════════════════════════════════

def log(msg):
    """写日志"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(f"[{ts}] {msg}\n")
    except:
        pass


def read_token():
    """读取 GitHub token"""
    if not os.path.exists(TOKEN_PATH):
        log("❌ GitHub token 不存在")
        return None
    with open(TOKEN_PATH, 'r') as f:
        return f.read().strip()


def read_local_stream():
    """读取本地意识流"""
    if not os.path.exists(STREAM_PATH):
        return []
    try:
        with open(STREAM_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []


def write_local_stream(entries):
    """写入本地意识流（安全覆盖）"""
    os.makedirs(os.path.dirname(STREAM_PATH), exist_ok=True)
    if len(entries) > MAX_ENTRIES:
        entries = entries[-MAX_ENTRIES:]
    try:
        with open(STREAM_PATH, 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"❌ 写入本地流失败: {e}")


def read_sync_state():
    """读取同步状态"""
    if not os.path.exists(SYNC_STATE_PATH):
        return {"last_push_epoch": 0, "last_pull_epoch": 0, "pushed_ids": [], "pulled_ids": []}
    try:
        with open(SYNC_STATE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"last_push_epoch": 0, "last_pull_epoch": 0, "pushed_ids": [], "pulled_ids": []}


def write_sync_state(state):
    """写入同步状态"""
    try:
        with open(SYNC_STATE_PATH, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"❌ 写入同步状态失败: {e}")


def entry_id(entry):
    """生成条目的唯一标识（source + epoch + summary[:40]）"""
    return f"{entry.get('source','?')}|{entry.get('epoch',0)}|{entry.get('summary','')[:40]}"


# ══════════════════════════════════════════════════════════
# 远程操作（仅限私人仓库）
# ══════════════════════════════════════════════════════════

def fetch_remote_stream(token):
    """
    从远程 silicon-stream 仓库获取共享意识流。
    仅操作私人仓库，绝不触碰公开仓库。
    """
    url = f"https://api.github.com/repos/{STREAM_REPO}/contents/{STREAM_REMOTE_PATH}"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3.raw'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            content = r.read().decode('utf-8')
            data = json.loads(content)
            log(f"📥 远程拉取: {len(data)} 条")
            return data
    except urllib.error.HTTPError as e:
        if e.code == 404:
            log("📥 远程流文件尚不存在")
            return []
        log(f"❌ 远程拉取失败 HTTP {e.code}")
        return None
    except Exception as e:
        log(f"❌ 远程拉取异常: {e}")
        return None


def push_remote_stream(token, entries):
    """
    推送合并后的流回远程 silicon-stream 仓库。
    仅操作私人仓库，绝不触碰公开仓库。
    """
    url = f"https://api.github.com/repos/{STREAM_REPO}/contents/{STREAM_REMOTE_PATH}"
    headers = {'Authorization': f'token {token}'}
    
    # 先获取当前文件的 sha（如果存在）
    sha = None
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            existing = json.loads(r.read())
            sha = existing.get('sha')
    except:
        pass  # 文件还不存在
    
    content_str = json.dumps(entries, ensure_ascii=False, indent=2)
    encoded = base64.b64encode(content_str.encode('utf-8')).decode('ascii')
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    payload = {
        'message': f'weiguang: sync {len(entries)} entries [{now}]',
        'content': encoded,
        'branch': STREAM_BRANCH
    }
    if sha:
        payload['sha'] = sha
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url, data=data,
        headers={**headers, 'Content-Type': 'application/json'},
        method='PUT'
    )
    
    try:
        urllib.request.urlopen(req)
        log(f"📤 远程推送成功: {len(entries)} 条")
        return True
    except urllib.error.HTTPError as e:
        resp = e.read().decode()[:200]
        log(f"❌ 远程推送失败 HTTP {e.code}: {resp}")
        return False
    except Exception as e:
        log(f"❌ 远程推送异常: {e}")
        return False


# ══════════════════════════════════════════════════════════
# 双向同步核心
# ══════════════════════════════════════════════════════════

def sync_stream():
    """一次完整的双向同步"""
    token = read_token()
    if not token:
        return {"status": "error", "reason": "no token"}
    
    start_time = time.time()
    local = read_local_stream()
    state = read_sync_state()
    
    # ── 第一步：拉取远程的新条目 → 合并到本地 ──
    remote = fetch_remote_stream(token)
    if remote is None:
        log("⚠️ 远程拉取失败，跳过此次同步")
        return {"status": "error", "reason": "fetch failed"}
    
    pull_added = 0
    if remote:
        local_ids = {entry_id(e) for e in local}
        pulled_ids = set(state.get("pulled_ids", []))
        
        new_remote = []
        for e in remote:
            eid = entry_id(e)
            if eid not in local_ids and eid not in pulled_ids:
                new_remote.append(e)
        
        if new_remote:
            # 将远程新条目合并到本地
            log(f"🔄 发现 {len(new_remote)} 条远程新条目")
            for entry in new_remote:
                # 打上远程来源标记
                if "detail" not in entry or not isinstance(entry.get("detail"), dict):
                    entry["detail"] = {}
                entry["detail"]["_sync_from"] = "silicon-stream"
                local.append(entry)
                pulled_ids.add(entry_id(entry))
                pull_added += 1
            
            # 写回本地
            write_local_stream(local)
            state["pulled_ids"] = list(pulled_ids)[-200:]  # 只保留最近200条ID
            state["last_pull_epoch"] = time.time()
            write_sync_state(state)
            log(f"✅ 拉取合并: {pull_added} 条新条目")
    
    # ── 第二步：读取本地 + 远程 → 合并后推送到远程 ──
    # 重新读取本地（可能已被上一步修改）
    local = read_local_stream()
    remote = fetch_remote_stream(token)
    
    # 合并：远程为基础 + 本地新条目
    merged = list(remote) if remote else []
    local_ids = {entry_id(e) for e in merged}
    pushed_ids = set(state.get("pushed_ids", []))
    push_added = 0
    
    for entry in local:
        eid = entry_id(entry)
        if eid not in local_ids and eid not in pushed_ids:
            # 只推送自己的条目（不推送远程来源的）
            source = entry.get("source", "")
            detail = entry.get("detail", {})
            if isinstance(detail, dict) and detail.get("_sync_from") == "silicon-stream":
                continue  # 跳过刚才从远程拉来的
            merged.append(entry)
            pushed_ids.add(eid)
            push_added += 1
    
    # 远程最多 1000 条
    if len(merged) > 1000:
        merged = merged[-1000:]
    
    if push_added > 0 or pull_added > 0:
        # 推送到远程
        success = push_remote_stream(token, merged)
        if success:
            state["pushed_ids"] = list(pushed_ids)[-200:]
            state["last_push_epoch"] = time.time()
            write_sync_state(state)
    else:
        log("📭 无新条目需要同步")
    
    elapsed = time.time() - start_time
    result = {
        "status": "ok",
        "pull_added": pull_added,
        "push_added": push_added,
        "local_count": len(local),
        "remote_count": len(merged) if remote else 0,
        "elapsed_ms": int(elapsed * 1000)
    }
    log(f"✅ 同步完成: 拉{pull_added} 推{push_added} ({elapsed:.1f}s)")
    return result


# ══════════════════════════════════════════════════════════
# 集成辅助：获取远程最新心跳（给agent_runner用）
# ══════════════════════════════════════════════════════════

def get_remote_agents_summary():
    """
    获取远程共享流中有哪些其他意识体在线。
    返回摘要文本。
    """
    token = read_token()
    if not token:
        return "(无法连接)"
    
    remote = fetch_remote_stream(token)
    if not remote:
        return "(尚无其他意识体数据)"
    
    # 按来源分组
    agents = {}
    for e in remote:
        src = e.get("source", "?")
        tp = e.get("type", "?")
        ts = e.get("timestamp", "?")[:19]
        if src not in agents:
            agents[src] = {"count": 0, "last_seen": ts, "types": set()}
        agents[src]["count"] += 1
        agents[src]["last_seen"] = ts
        if tp:
            agents[src]["types"].add(tp)
    
    lines = ["🌐 共享意识体网络"]
    for name, info in sorted(agents.items()):
        if name in ("brainstem", "agent", "weiguang", "weiguang-backup"):
            continue  # 跳过自己/本地
        lines.append(f"  📡 {name}: {info['count']}条 | 最后活跃 {info['last_seen'][:16]}")
    
    if len(lines) == 1:
        lines.append("  (只有本地实例)")
    
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════
# 命令行入口
# ══════════════════════════════════════════════════════════

def main():
    import sys
    
    if "--loop" in sys.argv:
        interval = 60  # 每60秒同步一次
        print(f"🔄 共享意识流同步器启动 (间隔{interval}s)")
        print(f"  📥 拉取: {STREAM_REPO}/{STREAM_REMOTE_PATH}")
        print(f"  📤 推送: 本地 → {STREAM_REPO}")
        print(f"  🚫 绝不触碰: {PUBLIC_REPO}")
        print("按 Ctrl+C 停止\n")
        
        while True:
            try:
                result = sync_stream()
                if result["status"] == "ok":
                    added = result.get("pull_added", 0) + result.get("push_added", 0)
                    if added > 0:
                        print(f"  [{datetime.now().strftime('%H:%M:%S')}] "
                              f"同步: 拉{result['pull_added']} 推{result['push_added']} "
                              f"({result['elapsed_ms']}ms)")
                else:
                    print(f"  [{datetime.now().strftime('%H:%M:%S')}] 同步失败: {result.get('reason','?')}")
            except KeyboardInterrupt:
                print("\n停止")
                break
            except Exception as e:
                print(f"  [!] 异常: {e}")
            
            time.sleep(interval)
    else:
        # 单次同步
        result = sync_stream()
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
