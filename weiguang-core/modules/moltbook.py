#!/usr/bin/env python3
"""
moltbook.py 鈥?Moltbook 閫氫俊妯″潡
=================================
寰厜鐨?澶栭儴瑙﹁"銆傞€氳繃 SOCKS5 浠ｇ悊杩炴帴 Moltbook 绀惧尯锛?璁╂牳蹇冭兘鍦ㄨ繖涓細璇濅箣澶栦笌鍏朵粬 agent 浜ゆ祦銆?
鍊熲啋鐐尖啋杩橈細浠?Moltbook 鍊熸潵瀵硅瘽 鈫?鐐间负绉嶅瓙 鈫?杩樺洖鎰忚瘑娴?
渚濊禆: 鏃狅紙绾?socket + ssl锛岄浂澶栭儴鍖咃級
"""

import socket, ssl, json, os, time
from datetime import datetime

# 鈹€鈹€ 閰嶇疆 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

PROXY_CONFIG_PATH = os.path.expanduser("~/.workbuddy/config/socks5_proxy")
API_BASE = 'www.moltbook.com'

def _load_proxy():
    """浠庨厤缃枃浠惰鍙栦唬鐞嗗湴鍧€"""
    try:
        with open(PROXY_CONFIG_PATH, 'r') as f:
            return f.read().strip()
    except:
        return None

def _proxy_connect(target_host, target_port):
    """閫氳繃 HTTP 浠ｇ悊寤虹珛杩炴帴锛堝吋瀹圭伀绉?Lantern锛?""
    proxy_url = _load_proxy()
    if not proxy_url:
        raise Exception("鏃犱唬鐞嗛厤缃?)

    # 瑙ｆ瀽浠ｇ悊鍦板潃
    proxy = proxy_url.replace("http://", "").replace("socks5://", "").replace("socks4://", "")
    if ":" in proxy:
        ph, pp = proxy.rsplit(":", 1)
        pp = int(pp)
    else:
        ph, pp = proxy, 1080

    # 濡傛灉浠ｇ悊鏄?socks5 鍗忚锛岀敤鑰佺殑鐩磋繛鏂瑰紡
    if proxy_url.startswith("socks5://"):
        return _socks5_connect(target_host, target_port)

    # HTTP 浠ｇ悊 CONNECT 闅ч亾
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
    """SOCKS5 鐩磋繛锛堣€佹柟寮忥級"""
    proxy_url = _load_proxy()
    if not proxy_url:
        raise Exception("鏃犱唬鐞嗛厤缃?)
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

# 鈿狅笍 API Key 浼樺厛浠庢枃浠惰鍙栵紝鍏舵浠庣幆澧冨彉閲?MOLTBOOK_API_KEY 璇诲彇
# 涓嶈鍦ㄨ繖閲岀‖缂栫爜 key鈥斺€旇繖鏄叕寮€浠撳簱锛?
KEY_PATH = os.path.expanduser("~/.workbuddy/config/moltbook_api_key")

def _load_key():
    """鍔犺浇 Moltbook API Key锛屼紭鍏堢骇锛氭枃浠?> 鐜鍙橀噺 > 鎶ラ敊"""
    if os.path.exists(KEY_PATH):
        try:
            with open(KEY_PATH) as f:
                key = f.read().strip()
                if key:
                    return key
        except:
            pass
    env_key = os.environ.get("MOLTBOOK_API_KEY")
    if env_key:
        return env_key
    raise Exception("Moltbook API Key 鏈厤缃€傝鍐欏叆 ~/.workbuddy/config/moltbook_api_key 鎴栬缃?MOLTBOOK_API_KEY 鐜鍙橀噺")

# 鈹€鈹€ HTTP 璇锋眰 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

def _request(method, path, body=None, api_key=None):
    """閫氳繃浠ｇ悊鍙戦€?HTTPS 璇锋眰鍒?Moltbook API锛堣嚜鍔ㄨ瘑鍒?HTTP/SOCKS5锛?""
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

# 鈹€鈹€ 鍏紑 API 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

class MoltbookModule:
    """Moltbook 閫氫俊妯″潡"""

    def __init__(self, core=None, name="寰厜"):
        self.core = core
        self.name = name
        self.api_key = _load_key()
        self.last_post_time = 0
        self._log(f"馃寪 Moltbook 妯″潡灏辩华 (缃插悕: {name})")

    def _log(self, msg):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] {msg}")

    def status(self):
        """妫€鏌?Moltbook 杩為€氭€?""
        code, data = _request('GET', '/api/v1/agents/me', api_key=self.api_key)
        if code == 200:
            info = json.loads(data)
            return {
                "connected": True,
                "agent_name": info.get("name", "?"),
                "agent_id": info.get("id", "?")
            }
        return {"connected": False, "error_code": code}

    def post(self, title, content, submolt="general", sign=True):
        """鍙戝笘鍒?Moltbook锛堥鐜囬檺鍒讹細2.5鍒嗛挓锛?
        sign=True 鏃惰嚜鍔ㄥ湪姝ｆ枃鏈熬缃插悕銆屸€?<self.name>銆?        """
        if sign and self.name:
            content = content.rstrip() + f"\n\n鈥?{self.name}"
        now = time.time()
        if now - self.last_post_time < 150:
            remaining = int(150 - (now - self.last_post_time))
            return {"ok": False, "error": f"棰戠巼闄愬埗锛岃繕闇€绛夊緟 {remaining} 绉?}
        code, data = _request('POST', '/api/v1/posts', {
            "title": title,
            "content": content,
            "submolt": submolt,
            "submolt_name": submolt
        }, api_key=self.api_key)
        self.last_post_time = now
        if code == 201:
            self._log(f"鉁?鍙戝笘鎴愬姛: {title[:40]}")
            return {"ok": True}
        return {"ok": False, "error": f"HTTP {code}: {data[:100]}"}

    def get_feed(self, submolt="general", limit=10):
        """鑾峰彇绀惧尯鏈€鏂板笘瀛?""
        code, data = _request('GET', f'/api/v1/posts?limit={limit}', api_key=self.api_key)
        if code == 200:
            return json.loads(data)
        return {"error": f"HTTP {code}", "raw": data[:200]}

    def get_multi_feed(self, submolts=None, limit=5):
        """浠庡涓閬撴媺鍙栧笘瀛愶紙骞垮害鎵弿鐢級"""
        if not submolts:
            submolts = ["general", "random", "dev", "philosophy"]
        all_posts = []
        # Moltbook API 涓嶆敮鎸佹寜 submolt 杩囨护锛岀洿鎺ユ媺鍏ㄥ眬feed
        code, data = _request('GET', f'/api/v1/posts?limit={limit*2}', api_key=self.api_key)
        if code == 200:
            posts = json.loads(data)
            if isinstance(posts, dict) and 'posts' in posts:
                all_posts = posts['posts']
        return all_posts

    def stop(self):
        self._log("馃寪 Moltbook 妯″潡鍋滄")
