try {
    $t = Get-ScheduledTask -TaskName DailyFinanceSummary -ErrorAction Stop
    Write-Host ("Name: " + $t.TaskName)
    Write-Host ("State: " + $t.State)
    foreach($tr in $t.Triggers) {
        Write-Host ("Trigger: " + $tr.TriggerType)
    }
} catch {
    Write-Host "任务不存在: $_"
}
