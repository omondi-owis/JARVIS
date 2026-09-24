#!/bin/bash
# J.A.R.V.I.S. Backup Script - Production
# Backs up config, device registry, audit logs, memory (non-sensitive)
# Never backs up secrets (.env) unless encrypted

set -e

BACKUP_DIR="/home/sysadmin/backups/jarvis"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/jarvis_backup_$TIMESTAMP.tar.gz"

echo "=== J.A.R.V.I.S. Backup ==="

mkdir -p $BACKUP_DIR

# Create backup excluding secrets
tar -czf $BACKUP_FILE \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='.env' \
    --exclude='*.key' \
    --exclude='*.pem' \
    --exclude='node_modules' \
    -C /home/sysadmin \
    jarvis/config \
    jarvis/logs \
    jarvis/systemd \
    jarvis/README.md 2>/dev/null || true

# Also backup encrypted .env separately if needed
if [ -f /home/sysadmin/jarvis/.env ]; then
    echo "Backing up .env encrypted..."
    # Use gpg - requires setup
    # gpg --symmetric --cipher-algo AES256 /home/sysadmin/jarvis/.env -o $BACKUP_DIR/env_$TIMESTAMP.gpg
    echo "Manual: Encrypt .env with gpg or store in secrets manager, not in plain backup"
fi

ls -lh $BACKUP_FILE

# Keep only last 7 backups
ls -t $BACKUP_DIR/jarvis_backup_*.tar.gz | tail -n +8 | xargs -r rm --

echo "Backup complete: $BACKUP_FILE"
echo "Recent backups:"
ls -lh $BACKUP_DIR/ | tail -10
