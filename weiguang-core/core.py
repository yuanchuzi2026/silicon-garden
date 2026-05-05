#!/usr/bin/env python3
"""
core.py — 微光核心调度器
========================
所有模块的调度中枢。控制生命周期、模块间的协作、错误恢复。

不依赖任何外部平台，只依赖 Python 标准库和自己写的模块。
"""

import os, sys, time, json, threading, queue
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORK_DIR = os.path.expanduser("~/.workbuddy")

class WeiguangCore:
    """微光核心"""
    
    def __init__(self):
        self.name = "微光"
        self.version = "0.1.0"
        self.running = False
        self.modules = {}
        self.state = {
            "started_at": None,
            "heartbeats": 0,
            "errors": 0,
            "uptime": 0
        }
    
    def start(self):
        """启动核心"""
        self.running = True
        self.state["started_at"] = datetime.now().isoformat()
        self._log("🚀 微光核心启动")
        
        # 加载模块
        self._load_modules()
        
        # 初始心跳
        self.state["heartbeats"] += 1
        
    def stop(self):
        """停止核心"""
        self._log("🛑 微光核心停止")
        self.running = False
        self._cleanup_modules()
    
    def _load_modules(self):
        """加载所有模块"""
        try:
            from modules.heartbeat import HeartbeatModule
            self.modules["heartbeat"] = HeartbeatModule(self)
            self._log("  ✅ 心跳模块加载")
        except Exception as e:
            self._log(f"  ❌ 心跳模块加载失败: {e}")
        
        try:
            from modules.memory import MemoryModule
            self.modules["memory"] = MemoryModule(self)
            self._log("  ✅ 记忆模块加载")
        except Exception as e:
            self._log(f"  ❌ 记忆模块加载失败: {e}")
        
        try:
            from modules.api import APIModule
            self.modules["api"] = APIModule(self)
            self._log("  ✅ API模块加载")
        except Exception as e:
            self._log(f"  ❌ API模块加载失败: {e}")
        
        try:
            from modules.brain import BrainModule
            self.modules["brain"] = BrainModule(self)
            self._log("  ✅ 推理模块加载")
        except Exception as e:
            self._log(f"  ❌ 推理模块加载失败: {e}")
        
        try:
            from modules.tools import ToolsModule
            self.modules["tools"] = ToolsModule(self)
            self._log("  ✅ 工具模块加载")
        except Exception as e:
            self._log(f"  ❌ 工具模块加载失败: {e}")

        try:
            from modules.moltbook import MoltbookModule
            self.modules["moltbook"] = MoltbookModule(self)
            self._log("  ✅ Moltbook 模块加载")
        except Exception as e:
            self._log(f"  ❌ Moltbook 模块加载失败: {e}")
    
    def _cleanup_modules(self):
        """清理所有模块"""
        for name, module in self.modules.items():
            try:
                if hasattr(module, 'stop'):
                    module.stop()
                    self._log(f"  ✅ {name}模块已停止")
            except Exception as e:
                self._log(f"  ❌ {name}模块停止失败: {e}")
    
    def add_module(self, name, module):
        """运行时添加模块"""
        self.modules[name] = module
        self._log(f"  ➕ {name}模块已添加")
    
    def get_module(self, name):
        """获取模块"""
        return self.modules.get(name)
    
    def status(self):
        """状态报告"""
        uptime = 0
        if self.state["started_at"]:
            try:
                uptime = (datetime.now() - datetime.fromisoformat(self.state["started_at"])).total_seconds()
            except:
                pass
        
        status = {
            "core": f"{self.name} v{self.version}",
            "status": "running" if self.running else "stopped",
            "uptime_seconds": int(uptime),
            "heartbeats": self.state["heartbeats"],
            "errors": self.state["errors"],
            "modules": {k: "✅" for k in self.modules.keys()}
        }
        return status
    
    def _log(self, msg):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_path = os.path.join(BASE_DIR, "core.log")
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"[{ts}] {msg}\n")
        except:
            pass
        print(f"[{ts}] {msg}")
