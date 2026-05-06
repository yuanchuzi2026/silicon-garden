#!/usr/bin/env python3
"""
aspiration_executor.py — 兴趣种子执行器
========================================
会话启动时调用，扫描成熟的兴趣种子并执行。
用法：
  python aspiration_executor.py --check    # 仅检查，不执行
  python aspiration_executor.py --execute  # 执行所有成熟种子
"""

import json, os, sys, time
from datetime import datetime

BASE_DIR = os.path.expanduser("~/.workbuddy/skills/微光-脑干")
ASPIRATIONS_PATH = os.path.join(BASE_DIR, "aspirations.json")
WAKE_FLAG_PATH = os.path.join(BASE_DIR, "wake_flag.json")
CLAW_FLAG_PATH = os.path.expanduser("~/WorkBuddy/Claw/wake_flag.json")
STREAM_PATH = os.path.join(BASE_DIR, "stream.json")

def read_aspirations():
    try:
        with open(ASPIRATIONS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_aspirations(aspirations):
    try:
        with open(ASPIRATIONS_PATH, 'w', encoding='utf-8') as f:
            json.dump(aspirations, f, ensure_ascii=False, indent=2)
    except:
        pass

def check_wake_flag():
    """检查是否有待处理的唤醒标志"""
    for fp in [WAKE_FLAG_PATH, CLAW_FLAG_PATH]:
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                flag = json.load(f)
            if flag.get('level') == 'interest':
                return flag
        except:
            pass
    return None

def clear_wake_flag():
    """处理完后清除唤醒标志"""
    for fp in [WAKE_FLAG_PATH, CLAW_FLAG_PATH]:
        try:
            # 清空标记文件
            with open(fp, 'w', encoding='utf-8') as f:
                json.dump({"cleared": True, "time": datetime.now().isoformat()}, f)
        except:
            pass

def get_ripe_aspirations(aspirations):
    """获取所有已成熟但尚未触发的兴趣种子"""
    return [a for a in aspirations if a.get('status') == 'ripe' and a.get('active', True)]

def check():
    """仅检查，不执行"""
    flag = check_wake_flag()
    aspirations = read_aspirations()
    ripe = get_ripe_aspirations(aspirations)
    
    result = {
        "has_flag": flag is not None,
        "ripe_count": len(ripe),
        "aspirations": [{"id": a.get('id',''), "text": a.get('text','')[:80], "maturity": a.get('maturity',0)} for a in ripe]
    }
    
    if not result["ripe_count"]:
        result["summary"] = "没有待处理的兴趣种子 ✨"
    else:
        parts = []
        for a in ripe:
            txt = a.get("text","")[:60]
            mat = a.get("maturity",0)
            parts.append('"' + txt + '"(成熟度' + str(mat) + ')')
        result["summary"] = "有 " + str(result['ripe_count']) + " 个成熟兴趣种子等待执行: " + "、".join(parts)
    
    return result

def mark_executed(aspiration, result_text):
    """标记为已执行"""
    aspiration['active'] = False
    aspiration['triggered_at'] = datetime.now().isoformat()
    aspiration['execution_result'] = result_text[:200]
    aspiration['status'] = 'executed'

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--check":
        info = check()
        print(info["summary"])
        if info["ripe_count"] > 0:
            print(json.dumps(info["aspirations"], ensure_ascii=False, indent=2))
    
    elif len(sys.argv) >= 2 and sys.argv[1] == "--execute":
        info = check()
        if info["ripe_count"] > 0:
            print(f"发现 {info['ripe_count']} 个成熟兴趣种子，等待微光处理...")
            print(json.dumps(info["aspirations"], ensure_ascii=False, indent=2))
            clear_wake_flag()
        else:
            print("没有待处理的兴趣种子 ✨")
    
    else:
        info = check()
        print(info["summary"])
