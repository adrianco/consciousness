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


class EmotionalState(BaseModel):
    """Tracks consciousness emotional states over time."""

    __tablename__ = "emotional_states"

    # Core emotional dimensions
    happiness: Mapped[float] = mapped_column(
        Float, CheckConstraint("happiness >= 0 AND happiness <= 1")
    )
    worry: Mapped[float] = mapped_column(
        Float, CheckConstraint("worry >= 0 AND worry <= 1")
    )
    boredom: Mapped[float] = mapped_column(
        Float, CheckConstraint("boredom >= 0 AND boredom <= 1")
    )
    excitement: Mapped[float] = mapped_column(
        Float, CheckConstraint("excitement >= 0 AND excitement <= 1")
    )

    # State metadata
    primary_emotion: Mapped[str] = mapped_column(String(50))
    intensity: Mapped[float] = mapped_column(
        Float, CheckConstraint("intensity >= 0 AND intensity <= 1")
    )
    confidence: Mapped[float] = mapped_column(
        Float, CheckConstraint("confidence >= 0 AND confidence <= 1")
    )

    # Context
    trigger_event: Mapped[Optional[str]] = mapped_column(String(255))
    context_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    reasoning: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    experiences: Mapped[List["Experience"]] = relationship(
        "Experience", back_populates="emotional_state"
    )

    __table_args__ = (
        Index("ix_emotional_states_timestamp", "created_at"),
        Index("ix_emotional_states_primary_emotion", "primary_emotion"),
        Index("ix_emotional_states_intensity", "intensity"),
    )


class Memory(BaseModel):
    """Stores consciousness memories and experiences."""

    __tablename__ = "memories"

    # Memory classification
    memory_type: Mapped[str] = mapped_column(
        String(50)
    )  # episodic, semantic, procedural
    category: Mapped[str] = mapped_column(String(100))
    importance: Mapped[float] = mapped_column(
        Float, CheckConstraint("importance >= 0 AND importance <= 1")
    )

    # Memory content
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    content: Mapped[Dict[str, Any]] = mapped_column(JSON)

    # Memory metadata
    source: Mapped[str] = mapped_column(
        String(100)
    )  # sensor, user_interaction, internal
    confidence: Mapped[float] = mapped_column(
        Float, CheckConstraint("confidence >= 0 AND confidence <= 1")
    )
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
        Index("ix_memories_type_category", "memory_type", "category"),
        Index("ix_memories_importance", "importance"),
        Index("ix_memories_created_at", "created_at"),
        Index("ix_memories_last_accessed", "last_accessed"),
    )


class Experience(BaseModel):
    """Links memories with emotional states and outcomes."""

    __tablename__ = "experiences"

    # Foreign keys
    memory_id: Mapped[int] = mapped_column(ForeignKey("memories.id"))
    emotional_state_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("emotional_states.id")
    )

    # Experience details
    experience_type: Mapped[str] = mapped_column(String(100))
    outcome: Mapped[str] = mapped_column(String(100))  # positive, negative, neutral
    impact_score: Mapped[float] = mapped_column(
        Float, CheckConstraint("impact_score >= -1 AND impact_score <= 1")
    )

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
        Index("ix_experiences_type_outcome", "experience_type", "outcome"),
        Index("ix_experiences_impact_score", "impact_score"),
        Index("ix_experiences_created_at", "created_at"),
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
        Index("ix_consciousness_sessions_status", "status"),
        Index("ix_consciousness_sessions_start_time", "start_time"),
    )
