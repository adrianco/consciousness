# Operating Guide

This guide covers day-to-day operations, maintenance, and monitoring of your House Consciousness System.

## Overview

The consciousness system is designed to run continuously, learning and adapting to your home environment. This guide helps you keep it healthy and understand what's happening under the hood.

## 📊 Monitoring & Observability

### What You Should Monitor

**System Health:**
- CPU and memory usage
- Database performance and size
- API response times
- Device discovery success rates
- AI conversation response times
- Error rates and exceptions

**Business Metrics:**
- Number of devices discovered and managed
- Automation scenarios executed
- User interactions (chat messages, API calls)
- Learning model accuracy over time
- Energy optimization savings
- Security events detected

### Prometheus Metrics (Advanced Monitoring)

**Setup Prometheus:**
```bash
# Install Prometheus
# macOS:
brew install prometheus

# Ubuntu/Debian:
sudo apt install prometheus

# Or use Docker:
docker run -p 9090:9090 prom/prometheus
```

**Configure Prometheus** (`prometheus.yml`):
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'consciousness'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

**Metrics the system exposes:**
- `consciousness_active_sessions` - Current active user sessions
- `consciousness_total_requests` - Total API requests processed
- `consciousness_device_count` - Number of discovered devices
- `consciousness_discovery_success_rate` - Device discovery success %
- `consciousness_ai_response_time` - AI conversation response times
- `consciousness_automation_executions` - Scenarios run count
- `consciousness_errors_total` - Total system errors
- `consciousness_memory_usage_bytes` - Memory consumption
- `consciousness_database_size_bytes` - Database size

### Grafana Dashboards (Visualization)

**Setup Grafana:**
```bash
# Install Grafana
# macOS:
brew install grafana

# Ubuntu/Debian:
sudo apt install grafana

# Or use Docker:
docker run -d -p 3000:3000 grafana/grafana
```

**Access:** http://localhost:3000 (admin/admin)

**Recommended Dashboards:**

1. **System Overview Dashboard**
   - System uptime and health status
   - API request rates and response times
   - Error rates and recent alerts
   - Resource utilization (CPU, memory, disk)

2. **Device Management Dashboard**
   - Device discovery trends over time
   - Device online/offline status
   - Device type distribution
   - Discovery protocol success rates

3. **AI & Automation Dashboard**
   - Conversation volume and response times
   - Most used automation scenarios
   - Learning model accuracy metrics
   - User interaction patterns

4. **Security Dashboard**
   - Security events and alerts
   - Failed authentication attempts
   - Unusual device behavior
   - Network scanning attempts

## 🔧 Daily Operations

### Starting the System

**Development/Testing:**
```bash
# Activate environment
source consciousness-env/bin/activate

# Start with auto-reload
python -m consciousness.main

# Or with specific configuration
DEBUG=true python -m consciousness.main
```

**Production (Systemd):**
```bash
# Start service
sudo systemctl start consciousness

# Check status
sudo systemctl status consciousness

# View logs
journalctl -u consciousness -f
```

**Production (Docker):**
```bash
# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f consciousness
```

### Health Checks

**Basic Health Check:**
```bash
curl http://localhost:8000/health
```

**Detailed Health Check:**
```bash
curl http://localhost:8000/health/detailed
```

**Web Interface Health:**
- Visit http://localhost:8000
- Check system status indicators
- Verify device count updates
- Test chat functionality

### Log Management

**Log Locations:**
- Application logs: `logs/consciousness.log`
- System logs: `journalctl -u consciousness`
- Docker logs: `docker-compose logs consciousness`
- Web server logs: Usually in `/var/log/nginx/` if using reverse proxy

**Log Rotation:**
```bash
# Configure logrotate for application logs
sudo cat > /etc/logrotate.d/consciousness << EOF
/path/to/consciousness/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 644 consciousness consciousness
    postrotate
        systemctl reload consciousness
    endscript
}
EOF
```

## 🛠️ Maintenance Tasks

### Daily Checks

**Automated (add to crontab):**
```bash
# Check system health daily at 9 AM
0 9 * * * curl -f http://localhost:8000/health || echo "Consciousness system down" | mail -s "Alert" admin@yourdomain.com

# Check disk space
0 8 * * * df -h /path/to/consciousness | awk 'NR==2{print $5}' | grep -q "9[0-9]%" && echo "Disk space low" | mail -s "Disk Alert" admin@yourdomain.com
```

**Manual Checks:**
- [ ] System responding on web interface
- [ ] Device discovery working
- [ ] Chat interface responsive
- [ ] No error spikes in logs
- [ ] Database size reasonable

### Weekly Maintenance

**Performance Review:**
```bash
# Check database size
du -sh consciousness.db

# Check memory usage
ps aux | grep consciousness

# Review error logs
grep -i error logs/consciousness.log | tail -20

# Check device discovery stats
curl http://localhost:8000/metrics | grep device_count
```

**Backup Verification:**
```bash
# Test backup script
./scripts/backup.sh

# Verify backup integrity
ls -la memory/backups/
```

### Monthly Maintenance

**System Updates:**
```bash
# Update Python dependencies
pip install --upgrade -r requirements.txt

# Update system packages
sudo apt update && sudo apt upgrade

# Restart services
sudo systemctl restart consciousness
```

**Database Maintenance:**
```bash
# Vacuum SQLite database (if using SQLite)
sqlite3 consciousness.db "VACUUM;"

# Analyze database performance
sqlite3 consciousness.db ".schema"
```

**Security Review:**
```bash
# Check for security updates
./scripts/security-scan.sh

# Review access logs
grep -i "failed\|denied\|error" logs/consciousness.log

# Update SSL certificates (if applicable)
sudo certbot renew
```

## 🚨 Troubleshooting

