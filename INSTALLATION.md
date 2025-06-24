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

#### 🚀 **ZERO CONFIGURATION START**

The system comes with working defaults! Just copy the file and start:

```bash
cp .env.example .env
# That's it! The system will run with sensible defaults
```

**What you get out of the box:**
- ✅ Working local API server at `http://localhost:8000`
- ✅ SQLite database (no setup required)
- ✅ Device discovery enabled
- ✅ Basic logging and monitoring
- ✅ Safe development defaults

#### 🤖 **ADD AI CONVERSATIONS** (Optional - for intelligent features)

To enable natural language conversations with your house:

```bash
# Edit .env and add your API keys:
OPENAI_API_KEY=sk-your-openai-key-here    # Get free at: https://platform.openai.com
ANTHROPIC_API_KEY=your-anthropic-key      # Get free at: https://console.anthropic.com
```

**What the secret keys are for:**
- `SECRET_KEY`: Encrypts your session data (login cookies, preferences)
- `JWT_SECRET_KEY`: Secures API authentication tokens
- `ENCRYPTION_KEY`: Protects sensitive device data in the database

*For development, the default keys work fine. Only change them for production deployment.*

#### ⚡ **BOOST PERFORMANCE** (Optional - but recommended)

Add Redis for much faster responses:

```bash
# Install Redis:
sudo apt install redis-server    # Ubuntu/Debian
# brew install redis             # macOS

# No configuration needed - the default Redis URL works
```

#### 🌐 **ADVANCED FEATURES** (All optional)

The `.env` file includes many optional features, each with clear explanations:

- **Weather integration**: Makes automations weather-aware
- **Energy monitoring**: Track and optimize power usage
- **HomeKit compatibility**: Apple ecosystem integration
- **System monitoring**: Health dashboards and alerting
- **AI behavior tuning**: Customize consciousness personality
- **Backup & notifications**: Protect data and get alerts

**Complete configuration reference:** See `.env.example` for all available options with detailed explanations.

### Super Quick Start

**🚀 Get running in 1 minute:**
```bash
# Clone and copy environment
git clone https://github.com/adrianco/consciousness.git
cd consciousness
cp .env.example .env

# Install and start (choose one method):
docker-compose up -d        # Docker (easiest)
# OR
uv sync && uv run uvicorn consciousness.main:app
# OR
pip install -e . && python -m consciousness.main
```

**🎯 That's it!** Open `http://localhost:8000` to see your consciousness system.

**🤖 Want AI conversations?** Just add API keys to `.env`:
```bash
OPENAI_API_KEY=sk-your-key-here      # Free at platform.openai.com
ANTHROPIC_API_KEY=your-key-here      # Free at console.anthropic.com
```

**⚡ Want it faster?** Install Redis:
```bash
sudo apt install redis-server    # Ubuntu
brew install redis              # macOS
```

### Production Deployment

For production use, generate secure keys:

```bash
# Generate production keys:
openssl rand -base64 32  # Copy to SECRET_KEY
openssl rand -base64 32  # Copy to JWT_SECRET_KEY
openssl rand -hex 16     # Copy to ENCRYPTION_KEY

# Update .env:
ENVIRONMENT=production
DEBUG=false
API_HOST=0.0.0.0  # Allow external access
```

### Getting API Keys

- **OpenAI**: https://platform.openai.com (GPT models)
- **Anthropic**: https://console.anthropic.com (Claude models)
- **Weather**: https://openweathermap.org/api (weather data)

### Prerequisites for Advanced Features

- **Bluetooth discovery**: `sudo apt install bluetooth bluez`
- **Zigbee devices**: Requires USB coordinator hardware
- **PostgreSQL**: Alternative to SQLite for larger deployments

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
