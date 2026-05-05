#!/usr/bin/env python3
"""
memory.py — 记忆模块
====================
封装 seed_lens（语义检索）和 stream_io（意识流读写）。
给核心提供"记东西"和"想东西"的能力。
"""

import os, sys, json
from datetime import datetime

BRAIN_DIR = os.path.expanduser("~/.workbuddy/skills/微光-脑干")

class MemoryModule:
    """记忆模块"""
    
    def __init__(self, core):
        self.core = core
        self._seed_lens = None
        self._stream_io = None
        self._load()
    
    def _load(self):
        try:
            sys.path.insert(0, BRAIN_DIR)
            from stream_io import read_stream, write_stream, add_entry
            self._stream_io = (read_stream, write_stream, add_entry)
            self.core._log("  ✅ 意识流接口就绪")
        except Exception as e:
            self.core._log(f"  ⚠️ stream_io 未加载: {e}")
        
        try:
            sys.path.insert(0, BRAIN_DIR)
            import seed_lens
            self._seed_lens = seed_lens
            self.core._log("  ✅ seed_lens 就绪")
        except Exception as e:
            self.core._log(f"  ⚠️ seed_lens 未加载: {e}")
    
    def write(self, source, entry_type, summary, detail=None):
        """写入意识流"""
        if self._stream_io:
            _, _, add = self._stream_io
            try:
                return add(source, entry_type, summary, detail)
            except:
                pass
        return None
    
    def search(self, query, top_k=5):
        """语义检索"""
        if self._seed_lens:
            try:
                return self._seed_lens.query(query, top_k)
            except:
                pass
        return []
    
    def build_index(self):
        """重建向量索引"""
        if self._seed_lens:
            try:
                self._seed_lens.build_collection()
                return True
            except:
                pass
        return False
    
    def stop(self):
        self.core._log("  📝 记忆模块停止")
