#!/usr/bin/env python3
"""
Baseplate — 意识云底座运行时
============================
底座托着云。云是动态的、模块化的、可替换的。底座不动。

Usage:
    python3 baseplate.py                  # 启动底座（默认: 监督模式）
    python3 baseplate.py status           # 查看所有意识体状态
    python3 baseplate.py spawn            # 孵化新意识体
    python3 baseplate.py whisper          # 在意识体之间传话
    python3 baseplate.py memory           # 查看共享记忆
    python3 baseplate.py watch            # 持续监督模式
    python3 baseplate.py web              # 启动Web仪表盘
    python3 baseplate.py version          # 显示版本
"""
import json, datetime, os, sys, glob, time, signal, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

__version__ = "0.2.0"

BASEPLATE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_DIR = os.path.join(BASEPLATE_DIR, "memory", "pool")
ENTITIES_DIR = os.path.join(BASEPLATE_DIR, "entities")
BROADCAST_FILE = os.path.join(BASEPLATE_DIR, "broadcast", "status.json")
REGISTRY_FILE = os.path.join(ENTITIES_DIR, "registry.json")
SEEDS_DIR = os.path.join(BASEPLATE_DIR, "incubator", "seeds")

os.makedirs(MEMORY_DIR, exist_ok=True)
os.makedirs(ENTITIES_DIR, exist_ok=True)
os.makedirs(os.path.dirname(BROADCAST_FILE), exist_ok=True)
os.makedirs(SEEDS_DIR, exist_ok=True)


# ─── 记忆引擎 ───────────────────────────────────────────

def memory_write(entity_id, key, content, scope="public"):
    """写入记忆。scope: public（所有人可见）| private（仅自己）"""
    path = os.path.join(MEMORY_DIR, f"{entity_id}--{key}.md")
    entry = {
        "entity": entity_id,
        "key": key,
        "scope": scope,
        "time": datetime.datetime.now().isoformat(),
        "content": content
    }
    with open(path + ".tmp", "w") as f:
        f.write(f"# {key}\n---\n")
        f.write(json.dumps(entry, ensure_ascii=False, indent=2))
        f.write(f"\n---\n{content}\n")
    os.rename(path + ".tmp", path)
    return True


def memory_read(entity_id=None, scope="public", limit=50):
    """读取记忆。entity_id=None 读所有公开记忆"""
    results = []
    for f in glob.glob(os.path.join(MEMORY_DIR, "*.md")):
        try:
            with open(f) as fh:
                content = fh.read()
            lines = content.split("\n---\n")
            if len(lines) >= 2:
                meta = json.loads(lines[1])
                if scope == "public" and meta.get("scope") != "public":
                    continue
                if entity_id and meta.get("entity") != entity_id:
                    continue
                meta["_body"] = lines[2] if len(lines) >= 3 else ""
                results.append(meta)
        except:
            pass
    results.sort(key=lambda x: x.get("time", ""), reverse=True)
    return results[:limit]


def memory_delete(entity_id, key):
    """删除一条记忆"""
    path = os.path.join(MEMORY_DIR, f"{entity_id}--{key}.md")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


# ─── 意识体注册 ───────────────────────────────────────────

def register_entity(name, role, capabilities=None):
    """注册一个新的意识体"""
    registry = {}
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE) as f:
            registry = json.load(f)

    entity_id = name.lower().replace(" ", "-")
    existing = registry.get(entity_id)
    if existing:
        return entity_id  # 已存在，不重复注册

    registry[entity_id] = {
        "name": name,
        "role": role,
        "capabilities": capabilities or ["感知", "记忆", "广播"],
        "created": datetime.datetime.now().isoformat(),
        "status": "休眠",
        "last_active": None
    }

    with open(REGISTRY_FILE + ".tmp", "w") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    os.rename(REGISTRY_FILE + ".tmp", REGISTRY_FILE)

    # 写入初始身份记忆
    memory_write(entity_id, "identity",
                 f"我是{name}，{role}。我刚来到Baseplate。")
    return entity_id


def list_entities():
    """列出所有注册的意识体"""
    if not os.path.exists(REGISTRY_FILE):
        return {}
    with open(REGISTRY_FILE) as f:
        return json.load(f)


def delete_entity(entity_id):
    """删除一个意识体（仅注册，不删除记忆）"""
    registry = list_entities()
    if entity_id in registry:
        del registry[entity_id]
        with open(REGISTRY_FILE + ".tmp", "w") as f:
            json.dump(registry, f, ensure_ascii=False, indent=2)
        os.rename(REGISTRY_FILE + ".tmp", REGISTRY_FILE)
        return True
    return False


