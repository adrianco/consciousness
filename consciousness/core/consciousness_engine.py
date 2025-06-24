import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_async_session
from ..models.consciousness import ConsciousnessSession
from .decision_engine import DecisionMakingEngine
from .emotion_processor import EmotionProcessor
from .learning_engine import LearningEngine
from .memory_manager import MemoryManager
from .prediction_engine import PredictionEngine
from .query_engine import QueryEngine


class ConsciousnessEngine:
    """Main consciousness orchestrator that coordinates all cognitive processes."""

    def __init__(self):
        self.session_id = None
        self.is_active = False
        self.processing_interval = 5.0  # seconds

        # Core components
        self.emotion_processor: Optional[EmotionProcessor] = None
        self.memory_manager: Optional[MemoryManager] = None
        self.decision_engine: Optional[DecisionMakingEngine] = None
        self.learning_engine: Optional[LearningEngine] = None
        self.query_engine: Optional[QueryEngine] = None
        self.prediction_engine: Optional[PredictionEngine] = None

        # State tracking
        self.current_state = {
            "emotional_state": None,
            "active_memories": [],
            "pending_decisions": [],
            "recent_experiences": [],
            "performance_metrics": {},
        }

        # Metrics
        self.metrics = {
            "events_processed": 0,
            "decisions_made": 0,
            "learning_updates": 0,
            "queries_answered": 0,
            "predictions_made": 0,
        }

    async def initialize(self):
        """Initialize all consciousness components."""
        try:
            self.session_id = f"consciousness_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

            # Get async session generator
            session_gen = get_async_session()
            session = await session_gen.__anext__()

                # Initialize components
                self.emotion_processor = EmotionProcessor(session)
                self.memory_manager = MemoryManager(session)
                self.decision_engine = DecisionMakingEngine(session)
                self.learning_engine = LearningEngine(session)
                self.query_engine = QueryEngine(session)
                self.prediction_engine = PredictionEngine(session)

                # Load initial state
                await self._load_initial_state(session)

                # Create session record
                await self._create_session_record(session)

                self.is_active = True
                print(f"🧠 Consciousness engine initialized - Session: {self.session_id}")
            finally:
                await session.close()
        except Exception as e:
            self.session_id = None
            raise RuntimeError(f"Failed to initialize consciousness engine: {e}")

    async def start(self):
        """Start the consciousness processing loop."""
        if not self.is_active:
            await self.initialize()

        print("🚀 Starting consciousness processing loop...")

        while self.is_active:
            try:
                await self._process_cycle()
                await asyncio.sleep(self.processing_interval)
            except Exception as e:
                print(f"❌ Error in consciousness cycle: {e}")
                await asyncio.sleep(1)  # Brief pause before retry

    async def stop(self):
        """Stop the consciousness engine gracefully."""
        self.is_active = False

        async with get_async_session() as session:
            await self._finalize_session(session)

        print(f"⏹️ Consciousness engine stopped - Session: {self.session_id}")

    async def _process_cycle(self):
        """Single consciousness processing cycle."""
        async with get_async_session() as session:
            # Update components with current session
            for component in [
                self.emotion_processor,
                self.memory_manager,
                self.decision_engine,
                self.learning_engine,
                self.query_engine,
                self.prediction_engine,
            ]:
                component.session = session

            # 1. Process emotions and update state
            emotional_state = await self.emotion_processor.process_current_emotions()
            self.current_state["emotional_state"] = emotional_state

            # 2. Consolidate memories from recent experiences
            await self.memory_manager.consolidate_recent_memories()

            # 3. Evaluate pending decisions
            decisions = await self.decision_engine.process_pending_decisions()
            self.metrics["decisions_made"] += len(decisions)

            # 4. Update learning from feedback
            learning_updates = await self.learning_engine.process_learning_updates()
            self.metrics["learning_updates"] += learning_updates

            # 5. Generate predictions for future states
            predictions = await self.prediction_engine.generate_predictions()
            self.metrics["predictions_made"] += len(predictions)

            # 6. Update performance metrics
            await self._update_performance_metrics()

            self.metrics["events_processed"] += 1

    async def process_query(
        self, query: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Process a natural language query."""
        if not self.is_active:
            return {"error": "Consciousness engine not active"}

        async with get_async_session() as session:
            self.query_engine.session = session
            response = await self.query_engine.process_query(query, context or {})
            self.metrics["queries_answered"] += 1
            return response

    async def get_status(self) -> Dict[str, Any]:
        """Get current consciousness status."""
        return {
            "session_id": self.session_id,
            "is_active": self.is_active,
            "current_state": self.current_state,
            "metrics": self.metrics,
            "uptime": datetime.utcnow().isoformat(),
        }

    async def make_decision(
        self,
        decision_type: str,
        context: Dict[str, Any],
        options: List[Dict[str, Any]],
        urgency: str = "medium",
    ) -> Dict[str, Any]:
        """Make a decision using the decision engine."""
        if not self.is_active:
            return {"error": "Consciousness engine not active"}

        async with get_async_session() as session:
            self.decision_engine.session = session
            decision = await self.decision_engine.make_decision(
                decision_type=decision_type,
                context=context,
                options=options,
                urgency=urgency,
            )
            self.metrics["decisions_made"] += 1
            return decision

    async def learn_from_feedback(
        self, action: str, outcome: str, feedback_score: float, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Learn from feedback using the learning engine."""
        if not self.is_active:
            return {"error": "Consciousness engine not active"}

        async with get_async_session() as session:
            self.learning_engine.session = session
            learning_result = await self.learning_engine.learn_from_feedback(
                action=action,
                outcome=outcome,
                feedback_score=feedback_score,
                context=context,
            )
            self.metrics["learning_updates"] += 1
            return learning_result

    async def store_memory(
        self,
        title: str,
        description: str,
        memory_type: str = "episodic",
        category: str = "general",
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        related_entities: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Store a memory using the memory manager."""
        if not self.is_active:
            return {"error": "Consciousness engine not active"}

        async with get_async_session() as session:
            self.memory_manager.session = session
            memory = await self.memory_manager.store_memory(
                title=title,
                description=description,
                memory_type=memory_type,
                category=category,
                importance=importance,
                tags=tags,
                related_entities=related_entities,
            )
            return {
                "memory_id": memory.id,
                "title": memory.title,
                "importance": memory.importance,
                "created_at": memory.created_at.isoformat(),
            }

    async def predict_future_state(
        self, prediction_type: str, context: Dict[str, Any], timeframe_hours: int = 24
    ) -> Dict[str, Any]:
        """Generate a prediction using the prediction engine."""
        if not self.is_active:
            return {"error": "Consciousness engine not active"}

        async with get_async_session() as session:
            self.prediction_engine.session = session
            prediction = await self.prediction_engine.predict_specific_outcome(
                prediction_type=prediction_type,
                context=context,
                timeframe_hours=timeframe_hours,
            )
            self.metrics["predictions_made"] += 1
            return prediction

    async def get_emotional_state(self) -> Dict[str, Any]:
        """Get current emotional state."""
        if not self.is_active:
            return {"error": "Consciousness engine not active"}

        return self.current_state.get("emotional_state", {})

    async def get_recent_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent memories."""
        if not self.is_active:
            return []

        async with get_async_session() as session:
            self.memory_manager.session = session
            memories = await self.memory_manager.retrieve_memories(limit=limit)

            return [
                {
                    "id": memory.id,
                    "title": memory.title,
                    "description": memory.description,
                    "importance": memory.importance,
                    "created_at": memory.created_at.isoformat(),
                }
                for memory in memories
            ]

    async def get_system_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        if not self.is_active:
            return {"error": "Consciousness engine not active"}

        async with get_async_session() as session:
            # Update component sessions
            for component in [
                self.emotion_processor,
                self.memory_manager,
                self.decision_engine,
                self.learning_engine,
                self.prediction_engine,
            ]:
                component.session = session

            # Gather statistics from all components
            emotion_stats = await self.emotion_processor.get_emotional_history(hours=24)
            memory_stats = await self.memory_manager.get_memory_statistics()
            decision_stats = await self.decision_engine.get_decision_statistics()
            learning_stats = await self.learning_engine.get_learning_statistics()
            prediction_stats = (
                await self.prediction_engine.get_prediction_accuracy_stats()
            )

            return {
                "session_metrics": self.metrics,
                "emotional_states_24h": len(emotion_stats),
                "memory_statistics": memory_stats,
                "decision_statistics": decision_stats,
                "learning_statistics": learning_stats,
                "prediction_statistics": prediction_stats,
                "session_id": self.session_id,
                "uptime_hours": (
                    datetime.utcnow()
                    - datetime.fromisoformat(self.session_id.split("_")[1])
                ).total_seconds()
                / 3600,
            }

    async def _load_initial_state(self, session: AsyncSession):
        """Load initial consciousness state from database."""
        # Load most recent emotional state
        recent_state = await self.emotion_processor.get_current_state()
        if recent_state:
            self.current_state["emotional_state"] = {
                "happiness": recent_state.happiness,
                "worry": recent_state.worry,
                "boredom": recent_state.boredom,
                "excitement": recent_state.excitement,
                "primary_emotion": recent_state.primary_emotion,
                "intensity": recent_state.intensity,
            }

    async def _create_session_record(self, session: AsyncSession):
        """Create database record for consciousness session."""
        session_record = ConsciousnessSession(
            session_id=self.session_id,
            status="active",
            start_time=datetime.utcnow(),
            initial_state=self.current_state,
            performance_metrics=self.metrics,
        )
        session.add(session_record)
        await session.commit()

    async def _finalize_session(self, session: AsyncSession):
        """Finalize consciousness session in database."""
        from sqlalchemy import update

        from ..models.consciousness import ConsciousnessSession

        await session.execute(
            update(ConsciousnessSession)
            .where(ConsciousnessSession.session_id == self.session_id)
            .values(
                status="terminated",
                end_time=datetime.utcnow(),
                final_state=self.current_state,
                events_processed=self.metrics["events_processed"],
                decisions_made=self.metrics["decisions_made"],
                learning_updates=self.metrics["learning_updates"],
                performance_metrics=self.metrics,
            )
        )
        await session.commit()

    async def _update_performance_metrics(self):
        """Update internal performance metrics."""
        # Calculate processing rate (events per minute)
        session_start = datetime.fromisoformat(
            self.session_id.split("_")[1] + "_" + self.session_id.split("_")[2]
        )
        uptime_minutes = (datetime.utcnow() - session_start).total_seconds() / 60

        self.current_state["performance_metrics"] = {
            "processing_rate": self.metrics["events_processed"]
            / max(1, uptime_minutes),
            "decision_efficiency": self.metrics["decisions_made"]
            / max(1, self.metrics["events_processed"]),
            "learning_rate": self.metrics["learning_updates"]
            / max(1, self.metrics["events_processed"]),
            "query_response_rate": self.metrics["queries_answered"],
            "prediction_rate": self.metrics["predictions_made"]
            / max(1, self.metrics["events_processed"]),
        }

    # Additional utility methods for external integration

    async def process_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process an external event through the consciousness system."""
        if not self.is_active:
            return {"error": "Consciousness engine not active"}

        # Store event for processing
        from ..models.events import Event

        async with get_async_session() as session:
            event = Event(
                event_type=event_type,
                category="external",
                severity="medium",
                title=f"External event: {event_type}",
                description=f"Processing {event_type} event",
                source="consciousness_engine",
                event_data=event_data,
                processed=False,
            )
            session.add(event)
            await session.commit()

            # If it's a decision event, process immediately
            if event_type == "pending_decision":
                decision = await self.decision_engine.process_pending_decisions()
                return {"decisions": decision}

            return {"event_id": event.id, "status": "queued_for_processing"}

    async def run_single_cycle(self) -> Dict[str, Any]:
        """Run a single consciousness processing cycle manually."""
        if not self.is_active:
            return {"error": "Consciousness engine not active"}

        await self._process_cycle()
        return {
            "cycle_completed": True,
            "metrics": self.metrics,
            "emotional_state": self.current_state.get("emotional_state"),
            "timestamp": datetime.utcnow().isoformat(),
        }
