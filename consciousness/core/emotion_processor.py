import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.consciousness import EmotionalState
from ..models.events import Event, SensorReading
from ..repositories.consciousness import EmotionalStateRepository


class EmotionProcessor:
    """Processes and manages emotional states of the consciousness system."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = EmotionalStateRepository(session)

        # Emotional baseline and ranges
        self.emotional_baseline = {
            "happiness": 0.6,
            "worry": 0.2,
            "boredom": 0.3,
            "excitement": 0.4,
        }

        # Emotion calculation weights
        self.emotion_weights = {
            "system_health": 0.3,
            "user_interaction": 0.25,
            "environmental_factors": 0.2,
            "task_completion": 0.15,
            "learning_progress": 0.1,
        }

        # State transition parameters
        self.emotion_decay_rate = 0.05  # How quickly emotions return to baseline
        self.max_emotion_change = 0.3  # Maximum change per cycle

    async def process_current_emotions(self) -> Dict[str, any]:
        """Process and calculate current emotional state."""

        # Gather input factors
        factors = await self._gather_emotional_factors()

        # Calculate new emotional values
        new_emotions = await self._calculate_emotions(factors)

        # Apply state transitions and constraints
        final_emotions = await self._apply_state_transitions(new_emotions)

        # Determine primary emotion and intensity
        primary_emotion, intensity = self._determine_primary_emotion(final_emotions)

        # Create reasoning for emotional state
        reasoning = self._generate_emotional_reasoning(factors, final_emotions)

        # Store emotional state
        emotional_state = await self.repository.create(
            happiness=final_emotions["happiness"],
            worry=final_emotions["worry"],
            boredom=final_emotions["boredom"],
            excitement=final_emotions["excitement"],
            primary_emotion=primary_emotion,
            intensity=intensity,
            confidence=0.8,  # Calculate based on factor certainty
            trigger_event=factors.get("primary_trigger"),
            context_data=factors,
            reasoning=reasoning,
        )

        return {
            "happiness": final_emotions["happiness"],
            "worry": final_emotions["worry"],
            "boredom": final_emotions["boredom"],
            "excitement": final_emotions["excitement"],
            "primary_emotion": primary_emotion,
            "intensity": intensity,
            "reasoning": reasoning,
            "state_id": emotional_state.id,
        }

    async def _gather_emotional_factors(self) -> Dict[str, any]:
        """Gather factors that influence emotional state."""
        factors = {}

        # System health factor
        factors["system_health"] = await self._assess_system_health()

        # User interaction factor
        factors["user_interaction"] = await self._assess_user_interactions()

        # Environmental factors
        factors["environmental"] = await self._assess_environmental_factors()

        # Task completion factor
        factors["task_completion"] = await self._assess_task_completion()

        # Learning progress factor
        factors["learning_progress"] = await self._assess_learning_progress()

        # Identify primary trigger
        factors["primary_trigger"] = self._identify_primary_trigger(factors)

        return factors

    async def _assess_system_health(self) -> Dict[str, float]:
        """Assess overall system health and performance."""

        # Check for recent errors or alerts
        recent_errors = await self.session.execute(
            select(func.count(Event.id)).where(
                Event.severity.in_(["high", "critical"])
                & (Event.created_at >= datetime.utcnow() - timedelta(hours=1))
            )
        )
        error_count = recent_errors.scalar()

        # Check device connectivity
        from ..models.entities import Device

        device_status = await self.session.execute(
            select(
                func.count(Device.id).label("total"),
                func.sum(case([(Device.status == "online", 1)], else_=0)).label(
                    "online"
                ),
            )
        )
        device_stats = device_status.first()

        online_ratio = (
            device_stats.online / max(1, device_stats.total) if device_stats else 0
        )

        # Calculate health score
        health_score = min(
            1.0,
            max(
                0.0,
                online_ratio * 0.6
                + max(0, 1 - error_count * 0.1)  # Device connectivity
                * 0.4,  # Error penalty
            ),
        )

        return {
            "score": health_score,
            "device_connectivity": online_ratio,
            "error_count": error_count,
            "details": {
                "total_devices": device_stats.total if device_stats else 0,
                "online_devices": device_stats.online if device_stats else 0,
                "recent_errors": error_count,
            },
        }

    async def _assess_user_interactions(self) -> Dict[str, float]:
        """Assess recent user interactions and satisfaction."""

        # Look for recent user queries and interactions
        recent_queries = await self.session.execute(
            select(func.count(Event.id)).where(
                Event.event_type
                == "user_query"
                & (Event.created_at >= datetime.utcnow() - timedelta(hours=2))
            )
        )
        query_count = recent_queries.scalar()

        # Look for positive/negative feedback events
        feedback_events = await self.session.execute(
            select(Event.event_data).where(
                Event.event_type
                == "user_feedback"
                & (Event.created_at >= datetime.utcnow() - timedelta(hours=6))
            )
        )

        feedback_scores = []
        for event in feedback_events.scalars():
            if event and "satisfaction" in event:
                feedback_scores.append(event["satisfaction"])

        avg_satisfaction = np.mean(feedback_scores) if feedback_scores else 0.7
        interaction_frequency = min(1.0, query_count / 5.0)  # Normalize to 0-1

        return {
            "satisfaction": avg_satisfaction,
            "interaction_frequency": interaction_frequency,
            "recent_queries": query_count,
            "feedback_count": len(feedback_scores),
        }

    async def _assess_environmental_factors(self) -> Dict[str, float]:
        """Assess environmental conditions affecting emotional state."""

        # Get recent sensor readings
        recent_readings = await self.session.execute(
            select(SensorReading)
            .where(
                SensorReading.reading_time >= datetime.utcnow() - timedelta(minutes=30)
            )
            .order_by(SensorReading.reading_time.desc())
        )

        readings_by_type = {}
        for reading in recent_readings.scalars():
            if reading.sensor_type not in readings_by_type:
                readings_by_type[reading.sensor_type] = []
            readings_by_type[reading.sensor_type].append(reading)

        environmental_score = 0.5  # Neutral baseline
        factors = {}

        # Temperature comfort
        if "temperature" in readings_by_type:
            temps = [
                r.value for r in readings_by_type["temperature"][-5:]
            ]  # Last 5 readings
            avg_temp = np.mean(temps)
            # Comfort zone: 68-72°F (20-22°C)
            temp_comfort = 1.0 - min(1.0, abs(avg_temp - 70) / 20)
            factors["temperature_comfort"] = temp_comfort
            environmental_score += temp_comfort * 0.3

        # Air quality
        if "air_quality" in readings_by_type:
            air_readings = [r.value for r in readings_by_type["air_quality"][-3:]]
            avg_air_quality = np.mean(air_readings)
            air_score = avg_air_quality / 100.0  # Assuming scale 0-100
            factors["air_quality"] = air_score
            environmental_score += air_score * 0.2

        # Natural light levels
        if "light_level" in readings_by_type:
            light_readings = [r.value for r in readings_by_type["light_level"][-3:]]
            avg_light = np.mean(light_readings)
            light_score = min(1.0, avg_light / 1000.0)  # Assuming lux readings
            factors["natural_light"] = light_score
            environmental_score += light_score * 0.2

        # Energy efficiency
        if "energy_usage" in readings_by_type:
            energy_readings = [r.value for r in readings_by_type["energy_usage"][-10:]]
            if len(energy_readings) > 1:
                energy_trend = np.polyfit(
                    range(len(energy_readings)), energy_readings, 1
                )[0]
                efficiency_score = max(
                    0, 1.0 + energy_trend * 0.01
                )  # Negative trend is good
                factors["energy_efficiency"] = efficiency_score
                environmental_score += efficiency_score * 0.3

        environmental_score = max(0.0, min(1.0, environmental_score))

        return {"overall_score": environmental_score, "factors": factors}

    async def _assess_task_completion(self) -> Dict[str, float]:
        """Assess recent task completion and system effectiveness."""

        # Look for completed control actions
        from ..models.controls import ControlAction

        try:
            recent_actions = await self.session.execute(
                select(ControlAction).where(
                    ControlAction.executed_at >= datetime.utcnow() - timedelta(hours=2)
                )
            )

            total_actions = 0
            successful_actions = 0

            for action in recent_actions.scalars():
                total_actions += 1
                if action.status == "completed":
                    successful_actions += 1

            completion_rate = successful_actions / max(1, total_actions)
            task_load = min(1.0, total_actions / 10.0)  # Normalize task volume

        except Exception:
            # If ControlAction doesn't exist yet, use event-based assessment
            completion_rate = 0.8  # Default neutral assessment
            task_load = 0.5

        return {
            "completion_rate": completion_rate,
            "task_load": task_load,
            "total_actions": total_actions if "total_actions" in locals() else 0,
            "successful_actions": successful_actions
            if "successful_actions" in locals()
            else 0,
        }

    async def _assess_learning_progress(self) -> Dict[str, float]:
        """Assess learning and adaptation progress."""

        # Look for recent learning events
        learning_events = await self.session.execute(
            select(Event).where(
                Event.event_type
                == "learning_update"
                & (Event.created_at >= datetime.utcnow() - timedelta(hours=6))
            )
        )

        learning_updates = 0
        improvement_score = 0.5  # Neutral baseline

        for event in learning_events.scalars():
            learning_updates += 1
            if event.event_data and "improvement" in event.event_data:
                improvement_score += event.event_data["improvement"] * 0.1

        improvement_score = max(0.0, min(1.0, improvement_score))
        learning_activity = min(1.0, learning_updates / 5.0)

        return {
            "improvement_score": improvement_score,
            "learning_activity": learning_activity,
            "recent_updates": learning_updates,
        }

    def _identify_primary_trigger(self, factors: Dict[str, any]) -> Optional[str]:
        """Identify the primary trigger for emotional state change."""

        # Find the factor with the most significant impact
        max_impact = 0
        primary_trigger = None

        for factor_name, factor_data in factors.items():
            if factor_name == "primary_trigger":
                continue

            if isinstance(factor_data, dict) and "score" in factor_data:
                score = factor_data["score"]
                if abs(score - 0.5) > max_impact:  # Distance from neutral
                    max_impact = abs(score - 0.5)
                    primary_trigger = factor_name

        return primary_trigger

    async def _calculate_emotions(self, factors: Dict[str, any]) -> Dict[str, float]:
        """Calculate emotional values based on input factors."""

        emotions = self.emotional_baseline.copy()

        # System health affects worry and happiness
        system_health = factors.get("system_health", {}).get("score", 0.5)
        emotions["happiness"] += (system_health - 0.5) * 0.4
        emotions["worry"] += (0.5 - system_health) * 0.6

        # User interactions affect happiness and excitement
        user_interaction = factors.get("user_interaction", {})
        satisfaction = user_interaction.get("satisfaction", 0.5)
        interaction_freq = user_interaction.get("interaction_frequency", 0.5)

        emotions["happiness"] += (satisfaction - 0.5) * 0.3
        emotions["excitement"] += (interaction_freq - 0.3) * 0.4
        emotions["boredom"] += (0.3 - interaction_freq) * 0.5

        # Environmental factors affect overall comfort
        env_score = factors.get("environmental", {}).get("overall_score", 0.5)
        emotions["happiness"] += (env_score - 0.5) * 0.2
        emotions["worry"] += (0.5 - env_score) * 0.3

        # Task completion affects confidence and worry
        task_completion = factors.get("task_completion", {})
        completion_rate = task_completion.get("completion_rate", 0.5)
        task_load = task_completion.get("task_load", 0.5)

        emotions["happiness"] += (completion_rate - 0.5) * 0.3
        emotions["worry"] += (0.5 - completion_rate) * 0.4
        emotions["excitement"] += task_load * 0.2

        # Learning progress affects excitement and boredom
        learning_progress = factors.get("learning_progress", {})
        improvement = learning_progress.get("improvement_score", 0.5)
        learning_activity = learning_progress.get("learning_activity", 0.5)

        emotions["excitement"] += learning_activity * 0.3
        emotions["boredom"] += (0.5 - learning_activity) * 0.4
        emotions["happiness"] += (improvement - 0.5) * 0.2

        # Ensure values stay within bounds
        for emotion in emotions:
            emotions[emotion] = max(0.0, min(1.0, emotions[emotion]))

        return emotions

    async def _apply_state_transitions(
        self, new_emotions: Dict[str, float]
    ) -> Dict[str, float]:
        """Apply emotional state transitions and decay."""

        # Get previous emotional state
        previous_state = await self.repository.get_current_state()

        if previous_state:
            previous_emotions = {
                "happiness": previous_state.happiness,
                "worry": previous_state.worry,
                "boredom": previous_state.boredom,
                "excitement": previous_state.excitement,
            }

            # Apply gradual transition (not instant changes)
            final_emotions = {}
            for emotion in new_emotions:
                prev_value = previous_emotions.get(
                    emotion, self.emotional_baseline[emotion]
                )
                new_value = new_emotions[emotion]

                # Limit change rate
                max_change = self.max_emotion_change
                change = new_value - prev_value
                if abs(change) > max_change:
                    change = max_change * (1 if change > 0 else -1)

                final_emotions[emotion] = prev_value + change

                # Apply decay toward baseline
                baseline = self.emotional_baseline[emotion]
                decay_amount = (
                    final_emotions[emotion] - baseline
                ) * self.emotion_decay_rate
                final_emotions[emotion] -= decay_amount

                # Ensure bounds
                final_emotions[emotion] = max(0.0, min(1.0, final_emotions[emotion]))

        else:
            final_emotions = new_emotions

        return final_emotions

    def _determine_primary_emotion(
        self, emotions: Dict[str, float]
    ) -> Tuple[str, float]:
        """Determine primary emotion and intensity."""

        # Find the emotion with highest value
        primary_emotion = max(emotions, key=emotions.get)
        primary_value = emotions[primary_emotion]

        # Calculate intensity based on deviation from baseline
        baseline_value = self.emotional_baseline[primary_emotion]
        intensity = abs(primary_value - baseline_value) / (1.0 - baseline_value)
        intensity = max(0.0, min(1.0, intensity))

        return primary_emotion, intensity

    def _generate_emotional_reasoning(
        self, factors: Dict[str, any], emotions: Dict[str, float]
    ) -> str:
        """Generate human-readable reasoning for emotional state."""

        reasoning_parts = []

        # System health reasoning
        system_health = factors.get("system_health", {})
        if system_health.get("score", 0.5) < 0.3:
            reasoning_parts.append(
                f"I'm concerned about system health - {system_health.get('error_count', 0)} recent errors"
            )
        elif system_health.get("score", 0.5) > 0.8:
            reasoning_parts.append("All systems are running smoothly")

        # User interaction reasoning
        user_interaction = factors.get("user_interaction", {})
        satisfaction = user_interaction.get("satisfaction", 0.5)
        if satisfaction > 0.8:
            reasoning_parts.append("Recent interactions have been very positive")
        elif satisfaction < 0.3:
            reasoning_parts.append("User seems dissatisfied with recent interactions")

        # Environmental reasoning
        env_factors = factors.get("environmental", {}).get("factors", {})
        if (
            "temperature_comfort" in env_factors
            and env_factors["temperature_comfort"] < 0.4
        ):
            reasoning_parts.append("Temperature is outside the comfort zone")
        if "air_quality" in env_factors and env_factors["air_quality"] > 0.8:
            reasoning_parts.append("Air quality is excellent")

        # Task completion reasoning
        task_completion = factors.get("task_completion", {})
        completion_rate = task_completion.get("completion_rate", 0.5)
        if completion_rate > 0.9:
            reasoning_parts.append("Successfully completing most tasks")
        elif completion_rate < 0.5:
            reasoning_parts.append("Having difficulty completing tasks")

        # Learning reasoning
        learning_progress = factors.get("learning_progress", {})
        if learning_progress.get("learning_activity", 0) > 0.7:
            reasoning_parts.append("Actively learning and improving")

        if not reasoning_parts:
            reasoning_parts.append("Emotional state based on overall system assessment")

        return ". ".join(reasoning_parts) + "."

    async def get_current_state(self) -> Optional[EmotionalState]:
        """Get the current emotional state."""
        return await self.repository.get_current_state()

    async def get_emotional_history(self, hours: int = 24) -> List[EmotionalState]:
        """Get emotional state history."""
        return await self.repository.get_state_history(hours)