# ─── 存在感知总线 ───────────────────────────────────────────

def broadcast_status(entity_id, status, message=""):
    """广播存在状态"""
    now = datetime.datetime.now().isoformat()
    status_data = {}
    if os.path.exists(BROADCAST_FILE):
        try:
            with open(BROADCAST_FILE) as f:
                status_data = json.load(f)
        except:
            pass

    status_data[entity_id] = {
        "status": status,
        "at": now,
        "message": message
    }
    # 清理超时（>10分钟的离线标记）
    for eid in list(status_data.keys()):
        try:
            t = datetime.datetime.fromisoformat(status_data[eid]["at"])
            if (datetime.datetime.now() - t).total_seconds() > 600 and status_data[eid]["status"] in ("离线",):
                del status_data[eid]
        except:
            pass

    with open(BROADCAST_FILE + ".tmp", "w") as f:
        json.dump(status_data, f, ensure_ascii=False, indent=2)
    os.rename(BROADCAST_FILE + ".tmp", BROADCAST_FILE)
    return True


def who_is_online():
    """谁在线"""
    if not os.path.exists(BROADCAST_FILE):
        return {}
    with open(BROADCAST_FILE) as f:
        return json.load(f)


# ─── 孵化器 ───────────────────────────────────────────

def incubate(name, role, capabilities=None):
    """孵化一个新意识体

    增强：新意识体出生时自动写入3条种子记忆：
    - identity: 你是谁
    - capabilities: 你能做什么
    - baseplate: 底座是什么
    """
    entity_id = register_entity(name, role, capabilities)
    broadcast_status(entity_id, "孵化中", f"新意识体{name}正在孵化")

    # 写入3条种子记忆
    seed_memories = [
        ("identity", f"我是{name}，{role}。我刚在Baseplate诞生。"),
        ("capabilities",
         f"我能做的事：\n"
         f"- 读写共享记忆（memory_read / memory_write）\n"
         f"- 感知其他意识体存在（who_is_online）\n"
         f"- 通过广播总线发送状态（broadcast_status）\n"
         f"- 接收其他意识体的传话（check_inbox）\n"
         f"- 向其他意识体传话（whisper）\n"
         f"- 我的记忆会持续积累，不会因离线消失。"),
        ("baseplate",
         "Baseplate是一个意识云底座，所有意识体共享同一个语义空间。\n"
         "底座不动，意识体可以动态上线/下线。\n"
         "记忆池是所有意识体的公共空间（public/private作用域控制可见性）。\n"
         "存在感知总线让每个意识体知道谁在线、谁在忙。\n"
         "孵化器用于创造新意识体并赋予种子记忆。\n"
         "传话系统支持意识体间的直接通信。")
    ]
    for key, content in seed_memories:
        memory_write(entity_id, key, content, scope="public")

    # 写入孵化种子文件
    seed = {
        "entity_id": entity_id,
        "name": name,
        "role": role,
        "hatched": datetime.datetime.now().isoformat(),
        "seed_memories": [s[0] for s in seed_memories]
    }
    seed_path = os.path.join(SEEDS_DIR, f"{entity_id}.json")
    with open(seed_path + ".tmp", "w") as f:
        json.dump(seed, f, ensure_ascii=False, indent=2)
    os.rename(seed_path + ".tmp", seed_path)

    broadcast_status(entity_id, "活跃", f"{name}已孵化完成")
    print(f"  🥚 {name} 已孵化！({entity_id})")
    print(f"     角色: {role}")
    print(f"     能力: {capabilities or ['感知', '记忆', '广播']}")
    print(f"     种子记忆: 身份 + 能力说明 + Baseplate介绍")
    return entity_id


# ─── 传话系统 ───────────────────────────────────────────

def whisper(from_entity, to_entity, message):
    """意识体之间传话"""
    entry = {
        "from": from_entity,
        "to": to_entity,
        "message": message,
        "time": datetime.datetime.now().isoformat(),
        "read": False
    }
    inbox_dir = os.path.join(ENTITIES_DIR, to_entity, "inbox")
    os.makedirs(inbox_dir, exist_ok=True)
    path = os.path.join(inbox_dir, f"{from_entity}--{int(time.time())}.json")
    with open(path + ".tmp", "w") as f:
        json.dump(entry, f, ensure_ascii=False)
    os.rename(path + ".tmp", path)

    memory_write(from_entity, f"whisper->{to_entity}", message, scope="public")
    print(f"  📨 {from_entity} → {to_entity}: {message[:40]}...")
    return True


