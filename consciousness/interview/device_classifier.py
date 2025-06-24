"""
LLM-powered device classification from natural language descriptions.

This module uses large language models to extract structured device information
from natural language user descriptions, classify device types, and match them
to appropriate integration patterns.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DeviceClassifier:
    """LLM-powered device classification from natural language."""

    def __init__(self, llm_client: Any):
        self.llm_client = llm_client
        self._initialize_classification_patterns()

    def _initialize_classification_patterns(self) -> None:
        """Initialize device classification patterns and mappings."""

        # Brand patterns for fallback recognition
        self.brand_patterns = {
            r"\b(philips|hue)\b": "Philips",
            r"\b(nest|google nest)\b": "Google Nest",
            r"\b(ring)\b": "Ring",
            r"\b(tesla)\b": "Tesla",
            r"\b(sonos)\b": "Sonos",
            r"\b(roku)\b": "Roku",
            r"\b(samsung|smartthings)\b": "Samsung",
            r"\b(amazon|alexa|echo)\b": "Amazon",
            r"\b(lifx)\b": "LIFX",
            r"\b(tp-?link|kasa)\b": "TP-Link",
            r"\b(lutron)\b": "Lutron",
            r"\b(ecobee)\b": "Ecobee",
            r"\b(arlo)\b": "Arlo",
            r"\b(yale)\b": "Yale",
            r"\b(august)\b": "August",
            r"\b(honeywell)\b": "Honeywell",
        }

        # Function patterns for fallback recognition
        self.function_patterns = {
            r"\b(light|bulb|lamp|lighting)\b": "lighting",
            r"\b(thermostat|temperature|climate|hvac|heat|cool)\b": "climate",
            r"\b(camera|security|surveillance)\b": "security",
            r"\b(doorbell|door bell)\b": "doorbell",
            r"\b(sensor|motion|door|window)\b": "sensor",
            r"\b(lock|smart lock|door lock)\b": "lock",
            r"\b(switch|outlet|plug|socket)\b": "switch",
            r"\b(speaker|audio|music)\b": "media",
            r"\b(tv|television|streaming)\b": "media",
            r"\b(energy|solar|battery|power)\b": "energy",
            r"\b(vacuum|robot|clean)\b": "vacuum",
            r"\b(garage|garage door)\b": "garage",
            r"\b(irrigation|sprinkler|water)\b": "irrigation",
        }

        # Device keywords for confidence scoring
        self.device_keywords = [
            "smart",
            "connected",
            "wifi",
            "bluetooth",
            "iot",
            "automation",
            "home",
            "control",
            "app",
            "voice",
            "remote",
            "wireless",
            "hub",
            "bridge",
            "zigbee",
            "zwave",
            "matter",
            "homekit",
            "google",
            "alexa",
        ]

    async def extract_device_mentions(self, user_input: str) -> List[Dict[str, Any]]:
        """Extract device mentions from user input using LLM."""

        logger.info(f"Extracting device mentions from: '{user_input[:100]}...'")

        # Create comprehensive prompt for device extraction
        prompt = self._create_device_extraction_prompt(user_input)

        try:
            # Call LLM for structured extraction
            response = await self._call_llm(prompt)
            devices = self._parse_llm_device_response(response)

            # Enhance with fallback pattern matching
            devices = await self._enhance_with_pattern_matching(devices, user_input)

            # Calculate confidence scores
            for device in devices:
                device["confidence"] = self._calculate_confidence(device, user_input)

            logger.info(f"Extracted {len(devices)} device mentions")
            return devices

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            # Fallback to pattern-based extraction
            return await self._fallback_pattern_extraction(user_input)

    def _create_device_extraction_prompt(self, user_input: str) -> str:
        """Create a comprehensive prompt for device extraction."""

        return f"""
        Extract smart home devices mentioned in this text: "{user_input}"

        For each device, identify:
        - description: The exact text the user used to describe the device
        - brand: Brand name if mentioned (e.g., "Philips", "Nest", "Ring")
        - function: Device type/function (e.g., "lighting", "climate", "security", "sensor")
        - model: Specific model if mentioned (e.g., "Hue Color Bulb", "Video Doorbell Pro")
        - location: Room or area mentioned (e.g., "living room", "kitchen", "outdoor")
        - keywords: List of relevant terms that help identify this device
        - count: Number of devices if specified (e.g., "three lights" = 3)

        Return as a JSON array. If no smart devices are found, return an empty array.

        Example output:
        [
          {{
            "description": "Philips Hue lights in the living room",
            "brand": "Philips",
            "function": "lighting",
            "model": "Hue",
            "location": "living room",
            "keywords": ["philips", "hue", "lights", "living room"],
            "count": 1
          }}
        ]

        Text to analyze: "{user_input}"
        """

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM API with proper error handling."""
        try:
            # This would integrate with your specific LLM client
            # For now, return a structured response based on patterns
            return await self._simulate_llm_response(prompt)
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    async def _simulate_llm_response(self, prompt: str) -> str:
        """Simulate LLM response for development/testing."""

        # Extract the user input from the prompt
        text_match = re.search(r'Text to analyze: "(.*?)"', prompt, re.DOTALL)
        if not text_match:
            return "[]"

        user_input = text_match.group(1).lower()
        devices = []

        # Simple pattern-based extraction for simulation
        patterns = [
            (r"(philips\s+hue|hue)\s+(lights?|bulbs?)", "Philips", "lighting", "Hue"),
            (
                r"(nest|google\s+nest)\s+(thermostat|temperature)",
                "Google Nest",
                "climate",
                "Thermostat",
            ),
            (r"ring\s+(doorbell|camera)", "Ring", "security", "Doorbell"),
            (r"tesla\s+(powerwall|solar|energy)", "Tesla", "energy", "Powerwall"),
            (r"(smart\s+)?(lights?|bulbs?|lighting)", None, "lighting", None),
            (r"(smart\s+)?(thermostat|temperature)", None, "climate", None),
            (r"(security\s+)?(cameras?|surveillance)", None, "security", None),
            (r"(smart\s+)?(plugs?|outlets?|switches?)", None, "switch", None),
        ]

        for pattern, brand, function, model in patterns:
            matches = re.finditer(pattern, user_input, re.IGNORECASE)
            for match in matches:
                description = match.group(0)

                # Look for location context
                location = self._extract_location_context(
                    user_input, match.start(), match.end()
                )

                device = {
                    "description": description,
                    "brand": brand,
                    "function": function,
                    "model": model,
                    "location": location,
                    "keywords": description.lower().split(),
                    "count": 1,
                }
                devices.append(device)

        return json.dumps(devices)

    def _extract_location_context(
        self, text: str, start: int, end: int
    ) -> Optional[str]:
        """Extract location context around a device mention."""

        # Look for room/location keywords near the device mention
        location_keywords = [
            "living room",
            "bedroom",
            "kitchen",
            "bathroom",
            "garage",
            "basement",
            "attic",
            "office",
            "dining room",
            "hallway",
            "outdoor",
            "outside",
            "patio",
            "deck",
            "yard",
            "garden",
        ]

        # Check words before and after the match
        words_before = text[:start].lower().split()[-5:]  # 5 words before
        words_after = text[end:].lower().split()[:5]  # 5 words after
        context_words = words_before + words_after

        context_text = " ".join(context_words)

        for location in location_keywords:
            if location in context_text:
                return location

        return None

    def _parse_llm_device_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response and extract device information."""

        try:
            devices = json.loads(response)
            if not isinstance(devices, list):
                logger.warning("LLM response is not a list, wrapping in list")
                devices = [devices] if devices else []

            # Validate and clean device entries
            cleaned_devices = []
            for device in devices:
                if isinstance(device, dict) and "description" in device:
                    # Ensure required fields exist
                    cleaned_device = {
                        "description": device.get("description", ""),
                        "brand": device.get("brand"),
                        "function": device.get("function"),
                        "model": device.get("model"),
                        "location": device.get("location"),
                        "keywords": device.get("keywords", []),
                        "count": device.get("count", 1),
                    }
                    cleaned_devices.append(cleaned_device)

            return cleaned_devices

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return []

    async def _enhance_with_pattern_matching(
        self, devices: List[Dict[str, Any]], user_input: str
    ) -> List[Dict[str, Any]]:
        """Enhance LLM results with pattern matching for missing information."""

        for device in devices:
            # Fill in missing brand information
            if not device.get("brand"):
                device["brand"] = self._extract_brand_from_text(user_input)

            # Fill in missing function information
            if not device.get("function"):
                device["function"] = self._extract_function_from_text(user_input)

            # Enhance keywords
            extracted_keywords = self._extract_keywords(user_input)
            existing_keywords = device.get("keywords", [])
            device["keywords"] = list(set(existing_keywords + extracted_keywords))

        return devices

    def _extract_brand_from_text(self, text: str) -> Optional[str]:
        """Extract brand using pattern matching."""

        text_lower = text.lower()
        for pattern, brand in self.brand_patterns.items():
            if re.search(pattern, text_lower):
                return brand
        return None

    def _extract_function_from_text(self, text: str) -> Optional[str]:
        """Extract function using pattern matching."""

        text_lower = text.lower()
        for pattern, function in self.function_patterns.items():
            if re.search(pattern, text_lower):
                return function
        return None

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text."""

        words = re.findall(r"\b\w+\b", text.lower())
        keywords = []

        for word in words:
            if word in self.device_keywords or len(word) > 3:
                keywords.append(word)

        return list(set(keywords))

    def _calculate_confidence(self, device: Dict[str, Any], user_input: str) -> float:
        """Calculate confidence score for device extraction."""

        confidence = 0.0

        # Base confidence from having key information
        if device.get("brand"):
            confidence += 0.3
        if device.get("function"):
            confidence += 0.3
        if device.get("description"):
            confidence += 0.2

        # Boost confidence for keyword matches
        keywords = device.get("keywords", [])
        keyword_matches = sum(
            1 for keyword in keywords if keyword in self.device_keywords
        )
        confidence += min(keyword_matches * 0.05, 0.2)

        return min(confidence, 1.0)

    async def _fallback_pattern_extraction(
        self, user_input: str
    ) -> List[Dict[str, Any]]:
        """Fallback extraction using only pattern matching."""

        logger.info("Using fallback pattern extraction")

        devices = []
        text_lower = user_input.lower()

        # Look for brand + function combinations
        for brand_pattern, brand in self.brand_patterns.items():
            for func_pattern, function in self.function_patterns.items():
                pattern = f"({brand_pattern}).*?({func_pattern})|({func_pattern}).*?({brand_pattern})"
                matches = re.finditer(pattern, text_lower)

                for match in matches:
                    description = match.group(0)
                    keywords = description.split()

                    device = {
                        "description": description,
                        "brand": brand,
                        "function": function,
                        "model": None,
                        "location": self._extract_location_context(
                            user_input, match.start(), match.end()
                        ),
                        "keywords": keywords,
                        "count": 1,
                    }
                    devices.append(device)

        # Remove duplicates
        unique_devices = []
        seen_descriptions = set()

        for device in devices:
            desc = device["description"]
            if desc not in seen_descriptions:
                seen_descriptions.add(desc)
                unique_devices.append(device)

        return unique_devices

    async def parse_classification_response(
        self, user_message: str, device_candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Parse user response for device classification confirmations/corrections."""

        prompt = f"""
        The user is responding to questions about their smart home devices.

        Current device candidates:
        {json.dumps(device_candidates, indent=2)}

        User response: "{user_message}"

        Parse the user's response for:
        - Confirmations (yes, correct, that's right)
        - Corrections (brand names, device types, models)
        - Additional information
        - Rejections (no, that's not right, don't have that)

        Return JSON array with updates for each candidate:
        [
          {{
            "candidate_id": "candidate_id_here",
            "confirmed": true/false,
            "brand_correction": "corrected brand if any",
            "function_correction": "corrected function if any",
            "model_correction": "corrected model if any",
            "additional_info": "any additional details"
          }}
        ]
        """

        try:
            response = await self._call_llm(prompt)
            return json.loads(response)
        except Exception as e:
            logger.error(f"Failed to parse classification response: {e}")
            return []

    async def extract_configuration_info(
        self, user_message: str, device_candidates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract configuration information from user response."""

        prompt = f"""
        Extract configuration information from the user's response about their devices.

        Devices being configured:
        {json.dumps(device_candidates, indent=2)}

        User response: "{user_message}"

        Look for:
        - Hub/bridge information (IP addresses, device IDs)
        - Account credentials or app usage
        - Network connection details
        - Device-specific settings
        - Location/room assignments

        Return JSON with configuration data:
        {{
          "device_id_1": {{
            "hub_ip": "192.168.1.100",
            "account_info": "uses_app_name",
            "network": "wifi",
            "location": "living room"
          }}
        }}
        """

        try:
            response = await self._call_llm(prompt)
            return json.loads(response)
        except Exception as e:
            logger.error(f"Failed to extract configuration info: {e}")
            return {}

    async def parse_twin_preferences(self, user_message: str) -> Dict[str, Any]:
        """Parse user preferences for digital twin creation."""

        prompt = f"""
        Parse the user's preferences for digital twin creation.

        User response: "{user_message}"

        Determine:
        - create_twins: true/false (do they want digital twins?)
        - fidelity_level: "basic", "advanced", or "expert"
        - enable_predictions: true/false
        - enable_scenarios: true/false
        - enable_learning: true/false
        - physics_modeling: true/false

        Return JSON:
        {{
          "create_twins": true/false,
          "fidelity_level": "basic/advanced/expert",
          "enable_predictions": true/false,
          "enable_scenarios": true/false,
          "enable_learning": true/false,
          "physics_modeling": true/false
        }}
        """

        try:
            response = await self._call_llm(prompt)
            return json.loads(response)
        except Exception as e:
            logger.error(f"Failed to parse twin preferences: {e}")
            return {"create_twins": False}

    async def classify_user_intent(
        self, user_message: str, current_phase: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Classify user intent for conversation management."""

        prompt = f"""
        Classify the user's intent in this smart home setup conversation.

        Current phase: {current_phase}
        Context: {json.dumps(context)}
        User message: "{user_message}"

        Determine the intent type:
        - "clarification_request": User is asking for clarification
        - "correction": User is correcting previous information
        - "additional_device": User is mentioning another device
        - "confirmation": User is confirming something
        - "help": User needs help or guidance
        - "general": General conversation

        Return JSON:
        {{
          "type": "intent_type",
          "confidence": 0.0-1.0,
          "details": "any relevant details"
        }}
        """

        try:
            response = await self._call_llm(prompt)
            return json.loads(response)
        except Exception as e:
            logger.error(f"Failed to classify user intent: {e}")
            return {"type": "general", "confidence": 0.5}
