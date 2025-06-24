"""
Conversational interview controller for device discovery.

This module manages the conversational device discovery process, guiding users
through natural language interactions to identify, classify, and configure their
smart home devices while automatically creating digital twins.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from consciousness.digital_twin.twin_manager import DigitalTwinManager
from consciousness.discovery.auto_discovery import AutoDiscoveryService
from consciousness.interview.device_classifier import DeviceClassifier
from consciousness.interview.integration_matcher import IntegrationMatcher
from consciousness.interview.question_generator import QuestionGenerator

logger = logging.getLogger(__name__)


class InterviewSession:
    """Represents an active device discovery interview session."""

    def __init__(self, session_id: str, house_id: str, user_id: Optional[str] = None):
        self.session_id = session_id
        self.house_id = house_id
        self.user_id = user_id
        self.started_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None

        # Interview state
        self.current_phase = "introduction"  # introduction, discovery, classification, configuration, twin_creation
        self.conversation_log: List[Dict[str, Any]] = []
        self.discovered_devices: List[Dict[str, Any]] = []
        self.device_candidates: List[Dict[str, Any]] = []
        self.configured_devices: List[Dict[str, Any]] = []
        self.created_twins: List[Dict[str, Any]] = []

        # Progress tracking
        self.completed_steps: List[str] = []
        self.current_step = 0
        self.total_steps = 0
        self.estimated_duration = 0  # minutes

        # Session metadata
        self.context: Dict[str, Any] = {}
        self.preferences: Dict[str, Any] = {}
        self.status = "active"  # active, completed, paused, cancelled


class DeviceCandidate:
    """Represents a potential device identified during the interview."""

    def __init__(self, user_description: str, session_id: str):
        self.id = f"candidate_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{len(user_description)}"
        self.session_id = session_id
        self.user_description = user_description
        self.extracted_keywords: List[str] = []

        # AI classification results
        self.detected_brand: Optional[str] = None
        self.detected_model: Optional[str] = None
        self.detected_function: Optional[str] = None
        self.confidence_score: float = 0.0

        # Integration matching
        self.possible_integrations: List[Dict[str, Any]] = []
        self.recommended_integration: Optional[str] = None
        self.integration_confidence: float = 0.0

        # Discovery results
        self.network_discovery_results: Dict[str, Any] = {}
        self.auto_discovery_successful = False

        # Status and validation
        self.status = "pending"  # pending, confirmed, rejected, needs_info
        self.rejection_reason: Optional[str] = None
        self.validation_errors: List[str] = []

        # Final device mapping
        self.created_device_id: Optional[str] = None
        self.created_twin_id: Optional[str] = None


class InterviewController:
    """Manages the conversational device discovery interview process."""

    def __init__(
        self,
        llm_client: Any,
        auto_discovery: AutoDiscoveryService,
        twin_manager: DigitalTwinManager,
    ):
        self.llm_client = llm_client
        self.auto_discovery = auto_discovery
        self.twin_manager = twin_manager

        # Initialize components
        self.classifier = DeviceClassifier(llm_client)
        self.question_generator = QuestionGenerator()
        self.integration_matcher = IntegrationMatcher()

        # Active sessions
        self.active_sessions: Dict[str, InterviewSession] = {}

        # Interview templates and flows
        self._load_interview_templates()

    def _load_interview_templates(self) -> None:
        """Load interview templates and conversation flows."""
        self.interview_templates = {
            "initial_greeting": [
                "Hi! I'm here to help you set up your smart home devices. "
                "I'll learn about what you have through a quick conversation.",
                "Tell me about any smart devices in your home. You can describe "
                "them however feels natural - by room, by what they do, or just "
                "whatever comes to mind.",
                "For example, you might say 'I have Philips Hue lights in the living room' "
                "or 'We have a Nest thermostat and some security cameras.'",
            ],
            "discovery_prompts": [
                "What smart devices do you have in your home?",
                "Tell me about your connected devices.",
                "Which rooms have smart home technology?",
                "What apps do you use to control things in your house?",
            ],
            "room_based_questions": [
                "Let's go room by room. Starting with your living room - what smart devices do you have there?",
                "In your bedroom, do you have any smart lights, fans, or other connected devices?",
                "What about your kitchen? Any smart appliances, lights, or sensors?",
                "Do you have any devices in your bathroom? Smart switches, fans, or sensors?",
                "What smart devices do you have outdoors? Lights, cameras, or irrigation?",
            ],
            "function_based_questions": [
                "Tell me about how you control your home's temperature. Do you have a smart thermostat?",
                "For lighting, do you have any smart bulbs, switches, or dimmers?",
                "What about security? Any cameras, doorbells, or alarm systems?",
                "Do you have any entertainment devices? Smart TVs, speakers, or streaming devices?",
                "What about energy management? Solar panels, battery systems, or smart plugs?",
            ],
        }

    async def start_interview(
        self,
        house_id: str,
        user_id: Optional[str] = None,
        interview_type: str = "device_discovery",
    ) -> InterviewSession:
        """Start a new device discovery interview session."""

        # Check for existing active session
        existing_session = self._get_active_session_for_house(house_id)
        if existing_session:
            logger.info(
                f"Resuming existing interview session {existing_session.session_id}"
            )
            return existing_session

        # Create new session
        session_id = (
            f"interview_{house_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        )
        session = InterviewSession(session_id, house_id, user_id)

        # Initialize session context
        session.context = {
            "interview_type": interview_type,
            "discovery_strategy": "conversational",
            "auto_discovery_enabled": True,
            "twin_creation_enabled": True,
        }

        # Add welcome message
        welcome_message = self._select_welcome_message()
        await self._add_ai_response(session, welcome_message)

        # Store session
        self.active_sessions[session_id] = session

        logger.info(f"Started new interview session {session_id} for house {house_id}")
        return session

    def _get_active_session_for_house(
        self, house_id: str
    ) -> Optional[InterviewSession]:
        """Get active interview session for a house."""
        for session in self.active_sessions.values():
            if session.house_id == house_id and session.status == "active":
                return session
        return None

    def _select_welcome_message(self) -> str:
        """Select appropriate welcome message."""
        return self.interview_templates["initial_greeting"][0]

    async def process_user_message(
        self,
        session_id: str,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process user input and generate appropriate response."""

        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Add user message to conversation log
        await self._add_user_message(session, user_message, context)

        # Process based on current phase
        if session.current_phase == "introduction":
            return await self._handle_initial_discovery(session, user_message)
        elif session.current_phase == "discovery":
            return await self._handle_device_discovery(session, user_message)
        elif session.current_phase == "classification":
            return await self._handle_device_classification(session, user_message)
        elif session.current_phase == "configuration":
            return await self._handle_device_configuration(session, user_message)
        elif session.current_phase == "twin_creation":
            return await self._handle_twin_creation(session, user_message)
        else:
            return await self._handle_general_response(session, user_message)

    async def _handle_initial_discovery(
        self, session: InterviewSession, user_message: str
    ) -> Dict[str, Any]:
        """Handle the initial device discovery phase."""

        # Use LLM to extract device mentions from user input
        logger.info(f"Processing initial discovery for session {session.session_id}")

        try:
            device_mentions = await self.classifier.extract_device_mentions(
                user_message
            )
            logger.info(f"Extracted {len(device_mentions)} device mentions")

            # Create device candidates for each mention
            candidates = []
            for mention in device_mentions:
                candidate = DeviceCandidate(
                    user_description=mention["description"],
                    session_id=session.session_id,
                )

                # Populate from classification
                candidate.extracted_keywords = mention.get("keywords", [])
                candidate.detected_brand = mention.get("brand")
                candidate.detected_function = mention.get("function")
                candidate.detected_model = mention.get("model")
                candidate.confidence_score = mention.get("confidence", 0.0)

                # Match integrations
                candidate.possible_integrations = (
                    await self.integration_matcher.match_integrations(
                        candidate.detected_brand,
                        candidate.detected_function,
                        candidate.extracted_keywords,
                    )
                )

                candidates.append(candidate)
                session.device_candidates.append(candidate.to_dict())

            # Run automatic discovery in parallel
            if session.context.get("auto_discovery_enabled", True):
                logger.info("Running automatic discovery")
                discovery_results = await self.auto_discovery.discover_all_protocols()

                # Correlate discovered devices with user mentions
                await self._correlate_discovery_results(candidates, discovery_results)

            # Generate follow-up response
            if candidates:
                ai_response = await self._generate_classification_questions(candidates)
                session.current_phase = "classification"
                session.completed_steps.append("initial_discovery")
            else:
                # No devices detected, ask for clarification
                ai_response = await self._generate_clarification_prompt()
                # Stay in introduction phase

            await self._add_ai_response(session, ai_response)

            return {
                "response": ai_response,
                "candidates": [c.to_dict() for c in candidates],
                "phase": session.current_phase,
                "discovered_count": len(candidates),
            }

        except Exception as e:
            logger.error(f"Error in initial discovery: {e}")
            error_response = "I had trouble understanding that. Could you tell me about your smart devices in a different way?"
            await self._add_ai_response(session, error_response)

            return {
                "response": error_response,
                "candidates": [],
                "phase": session.current_phase,
                "error": str(e),
            }

    async def _handle_device_classification(
        self, session: InterviewSession, user_message: str
    ) -> Dict[str, Any]:
        """Handle the device classification and validation phase."""

        logger.info(
            f"Processing device classification for session {session.session_id}"
        )

        # Parse user response for confirmations/corrections
        classification_updates = await self.classifier.parse_classification_response(
            user_message, session.device_candidates
        )

        # Update candidates based on user feedback
        updated_candidates = []
        for update in classification_updates:
            candidate_id = update.get("candidate_id")
            candidate = self._find_candidate(session, candidate_id)

            if candidate:
                # Apply updates
                if "confirmed" in update:
                    candidate.status = (
                        "confirmed" if update["confirmed"] else "needs_info"
                    )

                if "brand_correction" in update:
                    candidate.detected_brand = update["brand_correction"]

                if "function_correction" in update:
                    candidate.detected_function = update["function_correction"]

                # Re-match integrations with corrections
                candidate.possible_integrations = (
                    await self.integration_matcher.match_integrations(
                        candidate.detected_brand,
                        candidate.detected_function,
                        candidate.extracted_keywords,
                    )
                )

                updated_candidates.append(candidate)

        # Check if all candidates are classified
        all_classified = all(
            c.status in ["confirmed", "rejected"] for c in session.device_candidates
        )

        if all_classified:
            # Move to configuration phase
            session.current_phase = "configuration"
            session.completed_steps.append("classification")
            ai_response = await self._generate_configuration_intro(session)
        else:
            # Ask for more clarification
            ai_response = await self._generate_additional_classification_questions(
                updated_candidates
            )

        await self._add_ai_response(session, ai_response)

        return {
            "response": ai_response,
            "candidates": [c.to_dict() for c in updated_candidates],
            "phase": session.current_phase,
            "all_classified": all_classified,
        }

    async def _handle_device_configuration(
        self, session: InterviewSession, user_message: str
    ) -> Dict[str, Any]:
        """Handle device configuration phase."""

        logger.info(f"Processing device configuration for session {session.session_id}")

        # Extract configuration information from user response
        config_info = await self.classifier.extract_configuration_info(
            user_message, session.device_candidates
        )

        configured_devices = []

        for candidate_data in session.device_candidates:
            if candidate_data.get("status") != "confirmed":
                continue

            try:
                # Create actual device configuration
                device_config = await self._create_device_configuration(
                    candidate_data, config_info
                )

                configured_devices.append(device_config)

            except Exception as e:
                logger.error(
                    f"Failed to configure device {candidate_data.get('id')}: {e}"
                )
                candidate_data["configuration_error"] = str(e)

        session.configured_devices.extend(configured_devices)

        # Check if twin creation is enabled
        if session.context.get("twin_creation_enabled", True) and configured_devices:
            session.current_phase = "twin_creation"
            ai_response = await self._generate_twin_creation_offer(configured_devices)
        else:
            # Complete the interview
            session.current_phase = "completed"
            session.status = "completed"
            session.completed_at = datetime.utcnow()
            ai_response = await self._generate_completion_summary(session)

        await self._add_ai_response(session, ai_response)

        return {
            "response": ai_response,
            "configured_devices": configured_devices,
            "phase": session.current_phase,
            "completed": session.status == "completed",
        }

    async def _handle_twin_creation(
        self, session: InterviewSession, user_message: str
    ) -> Dict[str, Any]:
        """Handle digital twin creation phase."""

        logger.info(f"Processing twin creation for session {session.session_id}")

        # Parse user preferences for twin creation
        twin_preferences = await self.classifier.parse_twin_preferences(user_message)

        created_twins = []

        if twin_preferences.get("create_twins", False):
            for device_config in session.configured_devices:
                try:
                    # Create digital twin with user preferences
                    twin_config = {
                        "fidelity_level": twin_preferences.get(
                            "fidelity_level", "basic"
                        ),
                        "sync_frequency": twin_preferences.get("sync_frequency", 60),
                        "enable_predictions": twin_preferences.get(
                            "enable_predictions", True
                        ),
                        "enable_scenarios": twin_preferences.get(
                            "enable_scenarios", False
                        ),
                        "enable_learning": twin_preferences.get(
                            "enable_learning", False
                        ),
                        "physics_modeling": twin_preferences.get(
                            "physics_modeling", False
                        ),
                    }

                    twin = await self.twin_manager.create_device_twin(
                        device_config, twin_config
                    )

                    created_twins.append(twin)

                except Exception as e:
                    logger.error(
                        f"Failed to create twin for device {device_config.get('id')}: {e}"
                    )

        session.created_twins.extend([t.to_dict() for t in created_twins])

        # Complete the interview
        session.current_phase = "completed"
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        session.completed_steps.append("twin_creation")

        ai_response = await self._generate_completion_summary_with_twins(
            session, created_twins
        )

        await self._add_ai_response(session, ai_response)

        return {
            "response": ai_response,
            "created_twins": [t.to_dict() for t in created_twins],
            "phase": session.current_phase,
            "completed": True,
        }

    async def _handle_general_response(
        self, session: InterviewSession, user_message: str
    ) -> Dict[str, Any]:
        """Handle general responses and conversation management."""

        # Use LLM to understand intent and generate appropriate response
        intent = await self.classifier.classify_user_intent(
            user_message, session.current_phase, session.context
        )

        if intent.get("type") == "clarification_request":
            ai_response = await self._handle_clarification_request(session, intent)
        elif intent.get("type") == "correction":
            ai_response = await self._handle_correction(session, intent)
        elif intent.get("type") == "additional_device":
            ai_response = await self._handle_additional_device(session, user_message)
        else:
            # General conversational response
            ai_response = await self._generate_contextual_response(
                session, user_message
            )

        await self._add_ai_response(session, ai_response)

        return {
            "response": ai_response,
            "intent": intent,
            "phase": session.current_phase,
        }

    async def _generate_classification_questions(
        self, candidates: List[DeviceCandidate]
    ) -> str:
        """Generate questions to clarify device details."""

        if not candidates:
            return "I didn't find any devices in what you said. Could you tell me more?"

        questions = []

        for candidate in candidates:
            if candidate.confidence_score > 0.8:
                # High confidence - ask for confirmation
                brand = candidate.detected_brand or "smart"
                function = candidate.detected_function or "device"
                questions.append(
                    f"I found what looks like a {brand} {function}. Is that right?"
                )
            else:
                # Low confidence - ask for clarification
                questions.append(
                    f"You mentioned '{candidate.user_description}'. "
                    f"What brand and type of device is that?"
                )

        if len(questions) == 1:
            return questions[0]
        else:
            response = "Let me ask about each device:\n\n"
            for i, q in enumerate(questions, 1):
                response += f"{i}. {q}\n"
            return response

    async def _generate_clarification_prompt(self) -> str:
        """Generate a clarification prompt when no devices are detected."""
        return (
            "I didn't catch any specific devices in what you said. "
            "Could you tell me about specific smart devices you have? "
            "For example, smart lights, thermostats, cameras, or speakers?"
        )

    async def _correlate_discovery_results(
        self,
        candidates: List[DeviceCandidate],
        discovery_results: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Correlate automatic discovery results with user-mentioned devices."""

        for candidate in candidates:
            # Try to find matching discovered devices
            matches = []

            for protocol, devices in discovery_results.items():
                for device in devices:
                    match_score = self._calculate_device_match_score(candidate, device)
                    if match_score > 0.5:  # Threshold for correlation
                        matches.append(
                            {
                                "device": device,
                                "protocol": protocol,
                                "match_score": match_score,
                            }
                        )

            # Sort by match score and take best matches
            matches.sort(key=lambda x: x["match_score"], reverse=True)
            candidate.network_discovery_results = {
                "matches": matches[:3],  # Top 3 matches
                "auto_discovery_successful": len(matches) > 0,
            }

    def _calculate_device_match_score(
        self, candidate: DeviceCandidate, discovered_device: Dict[str, Any]
    ) -> float:
        """Calculate how well a candidate matches a discovered device."""

        score = 0.0

        # Brand matching
        if candidate.detected_brand:
            device_name = discovered_device.get("name", "").lower()
            if candidate.detected_brand.lower() in device_name:
                score += 0.4

        # Function/type matching
        if candidate.detected_function:
            device_type = discovered_device.get("type", "").lower()
            if candidate.detected_function.lower() in device_type:
                score += 0.3

        # Keyword matching
        for keyword in candidate.extracted_keywords:
            device_info = str(discovered_device).lower()
            if keyword.lower() in device_info:
                score += 0.1

        return min(score, 1.0)

    async def _add_user_message(
        self,
        session: InterviewSession,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add user message to conversation log."""
        session.conversation_log.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "user",
                "message": message,
                "context": context or {},
            }
        )

    async def _add_ai_response(self, session: InterviewSession, message: str) -> None:
        """Add AI response to conversation log."""
        session.conversation_log.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "assistant",
                "message": message,
            }
        )

    def _find_candidate(
        self, session: InterviewSession, candidate_id: str
    ) -> Optional[DeviceCandidate]:
        """Find a device candidate by ID."""
        for candidate_data in session.device_candidates:
            if candidate_data.get("id") == candidate_id:
                # Convert back to DeviceCandidate object
                candidate = DeviceCandidate(
                    candidate_data["user_description"], candidate_data["session_id"]
                )
                candidate.id = candidate_data["id"]
                candidate.__dict__.update(candidate_data)
                return candidate
        return None

    async def _create_device_configuration(
        self, candidate_data: Dict[str, Any], config_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create device configuration from candidate and user input."""

        # This would integrate with actual device configuration systems
        device_config = {
            "id": f"device_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "name": candidate_data.get("user_description"),
            "brand": candidate_data.get("detected_brand"),
            "model": candidate_data.get("detected_model"),
            "function": candidate_data.get("detected_function"),
            "integration_type": candidate_data.get("recommended_integration"),
            "configuration": config_info.get(candidate_data.get("id"), {}),
            "status": "configured",
        }

        return device_config

    async def _generate_twin_creation_offer(
        self, configured_devices: List[Dict[str, Any]]
    ) -> str:
        """Generate offer to create digital twins."""

        device_count = len(configured_devices)
        device_list = ", ".join([d.get("name", "device") for d in configured_devices])

        return f"""Great! I've successfully configured {device_count} device{"s" if device_count > 1 else ""}: {device_list}.

Would you like me to create digital twins for these devices? Digital twins provide:
• Safe testing without affecting your real devices
• Predictive insights about usage and efficiency
• Scenario planning (power outages, vacations, etc.)
• Accelerated learning and optimization

I can create different levels of detail:
• Basic: Simple state tracking and predictions (recommended)
• Advanced: Physics-based modeling with environmental factors
• Expert: Machine learning with usage pattern optimization

Would you like digital twins, and if so, which level?"""

    async def _generate_completion_summary(self, session: InterviewSession) -> str:
        """Generate completion summary without twins."""

        device_count = len(session.configured_devices)

        return f"""Perfect! I've successfully set up {device_count} device{"s" if device_count > 1 else ""} for your smart home.

Your devices are now integrated and ready to use. You can monitor and control them through the consciousness system.

Is there anything else you'd like to set up or any questions about your devices?"""

    async def _generate_completion_summary_with_twins(
        self, session: InterviewSession, created_twins: List[Any]
    ) -> str:
        """Generate completion summary with digital twins."""

        device_count = len(session.configured_devices)
        twin_count = len(created_twins)

        return f"""Excellent! I've successfully completed your smart home setup:

✅ {device_count} device{"s" if device_count > 1 else ""} configured and integrated
✅ {twin_count} digital twin{"s" if twin_count > 1 else ""} created and synchronized

Your digital twins are now learning from your devices and will provide insights about usage patterns, energy efficiency, and optimization opportunities.

Your smart home consciousness system is fully operational! Is there anything else you'd like to explore?"""

    async def _generate_contextual_response(
        self, session: InterviewSession, user_message: str
    ) -> str:
        """Generate contextual response using LLM."""

        context_prompt = f"""
        You are helping a user set up their smart home devices through a conversational interview.

        Current phase: {session.current_phase}
        Discovered devices: {len(session.device_candidates)}
        Configured devices: {len(session.configured_devices)}

        User said: "{user_message}"

        Provide a helpful, natural response that continues the conversation appropriately.
        """

        try:
            response = await self._call_llm(context_prompt)
            return response
        except Exception as e:
            logger.error(f"Error generating contextual response: {e}")
            return "I'm here to help with your smart home setup. What would you like to know?"

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM API with proper error handling."""
        try:
            # This would integrate with your LLM client
            # For now, return a placeholder
            return "I understand. Let me help you with that."
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return "I'm having trouble processing that. Could you try rephrasing?"

    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current status of an interview session."""

        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        progress_percentage = (
            len(session.completed_steps) / max(len(session.completed_steps) + 3, 6)
        ) * 100

        return {
            "session_id": session.session_id,
            "house_id": session.house_id,
            "status": session.status,
            "current_phase": session.current_phase,
            "progress_percentage": progress_percentage,
            "discovered_devices": len(session.device_candidates),
            "configured_devices": len(session.configured_devices),
            "created_twins": len(session.created_twins),
            "started_at": session.started_at.isoformat(),
            "completed_at": session.completed_at.isoformat()
            if session.completed_at
            else None,
            "conversation_turns": len(session.conversation_log),
        }


# Extension methods for DeviceCandidate
def device_candidate_to_dict(candidate: DeviceCandidate) -> Dict[str, Any]:
    """Convert DeviceCandidate to dictionary."""
    return {
        "id": candidate.id,
        "session_id": candidate.session_id,
        "user_description": candidate.user_description,
        "extracted_keywords": candidate.extracted_keywords,
        "detected_brand": candidate.detected_brand,
        "detected_model": candidate.detected_model,
        "detected_function": candidate.detected_function,
        "confidence_score": candidate.confidence_score,
        "possible_integrations": candidate.possible_integrations,
        "recommended_integration": candidate.recommended_integration,
        "integration_confidence": candidate.integration_confidence,
        "network_discovery_results": candidate.network_discovery_results,
        "auto_discovery_successful": candidate.auto_discovery_successful,
        "status": candidate.status,
        "rejection_reason": candidate.rejection_reason,
        "validation_errors": candidate.validation_errors,
        "created_device_id": candidate.created_device_id,
        "created_twin_id": candidate.created_twin_id,
    }


# Monkey patch the to_dict method
DeviceCandidate.to_dict = device_candidate_to_dict
