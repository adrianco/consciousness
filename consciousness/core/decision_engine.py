import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.consciousness import EmotionalState, Experience, Memory
from ..models.entities import Device
from ..models.events import ControlAction, Event
from ..repositories.consciousness import EmotionalStateRepository, MemoryRepository


class DecisionMakingEngine:
    """Manages decision processing, reasoning, and outcome tracking."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.memory_repo = MemoryRepository(session)
        self.emotion_repo = EmotionalStateRepository(session)

        # Decision framework configuration
        self.decision_criteria = {
            "safety": {
                "weight": 0.3,
                "description": "Safety and risk assessment",
                "threshold": 0.8,
            },
            "user_satisfaction": {
                "weight": 0.25,
                "description": "Impact on user happiness and satisfaction",
                "threshold": 0.7,
            },
            "efficiency": {
                "weight": 0.2,
                "description": "Resource efficiency and performance",
                "threshold": 0.6,
            },
            "learning_value": {
                "weight": 0.15,
                "description": "Potential for learning and improvement",
                "threshold": 0.5,
            },
            "system_stability": {
                "weight": 0.1,
                "description": "Impact on overall system stability",
                "threshold": 0.8,
            },
        }

        # Decision types and their characteristics
        self.decision_types = {
            "device_control": {
                "timeout": 30,  # seconds
                "requires_confirmation": False,
                "reversible": True,
                "impact_level": "low",
            },
            "system_configuration": {
                "timeout": 300,  # 5 minutes
                "requires_confirmation": True,
                "reversible": True,
                "impact_level": "medium",
            },
            "security_action": {
                "timeout": 10,  # immediate
                "requires_confirmation": False,
                "reversible": False,
                "impact_level": "high",
            },
            "user_response": {
                "timeout": 60,  # 1 minute
                "requires_confirmation": False,
                "reversible": False,
                "impact_level": "low",
            },
            "learning_adaptation": {
                "timeout": 600,  # 10 minutes
                "requires_confirmation": True,
                "reversible": True,
                "impact_level": "medium",
            },
        }

        # Decision confidence thresholds
        self.confidence_thresholds = {
            "high_confidence": 0.8,
            "medium_confidence": 0.6,
            "low_confidence": 0.4,
            "uncertain": 0.2,
        }

        # Pending decisions tracking
        self.pending_decisions = []
        self.decision_history = []

        # Performance metrics
        self.decision_metrics = {
            "total_decisions": 0,
            "successful_decisions": 0,
            "failed_decisions": 0,
            "high_confidence_accuracy": 0.0,
            "average_decision_time": 0.0,
        }

    async def process_pending_decisions(self) -> List[Dict[str, Any]]:
        """Process all pending decisions and return completed decisions."""

        completed_decisions = []

        # Get pending decisions from memory/database
        pending_decisions = await self._get_pending_decisions()

        for decision_context in pending_decisions:
            try:
                # Check if decision is still valid/relevant
                if await self._is_decision_still_relevant(decision_context):
                    # Process the decision
                    decision_result = await self.make_decision(
                        decision_context["context"],
                        decision_context["options"],
                        decision_context.get("constraints", {}),
                        decision_context.get("decision_type", "general"),
                    )

                    # Execute the decision if confidence is sufficient
                    if (
                        decision_result["confidence"]
                        >= self.confidence_thresholds["low_confidence"]
                    ):
                        execution_result = await self._execute_decision(
                            decision_result, decision_context
                        )
                        decision_result["execution_result"] = execution_result

                        # Store decision and outcome
                        await self._store_decision_outcome(
                            decision_result, decision_context
                        )

                        completed_decisions.append(decision_result)
                    else:
                        # Decision confidence too low, defer or request guidance
                        await self._defer_decision(decision_context, decision_result)

                # Remove from pending list
                await self._remove_pending_decision(decision_context["id"])

            except Exception as e:
                print(
                    f"Error processing decision {decision_context.get('id', 'unknown')}: {e}"
                )
                await self._handle_decision_error(decision_context, str(e))

        return completed_decisions

    async def make_decision(
        self,
        context: Dict[str, Any],
        options: List[Dict[str, Any]],
        constraints: Dict[str, Any] = None,
        decision_type: str = "general",
    ) -> Dict[str, Any]:
        """Make a decision given context, options, and constraints."""

        decision_start_time = datetime.utcnow()

        # Initialize decision framework
        decision_result = {
            "decision_id": f"decision_{decision_start_time.strftime('%Y%m%d_%H%M%S_%f')}",
            "context": context,
            "options": options,
            "constraints": constraints or {},
            "decision_type": decision_type,
            "chosen_option": None,
            "confidence": 0.0,
            "reasoning": [],
            "criteria_scores": {},
            "risk_assessment": {},
            "alternatives_considered": len(options),
            "decision_time": 0.0,
            "timestamp": decision_start_time.isoformat(),
        }

        # Analyze each option against decision criteria
        option_analyses = []
        for option in options:
            analysis = await self._analyze_option(
                option, context, constraints, decision_type
            )
            option_analyses.append(analysis)

        # Calculate overall scores for each option
        scored_options = await self._score_options(option_analyses, decision_type)

        # Select the best option
        best_option = await self._select_best_option(scored_options, context)

        # Build reasoning and confidence
        reasoning = await self._build_decision_reasoning(
            best_option, scored_options, context
        )
        confidence = await self._calculate_decision_confidence(
            best_option, scored_options, context
        )

        # Perform risk assessment
        risk_assessment = await self._assess_decision_risk(
            best_option, context, decision_type
        )

        # Finalize decision result
        decision_result.update(
            {
                "chosen_option": best_option["option"],
                "confidence": confidence,
                "reasoning": reasoning,
                "criteria_scores": best_option["scores"],
                "risk_assessment": risk_assessment,
                "decision_time": (
                    datetime.utcnow() - decision_start_time
                ).total_seconds(),
            }
        )

        # Learn from the decision-making process
        await self._learn_from_decision_process(decision_result, option_analyses)

        return decision_result

    async def evaluate_decision_outcome(
        self,
        decision_id: str,
        actual_outcome: Dict[str, Any],
        success_metrics: Dict[str, float] = None,
    ) -> Dict[str, Any]:
        """Evaluate the outcome of a previous decision for learning."""

        # Retrieve the original decision
        original_decision = await self._get_decision_by_id(decision_id)

        if not original_decision:
            return {"error": "Decision not found"}

        # Calculate outcome evaluation
        evaluation = {
            "decision_id": decision_id,
            "predicted_outcome": original_decision.get("expected_outcome", {}),
            "actual_outcome": actual_outcome,
            "success_metrics": success_metrics or {},
            "accuracy_score": 0.0,
            "lessons_learned": [],
            "improvement_suggestions": [],
            "confidence_calibration": 0.0,
        }

        # Compare predicted vs actual outcomes
        accuracy_score = await self._calculate_outcome_accuracy(
            original_decision.get("expected_outcome", {}), actual_outcome
        )
        evaluation["accuracy_score"] = accuracy_score

        # Assess confidence calibration
        confidence_calibration = await self._assess_confidence_calibration(
            original_decision["confidence"], accuracy_score
        )
        evaluation["confidence_calibration"] = confidence_calibration

        # Extract lessons learned
        lessons = await self._extract_decision_lessons(
            original_decision, actual_outcome, accuracy_score
        )
        evaluation["lessons_learned"] = lessons

        # Generate improvement suggestions
        improvements = await self._generate_decision_improvements(
            original_decision, evaluation
        )
        evaluation["improvement_suggestions"] = improvements

        # Update decision metrics
        await self._update_decision_metrics(original_decision, evaluation)

        # Store evaluation for future learning
        await self._store_decision_evaluation(evaluation)

        return evaluation

    async def get_decision_reasoning(self, decision_id: str) -> Dict[str, Any]:
        """Get detailed reasoning for a specific decision."""

        decision = await self._get_decision_by_id(decision_id)

        if not decision:
            return {"error": "Decision not found"}

        # Enhance reasoning with additional context
        enhanced_reasoning = {
            "decision_id": decision_id,
            "basic_reasoning": decision.get("reasoning", []),
            "criteria_breakdown": decision.get("criteria_scores", {}),
            "risk_factors": decision.get("risk_assessment", {}),
            "alternative_analysis": [],
            "confidence_factors": [],
            "supporting_memories": [],
            "emotional_context": {},
        }

        # Get supporting memories that influenced the decision
        supporting_memories = await self._get_supporting_memories(decision)
        enhanced_reasoning["supporting_memories"] = supporting_memories

        # Get emotional context at decision time
        emotional_context = await self._get_decision_emotional_context(decision)
        enhanced_reasoning["emotional_context"] = emotional_context

        # Analyze confidence factors
        confidence_factors = await self._analyze_confidence_factors(decision)
        enhanced_reasoning["confidence_factors"] = confidence_factors

        return enhanced_reasoning

    async def _get_pending_decisions(self) -> List[Dict[str, Any]]:
        """Retrieve pending decisions from storage."""

        # Look for pending decision events
        pending_events = await self.session.execute(
            select(Event)
            .where(
                and_(
                    Event.event_type == "pending_decision",
                    Event.created_at
                    >= datetime.utcnow() - timedelta(hours=24),  # Only recent decisions
                )
            )
            .order_by(Event.created_at.asc())
        )

        pending_decisions = []
        for event in pending_events.scalars():
            if event.event_data:
                decision_context = event.event_data.copy()
                decision_context["id"] = event.id
                decision_context["created_at"] = event.created_at
                pending_decisions.append(decision_context)

        return pending_decisions

    async def _is_decision_still_relevant(
        self, decision_context: Dict[str, Any]
    ) -> bool:
        """Check if a pending decision is still relevant."""

        # Check timeout
        decision_type = decision_context.get("decision_type", "general")
        timeout_seconds = self.decision_types.get(decision_type, {}).get("timeout", 300)

        created_at = decision_context.get("created_at", datetime.utcnow())
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        if (datetime.utcnow() - created_at).total_seconds() > timeout_seconds:
            return False

        # Check if context is still valid
        context = decision_context.get("context", {})

        # For device control decisions, check if device is still available
        if decision_type == "device_control" and "device_id" in context:
            device = await self.session.execute(
                select(Device).where(Device.id == context["device_id"])
            )
            device_obj = device.scalar_one_or_none()
            if not device_obj or device_obj.status != "online":
                return False

        return True

    async def _analyze_option(
        self,
        option: Dict[str, Any],
        context: Dict[str, Any],
        constraints: Dict[str, Any],
        decision_type: str,
    ) -> Dict[str, Any]:
        """Analyze a single option against decision criteria."""

        analysis = {
            "option": option,
            "scores": {},
            "feasibility": 1.0,
            "risks": [],
            "benefits": [],
            "resource_requirements": {},
            "time_estimate": 0.0,
        }

        # Evaluate each decision criterion
        for criterion, config in self.decision_criteria.items():
            score = await self._evaluate_criterion(
                option, context, criterion, decision_type
            )
            analysis["scores"][criterion] = score

        # Check feasibility against constraints
        feasibility = await self._check_feasibility(option, constraints, context)
        analysis["feasibility"] = feasibility

        # Identify risks and benefits
        risks = await self._identify_option_risks(option, context, decision_type)
        benefits = await self._identify_option_benefits(option, context, decision_type)

        analysis["risks"] = risks
        analysis["benefits"] = benefits

        # Estimate resource requirements
        resources = await self._estimate_resource_requirements(option, context)
        analysis["resource_requirements"] = resources

        # Estimate time to completion
        time_estimate = await self._estimate_completion_time(
            option, context, decision_type
        )
        analysis["time_estimate"] = time_estimate

        return analysis

    async def _evaluate_criterion(
        self,
        option: Dict[str, Any],
        context: Dict[str, Any],
        criterion: str,
        decision_type: str,
    ) -> float:
        """Evaluate an option against a specific criterion."""

        if criterion == "safety":
            return await self._evaluate_safety(option, context, decision_type)
        elif criterion == "user_satisfaction":
            return await self._evaluate_user_satisfaction(option, context)
        elif criterion == "efficiency":
            return await self._evaluate_efficiency(option, context)
        elif criterion == "learning_value":
            return await self._evaluate_learning_value(option, context)
        elif criterion == "system_stability":
            return await self._evaluate_system_stability(option, context)
        else:
            return 0.5  # Neutral score for unknown criteria

    async def _evaluate_safety(
        self, option: Dict[str, Any], context: Dict[str, Any], decision_type: str
    ) -> float:
        """Evaluate safety aspects of an option."""

        safety_score = 0.8  # Base safety score

        # Check for known risk factors
        action_type = option.get("action_type", "").lower()

        # High-risk actions
        if any(
            risk in action_type for risk in ["delete", "disable", "shutdown", "reset"]
        ):
            safety_score -= 0.3

        # Security-related actions
        if decision_type == "security_action":
            safety_score += 0.2  # Security actions are inherently important for safety

        # Check historical safety data
        similar_actions = await self._get_similar_action_history(option, days=30)
        if similar_actions:
            failure_rate = sum(
                1 for action in similar_actions if action.get("outcome") == "failed"
            ) / len(similar_actions)
            safety_score -= failure_rate * 0.4

        # Device-specific safety considerations
        if "device_id" in context:
            device_safety = await self._assess_device_safety(context["device_id"])
            safety_score = (safety_score + device_safety) / 2

        return max(0.0, min(1.0, safety_score))

    async def _evaluate_user_satisfaction(
        self, option: Dict[str, Any], context: Dict[str, Any]
    ) -> float:
        """Evaluate potential user satisfaction impact."""

        satisfaction_score = 0.6  # Neutral baseline

        # Check user preferences from memory
        user_preferences = await self._get_user_preferences(context)

        if user_preferences:
            # Check if option aligns with preferences
            preference_alignment = await self._calculate_preference_alignment(
                option, user_preferences
            )
            satisfaction_score += preference_alignment * 0.3

        # Check emotional state impact
        current_emotion = await self.emotion_repo.get_current_state()
        if current_emotion:
            if option.get("expected_emotional_impact") == "positive":
                satisfaction_score += 0.2
            elif option.get("expected_emotional_impact") == "negative":
                satisfaction_score -= 0.2

        # Check response time expectations
        if context.get("urgency") == "high" and option.get("response_time", 0) < 10:
            satisfaction_score += 0.2
        elif context.get("urgency") == "low" and option.get("response_time", 0) > 60:
            satisfaction_score -= 0.1

        return max(0.0, min(1.0, satisfaction_score))

    async def _evaluate_efficiency(
        self, option: Dict[str, Any], context: Dict[str, Any]
    ) -> float:
        """Evaluate efficiency aspects of an option."""

        efficiency_score = 0.7  # Base efficiency

        # Resource efficiency
        resources = option.get("resource_requirements", {})

        # CPU efficiency
        cpu_usage = resources.get("cpu_percent", 0)
        if cpu_usage < 20:
            efficiency_score += 0.1
        elif cpu_usage > 80:
            efficiency_score -= 0.2

        # Memory efficiency
        memory_usage = resources.get("memory_mb", 0)
        if memory_usage < 100:
            efficiency_score += 0.1
        elif memory_usage > 1000:
            efficiency_score -= 0.2

        # Time efficiency
        execution_time = option.get("estimated_duration", 0)
        if execution_time < 5:
            efficiency_score += 0.1
        elif execution_time > 60:
            efficiency_score -= 0.1

        # Energy efficiency (for device control)
        if "device_id" in context:
            energy_impact = option.get("energy_impact", "neutral")
            if energy_impact == "positive":
                efficiency_score += 0.2
            elif energy_impact == "negative":
                efficiency_score -= 0.2

        return max(0.0, min(1.0, efficiency_score))

    async def _evaluate_learning_value(
        self, option: Dict[str, Any], context: Dict[str, Any]
    ) -> float:
        """Evaluate learning potential of an option."""

        learning_score = 0.5  # Neutral baseline

        # Novelty factor
        similar_actions = await self._get_similar_action_history(option, days=30)
        if len(similar_actions) == 0:
            learning_score += 0.3  # Novel action has high learning value
        elif len(similar_actions) < 3:
            learning_score += 0.1  # Some learning value

        # Complexity factor
        complexity = option.get("complexity", "medium")
        if complexity == "high":
            learning_score += 0.2
        elif complexity == "low":
            learning_score -= 0.1

        # Feedback availability
        if option.get("provides_feedback", False):
            learning_score += 0.2

        # Experimental nature
        if option.get("experimental", False):
            learning_score += 0.1

        return max(0.0, min(1.0, learning_score))

    async def _evaluate_system_stability(
        self, option: Dict[str, Any], context: Dict[str, Any]
    ) -> float:
        """Evaluate system stability impact."""

        stability_score = 0.8  # Assume stable by default

        # Check for system-critical actions
        action_type = option.get("action_type", "").lower()

        if any(
            critical in action_type for critical in ["restart", "reconfigure", "update"]
        ):
            stability_score -= 0.3

        # Check current system load
        system_load = context.get("system_load", 0.5)
        if system_load > 0.8:
            stability_score -= 0.2  # High load makes changes risky

        # Check for concurrent operations
        concurrent_ops = context.get("concurrent_operations", 0)
        if concurrent_ops > 3:
            stability_score -= 0.1

        # Check rollback capability
        if option.get("reversible", False):
            stability_score += 0.1

        return max(0.0, min(1.0, stability_score))

    async def _score_options(
        self, option_analyses: List[Dict[str, Any]], decision_type: str
    ) -> List[Dict[str, Any]]:
        """Calculate weighted scores for all options."""

        scored_options = []

        for analysis in option_analyses:
            # Calculate weighted score
            total_score = 0.0
            weighted_scores = {}

            for criterion, score in analysis["scores"].items():
                weight = self.decision_criteria[criterion]["weight"]
                weighted_score = score * weight
                weighted_scores[criterion] = weighted_score
                total_score += weighted_score

            # Apply feasibility multiplier
            total_score *= analysis["feasibility"]

            # Apply decision type modifiers
            total_score = await self._apply_decision_type_modifiers(
                total_score, analysis, decision_type
            )

            scored_option = {
                "option": analysis["option"],
                "total_score": total_score,
                "scores": analysis["scores"],
                "weighted_scores": weighted_scores,
                "feasibility": analysis["feasibility"],
                "risks": analysis["risks"],
                "benefits": analysis["benefits"],
                "analysis": analysis,
            }

            scored_options.append(scored_option)

        # Sort by total score
        scored_options.sort(key=lambda x: x["total_score"], reverse=True)

        return scored_options

    async def _select_best_option(
        self, scored_options: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Select the best option from scored options."""

        if not scored_options:
            return {"option": {}, "total_score": 0.0, "scores": {}}

        # Default to highest scoring option
        best_option = scored_options[0]

        # Check for minimum thresholds
        for criterion, config in self.decision_criteria.items():
            threshold = config["threshold"]
            if best_option["scores"].get(criterion, 0) < threshold:
                # Look for alternative that meets threshold
                for option in scored_options[1:]:
                    if option["scores"].get(criterion, 0) >= threshold:
                        best_option = option
                        break
                break

        # Apply context-specific selection rules
        urgency = context.get("urgency", "medium")
        if urgency == "high":
            # Prefer faster options for urgent decisions
            fast_options = [
                opt
                for opt in scored_options
                if opt["analysis"].get("time_estimate", 0) < 30
            ]
            if fast_options:
                best_option = fast_options[0]

        return best_option

    async def _build_decision_reasoning(
        self,
        chosen_option: Dict[str, Any],
        all_options: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[str]:
        """Build human-readable reasoning for the decision."""

        reasoning = []

        # Primary reason for selection
        reasoning.append(
            f"Selected option scored {chosen_option['total_score']:.2f} out of 1.0"
        )

        # Highlight strongest criteria
        best_criteria = sorted(
            chosen_option["scores"].items(), key=lambda x: x[1], reverse=True
        )[:2]

        for criterion, score in best_criteria:
            if score > 0.7:
                reasoning.append(f"Strong {criterion}: {score:.1%}")

        # Compare to alternatives
        if len(all_options) > 1:
            second_best = all_options[1]
            score_diff = chosen_option["total_score"] - second_best["total_score"]
            reasoning.append(
                f"Outperformed next best option by {score_diff:.2f} points"
            )

        # Risk considerations
        risks = chosen_option.get("risks", [])
        if risks:
            high_risks = [
                risk for risk in risks if risk.get("severity", "low") == "high"
            ]
            if high_risks:
                reasoning.append(
                    f"Proceeding despite {len(high_risks)} high-risk factors"
                )
            else:
                reasoning.append(f"Acceptable risk level with {len(risks)} minor risks")
        else:
            reasoning.append("No significant risks identified")

        # Benefits highlight
        benefits = chosen_option.get("benefits", [])
        if benefits:
            reasoning.append(f"Expected {len(benefits)} positive outcomes")

        # Context-specific reasoning
        if context.get("urgency") == "high":
            reasoning.append("Fast execution prioritized due to high urgency")

        if context.get("user_preference"):
            reasoning.append("Aligns with user preferences")

        return reasoning

    async def _calculate_decision_confidence(
        self,
        chosen_option: Dict[str, Any],
        all_options: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> float:
        """Calculate confidence in the decision."""

        confidence_factors = []

        # Score quality
        total_score = chosen_option["total_score"]
        confidence_factors.append(total_score)

        # Score separation from alternatives
        if len(all_options) > 1:
            score_separation = (
                chosen_option["total_score"] - all_options[1]["total_score"]
            )
            confidence_factors.append(min(1.0, score_separation * 2))
        else:
            confidence_factors.append(0.8)  # Single option gets medium confidence

        # Criteria consistency (how evenly criteria agree)
        scores = list(chosen_option["scores"].values())
        if scores:
            score_variance = np.var(scores)
            consistency = max(0.0, 1.0 - score_variance)
            confidence_factors.append(consistency)

        # Experience with similar decisions
        similar_decisions = await self._get_similar_decision_history(
            chosen_option, context
        )
        if similar_decisions:
            success_rate = sum(
                1 for d in similar_decisions if d.get("outcome") == "success"
            ) / len(similar_decisions)
            confidence_factors.append(success_rate)
        else:
            confidence_factors.append(0.5)  # Neutral for no experience

        # Risk assessment
        risks = chosen_option.get("risks", [])
        high_risks = sum(1 for risk in risks if risk.get("severity") == "high")
        risk_factor = max(0.0, 1.0 - high_risks * 0.2)
        confidence_factors.append(risk_factor)

        # Feasibility
        confidence_factors.append(chosen_option["feasibility"])

        # Calculate weighted average
        weights = [0.25, 0.2, 0.15, 0.15, 0.15, 0.1]  # Match factor order
        weighted_confidence = sum(
            factor * weight for factor, weight in zip(confidence_factors, weights)
        )

        return max(0.0, min(1.0, weighted_confidence))

    async def _assess_decision_risk(
        self, chosen_option: Dict[str, Any], context: Dict[str, Any], decision_type: str
    ) -> Dict[str, Any]:
        """Assess risks associated with the decision."""

        risk_assessment = {
            "overall_risk": "medium",
            "risk_factors": [],
            "mitigation_strategies": [],
            "reversibility": chosen_option["option"].get("reversible", False),
            "impact_level": self.decision_types.get(decision_type, {}).get(
                "impact_level", "medium"
            ),
        }

        # Analyze risk factors
        risks = chosen_option.get("risks", [])
        high_risk_count = sum(1 for risk in risks if risk.get("severity") == "high")
        medium_risk_count = sum(1 for risk in risks if risk.get("severity") == "medium")

        # Determine overall risk level
        if high_risk_count > 2:
            risk_assessment["overall_risk"] = "high"
        elif high_risk_count > 0 or medium_risk_count > 3:
            risk_assessment["overall_risk"] = "medium"
        else:
            risk_assessment["overall_risk"] = "low"

        # Add specific risk factors
        risk_assessment["risk_factors"] = risks

        # Generate mitigation strategies
        for risk in risks:
            if risk.get("severity") in ["high", "medium"]:
                mitigation = await self._generate_risk_mitigation(
                    risk, chosen_option, context
                )
                if mitigation:
                    risk_assessment["mitigation_strategies"].append(mitigation)

        return risk_assessment

    async def _execute_decision(
        self, decision_result: Dict[str, Any], decision_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the chosen decision."""

        execution_result = {
            "status": "pending",
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None,
            "success": False,
            "error_message": None,
            "execution_details": {},
        }

        try:
            chosen_option = decision_result["chosen_option"]
            decision_type = decision_result["decision_type"]

            # Execute based on decision type
            if decision_type == "device_control":
                result = await self._execute_device_control(
                    chosen_option, decision_context
                )
            elif decision_type == "user_response":
                result = await self._execute_user_response(
                    chosen_option, decision_context
                )
            elif decision_type == "system_configuration":
                result = await self._execute_system_configuration(
                    chosen_option, decision_context
                )
            elif decision_type == "security_action":
                result = await self._execute_security_action(
                    chosen_option, decision_context
                )
            else:
                result = await self._execute_generic_action(
                    chosen_option, decision_context
                )

            execution_result.update(result)
            execution_result["success"] = result.get("status") == "completed"

        except Exception as e:
            execution_result["status"] = "failed"
            execution_result["error_message"] = str(e)
            execution_result["success"] = False

        execution_result["end_time"] = datetime.utcnow().isoformat()
        return execution_result

    async def _execute_device_control(
        self, option: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a device control decision."""

        device_id = context.get("device_id")
        action_type = option.get("action_type")
        parameters = option.get("parameters", {})

        # Create control action record
        control_action = ControlAction(
            device_id=device_id,
            action_type=action_type,
            parameters=parameters,
            executed_at=datetime.utcnow(),
            status="executing",
        )

        self.session.add(control_action)
        await self.session.commit()

        # Simulate execution (in real implementation, this would call device APIs)
        await asyncio.sleep(0.1)  # Simulate execution time

        # Update action status
        control_action.status = "completed"
        control_action.result = {
            "success": True,
            "message": "Action completed successfully",
        }
        await self.session.commit()

        return {
            "status": "completed",
            "action_id": control_action.id,
            "device_id": device_id,
            "action_type": action_type,
        }

    async def _execute_user_response(
        self, option: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a user response decision."""

        response_text = option.get("response_text", "")
        response_type = option.get("response_type", "text")

        # Log the response
        response_event = Event(
            event_type="user_response",
            severity="info",
            event_data={
                "response_text": response_text,
                "response_type": response_type,
                "context": context,
            },
        )

        self.session.add(response_event)
        await self.session.commit()

        return {
            "status": "completed",
            "response_text": response_text,
            "response_type": response_type,
        }

    async def _execute_system_configuration(
        self, option: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a system configuration decision."""

        config_changes = option.get("configuration_changes", {})

        # Log configuration change
        config_event = Event(
            event_type="system_configuration_change",
            severity="info",
            event_data={"changes": config_changes, "context": context},
        )

        self.session.add(config_event)
        await self.session.commit()

        return {"status": "completed", "configuration_changes": config_changes}

    async def _execute_security_action(
        self, option: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a security action decision."""

        action_type = option.get("action_type")
        target = option.get("target")

        # Log security action
        security_event = Event(
            event_type="security_action",
            severity="high",
            event_data={
                "action_type": action_type,
                "target": target,
                "context": context,
            },
        )

        self.session.add(security_event)
        await self.session.commit()

        return {"status": "completed", "action_type": action_type, "target": target}

    async def _execute_generic_action(
        self, option: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a generic action decision."""

        action_data = option.copy()

        # Log generic action
        action_event = Event(
            event_type="generic_decision_action",
            severity="info",
            event_data={"action": action_data, "context": context},
        )

        self.session.add(action_event)
        await self.session.commit()

        return {"status": "completed", "action": action_data}

    async def _store_decision_outcome(
        self, decision_result: Dict[str, Any], decision_context: Dict[str, Any]
    ):
        """Store the decision and its outcome."""

        # Create memory of the decision
        decision_memory_data = {
            "event_type": "decision_made",
            "decision_result": decision_result,
            "decision_context": decision_context,
            "timestamp": datetime.utcnow().isoformat(),
        }

        importance = 0.5 + (decision_result["confidence"] * 0.3)

        await self.memory_repo.create(
            memory_type="procedural",
            category="decision_making",
            importance=importance,
            title=f"Decision: {decision_result['decision_type']}",
            description=f"Made {decision_result['decision_type']} decision with {decision_result['confidence']:.1%} confidence",
            content=decision_memory_data,
            source="decision_engine",
            confidence=decision_result["confidence"],
            tags=["decision", decision_result["decision_type"]],
            related_entities=[],
        )

        # Update metrics
        self.decision_metrics["total_decisions"] += 1

    async def _defer_decision(
        self, decision_context: Dict[str, Any], decision_result: Dict[str, Any]
    ):
        """Defer a decision due to low confidence."""

        # Log the deferral
        defer_event = Event(
            event_type="decision_deferred",
            severity="info",
            event_data={
                "decision_context": decision_context,
                "decision_result": decision_result,
                "reason": "Low confidence",
                "confidence": decision_result["confidence"],
            },
        )

        self.session.add(defer_event)
        await self.session.commit()

    async def _remove_pending_decision(self, decision_id: int):
        """Remove a decision from the pending list."""

        # Mark the pending decision event as processed
        update_event = Event(
            event_type="decision_processed",
            severity="info",
            event_data={"processed_decision_id": decision_id},
        )

        self.session.add(update_event)
        await self.session.commit()

    async def _handle_decision_error(
        self, decision_context: Dict[str, Any], error_message: str
    ):
        """Handle errors in decision processing."""

        error_event = Event(
            event_type="decision_error",
            severity="high",
            event_data={
                "decision_context": decision_context,
                "error_message": error_message,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        self.session.add(error_event)
        await self.session.commit()

    # Helper methods for decision evaluation

    async def _get_similar_action_history(
        self, option: Dict[str, Any], days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get history of similar actions."""

        action_type = option.get("action_type", "")
        if not action_type:
            return []

        cutoff_time = datetime.utcnow() - timedelta(days=days)

        # Search in control actions
        similar_actions = await self.session.execute(
            select(ControlAction)
            .where(
                and_(
                    ControlAction.action_type == action_type,
                    ControlAction.executed_at >= cutoff_time,
                )
            )
            .limit(20)
        )

        actions = []
        for action in similar_actions.scalars():
            actions.append(
                {
                    "action_type": action.action_type,
                    "status": action.status,
                    "outcome": "success" if action.status == "completed" else "failed",
                    "executed_at": action.executed_at,
                }
            )

        return actions

    async def _assess_device_safety(self, device_id: int) -> float:
        """Assess safety of a specific device."""

        device = await self.session.execute(
            select(Device).where(Device.id == device_id)
        )
        device_obj = device.scalar_one_or_none()

        if not device_obj:
            return 0.0

        safety_score = 0.8  # Base safety

        # Check device status
        if device_obj.status != "online":
            safety_score -= 0.3

        # Check recent error history
        recent_errors = await self.session.execute(
            select(func.count(Event.id)).where(
                and_(
                    Event.event_data.contains(f'"device_id": {device_id}'),
                    Event.severity.in_(["high", "critical"]),
                    Event.created_at >= datetime.utcnow() - timedelta(days=7),
                )
            )
        )

        error_count = recent_errors.scalar()
        if error_count > 0:
            safety_score -= min(0.4, error_count * 0.1)

        return max(0.0, min(1.0, safety_score))

    async def _get_user_preferences(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get user preferences from memory."""

        preference_memories = await self.memory_repo.search_memories(
            query="user_preferences", memory_type="semantic", limit=5
        )

        preferences = {}
        for memory in preference_memories:
            if memory.content and "preference_type" in memory.content:
                pref_type = memory.content["preference_type"]
                pref_data = memory.content.get("pattern_data", {})
                preferences[pref_type] = pref_data

        return preferences

    async def _calculate_preference_alignment(
        self, option: Dict[str, Any], preferences: Dict[str, Any]
    ) -> float:
        """Calculate how well an option aligns with user preferences."""

        alignment_score = 0.0
        alignment_count = 0

        # Check timing preferences
        if "timing_preference" in preferences:
            current_hour = datetime.utcnow().hour
            preferred_hours = preferences["timing_preference"].get(
                "preferred_hours", []
            )
            if current_hour in preferred_hours:
                alignment_score += 0.3
                alignment_count += 1

        # Check interaction preferences
        if "interaction_preference" in preferences:
            option_type = option.get("response_type", option.get("action_type", ""))
            preferred_types = preferences["interaction_preference"].get(
                "preferred_types", []
            )
            if option_type in preferred_types:
                alignment_score += 0.4
                alignment_count += 1

        return alignment_score / max(1, alignment_count) if alignment_count > 0 else 0.5

    async def _apply_decision_type_modifiers(
        self, score: float, analysis: Dict[str, Any], decision_type: str
    ) -> float:
        """Apply decision type specific modifiers to the score."""

        if decision_type == "security_action":
            # Prioritize safety for security actions
            safety_score = analysis["scores"].get("safety", 0.5)
            if safety_score > 0.8:
                score *= 1.1
            elif safety_score < 0.6:
                score *= 0.8

        elif decision_type == "user_response":
            # Prioritize user satisfaction for responses
            satisfaction_score = analysis["scores"].get("user_satisfaction", 0.5)
            if satisfaction_score > 0.8:
                score *= 1.1

        elif decision_type == "device_control":
            # Balance efficiency and safety for device control
            efficiency_score = analysis["scores"].get("efficiency", 0.5)
            safety_score = analysis["scores"].get("safety", 0.5)
            if efficiency_score > 0.7 and safety_score > 0.7:
                score *= 1.05

        return score

    async def _check_feasibility(
        self,
        option: Dict[str, Any],
        constraints: Dict[str, Any],
        context: Dict[str, Any],
    ) -> float:
        """Check feasibility of an option against constraints."""

        feasibility = 1.0

        # Resource constraints
        if "max_cpu_percent" in constraints:
            required_cpu = option.get("resource_requirements", {}).get("cpu_percent", 0)
            if required_cpu > constraints["max_cpu_percent"]:
                feasibility *= 0.5

        # Time constraints
        if "max_duration" in constraints:
            estimated_duration = option.get("estimated_duration", 0)
            if estimated_duration > constraints["max_duration"]:
                feasibility *= 0.3

        # Permission constraints
        if "required_permissions" in option:
            available_permissions = context.get("available_permissions", [])
            required_permissions = option["required_permissions"]
            if not all(perm in available_permissions for perm in required_permissions):
                feasibility *= 0.1

        return feasibility

    async def _identify_option_risks(
        self, option: Dict[str, Any], context: Dict[str, Any], decision_type: str
    ) -> List[Dict[str, Any]]:
        """Identify risks associated with an option."""

        risks = []

        # Action-specific risks
        action_type = option.get("action_type", "").lower()

        if "delete" in action_type:
            risks.append(
                {
                    "type": "data_loss",
                    "description": "Potential for irreversible data loss",
                    "severity": "high",
                    "mitigation": "Ensure backups are available",
                }
            )

        if "disable" in action_type or "shutdown" in action_type:
            risks.append(
                {
                    "type": "service_interruption",
                    "description": "Service may become unavailable",
                    "severity": "medium",
                    "mitigation": "Plan for service restoration",
                }
            )

        # Resource risks
        resource_reqs = option.get("resource_requirements", {})
        if resource_reqs.get("cpu_percent", 0) > 80:
            risks.append(
                {
                    "type": "performance_impact",
                    "description": "High CPU usage may impact system performance",
                    "severity": "medium",
                    "mitigation": "Monitor system performance during execution",
                }
            )

        # Time risks
        if option.get("estimated_duration", 0) > 300:  # 5 minutes
            risks.append(
                {
                    "type": "timeout_risk",
                    "description": "Long execution time may lead to timeout",
                    "severity": "low",
                    "mitigation": "Implement progress monitoring",
                }
            )

        return risks

    async def _identify_option_benefits(
        self, option: Dict[str, Any], context: Dict[str, Any], decision_type: str
    ) -> List[Dict[str, Any]]:
        """Identify benefits of an option."""

        benefits = []

        # Efficiency benefits
        if option.get("energy_impact") == "positive":
            benefits.append(
                {
                    "type": "energy_savings",
                    "description": "Reduces energy consumption",
                    "impact": "medium",
                }
            )

        # User satisfaction benefits
        if option.get("expected_emotional_impact") == "positive":
            benefits.append(
                {
                    "type": "user_satisfaction",
                    "description": "Improves user experience",
                    "impact": "high",
                }
            )

        # Learning benefits
        if option.get("provides_feedback", False):
            benefits.append(
                {
                    "type": "learning_opportunity",
                    "description": "Provides valuable feedback for future decisions",
                    "impact": "medium",
                }
            )

        # Performance benefits
        if option.get("performance_improvement", False):
            benefits.append(
                {
                    "type": "performance_gain",
                    "description": "Improves system performance",
                    "impact": "high",
                }
            )

        return benefits

    async def _estimate_resource_requirements(
        self, option: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Estimate resource requirements for an option."""

        # Default estimates
        resources = {
            "cpu_percent": 10,
            "memory_mb": 50,
            "network_bandwidth": 0,
            "disk_io": 0,
        }

        # Adjust based on action type
        action_type = option.get("action_type", "").lower()

        if "analysis" in action_type or "calculation" in action_type:
            resources["cpu_percent"] = 30
            resources["memory_mb"] = 200

        if "download" in action_type or "upload" in action_type:
            resources["network_bandwidth"] = 100  # KB/s

        if "backup" in action_type or "save" in action_type:
            resources["disk_io"] = 50  # MB/s

        # Override with explicit requirements
        if "resource_requirements" in option:
            resources.update(option["resource_requirements"])

        return resources

    async def _estimate_completion_time(
        self, option: Dict[str, Any], context: Dict[str, Any], decision_type: str
    ) -> float:
        """Estimate time to complete an option in seconds."""

        base_time = 5.0  # Default 5 seconds

        # Adjust based on action complexity
        complexity = option.get("complexity", "medium")
        if complexity == "low":
            base_time *= 0.5
        elif complexity == "high":
            base_time *= 3.0

        # Adjust based on decision type
        type_multipliers = {
            "device_control": 1.0,
            "user_response": 0.5,
            "system_configuration": 2.0,
            "security_action": 0.3,
            "learning_adaptation": 5.0,
        }

        multiplier = type_multipliers.get(decision_type, 1.0)
        estimated_time = base_time * multiplier

        # Override with explicit estimate
        if "estimated_duration" in option:
            estimated_time = option["estimated_duration"]

        return estimated_time

    async def _learn_from_decision_process(
        self, decision_result: Dict[str, Any], option_analyses: List[Dict[str, Any]]
    ):
        """Learn from the decision-making process."""

        # Store decision-making insights
        learning_data = {
            "event_type": "decision_process_learning",
            "decision_type": decision_result["decision_type"],
            "options_considered": len(option_analyses),
            "chosen_score": decision_result.get("criteria_scores", {}),
            "decision_time": decision_result["decision_time"],
            "confidence": decision_result["confidence"],
            "learning_date": datetime.utcnow().isoformat(),
        }

        await self.memory_repo.create(
            memory_type="procedural",
            category="decision_learning",
            importance=0.6,
            title=f"Decision Process: {decision_result['decision_type']}",
            description=f"Decision-making process with {decision_result['confidence']:.1%} confidence",
            content=learning_data,
            source="decision_engine",
            confidence=0.8,
            tags=["decision", "learning", "process"],
            related_entities=[decision_result["decision_type"]],
        )

    async def _get_decision_by_id(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a decision by its ID."""

        # Search for decision in memory
        decision_memories = await self.memory_repo.search_memories(
            query=decision_id,
            memory_type="procedural",
            category="decision_making",
            limit=1,
        )

        if decision_memories:
            memory = decision_memories[0]
            if memory.content and "decision_result" in memory.content:
                return memory.content["decision_result"]

        return None

    async def _calculate_outcome_accuracy(
        self, predicted: Dict[str, Any], actual: Dict[str, Any]
    ) -> float:
        """Calculate accuracy of predicted vs actual outcomes."""

        if not predicted or not actual:
            return 0.5

        accuracy_scores = []

        # Compare specific outcome fields
        for key in predicted.keys():
            if key in actual:
                pred_val = predicted[key]
                actual_val = actual[key]

                if isinstance(pred_val, (int, float)) and isinstance(
                    actual_val, (int, float)
                ):
                    # Numerical comparison
                    diff = abs(pred_val - actual_val) / max(
                        abs(pred_val), abs(actual_val), 1
                    )
                    accuracy = 1.0 - min(1.0, diff)
                    accuracy_scores.append(accuracy)
                elif pred_val == actual_val:
                    # Exact match
                    accuracy_scores.append(1.0)
                else:
                    # No match
                    accuracy_scores.append(0.0)

        return np.mean(accuracy_scores) if accuracy_scores else 0.5

    async def _assess_confidence_calibration(
        self, predicted_confidence: float, accuracy: float
    ) -> float:
        """Assess how well confidence matched actual accuracy."""

        # Perfect calibration would have confidence == accuracy
        calibration_error = abs(predicted_confidence - accuracy)
        calibration_score = 1.0 - calibration_error

        return max(0.0, calibration_score)

    async def _extract_decision_lessons(
        self,
        original_decision: Dict[str, Any],
        actual_outcome: Dict[str, Any],
        accuracy: float,
    ) -> List[str]:
        """Extract lessons learned from decision outcome."""

        lessons = []

        if accuracy > 0.8:
            lessons.append("Decision criteria and weighting were well-calibrated")
            lessons.append("Continue using similar approach for this decision type")
        elif accuracy < 0.4:
            lessons.append("Decision criteria may need adjustment")
            lessons.append("Consider additional factors for future similar decisions")

        # Confidence lessons
        confidence = original_decision.get("confidence", 0.5)
        if confidence > 0.8 and accuracy < 0.5:
            lessons.append("Overconfident - need better uncertainty assessment")
        elif confidence < 0.5 and accuracy > 0.8:
            lessons.append("Underconfident - trust the decision framework more")

        # Risk assessment lessons
        risks = original_decision.get("risk_assessment", {})
        if risks.get("overall_risk") == "low" and accuracy < 0.5:
            lessons.append("Risk assessment was too optimistic")

        return lessons

    async def _generate_decision_improvements(
        self, original_decision: Dict[str, Any], evaluation: Dict[str, Any]
    ) -> List[str]:
        """Generate suggestions for improving future decisions."""

        improvements = []

        accuracy = evaluation["accuracy_score"]

        if accuracy < 0.6:
            improvements.append("Consider additional decision criteria")
            improvements.append("Gather more context before deciding")
            improvements.append("Increase weight of safety criterion")

        confidence_calibration = evaluation["confidence_calibration"]
        if confidence_calibration < 0.6:
            improvements.append("Improve confidence estimation methods")
            improvements.append("Consider uncertainty in risk assessment")

        # Decision time improvements
        decision_time = original_decision.get("decision_time", 0)
        if decision_time > 30:
            improvements.append("Optimize decision-making process for speed")
        elif decision_time < 1 and accuracy < 0.5:
            improvements.append("Spend more time analyzing options")

        return improvements

    async def _update_decision_metrics(
        self, original_decision: Dict[str, Any], evaluation: Dict[str, Any]
    ):
        """Update decision performance metrics."""

        accuracy = evaluation["accuracy_score"]
        confidence = original_decision.get("confidence", 0.5)

        if accuracy > 0.7:
            self.decision_metrics["successful_decisions"] += 1
        else:
            self.decision_metrics["failed_decisions"] += 1

        # Update confidence accuracy for high-confidence decisions
        if confidence > self.confidence_thresholds["high_confidence"]:
            current_accuracy = self.decision_metrics.get(
                "high_confidence_accuracy", 0.0
            )
            high_conf_count = self.decision_metrics.get("high_confidence_count", 0)

            new_accuracy = (current_accuracy * high_conf_count + accuracy) / (
                high_conf_count + 1
            )
            self.decision_metrics["high_confidence_accuracy"] = new_accuracy
            self.decision_metrics["high_confidence_count"] = high_conf_count + 1

        # Update average decision time
        decision_time = original_decision.get("decision_time", 0)
        current_avg_time = self.decision_metrics.get("average_decision_time", 0.0)
        total_decisions = self.decision_metrics["total_decisions"]

        if total_decisions > 0:
            new_avg_time = (current_avg_time * total_decisions + decision_time) / (
                total_decisions + 1
            )
            self.decision_metrics["average_decision_time"] = new_avg_time

    async def _store_decision_evaluation(self, evaluation: Dict[str, Any]):
        """Store decision evaluation for future learning."""

        await self.memory_repo.create(
            memory_type="procedural",
            category="decision_evaluation",
            importance=0.7,
            title=f"Decision Evaluation: {evaluation['decision_id']}",
            description=f"Evaluation with {evaluation['accuracy_score']:.1%} accuracy",
            content=evaluation,
            source="decision_engine",
            confidence=0.9,
            tags=["decision", "evaluation", "learning"],
            related_entities=[evaluation["decision_id"]],
        )

    async def _get_supporting_memories(
        self, decision: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get memories that supported the decision."""

        decision_type = decision.get("decision_type", "")
        context = decision.get("context", {})

        # Search for relevant memories
        query_terms = [decision_type]
        if "device_id" in context:
            query_terms.append(f"device_{context['device_id']}")

        supporting_memories = []
        for term in query_terms[:2]:  # Limit to avoid too many queries
            memories = await self.memory_repo.search_memories(query=term, limit=3)

            for memory in memories:
                supporting_memories.append(
                    {
                        "title": memory.title,
                        "description": memory.description,
                        "importance": memory.importance,
                        "created_at": memory.created_at.isoformat(),
                    }
                )

        return supporting_memories[:5]  # Limit results

    async def _get_decision_emotional_context(
        self, decision: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get emotional context at the time of decision."""

        decision_time = decision.get("timestamp")
        if not decision_time:
            return {}

        # Get emotional state near decision time
        if isinstance(decision_time, str):
            decision_time = datetime.fromisoformat(decision_time.replace("Z", "+00:00"))

        emotional_states = await self.emotion_repo.get_state_history(hours=1)

        # Find closest emotional state
        closest_state = None
        min_time_diff = float("inf")

        for state in emotional_states:
            time_diff = abs((state.created_at - decision_time).total_seconds())
            if time_diff < min_time_diff:
                min_time_diff = time_diff
                closest_state = state

        if closest_state:
            return {
                "primary_emotion": closest_state.primary_emotion,
                "intensity": closest_state.intensity,
                "happiness": closest_state.happiness,
                "worry": closest_state.worry,
                "boredom": closest_state.boredom,
                "excitement": closest_state.excitement,
            }

        return {}

    async def _analyze_confidence_factors(
        self, decision: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Analyze factors that contributed to decision confidence."""

        confidence = decision.get("confidence", 0.5)
        factors = []

        if confidence > 0.8:
            factors.append(
                {
                    "factor": "High option score",
                    "description": "Chosen option scored well on most criteria",
                }
            )
            factors.append(
                {
                    "factor": "Clear best choice",
                    "description": "Significant score separation from alternatives",
                }
            )
        elif confidence < 0.4:
            factors.append(
                {
                    "factor": "Close alternatives",
                    "description": "Multiple options had similar scores",
                }
            )
            factors.append(
                {
                    "factor": "High uncertainty",
                    "description": "Limited experience with this decision type",
                }
            )

        # Risk factors
        risk_assessment = decision.get("risk_assessment", {})
        overall_risk = risk_assessment.get("overall_risk", "medium")

        if overall_risk == "low":
            factors.append(
                {"factor": "Low risk", "description": "Decision carried minimal risk"}
            )
        elif overall_risk == "high":
            factors.append(
                {
                    "factor": "High risk",
                    "description": "Decision had significant risk factors",
                }
            )

        return factors

    async def _get_similar_decision_history(
        self, chosen_option: Dict[str, Any], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get history of similar decisions."""

        decision_type = context.get("decision_type", "")

        # Search for similar decisions in memory
        similar_decisions = await self.memory_repo.search_memories(
            query=decision_type,
            memory_type="procedural",
            category="decision_making",
            limit=10,
        )

        decisions = []
        for memory in similar_decisions:
            if memory.content and "decision_result" in memory.content:
                decision_data = memory.content["decision_result"]
                decisions.append(
                    {
                        "decision_type": decision_data.get("decision_type"),
                        "confidence": decision_data.get("confidence"),
                        "outcome": "success"
                        if decision_data.get("execution_result", {}).get("success")
                        else "unknown",
                        "created_at": memory.created_at,
                    }
                )

        return decisions

    async def _generate_risk_mitigation(
        self,
        risk: Dict[str, Any],
        chosen_option: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Optional[Dict[str, str]]:
        """Generate mitigation strategy for a specific risk."""

        risk_type = risk.get("type", "")

        mitigation_strategies = {
            "data_loss": {
                "strategy": "Create backup before proceeding",
                "implementation": "Automated backup verification",
            },
            "service_interruption": {
                "strategy": "Schedule during low-usage period",
                "implementation": "Maintenance window with user notification",
            },
            "performance_impact": {
                "strategy": "Monitor system resources during execution",
                "implementation": "Real-time performance monitoring with rollback capability",
            },
            "timeout_risk": {
                "strategy": "Implement progress checkpoints",
                "implementation": "Break down operation into smaller steps",
            },
        }

        return mitigation_strategies.get(risk_type)
