import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.consciousness import EmotionalState, Experience, Memory
from ..models.entities import Device
from ..models.events import ControlAction, Event
from ..repositories.consciousness import EmotionalStateRepository, MemoryRepository


class LearningEngine:
    """Manages learning, adaptation, and behavioral improvement through experience."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.memory_repo = MemoryRepository(session)
        self.emotion_repo = EmotionalStateRepository(session)

        # Learning configuration
        self.learning_types = {
            "pattern_recognition": {
                "description": "Learning patterns from sensor data and user behavior",
                "weight": 0.3,
                "confidence_threshold": 0.7,
            },
            "behavior_adaptation": {
                "description": "Adapting behavior based on outcomes and feedback",
                "weight": 0.25,
                "confidence_threshold": 0.8,
            },
            "efficiency_optimization": {
                "description": "Optimizing system efficiency and performance",
                "weight": 0.2,
                "confidence_threshold": 0.75,
            },
            "user_preference_learning": {
                "description": "Learning user preferences and habits",
                "weight": 0.15,
                "confidence_threshold": 0.9,
            },
            "error_correction": {
                "description": "Learning from errors and failures",
                "weight": 0.1,
                "confidence_threshold": 0.6,
            },
        }

        # Learning parameters
        self.min_experiences_for_learning = 3
        self.learning_rate = 0.1
        self.confidence_decay_rate = 0.05
        self.max_learning_updates_per_cycle = 10

        # Performance tracking
        self.performance_metrics = {
            "successful_predictions": 0,
            "failed_predictions": 0,
            "behavior_improvements": 0,
            "pattern_discoveries": 0,
            "efficiency_gains": 0,
        }

    async def process_learning_updates(self) -> int:
        """Process all pending learning updates and adaptations."""

        learning_updates = 0

        # Pattern recognition learning
        pattern_updates = await self._learn_patterns()
        learning_updates += pattern_updates

        # Behavior adaptation learning
        behavior_updates = await self._adapt_behaviors()
        learning_updates += behavior_updates

        # Efficiency optimization learning
        efficiency_updates = await self._optimize_efficiency()
        learning_updates += efficiency_updates

        # User preference learning
        preference_updates = await self._learn_user_preferences()
        learning_updates += preference_updates

        # Error correction learning
        error_updates = await self._learn_from_errors()
        learning_updates += error_updates

        # Update learning performance metrics
        await self._update_learning_metrics()

        # Store learning insights as memories
        if learning_updates > 0:
            await self._store_learning_insights(learning_updates)

        return learning_updates

    async def learn_from_experience(
        self,
        experience_data: Dict[str, Any],
        outcome: str,
        emotional_state: Optional[EmotionalState] = None,
    ) -> Dict[str, Any]:
        """Learn from a specific experience with known outcome."""

        learning_result = {
            "patterns_discovered": [],
            "behaviors_adapted": [],
            "insights_gained": [],
            "confidence_updates": {},
            "recommendations": [],
        }

        # Classify the learning opportunity
        learning_type = self._classify_learning_opportunity(experience_data, outcome)

        # Extract learning insights
        insights = await self._extract_learning_insights(
            experience_data, outcome, emotional_state
        )
        learning_result["insights_gained"] = insights

        # Update behavior patterns
        behavior_updates = await self._update_behavior_patterns(
            experience_data, outcome, insights
        )
        learning_result["behaviors_adapted"] = behavior_updates

        # Discover new patterns
        patterns = await self._discover_patterns(experience_data, outcome)
        learning_result["patterns_discovered"] = patterns

        # Update confidence levels
        confidence_updates = await self._update_confidence_levels(
            experience_data, outcome
        )
        learning_result["confidence_updates"] = confidence_updates

        # Generate recommendations
        recommendations = await self._generate_learning_recommendations(learning_result)
        learning_result["recommendations"] = recommendations

        # Store as learning memory
        await self._create_learning_memory(experience_data, outcome, learning_result)

        return learning_result

    async def get_learning_insights(
        self, domain: str = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve recent learning insights, optionally filtered by domain."""

        # Search for learning-related memories
        learning_memories = await self.memory_repo.search_memories(
            query="learning", memory_type="procedural", limit=limit
        )

        insights = []
        for memory in learning_memories:
            if domain and domain not in memory.tags:
                continue

            insight = {
                "title": memory.title,
                "description": memory.description,
                "importance": memory.importance,
                "confidence": memory.confidence,
                "tags": memory.tags,
                "created_at": memory.created_at.isoformat(),
                "content": memory.content,
            }
            insights.append(insight)

        return insights

    async def predict_learning_opportunity(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Predict potential learning opportunities based on current context."""

        prediction = {
            "opportunity_score": 0.0,
            "learning_type": None,
            "potential_insights": [],
            "recommended_actions": [],
            "confidence": 0.0,
        }

        # Analyze current context for learning potential
        context_analysis = await self._analyze_context_for_learning(context)

        # Calculate opportunity score
        opportunity_score = await self._calculate_learning_opportunity_score(
            context_analysis
        )
        prediction["opportunity_score"] = opportunity_score

        # Determine learning type
        if opportunity_score > 0.7:
            learning_type = await self._identify_primary_learning_type(context_analysis)
            prediction["learning_type"] = learning_type

            # Generate potential insights
            insights = await self._predict_potential_insights(
                context_analysis, learning_type
            )
            prediction["potential_insights"] = insights

            # Recommend actions
            actions = await self._recommend_learning_actions(
                context_analysis, learning_type
            )
            prediction["recommended_actions"] = actions

            prediction["confidence"] = min(0.9, opportunity_score * 1.2)

        return prediction

    async def _learn_patterns(self) -> int:
        """Learn patterns from recent experiences and sensor data."""

        pattern_updates = 0

        # Get recent experiences with positive outcomes
        recent_experiences = await self._get_recent_experiences(
            outcome_filter="positive", days=7
        )

        if len(recent_experiences) < self.min_experiences_for_learning:
            return 0

        # Group experiences by type and context
        experience_groups = self._group_experiences_by_pattern(recent_experiences)

        for pattern_type, experiences in experience_groups.items():
            if len(experiences) >= self.min_experiences_for_learning:
                # Discover pattern
                pattern = await self._analyze_experience_pattern(experiences)

                if (
                    pattern["confidence"]
                    > self.learning_types["pattern_recognition"]["confidence_threshold"]
                ):
                    # Store pattern as learning memory
                    await self._store_pattern_memory(pattern_type, pattern, experiences)
                    pattern_updates += 1
                    self.performance_metrics["pattern_discoveries"] += 1

        return pattern_updates

    async def _adapt_behaviors(self) -> int:
        """Adapt behaviors based on recent feedback and outcomes."""

        behavior_updates = 0

        # Get recent experiences with clear outcomes
        recent_experiences = await self._get_recent_experiences(days=3)

        # Analyze outcome patterns
        outcome_analysis = await self._analyze_outcome_patterns(recent_experiences)

        for behavior_context, analysis in outcome_analysis.items():
            if analysis["sample_size"] >= self.min_experiences_for_learning:
                # Calculate success rate
                success_rate = (
                    analysis["positive_outcomes"] / analysis["total_outcomes"]
                )

                if success_rate < 0.6:  # Poor performance, adapt behavior
                    adaptation = await self._generate_behavior_adaptation(
                        behavior_context, analysis
                    )

                    if (
                        adaptation["confidence"]
                        > self.learning_types["behavior_adaptation"][
                            "confidence_threshold"
                        ]
                    ):
                        # Store adaptation as learning memory
                        await self._store_adaptation_memory(
                            behavior_context, adaptation, analysis
                        )
                        behavior_updates += 1
                        self.performance_metrics["behavior_improvements"] += 1

        return behavior_updates

    async def _optimize_efficiency(self) -> int:
        """Learn efficiency optimizations from system performance data."""

        efficiency_updates = 0

        # Analyze recent control actions and their efficiency
        recent_actions = await self._get_recent_control_actions(days=7)

        if len(recent_actions) < self.min_experiences_for_learning:
            return 0

        # Group actions by device and action type
        action_groups = self._group_control_actions(recent_actions)

        for group_key, actions in action_groups.items():
            if len(actions) >= self.min_experiences_for_learning:
                # Analyze efficiency metrics
                efficiency_analysis = await self._analyze_action_efficiency(actions)

                if efficiency_analysis["improvement_potential"] > 0.2:
                    # Generate efficiency optimization
                    optimization = await self._generate_efficiency_optimization(
                        group_key, efficiency_analysis
                    )

                    if (
                        optimization["confidence"]
                        > self.learning_types["efficiency_optimization"][
                            "confidence_threshold"
                        ]
                    ):
                        # Store optimization as learning memory
                        await self._store_efficiency_memory(
                            group_key, optimization, efficiency_analysis
                        )
                        efficiency_updates += 1
                        self.performance_metrics["efficiency_gains"] += 1

        return efficiency_updates

    async def _learn_user_preferences(self) -> int:
        """Learn user preferences from interaction patterns."""

        preference_updates = 0

        # Get recent user interactions
        user_interactions = await self._get_recent_user_interactions(days=14)

        if len(user_interactions) < self.min_experiences_for_learning:
            return 0

        # Analyze preference patterns
        preference_patterns = await self._analyze_preference_patterns(user_interactions)

        for preference_type, pattern in preference_patterns.items():
            if (
                pattern["confidence"]
                > self.learning_types["user_preference_learning"][
                    "confidence_threshold"
                ]
            ):
                # Store preference as learning memory
                await self._store_preference_memory(preference_type, pattern)
                preference_updates += 1

        return preference_updates

    async def _learn_from_errors(self) -> int:
        """Learn from errors and system failures."""

        error_updates = 0

        # Get recent error events
        error_events = await self._get_recent_error_events(days=7)

        for error_event in error_events:
            # Analyze error context and causes
            error_analysis = await self._analyze_error_context(error_event)

            # Generate error prevention strategy
            prevention_strategy = await self._generate_error_prevention(error_analysis)

            if (
                prevention_strategy["confidence"]
                > self.learning_types["error_correction"]["confidence_threshold"]
            ):
                # Store error learning as memory
                await self._store_error_learning_memory(
                    error_event, error_analysis, prevention_strategy
                )
                error_updates += 1

        return error_updates

    async def _get_recent_experiences(
        self, outcome_filter: str = None, days: int = 7
    ) -> List[Experience]:
        """Get recent experiences, optionally filtered by outcome."""

        cutoff_time = datetime.utcnow() - timedelta(days=days)
        query = select(Experience).where(Experience.created_at >= cutoff_time)

        if outcome_filter:
            query = query.where(Experience.outcome == outcome_filter)

        result = await self.session.execute(
            query.order_by(Experience.created_at.desc()).limit(100)
        )
        return result.scalars().all()

    async def _get_recent_control_actions(self, days: int = 7) -> List[ControlAction]:
        """Get recent control actions for efficiency analysis."""

        cutoff_time = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(ControlAction)
            .where(ControlAction.executed_at >= cutoff_time)
            .order_by(ControlAction.executed_at.desc())
            .limit(200)
        )
        return result.scalars().all()

    async def _get_recent_user_interactions(self, days: int = 14) -> List[Event]:
        """Get recent user interaction events."""

        cutoff_time = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(Event)
            .where(
                and_(Event.event_type == "user_query", Event.created_at >= cutoff_time)
            )
            .order_by(Event.created_at.desc())
            .limit(100)
        )
        return result.scalars().all()

    async def _get_recent_error_events(self, days: int = 7) -> List[Event]:
        """Get recent error events for learning."""

        cutoff_time = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(Event)
            .where(
                and_(
                    Event.severity.in_(["high", "critical"]),
                    Event.created_at >= cutoff_time,
                )
            )
            .order_by(Event.created_at.desc())
            .limit(50)
        )
        return result.scalars().all()

    def _group_experiences_by_pattern(
        self, experiences: List[Experience]
    ) -> Dict[str, List[Experience]]:
        """Group experiences by potential patterns."""

        groups = {}

        for experience in experiences:
            # Group by experience type and context
            pattern_key = f"{experience.experience_type}_{experience.outcome}"

            # Add context from experience context
            if experience.context:
                if "device_type" in experience.context:
                    pattern_key += f"_{experience.context['device_type']}"
                if "time_of_day" in experience.context:
                    hour = experience.created_at.hour
                    time_period = (
                        "morning"
                        if 6 <= hour < 12
                        else "afternoon"
                        if 12 <= hour < 18
                        else "evening"
                        if 18 <= hour < 22
                        else "night"
                    )
                    pattern_key += f"_{time_period}"

            if pattern_key not in groups:
                groups[pattern_key] = []
            groups[pattern_key].append(experience)

        return groups

    async def _analyze_experience_pattern(
        self, experiences: List[Experience]
    ) -> Dict[str, Any]:
        """Analyze a group of experiences to discover patterns."""

        pattern = {
            "type": experiences[0].experience_type,
            "sample_size": len(experiences),
            "success_rate": sum(1 for e in experiences if e.outcome == "positive")
            / len(experiences),
            "average_impact": np.mean([e.impact_score for e in experiences]),
            "common_contexts": {},
            "temporal_patterns": {},
            "confidence": 0.0,
        }

        # Analyze common contexts
        all_contexts = [e.context for e in experiences if e.context]
        if all_contexts:
            context_keys = set()
            for context in all_contexts:
                context_keys.update(context.keys())

            for key in context_keys:
                values = [
                    context.get(key) for context in all_contexts if context.get(key)
                ]
                if values:
                    most_common = max(set(values), key=values.count)
                    frequency = values.count(most_common) / len(values)
                    if frequency > 0.6:  # Strong pattern
                        pattern["common_contexts"][key] = {
                            "value": most_common,
                            "frequency": frequency,
                        }

        # Analyze temporal patterns
        hours = [e.created_at.hour for e in experiences]
        hour_counts = {}
        for hour in hours:
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        if hour_counts:
            peak_hour = max(hour_counts, key=hour_counts.get)
            peak_frequency = hour_counts[peak_hour] / len(hours)
            if peak_frequency > 0.3:
                pattern["temporal_patterns"]["peak_hour"] = {
                    "hour": peak_hour,
                    "frequency": peak_frequency,
                }

        # Calculate confidence
        confidence_factors = [
            pattern["sample_size"] / 10.0,  # More samples = higher confidence
            pattern["success_rate"],  # Higher success rate = higher confidence
            len(pattern["common_contexts"])
            * 0.1,  # More common contexts = higher confidence
            len(pattern["temporal_patterns"])
            * 0.1,  # Temporal patterns = higher confidence
        ]

        pattern["confidence"] = min(
            1.0, sum(confidence_factors) / len(confidence_factors)
        )

        return pattern

    async def _analyze_outcome_patterns(
        self, experiences: List[Experience]
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze patterns in experience outcomes."""

        outcome_analysis = {}

        # Group by behavior context
        behavior_contexts = {}
        for experience in experiences:
            context_key = experience.experience_type
            if experience.context and "behavior_context" in experience.context:
                context_key = experience.context["behavior_context"]

            if context_key not in behavior_contexts:
                behavior_contexts[context_key] = []
            behavior_contexts[context_key].append(experience)

        # Analyze each context
        for context, context_experiences in behavior_contexts.items():
            if len(context_experiences) >= 2:
                positive_outcomes = sum(
                    1 for e in context_experiences if e.outcome == "positive"
                )
                total_outcomes = len(context_experiences)

                outcome_analysis[context] = {
                    "total_outcomes": total_outcomes,
                    "positive_outcomes": positive_outcomes,
                    "negative_outcomes": total_outcomes - positive_outcomes,
                    "success_rate": positive_outcomes / total_outcomes,
                    "average_impact": np.mean(
                        [e.impact_score for e in context_experiences]
                    ),
                    "sample_size": total_outcomes,
                }

        return outcome_analysis

    async def _generate_behavior_adaptation(
        self, behavior_context: str, analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate behavior adaptation based on outcome analysis."""

        adaptation = {
            "context": behavior_context,
            "current_success_rate": analysis["success_rate"],
            "recommended_changes": [],
            "confidence": 0.0,
            "expected_improvement": 0.0,
        }

        # Generate specific recommendations based on context
        if "device" in behavior_context.lower():
            adaptation["recommended_changes"].append(
                {
                    "type": "timing_adjustment",
                    "description": "Adjust device operation timing based on usage patterns",
                    "expected_impact": 0.2,
                }
            )

        if "user_interaction" in behavior_context.lower():
            adaptation["recommended_changes"].append(
                {
                    "type": "response_optimization",
                    "description": "Optimize response strategy based on user feedback patterns",
                    "expected_impact": 0.15,
                }
            )

        if analysis["average_impact"] < 0:
            adaptation["recommended_changes"].append(
                {
                    "type": "risk_mitigation",
                    "description": "Implement additional safety checks to reduce negative impacts",
                    "expected_impact": 0.3,
                }
            )

        # Calculate confidence and expected improvement
        if adaptation["recommended_changes"]:
            adaptation["expected_improvement"] = np.mean(
                [
                    change["expected_impact"]
                    for change in adaptation["recommended_changes"]
                ]
            )
            adaptation["confidence"] = min(
                0.9, (1 - analysis["success_rate"]) * adaptation["expected_improvement"]
            )

        return adaptation

    def _group_control_actions(
        self, actions: List[ControlAction]
    ) -> Dict[str, List[ControlAction]]:
        """Group control actions for efficiency analysis."""

        groups = {}

        for action in actions:
            # Group by device and action type
            group_key = f"{action.device_id}_{action.action_type}"

            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(action)

        return groups

    async def _analyze_action_efficiency(
        self, actions: List[ControlAction]
    ) -> Dict[str, Any]:
        """Analyze efficiency of control actions."""

        analysis = {
            "total_actions": len(actions),
            "successful_actions": sum(1 for a in actions if a.status == "completed"),
            "average_execution_time": 0.0,
            "improvement_potential": 0.0,
            "efficiency_score": 0.0,
        }

        # Calculate execution time metrics
        execution_times = []
        for action in actions:
            if action.executed_at and action.created_at:
                exec_time = (action.executed_at - action.created_at).total_seconds()
                execution_times.append(exec_time)

        if execution_times:
            analysis["average_execution_time"] = np.mean(execution_times)
            analysis["execution_time_variance"] = np.var(execution_times)

            # High variance suggests optimization opportunity
            if analysis["execution_time_variance"] > analysis["average_execution_time"]:
                analysis["improvement_potential"] = 0.3
            elif analysis["average_execution_time"] > 10:  # Slow actions
                analysis["improvement_potential"] = 0.2

        # Calculate efficiency score
        success_rate = analysis["successful_actions"] / analysis["total_actions"]
        time_efficiency = 1.0 / (
            1.0 + analysis["average_execution_time"] / 5.0
        )  # Normalize around 5 seconds

        analysis["efficiency_score"] = (success_rate + time_efficiency) / 2.0

        if analysis["efficiency_score"] < 0.7:
            analysis["improvement_potential"] = max(
                analysis["improvement_potential"], 0.8 - analysis["efficiency_score"]
            )

        return analysis

    async def _generate_efficiency_optimization(
        self, group_key: str, analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate efficiency optimization recommendations."""

        optimization = {
            "group": group_key,
            "current_efficiency": analysis["efficiency_score"],
            "optimizations": [],
            "confidence": 0.0,
            "expected_improvement": analysis["improvement_potential"],
        }

        # Generate specific optimizations
        if analysis["average_execution_time"] > 5:
            optimization["optimizations"].append(
                {
                    "type": "execution_speed",
                    "description": "Optimize action execution to reduce response time",
                    "target_improvement": min(
                        0.3, analysis["average_execution_time"] / 10.0
                    ),
                }
            )

        if analysis["successful_actions"] / analysis["total_actions"] < 0.9:
            optimization["optimizations"].append(
                {
                    "type": "reliability",
                    "description": "Improve action reliability through better error handling",
                    "target_improvement": 0.2,
                }
            )

        if (
            analysis.get("execution_time_variance", 0)
            > analysis["average_execution_time"]
        ):
            optimization["optimizations"].append(
                {
                    "type": "consistency",
                    "description": "Reduce execution time variance for more consistent performance",
                    "target_improvement": 0.15,
                }
            )

        # Calculate confidence
        optimization["confidence"] = min(
            0.9, analysis["improvement_potential"] * (analysis["total_actions"] / 10.0)
        )

        return optimization

    async def _analyze_preference_patterns(
        self, interactions: List[Event]
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze user preference patterns from interactions."""

        patterns = {}

        # Analyze timing preferences
        hours = [interaction.created_at.hour for interaction in interactions]
        hour_counts = {}
        for hour in hours:
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        if hour_counts:
            peak_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[
                :3
            ]
            total_interactions = len(interactions)

            if peak_hours[0][1] / total_interactions > 0.2:  # Significant preference
                patterns["timing_preference"] = {
                    "preferred_hours": [hour for hour, count in peak_hours],
                    "confidence": peak_hours[0][1] / total_interactions,
                    "pattern_strength": sum(count for _, count in peak_hours)
                    / total_interactions,
                }

        # Analyze interaction type preferences
        interaction_types = {}
        for interaction in interactions:
            if interaction.event_data and "query_type" in interaction.event_data:
                query_type = interaction.event_data["query_type"]
                interaction_types[query_type] = interaction_types.get(query_type, 0) + 1

        if interaction_types:
            total_types = sum(interaction_types.values())
            preferred_types = [
                (t, c) for t, c in interaction_types.items() if c / total_types > 0.2
            ]

            if preferred_types:
                patterns["interaction_preference"] = {
                    "preferred_types": [t for t, _ in preferred_types],
                    "confidence": max(c for _, c in preferred_types) / total_types,
                    "type_distribution": interaction_types,
                }

        return patterns

    async def _analyze_error_context(self, error_event: Event) -> Dict[str, Any]:
        """Analyze the context of an error event."""

        analysis = {
            "error_type": error_event.event_type,
            "severity": error_event.severity,
            "context": error_event.event_data or {},
            "timestamp": error_event.created_at,
            "related_events": [],
            "potential_causes": [],
            "prevention_strategies": [],
        }

        # Look for related events around the error time
        time_window = timedelta(minutes=30)
        related_events = await self.session.execute(
            select(Event)
            .where(
                and_(
                    Event.created_at >= error_event.created_at - time_window,
                    Event.created_at <= error_event.created_at + time_window,
                    Event.id != error_event.id,
                )
            )
            .limit(10)
        )

        analysis["related_events"] = [
            {
                "event_type": event.event_type,
                "severity": event.severity,
                "time_offset": (
                    event.created_at - error_event.created_at
                ).total_seconds(),
            }
            for event in related_events.scalars()
        ]

        # Identify potential causes based on context
        if "device_id" in analysis["context"]:
            analysis["potential_causes"].append("device_malfunction")

        if "network" in error_event.event_type.lower():
            analysis["potential_causes"].append("connectivity_issue")

        if len(analysis["related_events"]) > 3:
            analysis["potential_causes"].append("system_overload")

        return analysis

    async def _generate_error_prevention(
        self, error_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate error prevention strategies."""

        prevention = {
            "error_type": error_analysis["error_type"],
            "strategies": [],
            "confidence": 0.0,
            "priority": "medium",
        }

        # Generate strategies based on potential causes
        for cause in error_analysis["potential_causes"]:
            if cause == "device_malfunction":
                prevention["strategies"].append(
                    {
                        "type": "device_monitoring",
                        "description": "Implement enhanced device health monitoring",
                        "implementation": "Add device status checks before critical operations",
                    }
                )

            elif cause == "connectivity_issue":
                prevention["strategies"].append(
                    {
                        "type": "connectivity_resilience",
                        "description": "Improve network connectivity resilience",
                        "implementation": "Add connection retry logic and offline mode fallbacks",
                    }
                )

            elif cause == "system_overload":
                prevention["strategies"].append(
                    {
                        "type": "load_management",
                        "description": "Implement better system load management",
                        "implementation": "Add request queuing and rate limiting",
                    }
                )

        # Set priority based on severity
        if error_analysis["severity"] == "critical":
            prevention["priority"] = "high"
            prevention["confidence"] = 0.8
        elif error_analysis["severity"] == "high":
            prevention["priority"] = "medium"
            prevention["confidence"] = 0.7
        else:
            prevention["confidence"] = 0.6

        return prevention

    async def _store_pattern_memory(
        self, pattern_type: str, pattern: Dict[str, Any], experiences: List[Experience]
    ):
        """Store discovered pattern as a learning memory."""

        memory_data = {
            "event_type": "pattern_discovery",
            "pattern_type": pattern_type,
            "pattern_data": pattern,
            "source_experiences": [e.id for e in experiences],
            "discovery_date": datetime.utcnow().isoformat(),
            "learning_type": "pattern_recognition",
        }

        await self.memory_repo.create(
            memory_type="procedural",
            category="pattern_learning",
            importance=pattern["confidence"],
            title=f"Pattern Discovery: {pattern_type}",
            description=f"Discovered pattern with {pattern['confidence']:.1%} confidence from {pattern['sample_size']} experiences",
            content=memory_data,
            source="learning_engine",
            confidence=pattern["confidence"],
            tags=["learning", "pattern", pattern_type],
            related_entities=[],
        )

    async def _store_adaptation_memory(
        self,
        behavior_context: str,
        adaptation: Dict[str, Any],
        analysis: Dict[str, Any],
    ):
        """Store behavior adaptation as a learning memory."""

        memory_data = {
            "event_type": "behavior_adaptation",
            "behavior_context": behavior_context,
            "adaptation_data": adaptation,
            "analysis": analysis,
            "adaptation_date": datetime.utcnow().isoformat(),
            "learning_type": "behavior_adaptation",
        }

        await self.memory_repo.create(
            memory_type="procedural",
            category="behavior_learning",
            importance=adaptation["confidence"],
            title=f"Behavior Adaptation: {behavior_context}",
            description=f"Adapted behavior with {adaptation['expected_improvement']:.1%} expected improvement",
            content=memory_data,
            source="learning_engine",
            confidence=adaptation["confidence"],
            tags=["learning", "adaptation", "behavior"],
            related_entities=[behavior_context],
        )

    async def _store_efficiency_memory(
        self, group_key: str, optimization: Dict[str, Any], analysis: Dict[str, Any]
    ):
        """Store efficiency optimization as a learning memory."""

        memory_data = {
            "event_type": "efficiency_optimization",
            "group_key": group_key,
            "optimization_data": optimization,
            "analysis": analysis,
            "optimization_date": datetime.utcnow().isoformat(),
            "learning_type": "efficiency_optimization",
        }

        await self.memory_repo.create(
            memory_type="procedural",
            category="efficiency_learning",
            importance=optimization["confidence"],
            title=f"Efficiency Optimization: {group_key}",
            description=f"Optimization with {optimization['expected_improvement']:.1%} expected improvement",
            content=memory_data,
            source="learning_engine",
            confidence=optimization["confidence"],
            tags=["learning", "efficiency", "optimization"],
            related_entities=[group_key],
        )

    async def _store_preference_memory(
        self, preference_type: str, pattern: Dict[str, Any]
    ):
        """Store learned user preference as memory."""

        memory_data = {
            "event_type": "preference_learning",
            "preference_type": preference_type,
            "pattern_data": pattern,
            "learning_date": datetime.utcnow().isoformat(),
            "learning_type": "user_preference_learning",
        }

        await self.memory_repo.create(
            memory_type="semantic",
            category="user_preferences",
            importance=pattern["confidence"],
            title=f"User Preference: {preference_type}",
            description=f"Learned user preference with {pattern['confidence']:.1%} confidence",
            content=memory_data,
            source="learning_engine",
            confidence=pattern["confidence"],
            tags=["learning", "preferences", "user"],
            related_entities=["user_preferences"],
        )

    async def _store_error_learning_memory(
        self, error_event: Event, analysis: Dict[str, Any], prevention: Dict[str, Any]
    ):
        """Store error learning as memory."""

        memory_data = {
            "event_type": "error_learning",
            "original_error": {
                "id": error_event.id,
                "type": error_event.event_type,
                "severity": error_event.severity,
            },
            "analysis": analysis,
            "prevention_strategy": prevention,
            "learning_date": datetime.utcnow().isoformat(),
            "learning_type": "error_correction",
        }

        await self.memory_repo.create(
            memory_type="procedural",
            category="error_learning",
            importance=prevention["confidence"],
            title=f"Error Learning: {error_event.event_type}",
            description=f"Learned from error with {len(prevention['strategies'])} prevention strategies",
            content=memory_data,
            source="learning_engine",
            confidence=prevention["confidence"],
            tags=["learning", "error", "prevention"],
            related_entities=[error_event.event_type],
        )

    async def _create_learning_memory(
        self,
        experience_data: Dict[str, Any],
        outcome: str,
        learning_result: Dict[str, Any],
    ):
        """Create a memory from a learning experience."""

        memory_data = {
            "event_type": "learning_experience",
            "original_experience": experience_data,
            "outcome": outcome,
            "learning_result": learning_result,
            "learning_date": datetime.utcnow().isoformat(),
        }

        # Calculate importance from learning result
        importance = 0.5
        if learning_result["patterns_discovered"]:
            importance += 0.2
        if learning_result["behaviors_adapted"]:
            importance += 0.2
        if learning_result["insights_gained"]:
            importance += len(learning_result["insights_gained"]) * 0.1

        importance = min(1.0, importance)

        await self.memory_repo.create(
            memory_type="procedural",
            category="learning_experience",
            importance=importance,
            title=f"Learning Experience: {experience_data.get('event_type', 'Unknown')}",
            description=f"Learning from {outcome} outcome with {len(learning_result['insights_gained'])} insights gained",
            content=memory_data,
            source="learning_engine",
            confidence=0.8,
            tags=["learning", "experience", outcome],
            related_entities=[],
        )

    async def _store_learning_insights(self, update_count: int):
        """Store summary of learning updates as memory."""

        insight_data = {
            "event_type": "learning_cycle_summary",
            "updates_processed": update_count,
            "performance_metrics": self.performance_metrics.copy(),
            "cycle_date": datetime.utcnow().isoformat(),
        }

        await self.memory_repo.create(
            memory_type="semantic",
            category="learning_progress",
            importance=min(1.0, update_count * 0.1),
            title=f"Learning Cycle: {update_count} Updates",
            description=f"Processed {update_count} learning updates with performance improvements",
            content=insight_data,
            source="learning_engine",
            confidence=0.9,
            tags=["learning", "progress", "cycle"],
            related_entities=["learning_engine"],
        )

    async def _update_learning_metrics(self):
        """Update learning performance metrics."""

        # Store metrics in event log
        metrics_event = Event(
            event_type="learning_metrics_update",
            severity="info",
            event_data=self.performance_metrics.copy(),
        )

        self.session.add(metrics_event)
        await self.session.commit()

    def _classify_learning_opportunity(
        self, experience_data: Dict[str, Any], outcome: str
    ) -> str:
        """Classify the type of learning opportunity."""

        # Determine learning type based on experience characteristics
        if "pattern" in experience_data.get("event_type", "").lower():
            return "pattern_recognition"
        elif "user" in experience_data.get("source", "").lower():
            return "user_preference_learning"
        elif "error" in outcome or "failure" in outcome:
            return "error_correction"
        elif "efficiency" in experience_data.get("event_type", ""):
            return "efficiency_optimization"
        else:
            return "behavior_adaptation"

    async def _extract_learning_insights(
        self,
        experience_data: Dict[str, Any],
        outcome: str,
        emotional_state: Optional[EmotionalState],
    ) -> List[str]:
        """Extract learning insights from experience."""

        insights = []

        # Outcome-based insights
        if outcome == "positive":
            insights.append(
                f"Successful strategy: {experience_data.get('event_type', 'Unknown action')}"
            )
            if emotional_state and emotional_state.happiness > 0.7:
                insights.append("Action resulted in positive emotional state")
        elif outcome == "negative":
            insights.append(
                f"Strategy to avoid: {experience_data.get('event_type', 'Unknown action')}"
            )
            if emotional_state and emotional_state.worry > 0.6:
                insights.append("Action caused worry - implement prevention measures")

        # Context-based insights
        if "timing" in experience_data:
            insights.append(
                f"Timing impact: {experience_data['timing']} timing affects outcomes"
            )

        if "device_type" in experience_data:
            insights.append(
                f"Device-specific learning for {experience_data['device_type']}"
            )

        return insights

    async def _update_behavior_patterns(
        self, experience_data: Dict[str, Any], outcome: str, insights: List[str]
    ) -> List[str]:
        """Update behavior patterns based on experience."""

        updates = []

        # Update success/failure patterns
        behavior_key = experience_data.get("event_type", "unknown")

        if outcome == "positive":
            updates.append(f"Reinforced positive behavior pattern for {behavior_key}")
        elif outcome == "negative":
            updates.append(f"Marked behavior pattern {behavior_key} for adaptation")

        return updates

    async def _discover_patterns(
        self, experience_data: Dict[str, Any], outcome: str
    ) -> List[str]:
        """Discover new patterns from experience."""

        patterns = []

        # Time-based patterns
        current_hour = datetime.utcnow().hour
        if "timing_pattern" not in experience_data:
            patterns.append(
                f"Potential time pattern: {outcome} outcome at hour {current_hour}"
            )

        # Context patterns
        if "context" in experience_data:
            context = experience_data["context"]
            for key, value in context.items():
                patterns.append(
                    f"Context pattern: {key}={value} correlates with {outcome} outcome"
                )

        return patterns

    async def _update_confidence_levels(
        self, experience_data: Dict[str, Any], outcome: str
    ) -> Dict[str, float]:
        """Update confidence levels based on experience outcome."""

        updates = {}

        action_type = experience_data.get("event_type", "unknown")

        if outcome == "positive":
            # Increase confidence for successful actions
            updates[f"{action_type}_confidence"] = 0.1
        elif outcome == "negative":
            # Decrease confidence for failed actions
            updates[f"{action_type}_confidence"] = -0.1

        return updates

    async def _generate_learning_recommendations(
        self, learning_result: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on learning results."""

        recommendations = []

        if learning_result["patterns_discovered"]:
            recommendations.append(
                "Apply discovered patterns to improve future decision-making"
            )

        if learning_result["behaviors_adapted"]:
            recommendations.append("Test adapted behaviors in controlled scenarios")

        if learning_result["confidence_updates"]:
            recommendations.append(
                "Monitor confidence level changes and adjust strategies accordingly"
            )

        return recommendations

    async def _analyze_context_for_learning(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze context for learning opportunities."""

        analysis = {
            "novelty_score": 0.0,
            "complexity_score": 0.0,
            "uncertainty_score": 0.0,
            "potential_impact": 0.0,
        }

        # Assess novelty
        context_keys = set(context.keys())
        if len(context_keys) > 3:
            analysis["novelty_score"] = 0.7

        # Assess complexity
        nested_values = sum(1 for v in context.values() if isinstance(v, (dict, list)))
        analysis["complexity_score"] = min(1.0, nested_values * 0.3)

        # Assess uncertainty
        if "confidence" in context and context["confidence"] < 0.7:
            analysis["uncertainty_score"] = 1.0 - context["confidence"]

        # Assess potential impact
        if "priority" in context:
            priority_map = {"high": 0.9, "medium": 0.6, "low": 0.3}
            analysis["potential_impact"] = priority_map.get(context["priority"], 0.5)

        return analysis

    async def _calculate_learning_opportunity_score(
        self, context_analysis: Dict[str, Any]
    ) -> float:
        """Calculate overall learning opportunity score."""

        weights = {
            "novelty_score": 0.3,
            "complexity_score": 0.2,
            "uncertainty_score": 0.3,
            "potential_impact": 0.2,
        }

        total_score = 0.0
        for factor, score in context_analysis.items():
            weight = weights.get(factor, 0.0)
            total_score += score * weight

        return min(1.0, total_score)

    async def _identify_primary_learning_type(
        self, context_analysis: Dict[str, Any]
    ) -> str:
        """Identify the primary learning type for the opportunity."""

        if context_analysis["novelty_score"] > 0.7:
            return "pattern_recognition"
        elif context_analysis["uncertainty_score"] > 0.6:
            return "behavior_adaptation"
        elif context_analysis["complexity_score"] > 0.5:
            return "efficiency_optimization"
        else:
            return "user_preference_learning"

    async def _predict_potential_insights(
        self, context_analysis: Dict[str, Any], learning_type: str
    ) -> List[str]:
        """Predict potential insights from learning opportunity."""

        insights = []

        if learning_type == "pattern_recognition":
            insights.append("May discover new behavioral patterns")
            insights.append("Could identify temporal correlations")

        elif learning_type == "behavior_adaptation":
            insights.append("Could improve response strategies")
            insights.append("May optimize decision-making processes")

        elif learning_type == "efficiency_optimization":
            insights.append("Potential for performance improvements")
            insights.append("Could reduce resource consumption")

        return insights

    async def _recommend_learning_actions(
        self, context_analysis: Dict[str, Any], learning_type: str
    ) -> List[str]:
        """Recommend actions to maximize learning from opportunity."""

        actions = []

        actions.append("Monitor outcomes closely for learning signals")
        actions.append("Record detailed context information")

        if learning_type == "pattern_recognition":
            actions.append("Collect data across multiple similar scenarios")

        elif learning_type == "behavior_adaptation":
            actions.append("Test multiple approaches and compare results")

        elif learning_type == "efficiency_optimization":
            actions.append("Measure performance metrics before and after changes")

        return actions
