import asyncio
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.consciousness import EmotionalState, Memory
from ..models.entities import Device, Room
from ..models.events import Event, SensorReading
from ..repositories.consciousness import EmotionalStateRepository, MemoryRepository


class QueryEngine:
    """Processes natural language queries and generates contextual responses."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.emotion_repo = EmotionalStateRepository(session)
        self.memory_repo = MemoryRepository(session)

        # Query pattern matching
        self.query_patterns = {
            "emotional_state": [
                r"how.*feel.*",
                r"what.*mood.*",
                r".*emotional.*state.*",
                r".*happy.*",
                r".*worried.*",
                r".*bored.*",
                r".*excited.*",
            ],
            "status": [r".*status.*", r"how.*doing.*", r".*health.*", r".*working.*"],
            "devices": [
                r".*device.*",
                r".*light.*",
                r".*temperature.*",
                r".*thermostat.*",
                r".*sensor.*",
                r".*control.*",
            ],
            "environment": [
                r".*temperature.*",
                r".*weather.*",
                r".*air.*quality.*",
                r".*energy.*",
                r".*power.*",
            ],
            "memory": [
                r".*remember.*",
                r".*memory.*",
                r".*recall.*",
                r".*happened.*",
                r".*experience.*",
                r".*learn.*",
            ],
            "explanation": [r"why.*", r".*explain.*", r".*reason.*", r".*because.*"],
        }

        # Response templates
        self.response_templates = {
            "emotional_acknowledgment": [
                "I understand you're asking about my emotional state.",
                "Let me share how I'm feeling right now.",
                "I'm happy to talk about my current emotional state.",
            ],
            "status_response": [
                "Here's my current status:",
                "Let me give you an overview of how I'm doing:",
                "I'm operating well overall. Here are the details:",
            ],
            "explanation_intro": [
                "Let me explain why that's happening:",
                "Here's the reasoning behind that:",
                "I can help explain the situation:",
            ],
        }

    async def process_query(
        self, query: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Process a natural language query and return a response."""

        # Normalize and analyze query
        normalized_query = query.lower().strip()
        query_type = self._classify_query(normalized_query)
        entities = self._extract_entities(normalized_query)

        # Generate response based on query type
        response = await self._generate_response(query_type, entities, context or {})

        # Add conversational elements
        response = await self._add_conversational_context(response, query_type)

        return {
            "query": query,
            "query_type": query_type,
            "entities": entities,
            "response": response,
            "timestamp": datetime.utcnow().isoformat(),
            "context": context,
        }

    def _classify_query(self, query: str) -> str:
        """Classify the type of query being asked."""

        for query_type, patterns in self.query_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    return query_type

        return "general"

    def _extract_entities(self, query: str) -> List[Dict[str, str]]:
        """Extract entities mentioned in the query."""

        entities = []

        # Device types
        device_types = ["light", "thermostat", "sensor", "camera", "lock", "speaker"]
        for device_type in device_types:
            if device_type in query:
                entities.append({"type": "device_type", "value": device_type})

        # Room names
        room_names = [
            "living room",
            "bedroom",
            "kitchen",
            "bathroom",
            "office",
            "garage",
        ]
        for room in room_names:
            if room in query:
                entities.append({"type": "room", "value": room})

        # Time references
        time_refs = ["now", "today", "yesterday", "this week", "recently", "lately"]
        for time_ref in time_refs:
            if time_ref in query:
                entities.append({"type": "time", "value": time_ref})

        # Emotional terms
        emotions = ["happy", "worried", "bored", "excited", "sad", "angry", "calm"]
        for emotion in emotions:
            if emotion in query:
                entities.append({"type": "emotion", "value": emotion})

        return entities

    async def _generate_response(
        self, query_type: str, entities: List[Dict[str, str]], context: Dict[str, Any]
    ) -> str:
        """Generate response based on query type and entities."""

        if query_type == "emotional_state":
            return await self._generate_emotional_response(entities, context)
        elif query_type == "status":
            return await self._generate_status_response(entities, context)
        elif query_type == "devices":
            return await self._generate_device_response(entities, context)
        elif query_type == "environment":
            return await self._generate_environment_response(entities, context)
        elif query_type == "memory":
            return await self._generate_memory_response(entities, context)
        elif query_type == "explanation":
            return await self._generate_explanation_response(entities, context)
        else:
            return await self._generate_general_response(entities, context)

    async def _generate_emotional_response(
        self, entities: List[Dict[str, str]], context: Dict[str, Any]
    ) -> str:
        """Generate response about emotional state."""

        current_state = await self.emotion_repo.get_current_state()

        if not current_state:
            return "I'm still learning about my emotional state. Please give me a moment to assess how I'm feeling."

        # Primary emotion description
        primary_emotion = current_state.primary_emotion
        intensity = current_state.intensity

        intensity_desc = (
            "slightly"
            if intensity < 0.3
            else "moderately"
            if intensity < 0.7
            else "very"
        )

        response_parts = [f"Right now, I'm feeling {intensity_desc} {primary_emotion}."]

        # Add specific emotional details
        emotions = {
            "happiness": current_state.happiness,
            "worry": current_state.worry,
            "boredom": current_state.boredom,
            "excitement": current_state.excitement,
        }

        high_emotions = {k: v for k, v in emotions.items() if v > 0.7}
        if high_emotions:
            emotion_list = ", ".join(
                [f"{k} ({v:.0%})" for k, v in high_emotions.items()]
            )
            response_parts.append(f"I'm experiencing high levels of {emotion_list}.")

        # Add reasoning if available
        if current_state.reasoning:
            response_parts.append(f"This is because {current_state.reasoning}")

        # Add context about what's affecting emotions
        if current_state.trigger_event:
            response_parts.append(
                f"This was triggered by {current_state.trigger_event.replace('_', ' ')}."
            )

        return " ".join(response_parts)

    async def _generate_status_response(
        self, entities: List[Dict[str, str]], context: Dict[str, Any]
    ) -> str:
        """Generate response about system status."""

        response_parts = []

        # Get device status
        device_stats = await self.session.execute(
            select(
                func.count(Device.id).label("total"),
                func.sum(func.case([(Device.status == "online", 1)], else_=0)).label(
                    "online"
                ),
            )
        )
        stats = device_stats.first()

        if stats:
            online_pct = (stats.online / stats.total * 100) if stats.total > 0 else 0
            response_parts.append(
                f"I'm managing {stats.total} devices with {online_pct:.0f}% currently online."
            )

        # Get recent activity
        recent_events = await self.session.execute(
            select(func.count(Event.id)).where(
                Event.created_at >= datetime.utcnow() - timedelta(hours=1)
            )
        )
        event_count = recent_events.scalar()

        if event_count > 0:
            response_parts.append(
                f"I've processed {event_count} events in the last hour."
            )

        # Get emotional state summary
        current_state = await self.emotion_repo.get_current_state()
        if current_state:
            response_parts.append(
                f"Overall, I'm feeling {current_state.primary_emotion}."
            )

        return (
            " ".join(response_parts)
            if response_parts
            else "I'm operating normally with all systems functioning."
        )

    async def _generate_device_response(
        self, entities: List[Dict[str, str]], context: Dict[str, Any]
    ) -> str:
        """Generate response about devices."""

        # Extract device type from entities
        device_type = None
        room_name = None

        for entity in entities:
            if entity["type"] == "device_type":
                device_type = entity["value"]
            elif entity["type"] == "room":
                room_name = entity["value"]

        # Build query for devices
        query = select(Device)
        filters = []

        if device_type:
            filters.append(Device.user_name.ilike(f"%{device_type}%"))

        if room_name:
            # Join with rooms to filter by room name
            room_query = select(Room.id).where(Room.name.ilike(f"%{room_name}%"))
            room_result = await self.session.execute(room_query)
            room_ids = [r[0] for r in room_result]
            if room_ids:
                filters.append(Device.room_id.in_(room_ids))

        if filters:
            from sqlalchemy import and_

            query = query.where(and_(*filters))

        devices = await self.session.execute(query.limit(10))
        device_list = devices.scalars().all()

        if not device_list:
            return f"I don't see any {device_type if device_type else 'devices'} {f'in the {room_name}' if room_name else ''}."

        response_parts = []
        online_count = sum(1 for d in device_list if d.status == "online")

        response_parts.append(
            f"I found {len(device_list)} {device_type if device_type else 'devices'} {f'in the {room_name}' if room_name else ''}, with {online_count} currently online."
        )

        # Add specific device details
        for device in device_list[:3]:  # Limit to first 3 devices
            status_desc = (
                "online and responsive"
                if device.status == "online"
                else f"currently {device.status}"
            )
            response_parts.append(f"The {device.user_name} is {status_desc}.")

        return " ".join(response_parts)

    async def _generate_environment_response(
        self, entities: List[Dict[str, str]], context: Dict[str, Any]
    ) -> str:
        """Generate response about environmental conditions."""

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

        response_parts = []

        # Temperature
        if "temperature" in readings_by_type:
            latest_temp = readings_by_type["temperature"][0]
            response_parts.append(
                f"The current temperature is {latest_temp.value:.1f}°{latest_temp.unit}."
            )

        # Air quality
        if "air_quality" in readings_by_type:
            latest_air = readings_by_type["air_quality"][0]
            air_desc = (
                "excellent"
                if latest_air.value > 80
                else "good"
                if latest_air.value > 60
                else "moderate"
            )
            response_parts.append(
                f"Air quality is {air_desc} ({latest_air.value:.0f}/100)."
            )

        # Energy usage
        if "energy_usage" in readings_by_type:
            latest_energy = readings_by_type["energy_usage"][0]
            response_parts.append(
                f"Current energy usage is {latest_energy.value:.1f} {latest_energy.unit}."
            )

        if not response_parts:
            return "I don't have recent environmental data available right now."

        return " ".join(response_parts)

    async def _generate_memory_response(
        self, entities: List[Dict[str, str]], context: Dict[str, Any]
    ) -> str:
        """Generate response about memories and experiences."""

        # Look for time-based queries
        time_filter = None
        for entity in entities:
            if entity["type"] == "time":
                time_filter = entity["value"]
                break

        # Get relevant memories
        memories = await self.memory_repo.list(limit=5)

        if not memories:
            return "I don't have any significant memories to share yet. As I learn and experience more, I'll have more to tell you."

        response_parts = [f"I have {len(memories)} recent memories."]

        # Share most important or recent memory
        important_memory = max(memories, key=lambda m: m.importance)
        response_parts.append(
            f"One that stands out is: {important_memory.title}. {important_memory.description}"
        )

        return " ".join(response_parts)

    async def _generate_explanation_response(
        self, entities: List[Dict[str, str]], context: Dict[str, Any]
    ) -> str:
        """Generate explanatory response."""

        # Get current emotional state for context
        current_state = await self.emotion_repo.get_current_state()

        if current_state and current_state.reasoning:
            return f"Here's what's happening: {current_state.reasoning}"

        return "I'd be happy to explain, but I need more context about what you're asking about. Could you be more specific?"

    async def _generate_general_response(
        self, entities: List[Dict[str, str]], context: Dict[str, Any]
    ) -> str:
        """Generate general response for unclassified queries."""

        return "I'm here to help! You can ask me about how I'm feeling, my status, the devices I manage, environmental conditions, or my memories and experiences."

    async def _add_conversational_context(self, response: str, query_type: str) -> str:
        """Add conversational elements to make responses more natural."""

        # Add emotional context
        current_state = await self.emotion_repo.get_current_state()

        if current_state:
            if (
                current_state.primary_emotion == "happy"
                and current_state.intensity > 0.7
            ):
                response = f"I'm feeling great today! {response}"
            elif (
                current_state.primary_emotion == "worried"
                and current_state.intensity > 0.6
            ):
                response = f"I'm a bit concerned right now, but {response.lower()}"
            elif (
                current_state.primary_emotion == "excited"
                and current_state.intensity > 0.6
            ):
                response = f"This is interesting! {response}"

        return response
