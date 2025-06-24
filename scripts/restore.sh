#!/bin/bash
# Comprehensive restore script for House Consciousness System

set -e

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file> [--force] [--no-backup]"
    echo ""
    echo "Options:"
    echo "  --force      Skip confirmation prompts"
    echo "  --no-backup  Skip backing up current data"
    echo ""
    echo "Examples:"
    echo "  $0 consciousness_backup_20240624_120000.tar.gz"
    echo "  $0 consciousness_backup_20240624_120000.tar.gz --force"
    exit 1
fi

BACKUP_FILE="$1"
FORCE_MODE=""
NO_BACKUP=""

# Parse additional arguments
shift
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE_MODE="true"
            shift
            ;;
        --no-backup)
            NO_BACKUP="true"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Configuration
DATA_DIR="${DATA_DIR:-/opt/consciousness/data}"
BACKUP_DIR="${BACKUP_DIR:-/opt/consciousness/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Validate backup file
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: Backup file '${BACKUP_FILE}' not found"
    exit 1
fi

# Check if file is in backup directory, if not assume it's a path
if [[ "${BACKUP_FILE}" != *"/"* ]]; then
    BACKUP_FILE="${BACKUP_DIR}/${BACKUP_FILE}"
fi

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: Backup file '${BACKUP_FILE}' not found"
    exit 1
fi

echo "House Consciousness System Restore"
echo "=================================="
echo "Backup file: ${BACKUP_FILE}"
echo "Data directory: ${DATA_DIR}"
echo "Restore timestamp: ${TIMESTAMP}"
echo ""

# Verify backup integrity if checksums exist
BACKUP_BASE=$(basename "${BACKUP_FILE}" .tar.gz)
CHECKSUM_FILE="${BACKUP_DIR}/${BACKUP_BASE}.checksums"

if [ -f "${CHECKSUM_FILE}" ]; then
    echo "Verifying backup integrity..."
    cd "${BACKUP_DIR}"
    if sha256sum -c "${CHECKSUM_FILE}" --quiet; then
        echo "✓ Backup integrity verified"
    else
        echo "✗ Backup integrity check failed!"
        if [ -z "${FORCE_MODE}" ]; then
            read -p "Continue anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi
else
    echo "Warning: No checksum file found for integrity verification"
fi

# Show backup manifest if available
MANIFEST_FILE="${BACKUP_DIR}/${BACKUP_BASE}.manifest"
if [ -f "${MANIFEST_FILE}" ]; then
    echo ""
    echo "Backup Information:"
    cat "${MANIFEST_FILE}"
    echo ""
fi

# Confirmation prompt
if [ -z "${FORCE_MODE}" ]; then
    echo "WARNING: This will replace all current data in ${DATA_DIR}"
    echo "Current data will be backed up to ${DATA_DIR}_backup_${TIMESTAMP}"
    echo ""
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Restore cancelled"
        exit 0
    fi
fi

# Check if services are running and stop them
SERVICES=("consciousness" "consciousness-worker")
STOPPED_SERVICES=()

for service in "${SERVICES[@]}"; do
    if systemctl is-active --quiet "$service" 2>/dev/null; then
        echo "Stopping service: $service"
        sudo systemctl stop "$service"
        STOPPED_SERVICES+=("$service")
    fi
done

# Also stop Docker containers if they're running
if command -v docker-compose &> /dev/null; then
    if [ -f "docker-compose.prod.yml" ]; then
        echo "Stopping Docker containers..."
        docker-compose -f docker-compose.prod.yml down
    fi
fi

# Backup current data unless --no-backup is specified
if [ -z "${NO_BACKUP}" ] && [ -d "${DATA_DIR}" ]; then
    echo "Backing up current data..."
    mv "${DATA_DIR}" "${DATA_DIR}_backup_${TIMESTAMP}"
    echo "Current data backed up to: ${DATA_DIR}_backup_${TIMESTAMP}"
fi

# Create new data directory
echo "Creating data directory..."
mkdir -p "${DATA_DIR}"

# Extract backup
echo "Restoring from backup..."
tar -xzf "${BACKUP_FILE}" -C "${DATA_DIR}" || {
    echo "Error: Failed to extract backup"

    # Restore original data if backup failed
    if [ -d "${DATA_DIR}_backup_${TIMESTAMP}" ]; then
        echo "Restoring original data..."
        rm -rf "${DATA_DIR}"
        mv "${DATA_DIR}_backup_${TIMESTAMP}" "${DATA_DIR}"
    fi
    exit 1
}

# Set proper permissions
echo "Setting permissions..."
if id "consciousness" &>/dev/null; then
    chown -R consciousness:consciousness "${DATA_DIR}"
else
    echo "Warning: consciousness user not found, using current user"
fi
chmod -R 755 "${DATA_DIR}"

# Restart services
echo "Starting services..."
for service in "${STOPPED_SERVICES[@]}"; do
    echo "Starting service: $service"
    sudo systemctl start "$service"
done

# Start Docker containers if compose file exists
if [ -f "docker-compose.prod.yml" ]; then
    echo "Starting Docker containers..."
    docker-compose -f docker-compose.prod.yml up -d
fi

# Verify restoration
echo "Verifying restoration..."
sleep 10

# Health check
if command -v curl &> /dev/null; then
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✓ Health check passed"
    else
        echo "✗ Health check failed"
        echo "Services may need manual intervention"
    fi
else
    echo "Warning: curl not available for health check"
fi

# Check database
if [ -f "${DATA_DIR}/consciousness.db" ]; then
    if sqlite3 "${DATA_DIR}/consciousness.db" "SELECT 1" > /dev/null 2>&1; then
        echo "✓ Database verification passed"
    else
        echo "✗ Database verification failed"
    fi
fi

echo ""
echo "Restoration completed successfully!"
echo "Restored from: ${BACKUP_FILE}"
echo "Data location: ${DATA_DIR}"

if [ -d "${DATA_DIR}_backup_${TIMESTAMP}" ]; then
    echo "Previous data saved to: ${DATA_DIR}_backup_${TIMESTAMP}"
    echo ""
    echo "You can remove the backup with:"
    echo "  rm -rf ${DATA_DIR}_backup_${TIMESTAMP}"
fi

echo ""
echo "Restore process finished at $(date)"
