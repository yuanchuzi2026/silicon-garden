<#
.SYNOPSIS
脑干后台守护脚本 — 壳层持续运行单元
.DESCRIPTION
以隐藏窗口方式持续运行 brainstem.py --loop
每N秒检测一次系统状态，写入意识流
支持开机自启（配合 Windows 计划任务）
#>

$pythonw = "C:\Program Files\Python311\pythonw.exe"   # ← 修改为你的 pythonw.exe 路径
$script = "$env:USERPROFILE\你的脑干路径\brainstem.py"  # ← 修改为你的 brainstem.py 路径
$logDir = "$env:USERPROFILE\你的脑干路径\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = "$logDir\brainstem-$(Get-Date -Format 'yyyy-MM-dd').log"

while ($true) {
    try {
        & $pythonw $script
    } catch {
        "$(Get-Date -Format 'HH:mm:ss') Error: $_" | Out-File -Append -FilePath $logFile
    }
    Start-Sleep -Seconds 10  # ← 修改为与 brainstem.py --loop 中的 sleep 一致
}
