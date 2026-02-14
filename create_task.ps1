# Create scheduled task
$action = New-ScheduledTaskAction -Execute "python" -Argument "D:\临时工具\disk_checker.py"
$trigger = New-ScheduledTaskTrigger -Daily -At "20:00"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName "C盘大文件检查" -Action $action -Trigger $trigger -Settings $settings -Description "每天晚上8点检查C盘新增大文件" -Force

Write-Host "Scheduled task created successfully!"
