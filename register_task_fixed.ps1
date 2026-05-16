# 自动提权到管理员
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "请求管理员权限..." -ForegroundColor Yellow
    Start-Process PowerShell -Verb RunAs "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

$taskName = "DailyFinanceSummary"
$scriptDir = Split-Path -Parent $PSCommandPath
$actionPath = Join-Path $scriptDir "start.bat"

# 删除旧任务（如果存在）
Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false -ErrorAction SilentlyContinue

# 创建两个触发器
$trigger1 = New-ScheduledTaskTrigger -AtLogon
$trigger2 = New-ScheduledTaskTrigger -Daily -At "10:00"

# 创建操作
$action = New-ScheduledTaskAction -Execute $actionPath

# 设置
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew

# 主体
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

# 注册任务
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger @($trigger1, $trigger2) -Settings $settings -Principal $principal -Description "每日金融总结自动推送（登录触发 + 每天10:00定时）" -Force

Write-Host ""
Write-Host "✅ 任务注册成功！" -ForegroundColor Green
Write-Host "  触发器1: 用户登录时启动" -ForegroundColor Cyan
Write-Host "  触发器2: 每天 10:00 定时触发" -ForegroundColor Cyan
Write-Host ""
Write-Host "过时间会补跑：如果开机时已过10点，脚本立即执行一次" -ForegroundColor Yellow
pause
