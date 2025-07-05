# StreamMate AI Server Backup Script
# Backup server files from VPS to local

param(
    [string]$ServerIP = "69.62.79.238",
    [string]$ServerUser = "root",
    [string]$ServerFolder = "streammateai_server",
    [string]$LocalBackupPath = "./backups/"
)

# Create timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFileName = "streammateai_server_backup_$timestamp.tar.gz"
$remoteBackupPath = "/root/$backupFileName"

Write-Host "Starting StreamMate AI Server Backup..." -ForegroundColor Green
Write-Host "Timestamp: $timestamp" -ForegroundColor Yellow
Write-Host "Server: $ServerUser@$ServerIP" -ForegroundColor Yellow
Write-Host "Source: $ServerFolder" -ForegroundColor Yellow
Write-Host "Destination: $LocalBackupPath" -ForegroundColor Yellow

# Ensure local backup directory exists
if (!(Test-Path $LocalBackupPath)) {
    New-Item -ItemType Directory -Path $LocalBackupPath -Force
    Write-Host "Created backup directory: $LocalBackupPath" -ForegroundColor Green
}

try {
    # Step 1: Create backup on server
    Write-Host "Creating backup on server..." -ForegroundColor Cyan
    $createBackupCmd = "cd /root; tar -czf $backupFileName $ServerFolder"
    ssh "$ServerUser@$ServerIP" $createBackupCmd
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Backup created successfully on server" -ForegroundColor Green
    } else {
        throw "Failed to create backup on server"
    }

    # Step 2: Download backup to local
    Write-Host "Downloading backup to local..." -ForegroundColor Cyan
    scp "${ServerUser}@${ServerIP}:$remoteBackupPath" "$LocalBackupPath$backupFileName"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Backup downloaded successfully" -ForegroundColor Green
        
        # Get file size
        $fileInfo = Get-Item "$LocalBackupPath$backupFileName"
        $fileSizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
        Write-Host "Backup size: $fileSizeMB MB" -ForegroundColor Yellow
        
    } else {
        throw "Failed to download backup from server"
    }

    # Step 3: Verify backup contents
    Write-Host "Verifying backup contents..." -ForegroundColor Cyan
    $backupContents = tar -tzf "$LocalBackupPath$backupFileName" | Select-Object -First 10
    Write-Host "Backup contains:" -ForegroundColor Yellow
    $backupContents | ForEach-Object { Write-Host "   $_" -ForegroundColor White }

    # Step 4: Clean up server backup
    Write-Host "Cleaning up server backup..." -ForegroundColor Cyan
    ssh "$ServerUser@$ServerIP" "rm -f $remoteBackupPath"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Server cleanup completed" -ForegroundColor Green
    }

    # Step 5: List all local backups
    Write-Host "Local backups:" -ForegroundColor Cyan
    Get-ChildItem $LocalBackupPath -Filter "streammateai_server_backup_*.tar.gz" | 
        Sort-Object LastWriteTime -Descending | 
        ForEach-Object { 
            $sizeMB = [math]::Round($_.Length / 1MB, 2)
            Write-Host "   $($_.Name) - $sizeMB MB - $($_.LastWriteTime)" -ForegroundColor White 
        }

    Write-Host "Backup completed successfully!" -ForegroundColor Green
    Write-Host "Backup saved as: $LocalBackupPath$backupFileName" -ForegroundColor Green

} catch {
    Write-Host "Backup failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Optional: Keep only last 5 backups
Write-Host "Cleaning old backups (keeping last 5)..." -ForegroundColor Cyan
Get-ChildItem $LocalBackupPath -Filter "streammateai_server_backup_*.tar.gz" | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -Skip 5 | 
    ForEach-Object { 
        Remove-Item $_.FullName -Force
        Write-Host "   Deleted: $($_.Name)" -ForegroundColor Yellow
    }

Write-Host "All done! Your StreamMate AI server is safely backed up." -ForegroundColor Green 