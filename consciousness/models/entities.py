from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
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
    interview_sessions: Mapped[List["InterviewSession"]] = relationship(
        "InterviewSession", back_populates="house"
    )

    __table_args__ = (Index("ix_houses_name", "name"),)


class Room(BaseModel):
    """Represents rooms within a house."""

    __tablename__ = "rooms"

    house_id: Mapped[int] = mapped_column(ForeignKey("houses.id"))

    name: Mapped[str] = mapped_column(String(255))
    room_type: Mapped[str] = mapped_column(
        String(100)
    )  # bedroom, kitchen, living_room, etc.
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
        Index("ix_rooms_house_type", "house_id", "room_type"),
        Index("ix_rooms_name", "name"),
    )


class Device(BaseModel):
    """Represents dynamically discovered IoT devices."""

    __tablename__ = "devices"

    house_id: Mapped[int] = mapped_column(ForeignKey("houses.id"))
    room_id: Mapped[Optional[int]] = mapped_column(ForeignKey("rooms.id"))

    # User-provided information from interview
    user_name: Mapped[str] = mapped_column(String(255))  # "Living room lights"
    user_description: Mapped[Optional[str]] = mapped_column(
        Text
    )  # "Philips Hue bulbs above couch"
    location: Mapped[Optional[str]] = mapped_column(String(255))  # "Living room"

    # Dynamic device identification (no fixed DeviceType enum)
    detected_brand: Mapped[Optional[str]] = mapped_column(String(100))  # "Philips"
    detected_model: Mapped[Optional[str]] = mapped_column(
        String(255)
    )  # "Hue Color Bulb A19"
    integration_type: Mapped[str] = mapped_column(String(100))  # "hue", "nest", "ring"
    device_class: Mapped[str] = mapped_column(
        String(50)
    )  # "light", "sensor", "climate"

    # Connection and capabilities
    connection_method: Mapped[Optional[str]] = mapped_column(
        String(50)
    )  # "wifi", "zigbee", "cloud"
    requires_hub: Mapped[bool] = mapped_column(Boolean, default=False)
    hub_id: Mapped[Optional[int]] = mapped_column(ForeignKey("devices.id"))

    # Feature support (dynamic, not predefined)
    supported_features: Mapped[List[str]] = mapped_column(JSON, default=list)
    capabilities: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Authentication and configuration
    requires_auth: Mapped[bool] = mapped_column(Boolean, default=False)
    auth_method: Mapped[Optional[str]] = mapped_column(
        String(50)
    )  # "oauth", "api_key", "none"
    config_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Status and monitoring
    status: Mapped[str] = mapped_column(String(50), default="offline")
    current_state: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Discovery metadata
    discovery_method: Mapped[str] = mapped_column(
        String(50)
    )  # "interview", "auto_dhcp", "manual"
    discovery_confidence: Mapped[float] = mapped_column(Float, default=1.0)
    interview_session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("interview_sessions.id")
    )

    # Relationships
    house: Mapped["House"] = relationship("House", back_populates="devices")
    room: Mapped[Optional["Room"]] = relationship("Room", back_populates="devices")
    hub_devices: Mapped[List["Device"]] = relationship(
        "Device", remote_side="Device.id"
    )
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
        Index("ix_devices_house_integration", "house_id", "integration_type"),
        Index("ix_devices_status", "status"),
        Index("ix_devices_device_class", "device_class"),
        Index("ix_devices_discovery_method", "discovery_method"),
    )


class DeviceEntity(BaseModel):
    """Individual capabilities/sensors within a device (Home Assistant pattern)."""

    __tablename__ = "device_entities"

    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"))

    # Entity identification
    entity_id: Mapped[str] = mapped_column(
        String(255), unique=True
    )  # "sensor.living_room_temp"
    unique_id: Mapped[str] = mapped_column(String(255))  # Device serial + entity type

    # Entity properties
    name: Mapped[str] = mapped_column(String(255))
    entity_type: Mapped[str] = mapped_column(String(50))  # "sensor", "switch", "light"
    device_class: Mapped[Optional[str]] = mapped_column(
        String(50)
    )  # "temperature", "humidity"

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
        Index("ix_device_entities_entity_type", "entity_type"),
        Index("ix_device_entities_device_id", "device_id"),
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
        Index("ix_people_house_role", "house_id", "role"),
        Index("ix_people_name", "name"),
    )
