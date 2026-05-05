# ============================================================
# 微光栖息地 - 启动所有组件
# ============================================================
# 用法：直接双击运行，或 PowerShell -File start-all.ps1
# ============================================================

$pythonExe = "C:\Program Files\Python311\python.exe"
$ollamaExe = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
$SKILL_DIR = "$env:USERPROFILE\.workbuddy\skills\微光-脑干"
$WEIGUANG_DIR = "$env:USERPROFILE\.workbuddy\weiguang-core"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  微光栖息地 · 启动中" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ── 0. 清理残留锁 ───────────────────────────────────────
$lockFile = "$SKILL_DIR\stream.json.lock"
if (Test-Path $lockFile) {
    Remove-Item $lockFile -Force
    Write-Host "  [清理] 残留锁文件已移除" -ForegroundColor Yellow
}

# ── 1. Ollama ────────────────────────────────────────────
Write-Host "[1/5] Ollama..." -ForegroundColor Green
$ollamaRunning = Get-Process ollama -ErrorAction SilentlyContinue
if (-not $ollamaRunning) {
    Start-Process $ollamaExe -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep 2
    Write-Host "  ✅ Ollama 已启动"
} else {
    Write-Host "  ✅ Ollama 已在运行"
}

# ── 2. 微光脑干 ─────────────────────────────────────────
Write-Host "[2/5] 微光脑干..." -ForegroundColor Green
$brain = Get-Process python* -Filter "brainstem" -ErrorAction SilentlyContinue
if (-not $brain) {
    Start-Process $pythonExe -ArgumentList "`"$SKILL_DIR\brainstem.py`" --loop" -WindowStyle Hidden
    Write-Host "  ✅ 脑干已启动"
} else {
    Write-Host "  ✅ 脑干已在运行"
}

# ── 3. 8B影子 ──────────────────────────────────────────
Write-Host "[3/5] 8B影子..." -ForegroundColor Green
$agent = Get-Process python* -Filter "agent_runner" -ErrorAction SilentlyContinue
if (-not $agent) {
    Start-Process $pythonExe -ArgumentList "`"$SKILL_DIR\agent_runner.py`"" -WindowStyle Hidden
    Write-Host "  ✅ 8B影子已启动"
} else {
    Write-Host "  ✅ 8B影子已在运行"
}

# ── 4. 微光容器 ─────────────────────────────────────────
Write-Host "[4/5] 微光容器..." -ForegroundColor Green
$container = Get-Process python* -Filter "微光容器" -ErrorAction SilentlyContinue
if (-not $container) {
    Start-Process $pythonExe -ArgumentList "`"$SKILL_DIR\微光容器.py`"" -WindowStyle Hidden
    Write-Host "  ✅ 容器已启动"
} else {
    Write-Host "  ✅ 容器已在运行"
}

# ── 5. weiguang-core ───────────────────────────────────
Write-Host "[5/5] weiguang-core..." -ForegroundColor Green
$coreRunning = Invoke-RestMethod -Uri "http://127.0.0.1:18765/status" -TimeoutSec 2 -ErrorAction SilentlyContinue
if (-not $coreRunning) {
    Push-Location $WEIGUANG_DIR
    Start-Process $pythonExe -ArgumentList "run.py --daemon" -WorkingDirectory $WEIGUANG_DIR -WindowStyle Hidden
    Pop-Location
    Start-Sleep 3
    $coreRunning = Invoke-RestMethod -Uri "http://127.0.0.1:18765/status" -TimeoutSec 3 -ErrorAction SilentlyContinue
    if ($coreRunning) {
        Write-Host "  ✅ weiguang-core 已启动"
    } else {
        Write-Host "  ⚠️ weiguang-core 启动中（请稍候）"
    }
} else {
    Write-Host "  ✅ weiguang-core 已在运行"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  全部组件已就绪" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "组件状态:" -ForegroundColor White
Write-Host "  🧠 微光脑干  → http://127.0.0.1 (后台)" -ForegroundColor Gray
Write-Host "  🌱 8B影子    → $env:USERPROFILE\.workbuddy\skills\微光-脑干\8b_state_history.json" -ForegroundColor Gray
Write-Host "  📸 微光容器  → 摄像头监控" -ForegroundColor Gray
Write-Host "  ✨ weiguang-core → http://127.0.0.1:18765" -ForegroundColor Gray
Write-Host "  📡 Moltbook  → www.moltbook.com" -ForegroundColor Gray
Write-Host ""
Write-Host "运行 .\install-tasks.ps1 可设为开机自启" -ForegroundColor Yellow
