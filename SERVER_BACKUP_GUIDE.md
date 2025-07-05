# 🔒 StreamMate AI Server Backup & Restore Guide

## 📋 Overview

Panduan lengkap untuk backup dan restore server StreamMate AI yang berjalan di VPS `root@69.62.79.238`.

---

## 🛡️ Backup System

### **Automated Backup Script**
- **File**: `backup_server.ps1`
- **Fungsi**: Backup otomatis folder `streammateai_server` dari VPS ke local
- **Output**: Compressed tar.gz file dengan timestamp

### **What Gets Backed Up**
```
streammateai_server/
├── server_inti.py                    # Main server application
├── requirements.txt                  # Python dependencies
├── config/                          # Configuration files
│   ├── settings.json               # App settings
│   ├── subscription_status.json    # User subscriptions
│   ├── google_oauth.json          # OAuth credentials
│   ├── voices.json                 # TTS voice config
│   └── production_config.json     # Production settings
├── billing_security.db             # Payment database
├── logs/                           # Server logs
└── modules_server/                 # Server modules
```

---

## 🚀 Quick Start

### **1. Create Backup**
```powershell
# Run backup script
.\backup_server.ps1

# Or with custom parameters
.\backup_server.ps1 -ServerIP "69.62.79.238" -ServerUser "root" -LocalBackupPath "./backups/"
```

### **2. Restore from Backup**
```powershell
# Interactive restore (shows backup list)
.\restore_server.ps1

# Or specify backup file
.\restore_server.ps1 -BackupFile "streammateai_server_backup_20250701_010320.tar.gz"
```

---

## 📁 Backup Management

### **Backup Location**
- **Local Path**: `./backups/`
- **Naming**: `streammateai_server_backup_YYYYMMDD_HHMMSS.tar.gz`
- **Retention**: Keeps last 5 backups automatically

### **Backup Schedule Recommendations**
- **Daily**: Before major updates
- **Weekly**: Regular maintenance
- **Before Changes**: Code deployments, config updates
- **Before Scaling**: Server migrations

---

## 🔧 Manual Backup Commands

### **Create Manual Backup**
```bash
# SSH to server
ssh root@69.62.79.238

# Create backup
cd /root
tar -czf streammateai_manual_$(date +%Y%m%d_%H%M%S).tar.gz streammateai_server

# Download to local
scp root@69.62.79.238:/root/streammateai_manual_*.tar.gz ./backups/
```

### **Verify Backup Contents**
```powershell
# List files in backup
tar -tzf ./backups/streammateai_server_backup_20250701_010320.tar.gz

# Extract to verify (creates folder)
tar -xzf ./backups/streammateai_server_backup_20250701_010320.tar.gz
```

---

## 🔄 Restore Procedures

### **Full Server Restore**
1. **Stop Server** (if running)
   ```bash
   ssh root@69.62.79.238 "pkill -f server_inti.py"
   ```

2. **Run Restore Script**
   ```powershell
   .\restore_server.ps1
   ```

3. **Restart Server**
   ```bash
   ssh root@69.62.79.238 "cd /root/streammateai_server && python server_inti.py"
   ```

### **Selective Restore**
```bash
# Extract specific files only
tar -xzf backup.tar.gz streammateai_server/config/settings.json
scp streammateai_server/config/settings.json root@69.62.79.238:/root/streammateai_server/config/
```

---

## 🚨 Emergency Procedures

### **Quick Emergency Backup**
```bash
# One-liner emergency backup
ssh root@69.62.79.238 "cd /root && tar -czf emergency_backup_$(date +%Y%m%d_%H%M%S).tar.gz streammateai_server" && scp root@69.62.79.238:/root/emergency_backup_*.tar.gz ./
```

### **Database-Only Backup**
```bash
# Backup only the database
ssh root@69.62.79.238 "cp /root/streammateai_server/billing_security.db /root/db_backup_$(date +%Y%m%d_%H%M%S).db"
scp root@69.62.79.238:/root/db_backup_*.db ./backups/
```

### **Config-Only Backup**
```bash
# Backup only configuration
ssh root@69.62.79.238 "cd /root && tar -czf config_backup_$(date +%Y%m%d_%H%M%S).tar.gz streammateai_server/config"
scp root@69.62.79.238:/root/config_backup_*.tar.gz ./backups/
```

---

## 📊 Backup Monitoring

### **Check Backup Status**
```powershell
# List all local backups
Get-ChildItem ./backups/ -Filter "streammateai_server_backup_*.tar.gz" | 
    Sort-Object LastWriteTime -Descending | 
    ForEach-Object { 
        $sizeMB = [math]::Round($_.Length / 1MB, 2)
        Write-Host "$($_.Name) - $sizeMB MB - $($_.LastWriteTime)"
    }
```

