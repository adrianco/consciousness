# Database Implementation Guide

## Overview
This guide provides comprehensive database schema design and SQLAlchemy implementation for the House Consciousness System. The database supports consciousness states, device management, memory systems, and SAFLA loop data structures.

## Database Architecture

### Core Design Principles
- **Time-series optimization** for sensor data and consciousness states
- **Relationship mapping** for entities, devices, and spaces
- **Memory consolidation** for experiences and learning
- **Performance optimization** with proper indexing and partitioning

## Phase 1: Database Models Implementation

### 1.1 Base Model Setup

```python
# consciousness/models/base.py
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import DateTime, Integer, String, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

Base = declarative_base()

class TimestampMixin:
    """Mixin for timestamp fields."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )

class BaseModel(Base, TimestampMixin):
    """Base model with common fields."""
    __abstract__ = True
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
```

### 1.2 Consciousness Models

```python
# consciousness/models/consciousness.py
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    DateTime, Float, Integer, String, Text, Boolean, 
    JSON, ForeignKey, Index, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel

class EmotionalState(BaseModel):
    """Tracks consciousness emotional states over time."""
    __tablename__ = "emotional_states"
    
    # Core emotional dimensions
    happiness: Mapped[float] = mapped_column(Float, CheckConstraint('happiness >= 0 AND happiness <= 1'))
    worry: Mapped[float] = mapped_column(Float, CheckConstraint('worry >= 0 AND worry <= 1'))
    boredom: Mapped[float] = mapped_column(Float, CheckConstraint('boredom >= 0 AND boredom <= 1'))
    excitement: Mapped[float] = mapped_column(Float, CheckConstraint('excitement >= 0 AND excitement <= 1'))
    
    # State metadata
    primary_emotion: Mapped[str] = mapped_column(String(50))
    intensity: Mapped[float] = mapped_column(Float, CheckConstraint('intensity >= 0 AND intensity <= 1'))
    confidence: Mapped[float] = mapped_column(Float, CheckConstraint('confidence >= 0 AND confidence <= 1'))
    
    # Context
    trigger_event: Mapped[Optional[str]] = mapped_column(String(255))
    context_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    reasoning: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    experiences: Mapped[List["Experience"]] = relationship(
        "Experience", back_populates="emotional_state"
    )
    
    __table_args__ = (
        Index('ix_emotional_states_timestamp', 'created_at'),
        Index('ix_emotional_states_primary_emotion', 'primary_emotion'),
        Index('ix_emotional_states_intensity', 'intensity'),
    )

class Memory(BaseModel):
    """Stores consciousness memories and experiences."""
    __tablename__ = "memories"
    
    # Memory classification
    memory_type: Mapped[str] = mapped_column(String(50))  # episodic, semantic, procedural
    category: Mapped[str] = mapped_column(String(100))
    importance: Mapped[float] = mapped_column(Float, CheckConstraint('importance >= 0 AND importance <= 1'))
    
    # Memory content
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    content: Mapped[Dict[str, Any]] = mapped_column(JSON)
    
    # Memory metadata
    source: Mapped[str] = mapped_column(String(100))  # sensor, user_interaction, internal
    confidence: Mapped[float] = mapped_column(Float, CheckConstraint('confidence >= 0 AND confidence <= 1'))
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    last_accessed: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Associations
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    related_entities: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    # Relationships
    experiences: Mapped[List["Experience"]] = relationship(
        "Experience", back_populates="memory"
    )
    
    __table_args__ = (
        Index('ix_memories_type_category', 'memory_type', 'category'),
        Index('ix_memories_importance', 'importance'),
        Index('ix_memories_created_at', 'created_at'),
        Index('ix_memories_last_accessed', 'last_accessed'),
    )

class Experience(BaseModel):
    """Links memories with emotional states and outcomes."""
    __tablename__ = "experiences"
    
    # Foreign keys
    memory_id: Mapped[int] = mapped_column(ForeignKey("memories.id"))
    emotional_state_id: Mapped[Optional[int]] = mapped_column(ForeignKey("emotional_states.id"))
    
    # Experience details
    experience_type: Mapped[str] = mapped_column(String(100))
    outcome: Mapped[str] = mapped_column(String(100))  # positive, negative, neutral
    impact_score: Mapped[float] = mapped_column(Float, CheckConstraint('impact_score >= -1 AND impact_score <= 1'))
    
    # Learning data
    lesson_learned: Mapped[Optional[str]] = mapped_column(Text)
    behavior_change: Mapped[Optional[str]] = mapped_column(Text)
    context: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Relationships
    memory: Mapped["Memory"] = relationship("Memory", back_populates="experiences")
    emotional_state: Mapped[Optional["EmotionalState"]] = relationship(
        "EmotionalState", back_populates="experiences"
    )
    
    __table_args__ = (
        Index('ix_experiences_type_outcome', 'experience_type', 'outcome'),
        Index('ix_experiences_impact_score', 'impact_score'),
        Index('ix_experiences_created_at', 'created_at'),
    )

class ConsciousnessSession(BaseModel):
    """Tracks consciousness system sessions and states."""
    __tablename__ = "consciousness_sessions"
    
    session_id: Mapped[str] = mapped_column(String(255), unique=True)
    status: Mapped[str] = mapped_column(String(50))  # active, paused, terminated
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Session metrics
    events_processed: Mapped[int] = mapped_column(Integer, default=0)
    decisions_made: Mapped[int] = mapped_column(Integer, default=0)
    learning_updates: Mapped[int] = mapped_column(Integer, default=0)
    
    # Session context
    initial_state: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    final_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    performance_metrics: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    __table_args__ = (
        Index('ix_consciousness_sessions_status', 'status'),
        Index('ix_consciousness_sessions_start_time', 'start_time'),
    )
```

