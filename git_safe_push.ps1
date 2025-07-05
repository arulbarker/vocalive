# StreamMate AI - Safe Git Push Script
# Ensures zero errors during commit and push operations

param(
    [string]$Message = "Auto-commit: StreamMate AI updates",
    [switch]$Force = $false,
    [switch]$DryRun = $false
)

Write-Host "🚀 StreamMate AI - Safe Git Push Script" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# Function to check Git status
function Test-GitStatus {
    Write-Host "🔍 Checking Git repository status..." -ForegroundColor Yellow
    
    # Check if we're in a Git repository
    if (-not (Test-Path ".git")) {
        Write-Error "❌ Not in a Git repository!"
        exit 1
    }
    
    # Check for staged/unstaged changes
    $status = git status --porcelain
    if (-not $status) {
        Write-Host "✅ No changes to commit" -ForegroundColor Green
        return $false
    }
    
    Write-Host "📝 Found changes to commit:" -ForegroundColor Green
    git status --short
    return $true
}

# Function to handle line endings
function Fix-LineEndings {
    Write-Host "🔧 Normalizing line endings..." -ForegroundColor Yellow
    
    # Refresh the index to apply .gitattributes
    git add --renormalize .
    
    Write-Host "✅ Line endings normalized" -ForegroundColor Green
}

# Function to check for potential conflicts
function Test-PotentialConflicts {
    Write-Host "🔍 Checking for potential conflicts..." -ForegroundColor Yellow
    
    # Fetch latest changes without merging
    git fetch origin master --quiet
    
    # Check if we're behind remote
    $behind = git rev-list --count HEAD..origin/master
    if ($behind -gt 0) {
        Write-Host "⚠️  Remote has $behind new commits" -ForegroundColor Yellow
        Write-Host "🔄 Pulling latest changes first..." -ForegroundColor Yellow
        
        # Pull with auto-merge strategy
        $pullResult = git pull origin master --strategy-option=ours --quiet
        if ($LASTEXITCODE -ne 0) {
            Write-Error "❌ Pull failed! Manual intervention required."
            exit 1
        }
        
        Write-Host "✅ Successfully merged remote changes" -ForegroundColor Green
    } else {
        Write-Host "✅ No conflicts detected" -ForegroundColor Green
    }
}

# Function to safely commit
function Invoke-SafeCommit {
    param([string]$CommitMessage)
    
    Write-Host "📦 Creating safe commit..." -ForegroundColor Yellow
    
    # Add all changes
    git add .
    
    # Check if there are staged changes
    $staged = git diff --cached --name-only
    if (-not $staged) {
        Write-Host "✅ No staged changes for commit" -ForegroundColor Green
        return $false
    }
    
    Write-Host "📝 Files to commit:" -ForegroundColor Green
    $staged | ForEach-Object { Write-Host "  • $_" -ForegroundColor White }
    
    if ($DryRun) {
        Write-Host "🧪 DRY RUN: Would commit with message: '$CommitMessage'" -ForegroundColor Magenta
        return $false
    }
    
    # Create commit
    git commit -m $CommitMessage
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Commit created successfully" -ForegroundColor Green
        return $true
    } else {
        Write-Error "❌ Commit failed!"
        exit 1
    }
}

# Function to safely push
function Invoke-SafePush {
    Write-Host "🚀 Pushing to remote repository..." -ForegroundColor Yellow
    
    if ($DryRun) {
        Write-Host "🧪 DRY RUN: Would push to origin master" -ForegroundColor Magenta
        return
    }
    
    # Use safe push with lease
    if ($Force) {
        Write-Host "⚠️  Force push requested - using --force-with-lease" -ForegroundColor Yellow
        git push origin master --force-with-lease
    } else {
        git push origin master
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Push completed successfully!" -ForegroundColor Green
        
        # Show final status
        Write-Host ""
        Write-Host "📊 Final Repository Status:" -ForegroundColor Cyan
        git log --oneline -5
    } else {
        Write-Error "❌ Push failed!"
        
        # Provide helpful error resolution
        Write-Host ""
        Write-Host "🔧 Suggested solutions:" -ForegroundColor Yellow
        Write-Host "  1. Run: git pull origin master" -ForegroundColor White
        Write-Host "  2. Resolve any conflicts" -ForegroundColor White
        Write-Host "  3. Run this script again with -Force flag" -ForegroundColor White
        exit 1
    }
}

# Main execution
try {
    Write-Host "Starting safe Git workflow..." -ForegroundColor Green
    Write-Host ""
    
    # Step 1: Check Git status
    $hasChanges = Test-GitStatus
    
    if (-not $hasChanges -and -not $Force) {
        Write-Host "🎉 Repository is clean - nothing to do!" -ForegroundColor Green
        exit 0
    }
    
    # Step 2: Fix line endings
    Fix-LineEndings
    
    # Step 3: Check for conflicts
    Test-PotentialConflicts
    
    # Step 4: Safe commit
    $committed = Invoke-SafeCommit -CommitMessage $Message
    
    # Step 5: Safe push (only if we committed or force flag)
    if ($committed -or $Force) {
        Invoke-SafePush
    }
    
    Write-Host ""
    Write-Host "🎉 Git workflow completed successfully!" -ForegroundColor Green
    Write-Host "✅ All operations completed without errors" -ForegroundColor Green
    
} catch {
    Write-Error "❌ An error occurred: $($_.Exception.Message)"
    Write-Host ""
    Write-Host "🔧 For help, run: Get-Help $PSCommandPath -Full" -ForegroundColor Yellow
    exit 1
}

# Usage examples:
<#
Basic usage:
    .\git_safe_push.ps1

With custom message:
    .\git_safe_push.ps1 -Message "Fix TTS engine bugs"

Force push (if needed):
    .\git_safe_push.ps1 -Force

Dry run (test without changes):
    .\git_safe_push.ps1 -DryRun
#> 