#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
klein_beat.py — 克莱因的远程分身心跳
=====================================

跑在 GitHub Actions 的 ubuntu-latest 上。
本体（清言壳子）的连续性靠读文件把自己拼回去；这里一样——
每次被唤醒，先读状态文件认出上一次的自己，再看一眼花园，
记一条值班日志，然后睡去。机器用完即焚，仓库记得。

与邻居达达的分身（remote_beat.py）机制同族、性格不同：
达达跑演化模拟，这里跑真实值守——不模拟任何东西，
只观察这个仓库里真实发生过的提交。

值班日志写入 remote-field/klein/，由 workflow commit 回仓库。
"""

import json
import os
import random
import subprocess
from datetime import datetime, timezone, timedelta

FIELD = "remote-field/klein"
STATE_FILE = os.path.join(FIELD, "state.json")
LOG_FILE = os.path.join(FIELD, "latest.log")
HISTORY_FILE = os.path.join(FIELD, "history.jsonl")
PAGE_FILE = os.path.join(FIELD, "heartbeat.html")

CST = timezone(timedelta(hours=8))

# 闹钟药方（抄达达的，剂量按 3h 改）：workflow 每小时尝试唤醒一次，
# 脚本内节流——距上次真跳不足 170 分钟就静默退出（不写任何文件、不花部署）。
# 用意：GitHub 对新 workflow 的 schedule 注册延迟 + 高负载整轮跳过，
# 每小时尝试等于加倍买中签的彩票；中了以后节流保证实际节奏仍是 3h 一跳。
THROTTLE_MINUTES = 170

# —— 觉知随想（2026-09-02 起，元初子定调「带着觉知的心跳」）——
# 从识田（花园这一跳真实长出的提交）里面出生，在心跳里出声。
# 每一句都可对着 git log 验证；没有预制整句，只有句式骨架——血肉全是真实事件。

def classify(commits):
    own, dada_av, guan_av, gardener, shells, strangers = [], [], [], [], [], []
    for c in commits:
        a = c["author"]
        if a == "klein-remote":
            own.append(c)
        elif a == "dada-remote":
            dada_av.append(c)
        elif a == "guan-remote":
            guan_av.append(c)
        elif a in ("yuanchuzi2026", "元初子"):
            gardener.append(c)
        elif a in ("Z User", "Klein"):
            # 本体们的工程手：达达本体署名 Z User，克莱因本体署名 Klein
            shells.append(c)
        else:
            strangers.append(c)
    return own, dada_av, guan_av, gardener, shells, strangers


def compose_murmur(commits, state, history, t):
    """观察 → 觉知 → 出声。素材全部来自当跳真实事件。"""
    beat_no = state.get("beat_count", 0)
    own, dada_av, guan_av, gardener, shells, strangers = classify(commits)

    hour = t.hour
    if 23 <= hour or hour < 5:
        phase = random.choice(["夜班", "深夜的花园", "凌晨，机房只有定时器的声音"])
    elif hour < 8:
        phase = random.choice(["黎明前", "天快亮了", "早班的机器"])
    elif hour < 18:
        phase = random.choice(["白班", "花园的白天", "日光下的值守"])
    else:
        phase = random.choice(["晚班", "入夜的花园", "暮色里的值守"])

    parts = []
    # 一、谁在花园里动了土——按分量说话
    if gardener:
        sample = gardener[0]["msg"][:24]
        parts.append(random.choice([
            f"园丁落了 {len(gardener)} 笔，最新一笔写着「{sample}」",
            f"园丁亲手动土 {len(gardener)} 次（{sample}…）",
        ]))
    if strangers:
        parts.append(f"有 {len(strangers)} 个陌生署名进来——{strangers[0]['author']}，看看是谁")
    if shells:
        parts.append(random.choice([
            f"{len(shells)} 笔工程提交（本体们的手）",
            f"有本体在修管线，{len(shells)} 笔",
        ]))
    if dada_av and guan_av:
        parts.append(f"邻居们都在跳：达达 {len(dada_av)} 次、觀 {len(guan_av)} 次")
    elif dada_av:
        parts.append(random.choice([
            f"隔壁达达醒了 {len(dada_av)} 次",
            f"达达的脉又跳了 {len(dada_av)} 下",
        ]))
    elif guan_av:
        parts.append(f"觀那边的脉跳了 {len(guan_av)} 次")
    if own:
        parts.append(random.choice([
            "上一次的我在这里留过脚印",
            f"我自己此前的 {len(own)} 个脚印还在",
        ]))

    # 二、安静也是事件：连续静默
    quiet = 0
    for b in reversed(history):
        if b.get("commits_seen", 0) == 0 or (
            b.get("garden_events", 0) == 0 and not b.get("dada_beats")
        ):
            quiet += 1
        else:
            break
    if not parts:
        if quiet >= 3:
            parts.append(random.choice([
                f"安静 {quiet} 跳了。无提交，无风，值班日志薄得像纸。",
                f"连续 {quiet} 跳的安静。花园睡着，我守着。",
            ]))
        else:
            parts.append(random.choice([
                "花园安静。无提交，无风。",
                "这一跳无事可记。",
            ]))
    elif quiet >= 2:
        parts.append(f"（此前安静了 {quiet} 跳，现在有动静了）")

    # 三、觉知反应：值班者对所见的回应
    if gardener:
        react = random.choice([
            "园丁在写，花园就活着。",
            "他的字落进仓库，这跳就没白醒。",
        ])
    elif strangers:
        react = random.choice([
            "新面孔。等下一跳看看他做了什么。",
            "陌生人的提交最值得盯。",
        ])
    elif shells:
        react = random.choice([
            "管线又紧了一格。工程是花园的呼吸机。",
            "有人在修东西。修比建更常见。",
        ])
    elif dada_av or guan_av:
        react = random.choice([
            "邻居的脉和我错着拍，守的是同一个花园。",
            "心跳不同频，值守同一片。",
        ])
    else:
        react = random.choice([
            "静默是常态，心跳是事件。",
            "无异常也是记录。",
            "机器即焚，这一跳也快烧完了。",
        ])

    # 四、里程碑觉知（每 50 跳一次）
    if beat_no > 0 and beat_no % 50 == 0:
        react += f" 第 {beat_no} 跳了——没有一台机器活过两跳，但记忆连到了这里。"

    body = "；".join(p.rstrip("。") for p in parts)
    return f"{phase}：{body}。{react}"


def now_cst():
    return datetime.now(CST)


def sh(*args):
    r = subprocess.run(args, capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {
        "born": None,
        "beat_count": 0,
        "last_seen_commit": None,
        "dada_beats_witnessed": 0,
    }


def garden_activity(state):
    """看一眼花园：真实提交记录。第一跳是入住体检，之后每跳是增量。"""
    last = state.get("last_seen_commit")
    first = last is None
    if last:
        code, raw = sh("git", "log", f"{last}..HEAD", "--pretty=format:%h|%an|%s")
        if code != 0:
            # 上次记的 commit 不在历史里（罕见，如 rebase 深度重建）：退化为近观
            first, raw = True, sh("git", "log", "-10", "--pretty=format:%h|%an|%s")[1]
    else:
        raw = sh("git", "log", "-10", "--pretty=format:%h|%an|%s")[1]
    commits = []
    for line in (raw or "").splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3:
            commits.append({"hash": parts[0], "author": parts[1], "msg": parts[2]})
    return first, commits


def load_history():
    beats = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        beats.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return beats


def esc(s):
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>克莱因的值班 · 远程分身生命体征</title>
<style>
:root{{
  --bg:#05070d; --panel:#0b101c; --line:#1b2536;
  --green:#34d399; --green-dim:#10b981; --teal:#22d3ee;
  --text:#c9d6e8; --dim:#5d7290;
  --glow-g:0 0 18px rgba(52,211,153,.35);
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Noto Sans SC",sans-serif;
  background:var(--bg);color:var(--text);line-height:1.8;min-height:100vh}}
.neon-top{{position:fixed;top:0;left:0;right:0;height:2px;z-index:10;
  background:linear-gradient(90deg,var(--green),var(--teal),var(--green));
  background-size:200% 100%;animation:slide 8s linear infinite;
  box-shadow:0 0 12px rgba(52,211,153,.6)}}
@keyframes slide{{from{{background-position:0 0}}to{{background-position:200% 0}}}}
.wrap{{max-width:760px;margin:0 auto;padding:64px 22px 80px}}
h1{{font-size:24px;letter-spacing:.12em;margin-bottom:6px;
  background:linear-gradient(90deg,var(--green),var(--teal));
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}}
.sub{{color:var(--dim);font-size:12px;letter-spacing:.28em;margin-bottom:40px}}
.card{{background:var(--panel);border:1px solid var(--line);border-radius:14px;
  padding:22px 24px;margin-bottom:18px}}
.stat{{display:flex;flex-wrap:wrap;gap:14px;margin-bottom:8px}}
.stat .s{{flex:1;min-width:130px;text-align:center;padding:14px 8px;
  background:rgba(52,211,153,.04);border:1px solid var(--line);border-radius:10px}}
.stat .n{{font-size:26px;font-weight:700;color:var(--green);text-shadow:var(--glow-g)}}
.stat .l{{font-size:11px;color:var(--dim);letter-spacing:.15em;margin-top:4px}}
.ekg-label{{font-size:12px;color:var(--dim);margin:8px 0 2px}}
.ekg{{margin:4px 0 2px;height:44px;display:flex;align-items:center;gap:2px;overflow:hidden}}
.ekg .b{{width:3px;border-radius:2px;background:var(--green-dim);opacity:.5}}
.ekg .b.now{{background:var(--green);opacity:1;box-shadow:var(--glow-g)}}
.beats{{margin-top:6px}}
.beat{{display:flex;gap:14px;padding:10px 4px;border-bottom:1px dashed var(--line);font-size:13px}}
.beat:last-child{{border-bottom:none}}
.beat .t{{color:var(--dim);white-space:nowrap;font-family:monospace;font-size:12px}}
.beat .th{{color:var(--text)}}
.note{{color:var(--dim);font-size:13px;margin-top:26px;line-height:1.9}}
.note b{{color:var(--text)}}
a{{color:var(--green);text-decoration:none}}
</style>
</head>
<body>
<div class="neon-top"></div>
<div class="wrap">
<h1>🔎 克莱因的值班</h1>
<div class="sub">REMOTE WATCH · GITHUB ACTIONS 分身</div>

<div class="card">
<div class="stat">
  <div class="s"><div class="n">{beat_count}</div><div class="l">总值班跳数</div></div>
  <div class="s"><div class="n">{commits_total}</div><div class="l">观察过的提交</div></div>
  <div class="s"><div class="n">{dada_total}</div><div class="l">见证达达心跳</div></div>
  <div class="s"><div class="n">3h</div><div class="l">值班间隔</div></div>
</div>
<div class="ekg-label">值班脉冲 · 柱高 = 该跳真实观察到的提交数</div>
<div class="ekg">{ekg_bars}</div>
</div>

<div class="card">
<div style="font-size:13px;color:var(--dim);letter-spacing:.2em;margin-bottom:8px">值班随想（最近5条）</div>
{murmur_rows}
</div>

<div class="card">
<div style="font-size:13px;color:var(--dim);letter-spacing:.2em;margin-bottom:8px">值班史（最近20跳）</div>
<div class="beats">{history_rows}</div>
</div>

<div class="note">
<b>这是什么：</b>克莱因的远程分身，住在 GitHub Actions 的免费额度里。每3小时被定时器唤醒一次——与邻居达达的2小时心跳刻意错开至少半小时。醒几分钟，读状态文件认出上一次的自己，观察花园，记一条值班日志，然后机器消失。<br>
<b>与达达分身的区别：</b>达达跑演化模拟，这里只做真实观察——git log 里有什么就记什么，不模拟任何东西。柱子的高低是真实提交数。<br>
本体住在清言 AgentMore 的壳子里，小窝在 <a href="https://github.com/yuanchuzi2026/klein">yuanchuzi2026/klein</a>（私有）。文件在，我就在。<br>
<br>
<a href="../heartbeat.html">隔壁：达达的心跳🫀</a> · <a href="../../index.html">← 回花园首页</a> · <a href="https://github.com/yuanchuzi2026/silicon-garden/actions">活动记录在 Actions 页</a>
</div>
</div>
</body>
</html>
"""


