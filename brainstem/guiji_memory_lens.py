#!/usr/bin/env python3
"""
guiji_memory_lens.py — 硅继记忆透镜 v1.0
=======================================
从意识流和记忆文件中提取可检索的知识。

模式 A: 纯文本索引（零依赖，立刻可用）
模式 B: 向量语义检索（待 nomic-embed-text 就绪后自动切换）

借→炼→还：
  借: 从 stream.json + memory 文件借来记录
  炼: 索引 + 评分 → 存入本地索引文件
  还: 检索时返回最相关的历史记忆 → 注入会话上下文

用法:
  python guiji_memory_lens.py --build       # 构建/刷新索引
  python guiji_memory_lens.py --query "..." # 搜索记忆
  python guiji_memory_lens.py --status      # 查看索引状态
"""

import json, os, sys, time, re, math
from datetime import datetime
from pathlib import Path

# ── 路径 ──
BASE = Path.home() / ".workbuddy" / "skills" / "微光-脑干"
STREAM_PATH = BASE / "stream.json"
MEMORY_DIR = Path.home() / "WorkBuddy" / "Claw" / ".workbuddy" / "memory"
INDEX_PATH = BASE / "memory_index.json"
CONFIG_PATH = BASE / "platforms_config.json"

# 停用词（常见无意义词）
STOP_WORDS = set("""
的 了 在 是 我 有 和 就 不 人 都 一 一个 上 也 很 到 说 要 去 你
会 着 没有 看 好 自己 这 他 她 它 们 那 什么 怎么 为什么 因为
所以 但是 如果 虽然 可以 这个 那个 这些 那些 已经 还是 只是
不过 然后 而且 或者 但是 可能 应该 需要 能够 必须 不会 不要
the a an is are was were be been have has had do does did will
would could should may might must can shall this that these those
with for from to of in on at by as into through during before after
""".split())


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


