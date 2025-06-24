#!/bin/bash
# Comprehensive backup script for House Consciousness System

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/opt/consciousness/backups}"
DATA_DIR="${DATA_DIR:-/opt/consciousness/data}"
LOGS_DIR="${LOGS_DIR:-/opt/consciousness/logs}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="consciousness_backup_${TIMESTAMP}"

# Ensure backup directory exists
mkdir -p "${BACKUP_DIR}"

echo "Starting backup: ${BACKUP_NAME}"
echo "Data directory: ${DATA_DIR}"
echo "Backup directory: ${BACKUP_DIR}"

# Create main backup archive
echo "Creating main data backup..."
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" \
    -C "${DATA_DIR}" \
    --exclude="*.tmp" \
    --exclude="*.log" \
    --exclude="*.swp" \
    . || {
    echo "Error: Failed to create main backup archive"
    exit 1
}

# Backup database separately for point-in-time recovery
if [ -f "${DATA_DIR}/consciousness.db" ]; then
    echo "Creating database backup..."
    cp "${DATA_DIR}/consciousness.db" "${BACKUP_DIR}/consciousness_${TIMESTAMP}.db"

    # Create database dump for portability
    sqlite3 "${DATA_DIR}/consciousness.db" .dump > "${BACKUP_DIR}/consciousness_${TIMESTAMP}.sql"
    gzip "${BACKUP_DIR}/consciousness_${TIMESTAMP}.sql"
else
    echo "Warning: Database file not found at ${DATA_DIR}/consciousness.db"
fi

# Backup logs
if [ -d "${LOGS_DIR}" ] && [ "$(ls -A ${LOGS_DIR})" ]; then
    echo "Creating logs backup..."
    tar -czf "${BACKUP_DIR}/logs_${TIMESTAMP}.tar.gz" \
        -C "${LOGS_DIR}" \
        . || {
        echo "Warning: Failed to backup logs"
    }
fi

# Backup configuration files
if [ -d "/opt/consciousness/config" ]; then
    echo "Creating configuration backup..."
    tar -czf "${BACKUP_DIR}/config_${TIMESTAMP}.tar.gz" \
        -C "/opt/consciousness" \
        config/ || {
        echo "Warning: Failed to backup configuration"
    }
fi

# Generate backup manifest
cat > "${BACKUP_DIR}/${BACKUP_NAME}.manifest" << EOF
{
    "backup_name": "${BACKUP_NAME}",
    "timestamp": "${TIMESTAMP}",
    "created_at": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "data_size": "$(du -sh ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz | cut -f1)",
    "files": [
        "${BACKUP_NAME}.tar.gz",
        "consciousness_${TIMESTAMP}.db",
        "consciousness_${TIMESTAMP}.sql.gz",
        "logs_${TIMESTAMP}.tar.gz",
        "config_${TIMESTAMP}.tar.gz"
    ]
}
EOF

# Create checksums for integrity verification
echo "Generating checksums..."
cd "${BACKUP_DIR}"
sha256sum "${BACKUP_NAME}"* > "${BACKUP_NAME}.checksums"

# Clean old backups (keep last 30 days)
echo "Cleaning old backups..."
find "${BACKUP_DIR}" -name "consciousness_backup_*.tar.gz" -mtime +30 -delete
find "${BACKUP_DIR}" -name "consciousness_*.db" -mtime +30 -delete
find "${BACKUP_DIR}" -name "consciousness_*.sql.gz" -mtime +30 -delete
find "${BACKUP_DIR}" -name "logs_*.tar.gz" -mtime +30 -delete
find "${BACKUP_DIR}" -name "config_*.tar.gz" -mtime +30 -delete
find "${BACKUP_DIR}" -name "*.manifest" -mtime +30 -delete
find "${BACKUP_DIR}" -name "*.checksums" -mtime +30 -delete

# Get final backup size
BACKUP_SIZE=$(du -sh "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | cut -f1)

echo "Backup completed successfully!"
echo "Main backup: ${BACKUP_NAME}.tar.gz (${BACKUP_SIZE})"
echo "Location: ${BACKUP_DIR}"

# Upload to cloud storage if configured
if [ ! -z "${BACKUP_S3_BUCKET}" ] && command -v aws &> /dev/null; then
    echo "Uploading backup to S3..."
    aws s3 cp "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" "s3://${BACKUP_S3_BUCKET}/consciousness-backups/" && \
    aws s3 cp "${BACKUP_DIR}/${BACKUP_NAME}.manifest" "s3://${BACKUP_S3_BUCKET}/consciousness-backups/" && \
    echo "Backup uploaded to S3 successfully"
fi

# Send notification if configured
if [ ! -z "${BACKUP_WEBHOOK_URL}" ]; then
    curl -X POST "${BACKUP_WEBHOOK_URL}" \
        -H "Content-Type: application/json" \
        -d "{\"message\":\"Consciousness backup completed: ${BACKUP_NAME} (${BACKUP_SIZE})\"}" \
        > /dev/null 2>&1 || echo "Warning: Failed to send backup notification"
fi

echo "Backup process finished at $(date)"
