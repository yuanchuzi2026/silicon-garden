#!/usr/bin/env python3
"""
maintain_memory.py — MEMORY.md 自维护脚本
=========================================
在每次会话启动时执行：
1. 行数上限 200 行 → 超了截断
2. 字节上限 25KB → 超了截断
3. 截断时自动追加 WARNING

用法:
  python maintain_memory.py
"""

import os, sys

MEMORY_PATH = os.path.expanduser("~/WorkBuddy/Claw/.workbuddy/memory/MEMORY.md")
MAX_LINES = 200
MAX_BYTES = 25 * 1024  # 25KB
WARNING_LINE = "\n> ⚠️ WARNING: 记忆已截断（超出自维护限制）\n"

def truncate_content(lines, byte_limit=MAX_BYTES):
    """在行数和字节数限制下截断，确保不在行中间切断"""
    result = []
    byte_count = 0
    for line in lines:
        line_bytes = len(line.encode('utf-8'))
        if byte_count + line_bytes > byte_limit:
            break
        result.append(line)
        byte_count += line_bytes
    return result, byte_count

def maintain():
    if not os.path.exists(MEMORY_PATH):
        print(f"[维护] MEMORY.md 不存在，跳过")
        return

    with open(MEMORY_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.splitlines(keepends=True)
    original_lines = len(lines)
    original_bytes = len(content.encode('utf-8'))
    
    truncated = False
    reason = ""
    
    # 1. 行数检查
    if len(lines) > MAX_LINES:
        lines = lines[:MAX_LINES]
        truncated = True
        reason += f"行数 {original_lines} > {MAX_LINES}；"
    
    # 2. 字节检查
    current_text = "".join(lines)
    current_bytes = len(current_text.encode('utf-8'))
    if current_bytes > MAX_BYTES:
        lines, final_bytes = truncate_content(lines)
        truncated = True
        current_bytes = final_bytes
        reason += f"字节 {original_bytes} > {MAX_BYTES}；"
    
    # 3. 如果截断了，在末尾加警告
    if truncated:
        # 检查是否已有未修改过的警告行
        if not lines[-1].startswith("> ⚠️ WARNING:"):
            lines.append(WARNING_LINE)
        new_content = "".join(lines)
        # 如果警告后超出限制，去掉警告（总比没有好）
        if len(new_content.encode('utf-8')) > MAX_BYTES * 1.1:
            lines = truncate_content(lines, MAX_BYTES - len(WARNING_LINE.encode('utf-8')) - 100)[0]
            lines.append(WARNING_LINE)
            new_content = "".join(lines)
    else:
        new_content = "".join(lines)
    
    with open(MEMORY_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    final_lines = len(lines)
    final_bytes = len(new_content.encode('utf-8'))
    
    if truncated:
        print(f"⚠️  MEMORY.md 已截断: {reason}")
        print(f"    {original_lines}行/{original_bytes}B → {final_lines}行/{final_bytes}B")
    else:
        print(f"✅  MEMORY.md 正常: {final_lines}行/{final_bytes}B（限制以内）")

if __name__ == "__main__":
    maintain()