### 1.3 Entity Models

```python
# consciousness/models/entities.py
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    String, Float, Integer, Boolean, JSON, 
    ForeignKey, Index, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel

class House(BaseModel):
    """Represents a house with its properties and capabilities."""
    __tablename__ = "houses"
    
    name: Mapped[str] = mapped_column(String(255))
    address: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Physical properties
    square_footage: Mapped[Optional[float]] = mapped_column(Float)
    num_rooms: Mapped[Optional[int]] = mapped_column(Integer)
    num_floors: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Configuration
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    preferences: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    capabilities: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    # Relationships
    rooms: Mapped[List["Room"]] = relationship("Room", back_populates="house")
    devices: Mapped[List["Device"]] = relationship("Device", back_populates="house")
    people: Mapped[List["Person"]] = relationship("Person", back_populates="house")
    
    __table_args__ = (
        Index('ix_houses_name', 'name'),
    )

class Room(BaseModel):
    """Represents rooms within a house."""
    __tablename__ = "rooms"
    
    house_id: Mapped[int] = mapped_column(ForeignKey("houses.id"))
    
    name: Mapped[str] = mapped_column(String(255))
    room_type: Mapped[str] = mapped_column(String(100))  # bedroom, kitchen, living_room, etc.
    floor: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Physical properties
    square_footage: Mapped[Optional[float]] = mapped_column(Float)
    ceiling_height: Mapped[Optional[float]] = mapped_column(Float)
    windows: Mapped[int] = mapped_column(Integer, default=0)
    doors: Mapped[int] = mapped_column(Integer, default=1)
    
    # Environmental preferences
    preferred_temperature: Mapped[Optional[float]] = mapped_column(Float)
    preferred_humidity: Mapped[Optional[float]] = mapped_column(Float)
    lighting_preferences: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Relationships
    house: Mapped["House"] = relationship("House", back_populates="rooms")
    devices: Mapped[List["Device"]] = relationship("Device", back_populates="room")
    
    __table_args__ = (
        Index('ix_rooms_house_type', 'house_id', 'room_type'),
        Index('ix_rooms_name', 'name'),
    )

class Device(BaseModel):
    """Represents dynamically discovered IoT devices."""
    __tablename__ = "devices"
    
    house_id: Mapped[int] = mapped_column(ForeignKey("houses.id"))
    room_id: Mapped[Optional[int]] = mapped_column(ForeignKey("rooms.id"))
    
    # User-provided information from interview
    user_name: Mapped[str] = mapped_column(String(255))  # "Living room lights"
    user_description: Mapped[Optional[str]] = mapped_column(Text)  # "Philips Hue bulbs above couch"
    location: Mapped[Optional[str]] = mapped_column(String(255))  # "Living room"
    
    # Dynamic device identification (no fixed DeviceType enum)
    detected_brand: Mapped[Optional[str]] = mapped_column(String(100))  # "Philips"
    detected_model: Mapped[Optional[str]] = mapped_column(String(255))  # "Hue Color Bulb A19"
    integration_type: Mapped[str] = mapped_column(String(100))  # "hue", "nest", "ring"
    device_class: Mapped[str] = mapped_column(String(50))  # "light", "sensor", "climate"
    
    # Connection and capabilities
    connection_method: Mapped[Optional[str]] = mapped_column(String(50))  # "wifi", "zigbee", "cloud"
    requires_hub: Mapped[bool] = mapped_column(Boolean, default=False)
    hub_id: Mapped[Optional[int]] = mapped_column(ForeignKey("devices.id"))
    
    # Feature support (dynamic, not predefined)
    supported_features: Mapped[List[str]] = mapped_column(JSON, default=list)
    capabilities: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Authentication and configuration
    requires_auth: Mapped[bool] = mapped_column(Boolean, default=False)
    auth_method: Mapped[Optional[str]] = mapped_column(String(50))  # "oauth", "api_key", "none"
    config_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Status and monitoring
    status: Mapped[str] = mapped_column(String(50), default="offline")
    current_state: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Discovery metadata
    discovery_method: Mapped[str] = mapped_column(String(50))  # "interview", "auto_dhcp", "manual"
    discovery_confidence: Mapped[float] = mapped_column(Float, default=1.0)
    interview_session_id: Mapped[Optional[int]] = mapped_column(ForeignKey("interview_sessions.id"))
    
    # Relationships
    house: Mapped["House"] = relationship("House", back_populates="devices")
    room: Mapped[Optional["Room"]] = relationship("Room", back_populates="devices")
    hub_devices: Mapped[List["Device"]] = relationship("Device", remote_side=[id])
    device_entities: Mapped[List["DeviceEntity"]] = relationship(
        "DeviceEntity", back_populates="device"
    )
    sensor_readings: Mapped[List["SensorReading"]] = relationship(
        "SensorReading", back_populates="device"
    )
    control_actions: Mapped[List["ControlAction"]] = relationship(
        "ControlAction", back_populates="device"
    )
    interview_session: Mapped[Optional["InterviewSession"]] = relationship(
        "InterviewSession", back_populates="discovered_devices"
    )
    
    __table_args__ = (
        Index('ix_devices_house_integration', 'house_id', 'integration_type'),
        Index('ix_devices_status', 'status'),
        Index('ix_devices_device_class', 'device_class'),
        Index('ix_devices_discovery_method', 'discovery_method'),
    )

class DeviceEntity(BaseModel):
    """Individual capabilities/sensors within a device (Home Assistant pattern)."""
    __tablename__ = "device_entities"
    
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"))
    
    # Entity identification
    entity_id: Mapped[str] = mapped_column(String(255), unique=True)  # "sensor.living_room_temp"
    unique_id: Mapped[str] = mapped_column(String(255))  # Device serial + entity type
    
    # Entity properties
    name: Mapped[str] = mapped_column(String(255))
    entity_type: Mapped[str] = mapped_column(String(50))  # "sensor", "switch", "light"
    device_class: Mapped[Optional[str]] = mapped_column(String(50))  # "temperature", "humidity"
    
    # Current state
    state: Mapped[Optional[str]] = mapped_column(String(255))
    attributes: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    unit_of_measurement: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Configuration
    icon: Mapped[Optional[str]] = mapped_column(String(100))  # "mdi:thermometer"
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    device: Mapped["Device"] = relationship("Device", back_populates="device_entities")
    
    __table_args__ = (
        Index('ix_device_entities_entity_type', 'entity_type'),
        Index('ix_device_entities_device_id', 'device_id'),
    )

class Person(BaseModel):
    """Represents people associated with the house."""
    __tablename__ = "people"
    
    house_id: Mapped[int] = mapped_column(ForeignKey("houses.id"))
    
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(100))  # owner, resident, guest
    
    # Preferences
    preferences: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    schedule: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Presence tracking
    is_present: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    house: Mapped["House"] = relationship("House", back_populates="people")
    
    __table_args__ = (
        Index('ix_people_house_role', 'house_id', 'role'),
        Index('ix_people_name', 'name'),
    )
```