### Common Issues

**System Won't Start:**
```bash
# Check logs
tail -f logs/consciousness.log

# Check port availability
netstat -tlnp | grep :8000

# Check dependencies
pip list | grep -E "(fastapi|uvicorn|sqlalchemy)"

# Check environment variables
env | grep -E "(DEBUG|DATABASE_URL|REDIS_URL)"
```

**High Memory Usage:**
```bash
# Check memory usage
ps aux | grep consciousness

# Check for memory leaks
grep -i "memory\|oom" /var/log/syslog

# Restart service if needed
sudo systemctl restart consciousness
```

**Device Discovery Not Working:**
```bash
# Check Bluetooth service
sudo systemctl status bluetooth

# Check network connectivity
ping 8.8.8.8

# Check discovery protocols
grep -i "discovery\|device" logs/consciousness.log

# Test manual discovery
curl -X POST http://localhost:8000/api/discovery/scan
```

**Database Issues:**
```bash
# Check database connectivity
sqlite3 consciousness.db ".tables"

# Check database locks
fuser consciousness.db

# Check disk space
df -h .

# Backup and recreate if corrupted
cp consciousness.db consciousness.db.backup
rm consciousness.db
# Restart service to recreate
sudo systemctl restart consciousness
```

**AI Chat Not Responding:**
```bash
# Check API keys in .env
grep -E "(OPENAI|ANTHROPIC)" .env

# Test API connectivity
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models

# Check AI service logs
grep -i "ai\|openai\|anthropic" logs/consciousness.log
```

### Performance Tuning

**Database Performance:**
```bash
# Add database indexes (for PostgreSQL)
# This would be implemented in migration scripts

# Optimize SQLite
echo "PRAGMA optimize;" | sqlite3 consciousness.db
```

**Memory Optimization:**
```python
# In .env file:
MEMORY_RETENTION_DAYS=30  # Reduce from 365
EMOTION_UPDATE_INTERVAL=600  # Increase from 300
```

**API Performance:**
```bash
# Enable Redis for caching
REDIS_URL=redis://localhost:6379/0

# Increase worker processes
uvicorn consciousness.main:app --workers 4
```

## 🔐 Security Operations

### Security Monitoring

**Daily Security Checks:**
```bash
# Check failed login attempts
grep -i "failed\|denied" logs/consciousness.log

# Check unusual API access patterns
awk '{print $1}' access.log | sort | uniq -c | sort -nr | head -10

# Check for new devices
curl http://localhost:8000/api/devices/discovered | jq '.[] | select(.first_seen > "2024-01-01")'
```

**Security Hardening:**
```bash
# Update security keys (in production)
openssl rand -base64 32  # New SECRET_KEY
openssl rand -base64 32  # New JWT_SECRET_KEY

# Enable firewall
sudo ufw enable
sudo ufw allow 8000/tcp

# Set up fail2ban for API protection
sudo apt install fail2ban
# Configure fail2ban rules for consciousness API
```

### Backup & Recovery

**Automated Backups:**
```bash
# Daily backup script (add to crontab)
0 2 * * * /path/to/consciousness/scripts/backup.sh

# Weekly backup verification
0 3 * * 0 /path/to/consciousness/scripts/verify-backup.sh
```

**Recovery Procedures:**
```bash
# Restore from backup
./scripts/restore.sh /path/to/backup.json

# Verify restoration
curl http://localhost:8000/health/detailed
```

## 📈 Capacity Planning

### Growth Monitoring

**Track these metrics over time:**
- Database growth rate (MB/month)
- Device count growth
- API request volume growth
- Memory usage trends
- Disk space consumption

**Scaling Indicators:**
- API response time > 2 seconds consistently
- Memory usage > 80% regularly
- Database queries taking > 100ms
- Device discovery taking > 30 seconds

**Scaling Options:**
- Upgrade to PostgreSQL from SQLite
- Add Redis for caching
- Move to container orchestration (Kubernetes)
- Implement API rate limiting
- Add read replicas for database

## 🔔 Alerting

### Recommended Alerts

**Critical Alerts:**
- System down for > 5 minutes
- Database connectivity lost
- Memory usage > 90%
- Disk space > 85%
- Error rate > 5% over 10 minutes

**Warning Alerts:**
- Response time > 2 seconds average
- Device discovery failure rate > 20%
- Memory usage > 70%
- Disk space > 75%

**Setup with Prometheus Alertmanager:**
```yaml
# alerts.yml
groups:
- name: consciousness.rules
  rules:
  - alert: ConsciousnessDown
    expr: up{job="consciousness"} == 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Consciousness system is down"

  - alert: HighMemoryUsage
    expr: consciousness_memory_usage_bytes > 1000000000
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage detected"
```

## 🎯 Best Practices

### Development
- Always test changes in development environment first
- Use feature flags for gradual rollouts
- Keep dependencies updated
- Monitor performance impact of changes

### Production
- Use configuration management (Ansible, Terraform)
- Implement blue-green deployments
- Monitor error rates after deployments
- Have rollback procedures ready

### Maintenance
- Schedule maintenance during low-usage periods
- Always backup before major changes
- Test backups regularly
- Document all changes in change log

## 📚 Additional Resources

**Configuration Files:**
- `.env` - Environment configuration
- `docker-compose.prod.yml` - Production deployment
- `deploy/` - Deployment configurations

**Scripts:**
- `scripts/backup.sh` - Backup automation
- `scripts/restore.sh` - Restore procedures
- `scripts/deployment-check.sh` - Health validation

**Logs:**
- `logs/consciousness.log` - Application logs
- `logs/security.log` - Security events
- System logs via `journalctl -u consciousness`

For additional help, check the troubleshooting section in INSTALLATION.md or create an issue on GitHub.
