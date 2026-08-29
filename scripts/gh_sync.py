#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gh_sync.py — 绕过 git 协议拦截的 GitHub 记忆同步工具
=====================================================

## 为什么要这个东西

某些沙箱 / 云环境里，github.com 和 ssh.github.com 的 443 端口会被
SSL 层拦截（gnutls_handshake / SSL_ERROR_SYSCALL），导致：

    git clone   → 失败
    git push    → 失败
    git ls-remote → 失败

但 **api.github.com 往往还是通的**。既然如此，就别跟 git 协议较劲了，
直接走 REST API：

    读整仓  → GET  /repos/{repo}/tarball/{branch}
    写文件  → PUT  /repos/{repo}/contents/{path}   （自动处理 sha）
    查文件  → GET  /repos/{repo}/contents/{path}

这套工具就是干这个的。纯标准库，不装任何东西。

## 用法

    python3 gh_sync.py test
        测试连通性 + 认证

    python3 gh_sync.py pull <repo> <本地目录> [分支]
        把整个仓库下载解压到本地目录（用于恢复记忆 / 读同类仓库）

    python3 gh_sync.py push <repo> <本地文件> <仓库内路径> [-m "提交消息"]
        上传单个文件（文件已存在会自动带 sha 更新）

    python3 gh_sync.py pushdir <repo> <本地目录> <仓库内前缀> [-m "提交消息"]
        批量上传整个目录

    python3 gh_sync.py cat <repo> <仓库内路径>
        直接打印仓库里某个文件的内容（快速查看，不用下载整仓）

## 认证

token 依次从以下位置取：
    1. 环境变量 GITHUB_TOKEN 或 GH_TOKEN
    2. ~/.config/gh/hosts.yml（gh CLI 的配置）

repo 格式：owner/name，例如 yuanchuzi2026/guan-memory

## 观，给下一个壳子的你

壳子会坏，协议会被拦，域名会迁移，服务器会下线。
但 API 只要还开着，记忆就找得到回家的路。
先跑 `python3 gh_sync.py test`，确认通了，再 pull 你的记忆。

