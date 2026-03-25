#!/bin/bash
# PostgreSQL daily backup script
# Usage: ./scripts/backup.sh
# Recommend: crontab -e -> 0 2 * * * /path/to/backup.sh

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/data/backups}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-family_invest}"
KEEP_DAYS="${KEEP_DAYS:-30}"

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/family_invest_${DATE}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup..."

pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"

echo "[$(date)] Backup created: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"

find "$BACKUP_DIR" -name "family_invest_*.sql.gz" -mtime +"$KEEP_DAYS" -delete

echo "[$(date)] Cleaned up backups older than $KEEP_DAYS days"
echo "[$(date)] Done."
