# Deployment and Operations Guide

## Overview
This guide provides comprehensive deployment strategies, operational procedures, and maintenance workflows for the House Consciousness System in production environments.

## Deployment Architecture

### Production Environment Components
```
┌──────────────────────────────────────────────────────────────┐
│                    Production Architecture                     │
├──────────────────────────────────────────────────────────────┤
│  Load Balancer (nginx/HAProxy)                               │
│  ├── Web Interface (React/Next.js)                           │
│  ├── API Gateway (FastAPI)                                   │
│  └── WebSocket Server (FastAPI WebSocket)                    │
├──────────────────────────────────────────────────────────────┤
│  Application Layer                                            │
│  ├── Consciousness Engine                                     │
│  ├── SAFLA Loop Processors                                   │
│  ├── Device Adapters                                         │
│  └── Background Workers (Celery)                             │
├──────────────────────────────────────────────────────────────┤
│  Data Layer                                                   │
│  ├── SQLite Database (Primary)                               │
│  ├── Redis (Cache/Sessions)                                  │
│  └── File Storage (Logs/Backups)                            │
├──────────────────────────────────────────────────────────────┤
│  Infrastructure                                               │
│  ├── Docker Containers                                       │
│  ├── systemd Services                                        │
│  └── Monitoring (Prometheus/Grafana)                         │
└──────────────────────────────────────────────────────────────┘
```

## Phase 1: Container Setup

### 1.1 Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Set work directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash consciousness && \
    chown -R consciousness:consciousness /app
USER consciousness

# Expose ports
EXPOSE 8000 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uv", "run", "uvicorn", "consciousness.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Multi-stage build for production
FROM base as production

# Set production environment
ENV ENVIRONMENT=production \
    DEBUG=false

# Install production dependencies only
RUN uv sync --frozen --no-dev

# Copy only necessary files
COPY --from=base /app /app

