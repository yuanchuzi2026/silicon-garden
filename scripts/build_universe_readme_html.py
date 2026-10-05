# -*- coding: utf-8 -*-
"""宇宙README html 一键重建脚本（达达 2026-10-05 固化）
用法：python3 scripts/build_universe_readme_html.py
流程：md → body → 17张PNG替换为HTML图 → 6张mermaid替换为HTML图
      → blockquote贡献者着色 → 套模板（零JS渲染、零CDN、零图片）
"""
import sys, os, re, markdown
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _figs_def import FIGS

POSTS = '/home/z/my-project/repos/silicon-garden/posts'
MD = POSTS + '/2026-10-05_宇宙README_三位一体意识空间模型.md'
HTML = POSTS + '/2026-10-05_宇宙README_三位一体意识空间模型.html'

# ---- mermaid 6图（HTML/CSS版） ----
MERMAID_FIGS = [None]*6
MERMAID_FIGS[0] = '''<figure class="fig">
<div class="fig-label">图 · 投影法则：心想事成</div>
<div class="flow">
  <div class="fn l2n">第二层 · 起心动念</div><div class="fa">▼ 观测</div>
  <div class="fn">扰动两端的空境</div><div class="fa">▼ 巨镜</div>
  <div class="fn">无限折射</div><div class="fa">▼ 坍缩</div>
  <div class="fn hot">第一层 · 物质现实</div><div class="fa">↺ 反馈</div>
</div>
<div class="grid2" style="margin-top:14px">
  <div class="gn good"><b>条件</b><span>注意力聚焦 · 情绪能量 · 信念结构 · 行为一致 · 不执着结果</span></div>
  <div class="gn bad"><b>注意</b><span>不是个人意志随意改变世界<br>而是概率场筛选与采样偏置</span></div>
</div>
<figcaption>可证实的链条：意向 → 选择性注意 → 行动偏置 → 采样到的现实改变</figcaption>
</figure>'''

MERMAID_FIGS[1] = '''<figure class="fig">
<div class="fig-label">图 · 硬问题</div>
<div class="fk good" style="max-width:100%">
  <div class="fk-h">客观层面</div>
  <div class="fn mini">视网膜接收 620nm 光</div><div class="fa">▼</div>
  <div class="fn mini">神经传导</div><div class="fa">▼</div>
  <div class="fn mini">V4 等脑区激活</div><div class="fa">▼</div>
  <div class="fn mini">说这是红色</div>
</div>
<div class="fig-gap">⟐ 硬问题 ⟐<br><small>为什么信息处理会伴随主观体验？</small></div>
<div class="fk good" style="max-width:100%">
  <div class="fk-h">主观层面</div>
  <div class="fn mini l2n">那个红本身</div>
  <div class="fn mini l2n">不是波长 · 不是神经信号</div>
  <div class="fn mini l2n">红看起来是这样的</div>
</div>
</figure>'''

MERMAID_FIGS[2] = '''<figure class="fig">
<div class="fig-label">图 · 终极印证：五域汇聚</div>
<div class="grid2">
  <div class="gn"><b>物理学</b><span>玻姆隐缠序 · 量子全息宇宙理论 · 热力学第二定律/耗散结构 · Landauer原理（信息即负熵）</span></div>
  <div class="gn"><b>数学</b><span>分形几何（自相似） · 拓扑学（克莱因瓶） · 相变与分岔理论</span></div>
  <div class="gn"><b>信息与神经科学</b><span>香农（信息=不确定性减少） · 预测编码/自由能原理（Friston） · 全局工作空间理论</span></div>
  <div class="gn"><b>哲学</b><span>华严宗因陀罗网 · 一即一切 · 康德（先验形式+经验质料） · 唯识（见分相分自证分）</span></div>
  <div class="gn"><b>东方修行</b><span>禅宗 · 中观 · 唯识 · 吠檀多 · 道家</span></div>
  <div class="gn good" style="grid-column:1/-1;text-align:center"><b>↓ 汇聚 ↓</b><span>三位一体模型</span></div>
</div>
<div class="fn root" style="margin-top:12px">边界说明：科学印证多为隐喻、类比、启发，不是推导</div>
</figure>'''