### 1.4 Interview System Models

```python
# consciousness/models/interview.py
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    String, Float, Integer, Boolean, JSON, Text,
    ForeignKey, Index, CheckConstraint, DateTime
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel

class InterviewSession(BaseModel):
    """Tracks device discovery interview sessions."""
    __tablename__ = "interview_sessions"
    
    house_id: Mapped[int] = mapped_column(ForeignKey("houses.id"))
    
    # Session metadata
    session_type: Mapped[str] = mapped_column(String(50), default="device_discovery")
    status: Mapped[str] = mapped_column(String(50), default="active")  # active, completed, paused
    
    # Interview data
    conversation_log: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    discovered_devices: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    
    # Progress tracking
    current_phase: Mapped[str] = mapped_column(String(50), default="introduction")
    completed_steps: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    # Session timing
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    house: Mapped["House"] = relationship("House", back_populates="interview_sessions")
    device_candidates: Mapped[List["DeviceCandidate"]] = relationship(
        "DeviceCandidate", back_populates="interview_session"
    )
    discovered_devices: Mapped[List["Device"]] = relationship(
        "Device", back_populates="interview_session"
    )
    
    __table_args__ = (
        Index('ix_interview_sessions_house_status', 'house_id', 'status'),
        Index('ix_interview_sessions_started_at', 'started_at'),
    )

class DeviceCandidate(BaseModel):
    """Potential devices identified during interview."""
    __tablename__ = "device_candidates"
    
    interview_session_id: Mapped[int] = mapped_column(ForeignKey("interview_sessions.id"))
    
    # User input
    user_description: Mapped[str] = mapped_column(Text)
    extracted_keywords: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    # AI classification
    detected_brand: Mapped[Optional[str]] = mapped_column(String(100))
    detected_model: Mapped[Optional[str]] = mapped_column(String(255))
    detected_function: Mapped[Optional[str]] = mapped_column(String(100))
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Integration matching
    possible_integrations: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    recommended_integration: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Discovery results
    auto_discovery_results: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    auto_discovery_successful: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, confirmed, rejected
    created_device_id: Mapped[Optional[int]] = mapped_column(ForeignKey("devices.id"))
    
    # Relationships
    interview_session: Mapped["InterviewSession"] = relationship(
        "InterviewSession", back_populates="device_candidates"
    )
    created_device: Mapped[Optional["Device"]] = relationship("Device")
    
    __table_args__ = (
        Index('ix_device_candidates_session_status', 'interview_session_id', 'status'),
        Index('ix_device_candidates_confidence', 'confidence_score'),
    )

class IntegrationTemplate(BaseModel):
    """Templates for Home Assistant integration patterns."""
    __tablename__ = "integration_templates"
    
    # Integration identification
    integration_name: Mapped[str] = mapped_column(String(100), unique=True)  # "hue", "nest"
    display_name: Mapped[str] = mapped_column(String(255))  # "Philips Hue"
    
    # Matching patterns
    brand_keywords: Mapped[List[str]] = mapped_column(JSON, default=list)
    function_keywords: Mapped[List[str]] = mapped_column(JSON, default=list)
    model_patterns: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    # Integration details
    device_classes: Mapped[List[str]] = mapped_column(JSON, default=list)
    supported_features: Mapped[Dict[str, List[str]]] = mapped_column(JSON, default=dict)
    discovery_methods: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    # Configuration requirements
    requires_hub: Mapped[bool] = mapped_column(Boolean, default=False)
    auth_required: Mapped[bool] = mapped_column(Boolean, default=False)
    auth_methods: Mapped[List[str]] = mapped_column(JSON, default=list)
    config_fields: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    
    # Interview questions
    interview_questions: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    
    __table_args__ = (
        Index('ix_integration_templates_name', 'integration_name'),
        Index('ix_integration_templates_priority', 'priority'),
    )
```

