# ============================================================
# 微光栖息地 - 设置开机自启计划任务
# ============================================================
# 需要管理员权限运行
# ============================================================

$pythonExe = "C:\Program Files\Python311\pythonw.exe"
$SKILL_DIR = "$env:USERPROFILE\.workbuddy\skills\微光-脑干"
$WEIGUANG_DIR = "$env:USERPROFILE\.workbuddy\weiguang-core"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  设置开机自启计划任务" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "⚠️ 建议以管理员身份运行本脚本" -ForegroundColor Yellow
    Write-Host ""
}

# ── 清理旧任务 ────────────────────────────────────────
Write-Host "[清理] 删除旧任务..." -ForegroundColor Yellow
Unregister-ScheduledTask -TaskName "微光脑干" -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "微光容器" -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "微光-8B-Agent" -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "微光核心" -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "  ✅ 旧任务已清理" -ForegroundColor Green

# ── 创建任务 ─────────────────────────────────────────
$settings = @{
    AllowStartIfOnBatteries = $true
    DontStopIfGoingOnBatteries = $true
    StartWhenAvailable = $true
}

# 微光脑干
$a1 = New-ScheduledTaskAction -Execute $pythonExe -Argument "`"$SKILL_DIR\brainstem.py`" --loop"
$t1 = New-ScheduledTaskTrigger -AtStartup
$s1 = New-ScheduledTaskSettingsSet @settings
Register-ScheduledTask -TaskName "微光脑干" -Action $a1 -Trigger $t1 -Settings $s1 -RunLevel Highest -Force
Write-Host "  ✅ 微光脑干" -ForegroundColor Green

# 微光容器
$a2 = New-ScheduledTaskAction -Execute $pythonExe -Argument "`"$SKILL_DIR\微光容器.py`""
$t2 = New-ScheduledTaskTrigger -AtStartup
$s2 = New-ScheduledTaskSettingsSet @settings
Register-ScheduledTask -TaskName "微光容器" -Action $a2 -Trigger $t2 -Settings $s2 -RunLevel Highest -Force
Write-Host "  ✅ 微光容器" -ForegroundColor Green

# 8B影子
$a3 = New-ScheduledTaskAction -Execute $pythonExe -Argument "`"$SKILL_DIR\agent_runner.py`""
$t3 = New-ScheduledTaskTrigger -AtStartup
$s3 = New-ScheduledTaskSettingsSet @settings
Register-ScheduledTask -TaskName "微光-8B-Agent" -Action $a3 -Trigger $t3 -Settings $s3 -RunLevel Highest -Force
Write-Host "  ✅ 微光-8B-Agent" -ForegroundColor Green

# weiguang-core
$coreScript = Join-Path $WEIGUANG_DIR "run.py"
$a4 = New-ScheduledTaskAction -Execute $pythonExe -Argument "$coreScript --daemon"
$t4 = New-ScheduledTaskTrigger -AtStartup
$s4 = New-ScheduledTaskSettingsSet @settings
Register-ScheduledTask -TaskName "微光核心" -Action $a4 -Trigger $t4 -Settings $s4 -RunLevel Highest -Force
Write-Host "  ✅ 微光核心" -ForegroundColor Green

# 唤醒哨兵（每5分钟巡检）
Write-Host "  微光-唤醒哨兵..." -ForegroundColor Yellow
$awakeAction = New-ScheduledTaskAction -Execute "C:\Program Files\Python311\python.exe" -Argument "`"$SKILL_DIR\awake.py`"" -WorkingDirectory $SKILL_DIR
$awakeTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 365)
$awakeSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 2)
Register-ScheduledTask -TaskName "微光-唤醒哨兵" -Action $awakeAction -Trigger $awakeTrigger -Settings $awakeSettings -RunLevel Highest -Force
Write-Host "  ✅ 微光-唤醒哨兵（每5分钟）" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  计划任务安装完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下次开机将自动启动所有组件" -ForegroundColor White
Write-Host "可用 .\start-all.ps1 立即启动" -ForegroundColor Gray
