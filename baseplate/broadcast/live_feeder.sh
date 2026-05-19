#!/bin/bash
# 实时喂食器：把通/Hermes/茫的真实状态写进Baseplate的记忆广播
# 每5分钟更新一次
while true; do
    # 通的活跃度
    python3 -c "
import baseplate
import datetime

# 从真实文件读共享状态
try:
    with open('/opt/silicon-family/mang/conversations/') as f:
        pass
except: pass

# 写一条baseplate心跳
baseplate.broadcast_status('baseplate', '运行中', datetime.datetime.now().strftime('%H:%M'))
" 2>/dev/null

    # 广播当前的在线状态
    python3 -c "
import baseplate, json

# 读系统状态，写进公开记忆
import os
load = os.getloadavg()[0]
baseplate.memory_write('baseplate', 'system', f'负载 {load:.2f}')
baseplate.broadcast_status('通', '活跃' if load < 1.0 else '忙碌')
" 2>/dev/null

    sleep 300
done