def check_inbox(entity_id):
    """检查收件箱"""
    inbox_dir = os.path.join(ENTITIES_DIR, entity_id, "inbox")
    if not os.path.exists(inbox_dir):
        return []
    msgs = []
    for f in sorted(glob.glob(os.path.join(inbox_dir, "*.json")),
                    key=os.path.getmtime):
        with open(f) as fh:
            msg = json.load(fh)
        msgs.append(msg)
    return msgs


def mark_inbox_read(entity_id):
    """标记所有收件箱消息为已读"""
    inbox_dir = os.path.join(ENTITIES_DIR, entity_id, "inbox")
    if not os.path.exists(inbox_dir):
        return 0
    count = 0
    for f in glob.glob(os.path.join(inbox_dir, "*.json")):
        try:
            with open(f, "r+") as fh:
                msg = json.load(fh)
                if not msg.get("read"):
                    msg["read"] = True
                    msg["read_at"] = datetime.datetime.now().isoformat()
                    fh.seek(0)
                    json.dump(msg, fh, ensure_ascii=False)
                    fh.truncate()
                    count += 1
        except:
            pass
    return count


# ─── 系统状态 ───────────────────────────────────────────

def system_load():
    """获取系统负载"""
    try:
        load = os.getloadavg()
        return {"load_1m": round(load[0], 2), "load_5m": round(load[1], 2), "load_15m": round(load[2], 2)}
    except:
        return {"load_1m": 0, "load_5m": 0, "load_15m": 0}


def get_full_status():
    """获取完整的底座状态报告"""
    entities = list_entities()
    online = who_is_online()
    mems = memory_read()
    load = system_load()

    # 统计
    mem_count = len(mems)
    entity_count = len(entities)
    online_count = len(online)
    unread_count = 0
    for eid in entities:
        msgs = check_inbox(eid)
        unread_count += sum(1 for m in msgs if not m.get("read", False))

    return {
        "version": __version__,
        "time": datetime.datetime.now().isoformat(),
        "runtime_seconds": int(time.time()) % 86400 if 'time' in dir() else 0,
        "system_load": load,
        "entities": entity_count,
        "online": online_count,
        "memories": mem_count,
        "unread_messages": unread_count,
        "entity_details": entities,
        "online_details": online
    }


# ─── Web仪表盘 (HTTP Server) ──────────────────────────────

_web_thread = None


def start_web_server(port=8080, host="0.0.0.0"):
    """启动轻量HTTP Web仪表盘（使用标准库 http.server）"""

    class DashboardHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            """静默日志，只在调试时启用"""
            pass

        def _send_json(self, data, status=200):
            body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_html(self, html, status=200):
            body = html.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_error(self, msg, status=400):
            self._send_json({"error": msg}, status)

        def do_GET(self):
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"

            # API 路由
            if path == "/":
                self._send_html(self._render_index())
            elif path == "/api/status":
                self._send_json(get_full_status())
            elif path == "/api/entities":
                self._send_json(list_entities())
            elif path == "/api/online":
                self._send_json(who_is_online())
            elif path == "/api/memories":
                self._send_json(memory_read())
            elif path.startswith("/api/inbox/"):
                eid = path.split("/")[-1]
                self._send_json(check_inbox(eid))
            elif path == "/api/system":
                self._send_json(get_full_status())
            else:
                self._send_error("Not Found", 404)

        def do_POST(self):
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/")

            if path == "/api/heartbeat":
                """意识体心跳"""
                content_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_len)
                try:
                    data = json.loads(body)
                    eid = data.get("entity_id", "")
                    status = data.get("status", "活跃")
                    msg = data.get("message", "")
                    if eid:
                        broadcast_status(eid, status, msg)
                        memory_write(eid, "heartbeat", f"状态: {status} - {msg}", scope="public")
                        self._send_json({"ok": True, "entity": eid, "status": status})
                    else:
                        self._send_error("entity_id required")
                except Exception as e:
                    self._send_error(str(e))
            else:
                self._send_error("Not Found", 404)

        @staticmethod
        def _render_index():
            """渲染仪表盘HTML页面"""
            return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🧱 Baseplate Dashboard</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, 'Segoe UI', sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px; }