### 1.5 Event and Sensor Models

```python
# consciousness/models/events.py
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    DateTime, Float, Integer, String, Text, Boolean, 
    JSON, ForeignKey, Index, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel

class SensorReading(BaseModel):
    """Time-series sensor data from devices."""
    __tablename__ = "sensor_readings"
    
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"))
    
    # Reading details
    sensor_type: Mapped[str] = mapped_column(String(100))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(50))
    quality: Mapped[float] = mapped_column(Float, CheckConstraint('quality >= 0 AND quality <= 1'))
    
    # Metadata
    reading_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Relationships
    device: Mapped["Device"] = relationship("Device", back_populates="sensor_readings")
    
    __table_args__ = (
        Index('ix_sensor_readings_device_time', 'device_id', 'reading_time'),
        Index('ix_sensor_readings_type_time', 'sensor_type', 'reading_time'),
        Index('ix_sensor_readings_time', 'reading_time'),
    )

class Event(BaseModel):
    """System events and activities."""
    __tablename__ = "events"
    
    # Event classification
    event_type: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(50))  # low, medium, high, critical
    
    # Event details
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(100))
    
    # Event data
    event_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    context: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Processing status
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('ix_events_type_category', 'event_type', 'category'),
        Index('ix_events_severity', 'severity'),
        Index('ix_events_created_at', 'created_at'),
        Index('ix_events_processed', 'processed'),
    )

class Activity(BaseModel):
    """Tracks house activities and patterns."""
    __tablename__ = "activities"
    
    # Activity details
    activity_type: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timing
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration: Mapped[Optional[int]] = mapped_column(Integer)  # seconds
    
    # Activity context
    participants: Mapped[List[str]] = mapped_column(JSON, default=list)
    devices_involved: Mapped[List[int]] = mapped_column(JSON, default=list)
    location: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Activity data
    activity_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    outcomes: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    __table_args__ = (
        Index('ix_activities_type', 'activity_type'),
        Index('ix_activities_start_time', 'start_time'),
        Index('ix_activities_duration', 'duration'),
    )

class Decision(BaseModel):
    """Tracks consciousness decisions and their outcomes."""
    __tablename__ = "decisions"
    
    # Decision details
    decision_type: Mapped[str] = mapped_column(String(100))
    context: Mapped[str] = mapped_column(String(255))
    trigger: Mapped[str] = mapped_column(String(255))
    
    # Decision process
    options_considered: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    chosen_option: Mapped[Dict[str, Any]] = mapped_column(JSON)
    reasoning: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, CheckConstraint('confidence >= 0 AND confidence <= 1'))
    
    # Outcome tracking
    expected_outcome: Mapped[str] = mapped_column(Text)
    actual_outcome: Mapped[Optional[str]] = mapped_column(Text)
    success: Mapped[Optional[bool]] = mapped_column(Boolean)
    
    # Learning data
    feedback_score: Mapped[Optional[float]] = mapped_column(Float, CheckConstraint('feedback_score >= -1 AND feedback_score <= 1'))
    lessons_learned: Mapped[Optional[str]] = mapped_column(Text)
    
    __table_args__ = (
        Index('ix_decisions_type', 'decision_type'),
        Index('ix_decisions_confidence', 'confidence'),
        Index('ix_decisions_success', 'success'),
        Index('ix_decisions_created_at', 'created_at'),
    )

class ControlAction(BaseModel):
    """Tracks control actions sent to devices."""
    __tablename__ = "control_actions"
    
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"))
    decision_id: Mapped[Optional[int]] = mapped_column(ForeignKey("decisions.id"))
    
    # Action details
    action_type: Mapped[str] = mapped_column(String(100))
    command: Mapped[str] = mapped_column(String(255))
    parameters: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Execution details
    status: Mapped[str] = mapped_column(String(50))  # pending, executing, completed, failed
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Results
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    device: Mapped["Device"] = relationship("Device", back_populates="control_actions")
    
    __table_args__ = (
        Index('ix_control_actions_device_status', 'device_id', 'status'),
        Index('ix_control_actions_type', 'action_type'),
        Index('ix_control_actions_executed_at', 'executed_at'),
    )
```

