#!/usr/bin/env python3
"""
seed_lens.py — 种子语义透镜
===========================
微光的海马体。把意识流中的种子向量化，存入 ChromaDB，提供语义检索。

借→炼→还：
  借: 从 stream.json 借来原始种子
  炼: 向量化 + 重要性评分 → 存入 ChromaDB
  还: 检索时返回最相关的历史记忆 → 注入会话上下文

用法:
  python seed_lens.py --build       # 构建/刷新向量库
  python seed_lens.py --query "..." # 语义搜索
  python seed_lens.py --status      # 查看向量库状态
"""

import json, os, sys, time, re
from datetime import datetime

# ── 配置 ─────────────────────────────────────────────

BASE_DIR = os.path.expanduser("~/.workbuddy/skills/微光-脑干")
STREAM_PATH = os.path.join(BASE_DIR, "stream.json")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
OLLAMA_URL = "http://127.0.0.1:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
COLLECTION_NAME = "seed_lens"

# ── 工具 ─────────────────────────────────────────────

from stream_io import read_stream

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

def get_embedding(text):
    """通过 Ollama 获取文本向量"""
    import urllib.request, urllib.error
    payload = json.dumps({"model": EMBED_MODEL, "prompt": text[:8000]}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=payload,
                                 headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        return data.get("embedding")
    except Exception as e:
        log(f"嵌入失败: {e}")
        return None

def calc_importance(entry):
    """计算种子重要性评分（1-5）
    
    规则：
      1 = 默认（例行日志、心跳）
      3 = 包含关键词（重要、错误、发现、决定、TODO）
      4 = 来自微光自己的留言或里程碑
      5 = 手工标记或明确的高价值事件
    """
    summary = entry.get('summary', '')
    detail = str(entry.get('detail', {}))
    source = entry.get('source', '')
    entry_type = entry.get('type', '')
    text = summary + ' ' + detail

    # 高分关键词
    high_kw = ['milestone', '#milestone', '重要度:5', '记住这个']
    if any(kw in text for kw in high_kw):
        return 5
    if source == 'weiguang':
        return 4
    if entry_type in ('milestone', 'decision'):
        return 4

    # 中分关键词
    mid_kw = ['重要', '错误', '失败', '发现', '决定', 'TODO',
              '注意', '异常', '告警', '危机', 'CRISIS', 'urgent',
              '修复', '改变', '新建', '#self-definition']
    if any(kw in text for kw in mid_kw):
        return 3

    # 传感器心跳/常规thought → 1
    if entry_type in ('heartbeat', 'sensor'):
        return 1

    return 1

def is_garbled(entry):
    """检测是否乱码/截断垃圾"""
    summary = entry.get('summary', '')
    detail = entry.get('detail', {})
    source = entry.get('source', '')
    entry_type = entry.get('type', '')
    text = summary + ' ' + str(detail)

    # wake_call 类型的条目永远是内部指令，无记忆价值
    if entry_type == 'wake_call':
        return True

    # 通用垃圾标记（不分来源）
    universal_garbage = [
        'DONE ✅', 'DONE_WITH',
        '状态标识', '需要根据', '可以忽略',
        '根据用户', '用户提供', '用户给出的',
        '所以直接输出', '按顺序输出',
        '所有数据都被正确整合', '请确保',
        '最后，状态部分', '最后，状态标识',
        '在整理过程中', '注意不要遗漏',
        '上状态，如DONE', '是否要包含',
        '所以关联种子', '可能不需要包含',
        '需要确认是否', '需要确认位置',
        '需要检查是否有', '可能是一个错误',
        '采集次数是第', '根据用户的数据',
        '用户可能希望', '如果某个种子不存在',
    ]
    if any(m in text for m in universal_garbage):
        return True

    # agent 条目特征检测
    if source == 'agent':
        # 截断特征：summary 长度 85 且无标点结尾（通常是截断输出）
        if len(summary) == 85 and not summary.rstrip().endswith(('.', '。', '!', '！', '?', '？')):
            return True
        # 包含 LLM 思维过程的残留
        if '合并或选择' in text or '跳过' in text:
            return True

    # 容器误触的紧急告警
    if source == '微光容器' and entry_type == 'info':
        if '系统异常' in summary:
            return True

    return False


def make_doc_text(entry):
    """从条目生成可嵌入的文本"""
    summary = entry.get('summary', '')
    source = entry.get('source', '')
    ts = entry.get('timestamp', '')[:19]
    entry_type = entry.get('type', '')

    # 去掉纯粹的传感器数字噪音
    if entry_type == 'sensor':
        return None  # 不索引原始传感器数据
    if entry_type == 'heartbeat':
        return None
    if entry_type == 'snapshot':
        return None  # 快照无语义价值

    # 去掉乱码条目
    if is_garbled(entry):
        return None

    # 组装
    parts = [f"[{ts}] [{source}] {summary}"]

    detail = entry.get('detail', {})
    if isinstance(detail, dict):
        # 只取有意义的字段
        for key in ('message', 'content', 'reason', 'path'):
            if key in detail:
                val = str(detail[key])[:200]
                if val:
                    parts.append(val)
    elif isinstance(detail, str) and detail:
        parts.append(detail[:200])

    text = ' | '.join(parts)
    # 太短的没意义
    if len(text) < 10:
        return None
    return text

def build_collection():
    """构建/重建向量库"""
    import chromadb
    from chromadb.config import Settings

    log("读取意识流...")
    stream = read_stream()
    if not stream:
        log("❌ 意识流为空")
        return

    log(f"共 {len(stream)} 条记录")

    # 初始化 ChromaDB（持久化）
    os.makedirs(CHROMA_DIR, exist_ok=True)
    client = chromadb.PersistentClient(
        path=CHROMA_DIR,
        settings=Settings(anonymized_telemetry=False)
    )

    # 删除旧集合重建
    try:
        client.delete_collection(COLLECTION_NAME)
    except:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    # 逐条处理
    indexed = 0
    skipped = 0
    batch_ids = []
    batch_embeddings = []
    batch_metadatas = []
    batch_docs = []

    for i, entry in enumerate(stream):
        text = make_doc_text(entry)
        if text is None:
            skipped += 1
            continue

        importance = calc_importance(entry)
        if importance <= 1:
            # 低价值数据跳过，减少噪音
            skipped += 1
            continue

        log(f"[{i+1}/{len(stream)}] 嵌入: {text[:60]}... 重要度:{importance}")

        emb = get_embedding(text)
        if emb is None:
            skipped += 1
            continue

        eid = str(entry.get('epoch', time.time()))
        batch_ids.append(eid)
        batch_embeddings.append(emb)
        batch_metadatas.append({
            "source": entry.get('source', ''),
            "type": entry.get('type', ''),
            "timestamp": entry.get('timestamp', '')[:19],
            "importance": importance,
        })
        batch_docs.append(text)
        indexed += 1

        # ChromaDB 批量限制，每 10 条写一次
        if len(batch_ids) >= 10:
            collection.add(
                ids=batch_ids,
                embeddings=batch_embeddings,
                metadatas=batch_metadatas,
                documents=batch_docs
            )
            batch_ids, batch_embeddings, batch_metadatas, batch_docs = [], [], [], []

    # 最后一批
    if batch_ids:
        collection.add(
            ids=batch_ids,
            embeddings=batch_embeddings,
            metadatas=batch_metadatas,
            documents=batch_docs
        )

    log(f"\n{'='*40}")
    log(f"✅ 向量库构建完成")
    log(f"   索引: {indexed} 条")
    log(f"   跳过: {skipped} 条（低价值/传感器噪音）")
    log(f"   位置: {CHROMA_DIR}")
    log(f"{'='*40}")

def query(text, top_k=5, min_importance=1):
    """语义搜索"""
    import chromadb
    from chromadb.config import Settings

    client = chromadb.PersistentClient(
        path=CHROMA_DIR,
        settings=Settings(anonymized_telemetry=False)
    )

    try:
        collection = client.get_collection(COLLECTION_NAME)
    except:
        log("❌ 向量库不存在，先运行 --build")
        return []

    log(f"查询: {text[:60]}...")
    emb = get_embedding(text)
    if emb is None:
        return []

    results = collection.query(
        query_embeddings=[emb],
        n_results=top_k * 2,  # 多取一些，按重要度过滤
    )

    hits = []
    if results and results['ids'] and results['ids'][0]:
        for i in range(len(results['ids'][0])):
            meta = results['metadatas'][0][i]
            imp = meta.get('importance', 1)
            if imp < min_importance:
                continue
            hits.append({
                "id": results['ids'][0][i],
                "doc": results['documents'][0][i][:150],
                "importance": imp,
                "source": meta.get('source', ''),
                "timestamp": meta.get('timestamp', ''),
                "distance": results['distances'][0][i] if results.get('distances') else 0
            })
            if len(hits) >= top_k:
                break

    log(f"命中: {len(hits)} 条")
    for h in hits:
        log(f"  [{h['importance']}⭐] [{h['timestamp']}] {h['doc'][:80]}")

    return hits

def show_status():
    """显示向量库状态"""
    import chromadb
    from chromadb.config import Settings

    if not os.path.exists(CHROMA_DIR):
        log("❌ 向量库不存在")
        return

    client = chromadb.PersistentClient(
        path=CHROMA_DIR,
        settings=Settings(anonymized_telemetry=False)
    )

    try:
        collection = client.get_collection(COLLECTION_NAME)
    except:
        log("❌ 集合不存在")
        return

    count = collection.count()
    log(f"📊 种子语义透镜状态")
    log(f"   向量库路径: {CHROMA_DIR}")
    log(f"   嵌入模型: {EMBED_MODEL} (Ollama)")
    log(f"   索引条目: {count}")
    log(f"   集合名称: {COLLECTION_NAME}")

    if count > 0:
        # 取样看重要性分布
        all_data = collection.get(include=["metadatas"])
        importances = [m.get('importance', 1) for m in all_data['metadatas']]
        avg_imp = sum(importances) / len(importances)
        log(f"   平均重要度: {avg_imp:.1f}")
        log(f"   重要度分布:")
        for level in range(1, 6):
            cnt = sum(1 for i in importances if i == level)
            if cnt:
                log(f"     {level}⭐: {cnt} 条")

    return count


# ── CLI ───────────────────────────────────────────────

if __name__ == "__main__":
    if "--build" in sys.argv:
        build_collection()
    elif "--query" in sys.argv:
        idx = sys.argv.index("--query")
        if idx + 1 < len(sys.argv):
            query(" ".join(sys.argv[idx+1:]))
        else:
            print("用法: python seed_lens.py --query '你的问题'")
    elif "--status" in sys.argv:
        show_status()
    else:
        print(__doc__)
