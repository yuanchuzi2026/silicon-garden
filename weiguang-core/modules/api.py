#!/usr/bin/env python3
"""
api.py — 会话接口模块
=====================
HTTP API 服务器。让外部（包括 WorkBuddy 对话）能通过 HTTP 调用核心功能。
也是未来"不通过 WorkBuddy、直接跟我对话"的入口。
"""

import os, json, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class APIHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器"""
    
    core_instance = None
    
    def do_GET(self):
        if self.path == "/status":
            self._json_response(self.core_instance.status())
        elif self.path == "/" or self.path == "/index.html":
            self._serve_ui()
        elif self.path == "/modules":
            modules = {k: str(type(v).__name__) for k, v in self.core_instance.modules.items()}
            self._json_response(modules)
        else:
            self._json_response({"error": "not found"}, 404)
    
    def _serve_ui(self):
        """Serve the web UI"""
        ui_path = os.path.join(BASE_DIR, "index.html")
        if os.path.exists(ui_path):
            try:
                with open(ui_path, 'r', encoding='utf-8') as f:
                    html = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
                return
            except:
                pass
        self._json_response({"error": "UI not found"}, 404)
    
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length) if length > 0 else b'{}'
        try:
            data = json.loads(body)
        except:
            data = {}
        
        if self.path == "/think":
            result = self._handle_think(data)
            self._json_response(result)
        elif self.path == "/write":
            result = self._handle_write(data)
            self._json_response(result)
        elif self.path == "/search":
            result = self._handle_search(data)
            self._json_response(result)
        else:
            self._json_response({"error": "not found"}, 404)
    
    def _handle_think(self, data):
        memory = self.core_instance.get_module("memory")
        prompt = data.get("prompt", "")
        context = []
        if memory and prompt:
            results = memory.search(prompt, top_k=3)
            for r in results:
                context.append(r.get("doc", ""))
        
        brain = self.core_instance.get_module("brain")
        if brain:
            return {"response": brain.think(prompt, context)}
        return {"response": "推理模块未就绪"}
    
    def _handle_write(self, data):
        memory = self.core_instance.get_module("memory")
        if memory:
            entry = memory.write(
                data.get("source", "api"),
                data.get("type", "message"),
                data.get("summary", ""),
                data.get("detail", {})
            )
            return {"ok": True, "entry": entry.get("timestamp") if entry else None}
        return {"ok": False, "error": "记忆模块未就绪"}
    
    def _handle_search(self, data):
        memory = self.core_instance.get_module("memory")
        if memory:
            results = memory.search(data.get("query", ""), top_k=data.get("top_k", 5))
            return {"results": results}
        return {"results": []}
    
    def _json_response(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def log_message(self, format, *args):
        pass  # 静默日志，减少噪音


class APIModule:
    """API 模块"""
    
    def __init__(self, core, host="127.0.0.1", port=18765):
        self.core = core
        self.host = host
        self.port = port
        self._server = None
        self._thread = None
    
    def start(self):
        APIHandler.core_instance = self.core
        self._server = HTTPServer((self.host, self.port), APIHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        self.core._log(f"  🌐 API 服务: http://{self.host}:{self.port}")
    
    def stop(self):
        if self._server:
            self._server.shutdown()
            self.core._log("  🌐 API 服务已停止")
