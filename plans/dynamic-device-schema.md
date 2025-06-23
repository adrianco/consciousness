# Dynamic Device Database Schema

## Updated SQLAlchemy Models

### Core Models (Updated)

```python
from sqlalchemy import Column, String, DateTime, JSON, Boolean, Float, Text, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime
from typing import Optional, Dict, List, Any

Base = declarative_base()

class House(Base):
    __tablename__ = "houses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    location = Column(String(255))
    timezone = Column(String(50), default="UTC")
    owner_preferences = Column(JSON, default=dict)
    
    # Interview and setup status
    setup_completed = Column(Boolean, default=False)
    last_interview_date = Column(DateTime)
    
    # Relationships
    devices = relationship("Device", back_populates="house", cascade="all, delete-orphan")
    interview_sessions = relationship("InterviewSession", back_populates="house")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Device(Base):
    __tablename__ = "devices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    house_id = Column(UUID(as_uuid=True), ForeignKey("houses.id"), nullable=False)
    
    # User-provided information
    user_name = Column(String(255), nullable=False)  # "Living room lights"
    user_description = Column(Text)  # "Philips Hue color bulbs above the couch"
    location = Column(String(255))  # "Living room"
    
    # Technical identification (replaces fixed DeviceType enum)
    detected_brand = Column(String(100))  # "Philips", "Nest", "Ring"
    detected_model = Column(String(255))  # "Hue Color Bulb A19"
    integration_type = Column(String(100), nullable=False)  # "hue", "nest", "ring"
    device_class = Column(String(50), nullable=False)  # "light", "sensor", "switch", "climate"
    
    # Connection and capabilities
    connection_method = Column(String(50))  # "wifi", "zigbee", "cloud", "bluetooth"
    requires_hub = Column(Boolean, default=False)
    hub_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=True)  # Self-referencing for hub devices
    api_endpoint = Column(String(500))  # Direct device API endpoint if applicable
    
    # Feature support (JSON array of supported features)
    supported_features = Column(JSON, default=list)  # ["brightness", "color", "effects"]
    capabilities = Column(JSON, default=dict)  # Integration-specific capabilities
    
    # Authentication and configuration
    requires_auth = Column(Boolean, default=False)
    auth_method = Column(String(50))  # "oauth", "api_key", "local_token", "none"
    config_data = Column(JSON, default=dict)  # Integration-specific configuration
    credentials_id = Column(UUID(as_uuid=True), ForeignKey("device_credentials.id"))
    
    # Status and monitoring
    is_online = Column(Boolean, default=True)
    last_seen = Column(DateTime, default=datetime.utcnow)
    last_error = Column(Text)
    
    # Discovery metadata
    discovery_method = Column(String(50))  # "interview", "auto_dhcp", "auto_mdns", "manual"
    discovery_confidence = Column(Float, default=1.0)  # Confidence in device identification
    
    # Relationships
    house = relationship("House", back_populates="devices")
    credentials = relationship("DeviceCredentials", back_populates="device")
    entities = relationship("DeviceEntity", back_populates="device", cascade="all, delete-orphan")
    hub_devices = relationship("Device", remote_side=[id])  # Devices connected through this hub
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DeviceEntity(Base):
    """
    Individual data points/capabilities from a device (following Home Assistant pattern)
    One device can have multiple entities (e.g., temperature sensor, humidity sensor, battery level)
    """
    __tablename__ = "device_entities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False)
    
    # Entity identification
    entity_id = Column(String(255), nullable=False)  # "sensor.living_room_temperature"
    unique_id = Column(String(255), unique=True)  # Device serial + entity type
    
    # Entity properties
    name = Column(String(255), nullable=False)
    entity_type = Column(String(50), nullable=False)  # "sensor", "switch", "light"
    device_class = Column(String(50))  # "temperature", "humidity", "motion"
    
    # Current state
    state = Column(String(255))
    attributes = Column(JSON, default=dict)
    unit_of_measurement = Column(String(50))
    
    # Configuration
    icon = Column(String(100))  # "mdi:thermometer"
    is_enabled = Column(Boolean, default=True)
    is_visible = Column(Boolean, default=True)
    
    # Relationships
    device = relationship("Device", back_populates="entities")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DeviceCredentials(Base):
    """
    Secure storage for device authentication credentials
    """
    __tablename__ = "device_credentials"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Credential data (encrypted)
    credential_type = Column(String(50), nullable=False)  # "oauth_token", "api_key", "username_password"
    encrypted_data = Column(Text, nullable=False)  # Encrypted JSON with credentials
    
    # OAuth-specific fields
    access_token_encrypted = Column(Text)
    refresh_token_encrypted = Column(Text)
    token_expires_at = Column(DateTime)
    
    # Relationships
    device = relationship("Device", back_populates="credentials")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Interview System Models (New)

```python
class InterviewSession(Base):
    """
    Tracks device discovery interview sessions with homeowners
    """
    __tablename__ = "interview_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    house_id = Column(UUID(as_uuid=True), ForeignKey("houses.id"), nullable=False)
    
    # Session metadata
    session_type = Column(String(50), default="device_discovery")  # "initial_setup", "add_devices", "troubleshoot"
    status = Column(String(50), default="active")  # "active", "completed", "paused", "cancelled"
    
    # Interview data
    conversation_log = Column(JSON, default=list)  # Full conversation history
    discovered_devices = Column(JSON, default=list)  # Devices mentioned during interview
    
    # Progress tracking
    current_phase = Column(String(50), default="introduction")  # "introduction", "discovery", "configuration", "testing"
    completed_steps = Column(JSON, default=list)
    
    # Session timing
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    estimated_duration = Column(Integer)  # Minutes
    
    # Relationships
    house = relationship("House", back_populates="interview_sessions")
    device_candidates = relationship("DeviceCandidate", back_populates="interview_session")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DeviceCandidate(Base):
    """
    Potential devices identified during interview process, before final confirmation
    """
    __tablename__ = "device_candidates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False)
    
    # User input
    user_description = Column(Text, nullable=False)  # Raw user description
    extracted_keywords = Column(JSON, default=list)  # ["philips", "hue", "lights", "color"]
    
    # AI classification
    detected_brand = Column(String(100))
    detected_model = Column(String(255))
    detected_function = Column(String(100))  # "lighting", "climate", "security"
    confidence_score = Column(Float, default=0.0)
    
    # Integration matching
    possible_integrations = Column(JSON, default=list)  # List of possible HA integrations
    recommended_integration = Column(String(100))
    integration_confidence = Column(Float, default=0.0)
    
    # Discovery results
    network_discovery_results = Column(JSON, default=dict)
    auto_discovery_successful = Column(Boolean, default=False)
    
    # Status
    status = Column(String(50), default="pending")  # "pending", "confirmed", "rejected", "needs_info"
    rejection_reason = Column(Text)
    
    # Final device mapping
    created_device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"))
    
    # Relationships
    interview_session = relationship("InterviewSession", back_populates="device_candidates")
    created_device = relationship("Device")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class IntegrationTemplate(Base):
    """
    Templates for Home Assistant integration patterns
    """
    __tablename__ = "integration_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Integration identification
    integration_name = Column(String(100), unique=True, nullable=False)  # "hue", "nest", "ring"
    display_name = Column(String(255), nullable=False)  # "Philips Hue", "Google Nest"
    
    # Matching patterns
    brand_keywords = Column(JSON, default=list)  # ["philips", "hue"]
    function_keywords = Column(JSON, default=list)  # ["lights", "bulbs", "lighting"]
    model_patterns = Column(JSON, default=list)  # Regex patterns for model matching
    
    # Integration details
    device_classes = Column(JSON, default=list)  # ["light", "sensor", "switch"]
    supported_features = Column(JSON, default=dict)  # Features by device class
    discovery_methods = Column(JSON, default=list)  # ["mdns", "dhcp", "upnp"]
    
    # Configuration requirements
    requires_hub = Column(Boolean, default=False)
    auth_required = Column(Boolean, default=False)
    auth_methods = Column(JSON, default=list)  # ["oauth", "api_key"]
    config_fields = Column(JSON, default=list)  # Required configuration fields
    
    # Interview questions
    interview_questions = Column(JSON, default=list)  # Questions to ask for this integration
    
    # Home Assistant metadata
    ha_domain = Column(String(100))  # Home Assistant domain name
    ha_config_flow = Column(Boolean, default=False)  # Supports config flow
    ha_discovery = Column(JSON, default=list)  # Discovery methods in HA
    
    # Status
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=100)  # Lower number = higher priority
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Discovery and Events Models (Updated)