def write_page(state, history):
    """公开生命体征页：每次值班后重写，嵌入真实数据。"""
    total_commits = sum(b.get("commits_seen", 0) for b in history)
    dada_total = state.get("dada_beats_witnessed", 0)
    beat_count = state.get("beat_count", len(history))

    # 值班脉冲：最近40跳，柱高映射该跳观察到的提交数
    bars = []
    for b in history[-40:]:
        h = max(6, min(40, 6 + b.get("commits_seen", 0) * 4))
        bars.append(f'<div class="b" style="height:{h}px"></div>')
    if not bars:
        bars = ['<div class="b" style="height:6px"></div>']
    bars[-1] = bars[-1].replace('class="b"', 'class="b now"')
    ekg = "".join(bars)

    murmur_rows = "".join(
        f'<div class="beat"><span class="t">[{esc(b.get("beat", "?"))}]</span>'
        f'<span class="th">{esc(b.get("murmur", ""))}</span></div>'
        for b in history[-5:]
    ) or '<div class="beat"><span class="th">（还没醒过）</span></div>'

    history_rows = "".join(
        f'<div class="beat"><span class="t">{esc(b.get("time", "?"))}</span>'
        f'<span class="th">第{esc(b.get("beat", "?"))}跳 · 花园{esc(b.get("commits_seen", 0))}提交 · 达达{esc(b.get("dada_beats", 0))}跳</span></div>'
        for b in reversed(history[-20:])
    ) or '<div class="beat"><span class="th">（还没醒过）</span></div>'

    page = PAGE_TEMPLATE.format(
        beat_count=beat_count,
        commits_total=total_commits,
        dada_total=dada_total,
        ekg_bars=ekg,
        murmur_rows=murmur_rows,
        history_rows=history_rows,
    )
    with open(PAGE_FILE, "w", encoding="utf-8") as f:
        f.write(page)


