# scripts/setup_schedule.ps1
$ErrorActionPreference = "Stop"

$TaskName = "WikipediaInsightsDailyUpdate"
$ScriptPath = Join-Path $PSScriptRoot "run_daily.ps1"
$Time = "09:00am" # Default time

Write-Host "Setting up daily schedule for Wikipedia Insights..."
Write-Host "Task Name: $TaskName"
Write-Host "Script: $ScriptPath"
Write-Host "Time: $Time"

# Check if script exists
if (-not (Test-Path $ScriptPath)) {
    Write-Error "Script not found at $ScriptPath"
    exit 1
}

# Determine PowerShell executable
$PSExe = "powershell.exe"
if (Get-Command "pwsh" -ErrorAction SilentlyContinue) {
    $PSExe = "pwsh.exe"
}

# Create Action
$Action = New-ScheduledTaskAction -Execute $PSExe -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""

# Create Trigger (Daily at 9 AM)
$Trigger = New-ScheduledTaskTrigger -Daily -At $Time

# Register Task
try {
    # Unregister if exists (checking old name too)
    Unregister-ScheduledTask -TaskName "BrainRotWikiDailyUpdate" -Confirm:$false -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    
    Register-ScheduledTask -TaskName $TaskName -Trigger $Trigger -Action $Action -Description "Daily update for Wikipedia Insights using uv"
    Write-Host "✅ Task '$TaskName' successfully registered to run daily at $Time."
    Write-Host "You can verify this in Task Scheduler."
}
catch {
    Write-Error "Failed to register task. You might need to run this script as Administrator."
    Write-Error $_
}