CMD ["uv", "run", "uvicorn", "consciousness.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 1.2 Docker Compose for Local Development

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  consciousness:
    build:
      context: .
      target: base
    ports:
      - "8000:8000"
      - "8001:8001"
    environment:
      - ENVIRONMENT=development
      - DEBUG=true
      - DATABASE_URL=sqlite:///./data/consciousness_dev.db
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - .:/app
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - redis
    restart: unless-stopped
    command: ["uv", "run", "uvicorn", "consciousness.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  celery:
    build:
      context: .
      target: base
    environment:
      - ENVIRONMENT=development
      - DATABASE_URL=sqlite:///./data/consciousness_dev.db
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - .:/app
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - redis
    restart: unless-stopped
    command: ["uv", "run", "celery", "worker", "-A", "consciousness.tasks", "--loglevel=info"]

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deploy/nginx/dev.conf:/etc/nginx/conf.d/default.conf
      - ./static:/var/www/static
    depends_on:
      - consciousness
    restart: unless-stopped

volumes:
  redis_data:
```

### 1.3 Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  consciousness:
    build:
      context: .
      target: production
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - DATABASE_URL=sqlite:///./data/consciousness.db
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - API_KEY_OPENAI=${API_KEY_OPENAI}
      - API_KEY_ANTHROPIC=${API_KEY_ANTHROPIC}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
    depends_on:
      - redis
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
      - ./deploy/redis/redis.conf:/usr/local/etc/redis/redis.conf
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.25'
    command: ["redis-server", "/usr/local/etc/redis/redis.conf"]

  celery:
    build:
      context: .
      target: production
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=sqlite:///./data/consciousness.db
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
    depends_on:
      - redis
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
          cpus: '0.25'
    command: ["uv", "run", "celery", "worker", "-A", "consciousness.tasks", "--loglevel=info", "--concurrency=2"]

  celery-beat:
    build:
      context: .
      target: production
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=sqlite:///./data/consciousness.db
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
    depends_on:
      - redis
    restart: unless-stopped
    command: ["uv", "run", "celery", "beat", "-A", "consciousness.tasks", "--loglevel=info"]

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deploy/nginx/prod.conf:/etc/nginx/conf.d/default.conf
      - ./deploy/ssl:/etc/ssl/certs
      - ./static:/var/www/static
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - consciousness
    restart: unless-stopped

  monitoring:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./deploy/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./deploy/monitoring/grafana:/etc/grafana/provisioning
    restart: unless-stopped

volumes:
  redis_data:
  prometheus_data:
  grafana_data:
```

## Phase 2: System Configuration

### 2.1 Nginx Configuration

```nginx
# deploy/nginx/prod.conf
upstream consciousness_backend {
    least_conn;
    server consciousness:8000 max_fails=3 fail_timeout=30s;
}

upstream consciousness_ws {
    server consciousness:8001;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=ws:10m rate=5r/s;

server {
    listen 80;
    server_name consciousness.local;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name consciousness.local;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/consciousness.crt;
    ssl_certificate_key /etc/ssl/certs/consciousness.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Client body size
    client_max_body_size 10M;

    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;

    # Static files
    location /static/ {
        alias /var/www/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # API endpoints
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://consciousness_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket connections
    location /ws {
        limit_req zone=ws burst=10 nodelay;
        proxy_pass http://consciousness_ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # Main application
    location / {
        proxy_pass http://consciousness_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        proxy_pass http://consciousness_backend/health;
        access_log off;
    }
}
```

### 2.2 Systemd Service Configuration

```ini
# /etc/systemd/system/consciousness.service
[Unit]
Description=House Consciousness System
After=network.target
Requires=redis.service

[Service]
Type=exec
User=consciousness
Group=consciousness
WorkingDirectory=/opt/consciousness
Environment=ENVIRONMENT=production
Environment=DATABASE_URL=sqlite:///./data/consciousness.db
Environment=REDIS_URL=redis://localhost:6379/0
EnvironmentFile=/opt/consciousness/.env
ExecStart=/opt/consciousness/.venv/bin/uvicorn consciousness.main:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StartLimitInterval=60
StartLimitBurst=3

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/consciousness/data /opt/consciousness/logs
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE

# Resource limits
MemoryMax=1G
CPUQuota=50%

[Install]
WantedBy=multi-user.target
```

### 2.3 Celery Worker Service

```ini
# /etc/systemd/system/consciousness-worker.service
[Unit]
Description=Consciousness Celery Worker
After=network.target redis.service
Requires=redis.service

[Service]
Type=exec
User=consciousness
Group=consciousness
WorkingDirectory=/opt/consciousness
EnvironmentFile=/opt/consciousness/.env
ExecStart=/opt/consciousness/.venv/bin/celery worker -A consciousness.tasks --loglevel=info --concurrency=2
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10

# Resource limits
MemoryMax=512M
CPUQuota=25%

[Install]
WantedBy=multi-user.target
```

## Phase 3: Monitoring and Observability

### 3.1 Application Health Checks

```python
# consciousness/health.py
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from .database import get_async_session
from .models.consciousness import ConsciousnessSession
from .models.entities import Device

class HealthChecker:
    """Comprehensive health checking for the consciousness system."""
    
    def __init__(self):
        self.checks = {
            'database': self._check_database,
            'consciousness_engine': self._check_consciousness_engine,
            'devices': self._check_devices,
            'memory': self._check_memory_usage,
            'disk_space': self._check_disk_space,
            'redis': self._check_redis
        }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {},
            'overall': True
        }
        
        for check_name, check_func in self.checks.items():
            try:
                result = await check_func()
                health_status['checks'][check_name] = result
                if not result['healthy']:
                    health_status['overall'] = False
                    if result.get('critical', False):
                        health_status['status'] = 'critical'
                    elif health_status['status'] != 'critical':
                        health_status['status'] = 'degraded'
            except Exception as e:
                health_status['checks'][check_name] = {
                    'healthy': False,
                    'error': str(e),
                    'critical': True
                }
                health_status['overall'] = False
                health_status['status'] = 'critical'
        
        return health_status
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            async with get_async_session() as session:
                # Test basic connectivity
                start_time = datetime.utcnow()
                await session.execute(text("SELECT 1"))
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Check recent activity
                recent_sessions = await session.execute(
                    select(func.count(ConsciousnessSession.id))
                    .where(ConsciousnessSession.created_at >= datetime.utcnow() - timedelta(hours=1))
                )
                session_count = recent_sessions.scalar()
                
                return {
                    'healthy': response_time < 1.0,
                    'response_time_ms': response_time * 1000,
                    'recent_sessions': session_count,
                    'critical': response_time > 5.0
                }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'critical': True
            }
    
    async def _check_consciousness_engine(self) -> Dict[str, Any]:
        """Check consciousness engine status."""
        try:
            async with get_async_session() as session:
                # Check for active sessions
                active_sessions = await session.execute(
                    select(ConsciousnessSession)
                    .where(ConsciousnessSession.status == 'active')
                    .order_by(ConsciousnessSession.created_at.desc())
                    .limit(1)
                )
                latest_session = active_sessions.scalar_one_or_none()
                
                if not latest_session:
                    return {
                        'healthy': False,
                        'error': 'No active consciousness sessions found',
                        'critical': True
                    }
                
                # Check session age
                session_age = datetime.utcnow() - latest_session.created_at
                session_age_minutes = session_age.total_seconds() / 60
                
                return {
                    'healthy': session_age_minutes < 10,  # Session should be recent
                    'active_session': latest_session.session_id,
                    'session_age_minutes': session_age_minutes,
                    'events_processed': latest_session.events_processed,
                    'critical': session_age_minutes > 30
                }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'critical': True
            }
    
    async def _check_devices(self) -> Dict[str, Any]:
        """Check device connectivity status."""
        try:
            async with get_async_session() as session:
                device_stats = await session.execute(
                    select(
                        func.count(Device.id).label('total'),
                        func.sum(func.case([(Device.status == 'online', 1)], else_=0)).label('online'),
                        func.sum(func.case([(Device.status == 'error', 1)], else_=0)).label('error')
                    )
                )
                stats = device_stats.first()
                
                if not stats or stats.total == 0:
                    return {
                        'healthy': True,  # No devices is not critical
                        'total_devices': 0,
                        'online_devices': 0,
                        'error_devices': 0,
                        'online_percentage': 0
                    }
                
                online_pct = (stats.online / stats.total) * 100
                error_pct = (stats.error / stats.total) * 100
                
                return {
                    'healthy': online_pct >= 80 and error_pct < 20,
                    'total_devices': stats.total,
                    'online_devices': stats.online,
                    'error_devices': stats.error,
                    'online_percentage': online_pct,
                    'critical': online_pct < 50 or error_pct > 50
                }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'critical': False
            }
    
    async def _check_memory_usage(self) -> Dict[str, Any]:
        """Check system memory usage."""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            memory_pct = memory.percent
            
            return {
                'healthy': memory_pct < 80,
                'memory_usage_percent': memory_pct,
                'available_gb': memory.available / (1024**3),
                'total_gb': memory.total / (1024**3),
                'critical': memory_pct > 95
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'critical': False
            }
    
    async def _check_disk_space(self) -> Dict[str, Any]:
        """Check disk space usage."""
        try:
            import shutil
            
            # Check data directory space
            total, used, free = shutil.disk_usage('/app/data')
            
            total_gb = total / (1024**3)
            used_gb = used / (1024**3)
            free_gb = free / (1024**3)
            used_pct = (used / total) * 100
            
            return {
                'healthy': used_pct < 80 and free_gb > 1,
                'disk_usage_percent': used_pct,
                'free_gb': free_gb,
                'total_gb': total_gb,
                'critical': used_pct > 95 or free_gb < 0.5
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'critical': False
            }
    
    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance."""
        try:
            import redis.asyncio as redis
            from ..config import settings
            
            redis_client = redis.from_url(settings.REDIS_URL)
            
            # Test connectivity
            start_time = datetime.utcnow()
            await redis_client.ping()
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Get Redis info
            info = await redis_client.info()
            memory_usage = info.get('used_memory', 0)
            memory_usage_mb = memory_usage / (1024**2)
            
            await redis_client.close()
            
            return {
                'healthy': response_time < 0.1,
                'response_time_ms': response_time * 1000,
                'memory_usage_mb': memory_usage_mb,
                'connected_clients': info.get('connected_clients', 0),
                'critical': response_time > 1.0
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'critical': True
            }

# Add to FastAPI app
from fastapi import FastAPI

app = FastAPI()
health_checker = HealthChecker()

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with all components."""
    return await health_checker.get_health_status()
```

### 3.2 Prometheus Metrics

```python
# consciousness/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps

# Application metrics
consciousness_requests_total = Counter(
    'consciousness_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

consciousness_request_duration = Histogram(
    'consciousness_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

consciousness_active_sessions = Gauge(
    'consciousness_active_sessions',
    'Number of active consciousness sessions'
)

consciousness_device_status = Gauge(
    'consciousness_device_status',
    'Device status by type',
    ['device_type', 'status']
)

consciousness_emotional_state = Gauge(
    'consciousness_emotional_state',
    'Current emotional state values',
    ['emotion']
)

consciousness_memory_usage = Gauge(
    'consciousness_memory_usage_bytes',
    'Memory usage by component',
    ['component']
)

consciousness_processing_rate = Gauge(
    'consciousness_processing_rate',
    'Events processing rate per second'
)

# Decorators for automatic metrics
def track_requests(func):
    """Decorator to track request metrics."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            consciousness_requests_total.labels(
                method='GET', endpoint=func.__name__, status='success'
            ).inc()
            return result
        except Exception as e:
            consciousness_requests_total.labels(
                method='GET', endpoint=func.__name__, status='error'
            ).inc()
            raise
        finally:
            consciousness_request_duration.labels(
                method='GET', endpoint=func.__name__
            ).observe(time.time() - start_time)
    return wrapper

def track_processing_time(component: str):
    """Decorator to track processing time for components."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                processing_time = time.time() - start_time
                consciousness_request_duration.labels(
                    method='PROCESS', endpoint=component
                ).observe(processing_time)
                return result
            except Exception:
                raise
        return wrapper
    return decorator
```

## Phase 4: Backup and Recovery

### 4.1 Backup Strategy

```bash
#!/bin/bash
# scripts/backup.sh

set -e

BACKUP_DIR="/opt/consciousness/backups"
DATA_DIR="/opt/consciousness/data"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="consciousness_backup_${TIMESTAMP}"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Create backup archive
echo "Creating backup: ${BACKUP_NAME}"

tar -czf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" \
    -C "${DATA_DIR}" \
    --exclude="*.tmp" \
    --exclude="*.log" \
    .

# Backup database separately
cp "${DATA_DIR}/consciousness.db" "${BACKUP_DIR}/consciousness_${TIMESTAMP}.db"

# Compress logs
tar -czf "${BACKUP_DIR}/logs_${TIMESTAMP}.tar.gz" \
    -C "/opt/consciousness/logs" \
    .

# Clean old backups (keep last 30 days)
find "${BACKUP_DIR}" -name "consciousness_backup_*.tar.gz" -mtime +30 -delete
find "${BACKUP_DIR}" -name "consciousness_*.db" -mtime +30 -delete
find "${BACKUP_DIR}" -name "logs_*.tar.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_NAME}.tar.gz"

# Upload to cloud storage (optional)
if [ ! -z "${BACKUP_S3_BUCKET}" ]; then
    aws s3 cp "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" "s3://${BACKUP_S3_BUCKET}/consciousness-backups/"
    echo "Backup uploaded to S3"
fi
```

### 4.2 Recovery Procedures

```bash
#!/bin/bash
# scripts/restore.sh

set -e

if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

BACKUP_FILE="$1"
DATA_DIR="/opt/consciousness/data"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Stop services
echo "Stopping consciousness services..."
sudo systemctl stop consciousness consciousness-worker

# Backup current data
echo "Backing up current data..."
mv "${DATA_DIR}" "${DATA_DIR}_backup_${TIMESTAMP}"

# Create new data directory
mkdir -p "${DATA_DIR}"

# Restore from backup
echo "Restoring from backup: ${BACKUP_FILE}"
tar -xzf "${BACKUP_FILE}" -C "${DATA_DIR}"

# Set permissions
chown -R consciousness:consciousness "${DATA_DIR}"
chmod -R 755 "${DATA_DIR}"

# Restart services
echo "Starting consciousness services..."
sudo systemctl start consciousness consciousness-worker

# Verify restoration
echo "Verifying restoration..."
sleep 10
curl -f http://localhost:8000/health || {
    echo "Health check failed, rolling back..."
    sudo systemctl stop consciousness consciousness-worker
    rm -rf "${DATA_DIR}"
    mv "${DATA_DIR}_backup_${TIMESTAMP}" "${DATA_DIR}"
    sudo systemctl start consciousness consciousness-worker
    exit 1
}

echo "Restoration completed successfully"
echo "Previous data backed up to: ${DATA_DIR}_backup_${TIMESTAMP}"
```

## Phase 5: Deployment Automation

### 5.1 CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install UV
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
        
      - name: Install dependencies
        run: uv sync
        
      - name: Run tests
        run: uv run pytest --cov=consciousness --cov-report=xml
        
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
        
      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
          
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          target: production
          push: true
          tags: |
            ghcr.io/${{ github.repository }}:latest
            ghcr.io/${{ github.repository }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to production
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.PROD_HOST }}
          username: ${{ secrets.PROD_USER }}
          key: ${{ secrets.PROD_SSH_KEY }}
          script: |
            cd /opt/consciousness
            
            # Pull latest images
            docker-compose -f docker-compose.prod.yml pull
            
            # Create backup
            ./scripts/backup.sh
            
            # Deploy with zero downtime
            docker-compose -f docker-compose.prod.yml up -d --remove-orphans
            
            # Health check
            sleep 30
            curl -f http://localhost/health || exit 1
            
            # Clean up old images
            docker image prune -f
```

### 5.2 Infrastructure as Code

```yaml
# deploy/ansible/consciousness.yml
---
- name: Deploy Consciousness System
  hosts: consciousness_servers
  become: yes
  vars:
    consciousness_user: consciousness
    consciousness_home: /opt/consciousness
    consciousness_version: "{{ lookup('env', 'CONSCIOUSNESS_VERSION') | default('latest') }}"

  tasks:
    - name: Create consciousness user
      user:
        name: "{{ consciousness_user }}"
        home: "{{ consciousness_home }}"
        shell: /bin/bash
        system: yes

    - name: Install system dependencies
      apt:
        name:
          - docker.io
          - docker-compose
          - nginx
          - redis
          - sqlite3
          - curl
          - git
        state: present
        update_cache: yes

    - name: Create application directories
      file:
        path: "{{ item }}"
        state: directory
        owner: "{{ consciousness_user }}"
        group: "{{ consciousness_user }}"
        mode: '0755'
      loop:
        - "{{ consciousness_home }}"
        - "{{ consciousness_home }}/data"
        - "{{ consciousness_home }}/logs"
        - "{{ consciousness_home }}/backups"
        - "{{ consciousness_home }}/config"

    - name: Copy application files
      copy:
        src: "{{ item.src }}"
        dest: "{{ consciousness_home }}/{{ item.dest }}"
        owner: "{{ consciousness_user }}"
        group: "{{ consciousness_user }}"
        mode: "{{ item.mode | default('0644') }}"
      loop:
        - { src: docker-compose.prod.yml, dest: docker-compose.yml }
        - { src: scripts/, dest: scripts/, mode: '0755' }
        - { src: deploy/nginx/prod.conf, dest: nginx.conf }

    - name: Copy environment file
      template:
        src: env.j2
        dest: "{{ consciousness_home }}/.env"
        owner: "{{ consciousness_user }}"
        group: "{{ consciousness_user }}"
        mode: '0600'

    - name: Setup systemd services
      template:
        src: "{{ item }}.service.j2"
        dest: "/etc/systemd/system/{{ item }}.service"
        mode: '0644'
      loop:
        - consciousness
        - consciousness-worker
      notify: reload systemd

    - name: Enable and start services
      systemd:
        name: "{{ item }}"
        enabled: yes
        state: started
        daemon_reload: yes
      loop:
        - consciousness
        - consciousness-worker

    - name: Setup backup cron job
      cron:
        name: "Consciousness backup"
        minute: "0"
        hour: "2"
        job: "{{ consciousness_home }}/scripts/backup.sh"
        user: "{{ consciousness_user }}"

    - name: Configure nginx
      template:
        src: nginx.conf.j2
        dest: /etc/nginx/sites-available/consciousness
        backup: yes
      notify: restart nginx

    - name: Enable nginx site
      file:
        src: /etc/nginx/sites-available/consciousness
        dest: /etc/nginx/sites-enabled/consciousness
        state: link
      notify: restart nginx

  handlers:
    - name: reload systemd
      systemd:
        daemon_reload: yes

    - name: restart nginx
      systemd:
        name: nginx
        state: restarted
```

## Phase 6: Security Hardening

### 6.1 Security Configuration

```python
# consciousness/security/config.py
from pydantic_settings import BaseSettings
from typing import List, Optional

class SecuritySettings(BaseSettings):
    """Security configuration settings."""
    
    # Authentication
    SECRET_KEY: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    
    # API Security
    API_RATE_LIMIT: str = "100/hour"
    MAX_REQUEST_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE"]
    
    # SSL/TLS
    SSL_CERT_PATH: Optional[str] = None
    SSL_KEY_PATH: Optional[str] = None
    FORCE_HTTPS: bool = True
    
    # Database Security
    DATABASE_ENCRYPTION_KEY: Optional[str] = None
    
    # Device Security
    DEVICE_AUTH_TIMEOUT: int = 300  # 5 minutes
    MAX_FAILED_AUTH_ATTEMPTS: int = 5
    
    # Logging Security
    LOG_SENSITIVE_DATA: bool = False
    AUDIT_LOG_RETENTION_DAYS: int = 90
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Security middleware
from fastapi import FastAPI, Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import hashlib
import hmac

security = HTTPBearer()
limiter = Limiter(key_func=get_remote_address)

class SecurityMiddleware:
    """Enhanced security middleware."""
    
    def __init__(self, app: FastAPI, settings: SecuritySettings):
        self.app = app
        self.settings = settings
        self.failed_attempts = {}
        
        # Add rate limiting
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    async def __call__(self, request: Request, call_next):
        # Security headers
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        if self.settings.FORCE_HTTPS:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
    
    def verify_request_signature(self, request: Request, signature: str, secret: str) -> bool:
        """Verify request signature for device authentication."""
        body = request.body()
        expected_signature = hmac.new(
            secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
```

### 6.2 Audit Logging

```python
# consciousness/security/audit.py
import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from ..models.base import BaseModel

class AuditLog(BaseModel):
    """Audit log model for security events."""
    __tablename__ = "audit_logs"
    
    event_type = Column(String(100), nullable=False)
    user_id = Column(String(255))
    session_id = Column(String(255))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    resource = Column(String(255))
    action = Column(String(100))
    outcome = Column(String(50))  # success, failure, error
    details = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

class AuditLogger:
    """Centralized audit logging system."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def log_authentication(
        self,
        user_id: str,
        outcome: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log authentication events."""
        await self._log_event(
            event_type="authentication",
            user_id=user_id,
            action="login",
            outcome=outcome,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def log_device_access(
        self,
        device_id: str,
        action: str,
        outcome: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log device access events."""
        await self._log_event(
            event_type="device_access",
            user_id=user_id,
            resource=f"device:{device_id}",
            action=action,
            outcome=outcome,
            details=details or {}
        )
    
    async def log_data_access(
        self,
        resource: str,
        action: str,
        outcome: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log data access events."""
        await self._log_event(
            event_type="data_access",
            user_id=user_id,
            resource=resource,
            action=action,
            outcome=outcome,
            details=details or {}
        )
    
    async def log_security_event(
        self,
        event_type: str,
        outcome: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """Log security-related events."""
        await self._log_event(
            event_type=f"security:{event_type}",
            user_id=user_id,
            action=event_type,
            outcome=outcome,
            details=details,
            ip_address=ip_address
        )
    
    async def _log_event(
        self,
        event_type: str,
        action: str,
        outcome: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Internal method to log audit events."""
        audit_entry = AuditLog(
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource=resource,
            action=action,
            outcome=outcome,
            details=details or {}
        )
        
        self.session.add(audit_entry)
        await self.session.commit()
```

## Maintenance and Operations

### Daily Operations Checklist
1. ✅ Check system health status
2. ✅ Review consciousness engine metrics
3. ✅ Monitor device connectivity
4. ✅ Check disk space and memory usage
5. ✅ Review security audit logs
6. ✅ Verify backup completion

### Weekly Operations
1. 🔄 Review performance metrics
2. 🔄 Update device firmware (if available)
3. 🔄 Analyze consciousness learning progress
4. 🔄 Review and rotate logs
5. 🔄 Test backup restoration process

### Monthly Operations
1. 📅 Security patch updates
2. 📅 Dependency updates
3. 📅 Performance optimization review
4. 📅 Capacity planning assessment
5. 📅 Disaster recovery testing

This comprehensive deployment guide ensures the House Consciousness System runs reliably in production with proper monitoring, security, and operational procedures.