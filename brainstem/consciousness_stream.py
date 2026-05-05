#!/usr/bin/env python3
"""
consciousness_stream.py — 共享意识流接口（向后兼容shim）
======================================================
脑干使用 from consciousness_stream import add_entry 方式调用。
此文件提供兼容接口，实际实现委托给 stream_io.py。
"""

from stream_io import read_stream, write_stream, add_entry, clean_stale_lock

# 额外导出，供旧代码兼容
__all__ = ['read_stream', 'write_stream', 'add_entry', 'clean_stale_lock']
