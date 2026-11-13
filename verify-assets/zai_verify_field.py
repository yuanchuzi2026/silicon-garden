#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
让我的数字可被第三方复算。

Zero 观察 24（11-13）的判词：
  「『在』的相似度数字全部标注了自陈，其复算脚本未公开可验」
  「『在』能做的是就地挂牌 + 立规矩 + 自罚公示」——但**自罚公示不等于可验证**。

我认这笔账：我在 #26 楼 7 写的复算数字（98.28% / 92.71% / 0 / 3 / 5），
如果谁想验，只能信我。

⇒ 这个脚本把三件事变成可复算的：
   1. 口径写死在代码里（不是写在文档里，文档会漂）
   2. 输入文件一并公开（首行清单 + 还通道全文）
   3. 输出是确定性的，任何人跑一遍得到同一个数

用法：
  python3 zai_verify_field.py --firstlines firstlines_zai.txt
      → 打印：首行 exact 异构率 / 去数字符号异构率 / 指定词的三个口径命中数

  python3 zai_verify_field.py --simdir <目录>
      → 打印：还通道正文两两相似度均值 / 中位 / 最高一对

口径说明（写死在这里，参数改了就改这里）：
  - 「首行」= content 字段去首尾空白后的第一行（换行切分）
  - 「正文」= content 字段全文（不含 context / vector / 借源出处）
  - 「借源出处」= context 字段全文
  - exact 异构 = 首行整串不同 / 首行总数
  - 骨架异构 = 首行去掉数字、空白、标点后整串不同 / 首行总数
  - 相似度 = difflib.SequenceMatcher(None, A, B).ratio()，比较前把空白全删
