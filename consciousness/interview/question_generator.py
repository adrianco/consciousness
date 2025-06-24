"""
Dynamic question generator for device discovery interviews.

This module generates contextual questions for different phases of the device
discovery interview, adapting to specific device types, integration requirements,
and user responses.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class QuestionGenerator:
    """Generates contextual questions for device discovery interviews."""

    def __init__(self):
        self._initialize_question_templates()

    def _initialize_question_templates(self) -> None:
        """Initialize question templates for different scenarios."""

        # Integration-specific questions
        self.integration_questions = {
            "hue": [
                "Do you have a Philips Hue Bridge? It's usually a white device connected to your router.",
                "What types of Hue devices do you have? (bulbs, light strips, motion sensors, etc.)",
                "Are they all connected through the Hue app?",
                "How many Hue lights do you have in total?",
            ],
            "nest": [
                "Do you use the Nest app or Google Home to control your thermostat?",
                "What's the model of your Nest device?",
                "Is it connected to your Google account?",
                "Do you have any other Nest devices like cameras or smoke detectors?",
            ],
            "ring": [
                "What Ring devices do you have? (doorbell, cameras, alarm, etc.)",
                "Do you use the Ring app to view them?",
                "Are they all on the same Ring account?",
                "Do you have a Ring Alarm system or just cameras?",
            ],
            "tesla": [
                "Do you have Tesla Powerwall, solar panels, or vehicle charging?",
                "Do you monitor it through the Tesla app?",
                "Is your Tesla vehicle connected to your home energy system?",
                "What's your setup for energy storage and solar?",
            ],
            "sonos": [
                "How many Sonos speakers do you have?",
                "Which rooms have Sonos speakers?",
                "Do you control them through the Sonos app?",
                "Do you have any Sonos soundbars or subwoofers?",
            ],
            "smartthings": [
                "Do you have a SmartThings hub?",
                "What devices are connected through SmartThings?",
                "Do you use the SmartThings app to control everything?",
                "Are any devices using Z-Wave or Zigbee protocols?",
            ],
            "lifx": [
                "How many LIFX bulbs do you have?",
                "Do you control them through the LIFX app?",
                "Are they all on the same WiFi network?",
                "Do you use any LIFX light strips or other products?",
            ],
            "kasa": [
                "What TP-Link Kasa devices do you have? (plugs, switches, cameras)",
                "Do you control them through the Kasa app?",
                "Are they all connected to your WiFi?",
                "How many smart plugs or switches do you have?",
            ],
        }

        # Room-based discovery questions
        self.room_questions = {
            "living_room": [
                "In your living room, what smart devices do you have?",
                "Do you have smart lighting, TV, speakers, or other devices there?",
                "Any entertainment systems or media devices that are connected?",
                "Do you have smart switches or plugs controlling lamps or other items?",
            ],
            "bedroom": [
                "In your bedroom, do you have any smart lights, fans, or other connected devices?",
                "Any smart switches for lamps or ceiling fans?",
                "Do you have a smart alarm clock, speaker, or charging station?",
                "Any window shades or climate control devices?",
            ],
            "kitchen": [
                "What about your kitchen? Any smart appliances, lights, or sensors?",
                "Do you have smart switches for under-cabinet lighting?",
                "Any connected appliances like refrigerators, coffee makers, or ovens?",
                "Do you have smart faucets, garbage disposals, or exhaust fans?",
            ],
            "bathroom": [
                "Do you have any devices in your bathroom? Smart switches, fans, or sensors?",
                "Any smart mirrors, lighting, or exhaust fans?",
                "Do you have smart water leak sensors or humidity monitors?",
                "Any connected towel warmers or heated floors?",
            ],
            "outdoor": [
                "What smart devices do you have outdoors? Lights, cameras, or irrigation?",
                "Do you have smart outdoor lighting or security cameras?",
                "Any smart sprinkler systems or garden sensors?",
                "Smart garage door openers or outdoor speakers?",
            ],
        }

        # Function-based discovery questions
        self.function_questions = {
            "lighting": [
                "Tell me about your smart lighting setup.",
                "Do you have smart bulbs, switches, or dimmers?",
                "Which rooms have smart lighting?",
                "Do you use any lighting scenes or automation?",
            ],
            "climate": [
                "How do you control your home's temperature?",
                "Do you have a smart thermostat?",
                "Any smart fans, space heaters, or window AC units?",
                "Do you have humidity sensors or air quality monitors?",
            ],
            "security": [
                "What about security? Any cameras, doorbells, or alarm systems?",
                "Do you have outdoor security cameras?",
                "Any smart door locks or window sensors?",
                "Do you have a security system with monitoring?",
            ],
            "entertainment": [
                "What entertainment devices do you have?",
                "Smart TVs, streaming devices, or speakers?",
                "Do you have a whole-home audio system?",
                "Any gaming consoles or media servers that are connected?",
            ],
            "energy": [
                "Do you monitor or manage your home's energy usage?",
                "Any solar panels, battery systems, or EV charging?",
                "Smart plugs for monitoring device power usage?",
                "Do you have smart water heaters or HVAC systems?",
            ],
        }

        # App-based discovery questions
        self.app_questions = [
            "What apps do you use to control things in your home?",
            "Do you use voice assistants like Alexa, Google Assistant, or Siri?",
            "Which smart home apps are installed on your phone?",
            "Do you use any automation apps like IFTTT or SmartThings?",
        ]

        # Configuration clarification questions
        self.config_questions = {
            "hub_required": [
                "Do you have a hub or bridge device for your {brand} devices?",
                "Can you see the hub device? It's usually connected to your router.",
                "What's the status light showing on your hub?",
                "Is your hub showing up in the app as connected?",
            ],
            "auth_required": [
                "Do you currently use an app to control your {brand} devices?",
                "What account do you use to sign into the {brand} app?",
                "Are you signed in to the app right now?",
                "Would you be comfortable letting me connect to your {brand} account?",
            ],
            "network_info": [
                "Are your {brand} devices on the same WiFi network as this system?",
                "Do you see your devices in the {brand} app?",
                "Are they showing as online and working normally?",
                "Have you had any connectivity issues with these devices?",
            ],
        }

        # Twin creation questions
        self.twin_questions = {
            "benefits_explanation": [
                "Digital twins create virtual copies of your devices for safe testing and optimization.",
                "They can predict energy usage, detect problems early, and suggest improvements.",
                "You can run 'what-if' scenarios without affecting your real devices.",
                "Would you like me to create digital twins for better insights?",
            ],
            "fidelity_preferences": [
                "I can create different levels of digital twin detail:",
                "• Basic: Simple state tracking and basic predictions",
                "• Advanced: Physics-based modeling with environmental factors",
                "• Expert: Machine learning with usage pattern optimization",
                "Which level would you prefer?",
            ],
        }

    def generate_discovery_questions(
        self, strategy: str = "natural", context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Generate initial discovery questions based on strategy."""

        context = context or {}

        if strategy == "room_based":
            return self._generate_room_sequence()
        elif strategy == "function_based":
            return self._generate_function_sequence()
        elif strategy == "app_based":
            return self.app_questions.copy()
        else:
            # Natural conversation approach
            return [
                "Tell me about the smart devices in your home. You can describe them however feels natural - by room, by what they do, or just whatever comes to mind.",
                "For example, you might say 'I have Philips Hue lights in the living room' or 'We have a Nest thermostat and some security cameras.'",
            ]

    def _generate_room_sequence(self) -> List[str]:
        """Generate room-by-room discovery questions."""
        questions = []
        for room, room_questions in self.room_questions.items():
            questions.extend(room_questions)
        return questions

    def _generate_function_sequence(self) -> List[str]:
        """Generate function-based discovery questions."""
        questions = []
        for function, func_questions in self.function_questions.items():
            questions.extend(func_questions)
        return questions

    def generate_integration_questions(
        self, integration_type: str, device_info: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Generate questions specific to an integration type."""

        questions = self.integration_questions.get(integration_type, [])

        if not questions:
            # Generate generic questions for unknown integrations
            brand = (
                device_info.get("detected_brand", "device") if device_info else "device"
            )
            questions = [
                f"Tell me more about your {brand} devices.",
                f"How do you currently control your {brand} devices?",
                f"Do you use an app or voice commands to control them?",
                f"Are they all working properly and connected to your network?",
            ]

        return questions.copy()

    def generate_configuration_questions(
        self,
        integration_type: str,
        requirements: Dict[str, Any],
        device_info: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Generate configuration questions based on integration requirements."""

        questions = []
        brand = device_info.get("detected_brand", "device") if device_info else "device"

        # Add hub questions if required
        if requirements.get("requires_hub", False):
            hub_questions = [
                q.format(brand=brand) for q in self.config_questions["hub_required"]
            ]
            questions.extend(hub_questions)

        # Add authentication questions if required
        if requirements.get("auth_required", False):
            auth_questions = [
                q.format(brand=brand) for q in self.config_questions["auth_required"]
            ]
            questions.extend(auth_questions)

        # Add network questions
        network_questions = [
            q.format(brand=brand) for q in self.config_questions["network_info"]
        ]
        questions.extend(network_questions)

        return questions

    def generate_clarification_questions(
        self, device_candidates: List[Dict[str, Any]], unclear_aspects: List[str]
    ) -> List[str]:
        """Generate clarification questions for unclear device information."""

        questions = []

        for candidate in device_candidates:
            description = candidate.get("user_description", "device")
            brand = candidate.get("detected_brand")
            function = candidate.get("detected_function")
            confidence = candidate.get("confidence_score", 0.0)

            if confidence < 0.5:
                # Low confidence - ask for clarification
                questions.append(
                    f"You mentioned '{description}'. What brand and type of device is that?"
                )
            elif confidence < 0.8:
                # Medium confidence - ask for confirmation with best guess
                if brand and function:
                    questions.append(
                        f"I think '{description}' is a {brand} {function}. Is that correct?"
                    )
                elif brand:
                    questions.append(f"Is '{description}' a {brand} device? What type?")
                elif function:
                    questions.append(f"Is '{description}' for {function}? What brand?")
            else:
                # High confidence - just confirm
                if brand and function:
                    questions.append(f"I found {brand} {function}. Is that right?")

        return questions

    def generate_twin_creation_questions(
        self, configured_devices: List[Dict[str, Any]], phase: str = "offer"
    ) -> List[str]:
        """Generate questions about digital twin creation."""

        if phase == "offer":
            device_names = [d.get("name", "device") for d in configured_devices]
            device_list = ", ".join(device_names)

            questions = [
                f"Great! I've configured: {device_list}",
                "",  # Empty line for formatting
                "Would you like me to create digital twins for these devices?",
            ]
            questions.extend(self.twin_questions["benefits_explanation"])
            return questions

        elif phase == "fidelity":
            return self.twin_questions["fidelity_preferences"]

        return []

    def generate_followup_questions(
        self, context: str, user_response: str, missing_info: List[str]
    ) -> List[str]:
        """Generate follow-up questions based on user response and missing information."""

        questions = []

        for info_type in missing_info:
            if info_type == "brand":
                questions.append("What brand is that device?")
            elif info_type == "function":
                questions.append(
                    "What type of device is it? (lights, thermostat, camera, etc.)"
                )
            elif info_type == "location":
                questions.append("Which room or area is that device in?")
            elif info_type == "count":
                questions.append("How many of those devices do you have?")
            elif info_type == "model":
                questions.append("Do you know the specific model or product name?")
            elif info_type == "connection":
                questions.append(
                    "How is that device connected? (WiFi, hub, directly wired?)"
                )

        return questions

    def generate_error_recovery_questions(
        self, error_type: str, context: Dict[str, Any]
    ) -> List[str]:
        """Generate questions to recover from errors or misunderstandings."""

        if error_type == "no_devices_detected":
            return [
                "I didn't catch any specific smart devices in what you said.",
                "Could you tell me about specific devices you have?",
                "For example: 'I have smart lights' or 'We have a Nest thermostat'",
            ]

        elif error_type == "unclear_description":
            return [
                "I'm not sure I understood that correctly.",
                "Could you describe your devices in a different way?",
                "Maybe tell me the brand names or what they control?",
            ]

        elif error_type == "conflicting_information":
            return [
                "I'm getting some conflicting information.",
                "Let me ask about each device separately to make sure I understand.",
                "Can we go through them one by one?",
            ]

        elif error_type == "technical_failure":
            return [
                "I had a technical issue processing that.",
                "Could you try describing your devices again?",
                "Maybe start with just one or two devices?",
            ]

        return [
            "I'm having trouble understanding. Could you try explaining that differently?",
            "Let's start over with a simple description of your devices.",
        ]

    def adapt_questions_to_user_style(
        self, questions: List[str], user_style: str = "casual"
    ) -> List[str]:
        """Adapt questions to match user communication style."""

        if user_style == "technical":
            # Make questions more technical/detailed
            adapted = []
            for q in questions:
                q = q.replace("app", "application")
                q = q.replace("WiFi", "Wi-Fi network")
                q = q.replace("connected", "networked")
                adapted.append(q)
            return adapted

        elif user_style == "casual":
            # Make questions more conversational
            adapted = []
            for q in questions:
                q = q.replace("device", "thing")
                q = q.replace("connected", "hooked up")
                adapted.append(q)
            return adapted

        # Default - return as-is
        return questions.copy()

    def select_best_questions(
        self,
        available_questions: List[str],
        context: Dict[str, Any],
        max_questions: int = 3,
    ) -> List[str]:
        """Select the most relevant questions from available options."""

        # For now, just return the first max_questions
        # In a more sophisticated implementation, this could use:
        # - User preferences
        # - Conversation history
        # - Device complexity
        # - Time constraints

        return available_questions[:max_questions]

    def format_questions_for_response(
        self, questions: List[str], style: str = "numbered"
    ) -> str:
        """Format questions for presentation to user."""

        if not questions:
            return ""

        if len(questions) == 1:
            return questions[0]

        if style == "numbered":
            formatted = ""
            for i, question in enumerate(questions, 1):
                formatted += f"{i}. {question}\n"
            return formatted.rstrip()

        elif style == "bulleted":
            formatted = ""
            for question in questions:
                formatted += f"• {question}\n"
            return formatted.rstrip()

        elif style == "paragraph":
            return " ".join(questions)

        # Default - just join with newlines
        return "\n".join(questions)
