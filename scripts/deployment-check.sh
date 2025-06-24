#!/bin/bash
# Comprehensive deployment verification script for House Consciousness System

set -e

echo "House Consciousness System - Deployment Verification"
echo "=================================================="
echo "Timestamp: $(date)"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SUCCESS=0
WARNINGS=0
ERRORS=0

# Function to print status
print_status() {
    local status=$1
    local message=$2

    case $status in
        "ok")
            echo -e "${GREEN}✓${NC} $message"
            ((SUCCESS++))
            ;;
        "warn")
            echo -e "${YELLOW}⚠${NC} $message"
            ((WARNINGS++))
            ;;
        "error")
            echo -e "${RED}✗${NC} $message"
            ((ERRORS++))
            ;;
    esac
}

# Check Docker installation
check_docker() {
    echo "Checking Docker Installation..."

    if command -v docker &> /dev/null; then
        print_status "ok" "Docker is installed"
        docker --version
    else
        print_status "error" "Docker is not installed"
    fi

    if command -v docker-compose &> /dev/null; then
        print_status "ok" "Docker Compose is installed"
        docker-compose --version
    else
        print_status "error" "Docker Compose is not installed"
    fi
    echo ""
}

# Check configuration files
check_config_files() {
    echo "Checking Configuration Files..."

    local files=(
        "Dockerfile"
        "docker-compose.dev.yml"
        "docker-compose.prod.yml"
        "deploy/nginx/dev.conf"
        "deploy/nginx/prod.conf"
        "scripts/backup.sh"
        "scripts/restore.sh"
        ".env.example"
    )

    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            print_status "ok" "Found $file"
        else
            print_status "error" "Missing $file"
        fi
    done
    echo ""
}

# Check environment configuration
check_environment() {
    echo "Checking Environment Configuration..."

    if [ -f ".env" ]; then
        print_status "ok" "Environment file exists"

        # Check for required variables
        local required_vars=(
            "SECRET_KEY"
            "JWT_SECRET_KEY"
            "DATABASE_URL"
            "REDIS_URL"
        )

        for var in "${required_vars[@]}"; do
            if grep -q "^${var}=" .env; then
                print_status "ok" "$var is configured"
            else
                print_status "warn" "$var is not configured"
            fi
        done
    else
        print_status "warn" "No .env file found - copy from .env.example"
    fi
    echo ""
}

# Check Docker services
check_docker_services() {
    echo "Checking Docker Services..."

    if [ -f "docker-compose.prod.yml" ]; then
        # Check if services are running
        if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
            print_status "ok" "Docker services are running"
            docker-compose -f docker-compose.prod.yml ps
        else
            print_status "warn" "Docker services are not running"
        fi
    fi
    echo ""
}

# Check network connectivity
check_network() {
    echo "Checking Network Connectivity..."

    # Check if main service is responding
    if curl -sf http://localhost/health > /dev/null 2>&1; then
        print_status "ok" "Main service is responding"

        # Get detailed health check
        health_response=$(curl -s http://localhost/health/detailed 2>/dev/null || echo "{}")
        if echo "$health_response" | grep -q "healthy"; then
            print_status "ok" "Detailed health check passed"
        else
            print_status "warn" "Detailed health check shows issues"
        fi
    else
        print_status "warn" "Main service is not responding on port 80"
    fi

    # Check direct application port
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        print_status "ok" "Application is responding on port 8000"
    else
        print_status "warn" "Application is not responding on port 8000"
    fi
    echo ""
}

# Check monitoring services
check_monitoring() {
    echo "Checking Monitoring Services..."

    # Check Prometheus
    if curl -sf http://localhost:9090/-/healthy > /dev/null 2>&1; then
        print_status "ok" "Prometheus is running"
    else
        print_status "warn" "Prometheus is not accessible"
    fi

    # Check Grafana
    if curl -sf http://localhost:3000/api/health > /dev/null 2>&1; then
        print_status "ok" "Grafana is running"
    else
        print_status "warn" "Grafana is not accessible"
    fi
    echo ""
}

# Check system resources
check_resources() {
    echo "Checking System Resources..."

    # Check disk space
    disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -lt 80 ]; then
        print_status "ok" "Disk usage is $disk_usage% (healthy)"
    elif [ "$disk_usage" -lt 90 ]; then
        print_status "warn" "Disk usage is $disk_usage% (monitor closely)"
    else
        print_status "error" "Disk usage is $disk_usage% (critical)"
    fi

    # Check memory usage if available
    if command -v free &> /dev/null; then
        memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
        if [ "$memory_usage" -lt 80 ]; then
            print_status "ok" "Memory usage is $memory_usage% (healthy)"
        elif [ "$memory_usage" -lt 90 ]; then
            print_status "warn" "Memory usage is $memory_usage% (monitor closely)"
        else
            print_status "error" "Memory usage is $memory_usage% (critical)"
        fi
    fi
    echo ""
}

# Check backup system
check_backup() {
    echo "Checking Backup System..."

    if [ -x "scripts/backup.sh" ]; then
        print_status "ok" "Backup script is executable"
    else
        print_status "warn" "Backup script is not executable"
    fi

    if [ -x "scripts/restore.sh" ]; then
        print_status "ok" "Restore script is executable"
    else
        print_status "warn" "Restore script is not executable"
    fi

    # Check backup directory
    backup_dir="${BACKUP_DIR:-./backups}"
    if [ -d "$backup_dir" ]; then
        backup_count=$(find "$backup_dir" -name "*.tar.gz" | wc -l)
        print_status "ok" "Backup directory exists with $backup_count backups"
    else
        print_status "warn" "Backup directory not found"
    fi
    echo ""
}

# Check security configuration
check_security() {
    echo "Checking Security Configuration..."

    # Check if running as root (not recommended)
    if [ "$EUID" -eq 0 ]; then
        print_status "warn" "Running as root - consider using non-root user"
    else
        print_status "ok" "Not running as root"
    fi

    # Check for default passwords in .env
    if [ -f ".env" ]; then
        if grep -q "your-.*-here" .env; then
            print_status "warn" "Default passwords detected in .env file"
        else
            print_status "ok" "No default passwords found in .env"
        fi
    fi

    # Check SSL certificates
    if [ -f "deploy/ssl/consciousness.crt" ] && [ -f "deploy/ssl/consciousness.key" ]; then
        print_status "ok" "SSL certificates found"
    else
        print_status "warn" "SSL certificates not found"
    fi
    echo ""
}

# Main execution
main() {
    check_docker
    check_config_files
    check_environment
    check_docker_services
    check_network
    check_monitoring
    check_resources
    check_backup
    check_security

    echo "Deployment Verification Summary"
    echo "=============================="
    echo -e "${GREEN}✓ Successful checks: $SUCCESS${NC}"
    echo -e "${YELLOW}⚠ Warnings: $WARNINGS${NC}"
    echo -e "${RED}✗ Errors: $ERRORS${NC}"
    echo ""

    if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}🎉 Deployment verification passed! System is ready for production.${NC}"
        exit 0
    elif [ $ERRORS -eq 0 ]; then
        echo -e "${YELLOW}⚠ Deployment verification completed with warnings. Review and address warnings.${NC}"
        exit 1
    else
        echo -e "${RED}❌ Deployment verification failed! Address errors before proceeding.${NC}"
        exit 2
    fi
}

# Run main function
main "$@"