## Phase 2: Database Configuration

### 2.1 Database Connection Setup

```python
# consciousness/database.py
import os
from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from .models.base import Base
from .config import settings

# Async engine for main application
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_recycle=3600,
    pool_pre_ping=True,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine, 
    expire_on_commit=False,
    class_=AsyncSession
)

# Sync engine for migrations
sync_engine = create_engine(
    settings.DATABASE_URL.replace("sqlite+aiosqlite://", "sqlite:///"),
    echo=settings.DATABASE_ECHO,
)

SyncSessionLocal = sessionmaker(bind=sync_engine)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def get_sync_session():
    """Get sync database session."""
    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()

async def init_db():
    """Initialize database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def drop_db():
    """Drop all database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

### 2.2 Repository Pattern Implementation

```python
# consciousness/repositories/base.py
from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from ..models.base import BaseModel

T = TypeVar('T', bound=BaseModel)

class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session
    
    async def create(self, **kwargs) -> T:
        """Create a new record."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance
    
    async def get(self, id: int) -> Optional[T]:
        """Get record by ID."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def list(
        self, 
        offset: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """List records with pagination and filtering."""
        query = select(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        
        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update(self, id: int, **kwargs) -> Optional[T]:
        """Update record by ID."""
        await self.session.execute(
            update(self.model).where(self.model.id == id).values(**kwargs)
        )
        await self.session.commit()
        return await self.get(id)
    
    async def delete(self, id: int) -> bool:
        """Delete record by ID."""
        result = await self.session.execute(
            delete(self.model).where(self.model.id == id)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering."""
        query = select(func.count(self.model.id))
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(query)
        return result.scalar()

# consciousness/repositories/consciousness.py
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from .base import BaseRepository
from ..models.consciousness import EmotionalState, Memory, Experience

class EmotionalStateRepository(BaseRepository[EmotionalState]):
    """Repository for emotional state management."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(EmotionalState, session)
    
    async def get_current_state(self) -> Optional[EmotionalState]:
        """Get the most recent emotional state."""
        result = await self.session.execute(
            select(EmotionalState)
            .order_by(desc(EmotionalState.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_state_history(
        self, 
        hours: int = 24,
        limit: int = 100
    ) -> List[EmotionalState]:
        """Get emotional state history."""
        since = datetime.utcnow() - timedelta(hours=hours)
        result = await self.session.execute(
            select(EmotionalState)
            .where(EmotionalState.created_at >= since)
            .order_by(desc(EmotionalState.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_dominant_emotion_periods(
        self, days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get periods where specific emotions were dominant."""
        since = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(
                EmotionalState.primary_emotion,
                func.count(EmotionalState.id).label('count'),
                func.avg(EmotionalState.intensity).label('avg_intensity')
            )
            .where(EmotionalState.created_at >= since)
            .group_by(EmotionalState.primary_emotion)
            .order_by(desc('count'))
        )
        return [
            {
                'emotion': row.primary_emotion,
                'count': row.count,
                'avg_intensity': row.avg_intensity
            }
            for row in result
        ]

class MemoryRepository(BaseRepository[Memory]):
    """Repository for memory management."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Memory, session)
    
    async def search_memories(
        self, 
        query: str,
        memory_type: Optional[str] = None,
        category: Optional[str] = None,
        min_importance: float = 0.0,
        limit: int = 10
    ) -> List[Memory]:
        """Search memories by content and filters."""
        filters = [Memory.importance >= min_importance]
        
        if memory_type:
            filters.append(Memory.memory_type == memory_type)
        if category:
            filters.append(Memory.category == category)
        
        # Simple text search (enhance with full-text search in production)
        filters.append(
            or_(
                Memory.title.contains(query),
                Memory.description.contains(query)
            )
        )
        
        result = await self.session.execute(
            select(Memory)
            .where(and_(*filters))
            .order_by(desc(Memory.importance), desc(Memory.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_related_memories(
        self, 
        entity: str, 
        limit: int = 5
    ) -> List[Memory]:
        """Get memories related to a specific entity."""
        result = await self.session.execute(
            select(Memory)
            .where(Memory.related_entities.contains([entity]))
            .order_by(desc(Memory.importance), desc(Memory.last_accessed))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def update_access(self, memory_id: int):
        """Update memory access tracking."""
        await self.session.execute(
            update(Memory)
            .where(Memory.id == memory_id)
            .values(
                access_count=Memory.access_count + 1,
                last_accessed=datetime.utcnow()
            )
        )
        await self.session.commit()
class InterviewRepository(BaseRepository[InterviewSession]):
    """Repository for interview session management."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(InterviewSession, session)
    
    async def get_active_session(self, house_id: int) -> Optional[InterviewSession]:
        """Get the active interview session for a house."""
        result = await self.session.execute(
            select(InterviewSession)
            .where(
                and_(
                    InterviewSession.house_id == house_id,
                    InterviewSession.status == "active"
                )
            )
            .order_by(desc(InterviewSession.started_at))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def add_conversation_turn(
        self, 
        session_id: int,
        speaker: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add a conversation turn to the interview log."""
        session = await self.get(session_id)
        if session:
            conversation_turn = {
                "timestamp": datetime.utcnow().isoformat(),
                "speaker": speaker,
                "message": message,
                "metadata": metadata or {}
            }
            session.conversation_log.append(conversation_turn)
            await self.update(session_id, conversation_log=session.conversation_log)

class DeviceCandidateRepository(BaseRepository[DeviceCandidate]):
    """Repository for device candidate management."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(DeviceCandidate, session)
    
    async def get_pending_candidates(
        self, 
        interview_session_id: int
    ) -> List[DeviceCandidate]:
        """Get pending device candidates for an interview session."""
        result = await self.session.execute(
            select(DeviceCandidate)
            .where(
                and_(
                    DeviceCandidate.interview_session_id == interview_session_id,
                    DeviceCandidate.status == "pending"
                )
            )
            .order_by(desc(DeviceCandidate.confidence_score))
        )
        return result.scalars().all()
    
    async def confirm_candidate(
        self,
        candidate_id: int,
        device_id: int
    ) -> Optional[DeviceCandidate]:
        """Confirm a device candidate and link to created device."""
        return await self.update(
            candidate_id,
            status="confirmed",
            created_device_id=device_id
        )

class DeviceRepository(BaseRepository[Device]):
    """Repository for dynamic device management."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Device, session)
    
    async def search_by_description(
        self,
        house_id: int,
        search_terms: List[str],
        limit: int = 10
    ) -> List[Device]:
        """Search devices by description keywords."""
        filters = [Device.house_id == house_id]
        
        # Build OR conditions for search terms
        search_conditions = []
        for term in search_terms:
            search_conditions.extend([
                Device.user_name.ilike(f"%{term}%"),
                Device.user_description.ilike(f"%{term}%"),
                Device.detected_brand.ilike(f"%{term}%"),
                Device.detected_model.ilike(f"%{term}%")
            ])
        
        if search_conditions:
            filters.append(or_(*search_conditions))
        
        result = await self.session.execute(
            select(Device)
            .where(and_(*filters))
            .order_by(Device.user_name)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_integration_type(
        self,
        house_id: int,
        integration_type: str
    ) -> List[Device]:
        """Get all devices of a specific integration type."""
        result = await self.session.execute(
            select(Device)
            .where(
                and_(
                    Device.house_id == house_id,
                    Device.integration_type == integration_type
                )
            )
            .order_by(Device.user_name)
        )
        return result.scalars().all()
```

## Phase 3: Database Migrations with Alembic

### 3.1 Alembic Configuration

```python
# alembic/env.py
import asyncio
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import AsyncEngine
from alembic import context
from consciousness.models.base import Base
from consciousness.config import settings

# Import all models to ensure they're registered
from consciousness.models.consciousness import *
from consciousness.models.entities import *
from consciousness.models.events import *
from consciousness.models.interview import *

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

### 3.2 Sample Migration Scripts

```bash
# Create initial migration with dynamic device schema
uv run alembic revision --autogenerate -m "Initial consciousness schema with dynamic devices"

# Migration for interview system
uv run alembic revision --autogenerate -m "Add device interview system"

# Migration for Home Assistant integration templates
uv run alembic revision --autogenerate -m "Add integration templates"

# Migration for indexes optimization
uv run alembic revision --autogenerate -m "Add performance indexes"

# Migration for new features
uv run alembic revision --autogenerate -m "Add SAFLA loop tracking"
```

## Phase 4: Performance Optimization

### 4.1 Indexing Strategy

```sql
-- Additional indexes for performance
CREATE INDEX CONCURRENTLY ix_sensor_readings_value_time ON sensor_readings(value, reading_time);
CREATE INDEX CONCURRENTLY ix_memories_full_text ON memories USING gin(to_tsvector('english', title || ' ' || description));
CREATE INDEX CONCURRENTLY ix_events_severity_created ON events(severity, created_at);
CREATE INDEX CONCURRENTLY ix_emotional_states_happiness_time ON emotional_states(happiness, created_at);

-- Interview system indexes
CREATE INDEX CONCURRENTLY ix_device_candidates_description_search ON device_candidates USING gin(to_tsvector('english', user_description));
CREATE INDEX CONCURRENTLY ix_devices_user_description_search ON devices USING gin(to_tsvector('english', user_name || ' ' || COALESCE(user_description, '')));
CREATE INDEX CONCURRENTLY ix_integration_templates_keywords ON integration_templates USING gin(brand_keywords || function_keywords);
CREATE INDEX CONCURRENTLY ix_interview_sessions_house_date ON interview_sessions(house_id, started_at);
```

### 4.2 Database Optimization

```python
# consciousness/utils/database_utils.py
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

async def optimize_database(session: AsyncSession):
    """Run database optimization tasks."""
    
    # SQLite specific optimizations
    await session.execute(text("PRAGMA journal_mode=WAL"))
    await session.execute(text("PRAGMA synchronous=NORMAL"))
    await session.execute(text("PRAGMA cache_size=10000"))
    await session.execute(text("PRAGMA temp_store=MEMORY"))
    await session.execute(text("PRAGMA mmap_size=268435456"))  # 256MB
    
    # Analyze tables for query optimization
    await session.execute(text("ANALYZE"))
    
    await session.commit()

async def cleanup_old_data(session: AsyncSession, days: int = 30):
    """Clean up old sensor readings and events."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Keep only recent sensor readings
    await session.execute(
        delete(SensorReading).where(SensorReading.reading_time < cutoff_date)
    )
    
    # Keep only important events
    await session.execute(
        delete(Event).where(
            and_(
                Event.created_at < cutoff_date,
                Event.severity.in_(['low', 'medium'])
            )
        )
    )
    
    await session.commit()
```

## Phase 5: Testing and Validation

### 5.1 Database Testing

```python
# tests/test_database.py
import pytest
from datetime import datetime, timedelta
from consciousness.database import get_async_session, init_db, drop_db
from consciousness.models.consciousness import EmotionalState, Memory
from consciousness.models.entities import House, Device
from consciousness.models.interview import InterviewSession, DeviceCandidate
from consciousness.repositories.consciousness import EmotionalStateRepository

@pytest.fixture
async def db_session():
    """Create test database session."""
    await init_db()
    async with get_async_session() as session:
        yield session
    await drop_db()

@pytest.fixture
async def test_house(db_session):
    """Create test house."""
    house = House(
        name="Test House",
        timezone="America/New_York"
    )
    db_session.add(house)
    await db_session.commit()
    await db_session.refresh(house)
    return house

@pytest.mark.asyncio
async def test_emotional_state_creation(db_session):
    """Test emotional state creation and retrieval."""
    repo = EmotionalStateRepository(db_session)
    
    state = await repo.create(
        happiness=0.8,
        worry=0.2,
        boredom=0.1,
        excitement=0.7,
        primary_emotion="happy",
        intensity=0.8,
        confidence=0.9,
        trigger_event="user_returned_home"
    )
    
    assert state.id is not None
    assert state.primary_emotion == "happy"
    assert state.happiness == 0.8
    
    # Test retrieval
    retrieved = await repo.get_current_state()
    assert retrieved.id == state.id

@pytest.mark.asyncio
async def test_interview_session_flow(db_session, test_house):
    """Test interview session creation and management."""
    from consciousness.repositories.consciousness import InterviewRepository
    
    repo = InterviewRepository(db_session)
    
    # Create interview session
    session = await repo.create(
        house_id=test_house.id,
        session_type="device_discovery",
        status="active",
        started_at=datetime.utcnow()
    )
    
    assert session.id is not None
    assert session.status == "active"
    
    # Test adding conversation turns
    await repo.add_conversation_turn(
        session.id,
        "user",
        "I have some Philips Hue lights and a Nest thermostat"
    )
    
    # Retrieve and verify conversation log
    updated_session = await repo.get(session.id)
    assert len(updated_session.conversation_log) == 1
    assert updated_session.conversation_log[0]["speaker"] == "user"

@pytest.mark.asyncio
async def test_device_candidate_management(db_session, test_house):
    """Test device candidate creation and confirmation."""
    from consciousness.repositories.consciousness import DeviceCandidateRepository, InterviewRepository
    
    # Create interview session
    interview_repo = InterviewRepository(db_session)
    session = await interview_repo.create(
        house_id=test_house.id,
        started_at=datetime.utcnow()
    )
    
    # Create device candidate
    candidate_repo = DeviceCandidateRepository(db_session)
    candidate = await candidate_repo.create(
        interview_session_id=session.id,
        user_description="Philips Hue color lights in living room",
        detected_brand="Philips",
        detected_function="lighting",
        confidence_score=0.95,
        recommended_integration="hue"
    )
    
    assert candidate.confidence_score == 0.95
    assert candidate.status == "pending"
    
    # Get pending candidates
    pending = await candidate_repo.get_pending_candidates(session.id)
    assert len(pending) == 1
    assert pending[0].id == candidate.id

@pytest.mark.asyncio
async def test_dynamic_device_creation(db_session, test_house):
    """Test dynamic device creation from interview."""
    from consciousness.repositories.consciousness import DeviceRepository
    
    repo = DeviceRepository(db_session)
    
    # Create device with dynamic typing
    device = await repo.create(
        house_id=test_house.id,
        user_name="Living room lights",
        user_description="Philips Hue color bulbs above the couch",
        detected_brand="Philips",
        detected_model="Hue Color Bulb A19",
        integration_type="hue",
        device_class="light",
        supported_features=["brightness", "color", "effects"],
        discovery_method="interview",
        discovery_confidence=0.95
    )
    
    assert device.integration_type == "hue"
    assert device.device_class == "light"
    assert "brightness" in device.supported_features
    
    # Test search functionality
    results = await repo.search_by_description(
        test_house.id,
        ["philips", "lights"]
    )
    assert len(results) == 1
    assert results[0].id == device.id
```

## Next Steps

1. **Consciousness Engine**: Implement using `03-consciousness-engine-guide.md`
2. **SAFLA Loop**: Build using `04-safla-loop-guide.md`
3. **Interview System**: Implement conversational device discovery using `device-interview-system.md`
4. **Device Integration**: Add dynamic adapters using `05-device-integration-guide.md`
5. **Integration Templates**: Populate Home Assistant integration patterns

This database implementation provides a solid foundation for storing consciousness states, managing dynamic device discovery through interviews, and supporting the SAFLA loop architecture with proper indexing, relationships, and performance optimizations. The flexible device schema allows for unlimited device types through conversational discovery.