### **Backup Health Check**
```powershell
# Verify latest backup integrity
$latestBackup = Get-ChildItem ./backups/ -Filter "streammateai_server_backup_*.tar.gz" | 
                Sort-Object LastWriteTime -Descending | 
                Select-Object -First 1

tar -tzf $latestBackup.FullName | Measure-Object
```

---

## 🔐 Security Considerations

### **Sensitive Files in Backup**
⚠️ **WARNING**: Backups contain sensitive data:
- `google_oauth.json` - OAuth credentials
- `billing_security.db` - Payment database
- `production_config.json` - Production secrets
- `.env` files - Environment variables

### **Backup Security Best Practices**
1. **Encrypt Backups** for long-term storage
2. **Secure Transfer** - Use SSH keys, not passwords
3. **Access Control** - Limit who can access backups
4. **Regular Testing** - Verify restore procedures work

### **Encryption Example**
```powershell
# Encrypt backup with password
7z a -p"YourStrongPassword" ./backups/encrypted_backup.7z ./backups/streammateai_server_backup_*.tar.gz

# Decrypt when needed
7z x ./backups/encrypted_backup.7z -p"YourStrongPassword"
```

---

## 🔧 Troubleshooting

### **Common Issues**

#### **SSH Connection Failed**
```bash
# Test SSH connection
ssh -v root@69.62.79.238

# Check SSH key
ssh-add -l
```

#### **Backup Too Large**
```bash
# Check server disk space
ssh root@69.62.79.238 "df -h"

# Exclude large files
ssh root@69.62.79.238 "cd /root && tar --exclude='*.pyc' --exclude='__pycache__' -czf backup.tar.gz streammateai_server"
```

#### **Permission Denied**
```bash
# Fix permissions after restore
ssh root@69.62.79.238 "chmod -R 755 /root/streammateai_server"
ssh root@69.62.79.238 "chmod +x /root/streammateai_server/*.py"
```

### **Recovery Scenarios**

#### **Server Completely Down**
1. Check server status: `ssh root@69.62.79.238 "systemctl status"`
2. Check disk space: `ssh root@69.62.79.238 "df -h"`
3. Restore from latest backup: `.\restore_server.ps1`
4. Restart services

#### **Corrupted Database**
1. Stop server: `ssh root@69.62.79.238 "pkill -f server_inti.py"`
2. Backup current state: `ssh root@69.62.79.238 "cp billing_security.db billing_security.db.corrupted"`
3. Restore database from backup
4. Restart server

#### **Config Issues**
1. Backup current config: `ssh root@69.62.79.238 "cp -r config config.backup"`
2. Extract config from backup: `tar -xzf backup.tar.gz streammateai_server/config`
3. Upload config: `scp -r streammateai_server/config/* root@69.62.79.238:/root/streammateai_server/config/`

---

## 📅 Maintenance Schedule

### **Daily Tasks**
- [ ] Check backup script ran successfully
- [ ] Verify latest backup size is reasonable
- [ ] Monitor server disk space

### **Weekly Tasks**
- [ ] Test restore procedure with old backup
- [ ] Clean up old backups (keep last 5)
- [ ] Verify backup integrity

### **Monthly Tasks**
- [ ] Full disaster recovery test
- [ ] Review backup retention policy
- [ ] Update backup scripts if needed

---

## 📞 Emergency Contacts

### **When Backup/Restore Fails**
1. **Check server status** - Is VPS online?
2. **Check network** - Can you SSH to server?
3. **Check disk space** - Server and local storage
4. **Manual intervention** - SSH directly and investigate

### **Escalation Path**
1. **Level 1**: Run backup/restore scripts
2. **Level 2**: Manual SSH commands
3. **Level 3**: Contact VPS provider
4. **Level 4**: Full server rebuild

---

## 📝 Backup Log Template

```
Date: 2025-01-01
Time: 10:30 AM
Action: Scheduled Backup
Status: ✅ Success
File: streammateai_server_backup_20250101_103000.tar.gz
Size: 0.39 MB
Duration: 15 seconds
Notes: Normal backup, all files included
```

---

## 🎯 Best Practices Summary

### **DO**
✅ Backup before any changes  
✅ Test restore procedures regularly  
✅ Keep multiple backup versions  
✅ Monitor backup success/failure  
✅ Secure backup files  

### **DON'T**
❌ Rely on single backup  
❌ Skip backup verification  
❌ Store backups only locally  
❌ Ignore backup failures  
❌ Share backup files insecurely  

---

**🔒 Remember: Your backup is only as good as your last successful restore test!**

---

*Last Updated: 2025-01-01*  
*StreamMate AI Server Backup System v1.0* 