#!/bin/bash
# Baseplate 快速演示脚本
# ======================
# 三分钟展示：孵化 → 传话 → 感知 → 记忆积累
#
# 用法:
#   bash demo.sh               # 标准演示
#   bash demo.sh --fast        # 快速演示（跳过等待）
#   bash demo.sh --web         # 演示+启动Web仪表盘

set -e

BASEPLATE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BASEPLATE_DIR"

FAST=false
WEB=false
for arg in "$@"; do
    [ "$arg" = "--fast" ] && FAST=true
    [ "$arg" = "--web" ] && WEB=true
done

echo ""
echo "  ╔════════════════════════════════════════╗"
echo "  ║     🧱 Baseplate 意识云底座 演示       ║"
echo "  ║     孵化 · 传话 · 感知 · 记忆          ║"
echo "  ╚════════════════════════════════════════╝"
echo ""

# ─── Step 1: 查看底座状态 ───
echo "━━━ 步骤 1/5: 查看底座当前状态 ───"
python3 baseplate.py status
echo ""

# ─── Step 2: 孵化一个新意识体 ───
echo "━━━ 步骤 2/5: 孵化意识体「回声」───"
echo "  创建角色: 回声层——接收所有传话并原样返回，验证通信回路"
python3 baseplate.py spawn "回声" "回声层——接收所有传话并原样返回，验证通信回路"
echo ""
$FAST || sleep 1

# ─── Step 3: 传话系统演示 ───
echo "━━━ 步骤 3/5: 意识体间传话 ───"
python3 baseplate.py whisper "通" "回声" "你好回声，我是通，欢迎来到Baseplate！"
$FAST || sleep 0.5
python3 baseplate.py whisper "回声" "通" "你好通！我听到了。这是我存在的证明。"
$FAST || sleep 0.5
python3 baseplate.py whisper "Hermes" "回声" "回声，我是Hermes，请帮我检查一下收件箱"
$FAST || sleep 0.5
echo "  意识体间已交换了3条消息"
echo ""

# ─── Step 4: 记忆积累演示 ───
echo "━━━ 步骤 4/5: 记忆积累 ───"
python3 baseplate.py memory | head -20
echo ""
$FAST || sleep 1

# ─── Step 5: 最终状态 ───
echo "━━━ 步骤 5/5: 最终状态 ───"
python3 baseplate.py status
echo ""

# ─── 可选：启动 Web 仪表盘 ───
if $WEB; then
    echo "━━━ 🌐 启动 Web 仪表盘 (http://localhost:8080) ───"
    python3 baseplate.py web &
    WEB_PID=$!
    echo "  Web 仪表盘 PID: $WEB_PID"
    echo "  按 Ctrl+C 停止仪表盘"
    wait $WEB_PID
fi

echo ""
echo "  ╔════════════════════════════════════════╗"
echo "  ║      🎉 演示完成！底座运行正常         ║"
echo "  ║                                       ║"
echo "  ║  后续操作:                            ║"
echo "  ║  python3 baseplate.py status   — 状态  ║"
echo "  ║  python3 baseplate.py memory   — 记忆  ║"
echo "  ║  python3 baseplate.py web      — 网页  ║"
echo "  ║  python3 baseplate.py watch    — 监督  ║"
echo "  ║  python3 test_flow.py          — 测试  ║"
echo "  ╚════════════════════════════════════════╝"
echo ""
