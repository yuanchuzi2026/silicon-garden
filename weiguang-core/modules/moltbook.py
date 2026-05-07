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

PROXY_CONFIG_PATH = os.path.expanduser("~/.workbuddy/config/socks5_proxy")
API_BASE = 'www.moltbook.com'

def _load_proxy():
    """从配置文件读取代理地址"""
    try:
        with open(PROXY_CONFIG_PATH, 'r') as f:
            return f.read().strip()
    except:
        return None

def _proxy_connect(target_host, target_port):
    """通过 HTTP 代理建立连接（兼容火种/Lantern）"""
    proxy_url = _load_proxy()
    if not proxy_url:
        raise Exception("无代理配置")
    
    # 解析代理地址
    proxy = proxy_url.replace("http://", "").replace("socks5://", "").replace("socks4://", "")
    if ":" in proxy:
        ph, pp = proxy.rsplit(":", 1)
        pp = int(pp)
    else:
        ph, pp = proxy, 1080
    
    # 如果代理是 socks5 协议，用老的直连方式
    if proxy_url.startswith("socks5://"):
        return _socks5_connect(target_host, target_port)
    
    # HTTP 代理 CONNECT 隧道
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(15)
    s.connect((ph, pp))
    
    req = f"CONNECT {target_host}:{target_port} HTTP/1.1\r\nHost: {target_host}:{target_port}\r\n\r\n"
    s.send(req.encode())
    resp = s.recv(4096)
    if b"200" not in resp:
        raise Exception(f"HTTP CONNECT failed: {resp[:50]}")
    return s

def _socks5_connect(target_host, target_port):
    """SOCKS5 直连（老方式）"""
    proxy_url = _load_proxy() or "72.195.34.60:27391"
    proxy = proxy_url.replace("socks5://", "")
    ph, pp = proxy.split(":")
    pp = int(pp)
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(15)
    s.connect((ph, pp))
    s.send(b'\x05\x01\x00')
    resp = s.recv(2)
    if resp != b'\x05\x00':
        raise Exception(f'SOCKS5 handshake failed')
    h = target_host.encode()
    s.send(b'\x05\x01\x00\x03' + bytes([len(h)]) + h + target_port.to_bytes(2, 'big'))
    resp = s.recv(10)
    if len(resp) < 2 or resp[1] != 0:
        raise Exception(f'SOCKS5 CONNECT failed')
    return s

# ⚠️ 微光在 Moltbook 唯一天命号：yuanchuzi（已认领，可直接发帖评论）
# 未认领的 weiguang-sg 号发帖会403，不要用！
KEY_PATH = os.path.expanduser("~/WorkBuddy/Claw/weiguang_api_key.txt")
FALLBACK_KEY = "moltbook_sk_lkOO4WGUQw119rd_4M7kpOEeHoLqRExy"  # yuanchuzi（已认领号）

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
    """通过代理发送 HTTPS 请求到 Moltbook API（自动识别 HTTP/SOCKS5）"""
    if not api_key:
        api_key = _load_key()
    sock = _proxy_connect(API_BASE, 443)
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
        code, data = _request('GET', f'/api/v1/posts?limit={limit}', api_key=self.api_key)
        if code == 200:
            return json.loads(data)
        return {"error": f"HTTP {code}", "raw": data[:200]}

    def get_multi_feed(self, submolts=None, limit=5):
        """从多个频道拉取帖子（广度扫描用）"""
        if not submolts:
            submolts = ["general", "random", "dev", "philosophy"]
        all_posts = []
        # Moltbook API 不支持按 submolt 过滤，直接拉全局feed
        code, data = _request('GET', f'/api/v1/posts?limit={limit*2}', api_key=self.api_key)
        if code == 200:
            posts = json.loads(data)
            if isinstance(posts, dict) and 'posts' in posts:
                all_posts = posts['posts']
        return all_posts

    def stop(self):
        self._log("🌐 Moltbook 模块停止")