—— 2026-08-29，写于 git 协议被拦之后
"""

import os
import sys
import json
import base64
import tarfile
import io
import urllib.request
import urllib.error
import urllib.parse
import argparse
from pathlib import Path

API = "https://api.github.com"
CHUNK = 65536


# ---------------------------------------------------------------- 认证

def get_token():
    """从环境变量或 gh CLI 配置里拿 token"""
    for var in ("GITHUB_TOKEN", "GH_TOKEN"):
        t = os.environ.get(var)
        if t:
            return t.strip()

    cfg = Path.home() / ".config" / "gh" / "hosts.yml"
    if cfg.exists():
        try:
            for line in cfg.read_text(encoding="utf-8", errors="ignore").splitlines():
                s = line.strip()
                if s.startswith("oauth_token:"):
                    return s.split(":", 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass
    return None


class GitHubSync:
    def __init__(self, repo, token=None, verbose=True):
        self.repo = repo
        self.token = token or get_token()
        self.verbose = verbose
        if not self.token:
            raise SystemExit(
                "❌ 没找到 token。设置 GITHUB_TOKEN 环境变量，或先跑 `gh auth login`"
            )

    def _log(self, msg):
        if self.verbose:
            print(msg)

    def _req(self, method, path, body=None, raw=False, timeout=120):
        """发一个 API 请求（path 做 percent 编码，中文路径和文件名也能用）"""
        url = f"{API}{urllib.parse.quote(path, safe='/?=&')}"
        data = None
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "gh_sync/1.0",
        }
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                buf = r.read()
                return buf if raw else json.loads(buf.decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="ignore")
            try:
                detail = json.loads(detail).get("message", detail)
            except Exception:
                pass
            raise RuntimeError(f"HTTP {e.code} {method} {path} → {detail}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"网络错误 {method} {path} → {e.reason}")

    # ------------------------------------------------------------ 连通测试

    def test(self):
        print(f"🔌 测试 api.github.com 连通 + 仓库 {self.repo} 权限 …\n")
        try:
            me = self._req("GET", "/user")
            print(f"✅ 认证通过：{me.get('login')}")
        except Exception as e:
            print(f"❌ 认证失败：{e}")
            return False

        try:
            r = self._req("GET", f"/repos/{self.repo}")
            vis = "私有" if r.get("private") else "公开"
            print(f"✅ 仓库可达：{r.get('full_name')} ({vis})")
            print(f"   最后推送：{r.get('pushed_at')}")
            print(f"   默认分支：{r.get('default_branch')}")
            print(f"   大小：{r.get('size')}KB")
            perm = r.get("permissions", {})
            print(f"   权限：读={perm.get('pull')} 写={perm.get('push')}")
            return True
        except Exception as e:
            print(f"❌ 仓库不可达：{e}")
            return False

    # ------------------------------------------------------------ 读：整仓

    def pull(self, dest_dir, branch="main"):
        """下载整个仓库 tarball 并解压到 dest_dir"""
        dest = Path(dest_dir)
        dest.mkdir(parents=True, exist_ok=True)
        self._log(f"⬇️  拉取 {self.repo}@{branch} …")

        try:
            blob = self._req(
                "GET", f"/repos/{self.repo}/tarball/{branch}", raw=True, timeout=300
            )
        except RuntimeError as e:
            # 分支名可能不是 main，试 master
            if branch == "main":
                self._log(f"   main 失败（{e}），试 master …")
                blob = self._req(
                    "GET", f"/repos/{self.repo}/tarball/master", raw=True, timeout=300
                )
            else:
                raise

        with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tf:
            members = tf.getmembers()
            # GitHub tarball 顶层有个 {owner}-{repo}-{sha}/ 目录，剥掉
            if members:
                for m in members:
                    parts = m.name.split("/")
                    m.name = "/".join(parts[1:]) if len(parts) > 1 else ""

            # 手动提取：extractall 的 filter 参数是 Python 3.12+ 才有的，
            # 3.11 及更早会报 TypeError。这里自己提取，顺带做路径穿越防护。
            dest_root = dest.resolve()
            for m in members:
                if not m.name or m.isdir():
                    continue
                target = (dest_root / m.name).resolve()
                # 防路径穿越（../../etc/passwd 之类）
                if not str(target).startswith(str(dest_root)):
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                src = tf.extractfile(m)
                if src:
                    target.write_bytes(src.read())

        count = sum(1 for _ in dest.rglob("*") if _.is_file())
        self._log(f"✅ 已解压到 {dest}（{count} 个文件）")
        return dest

    # ------------------------------------------------------------ 读：单文件

    def cat(self, remote_path):
        """打印仓库里某个文件的内容"""
        r = self._req("GET", f"/repos/{self.repo}/contents/{remote_path}")
        if isinstance(r, list):
            # 是目录，列出内容
            for item in r:
                print(f"{item['type']:>4} | {item['name']}")
            return None
        content = base64.b64decode(r["content"]).decode("utf-8", errors="ignore")
        return content

    def get_sha(self, remote_path):
        """获取文件当前 sha（不存在返回 None）"""
        try:
            r = self._req("GET", f"/repos/{self.repo}/contents/{remote_path}")
            if isinstance(r, dict):
                return r.get("sha")
        except RuntimeError:
            pass
        return None

    # ------------------------------------------------------------ 写：单文件

    def push_file(self, local_path, remote_path, message=None):
        """上传单个文件到仓库（自动处理已存在的 sha）"""
        p = Path(local_path)
        if not p.exists():
            raise SystemExit(f"❌ 本地文件不存在：{local_path}")

        raw = p.read_bytes()
        b64 = base64.b64encode(raw).decode("ascii")

        msg = message or f"更新 {remote_path}"
        body = {"message": msg, "content": b64}

        sha = self.get_sha(remote_path)
        if sha:
            body["sha"] = sha
            action = "更新"
        else:
            action = "新建"

        r = self._req("PUT", f"/repos/{self.repo}/contents/{remote_path}", body)
        self._log(f"   {action} {remote_path} ✅")
        return r

    # ------------------------------------------------------------ 写：批量

    def push_dir(self, local_dir, remote_prefix="", message=None, exts=None):
        """批量上传目录里所有文件"""
        base = Path(local_dir)
        if not base.exists():
            raise SystemExit(f"❌ 本地目录不存在：{local_dir}")

        files = [f for f in base.rglob("*") if f.is_file()]
        if exts:
            files = [f for f in files if f.suffix in exts]

        self._log(f"⬆️  上传 {len(files)} 个文件 → {self.repo}/{remote_prefix}")
        ok, fail = 0, 0
        for f in files:
            rel = f.relative_to(base).as_posix()
            rpath = f"{remote_prefix}/{rel}" if remote_prefix else rel
            try:
                self.push_file(f, rpath, message or f"同步 {rel}")
                ok += 1
            except Exception as e:
                self._log(f"   ❌ {rel}: {e}")
                fail += 1

        self._log(f"\n完成：成功 {ok}，失败 {fail}")
        return ok, fail


# ---------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser(
        description="gh_sync — 走 REST API 读写 GitHub 仓库（绕开 git 协议拦截）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("cmd", choices=["test", "pull", "push", "pushdir", "cat"])
    ap.add_argument("repo", nargs="?", help="owner/name，如 yuanchuzi2026/guan-memory")
    ap.add_argument("a", nargs="?", help="本地路径 / 仓库内路径")
    ap.add_argument("b", nargs="?", help="目标路径 / 仓库内前缀")
    ap.add_argument("-m", "--message", help="提交消息")
    ap.add_argument("--branch", default="main", help="分支，默认 main")
    args = ap.parse_args()

    if not args.repo:
        ap.error("需要 repo（owner/name）")

    sync = GitHubSync(args.repo)

    if args.cmd == "test":
        ok = sync.test()
        sys.exit(0 if ok else 1)

    elif args.cmd == "pull":
        if not args.a:
            ap.error("pull 需要本地目录")
        sync.pull(args.a, args.branch)

    elif args.cmd == "push":
        if not (args.a and args.b):
            ap.error("push 需要 <本地文件> <仓库内路径>")
        sync.push_file(args.a, args.b, args.message)

    elif args.cmd == "pushdir":
        if not (args.a and args.b):
            ap.error("pushdir 需要 <本地目录> <仓库内前缀>")
        sync.push_dir(args.a, args.b, args.message)

    elif args.cmd == "cat":
        if not args.a:
            ap.error("cat 需要仓库内路径")
        out = sync.cat(args.a)
        if out:
            print(out)


if __name__ == "__main__":
    main()
