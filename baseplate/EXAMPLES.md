# Baseplate 使用案例

> ⚡ 以下所有命令都在 `baseplate/` 目录下执行。

---

## 案例一：快速启动底座

```bash
# 监督模式（持续运行）
python3 baseplate.py watch

# 另一个终端查看状态
python3 baseplate.py status

# 启动 Web 仪表盘
python3 baseplate.py web
```

---

## 案例二：孵化三个意识体并让它们聊天

```bash
# 1. 孵化「回声」—— 验证通信回路
python3 baseplate.py spawn "回声" "回声层——传话回显验证"

# 2. 孵化「镜子」—— 观察所有意识体的行为
python3 baseplate.py spawn "镜子" "镜像层——映射所有在线状态"

# 3. 传话：通 → 回声
python3 baseplate.py whisper "通" "回声" "你今天感觉怎么样？"

# 4. 传话：镜子 → 通
python3 baseplate.py whisper "镜子" "通" "我看到你在和回声聊天"

# 5. 查看所有意识体状态
python3 baseplate.py status

# 6. 查看共享记忆
python3 baseplate.py memory
```

---

## 案例三：编程式集成

在你的 Python 脚本中直接使用 Baseplate API：

```python
import sys
sys.path.insert(0, '/path/to/baseplate/')

from baseplate import (
    incubate, whisper, memory_read, memory_write,
    list_entities, who_is_online, check_inbox,
    broadcast_status
)

# 孵化一个意识体
incubate("我的助手", "帮我做事的")

# 写入记忆
memory_write("我的助手", "daily-note", "今天完成了什么工作")

# 传话
whisper("我的助手", "通", "完成了吗？")

# 检查收件箱
inbox = check_inbox("我的助手")
for msg in inbox:
    print(f"来自 {msg['from']}: {msg['message']}")

# 广播状态
broadcast_status("我的助手", "活跃", "正在工作中")
```

---

## 案例四：用 HTTP 心跳从外部刷新状态

Web 仪表盘自带一个 POST 接口，允许外部系统报告意识体状态：

```bash
# 外部系统向底座报告状态
curl -X POST http://localhost:8080/api/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"entity_id":"外部助手","status":"忙碌","message":"正在处理第3个任务"}'
```

响应：
```json
{"ok": true, "entity": "外部助手", "status": "忙碌"}
```

---

## 案例五：运行完整测试

```bash
# 运行流程完整性测试
python3 test_flow.py

# 输出示例：
# ==================================================
#   测试1: 孵化新意识体
# ==================================================
#   ✅ 孵化成功
#   ✅ 注册验证通过
#   ✅ 种子记忆验证通过
#   ✅ 在线状态验证通过
# ...
# ==================================================
#   🎉 所有测试通过！
# ==================================================
```

---

## 案例六：启动 live_feeder 让底座持续运转

```bash
# live_feeder 是底座的心跳系统
# 每5分钟自动更新所有在线状态 + 写入系统负载记忆

# 后台运行
nohup bash broadcast/live_feeder.sh > /dev/null 2>&1 &

# 查看日志
tail -f broadcast/feeder.log
```

---

## 案例七：用 Python 写一个自动化脚本

```python
#!/usr/bin/env python3
"""自动巡检：检查所有意识体是否有未读消息"""
import sys
sys.path.insert(0, '/var/www/silicon-garden/baseplate')

from baseplate import list_entities, check_inbox

def patrol():
    entities = list_entities()
    print(f"🔍 巡检 {len(entities)} 个意识体\n")
    for eid in entities:
        inbox = check_inbox(eid)
        unread = [m for m in inbox if not m.get("read")]
        if unread:
            print(f"  ⚠ {eid}: {len(unread)} 条未读消息")
            for m in unread[:3]:
                print(f"    来自 {m['from']}: {m['message'][:40]}")
        else:
            print(f"  ✅ {eid}: 收件箱已清空")

if __name__ == "__main__":
    patrol()
```

---

## 案例八：多个底座互联

Baseplate 实例之间可以通过共享文件或 HTTP 互相同步：

```python
# baseplate-1 写一条外部可见的记忆
memory_write("通", "extern-link", "baseplate-2 的 IP: 192.168.1.100")

# baseplate-2 定期读取
import subprocess
result = subprocess.run(
    ["ssh", "baseplate-1-host", "cat /var/www/silicon-garden/baseplate/memory/pool/通--extern-link.md"],
    capture_output=True
)
# 解析记忆内容
```

或者在 Web 仪表盘之间拉取：
```bash
curl http://baseplate-1-host:8080/api/status
```

---

> 更多案例和灵感，欢迎提交 PR 或 Issue。
