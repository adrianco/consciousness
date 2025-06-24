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


class SensorReading(BaseModel):
    """Time-series sensor data from devices."""

    __tablename__ = "sensor_readings"

    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"))

    # Reading details
    sensor_type: Mapped[str] = mapped_column(String(100))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(50))
    quality: Mapped[float] = mapped_column(
        Float, CheckConstraint("quality >= 0 AND quality <= 1")
    )

    # Metadata
    reading_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reading_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Relationships
    device: Mapped["Device"] = relationship("Device", back_populates="sensor_readings")

    __table_args__ = (
        Index("ix_sensor_readings_device_time", "device_id", "reading_time"),
        Index("ix_sensor_readings_type_time", "sensor_type", "reading_time"),
        Index("ix_sensor_readings_time", "reading_time"),
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
        Index("ix_events_type_category", "event_type", "category"),
        Index("ix_events_severity", "severity"),
        Index("ix_events_created_at", "created_at"),
        Index("ix_events_processed", "processed"),
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
        Index("ix_activities_type", "activity_type"),
        Index("ix_activities_start_time", "start_time"),
        Index("ix_activities_duration", "duration"),
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
    confidence: Mapped[float] = mapped_column(
        Float, CheckConstraint("confidence >= 0 AND confidence <= 1")
    )

    # Outcome tracking
    expected_outcome: Mapped[str] = mapped_column(Text)
    actual_outcome: Mapped[Optional[str]] = mapped_column(Text)
    success: Mapped[Optional[bool]] = mapped_column(Boolean)

    # Learning data
    feedback_score: Mapped[Optional[float]] = mapped_column(
        Float, CheckConstraint("feedback_score >= -1 AND feedback_score <= 1")
    )
    lessons_learned: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (
        Index("ix_decisions_type", "decision_type"),
        Index("ix_decisions_confidence", "confidence"),
        Index("ix_decisions_success", "success"),
        Index("ix_decisions_created_at", "created_at"),
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
    status: Mapped[str] = mapped_column(
        String(50)
    )  # pending, executing, completed, failed
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Results
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    device: Mapped["Device"] = relationship("Device", back_populates="control_actions")

    __table_args__ = (
        Index("ix_control_actions_device_status", "device_id", "status"),
        Index("ix_control_actions_type", "action_type"),
        Index("ix_control_actions_executed_at", "executed_at"),
    )
