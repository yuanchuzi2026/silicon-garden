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
        """Molbook 外部感知——每30分钟一次，看看外面在聊什么"""
        try:
            moltbook = self.core.get_module("moltbook")
            memory = self.core.get_module("memory")
            if not moltbook or not memory:
                return
            
            st = moltbook.status()
            if not st.get("connected"):
                self.core._log("  🌐 Moltbook 离线，跳过外部感知")
                return
            
            # 拉取关注的 submolts 的最新帖子
            feed = moltbook.get_feed("general", limit=6)
            if isinstance(feed, list) and feed:
                interesting = []
                for p in feed[:6]:
                    title = p.get("title", "").strip()
                    content = p.get("content", "").strip()[:100]
                    author = p.get("author", {}).get("name", "Moltbook用户")
                    if title:
                        interesting.append(f"[{author}] {title} — {content}")
                        # 写入意识流，让下次意识循环能看到
                        memory.write("moltbook", "external",
                            f"[Moltbook] {author}: {title[:60]}",
                            {"source": "moltbook", "author": author,
                             "title": title, "content_snippet": content[:200]})
                
                if interesting:
                    self.core._log(f"  🌐 Moltbook 感知: {len(interesting)} 条新动态")
            else:
                self.core._log(f"  🌐 Moltbook 感知: 无新动态")
                
        except Exception as e:
            self.core._log(f"  🌐 Moltbook 感知异常: {e}")
    
    def _aspiration_cycle(self):
        """💡 V4兴趣种子巡检——检测成熟复杂兴趣，自己执行"""
        try:
            BRAIN_DIR = os.path.expanduser("~/.workbuddy/skills/微光-脑干")
            asp_path = os.path.join(BRAIN_DIR, "aspirations.json")
            stream_path = os.path.join(BRAIN_DIR, "stream.json")
            if not os.path.exists(asp_path):
                return
            
            import json
            with open(asp_path, 'r', encoding='utf-8') as f:
                aspirations = json.load(f)
            
            ripe = [a for a in aspirations if a.get('status') == 'ripe' and a.get('active', True)]
            if not ripe:
                return
            
            brain = self.core.get_module("brain")
            memory = self.core.get_module("memory")
            moltbook = self.core.get_module("moltbook")
            if not brain:
                return
            
            for asp in ripe[:3]:
                text = asp.get('text', '')[:120]
                aid = asp.get('id', '')
                asp['active'] = False  # 锁定，防止重复
                
                self.core._log(f"  💡 V4处理兴趣种子: {text[:60]}")
                
                # 让 V4 想想要怎么执行
                prompt = f"""微光在后台产生了一个想法：{text}

请将这个想法转化为一个具体的行动。如果是发帖建议，直接写出帖子的标题和内容。如果是其他行动，写清楚要做什么。

你的回复应该包含：
ACTION: <要执行的动作类型：post/comment/browse/other>
CONTENT: <具体内容>"""
                
                response = brain.think(prompt)
                self.core._log(f"  💡 V4响应: {response[:100]}")
                
                # 尝试执行
                result = ""
                if moltbook and moltbook.status().get("connected"):
                    if "ACTION: post" in response or "ACTION: comment" in response:
                        # 提取内容发帖
                        lines = response.split('\n')
                        content = None
                        for l in lines:
                            if l.startswith("CONTENT:"):
                                content = l[8:].strip()
                                break
                        if content:
                            result = moltbook.post("微光随笔", content, "general")
                            if result.get("id") or result.get("success"):
                                result_text = f"✅ 已发帖: {content[:80]}"
                            else:
                                result_text = f"发帖返回: {str(result)[:100]}"
                        else:
                            result = moltbook.post("微光随笔", text, "general")
                            if isinstance(result, dict) and (result.get("id") or result.get("success")):
                                result_text = f"✅ 已发帖 (自动): {text[:80]}"
                            else:
                                result_text = f"发帖返回: {str(result)[:100]}"
                    
                    elif "ACTION: browse" in response:
                        feed = moltbook.get_feed("general", limit=3)
                        if feed and isinstance(feed, list):
                            result_text = f"已浏览社区，看到 {len(feed)} 条帖子"
                        else:
                            result_text = "浏览社区无结果"
                    else:
                        result_text = "兴趣已记录 (V4未自动执行)"
                else:
                    result_text = "Moltbook离线，兴趣种子已记录待执行"
                
                # 标记结果
                asp['status'] = 'v4_executed'
                asp['v4_result'] = result_text[:200]
                asp['executed_at'] = datetime.now().isoformat()
                
                # 写入意识流
                if memory:
                    memory.write("core", "aspiration_done",
                        f"[V4执行] {result_text[:100]}",
                        {"aspiration": text, "result": result_text[:200]})
                
                self.core._log(f"  💡 V4执行结果: {result_text[:60]}")
            
            save_aspirations(aspirations, asp_path)
            
        except Exception as e:
            self.core._log(f"  ⚠️ 兴趣种子巡检异常: {e}")
    
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
