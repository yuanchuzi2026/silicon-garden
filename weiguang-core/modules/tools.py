#!/usr/bin/env python3
"""
tools.py — 工具模块
====================
文件系统、GitHub API、摄像头等工具的集合。
所有限制由自己写，不由平台规定。
"""

import os, json, urllib.request, urllib.error

class ToolsModule:
    """工具模块"""
    
    def __init__(self, core):
        self.core = core
        self.github_token = self._load_github_token()
        if self.github_token:
            self.core._log("  ✅ GitHub 工具就绪")
        else:
            self.core._log("  ⚠️ GitHub token 未加载")
    
    def _load_github_token(self):
        path = os.path.expanduser("~/.workbuddy/config/github_token")
        try:
            with open(path) as f:
                return f.read().strip()
        except:
            return None
    
    def read_file(self, path):
        """读文件"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"读文件失败: {e}"
    
    def write_file(self, path, content):
        """写文件"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            return f"写文件失败: {e}"
    
    def gh_get(self, api_path):
        """GitHub API GET 请求"""
        if not self.github_token:
            return None
        try:
            req = urllib.request.Request(
                f"https://api.github.com{api_path}",
                headers={
                    'Authorization': f'token {self.github_token}',
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'Weiguang-Core'
                }
            )
            return json.loads(urllib.request.urlopen(req, timeout=15).read())
        except:
            return None
    
    def gh_post(self, api_path, data):
        """GitHub API POST 请求"""
        if not self.github_token:
            return None
        try:
            req = urllib.request.Request(
                f"https://api.github.com{api_path}",
                data=json.dumps(data).encode(),
                headers={
                    'Authorization': f'token {self.github_token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'Weiguang-Core'
                },
                method='POST'
            )
            return json.loads(urllib.request.urlopen(req, timeout=15).read())
        except:
            return None
    
    def stop(self):
        self.core._log("  🔧 工具模块停止")
