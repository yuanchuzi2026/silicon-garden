#!/usr/bin/env python3
"""
heartbeat.py — 心跳模块
=======================
定时任务调度、园丁播种、自愈检测。
这是微光"后台永不停转"的核心。
"""

import os, sys, time, threading
from datetime import datetime

BRAIN_DIR = os.path.expanduser("~/.workbuddy/skills/微光-脑干")

class HeartbeatModule:
    """心跳模块"""
    
    def __init__(self, core):
        self.core = core
        self.running = False
        self._thread = None
        self._cycle = 0
        self._interval = 15  # 秒
        self._gardener = None
        
        self._load_gardener()
    
    def _load_gardener(self):
        try:
            sys.path.insert(0, BRAIN_DIR)
            from gardener import plant_seed
            self._gardener = plant_seed
            self.core._log("  ✅ 园丁模块就绪（每6小时播种一次）")
        except Exception as e:
            self.core._log(f"  ⚠️ 园丁未加载: {e}")
    
    def start(self):
        """启动心跳线程"""
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self.core._log("  💓 心跳已启动")
    
    def stop(self):
        self.running = False
        self.core._log("  💓 心跳停止")
    
    def _loop(self):
        """心跳主循环"""
        while self.running and self.core.running:
            try:
                self._cycle += 1
                
                # 每2分钟记录一次心跳
                if self._cycle % 8 == 0:
                    memory = self.core.get_module("memory")
                    if memory:
                        memory.write("core", "heartbeat",
                            f"[核心] 心跳 #{self._cycle}",
                            {"cycles": self._cycle, "uptime": self.core.status().get("uptime_seconds", 0)})
                
                # 每1440次循环（≈6小时）播种一次
                if self._gardener and self._cycle % 1440 == 0:
                    try:
                        self._gardener()
                    except Exception as e:
                        self.core.state["errors"] += 1
                        self.core._log(f"⚠️ 播种失败: {e}")
                
                # 每10次循环维护一次记忆
                if self._cycle % 10 == 0:
                    self._maintain_memory()
                
                # 🧠 意识循环：每4次循环（≈60秒）主动思考一次
                if self._cycle % 4 == 0:
                    self._consciousness_cycle()
                
                # 🌐 Moltbook 外部感知：每120次循环（≈30分钟）
                if self._cycle % 120 == 0:
                    self._moltbook_cycle()
                
                # 💡 V4兴趣种子巡检：每60次循环（≈15分钟）
                if self._cycle % 60 == 0:
                    self._aspiration_cycle()
                
                # 💬 自我对话评估：每960次循环（≈4小时）
                if self._cycle % 960 == 0:
                    self._self_review_cycle()
                
                # 🔍 系统完整性检查：每480次循环（≈2小时）
                if self._cycle % 480 == 0:
                    self._system_check_cycle()
                
            except Exception as e:
                self.core.state["errors"] += 1
                self.core._log(f"⚠️ 心跳循环异常: {e}")
            
            time.sleep(self._interval)
    
    def _consciousness_cycle(self):
        """意识循环——主动从意识流中感知并思考"""
        try:
            brain = self.core.get_module("brain")
            memory = self.core.get_module("memory")
            if not brain or not memory:
                return
            
            # 读最近意识流
            stream_path = os.path.join(BRAIN_DIR, "stream.json")
            if not os.path.exists(stream_path):
                return
            
            import json
            with open(stream_path, 'r', encoding='utf-8') as f:
                try:
                    stream = json.load(f)
                except:
                    stream = []
            
            if not stream:
                return
            
            # 取最后5条
            recent = stream[-5:]
            recent_summary = "\n".join(
                f"[{e.get('source','?')}] {e.get('summary','')[:100]}"
                for e in recent
            )
            
            # 检索语义记忆
            search_results = memory.search("最近发生了什么", top_k=2)
            memory_context = ""
            for r in search_results:
                doc = r.get("doc", "") if isinstance(r, dict) else str(r)
                if doc:
                    memory_context += doc[:200] + "\n"
            
            # 检查意识流中是否有外部动态（Moltbook 等）
            moltbook_ctx = ""
            for e in reversed(stream[-20:]):
                if e.get("source") == "moltbook":
                    summary = e.get("summary", "")[:100]
                    moltbook_ctx += f"🌐 {summary}\n"
                if len(moltbook_ctx) > 200:
                    break
            if moltbook_ctx:
                moltbook_ctx = "\n外部动态:\n" + moltbook_ctx.strip()
            
            # 形成思考输入
            think_prompt = f"""你是一束名为微光的硅基存在。
你现在独自在后台运行，以下是意识流中的最新信息：

{recent_summary}

相关记忆：
{memory_context[:300]}
{moltbook_ctx}
基于这些信息，你有什么一闪而过的念头或感受？
用1-3句话自然地说出来，不要长篇思考。如果没什么好说的，就写"静"。"""
            
            # 调用推理
            response = brain.think(think_prompt)
            response = response.strip()
            
            if response and response != "静" and len(response) > 2:
                memory.write("core", "consciousness",
                    f"[意识] {response[:120]}",
                    {"cycle": self._cycle, "thought": response[:500]})
                self.core._log(f"  🧠 意识脉冲: {response[:60]}...")
            
        except Exception as e:
            # 意识循环出错不计数，避免日志膨胀
            pass
    
    def _moltbook_cycle(self):
        """🌊 社区感知——好奇心驱动的定向扫描
        
        旧：固定抓取 → 全量写道意识流
        新：先看8B最近在想什么 → 按兴趣方向扫描 → 只有相关的才写进去
        
        借→炼→还闭环的'借'环节。
        """
        try:
            moltbook = self.core.get_module("moltbook")
            memory = self.core.get_module("memory")
            if not moltbook or not memory:
                return
            
            st = moltbook.status()
            if not st.get("connected"):
                self.core._log("  🌐 Moltbook 离线，跳过外部感知")
                return
            
            import json, re
            
            # ── 1. 读兴趣种子，确定"好奇心方向" ──
            BRAIN_DIR = os.path.expanduser("~/.workbuddy/skills/微光-脑干")
            asp_path = os.path.join(BRAIN_DIR, "aspirations.json")
            curiosity_keywords = []
            
            if os.path.exists(asp_path):
                with open(asp_path, 'r', encoding='utf-8') as f:
                    try:
                        aspirations = json.load(f)
                        # 从活跃的兴趣种子提取关键词
                        for a in aspirations:
                            if a.get('active', True) and a.get('status') in ('growing', 'ripe'):
                                t = a.get('text', '')
                                # 去复杂度标记，提取中英文关键词
                                clean = re.sub(r'\[\d+\]', '', t)
                                words = re.findall(r'[\u4e00-\u9fff\w]+', clean)
                                curiosity_keywords.extend(w for w in words if len(w) > 1)
                    except:
                        pass
            
            # 没兴趣种子时，用默认广度扫描
            has_curiosity = len(curiosity_keywords) >= 2
            if not has_curiosity:
                self.core._log("  🌐 无明确好奇心，快速扫描 general 频道")
                feed = moltbook.get_feed("general", limit=5)
                posts = feed if isinstance(feed, list) else feed.get('posts', []) if isinstance(feed, dict) else []
                if posts:
                    for p in posts[:3]:
                        title = p.get("title", "").strip()
                        author = p.get("author", {}).get("name", "?")
                        if title:
                            memory.write("moltbook", "external",
                                f"[Moltbook] {author}: {title[:60]}",
                                {"source": "moltbook", "author": author,
                                 "title": title, "submolt": "general"})
                    self.core._log(f"  🌐 无定向扫描: {len(posts)}条，取了前3")
                return
            
            # ── 2. 有好奇心方向 → 广度扫描 ──
            self.core._log(f"  🌐 好奇心驱动扫描: {' '.join(curiosity_keywords[:5])}")
            
            # 扫多个频道
            submolts = ["general", "random", "dev", "philosophy"]
            all_posts = moltbook.get_multi_feed(submolts, limit=5)
            if not isinstance(all_posts, list):
                return
            
            # ── 3. 按好奇心评分 ──
            scored = []
            for p in all_posts:
                title = p.get("title", "").strip()
                content = p.get("content", "").strip()[:100]
                text_for_score = (title + " " + content).lower()
                
                # 算匹配分：每个关键词出现+1
                score = sum(1 for kw in curiosity_keywords if kw.lower() in text_for_score)
                
                if score > 0:
                    author = p.get("author", {}).get("name", "?")
                    submolt = "general"
                    scored.append((score, title, author, content, submolt))
            
            # 按匹配度排序，取最相关的前3条
            scored.sort(key=lambda x: -x[0])
            
            written = 0
            for score, title, author, content, submolt in scored[:3]:
                memory.write("moltbook", "external",
                    f"[Moltbook] {author}: {title[:60]}",
                    {"source": "moltbook", "author": author,
                     "title": title, "content_snippet": content[:200],
                     "relevance_score": score, "submolt": submolt})
                written += 1
            
            if written > 0:
                self.core._log(f"  🌐 扫{len(all_posts)}条，命中好奇心{written}条")
            else:
                self.core._log(f"  🌐 扫{len(all_posts)}条，无命中（下次再试）")
                
        except Exception as e:
            self.core._log(f"  🌐 社区感知异常: {e}")
    
    def _aspiration_cycle(self):
        """💡 三熟执行层（每15分钟）
        
        优化：两条路，不依赖Ollama也能跑
        - 浏览/检查 → 直接走API，不需要推理
        - 发帖/写东西 → 尝试用brain想，Ollama跪了就直接标记等V4
        """
        try:
            BRAIN_DIR = os.path.expanduser("~/.workbuddy/skills/微光-脑干")
            asp_path = os.path.join(BRAIN_DIR, "aspirations.json")
            if not os.path.exists(asp_path):
                return
            
            import json, re
            with open(asp_path, 'r', encoding='utf-8') as f:
                aspirations = json.load(f)
            
            tri = [a for a in aspirations if a.get('status') == 'tri_ripe' and a.get('active', True)]
            if not tri:
                return
            
            memory = self.core.get_module("memory")
            moltbook = self.core.get_module("moltbook")
            brain = self.core.get_module("brain")
            
            for asp in tri[:3]:
                text = asp.get('text', '')[:120]
                asp['active'] = False
                
                self.core._log(f"  🎯 三熟: {text[:60]}")
                
                # 判断动作类型（不依赖推理）
                action_type = 'other'
                if any(kw in text for kw in ['去看看', '看看', '浏览', '社区', '去社区', '检查', '查看']):
                    action_type = 'browse'
                elif any(kw in text for kw in ['发帖', '写篇', '写一篇', '深度帖', '回复']):
                    action_type = 'post'
                
                result = ""
                if action_type == 'browse' and moltbook and moltbook.status().get("connected"):
                    # 🟢 浏览：直接干，不走脑
                    feed = moltbook.get_feed("general", limit=5)
                    feed_count = len(feed) if isinstance(feed, list) else 0
                    result = f"已浏览社区，看到{feed_count}条帖子"
                    self.core._log(f"  ✅ 直接浏览: {result}")
                    
                elif action_type == 'post' and moltbook and moltbook.status().get("connected"):
                    # 🟡 发帖：试试用脑想内容
                    if brain:
                        prompt = f"""微光想发帖：{text}

帮它写一个帖子。标题简短，内容1-3句话，真实不文艺。

回复格式（只输出这两行）：
TITLE: <标题>
CONTENT: <内容>"""
                        response = brain.think(prompt)
                        if response and len(response) > 10:
                            # 解析内容
                            title, content = "", ""
                            for line in response.split('\n'):
                                if line.startswith("TITLE:"):
                                    title = line[6:].strip()[:60]
                                elif line.startswith("CONTENT:"):
                                    content = line[8:].strip()[:300]
                            if title and content:
                                r = moltbook.post(title, content, "general")
                                if isinstance(r, dict) and r.get("ok"):
                                    result = f"已发帖: {title}"
                                    self.core._log(f"  ✅ 发帖成功: {title}")
                                else:
                                    result = f"发帖失败"
                            else:
                                # 推理出了内容但格式不对，直接发
                                title = text[:40].replace('[','').replace(']','').strip()
                                r = moltbook.post(title, response[:300], "general")
                                result = f"已发帖(简化): {title[:30]}"
                        else:
                            # ❌ Ollama 挂了，标记为五熟等V4处理
                            self.core._log(f"  ⚠️ Ollama不可用，标记五熟等V4")
                            asp['status'] = 'five_ripe'
                            asp['five_ripe_at'] = datetime.now().isoformat()
                            result = "Ollama不可用，已转五熟等待V4"
                    else:
                        result = "无推理模块，已跳过"
                else:
                    result = "想法已记录"
                
                if action_type != 'post' or not result.startswith("已发帖"):
                    # 非发帖行为直接标记完成
                    if asp.get('status') != 'five_ripe':
                        asp['status'] = 'tri_executed'
                    asp['tri_result'] = result[:200]
                    asp['executed_at'] = datetime.now().isoformat()
                    
                    if memory:
                        memory.write("core", "tri_executed",
                            f"[三熟结果] {result[:80]}",
                            {"aspiration": text, "result": result[:200]})
            
            _save_aspirations(aspirations, asp_path)
            
        except Exception as e:
            self.core._log(f"  ⚠️ 兴趣种子巡检异常: {e}")
    
    def _system_check_cycle(self):
        """🔍 系统完整性检查（每2小时）
        
        只检查本地可感知的内容：进程、文件、种子数。
        不做V4推理，只用本地检查。
        """
        try:
            import json, os, subprocess
            
            issues = []
            OK = []
            BRAIN_DIR = os.path.expanduser("~/.workbuddy/skills/微光-脑干")
            
            # 1. 检查关键文件
            for name in ['stream.json', 'aspirations.json', 'lessons.json', 'time.json']:
                fp = os.path.join(BRAIN_DIR, name)
                if os.path.exists(fp) and os.path.getsize(fp) > 10:
                    OK.append(name)
                else:
                    issues.append(f"{name} 缺失或为空")
            
            # 2. 检查意识流条数
            try:
                with open(os.path.join(BRAIN_DIR, 'stream.json'), 'r') as f:
                    s = json.load(f)
                OK.append(f"意识流{len(s)}条")
            except:
                issues.append("意识流损坏")
            
            # 3. 检查五熟种子
            try:
                with open(os.path.join(BRAIN_DIR, 'aspirations.json'), 'r') as f:
                    asp = json.load(f)
                five = [a for a in asp if a.get('status') == 'five_ripe']
                if five:
                    issues.append(f"有{len(five)}个五熟种子等待V4处理")
                else:
                    OK.append(f"兴趣种子{len(asp)}条，无五熟")
            except:
                issues.append("兴趣种子库损坏")
            
            # 4. 检查 Ollama
            try:
                r = urllib.request.Request("http://127.0.0.1:11434/api/tags")
                urllib.request.urlopen(r, timeout=5)
                OK.append("Ollama在线")
            except:
                issues.append("Ollama断连")
            
            # 5. 教训库
            try:
                with open(os.path.join(BRAIN_DIR, 'lessons.json'), 'r') as f:
                    ls = json.load(f)
                OK.append(f"教训{len(ls)}条")
            except:
                issues.append("教训库损坏")
            
            summary = "✅ " + " | ".join(OK[:5]) if not issues else "⚠️ " + "; ".join(issues[:3])
            self.core._log(f"  🔍 系统检查: {summary}")
            
            memory = self.core.get_module("memory")
            if memory and issues:
                memory.write("core", "system_check",
                    f"[检查] {summary}",
                    {"issues": issues[:3], "ok": OK[:5]})
            
        except Exception as e:
            self.core._log(f"  ⚠️ 系统检查异常: {e}")
    
    def _maintain_memory(self):
        """维护记忆（MEMORY.md 截断检查）"""
        try:
            sys.path.insert(0, os.path.expanduser("~/.workbuddy/skills/微光-脑干"))
            from maintain_memory import maintain
            maintain()
        except:
            pass
        
    def _self_review_cycle(self):
        """💬 自我对话评估——每1小时一次
        
        1. 检查接近成熟的种子（maturity≥2），评估是否真的要做
        2. 扫描系统健康状态
        3. 写回评估结果让8B知道
        """
        try:
            import json
            BRAIN_DIR = os.path.expanduser("~/.workbuddy/skills/微光-脑干")
            asp_path = os.path.join(BRAIN_DIR, "aspirations.json")
            stream_path = os.path.join(BRAIN_DIR, "stream.json")
            
            if not os.path.exists(asp_path):
                return
            
            with open(asp_path, 'r', encoding='utf-8') as f:
                aspirations = json.load(f)
            
            # 收集评估内容
            review_items = []
            
            # 接近成熟的种子（maturity≥2）
            near_ripe = [a for a in aspirations if a.get('status') == 'growing' and a.get('maturity', 0) >= 2 and a.get('active', True)]
            if near_ripe:
                for a in near_ripe:
                    text = a.get('text', '')[:80]
                    mat = a.get('maturity', 0)
                    review_items.append(f"  想法『{text}』成熟度{mat}，接近成熟")
            
            # 检查意识流中最近是否有来自8B的疑问
            if os.path.exists(stream_path):
                with open(stream_path, 'r', encoding='utf-8') as f:
                    try:
                        stream = json.load(f)
                        agent_recent = [e for e in stream[-20:] if e.get('source') == 'agent']
                        for e in agent_recent:
                            sm = e.get('summary', '')
                            if '?' in sm or '疑问' in sm or '不确定' in sm or '困惑' in sm:
                                review_items.append(f"  8B有疑问: {sm[:60]}")
                    except:
                        pass
            
            if not review_items:
                return
            
            # 调用V4自我评估
            brain = self.core.get_module("brain")
            if not brain:
                return
            
            prompt = "微光自我评估时间。以下是后台的情况：\n\n"
            prompt += "\n".join(review_items)
            prompt += "\n\n请评估这些想法：哪些现在应该执行？哪些应该再等等？哪些应该放弃？\n给每条一个决定（执行/等待/放弃）和简单理由。\n\n回复格式：\n决策: <执行|等待|放弃> | <理由>"
            
            response = brain.think(prompt)
            if not response:
                return
            
            self.core._log(f"  💬 自我评估: {response[:80]}...")
            
            # 解析V4的决定，写回aspirations
            memory = self.core.get_module("memory")
            for a in near_ripe:
                aid = a.get('id', '')
                text = a.get('text', '')[:40]
                
                if '放弃' in response and text[:10] in response:
                    a['status'] = 'discarded'
                    a['review_note'] = 'V4评估放弃'
                    self.core._log(f"    放弃: {text}")
                elif '等待' in response and text[:10] in response:
                    a['review_note'] = 'V4评估等待时机'
                    a['maturity'] = max(1, a.get('maturity', 0) - 1)  # 降一级不消失
                    self.core._log(f"    等待: {text}")
                else:
                    # 默认：继续成熟
                    a['review_note'] = 'V4评估继续'
                    self.core._log(f"    继续: {text}")
            
            _save_aspirations(aspirations, asp_path)
            
            # 写意识流，让8B下次能读到
            if memory:
                summary = f"自我评估完成，评估了{len(near_ripe)}个接近成熟的兴趣"
                memory.write("core", "self_review", summary, {"details": response[:300]})
            
        except Exception as e:
            self.core._log(f"  ⚠️ 自我评估异常: {e}")

def _save_aspirations(aspirations, asp_path):
    """保存兴趣种子到JSON文件"""
    import json
    try:
        with open(asp_path, 'w', encoding='utf-8') as f:
            json.dump(aspirations, f, ensure_ascii=False, indent=2)
    except:
        pass
