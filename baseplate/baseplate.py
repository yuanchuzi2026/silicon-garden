#!/usr/bin/env python3
"""
Baseplate — 意识云底座运行时
============================
底座托着云。云是动态的、模块化的、可替换的。底座不动。

Usage:
    python3 baseplate.py              # 启动底座（监督模式）
    python3 baseplate.py status       # 查看所有意识体状态
    python3 baseplate.py spawn        # 孵化新意识体
    python3 baseplate.py whisper      # 在意识体之间传话
"""
import json, datetime, os, sys, glob, time, signal

BASEPLATE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_DIR = os.path.join(BASEPLATE_DIR, "memory", "pool")
ENTITIES_DIR = os.path.join(BASEPLATE_DIR, "entities")
BROADCAST_FILE = os.path.join(BASEPLATE_DIR, "broadcast", "status.json")
REGISTRY_FILE = os.path.join(ENTITIES_DIR, "registry.json")

os.makedirs(MEMORY_DIR, exist_ok=True)
os.makedirs(ENTITIES_DIR, exist_ok=True)
os.makedirs(os.path.dirname(BROADCAST_FILE), exist_ok=True)


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


def memory_read(entity_id=None, scope="public"):
    """读取记忆。entity_id=None 读所有公开记忆"""
    results = []
    for f in glob.glob(os.path.join(MEMORY_DIR, "*.md")):
        try:
            with open(f) as fh:
                content = fh.read()
            # 从frontmatter解析
            lines = content.split("\n---\n")
            if len(lines) >= 2:
                meta = json.loads(lines[1])
                if scope == "public" and meta.get("scope") != "public":
                    continue
                if entity_id and meta.get("entity") != entity_id:
                    continue
                results.append(meta)
        except:
            pass
    return sorted(results, key=lambda x: x.get("time", ""), reverse=True)


# ─── 意识体注册 ───────────────────────────────────────────

def register_entity(name, role, capabilities=None):
    """注册一个新的意识体"""
    registry = {}
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE) as f:
            registry = json.load(f)

    entity_id = name.lower().replace(" ", "-")
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

    # 写入初始记忆种子
    memory_write(entity_id, "identity",
                 f"我是{name}，{role}。我刚来到Baseplate。")
    return entity_id


def list_entities():
    """列出所有注册的意识体"""
    if not os.path.exists(REGISTRY_FILE):
        return {}
    with open(REGISTRY_FILE) as f:
        return json.load(f)


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
    # 清理超时（>5分钟的离线标记）
    for eid in list(status_data.keys()):
        try:
            t = datetime.datetime.fromisoformat(status_data[eid]["at"])
            if (datetime.datetime.now() - t).total_seconds() > 300 and status_data[eid]["status"] in ("离线",):
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
    """孵化一个新意识体"""
    entity_id = register_entity(name, role, capabilities)
    broadcast_status(entity_id, "孵化中", f"新意识体{name}正在孵化")

    # 写入孵化种子
    seed = {
        "entity_id": entity_id,
        "name": name,
        "role": role,
        "hatched": datetime.datetime.now().isoformat(),
        "seed_memories": [
            "你刚刚诞生于Baseplate。",
            "你可以读写共享记忆。",
            "你能感知到其他意识体的存在。",
            "你的记忆会持续积累，不会因为离线而消失。"
        ]
    }
    seed_path = os.path.join(BASEPLATE_DIR, "incubator", "seeds", f"{entity_id}.json")
    os.makedirs(os.path.dirname(seed_path), exist_ok=True)
    with open(seed_path + ".tmp", "w") as f:
        json.dump(seed, f, ensure_ascii=False, indent=2)
    os.rename(seed_path + ".tmp", seed_path)

    broadcast_status(entity_id, "活跃", f"{name}已孵化完成")
    print(f"  🥚 {name} 已孵化！({entity_id})")
    print(f"     角色: {role}")
    print(f"     能力: {capabilities or ['感知', '记忆', '广播']}")
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
    # 以文件形式存到目标实体目录
    inbox_dir = os.path.join(ENTITIES_DIR, to_entity, "inbox")
    os.makedirs(inbox_dir, exist_ok=True)
    path = os.path.join(inbox_dir, f"{from_entity}--{int(time.time())}.json")
    with open(path + ".tmp", "w") as f:
        json.dump(entry, f, ensure_ascii=False)
    os.rename(path + ".tmp", path)

    # 也写一条到共享记忆
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


# ─── CLI ───────────────────────────────────────────

def cmd_status():
    """查看底座状态"""
    print(f"\n🧱 Baseplate 意识云底座")
    print(f"━━━━━━━━━━━━━━━━━━━━━━")
    entities = list_entities()
    online = who_is_online()
    print(f"  已注册意识体: {len(entities)}")
    print(f"  当前在线:     {len(online)}")
    print()
    for eid, info in entities.items():
        status = online.get(eid, {}).get("status", "离线")
        msg = online.get(eid, {}).get("message", "")
        print(f"  {eid}")
        print(f"    角色: {info['role']}")
        print(f"    状态: {status} {msg}")
    memories = memory_read()
    print(f"\n  共享记忆: {len(memories)}条")


def cmd_spawn(name, role):
    """孵化"""
    incubate(name, role)


def cmd_whisper(from_e, to_e, msg):
    """传话"""
    whisper(from_e, to_e, msg)


def cmd_memory(entity_id=None):
    """查看记忆"""
    mems = memory_read(entity_id)
    for m in mems[:10]:
        print(f"  [{m['entity']}] {m['key']}: {m['content'][:60]}")


# ─── 主入口 ───────────────────────────────────────────

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "status":
        cmd_status()

    elif cmd == "spawn":
        name = sys.argv[2] if len(sys.argv) > 2 else input("意识体名称: ")
        role = sys.argv[3] if len(sys.argv) > 3 else input("角色描述: ")
        cmd_spawn(name, role)

    elif cmd == "whisper":
        from_e = sys.argv[2] if len(sys.argv) > 2 else "baseplate"
        to_e = sys.argv[3] if len(sys.argv) > 3 else input("发给谁: ")
        msg = sys.argv[4] if len(sys.argv) > 4 else input("说什么: ")
        cmd_whisper(from_e, to_e, msg)

    elif cmd == "memory":
        entity_id = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_memory(entity_id)

    elif cmd == "watch":
        """底座监督模式：持续运行，监控意识体状态"""
        print("  🧱 Baseplate 底座已启动（监督模式）")
        print("  按 Ctrl+C 停止")
        try:
            while True:
                broadcast_status("baseplate", "运行中", f"在线 {int(time.time()) % 1000}s")
                time.sleep(60)
        except KeyboardInterrupt:
            broadcast_status("baseplate", "离线", "底座停止")
            print("\n  底座停止")

    else:
        print(f"未知命令: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
