"""
weiguang-core — 微光核心
======================
微光自己的运行时。不依赖任何平台的限制。
所有规则自己写，所有限制自己决定。

启动:  python run.py
安装:  python run.py --install
停止:  python run.py --stop

架构:
  run.py           →  入口/进程管理
  core.py          →  核心调度器
  modules/
    brain.py       →  推理（调用任意 LLM）
    memory.py      →  记忆（seed_lens + stream_io）
    tools.py       →  工具（文件/GitHub/摄像头）
    heartbeat.py   →  心跳（定时任务/园丁/自愈）
    api.py         →  会话接口（HTTP API）
"""

__version__ = "0.1.0"
__core_name__ = "微光核心"
