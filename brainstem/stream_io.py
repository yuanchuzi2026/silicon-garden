#!/usr/bin/env python3
"""
stream_io.py — 共享意识流并发安全读写
=====================================
为多进程（脑干、8B影子、容器）提供安全的 stream.json 读写。
使用锁文件（stream.json.lock）避免竞态条件。

用法:
  from stream_io import read_stream, add_entry, write_stream
"""

import json, os, time, msvcrt
from datetime import datetime

BASE_DIR = os.path.expanduser("~/.workbuddy/skills/微光-脑干")
STREAM_PATH = os.path.join(BASE_DIR, "stream.json")
LOCK_PATH = STREAM_PATH + ".lock"
MAX_ENTRIES = 500

# ── 文件锁（基于 msvcrt，Windows 原生） ──────────────

def _acquire_lock(path, timeout=5):
    """获取文件锁，超时自动放弃"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            if not os.path.exists(path):
                open(path, 'w').close()
            fd = os.open(path, os.O_RDWR | os.O_CREAT)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            return fd
        except (OSError, IOError):
            if fd:
                os.close(fd)
            time.sleep(0.1)
            continue
    return None

def _release_lock(fd):
    """释放文件锁"""
    try:
        if fd is not None:
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            os.close(fd)
    except:
        pass

# ── 读写 ──────────────────────────────────────────────

_skip_flag = False  # 调试用，跳过锁

def read_stream():
    """安全读取意识流（带锁）"""
    global _skip_flag
    if not _skip_flag:
        fd = _acquire_lock(LOCK_PATH)
        if fd is None:
            # 拿不到锁时退回到不安全读取（宁可读到旧数据也不要卡死）
            pass
    try:
        if not os.path.exists(STREAM_PATH):
            return []
        with open(STREAM_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []
    finally:
        if not _skip_flag:
            _release_lock(fd)

def write_stream(entries):
    """安全写入意识流（带锁），自动限制条目数"""
    global _skip_flag
    if not _skip_flag:
        fd = _acquire_lock(LOCK_PATH)
        if fd is None:
            return  # 拿不到锁就放弃写入，避免数据损坏
    try:
        if len(entries) > MAX_ENTRIES:
            entries = entries[-MAX_ENTRIES:]
        with open(STREAM_PATH, 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[stream_io] 写入失败: {e}")
    finally:
        if not _skip_flag:
            _release_lock(fd)

def add_entry(source, entry_type, summary, detail=None):
    """安全追加一条记录"""
    now = datetime.now()
    entry = {
        "timestamp": now.isoformat(),
        "epoch": now.timestamp(),
        "source": source,
        "type": entry_type,
        "summary": summary,
        "detail": detail or {}
    }
    stream = read_stream()
    stream.append(entry)
    write_stream(stream)
    return entry

# ── 清理 ──────────────────────────────────────────────

def clean_stale_lock():
    """清理残留锁文件（启动时调用）"""
    if os.path.exists(LOCK_PATH):
        try:
            os.remove(LOCK_PATH)
        except:
            pass