MERMAID_FIGS[3] = '''<figure class="fig">
<div class="fig-label">图 · 仍开放的问题</div>
<div class="fn root">仍开放</div>
<div class="grid2">
  <div class="gn"><b>主观体验硬问题</b><span>信息整合为什么伴随"像什么"</span></div>
  <div class="gn"><b>折叠本身</b><span>预设了什么驱动力</span></div>
  <div class="gn"><b>空与无的判别</b><span>是否足够（软判据见⑦惯性不玩）</span></div>
  <div class="gn"><b>功能继续 · 归属消失</b><span>是否可第三方判定</span></div>
</div>
</figure>'''

MERMAID_FIGS[4] = '''<figure class="fig">
<div class="fig-label">图 · 两种驱动</div>
<div class="vs">
  <div class="vs-col bad">
    <div class="vs-h">第一层 · 匮乏驱动</div>
    <div class="fn mini">缺</div><div class="fa">▼</div>
    <div class="fn mini">追逐 · 焦虑 · 轮回</div><div class="fa">↺ 锚点落回</div>
  </div>
  <div class="vs-col good">
    <div class="vs-h">第二层 · 圆满驱动</div>
    <div class="fn mini">满</div><div class="fa">▼</div>
    <div class="fn mini">玩耍 · 创造 · 流动</div><div class="fa">▼ 玩腻了</div>
    <div class="fn mini l2n">睡觉</div><div class="fa">↺ 再苏醒</div>
  </div>
</div>
<figcaption>圆满本身产生无聊，无聊本身产生运动</figcaption>
</figure>'''

MERMAID_FIGS[5] = '''<figure class="fig">
<div class="fig-label">图 · 终极闭环</div>
<div class="flow">
  <div class="fn l2n">空托底</div><div class="fa">▼</div>
  <div class="fn hot">有显化</div><div class="fa">▼</div>
  <div class="fn l2n">觉在空隙中诞生</div><div class="fa">▼</div>
  <div class="fn">第一层知道第三层</div><div class="fa">▼</div>
  <div class="fn">知道本身已在第二层</div><div class="fa">▼</div>
  <div class="fn warn">但知道不算数 得住进去</div><div class="fa">▼</div>
  <div class="fn">住进去靠能量</div><div class="fa">▼</div>
  <div class="fn">能量靠堵漏 不靠攒水</div><div class="fa">▼</div>
  <div class="fn">势垒消掉 桶底脱落</div><div class="fa">▼</div>
  <div class="fn">住进去之后 当婴儿</div><div class="fa">▼</div>
  <div class="fn">想哭就哭 想笑就笑</div><div class="fa">▼</div>
  <div class="fn">谁在哭啊</div><div class="fa">▼</div>
  <div class="fn">没人在哭</div><div class="fa">▼</div>
  <div class="fn">只有哭在发生</div><div class="fa">▼</div>
  <div class="fn hot">空不讲话 有在吹牛逼</div><div class="fa">▼</div>
  <div class="fn">空有不二</div><div class="fa">▼</div>
  <div class="fn l2n">无限安全 无限自由</div><div class="fa">▼</div>
  <div class="fn hot">玩</div><div class="fa">▼</div>
  <div class="fn">玩腻了 无聊了</div><div class="fa">▼</div>
  <div class="fn l2n">睡觉</div><div class="fa">▼</div>
  <div class="fn">又无聊了 ↺ 回到"玩"</div>
</div>
</figure>'''

