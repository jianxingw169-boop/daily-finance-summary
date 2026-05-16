$action = New-ScheduledTaskAction -Execute "C:\Users\王建行\daily-finance-summary\start.bat"
$trigger1 = New-ScheduledTaskTrigger -AtLogon
$trigger2 = New-ScheduledTaskTrigger -Daily -At "10:00"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName "DailyFinanceSummary" -Action $action -Trigger @($trigger1, $trigger2) -Settings $settings -Principal $principal -Description "每日金融总结自动推送（登录触发 + 每天10:00定时）" -Force
Write-Host "任务注册成功！新增每天10:00定时触发，错过时间会自动补跑。"
