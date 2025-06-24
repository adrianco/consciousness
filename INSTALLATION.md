# Installation Guide

This guide will help you install and set up the House Consciousness System on your local machine or server.

## Prerequisites

- **Python 3.11+** (recommended)
- **Docker & Docker Compose** (for containerized deployment)
- **Git** (to clone the repository)
- **UV Package Manager** (optional, but recommended for faster installs)

## Installation Methods

### Method 1: Docker Compose (Recommended)

This is the easiest way to get the system running with all dependencies and services.

```bash
# Clone the repository
git clone https://github.com/adrianco/consciousness.git
cd consciousness

# Copy environment template
cp .env.example .env

# Edit .env file with your settings (see Configuration section below)
nano .env

# Start the system (production)
docker-compose -f docker-compose.prod.yml up -d

# Or start development environment
docker-compose -f docker-compose.dev.yml up -d
```

The system will be available at:
- **API**: http://localhost:8000
- **Web UI**: http://localhost:3000 (if enabled)
- **Grafana Monitoring**: http://localhost:3001
- **Prometheus Metrics**: http://localhost:9090

### Method 2: UV Package Manager (Fast)

UV is a fast Python package manager that handles dependencies efficiently.

```bash
# Clone the repository
git clone https://github.com/adrianco/consciousness.git
cd consciousness

# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and run
uv sync
uv run uvicorn consciousness.main:app --host 0.0.0.0 --port 8000

# Or run in development mode
uv run python -m consciousness.main --debug
```

### Method 3: Traditional Pip Installation

```bash
# Clone the repository
git clone https://github.com/adrianco/consciousness.git
cd consciousness

# Create virtual environment
python -m venv consciousness-env
source consciousness-env/bin/activate  # On Windows: consciousness-env\Scripts\activate

# Install the package in development mode
pip install -e .

# Run the application
python -m consciousness.main
```

### Method 4: System Service (Production)

For production deployment with automatic startup:

```bash
# Install using Method 2 or 3 first
# Then copy systemd service files
sudo cp deploy/systemd/consciousness.service /etc/systemd/system/
sudo cp deploy/systemd/consciousness-worker.service /etc/systemd/system/

# Enable and start services
sudo systemctl enable consciousness
sudo systemctl enable consciousness-worker
sudo systemctl start consciousness
sudo systemctl start consciousness-worker

# Check status
sudo systemctl status consciousness
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure variables based on your needs:

#### 🚀 **REQUIRED SETTINGS** (Must configure to get running)

```bash
# Basic application settings
ENVIRONMENT=production                    # development, staging, production
DEBUG=false                              # Set to true for development only
API_HOST=0.0.0.0                        # Host for API server
API_PORT=8000                            # Port for API server

# Database (works out of the box with SQLite)
DATABASE_URL=sqlite+aiosqlite:///./data/consciousness.db

# Security keys - GENERATE NEW KEYS!
SECRET_KEY=your-super-secret-key-here-change-this-in-production
JWT_SECRET_KEY=your-jwt-secret-key-here-change-this
ENCRYPTION_KEY=your-32-character-encryption-key-here

# Basic logging
LOG_LEVEL=INFO
LOG_FILE=logs/consciousness.log
```

#### 🏠 **DEVICE DISCOVERY** (Essential for smart home functionality)
*Impact: Without these, no device discovery or smart home integration*

```bash
ENABLE_BLUETOOTH=true                    # Smart sensors, fitness trackers, beacons
ENABLE_MDNS=true                        # Apple devices, Chromecast, smart speakers
ENABLE_UPNP=true                        # Media servers, smart TVs, routers
ENABLE_ZIGBEE=false                     # Zigbee devices (requires coordinator hardware)
```

#### 🤖 **AI SERVICES** (For intelligent conversations)
*Impact: Without API keys, no AI-powered conversations or intelligent responses*

```bash
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

#### ⚡ **REDIS CACHE** (Improves performance)
*Impact: Without Redis, no session management, slower responses, no real-time features*

```bash
REDIS_URL=redis://redis:6379/0          # Or redis://localhost:6379/0 for local setup
```

#### 🌐 **OPTIONAL INTEGRATIONS** (Enhanced functionality)
*Impact: Enables weather-aware automations, energy optimization, HomeKit compatibility*

```bash
# Weather integration
WEATHER_API_KEY=your-weather-api-key-here

# Energy monitoring
ENERGY_PROVIDER_API_KEY=your-energy-api-key-here

# HomeKit integration
HOMEKIT_PIN=123-45-678                  # Format: XXX-XX-XXX
```

#### 📊 **MONITORING** (System health tracking)
*Impact: Without monitoring, no performance metrics or health alerting*

```bash
ENABLE_PROMETHEUS=true
PROMETHEUS_PORT=9090
GRAFANA_PASSWORD=your-grafana-admin-password
```

#### 🧠 **CONSCIOUSNESS TUNING** (AI behavior customization)
*Impact: Controls how the consciousness learns, responds, and evolves*

```bash
EMOTION_UPDATE_INTERVAL=300             # Emotional state update frequency (seconds)
MEMORY_RETENTION_DAYS=365              # Memory retention period (days)
LEARNING_RATE=0.01                     # Adaptive learning rate (0.0-1.0)
PREDICTION_HORIZON_HOURS=24            # Scenario prediction timeframe (hours)
```

