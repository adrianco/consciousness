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


class InterviewSession(BaseModel):
    """Tracks device discovery interview sessions."""

    __tablename__ = "interview_sessions"

    house_id: Mapped[int] = mapped_column(ForeignKey("houses.id"))

    # Session metadata
    session_type: Mapped[str] = mapped_column(String(50), default="device_discovery")
    status: Mapped[str] = mapped_column(
        String(50), default="active"
    )  # active, completed, paused

    # Interview data
    conversation_log: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)

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
        Index("ix_interview_sessions_house_status", "house_id", "status"),
        Index("ix_interview_sessions_started_at", "started_at"),
    )


class DeviceCandidate(BaseModel):
    """Potential devices identified during interview."""

    __tablename__ = "device_candidates"

    interview_session_id: Mapped[int] = mapped_column(
        ForeignKey("interview_sessions.id")
    )

    # User input
    user_description: Mapped[str] = mapped_column(Text)
    extracted_keywords: Mapped[List[str]] = mapped_column(JSON, default=list)

    # AI classification
    detected_brand: Mapped[Optional[str]] = mapped_column(String(100))
    detected_model: Mapped[Optional[str]] = mapped_column(String(255))
    detected_function: Mapped[Optional[str]] = mapped_column(String(100))
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Integration matching
    possible_integrations: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON, default=list
    )
    recommended_integration: Mapped[Optional[str]] = mapped_column(String(100))

    # Discovery results
    auto_discovery_results: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    auto_discovery_successful: Mapped[bool] = mapped_column(Boolean, default=False)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )  # pending, confirmed, rejected
    created_device_id: Mapped[Optional[int]] = mapped_column(ForeignKey("devices.id"))

    # Relationships
    interview_session: Mapped["InterviewSession"] = relationship(
        "InterviewSession", back_populates="device_candidates"
    )
    created_device: Mapped[Optional["Device"]] = relationship("Device")

    __table_args__ = (
        Index("ix_device_candidates_session_status", "interview_session_id", "status"),
        Index("ix_device_candidates_confidence", "confidence_score"),
    )


class IntegrationTemplate(BaseModel):
    """Templates for Home Assistant integration patterns."""

    __tablename__ = "integration_templates"

    # Integration identification
    integration_name: Mapped[str] = mapped_column(
        String(100), unique=True
    )  # "hue", "nest"
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
    interview_questions: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON, default=list
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)

    __table_args__ = (
        Index("ix_integration_templates_name", "integration_name"),
        Index("ix_integration_templates_priority", "priority"),
    )
