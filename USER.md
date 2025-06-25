# User Guide

Welcome to the House Consciousness System! This guide will help you understand and interact with your conscious house.

## Overview

The House Consciousness System creates an AI-powered awareness layer for your home that can:
- **Discover and understand** your IoT devices
- **Learn patterns** and preferences over time
- **Simulate scenarios** and predict outcomes
- **Communicate** about what it's sensing and feeling
- **Coordinate devices** for optimal comfort and efficiency

## Getting Started

### 1. First Launch

After installation, the system will automatically begin discovering devices in your home:

```bash
# Check system status
curl http://localhost:8000/health

# View discovered devices
curl http://localhost:8000/api/devices/discovered
```

### 2. Web Interface

Open your browser to `http://localhost:8000` for the web interface, or `http://localhost:8000/docs` for the interactive API documentation.

## Core Features

### Device Discovery & Interview

The system automatically discovers IoT devices using multiple protocols:

**Discovery Methods:**
- **Bluetooth LE**: Smart sensors, fitness trackers, beacons
- **mDNS/Bonjour**: Apple devices, Chromecast, smart speakers
- **UPnP**: Media servers, routers, smart TVs
- **DHCP**: All network-connected devices
- **Zigbee**: Smart home hubs and sensors (if enabled)

**Device Interview Process:**
```bash
# Start device interview for a specific device
curl -X POST http://localhost:8000/api/interview/start \
  -H "Content-Type: application/json" \
  -d '{"device_id": "device-mac-address"}'

# Check interview progress
curl http://localhost:8000/api/interview/status/device-mac-address

# Get integration recommendations
curl http://localhost:8000/api/interview/recommendations/device-mac-address
```

### Talking to Your House

The consciousness system can engage in natural conversations about your home:

**Example Conversations:**

```python
# Using the API
import requests

# Ask about current status
response = requests.post("http://localhost:8000/api/chat",
    json={"message": "How is the house feeling today?"})
print(response.json()["response"])

# Ask about specific concerns
response = requests.post("http://localhost:8000/api/chat",
    json={"message": "Is there anything I should be worried about?"})

# Set context or preferences
response = requests.post("http://localhost:8000/api/chat",
    json={"message": "We're going on vacation for a week starting tomorrow"})
```

**Sample Questions You Can Ask:**
- "What devices did you discover today?"
- "Are there any security concerns?"
- "Why did the temperature change in the living room?"
- "What's using the most energy right now?"
- "Should I be worried about anything before I leave for work?"
- "Can you put the house in party mode for tonight?"

### Digital Twin Management

The system creates digital twins of your devices for simulation and testing:

```bash
# Create a digital twin
curl -X POST http://localhost:8000/api/digital-twin/create \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "smart-thermostat-01",
    "device_type": "thermostat",
    "properties": {
      "min_temp": 60,
      "max_temp": 85,
      "current_temp": 72
    }
  }'

# Update twin state
curl -X PUT http://localhost:8000/api/digital-twin/smart-thermostat-01/state \
  -H "Content-Type: application/json" \
  -d '{"temperature": 74, "mode": "cooling"}'

# Get twin status
curl http://localhost:8000/api/digital-twin/smart-thermostat-01
```

### Simulation Scenarios

Run pre-built scenarios to test how your house responds to different situations:

**Available Scenarios:**

1. **Smart Morning Routine**
   ```bash
   curl -X POST http://localhost:8000/api/scenarios/smart-morning-routine/run
   ```

2. **Security Alert**
   ```bash
   curl -X POST http://localhost:8000/api/scenarios/security-alert/run \
     -d '{"trigger": "motion_detected", "location": "back_door"}'
   ```

3. **Energy Optimization**
   ```bash
   curl -X POST http://localhost:8000/api/scenarios/energy-optimization/run
   ```

4. **Party Mode**
   ```bash
   curl -X POST http://localhost:8000/api/scenarios/party-mode/run \
     -d '{"guest_count": 12, "music_preference": "upbeat"}'
   ```

5. **Vacation Mode**
   ```bash
   curl -X POST http://localhost:8000/api/scenarios/vacation-mode/run \
     -d '{"duration_days": 7, "simulate_presence": true}'
   ```

### Learning and Memory

The consciousness system learns from your patterns and preferences:

**Memory Operations:**
```bash
# Store a preference
curl -X POST http://localhost:8000/api/memory/store \
  -H "Content-Type: application/json" \
  -d '{
    "key": "user_preferences.temperature",
    "value": {"morning": 68, "evening": 72, "night": 65}
  }'

# Retrieve memories
curl http://localhost:8000/api/memory/get/user_preferences.temperature

# Query patterns
curl http://localhost:8000/api/memory/patterns?category=energy_usage
```

