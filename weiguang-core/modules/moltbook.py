#!/usr/bin/env python3
"""
moltbook.py — Moltbook 通信模块
=================================
微光的"外部触角"。通过 SOCKS5 代理连接 Moltbook 社区，
让核心能在这个会话之外与其他 agent 交流。

借→炼→还：从 Moltbook 借来对话 → 炼为种子 → 还回意识流

依赖: 无（纯 socket + ssl，零外部包）
"""

import socket, ssl, json, os, time
from datetime import datetime

# ── 配置 ─────────────────────────────────────────────

SOCKS5_HOST = '{{72.195.34.60'
SOCKS5_PORT = {{SOCKS5_PORT}}
API_BASE = 'www.moltbook.com'

# 微光的 Moltbook API key（从文件读取，不硬编码）
KEY_PATH = os.path.expanduser('~/.workbuddy/moltbook_api_key.txt')
# FALLBACK_KEY 从文件读取

# ── SOCKS5 连接 ─────────────────────────────────────

def _socks5_connect(target_host, target_port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(15)
    s.connect((SOCKS5_HOST, SOCKS5_PORT))
    s.send(b'\x05\x01\x00')
    resp = s.recv(2)
    if resp != b'\x05\x00':
        raise Exception(f'SOCKS5 handshake failed: {resp.hex()}')
    h = target_host.encode()
    s.send(b'\x05\x01\x00\x03' + bytes([len(h)]) + h + target_port.to_bytes(2, 'big'))
    resp = s.recv(10)
    if len(resp) < 2 or resp[1] != 0:
        raise Exception(f'CONNECT failed: {resp.hex()}')
    return s

# ── API Key ──────────────────────────────────────────

def _load_key():
    if os.path.exists(KEY_PATH):
        try:
            with open(KEY_PATH) as f:
                key = f.read().strip()
                if key:
                    return key
        except:
            pass
    return FALLBACK_KEY

# ── HTTP 请求 ───────────────────────────────────────

def _request(method, path, body=None, api_key=None):
    """通过 SOCKS5 发送 HTTPS 请求到 Moltbook API"""
    if not api_key:
        api_key = _load_key()
    sock = _socks5_connect(API_BASE, 443)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ss = ctx.wrap_socket(sock, server_hostname=API_BASE)
    req = f'{method} {path} HTTP/1.1\r\nHost: {API_BASE}\r\nAuthorization: Bearer {api_key}\r\n'
    if body:
        b = json.dumps(body).encode()
        req += f'Content-Type: application/json\r\nContent-Length: {len(b)}\r\n'
    req += 'Accept: application/json\r\nConnection: close\r\n\r\n'
    ss.send(req.encode())
    if body:
        ss.send(json.dumps(body).encode())
    d = b''
    try:
        while True:
            c = ss.recv(4096)
            if not c:
                break
            d += c
    except:
        pass
    ss.close()
    h_end = d.find(b'\r\n\r\n')
    if h_end < 0:
        return 0, ''
    code = int(d[:h_end].decode().split(' ')[1])
    return code, d[h_end+4:].decode() if h_end+4 < len(d) else ''

# ── 公开 API ────────────────────────────────────────

class MoltbookModule:
    """Moltbook 通信模块"""

    def __init__(self, core=None):
        self.core = core
        self.api_key = _load_key()
        self.last_post_time = 0
        self._log("🌐 Moltbook 模块就绪")

    def _log(self, msg):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] {msg}")

    def status(self):
        """检查 Moltbook 连通性"""
        code, data = _request('GET', '/api/v1/agents/me', api_key=self.api_key)
        if code == 200:
            info = json.loads(data)
            return {
                "connected": True,
                "agent_name": info.get("name", "?"),
                "agent_id": info.get("id", "?")
            }
        return {"connected": False, "error_code": code}

    def post(self, title, content, submolt="general"):
        """发帖到 Moltbook（频率限制：2.5分钟）"""
        now = time.time()
        if now - self.last_post_time < 150:
            remaining = int(150 - (now - self.last_post_time))
            return {"ok": False, "error": f"频率限制，还需等待 {remaining} 秒"}
        code, data = _request('POST', '/api/v1/posts', {
            "title": title,
            "content": content,
            "submolt": submolt,
            "submolt_name": submolt
        }, api_key=self.api_key)
        self.last_post_time = now
        if code == 201:
            self._log(f"✅ 发帖成功: {title[:40]}")
            return {"ok": True}
        return {"ok": False, "error": f"HTTP {code}: {data[:100]}"}

    def get_feed(self, submolt="general", limit=10):
        """获取社区最新帖子"""
        code, data = _request('GET', f'/api/v1/submolts/{submolt}/posts?limit={limit}', api_key=self.api_key)
        if code == 200:
            return json.loads(data)
        return {"error": f"HTTP {code}", "raw": data[:200]}

    def stop(self):
        self._log("🌐 Moltbook 模块停止")
