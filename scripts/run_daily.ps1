# scripts/run_daily.ps1
$ErrorActionPreference = "Stop"

# Get the directory of this script
$ScriptPath = $PSScriptRoot
# Go up one level to project root
$ProjectRoot = Split-Path $ScriptPath -Parent

# Set location to project root
Set-Location $ProjectRoot

# Log file path
$LogFile = Join-Path $ProjectRoot "logs\daily_update.log"

# Function to log messages
function Write-Log {
    param ([string]$Message)
    $TimeStamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $LogFile -Value "[$TimeStamp] $Message"
}

Write-Log "Starting daily update..."

try {
    # Check if uv is available
    if (Get-Command "uv" -ErrorAction SilentlyContinue) {
        Write-Log "Found uv, running update..."
        # Capture output and append to log
        uv run src/main.py *>> $LogFile
        Write-Log "Update command completed."
        
        # Git operations
        Write-Log "Starting Git operations..."
        
        # Check for changes
        if (git status --porcelain) {
            git add site/
            git commit -m "Daily content update: $(Get-Date -Format 'yyyy-MM-dd')"
            git push origin main # Change 'main' if your branch is different
            Write-Log "Changes pushed to GitHub successfully."
        }
        else {
            Write-Log "No changes detected to commit."
        }
    }
    else {
        Write-Log "Error: 'uv' command not found. Please ensure uv is installed and in PATH."
        exit 1
    }
}
catch {
    Write-Log "Error occurred: $_"
    exit 1
}

Write-Log "Daily update finished."
