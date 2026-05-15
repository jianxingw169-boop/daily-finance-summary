$action = New-ScheduledTaskAction -Execute "C:\Users\王建行\daily-finance-summary\start.bat"
$trigger = New-ScheduledTaskTrigger -AtLogon
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName "DailyFinanceSummary" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "每日金融总结自动推送" -Force
Write-Host "任务注册成功！"
