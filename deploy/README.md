# Deployment Guide for House Consciousness System

This directory contains all the necessary files and configuration for deploying the House Consciousness System to production.

## Quick Start

### 1. Prerequisites

- Docker and Docker Compose
- Python 3.11+
- UV package manager
- Redis server
- Nginx (for production)
- SSL certificates (for HTTPS)

### 2. Development Deployment

```bash
# Clone the repository
git clone <repository-url>
cd consciousness

# Copy environment configuration
cp .env.example .env
# Edit .env with your configuration

# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Access the application
curl http://localhost/health
```

### 3. Production Deployment

```bash
# Copy environment configuration
cp .env.example .env
# Edit .env with production settings

# Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Or use systemd services
sudo cp deploy/systemd/*.service /etc/systemd/system/
sudo systemctl enable consciousness consciousness-worker
sudo systemctl start consciousness consciousness-worker
```

## Directory Structure

```
deploy/
├── nginx/           # Nginx configuration files
│   ├── dev.conf     # Development configuration
│   └── prod.conf    # Production configuration with SSL
├── redis/           # Redis configuration
│   └── redis.conf   # Production Redis settings
├── monitoring/      # Monitoring configuration
│   ├── prometheus.yml
│   └── grafana/
├── systemd/         # Systemd service files
│   ├── consciousness.service
│   └── consciousness-worker.service
└── ssl/             # SSL certificates (not in git)
    ├── consciousness.crt
    └── consciousness.key
```

## Configuration Files

### Docker Configuration

- **Dockerfile**: Multi-stage build for development and production
- **docker-compose.dev.yml**: Development environment with hot reload
- **docker-compose.prod.yml**: Production environment with monitoring

### Web Server Configuration

- **nginx/prod.conf**: Production Nginx configuration with:
  - SSL/TLS termination
  - Rate limiting
  - Security headers
  - Load balancing
  - WebSocket support

### Monitoring

- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and dashboards
- Custom health checks at `/health` and `/health/detailed`

### Security

- Rate limiting and DDoS protection
- Security headers (HSTS, CSP, etc.)
- Audit logging for all security events
- Input validation and sanitization

## Environment Variables

Copy `.env.example` to `.env` and configure:

### Required Settings

```bash
# Security (MUST change these)
SECRET_KEY=your-unique-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
GRAFANA_PASSWORD=your-grafana-password

# API Keys
API_KEY_OPENAI=your-openai-key
API_KEY_ANTHROPIC=your-anthropic-key
```

### Optional Settings

```bash
# Backup to cloud storage
BACKUP_S3_BUCKET=your-s3-bucket
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret

# Notifications
SLACK_WEBHOOK_URL=your-slack-webhook
```

## Deployment Methods

### Method 1: Docker Compose (Recommended)

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Method 2: Systemd Services

```bash
# Install services
sudo cp deploy/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable and start
sudo systemctl enable consciousness consciousness-worker
sudo systemctl start consciousness consciousness-worker

# Check status
sudo systemctl status consciousness
```

### Method 3: Manual Installation

```bash
# Create user and directories
sudo useradd -r -s /bin/bash consciousness
sudo mkdir -p /opt/consciousness/{data,logs,config}
sudo chown -R consciousness:consciousness /opt/consciousness

# Install application
sudo -u consciousness git clone <repo> /opt/consciousness/app
cd /opt/consciousness/app
sudo -u consciousness uv sync

# Start application
sudo -u consciousness uv run uvicorn consciousness.main:app --host 0.0.0.0 --port 8000
```

## SSL/TLS Setup

### Using Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Using Custom Certificates

```bash
# Copy certificates
sudo cp your-cert.crt deploy/ssl/consciousness.crt
sudo cp your-key.key deploy/ssl/consciousness.key
sudo chown root:root deploy/ssl/*
sudo chmod 600 deploy/ssl/*
```

## Monitoring Setup

### Accessing Monitoring

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/[GRAFANA_PASSWORD])
- **Application Health**: http://localhost/health/detailed

### Setting Up Alerts

1. Configure Prometheus alert rules
2. Set up Alertmanager for notifications
3. Configure Grafana dashboards

## Backup and Recovery

### Automated Backups

```bash
# Run backup script
./scripts/backup.sh

# Schedule daily backups
crontab -e
# Add: 0 2 * * * /opt/consciousness/scripts/backup.sh
```

### Manual Backup

```bash
# Create backup
tar -czf consciousness-backup.tar.gz data/ logs/ config/

# Upload to S3 (if configured)
aws s3 cp consciousness-backup.tar.gz s3://your-bucket/backups/
```

### Recovery

```bash
# Restore from backup
./scripts/restore.sh consciousness_backup_20240624_120000.tar.gz

# Or restore manually
sudo systemctl stop consciousness consciousness-worker
tar -xzf backup.tar.gz -C /opt/consciousness/
sudo systemctl start consciousness consciousness-worker
```

## Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   sudo systemctl status consciousness
   sudo journalctl -u consciousness -f
   ```

2. **Database issues**
   ```bash
   # Check database permissions
   ls -la /opt/consciousness/data/

   # Reset database
   rm /opt/consciousness/data/consciousness.db
   uv run alembic upgrade head
   ```

3. **Memory issues**
   ```bash
   # Check memory usage
   docker stats

   # Restart services
   docker-compose restart
   ```

### Health Checks

```bash
# Basic health check
curl http://localhost/health

# Detailed health check
curl http://localhost/health/detailed

# Check all services
docker-compose ps
systemctl status consciousness consciousness-worker
```

### Logs

```bash
# Application logs
docker-compose logs consciousness

# System logs
sudo journalctl -u consciousness -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log
```

## Security Checklist

- [ ] Changed default passwords and secret keys
- [ ] Configured SSL/TLS with valid certificates
- [ ] Set up proper firewall rules
- [ ] Enabled audit logging
- [ ] Configured rate limiting
- [ ] Updated all dependencies
- [ ] Set up monitoring and alerting
- [ ] Tested backup and recovery procedures

## Performance Optimization

### Resource Limits

- Adjust Docker memory/CPU limits in docker-compose.prod.yml
- Configure systemd resource limits in service files
- Monitor resource usage with Grafana dashboards

### Database Optimization

- Regular VACUUM operations for SQLite
- Index optimization for frequently queried tables
- Connection pooling configuration

### Caching

- Redis cache configuration
- Nginx caching for static content
- Application-level caching strategies

## Updates and Maintenance

### Regular Maintenance

1. **Daily**: Check health status and logs
2. **Weekly**: Review security logs and metrics
3. **Monthly**: Update dependencies and security patches
4. **Quarterly**: Test backup/recovery procedures

### Updating the Application

```bash
# Pull latest code
git pull origin main

# Update dependencies
uv sync

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

## Support

For support and troubleshooting:

1. Check application logs
2. Review health check endpoints
3. Monitor Grafana dashboards
4. Check GitHub issues and documentation
