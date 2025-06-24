# Installation Guide

This guide will help you install and set up the House Consciousness System on your local machine or server.

## Platform-Specific Installation

Choose your platform for complete from-scratch setup:

### 🍎 **macOS Installation**

```bash
# 1. Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install Python and Git
brew install python@3.11 git

# 3. Install Redis for performance boost
brew install redis

# 4. Install Bluetooth support (for device discovery)
brew install bluez-tools  # For Bluetooth device scanning

# 5. Clone and setup consciousness
git clone https://github.com/adrianco/consciousness.git
cd consciousness
cp .env.example .env

# 6. Create and activate virtual environment (IMPORTANT!)
python3 -m venv consciousness-env
source consciousness-env/bin/activate

# 7. Install Python dependencies
pip install -e .

# 8. Start Redis service (in background)
brew services start redis

# 9. Start consciousness system
python -m consciousness.main
```

**macOS Alternative (if virtual environment issues):**
```bash
# Install dependencies directly with pip3
pip3 install -e .
pip3 install psutil uvicorn fastapi

# Then run with python3
python3 -m consciousness.main
```

### 🥧 **Raspberry Pi Installation**

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Python 3.11+ and dependencies
sudo apt install -y python3 python3-pip python3-venv git

# 3. Install Redis and Bluetooth support
sudo apt install -y redis-server bluetooth bluez libbluetooth-dev

# 4. Install system dependencies for device discovery
sudo apt install -y libffi-dev libssl-dev python3-dev

# 5. Enable Bluetooth service
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# 6. Add user to bluetooth group (logout/login after this)
sudo usermod -a -G bluetooth $USER

# 7. Clone and setup consciousness
git clone https://github.com/adrianco/consciousness.git
cd consciousness
cp .env.example .env

# 8. Create virtual environment
python3 -m venv consciousness-env
source consciousness-env/bin/activate

# 9. Install Python dependencies
pip install -e .

# 10. Start Redis service
sudo systemctl enable redis-server
sudo systemctl start redis-server

# 11. Start consciousness system
python -m consciousness.main
```

### 🪟 **Windows Installation**

```powershell
# 1. Install Python 3.11+ from https://python.org/downloads
# Make sure to check "Add Python to PATH" during installation

# 2. Install Git from https://git-scm.com/download/win

# 3. Install Redis (using Chocolatey - optional but recommended)
# First install Chocolatey: https://chocolatey.org/install
# Then in Admin PowerShell:
choco install redis-64

# 4. Clone and setup consciousness
git clone https://github.com/adrianco/consciousness.git
cd consciousness
copy .env.example .env

# 5. Create virtual environment (recommended)
python -m venv consciousness-env
consciousness-env\Scripts\activate

# 6. Install Python dependencies
pip install -e .

# 7. Start Redis (if installed) - in separate terminal
redis-server

# 8. Start consciousness system (in new PowerShell window)
python -m consciousness.main
```

**Windows Alternative (without Redis):**
```powershell
# Skip Redis installation - system will work but be slower
# Comment out REDIS_URL in .env file:
# REDIS_URL=redis://localhost:6379/0

# Just do steps 1, 2, 4, 5, 6, 8 above
```

### 🐧 **Linux (Ubuntu/Debian) Installation**

```bash
# 1. Install system dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git redis-server
sudo apt install -y bluetooth bluez libbluetooth-dev libffi-dev libssl-dev

# 2. Enable services
sudo systemctl enable redis-server bluetooth
sudo systemctl start redis-server bluetooth

# 3. Clone and setup consciousness
git clone https://github.com/adrianco/consciousness.git
cd consciousness
cp .env.example .env

# 4. Create virtual environment
python3 -m venv consciousness-env
source consciousness-env/bin/activate

# 5. Install Python dependencies
pip install -e .

# 6. Start consciousness system
python -m consciousness.main
```

### 🐳 **Docker Installation (if you prefer containers)**

```bash
# Install Docker and Docker Compose first:
# macOS: brew install docker docker-compose
# Windows: Download Docker Desktop from docker.com
# Linux: sudo apt install docker.io docker-compose

# Clone repository
git clone https://github.com/adrianco/consciousness.git
cd consciousness
cp .env.example .env

# Start with Docker Compose
docker-compose up -d

# Or start development environment
docker-compose -f docker-compose.dev.yml up -d
```

**🎯 Success!** Open `http://localhost:8000` to see your consciousness system.

### Quick Add-Ons After Installation

**🤖 Want AI conversations?** Add API keys to `.env`:
```bash
OPENAI_API_KEY=sk-your-key-here      # Free at platform.openai.com
ANTHROPIC_API_KEY=your-key-here      # Free at console.anthropic.com
```

**⚙️ Troubleshooting:**
- **Port 8000 in use?** Change `API_PORT=8001` in `.env`
- **Redis not working?** Comment out `REDIS_URL` line in `.env`
- **Bluetooth issues?** Run `sudo systemctl status bluetooth`
- **Permission errors?** Make sure you're in the virtual environment

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

### 🚨 **Quick Fix for Common Errors**

**Getting "ModuleNotFoundError: No module named 'psutil'"?**
```bash
# Quick fix - install missing dependencies:
pip install psutil uvicorn fastapi sqlalchemy aiosqlite redis

# Or create proper virtual environment:
python3 -m venv consciousness-env
source consciousness-env/bin/activate  # macOS/Linux
pip install -e .
```

### 🔧 **Advanced Troubleshooting**

**Missing Dependencies (psutil, uvicorn, etc.):**
```bash
# If you get "ModuleNotFoundError: No module named 'psutil'":
pip install psutil uvicorn fastapi sqlalchemy aiosqlite redis

# Or reinstall everything:
pip install -e . --force-reinstall
```

**Virtual Environment Issues:**
```bash
# Make sure you're in the virtual environment:
source consciousness-env/bin/activate  # Linux/macOS
# consciousness-env\Scripts\activate   # Windows

# Check if virtual environment is active (should show path):
which python
```

**Additional Common Issues:**
- **Port 8000 in use?** Change `API_PORT=8001` in `.env`
- **Redis not working?** Comment out `REDIS_URL` line in `.env`
- **Bluetooth issues?** Run `sudo systemctl status bluetooth` (Linux) or check System Preferences (macOS)
- **Permission errors?** Make sure you're in the virtual environment
- **Python version issues?** Ensure Python 3.11+ with `python --version`

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