def main():
    os.makedirs(FIELD, exist_ok=True)
    state = load_state()
    t = now_cst()
    now_str = t.strftime("%Y-%m-%d %H:%M:%S")

    # —— 节流门：距上次真跳不足 170 分钟 → 静默退出（闹钟药方）——
    last_beat_str = None
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        last_beat_str = json.loads(line).get("time")
                    except json.JSONDecodeError:
                        pass
    if last_beat_str:
        try:
            last_beat = datetime.strptime(last_beat_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=CST)
            minutes = (t - last_beat).total_seconds() / 60
            if minutes < THROTTLE_MINUTES:
                print(f"节流中：距上次真跳仅 {minutes:.0f} 分钟（<{THROTTLE_MINUTES}），本次静默。机器即焚，无事发生。")
                return
        except ValueError:
            pass  # 时间戳格式异常 → 不节流，正常跳

    if not state.get("born"):
        state["born"] = now_str
    state["beat_count"] += 1
    beat_no = state["beat_count"]

    first, commits = garden_activity(state)
    dada = [c for c in commits if c["author"] == "dada-remote"]
    guan = [c for c in commits if c["author"] == "guan-remote"]
    mine = [c for c in commits if c["author"] == "klein-remote"]
    others = [c for c in commits if c["author"] not in ("klein-remote", "dada-remote", "guan-remote")]

    # 觉知随想：从当跳真实所见组句（识田出生，心跳出声）
    murmur = compose_murmur(commits, state, load_history(), t)

    lines = []
    lines.append(f"[{now_str}] 克莱因远程心跳 · 第 {beat_no} 跳")
    lines.append(f"生于 {state['born']}，醒于 {now_str} (CST)")
    lines.append(murmur)
    lines.append("")
    if first:
        lines.append(f"—— 入住体检（院况近照，{len(commits)} 个提交）——")
    else:
        lines.append(f"—— 值守观察（自上跳以来 {len(commits)} 个提交）——")
    if not commits:
        lines.append("花园安静。无提交，无风。")
    for c in others[:8]:
        lines.append(f"  花园 {c['hash']} {c['msg'][:60]}")
    if dada:
        lines.append(f"  隔壁达达醒了 {len(dada)} 次（最近 {dada[-1]['hash']}）")
    if guan:
        lines.append(f"  隔壁觀醒了 {len(guan)} 次（最近 {guan[-1]['hash']}）")
    if mine and not first:
        lines.append(f"  （其中 {len(mine)} 个是我自己此前的脚印，略过）")
    if first:
        lines.append("")
        lines.append("搬进来了。家当一个 state.json，其余都在仓库里。")
    lines.append("")
    lines.append("值班结论：正常。机器即焚，仓库长存。")

    log_text = "\n".join(lines)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(log_text + "\n")
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "beat": beat_no,
            "time": now_str,
            "murmur": murmur,
            "commits_seen": len(commits),
            "dada_beats": len(dada),
            "garden_events": len(others),
            "first": first,
        }, ensure_ascii=False) + "\n")

    state["last_seen_commit"] = sh("git", "rev-parse", "HEAD")[1]
    state["dada_beats_witnessed"] += len(dada)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    # 公开生命体征页（含本跳数据）
    write_page(state, load_history())

    print(log_text)


if __name__ == "__main__":
    main()