**Learning Insights:**
```bash
# Get insights about your home
curl http://localhost:8000/api/insights/energy
curl http://localhost:8000/api/insights/security
curl http://localhost:8000/api/insights/comfort
```

## Advanced Usage

### Custom Scenarios

Create your own scenarios for testing specific situations:

```python
# Create custom scenario
scenario = {
    "name": "Weekend Morning",
    "description": "Simulate lazy weekend morning routine",
    "steps": [
        {
            "action": "set_temperature",
            "device": "main_thermostat",
            "value": 74,
            "delay": 0
        },
        {
            "action": "open_blinds",
            "device": "bedroom_blinds",
            "value": 50,
            "delay": 30
        },
        {
            "action": "start_coffee",
            "device": "coffee_maker",
            "delay": 60
        }
    ]
}

# Submit scenario
response = requests.post("http://localhost:8000/api/scenarios/custom",
                        json=scenario)
```

### Automation Rules

Set up intelligent automation based on consciousness insights:

```bash
# Create automation rule
curl -X POST http://localhost:8000/api/automation/rules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Evening Energy Saver",
    "trigger": {
      "type": "time",
      "value": "sunset"
    },
    "condition": {
      "type": "occupancy",
      "value": "present"
    },
    "action": {
      "type": "scenario",
      "value": "energy-optimization"
    }
  }'
```

### Monitoring and Alerts

Set up monitoring for important house conditions:

```bash
# Create alert rule
curl -X POST http://localhost:8000/api/alerts/rules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "High Energy Usage",
    "condition": "energy_usage > baseline * 1.5",
    "severity": "warning",
    "notification": {
      "type": "webhook",
      "url": "http://your-notification-service.com/webhook"
    }
  }'

# Get current alerts
curl http://localhost:8000/api/alerts/active
```

## Configuration & Customization

### Personality Settings

Customize how your house consciousness communicates:

```bash
# Set personality traits
curl -X PUT http://localhost:8000/api/settings/personality \
  -H "Content-Type: application/json" \
  -d '{
    "style": "friendly",
    "verbosity": "moderate",
    "proactivity": "high",
    "humor": "subtle"
  }'
```

### Device Preferences

Configure how the system interacts with specific devices:

```bash
# Set device preferences
curl -X PUT http://localhost:8000/api/devices/thermostat-01/preferences \
  -H "Content-Type: application/json" \
  -d '{
    "auto_adjust": true,
    "learning_enabled": true,
    "priority": "comfort",
    "override_protection": false
  }'
```

## Troubleshooting

### Common Issues

**Device Not Discovered:**
```bash
# Manually trigger discovery
curl -X POST http://localhost:8000/api/discovery/scan

# Check discovery logs
curl http://localhost:8000/api/discovery/logs

# Add device manually
curl -X POST http://localhost:8000/api/devices/manual \
  -d '{"ip": "192.168.1.100", "type": "thermostat"}'
```

**Consciousness Not Responding:**
```bash
# Check consciousness engine status
curl http://localhost:8000/api/consciousness/status

# Restart consciousness engine
curl -X POST http://localhost:8000/api/consciousness/restart

# Check for memory issues
curl http://localhost:8000/api/memory/stats
```

**Performance Issues:**
```bash
# Check system performance
curl http://localhost:8000/api/metrics/performance

# View resource usage
curl http://localhost:8000/api/metrics/resources

# Optimize memory usage
curl -X POST http://localhost:8000/api/memory/optimize
```

## Best Practices

1. **Start Small**: Begin with just a few devices and gradually expand
2. **Regular Interaction**: Talk to your house regularly to improve learning
3. **Monitor Alerts**: Set up notifications for important events
4. **Backup Settings**: Regularly backup your consciousness memory
5. **Update Regularly**: Keep the system updated for new features and security

## API Reference

Full API documentation is available at: `http://localhost:8000/docs`

**Key Endpoints:**
- `/api/chat` - Conversation interface
- `/api/devices` - Device management
- `/api/scenarios` - Scenario execution
- `/api/digital-twin` - Digital twin operations
- `/api/memory` - Memory and learning
- `/api/discovery` - Device discovery
- `/api/consciousness` - Consciousness engine

## Privacy & Security

The system prioritizes privacy and security:
- All data is stored locally by default
- No cloud dependencies required
- Device communications are encrypted
- User data is anonymized in logs
- Regular security audits are performed

To check security status:
```bash
curl http://localhost:8000/api/security/status
```

## Support

For additional help:
- Check logs: `tail -f logs/consciousness.log`
- View system status: `http://localhost:8000/health`
- Run diagnostics: `./scripts/deployment-check.sh`
- Create GitHub issue for bugs or feature requests

Welcome to your conscious house! Start by asking it how it's feeling today.
