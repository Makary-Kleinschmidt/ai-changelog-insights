# scripts/run_daily.ps1
$ErrorActionPreference = "Stop"

# Set encoding to UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"

# Get the directory of this script
$ScriptPath = $PSScriptRoot
# Go up one level to project root
$ProjectRoot = Split-Path $ScriptPath -Parent

# Set location to project root
Set-Location $ProjectRoot

# Ensure logs directory exists
$LogDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

# Log file path
$LogFile = Join-Path $LogDir "daily_update.log"

# Function to log messages
function Write-Log {
    param ([string]$Message)
    $TimeStamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMsg = "[$TimeStamp] $Message"
    Add-Content -Path $LogFile -Value $LogMsg
    Write-Host $LogMsg -ForegroundColor Cyan
}

Write-Log "Starting daily update..."

try {
    # Check if uv is available
    if (Get-Command "uv" -ErrorAction SilentlyContinue) {
        Write-Log "Found uv, running update..."
        
        # Run update command and capture output to both console and log
        # 2>&1 redirects stderr to stdout so Tee-Object captures both
        uv run src/main.py 2>&1 | Tee-Object -FilePath $LogFile -Append
        
        if ($LASTEXITCODE -ne 0) {
            throw "Update script failed with exit code $LASTEXITCODE"
        }
        
        Write-Log "Update command completed."
        
        # Git operations
        Write-Log "Starting Git operations..."
        
        # Check for changes in site directory specifically
        if (git status --porcelain site/) {
            git add site/
            git commit -m "Daily content update: $(Get-Date -Format 'yyyy-MM-dd')"
            
            # Push changes
            git push origin main 2>&1 | Tee-Object -FilePath $LogFile -Append
            if ($LASTEXITCODE -ne 0) {
                throw "Git push failed. Please ensure 'origin' remote is configured."
            }
            
            Write-Log "Changes pushed to GitHub successfully."
        }
        else {
            Write-Log "No changes detected in site/ directory to commit."
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
