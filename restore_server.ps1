# StreamMate AI Server Restore Script
# Restore server files from local backup to VPS

param(
    [string]$ServerIP = "69.62.79.238",
    [string]$ServerUser = "root",
    [string]$ServerFolder = "streammateai_server",
    [string]$LocalBackupPath = "./backups/",
    [string]$BackupFile = ""
)

Write-Host "Starting StreamMate AI Server Restore..." -ForegroundColor Green

# If no backup file specified, show available backups
if ([string]::IsNullOrEmpty($BackupFile)) {
    Write-Host "Available backups:" -ForegroundColor Yellow
    $backups = Get-ChildItem $LocalBackupPath -Filter "streammateai_server_backup_*.tar.gz" | Sort-Object LastWriteTime -Descending
    
    for ($i = 0; $i -lt $backups.Count; $i++) {
        $sizeMB = [math]::Round($backups[$i].Length / 1MB, 2)
        Write-Host "  [$i] $($backups[$i].Name) - $sizeMB MB - $($backups[$i].LastWriteTime)" -ForegroundColor White
    }
    
    if ($backups.Count -eq 0) {
        Write-Host "No backups found. Please run backup_server.ps1 first." -ForegroundColor Red
        exit 1
    }
    
    $choice = Read-Host "Select backup number (0-$($backups.Count-1)) or press Enter for latest"
    
    if ([string]::IsNullOrEmpty($choice)) {
        $BackupFile = $backups[0].Name
    } else {
        $choiceInt = [int]$choice
        if ($choiceInt -ge 0 -and $choiceInt -lt $backups.Count) {
            $BackupFile = $backups[$choiceInt].Name
        } else {
            Write-Host "Invalid choice. Using latest backup." -ForegroundColor Yellow
            $BackupFile = $backups[0].Name
        }
    }
}

$localBackupFile = "$LocalBackupPath$BackupFile"

# Verify backup file exists
if (!(Test-Path $localBackupFile)) {
    Write-Host "Backup file not found: $localBackupFile" -ForegroundColor Red
    exit 1
}

Write-Host "Selected backup: $BackupFile" -ForegroundColor Green

# Confirm restore
$confirm = Read-Host "This will OVERWRITE the current server files. Are you sure? (yes/no)"
if ($confirm.ToLower() -ne "yes") {
    Write-Host "Restore cancelled." -ForegroundColor Yellow
    exit 0
}

try {
    # Step 1: Upload backup to server
    Write-Host "Uploading backup to server..." -ForegroundColor Cyan
    $remoteBackupPath = "/root/restore_$BackupFile"
    scp $localBackupFile "${ServerUser}@${ServerIP}:$remoteBackupPath"
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upload backup to server"
    }
    
    Write-Host "Backup uploaded successfully" -ForegroundColor Green

    # Step 2: Create backup of current server files
    Write-Host "Creating backup of current server files..." -ForegroundColor Cyan
    $currentBackupName = "current_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').tar.gz"
    ssh "$ServerUser@$ServerIP" "cd /root && tar -czf $currentBackupName $ServerFolder"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Current server files backed up as: $currentBackupName" -ForegroundColor Green
    }

    # Step 3: Remove current server folder
    Write-Host "Removing current server files..." -ForegroundColor Cyan
    ssh "$ServerUser@$ServerIP" "rm -rf /root/$ServerFolder"

    # Step 4: Extract backup
    Write-Host "Extracting backup..." -ForegroundColor Cyan
    ssh "$ServerUser@$ServerIP" "cd /root && tar -xzf $remoteBackupPath"
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to extract backup"
    }
    
    Write-Host "Backup extracted successfully" -ForegroundColor Green

    # Step 5: Set permissions
    Write-Host "Setting permissions..." -ForegroundColor Cyan
    ssh "$ServerUser@$ServerIP" "chmod -R 755 /root/$ServerFolder"
    ssh "$ServerUser@$ServerIP" "chmod +x /root/$ServerFolder/*.py"

    # Step 6: Clean up
    Write-Host "Cleaning up..." -ForegroundColor Cyan
    ssh "$ServerUser@$ServerIP" "rm -f $remoteBackupPath"

    # Step 7: Verify restore
    Write-Host "Verifying restore..." -ForegroundColor Cyan
    $serverFiles = ssh "$ServerUser@$ServerIP" "ls -la /root/$ServerFolder | wc -l"
    Write-Host "Server files count: $serverFiles" -ForegroundColor Yellow

    Write-Host "Restore completed successfully!" -ForegroundColor Green
    Write-Host "Server files have been restored from: $BackupFile" -ForegroundColor Green
    Write-Host "Previous server files backed up as: $currentBackupName" -ForegroundColor Yellow

} catch {
    Write-Host "Restore failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Server may be in inconsistent state. Please check manually." -ForegroundColor Red
    exit 1
}

Write-Host "All done! Server has been restored from backup." -ForegroundColor Green 