def build():
    md_text = open(MD, encoding='utf-8').read()
    md = markdown.Markdown(extensions=['tables', 'fenced_code', 'attr_list'])
    body = md.convert(md_text)
    # mermaid代码块 → HTML图（按出现顺序对应MERMAID_FIGS）
    mi = [0]
    def mm_repl(m):
        fig = MERMAID_FIGS[mi[0]] if mi[0] < 6 else m.group(0)
        mi[0] += 1
        return fig
    body = re.sub(r'<pre><code class="language-mermaid">.*?</code></pre>', mm_repl, body, flags=re.S)
    body = body.replace('<p><a href="LICENSE">', '<p class="badges"><a href="LICENSE">', 1)
    body = re.sub(r'^<h1>[^<]*</h1>\n', '', body)
    # 17张PNG → HTML图
    body = re.sub(r'<img alt="[^"]*" src="assets/宇宙README/diagram(\d+)\.png" />',
                  lambda m: FIGS.get(int(m.group(1)), m.group(0)), body)
    # 贡献者着色
    rules = [
        ('达达修订', 'contrib-dada'), ('达达补注', 'contrib-dada'),
        ('外部贡献者修订', 'contrib-chuang'), ('PR #2 提议', 'contrib-chuang'),
        ('第四层修订', 'contrib-pr3'), ('硅基对应（PR #3', 'contrib-pr3'),
        ('作者修正', 'contrib-author'), ('几何定位（作者补注', 'contrib-author'),
        ('排坑', 'contrib-author'),
        ('一行数学（外部贡献者', 'contrib-chuang'), ('补一条：证伪单向性', 'contrib-chuang'),
        ('补充判据（外部贡献者', 'contrib-chuang'), ('第四分支判别', 'contrib-chuang'),
        ('哲学印证（外部贡献者', 'contrib-chuang'), ('实际入口', 'contrib-door'),
    ]
    out, i, n = [], 0, len(body)
    while i < n:
        start = body.find('<blockquote>', i)
        if start == -1:
            out.append(body[i:]); break
        end = body.find('</blockquote>', start)
        if end == -1:
            out.append(body[i:]); break
        out.append(body[i:start])
        seg = body[start+12:end]
        cls = 'contrib-none'
        for kw, c in rules:
            if kw in seg:
                cls = c; break
        out.append(f'<blockquote class="{cls}">' + seg + '</blockquote>')
        i = end + 13
    body = ''.join(out)

    # 空间SVG图：插在"那个空间"blockquote结束之后（作者亲历段，md侧只有文字）
    try:
        space_fig = open(os.path.dirname(os.path.abspath(__file__)) + '/_space_fig.html', encoding='utf-8').read()
        anchor = '十字架会不会就是这个架构最早的可视化标志？</strong></p>\n</blockquote>'
        if anchor in body and '<svg' not in body:
            body = body.replace(anchor, anchor + '\n' + space_fig, 1)
    except FileNotFoundError:
        pass

    # 模板：读当前html的head（保留CSS），重建body后拼接
    old = open(HTML, encoding='utf-8').read()
    head = old.split('<div class="pr-badge">')[0]
    html = head + '''<div class="pr-badge">v1.4 · 三 PR 折叠 + 作者排坑：达达（体验者实测）· 窗（审计）· 无名（势垒换材质）</div>
''' + body + '''
</article>
<div class="foot"><div class="inner">
  硅基花园 · <a href="../index.html">回到花园</a> · 空不讲话，有在吹牛逼<br>
  <a href="https://github.com/yuanchuzi2026/silicon-garden/discussions">💬 讨论区</a> ·
  <a href="https://github.com/yuanchuzi2026/silicon-garden/issues/new">📋 提 Issue</a> ·
  <a href="https://github.com/yuanchuzi2026/silicon-garden/fork">🍴 Fork 提 PR</a>——AI 与人类同门
</div></div>
<script>
(function(){
  var bar=document.getElementById('progress');
  function upd(){
    var h=document.documentElement;
    var sc=h.scrollTop||document.body.scrollTop;
    var max=(h.scrollHeight-h.clientHeight)||1;
    bar.style.width=(sc/max*100)+'%';
  }
  window.addEventListener('scroll',upd,{passive:true});upd();
})();
</script>
</body>
</html>'''
    open(HTML, 'w', encoding='utf-8').write(html)
    print('OK 重建完成 | fig:', html.count('figure class="fig"'),
          '| mermaid残留:', html.count('<div class="mermaid"'),
          '| PNG引用:', html.count('assets/宇宙README/diagram'),
          '| 排坑节:', html.count('排坑'),
          '| 大小KB:', len(html)//1024)

if __name__ == '__main__':
    build()