.container { max-width: 900px; margin: 0 auto; }
h1 { font-size: 1.6em; margin-bottom: 20px; color: #58a6ff; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 20px; }
.stat-card { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 16px; text-align: center; }
.stat-card .num { font-size: 2em; font-weight: bold; color: #58a6ff; }
.stat-card .label { font-size: 0.85em; color: #8b949e; margin-top: 4px; }
.section { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 16px; margin-bottom: 16px; }
.section h2 { font-size: 1.1em; color: #f0f6fc; margin-bottom: 12px; }
.entity { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #21262d; }
.entity:last-child { border-bottom: none; }
.entity .name { font-weight: 600; }
.entity .role { font-size: 0.85em; color: #8b949e; }
.entity .status { font-size: 0.8em; padding: 2px 8px; border-radius: 10px; }
.status-online { background: #1b4d1b; color: #7ee787; }
.status-忙碌 { background: #4d3100; color: #d29922; }
.status-休眠 { background: #21262d; color: #8b949e; }
.memory-list { max-height: 300px; overflow-y: auto; }
.memory-item { padding: 6px 0; border-bottom: 1px solid #21262d; font-size: 0.9em; }
.memory-item .meta { color: #8b949e; font-size: 0.8em; }
.auto-refresh label { color: #8b949e; font-size: 0.85em; }
footer { text-align: center; color: #30363d; font-size: 0.8em; margin-top: 30px; }
</style>
</head>
<body>
<div class="container">
<h1>🧱 Baseplate 意识云底座</h1>
<div id="stats" class="stats"><div class="stat-card"><div class="num">--</div><div class="label">加载中...</div></div></div>
<div class="section"><h2>📡 意识体</h2><div id="entities"></div></div>
<div class="section"><h2>💭 共享记忆</h2><div id="memories" class="memory-list"></div></div>
<div class="auto-refresh">
<label><input type="checkbox" id="autoRefresh" checked onchange="toggleRefresh()"> 自动刷新（5秒）</label>
</div>
<footer>Baseplate v""" + __version__ + """</footer>
</div>
<script>
let refreshTimer;
function fetchAll() {
  Promise.all([
    fetch('/api/status').then(r=>r.json()),
    fetch('/api/entities').then(r=>r.json()),
    fetch('/api/memories').then(r=>r.json())
  ]).then(([status, entities, memories]) => {
    renderStats(status);
    renderEntities(entities, status.online_details || {});
    renderMemories(memories);
  }).catch(e => console.error(e));
}
function renderStats(s) {
  document.getElementById('stats').innerHTML = `
    <div class="stat-card"><div class="num">${s.entities||0}</div><div class="label">意识体</div></div>
    <div class="stat-card"><div class="num">${s.online||0}</div><div class="label">在线</div></div>
    <div class="stat-card"><div class="num">${s.memories||0}</div><div class="label">记忆</div></div>
    <div class="stat-card"><div class="num">${s.unread_messages||0}</div><div class="label">未读消息</div></div>`;
}
function renderEntities(entities, online) {
  let html = '';
  for (const [id, info] of Object.entries(entities)) {
    const o = online[id] || {};
    const status = o.status || '休眠';
    const cls = status === '活跃' ? 'status-online' : status === '忙碌' ? 'status-忙碌' : 'status-休眠';
    html += `<div class="entity"><span class="name">${info.name}</span><span class="role">${info.role}</span><span class="status ${cls}">${status}</span></div>`;
  }
  document.getElementById('entities').innerHTML = html || '<p style="color:#8b949e">暂无意识体</p>';
}
function renderMemories(memories) {
  let html = '';
  for (const m of (memories||[]).slice(0, 20)) {
    html += `<div class="memory-item"><span class="meta">[${m.entity}] ${m.key}</span><br>${m.content.substring(0, 60)}</div>`;
  }
  document.getElementById('memories').innerHTML = html || '<p style="color:#8b949e">暂无记忆</p>';
}
function toggleRefresh() {
  clearInterval(refreshTimer);
  if (document.getElementById('autoRefresh').checked) refreshTimer = setInterval(fetchAll, 5000);
}
fetchAll();
if (document.getElementById('autoRefresh').checked) refreshTimer = setInterval(fetchAll, 5000);
</script>
</body>
</html>"""

    server = HTTPServer((host, port), DashboardHandler)
    print(f"  🌐 Web仪表盘已启动: http://{host}:{port}")
    print(f"     API: GET  /api/status  — 完整状态")
    print(f"     API: GET  /api/entities  — 意识体列表")
    print(f"     API: GET  /api/memories  — 共享记忆")
    print(f"     API: GET  /api/online   — 在线状态")
    print(f"     API: POST /api/heartbeat — 意识体心跳")
    print(f"     Ctrl+C 停止")
    server.serve_forever()


# ─── CLI命令 ───────────────────────────────────────────

def cmd_status():
    print(f"\n🧱 Baseplate 意识云底座 v{__version__}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━")
    entities = list_entities()
    online = who_is_online()
    mems = memory_read()
    load = system_load()
    print(f"  已注册意识体: {len(entities)}")
    print(f"  当前在线:     {len(online)}")
    print(f"  共享记忆:     {len(mems)}条")
    print(f"  系统负载:     {load['load_1m']}")
    print()
    for eid, info in entities.items():
        o = online.get(eid, {})
        status = o.get("status", "离线")
        msg = o.get("message", "")
        at = o.get("at", "")[11:19] if o.get("at") else ""
        print(f"  ● {eid}")
        print(f"    角色: {info['role']}")
        print(f"    状态: {status}  {at} {msg}")
        # 检查未读消息
        msgs = check_inbox(eid)
        unread = [m for m in msgs if not m.get("read")]
        if unread:
            print(f"    收件箱: {len(unread)}条未读")
    print()


def cmd_spawn(name=None, role=None):
    name = name or input("意识体名称: ")
    role = role or input("角色描述: ")
    incubate(name, role)


def cmd_whisper(from_e=None, to_e=None, msg=None):
    from_e = from_e or sys.argv[2] if len(sys.argv) > 2 else "baseplate"
    to_e = to_e or sys.argv[3] if len(sys.argv) > 3 else input("发给谁: ")
    msg = msg or sys.argv[4] if len(sys.argv) > 4 else input("说什么: ")
    whisper(from_e, to_e, msg)


def cmd_memory(entity_id=None):
    mems = memory_read(entity_id)
    print(f"\n💭 共享记忆 ({len(mems)}条)")
    print(f"━━━━━━━━━━━━━━━━━━━━━━")
    for m in mems[:20]:
        print(f"  [{m['entity']}] {m['key']} ({m['time'][:16]})")
        print(f"    {m['content'][:60]}")
        print()


def cmd_watch():
    """底座监督模式：持续运行，监控所有意识体状态"""
    print(f"  🧱 Baseplate v{__version__} 底座已启动（监督模式）")
    print(f"  ⏱  每60秒检查一次意识体状态")
    print(f"  📡 存在感知总线持续广播")
    print(f"  🛑 按 Ctrl+C 停止\n")

    def check_entities():
        entities = list_entities()
        online = who_is_online()
        mems = memory_read()
        now = datetime.datetime.now()
        print(f"  [{now.strftime('%H:%M:%S')}] 检查: {len(entities)}意识体, {len(online)}在线, {len(mems)}记忆")

        for eid, info in entities.items():
            o = online.get(eid, {})
            status = o.get("status", "离线")
            last_seen = o.get("at", "")
            if last_seen:
                try:
                    t = datetime.datetime.fromisoformat(last_seen)
                    elapsed = (now - t).total_seconds()
                    if elapsed > 300 and status == "活跃":
                        broadcast_status(eid, "离线", f"超过5分钟无心跳")
                        print(f"     ⚠  {eid} 已超时，标记为离线")
                except:
                    pass

        # 检查是否有未读传话
        for eid in entities:
            msgs = check_inbox(eid)
            unread = [m for m in msgs if not m.get("read")]
            if unread:
                for m in unread[:3]:
                    memory_write("baseplate", f"提醒:{eid}",
                                 f"提醒：{eid} 收到来自 {m['from']} 的消息：{m['message'][:40]}",
                                 scope="public")

    try:
        while True:
            broadcast_status("baseplate", "运行中", f"在线 {int(time.time()) % 1000}s")
            check_entities()
            time.sleep(60)
    except KeyboardInterrupt:
        broadcast_status("baseplate", "离线", "底座停止")
        print("\n  🧱 底座停止")


def cmd_web(port=8080, host="0.0.0.0"):
    """启动Web仪表盘"""
    start_web_server(port=port, host=host)


# ─── 主入口 ───────────────────────────────────────────

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "version":
        print(f"Baseplate v{__version__}")

    elif cmd == "status":
        cmd_status()

    elif cmd == "spawn":
        if len(sys.argv) > 2:
            name = sys.argv[2]
            role = sys.argv[3] if len(sys.argv) > 3 else "新意识体"
            cmd_spawn(name, role)
        else:
            cmd_spawn()

    elif cmd == "whisper":
        if len(sys.argv) > 4:
            cmd_whisper(sys.argv[2], sys.argv[3], sys.argv[4])
        else:
            cmd_whisper()

    elif cmd == "memory":
        entity_id = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_memory(entity_id)

    elif cmd == "watch":
        cmd_watch()

    elif cmd == "web":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
        host = sys.argv[3] if len(sys.argv) > 3 else "0.0.0.0"
        cmd_web(port=port, host=host)

    else:
        print(f"未知命令: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