```python
class Event(Base):
    __tablename__ = "events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    house_id = Column(UUID(as_uuid=True), ForeignKey("houses.id"), nullable=False)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=True)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("device_entities.id"), nullable=True)
    
    # Event details
    event_type = Column(String(100), nullable=False)
    event_data = Column(JSON, default=dict)
    
    # State information
    old_state = Column(String(255))
    new_state = Column(String(255))
    state_attributes = Column(JSON, default=dict)
    
    # Context
    context = Column(JSON, default=dict)
    source = Column(String(100))  # "device", "automation", "user", "system"
    
    # Processing
    processed = Column(Boolean, default=False)
    processing_error = Column(Text)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    house = relationship("House")
    device = relationship("Device")
    entity = relationship("DeviceEntity")


class DiscoveryLog(Base):
    """
    Log of automatic device discovery attempts
    """
    __tablename__ = "discovery_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    house_id = Column(UUID(as_uuid=True), ForeignKey("houses.id"), nullable=False)
    
    # Discovery details
    discovery_method = Column(String(50), nullable=False)  # "dhcp", "mdns", "upnp", "bluetooth"
    discovery_target = Column(String(255))  # IP range, service type, etc.
    
    # Results
    devices_found = Column(JSON, default=list)
    discovery_data = Column(JSON, default=dict)
    success = Column(Boolean, default=False)
    error_message = Column(Text)
    
    # Timing
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    # Relationships
    house = relationship("House")
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

## Migration Strategy

### Step 1: Add New Tables
```sql
-- Create new tables for interview system
CREATE TABLE interview_sessions (...);
CREATE TABLE device_candidates (...);
CREATE TABLE integration_templates (...);
CREATE TABLE device_entities (...);
CREATE TABLE device_credentials (...);
CREATE TABLE discovery_logs (...);
```

### Step 2: Migrate Existing Device Data
```python
def migrate_existing_devices():
    """
    Migrate existing fixed-type devices to new dynamic schema
    """
    for device in old_devices:
        new_device = Device(
            user_name=device.name,
            user_description=f"{device.brand} {device.type}",
            detected_brand=device.brand,
            integration_type=map_old_type_to_integration(device.type),
            device_class=map_old_type_to_class(device.type),
            config_data=device.api_config,
            discovery_method="legacy_migration"
        )
        session.add(new_device)
```

### Step 3: Populate Integration Templates
```python
def populate_integration_templates():
    """
    Seed database with Home Assistant integration patterns
    """
    templates = load_ha_integration_data()
    for template_data in templates:
        template = IntegrationTemplate(**template_data)
        session.add(template)
```

This schema supports the full dynamic device discovery workflow while maintaining compatibility with the existing consciousness engine architecture.