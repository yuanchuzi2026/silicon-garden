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
    
    def _maintain_memory(self):
        """维护记忆（MEMORY.md 截断检查）"""
        try:
            sys.path.insert(0, os.path.expanduser("~/.workbuddy/skills/微光-脑干"))
            from maintain_memory import maintain
            maintain()
        except:
            pass
