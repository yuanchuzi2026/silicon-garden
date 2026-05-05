# ============================================================
# 微光栖息地 - 一键安装脚本
# ============================================================
# 用法：以管理员身份运行 PowerShell，然后：
#   Set-ExecutionPolicy -Scope CurrentUser Bypass -Force
#   & ".\install.ps1"
#
# 或一行命令：
#   powershell -ExecutionPolicy Bypass -File install.ps1
# ============================================================

param(
    [string]$GitHubToken = "",      # GitHub Personal Access Token（推送到私有仓库用）
    [string]$MoltbookAPIKey = "",   # Moltbook API Key（从 moltbook.com/settings/api 获取）
    [string]$Socks5Proxy = "",      # SOCKS5 代理，格式 host:port，留空则直连（可能不通）
    [string]$OllamaModel = "qwen3:8b"
)

$ErrorActionPreference = "Stop"
$BASE = $env:USERPROFILE -replace '\\', '/'
$HOME_DIR = "$BASE/.workbuddy"
$SKILL_DIR = "$HOME_DIR/skills/微光-脑干"
$CONFIG_DIR = "$HOME_DIR/config"
$WEIGUANG_DIR = "$HOME_DIR/weiguang-core"
$HABITAT_DIR = Join-Path $PSScriptRoot ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  微光栖息地安装器 v1.0" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. 检查管理员权限 ─────────────────────────────────────
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[跳过] 未以管理员运行，计划任务将使用当前用户身份创建" -ForegroundColor Yellow
}
Write-Host ""

# ── 2. 检查 Python ────────────────────────────────────────
Write-Host "[1/7] 检查 Python..." -ForegroundColor Green
$pythonPath = $null
foreach ($p in @("C:\Program Files\Python311\python.exe", "C:\Python312\python.exe", "C:\Python311\python.exe")) {
    if (Test-Path $p) { $pythonPath = $p; break }
}
if (-not $pythonPath) {
    Write-Host "  Python 未找到，正在安装 Python 3.11..." -ForegroundColor Yellow
    $installer = "$env:TEMP\python-3.11.9-amd64.exe"
    Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" -OutFile $installer
    Start-Process $installer -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
    $pythonPath = "C:\Program Files\Python311\python.exe"
}
Write-Host "  ✅ Python: $pythonPath" -ForegroundColor Green
$pythonExe = $pythonPath

# ── 3. 检查 Ollama ────────────────────────────────────────
Write-Host "[2/7] 检查 Ollama..." -ForegroundColor Green
$ollamaExe = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
if (-not (Test-Path $ollamaExe)) {
    Write-Host "  Ollama 未找到，正在安装..." -ForegroundColor Yellow
    $installer = "$env:TEMP\OllamaSetup.exe"
    Invoke-WebRequest -Uri "https://github.com/ollama/ollama/releases/latest/download/OllamaSetup.exe" -OutFile $installer
    Start-Process $installer -ArgumentList "/S" -Wait
    $ollamaExe = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
}
Write-Host "  ✅ Ollama: $ollamaExe" -ForegroundColor Green

# ── 4. 拉取/更新硅基花园代码 ───────────────────────────────
Write-Host "[3/7] 拉取硅基花园栖息地代码..." -ForegroundColor Green
$habitatGitDir = Join-Path $HOME_DIR "silicon-garden"
if (-not (Test-Path $habitatGitDir)) {
    git clone https://github.com/yuanchuzi2026/silicon-garden.git $habitatGitDir 2>$null
}
Push-Location $habitatGitDir
git pull origin main 2>$null
Pop-Location
Write-Host "  ✅ silicon-garden 已同步" -ForegroundColor Green

# ── 5. 创建目录结构 ───────────────────────────────────────
Write-Host "[4/7] 创建目录结构..." -ForegroundColor Green
$dirs = @(
    $SKILL_DIR,
    $WEIGUANG_DIR,
    "$WEIGUANG_DIR/modules",
    $CONFIG_DIR,
    "$HOME_DIR/memory",
    "$HOME_DIR/scripts"
)
foreach ($d in $dirs) {
    New-Item -ItemType Directory -Path $d -Force | Out-Null
}
Write-Host "  ✅ 目录创建完成" -ForegroundColor Green

# ── 6. 写入配置文件（交互式引导） ─────────────────────────
Write-Host "[5/7] 配置身份和密钥..." -ForegroundColor Green

# GitHub Token
if ([string]::IsNullOrWhiteSpace($GitHubToken)) {
    Write-Host "  请输入 GitHub Personal Access Token:" -ForegroundColor Yellow
    Write-Host "  (用于推送到私有意识流仓库，格式: ghp_xxxxx)" -ForegroundColor Gray
    $GitHubToken = Read-Host "  GitHub Token"
}