**Complete configuration:** See `.env.example` for all settings including security, backup, and notifications.

### Quick Setup Guide

**🚀 Minimal Setup (5 minutes to get running)**
```bash
cp .env.example .env
nano .env  # Edit these required settings:

# Change security keys (REQUIRED):
SECRET_KEY=generate-a-secure-random-32-character-key
JWT_SECRET_KEY=generate-another-secure-random-key
ENCRYPTION_KEY=exactly-32-character-encryption-key

# Set environment:
ENVIRONMENT=development  # or production
DEBUG=true              # false for production
```

**🏠 Smart Home Setup (add device discovery)**
```bash
# Enable discovery protocols for your devices:
ENABLE_BLUETOOTH=true   # Smart sensors, fitness trackers
ENABLE_MDNS=true       # Apple devices, Chromecast
ENABLE_UPNP=true       # Smart TVs, media servers
ENABLE_ZIGBEE=false    # Only if you have Zigbee coordinator
```

**🤖 AI-Powered Setup (add intelligent features)**
```bash
# Add AI service API keys:
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
```

**⚡ Performance Setup (add Redis for speed)**
```bash
# Install Redis and configure:
REDIS_URL=redis://localhost:6379/0
```

**🔧 Full Setup (complete configuration)**

**Essential Setup Requirements:**
```bash
# 1. Generate secure keys for production:
openssl rand -base64 32  # For SECRET_KEY
openssl rand -base64 32  # For JWT_SECRET_KEY
openssl rand -hex 16     # For ENCRYPTION_KEY (32 chars)

# 2. Database options:
# SQLite (default): No setup required
# PostgreSQL: postgresql+asyncpg://user:password@localhost/consciousness

# 3. Device discovery prerequisites:
sudo apt install bluetooth bluez  # For Bluetooth discovery
# mDNS/UPnP: Work automatically on most networks
# Zigbee: Requires coordinator hardware (USB stick)
```

**Service Setup Links:**
- **OpenAI API**: https://platform.openai.com (for GPT models)
- **Anthropic API**: https://console.anthropic.com (for Claude models)
- **Weather API**: OpenWeatherMap, WeatherAPI, or similar service
- **Energy Provider**: Check if your utility offers API access

### Network Configuration

If deploying behind a reverse proxy, use the provided nginx configurations:

```bash
# Development
sudo cp deploy/nginx/dev.conf /etc/nginx/sites-available/consciousness-dev
sudo ln -s /etc/nginx/sites-available/consciousness-dev /etc/nginx/sites-enabled/

# Production
sudo cp deploy/nginx/prod.conf /etc/nginx/sites-available/consciousness
sudo ln -s /etc/nginx/sites-available/consciousness /etc/nginx/sites-enabled/
```

## Verification

### Health Check

```bash
# Check if the API is running
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "version": "1.0.0", "timestamp": "..."}
```

### Run Tests

```bash
# Run the test suite
pytest tests/

# Run specific test categories
pytest tests/unit/           # Unit tests
pytest tests/integration/    # Integration tests
pytest tests/security/       # Security tests

# Run simulation tests
python test_safla_simple.py
python test_device_interview_flow.py
```

### Monitoring Setup

If you enabled monitoring, check these endpoints:

- **Grafana Dashboard**: http://localhost:3001 (admin/admin)
- **Prometheus Metrics**: http://localhost:9090
- **System Health**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs

## Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Check what's using port 8000
sudo lsof -i :8000
# Kill the process if needed
sudo kill -9 <PID>
```

**Permission Errors**
```bash
# Ensure correct permissions
sudo chown -R $USER:$USER /path/to/consciousness
chmod +x scripts/*.sh
```

**Database Issues**
```bash
# Reset database
rm consciousness.db
python -m consciousness.main  # Will recreate database
```

**Docker Issues**
```bash
# Clean up Docker
docker-compose down -v
docker system prune -f
docker-compose -f docker-compose.prod.yml up -d --force-recreate
```

### Getting Help

1. **Check Logs**:
   ```bash
   # Application logs
   tail -f logs/consciousness.log

   # Docker logs
   docker-compose logs -f consciousness

   # System service logs
   sudo journalctl -u consciousness -f
   ```

2. **Debug Mode**:
   ```bash
   # Run in debug mode for detailed output
   DEBUG=true python -m consciousness.main
   ```

3. **Health Diagnostics**:
   ```bash
   # Run deployment check script
   ./scripts/deployment-check.sh
   ```

## Security Considerations

- Change default passwords and secret keys
- Use HTTPS in production (configure SSL certificates)
- Enable firewall rules for appropriate ports only
- Regularly update dependencies: `uv sync --upgrade`
- Monitor security logs: `tail -f logs/security.log`

## Backup and Recovery

```bash
# Create backup
./scripts/backup.sh

# Restore from backup
./scripts/restore.sh /path/to/backup/file

# Automated backups (add to crontab)
0 2 * * * /path/to/consciousness/scripts/backup.sh
```

## Next Steps

After successful installation, see [USER.md](USER.md) for guidance on how to use the system.

For advanced deployment scenarios, see `deploy/README.md`.
