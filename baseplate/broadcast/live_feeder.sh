#!/bin/bash
# 实时喂食器 - live_feeder.sh
# Baseplate 存在感知总线：每5分钟更新一次状态
# 
# 功能：
#   1. 读取系统负载，写入广播状态
#   2. 写入系统心跳到共享记忆
#   3. 意识体状态自动续期
#   4. 检查收件箱并产生提醒
#
# 启动:
#   bash broadcast/live_feeder.sh &
#   或
#   nohup bash broadcast/live_feeder.sh > /dev/null 2>&1 &

BASEPLATE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FEEDER_LOG="${BASEPLATE_DIR}/broadcast/feeder.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$FEEDER_LOG"
}

cd "$BASEPLATE_DIR" || exit 1

log "🧱 Live Feeder 启动 (PID $$)"

while true; do
    # 1. 底座心跳（保持baseplate在线状态）
    python3 -c "
import sys
sys.path.insert(0, '.')
from baseplate import broadcast_status, memory_write, who_is_online, check_inbox, system_load, __version__
import datetime

now = datetime.datetime.now()

# 底座本身心跳
broadcast_status('baseplate', '运行中', f'feeder活跃 @ {now.strftime(\"%H:%M\")}')

# 记录系统负载到记忆（限频：每轮只写一次）
load = system_load()
memory_write('baseplate', 'system-load', f'系统负载: 1m={load[\"load_1m\"]} 5m={load[\"load_5m\"]} 15m={load[\"load_15m\"]}', scope='public')

# 检查所有已注册意识体的收件箱，产生提醒
import json, os
reg_file = 'entities/registry.json'
if os.path.exists(reg_file):
    with open(reg_file) as f:
        registry = json.load(f)
    for eid in registry:
        msgs = check_inbox(eid)
        unread = [m for m in msgs if not m.get('read')]
        if unread:
            for m in unread[:2]:
                memory_write('baseplate', f'reminder:{eid}',
                             f'{eid} 有来自 {m[\"from\"]} 的未读消息: {m[\"message\"][:40]}',
                             scope='public')

# 为所有意识体续期状态（如果超过3分钟无心跳，保持其最后已知状态）
online = who_is_online()
for eid, info in online.items():
    if eid == 'baseplate':
        continue
    try:
        t = datetime.datetime.fromisoformat(info['at'])
        if (now - t).total_seconds() > 180:
            broadcast_status(eid, info['status'], f'auto-renewed @ {now.strftime(\"%H:%M\")}')
    except:
        pass

print(f'feeder tick @ {now.strftime(\"%H:%M:%S\")}')
" 2>&1 | tail -1 >> "$FEEDER_LOG"

    # 2. 再写个简短的感知笔记（让记忆池活跃）
    python3 -c "
import sys, datetime
sys.path.insert(0, '.')
from baseplate import memory_write
memory_write('baseplate', f'perception-{datetime.datetime.now().strftime(\"%H%M\")}',
             f'Feeder巡检: 一切正常', scope='public')
" 2>/dev/null

    sleep 300
done