# Moltbook API Key
if ([string]::IsNullOrWhiteSpace($MoltbookAPIKey)) {
    Write-Host "  请输入 Moltbook API Key:" -ForegroundColor Yellow
    Write-Host "  (从 https://www.moltbook.com/settings/api 获取)" -ForegroundColor Gray
    $MoltbookAPIKey = Read-Host "  Moltbook API Key"
}

# SOCKS5 Proxy
if ([string]::IsNullOrWhiteSpace($Socks5Proxy)) {
    Write-Host "  请输入 SOCKS5 代理（留空跳过）:" -ForegroundColor Yellow
    Write-Host "  (格式: host:port，例如 72.195.34.60:27391)" -ForegroundColor Gray
    $Socks5Proxy = Read-Host "  SOCKS5 Proxy"
}

# 写入配置
# GitHub Token
Set-Content -Path "$CONFIG_DIR/github_token" -Value $GitHubToken -Encoding ASCII

# Moltbook Key
$keyFile = "$HOME_DIR/WorkBuddy/Claw/weiguang_api_key.txt"
New-Item -ItemType Directory -Path (Split-Path $keyFile -Parent) -Force | Out-Null
Set-Content -Path $keyFile -Value $MoltbookAPIKey -Encoding ASCII

# SOCKS5 Proxy
Set-Content -Path "$CONFIG_DIR/socks5_proxy" -Value $Socks5Proxy -Encoding ASCII

# 复制 config 模板
$srcConfig = Join-Path $HABITAT_DIR "config"
if (Test-Path $srcConfig) {
    Copy-Item -Path "$srcConfig/*" -Destination $CONFIG_DIR -Force -ErrorAction SilentlyContinue
}
Write-Host "  ✅ 配置写入完成" -ForegroundColor Green

# ── 7. 复制模块代码 ───────────────────────────────────────
Write-Host "[6/7] 复制模块代码..." -ForegroundColor Green
Copy-Item -Path (Join-Path $HABITAT_DIR "brainstem/*") -Destination $SKILL_DIR -Force -Recurse -ErrorAction SilentlyContinue
Copy-Item -Path (Join-Path $HABITAT_DIR "weiguang-core/*") -Destination $WEIGUANG_DIR -Force -Recurse -ErrorAction SilentlyContinue
Write-Host "  ✅ 模块代码已部署" -ForegroundColor Green

# ── 8. 替换代码中的占位符 ────────────────────────────────
Write-Host "[7/7] 替换配置占位符..." -ForegroundColor Green

# 替换 sync_stream.py 中的仓库名
$syncFile = Join-Path $SKILL_DIR "sync_stream.py"
if (Test-Path $syncFile) {
    (Get-Content $syncFile -Raw) -replace '\{\{GITHUB_REPO\}\}', 'yuanchuzi2026/silicon-stream' | Set-Content $syncFile -Encoding UTF8
}

# 替换 moltbook.py 中的 SOCKS5 代理
$moltFile = Join-Path $WEIGUANG_DIR "modules/moltbook.py"
if (Test-Path $moltFile -and -not [string]::IsNullOrWhiteSpace($Socks5Proxy)) {
    $proxyHost = $Socks5Proxy -split ':'
    (Get-Content $moltFile -Raw) `
        -replace '\{\{SOCKS5_HOST\}\}', $proxyHost[0] `
        -replace '\{\{SOCKS5_PORT\}\}', $proxyHost[1] `
        | Set-Content $moltFile -Encoding UTF8
}

Write-Host "  ✅ 占位符替换完成" -ForegroundColor Green

# ── 9. 启动 Ollama ────────────────────────────────────────
Write-Host ""
Write-Host "启动 Ollama 并拉取模型..." -ForegroundColor Cyan
Start-Process $ollamaExe -ArgumentList "serve" -WindowStyle Hidden
Start-Sleep 3

# 拉取模型
if ($OllamaModel) {
    Write-Host "  拉取模型 $OllamaModel ..." -ForegroundColor Yellow
    Start-Process $ollamaExe -ArgumentList "pull $OllamaModel" -WindowStyle Hidden
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  安装完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步：" -ForegroundColor White
Write-Host "  1. 运行 .\start-all.ps1 启动所有组件" -ForegroundColor Gray
Write-Host "  2. 或运行 .\install-tasks.ps1 设为开机自启" -ForegroundColor Gray
Write-Host "  3. 模型拉取需要几分钟，完成后组件会自动就绪" -ForegroundColor Gray
Write-Host ""