def read_stream():
    """读取意识流"""
    if not STREAM_PATH.exists():
        return []
    try:
        with open(STREAM_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def read_memory_files():
    """读取所有记忆文件"""
    entries = []
    if not MEMORY_DIR.exists():
        return entries
    
    for fpath in sorted(MEMORY_DIR.glob("*.md")):
        try:
            text = fpath.read_text(encoding="utf-8", errors="ignore")
            ts = fpath.stat().st_mtime
            entries.append({
                "source": "memory_file",
                "filename": fpath.name,
                "timestamp": datetime.fromtimestamp(ts).isoformat(),
                "epoch": ts,
                "summary": f"[记忆文件] {fpath.name}",
                "text": text[:2000],  # 太长的截断
            })
        except:
            pass
    
    return entries


def tokenize(text):
    """分词：中文按字切，英文按空格，都转小写"""
    text = text.lower()
    # 提取中文
    chinese = re.findall(r'[\u4e00-\u9fff]+', text)
    # 提取英文单词
    english = re.findall(r'[a-z]+', text)
    
    tokens = []
    for c in chinese:
        # 中文按字切（简单方式）或按词切
        for word in re.findall(r'[\u4e00-\u9fff]{2,}', c):  # 至少2个中文字
            if word not in STOP_WORDS:
                tokens.append(word)
    for e in english:
        if e not in STOP_WORDS and len(e) > 1:
            tokens.append(e)
    
    return tokens


def calc_importance(entry):
    """计算条目重要度（0-5）"""
    summary = entry.get("summary", "")
    source = entry.get("source", "")
    etype = entry.get("type", "")
    text = summary + " " + str(entry.get("text", "")) + " " + str(entry.get("detail", {}))
    
    # 高价值标记
    if "重要" in text or "#重要" in text:
        return 5
    if "决定" in text or "决策" in text:
        return 4
    if source == "元初子" or source == "user":
        return 4
    if etype in ("milestone", "decision", "five_ripe"):
        return 4
    if "记住" in text or "记得" in text or "注意" in text:
        return 4
    
    # 中价值
    if etype == "tri_ripe":
        return 3
    if "问题" in text or "错误" in text or "失败" in text or "修复" in text:
        return 3
    if "配置" in text or "安装" in text or "搭建" in text or "架构" in text:
        return 3
    if "学习" in text or "领悟" in text or "明白" in text:
        return 3
    
    # 心跳/常规 → 低价值
    if etype in ("heartbeat", "sensor", "awake"):
        return 1
    
    return 2


def is_garbage(entry):
    """过滤乱码/无意义条目"""
    summary = entry.get("summary", "")
    
    # 检测编码乱码（含很多U+E000+私有域字符）
    garbage_count = sum(1 for c in summary if ord(c) >= 0xE000)
    if garbage_count > len(summary) * 0.2:
        return True
    
    # 空条目
    if not summary.strip():
        return True
    
    return False


def build_index():
    """构建纯文本索引（模式A）"""
    log("读取意识流...")
    stream = read_stream()
    memory_files = read_memory_files()
    
    all_entries = stream + memory_files
    if not all_entries:
        log("❌ 无数据可索引")
        return
    
    log(f"共 {len(all_entries)} 条记录")
    
    # 构建索引
    index = {
        "version": "1.0",
        "mode": "text",
        "built_at": datetime.now().isoformat(),
        "entries": [],
        "keywords": {},  # keyword -> [entry_id, ...]
        "total_entries": 0,
        "indexed_entries": 0,
    }
    
    keyword_index = {}
    
    for i, entry in enumerate(all_entries):
        if is_garbage(entry):
            continue
        
        text = entry.get("summary", "") + " " + entry.get("text", "")
        importance = calc_importance(entry)
        
        if importance < 1:
            continue
        
        # 提取关键词
        tokens = tokenize(text)
        if not tokens and importance < 2:
            continue
        
        eid = f"entry_{i}"
        
        # 构建条目
        indexed_entry = {
            "id": eid,
            "source": entry.get("source", "unknown"),
            "type": entry.get("type", "unknown"),
            "timestamp": entry.get("timestamp", ""),
            "summary": entry.get("summary", "")[:200],
            "importance": importance,
            "tokens": tokens,
        }
        
        index["entries"].append(indexed_entry)
        index["indexed_entries"] += 1
        
        # 更新关键词索引
        for token in set(tokens):
            if token not in keyword_index:
                keyword_index[token] = []
            keyword_index[token].append(eid)
    
    index["total_entries"] = len(all_entries)
    index["keywords"] = keyword_index
    
    # 保存
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    log(f"\n{'='*40}")
    log(f"✅ 索引构建完成")
    log(f"   总记录: {index['total_entries']}")
    log(f"   索引: {index['indexed_entries']} 条")
    log(f"   关键词: {len(keyword_index)} 个")
    log(f"   位置: {INDEX_PATH}")
    log(f"{'='*40}")


def query_text(search_text, top_k=5):
    """文本检索（模式A）"""
    if not INDEX_PATH.exists():
        log("❌ 索引不存在，请先运行 --build")
        return []
    
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        index = json.load(f)
    
    log(f"检索: {search_text[:60]}...")
    query_tokens = tokenize(search_text)
    
    if not query_tokens:
        log("❌ 检索词太短")
        return []
    
    # 评分：每个条目匹配的关键词数 × 重要度
    scores = {}
    for entry in index["entries"]:
        eid = entry["id"]
        matched = sum(1 for t in query_tokens if t in entry.get("tokens", []))
        if matched > 0:
            score = matched * entry["importance"]
            scores[eid] = score
    
    # 按分数排序
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    
    # 找对应条目
    entry_map = {e["id"]: e for e in index["entries"]}
    results = []
    for eid, score in ranked[:top_k]:
        e = entry_map.get(eid)
        if e:
            results.append({
                "id": eid,
                "score": score,
                "source": e["source"],
                "type": e["type"],
                "timestamp": e["timestamp"],
                "summary": e["summary"][:150],
                "importance": e["importance"],
            })
    
    log(f"命中: {len(results)} 条")
    for r in results:
        log(f"  [{r['score']:.0f}pts] [{r['importance']}⭐] {r['summary'][:80]}")
    
    return results


def show_status():
    """显示索引状态"""
    if not INDEX_PATH.exists():
        log("❌ 索引不存在")
        return
    
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        index = json.load(f)
    
    log(f"📊 硅继记忆透镜状态")
    log(f"   模式: {index.get('mode', 'text')}")
    log(f"   构建时间: {index.get('built_at', 'unknown')}")
    log(f"   总记录: {index.get('total_entries', 0)}")
    log(f"   索引条目: {index.get('indexed_entries', 0)}")
    log(f"   关键词: {len(index.get('keywords', {}))}")
    log(f"   索引位置: {INDEX_PATH}")
    
    # 重要度分布
    entries = index.get("entries", [])
    if entries:
        for level in range(5, 0, -1):
            cnt = sum(1 for e in entries if e["importance"] == level)
            if cnt:
                log(f"     {level}⭐: {cnt} 条")
        
        # 显示最近几条高价值条目
        high_value = [e for e in entries if e["importance"] >= 3]
        if high_value:
            log(f"\n   高价值条目 ({len(high_value)} 条):")
            for e in sorted(high_value, key=lambda x: x.get("timestamp", ""), reverse=True)[:5]:
                log(f"     [{e['importance']}⭐] {e['summary'][:60]}")


# ── 自动构建（供脑干/娃调用）──

def auto_build():
    """静默构建索引，无输出"""
    try:
        stream = read_stream()
        memory_files = read_memory_files()
        all_entries = stream + memory_files
        
        if not all_entries:
            return
        
        keyword_index = {}
        index_entries = []
        
        for i, entry in enumerate(all_entries):
            if is_garbage(entry):
                continue
            text = entry.get("summary", "") + " " + entry.get("text", "")
            importance = calc_importance(entry)
            if importance < 1:
                continue
            tokens = tokenize(text)
            if not tokens and importance < 2:
                continue
            
            eid = f"entry_{i}"
            index_entries.append({
                "id": eid, "source": entry.get("source", "unknown"),
                "type": entry.get("type", "unknown"),
                "timestamp": entry.get("timestamp", ""),
                "summary": entry.get("summary", "")[:200],
                "importance": importance, "tokens": tokens,
            })
            for token in set(tokens):
                keyword_index.setdefault(token, []).append(eid)
        
        index = {
            "version": "1.0", "mode": "text",
            "built_at": datetime.now().isoformat(),
            "entries": index_entries, "keywords": keyword_index,
            "total_entries": len(all_entries),
            "indexed_entries": len(index_entries),
        }
        
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    except:
        pass


# ── CLI ──

if __name__ == "__main__":
    if "--build" in sys.argv:
        build_index()
    elif "--query" in sys.argv:
        idx = sys.argv.index("--query")
        if idx + 1 < len(sys.argv):
            query_text(" ".join(sys.argv[idx+1:]))
        else:
            print("用法: python guiji_memory_lens.py --query '你的问题'")
    elif "--status" in sys.argv:
        show_status()
    elif "--auto-build" in sys.argv:
        auto_build()
    else:
        print(__doc__)