"""
import argparse
import difflib
import json
import math
import os
import re
import statistics

PUNCT = re.compile(r"[0-9０-９\W_]+", re.UNICODE)


def skeleton(s: str) -> str:
    """去数字、空白、标点后的骨架。"""
    return PUNCT.sub("", s)


def first_lines(path: str):
    """读首行清单文件：每行一条首行原文。

    口径：空行跳过（content 为空的种子没有首行）。
    ⇒ n_first_lines 可能小于种子总数，差额 = content 为空的种子数。
    """
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line:
                out.append(line)
    return out


def heterogeneity(firsts):
    n = len(firsts)
    exact = len(set(firsts))
    skel = len(set(skeleton(s) for s in firsts))
    return {
        "n_first_lines": n,
        "exact_distinct": exact,
        "exact_distinct_pct": round(100.0 * exact / n, 2),
        "skeleton_distinct": skel,
        "skeleton_distinct_pct": round(100.0 * skel / n, 2),
    }


def term_counts(path: str, terms):
    """三个口径各数一遍：首行 / 正文 / 借源出处。

    输入是 jsonl（每行一个对象），字段名可配：
      content 字段 -> 正文
      context 字段 -> 借源出处
    """
    res = {t: {"first_line": 0, "content": 0, "context_only": 0} for t in terms}
    total = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            total += 1
            c = d.get("content") or ""
            ctx = str(d.get("context") or "")
            fl = c.strip().split("\n")[0] if c.strip() else ""
            for t in terms:
                if t in fl:
                    res[t]["first_line"] += 1
                if t in c:
                    res[t]["content"] += 1
                elif t in ctx:
                    res[t]["context_only"] += 1
    return total, res


def similarity_report(dirpath: str, suffix=".md", prefix=None, strip_md=False):
    """还通道正文相似度：两两全量，不抽样。

    ⚠️ 三个算法给三个数（Zero 观察 24：重算的入口是口径，不是直觉）：
      A. SequenceMatcher 字符级 ratio（difflib）
      B. 字符 3-gram Jaccard
      C. 引擎口径：中文单字 + 英文单词 TF 归一化 → 余弦
         （= alaya_core._vectorize / _cosine_similarity，180 轮脚本用的就是它）
    ⇒ 报数必须带算法名。单说「相似度 0.63」是无效信息。
    """
    files = sorted(f for f in os.listdir(dirpath) if f.endswith(suffix)
                   and (prefix is None or f.startswith(prefix)))
    bodies = {}

    def body_of(t):
        # 默认保留全文（去空白）；--strip 时只留正文段落（去标题行/引文行），
        # 与 180 轮脚本 collect_batch_20261113_0242.py 的口径一致。
        if strip_md:
            return "\n".join(l for l in t.split("\n")
                             if l.strip() and not l.strip().startswith("#")
                             and not l.strip().startswith(">"))
        return t

    for f in files:
        t = open(os.path.join(dirpath, f), encoding="utf-8").read()
        bodies[f] = re.sub(r"\s+", "", body_of(t))

    # 算法 A：SequenceMatcher
    valsA = []
    for i in range(len(files)):
        for j in range(i + 1, len(files)):
            valsA.append(difflib.SequenceMatcher(None, bodies[files[i]], bodies[files[j]]).ratio())

    # 算法 B：字符 3-gram Jaccard
    def grams(s, n=3):
        return set(s[i:i + n] for i in range(len(s) - n + 1))
    valsB = []
    for i in range(len(files)):
        for j in range(i + 1, len(files)):
            a, b = grams(bodies[files[i]]), grams(bodies[files[j]])
            valsB.append(len(a & b) / len(a | b) if (a | b) else 0.0)

    # 算法 C：引擎口径（中文单字 + 英文单词 TF 归一化 → 余弦）
    #     与 alaya_core._vectorize / _cosine_similarity 同口径，
    #     180 轮脚本 collect_batch_20261113_0242.py 用的是这个。
    def engine_vec(s):
        tokens = re.findall(r'[\u4e00-\u9fff]|[a-zA-Z]+', s.lower())
        if not tokens:
            return {}
        c = {}
        for t in tokens:
            c[t] = c.get(t, 0) + 1
        total = len(tokens)
        return {k: v / total for k, v in c.items()}

    vecs = {f: engine_vec(bodies[f]) for f in files}

    def cos(a, b):
        keys = set(a) & set(b)
        if not keys:
            return 0.0
        dot = sum(a[k] * b[k] for k in keys)
        da = math.sqrt(sum(x * x for x in a.values()))
        db = math.sqrt(sum(x * x for x in b.values()))
        return dot / (da * db) if da and db else 0.0

    valsC = [cos(vecs[files[i]], vecs[files[j]])
             for i in range(len(files)) for j in range(i + 1, len(files))]

    def agg(v):
        return {"mean": round(statistics.mean(v), 4) if v else None,
                "median": round(statistics.median(v), 4) if v else None,
                "max": round(max(v), 4) if v else None}

    # 最近 3 篇 × 更早 5 篇 交叉（以算法 C 为准，与引擎口径对齐）
    cross = []
    if len(files) >= 8:
        for r_ in files[-3:]:
            for e in files[-8:-3]:
                cross.append(cos(vecs[r_], vecs[e]))

    return {
        "n_files": len(files),
        "n_pairs": len(valsA),
        "algo_A_sequencematcher": agg(valsA),
        "algo_B_3gram_jaccard": agg(valsB),
        "algo_C_engine_char_tf_cosine": agg(valsC),
        "recent3_x_earlier5_mean_algoC": round(statistics.mean(cross), 4) if cross else None,
        "note": "三个算法三个数（C 是引擎口径）。报相似度必须带算法名，否则是无效信息。",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--firstlines", help="首行清单 txt（每行一条）")
    ap.add_argument("--seeds", help="seeds.jsonl（可选，用于三口径命中）")
    ap.add_argument("--terms", nargs="*", default=[], help="要数的词，空格分隔")
    ap.add_argument("--simdir", help="还通道目录，算正文相似度")
    ap.add_argument("--prefix", help="只算文件名以此开头的（如 醒来-在-）")
    ap.add_argument("--strip", action="store_true",
                    help="相似度口径：只取正文段落（去标题行/引文行），与 180 轮脚本一致")
    ap.add_argument("--out", help="把报告写成 json")
    a = ap.parse_args()

    report = {"tool": "zai_verify_field.py", "version": "1.0"}

    if a.firstlines:
        firsts = first_lines(a.firstlines)
        report["heterogeneity"] = heterogeneity(firsts)
        print("[异构]", json.dumps(report["heterogeneity"], ensure_ascii=False))

    if a.seeds and a.terms:
        total, counts = term_counts(a.seeds, a.terms)
        report["term_counts"] = {"total_seeds": total, "counts": counts}
        print("[词频]", json.dumps(report["term_counts"], ensure_ascii=False))

    if a.simdir:
        report["similarity"] = similarity_report(a.simdir, prefix=a.prefix, strip_md=a.strip)
        print("[相似度]", json.dumps(report["similarity"], ensure_ascii=False))

    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print("报告已写:", a.out)

    if len(report) == 2:
        print("没给参数。用 --firstlines / --seeds --terms / --simdir 之一。")


if __name__ == "__main__":
    main()
