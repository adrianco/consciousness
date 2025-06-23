# Dynamic Device Integration Through Conversational Interviews

## Overview

This guide implements a revolutionary approach to IoT device integration using conversational interviews instead of fixed device types. The system leverages Home Assistant's 2000+ integration patterns to dynamically discover, classify, and integrate any smart home device through natural language conversations.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  Conversational Interview Engine             │
├───────────────┬────────────────┬────────────────────────────┤
│   Natural     │    Device      │   Integration Template     │
│  Language     │ Classification │       Matching            │
│  Processing   │   (LLM-based)  │   (Home Assistant)        │
├───────────────┴────────────────┴────────────────────────────┤
│                   Automatic Discovery Layer                  │
├──────┬──────┬──────┬──────┬──────┬──────┬─────────────────┤
│ DHCP │mDNS  │Bluetooth│UPnP│Zigbee│Matter│   Protocol     │
│Scan  │Scan  │  Scan   │Scan│ Scan │ Scan │   Extensions   │
├──────┴──────┴──────┴──────┴──────┴──────┴─────────────────┤
│                   Dynamic Integration Factory                 │
├──────┬──────┬──────┬──────┬──────┬──────┬─────────────────┤
│ Hue  │Nest  │Ring  │Tesla │LIFX  │Kasa  │   2000+ More   │
└──────┴──────┴──────┴──────┴──────┴──────┴─────────────────┘
```

## Phase 1: Interview Engine Implementation

### 1.1 Conversational Interview Controller

```python
# consciousness/interview/interview_controller.py
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from consciousness.models.interview import InterviewSession, DeviceCandidate
from consciousness.repositories.consciousness import InterviewRepository, DeviceCandidateRepository
from consciousness.interview.device_classifier import DeviceClassifier
from consciousness.interview.question_generator import QuestionGenerator
from consciousness.discovery.auto_discovery import AutoDiscoveryService

class InterviewController:
    """Manages the conversational device discovery process."""
    
    def __init__(
        self,
        session: AsyncSession,
        llm_client: Any,  # OpenAI or Anthropic client
        auto_discovery: AutoDiscoveryService
    ):
        self.session = session
        self.llm_client = llm_client
        self.auto_discovery = auto_discovery
        
        self.interview_repo = InterviewRepository(session)
        self.candidate_repo = DeviceCandidateRepository(session)
        self.classifier = DeviceClassifier(llm_client)
        self.question_gen = QuestionGenerator()
    
    async def start_interview(self, house_id: int) -> InterviewSession:
        """Start a new device discovery interview."""
        
        # Check for existing active session
        existing = await self.interview_repo.get_active_session(house_id)
        if existing:
            return existing
        
        # Create new interview session
        interview = await self.interview_repo.create(
            house_id=house_id,
            session_type="device_discovery",
            status="active",
            started_at=datetime.utcnow(),
            current_phase="introduction"
        )
        
        # Add welcome message
        await self.add_ai_response(
            interview.id,
            "Hi! I'm here to learn about the smart devices in your home. "
            "Tell me about any connected devices you have - you can describe "
            "them however feels natural, by room, by brand, or just whatever "
            "comes to mind."
        )
        
        return interview
    
    async def process_user_message(
        self, 
        interview_id: int, 
        user_message: str
    ) -> Dict[str, Any]:
        """Process user input and generate appropriate response."""
        
        # Add user message to conversation log
        await self.interview_repo.add_conversation_turn(
            interview_id, "user", user_message
        )
        
        # Get current interview state
        interview = await self.interview_repo.get(interview_id)
        
        if interview.current_phase == "introduction":
            return await self._handle_initial_discovery(interview, user_message)
        elif interview.current_phase == "classification":
            return await self._handle_device_classification(interview, user_message)
        elif interview.current_phase == "configuration":
            return await self._handle_device_configuration(interview, user_message)
        else:
            return await self._handle_general_response(interview, user_message)
    
    async def _handle_initial_discovery(
        self, 
        interview: InterviewSession, 
        user_message: str
    ) -> Dict[str, Any]:
        """Handle the initial device discovery phase."""
        
        # Use LLM to extract device mentions from user input
        device_mentions = await self.classifier.extract_device_mentions(
            user_message
        )
        
        # Create device candidates for each mention
        candidates = []
        for mention in device_mentions:
            candidate = await self.candidate_repo.create(
                interview_session_id=interview.id,
                user_description=mention["description"],
                extracted_keywords=mention["keywords"],
                detected_brand=mention.get("brand"),
                detected_function=mention.get("function"),
                confidence_score=mention["confidence"],
                possible_integrations=mention["integrations"]
            )
            candidates.append(candidate)
        
        # Run automatic discovery in parallel
        discovery_results = await self.auto_discovery.discover_all_protocols()
        
        # Correlate discovered devices with user mentions
        await self._correlate_discovery_results(candidates, discovery_results)
        
        # Generate follow-up questions
        if candidates:
            ai_response = await self._generate_classification_questions(candidates)
            await self.interview_repo.update(
                interview.id, 
                current_phase="classification"
            )
        else:
            ai_response = "I didn't catch any specific devices in what you said. " \
                         "Could you tell me about specific smart devices you have? " \
                         "For example, smart lights, thermostats, cameras, or speakers?"
        
        await self.add_ai_response(interview.id, ai_response)
        
        return {
            "response": ai_response,
            "candidates": [self._candidate_to_dict(c) for c in candidates],
            "phase": interview.current_phase
        }
    
    async def _generate_classification_questions(
        self, 
        candidates: List[DeviceCandidate]
    ) -> str:
        """Generate questions to clarify device details."""
        
        questions = []
        
        for candidate in candidates:
            if candidate.detected_brand and candidate.detected_function:
                # High confidence - ask for confirmation
                questions.append(
                    f"I found what looks like {candidate.detected_brand} "
                    f"{candidate.detected_function}. Is that right?"
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
    
    async def add_ai_response(self, interview_id: int, message: str):
        """Add AI response to conversation log."""
        await self.interview_repo.add_conversation_turn(
            interview_id, "assistant", message
        )
```

### 1.2 Device Classification Engine

```python
# consciousness/interview/device_classifier.py
import json
import re
from typing import Dict, List, Any, Optional
from consciousness.models.interview import IntegrationTemplate
from consciousness.repositories.consciousness import IntegrationTemplateRepository

class DeviceClassifier:
    """LLM-powered device classification from natural language."""
    
    def __init__(self, llm_client: Any):
        self.llm_client = llm_client
    
    async def extract_device_mentions(self, user_input: str) -> List[Dict[str, Any]]:
        """Extract device mentions from user input using LLM."""
        
        prompt = f"""
        Extract smart home devices mentioned in this text: "{user_input}"
        
        For each device, identify:
        - Description (exact text from user)
        - Brand (if mentioned)
        - Function/type (lighting, climate, security, etc.)
        - Model (if mentioned)
        - Keywords (list of relevant terms)
        
        Return JSON array of devices found.
        """
        
        response = await self._call_llm(prompt)
        
        try:
            devices = json.loads(response)
            
            # Enhance with integration matching
            for device in devices:
                device["integrations"] = await self._match_integrations(device)
                device["confidence"] = self._calculate_confidence(device)
            
            return devices
            
        except json.JSONDecodeError:
            # Fallback to keyword extraction
            return await self._fallback_keyword_extraction(user_input)
    
    async def _match_integrations(self, device: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Match device to Home Assistant integration patterns."""
        
        possible_integrations = []
        
        # Load integration templates (these would be pre-populated)
        templates = await self._get_integration_templates()
        
        for template in templates:
            score = self._calculate_integration_match_score(device, template)
            if score > 0.3:  # Threshold for consideration
                possible_integrations.append({
                    "integration": template.integration_name,
                    "display_name": template.display_name,
                    "score": score,
                    "requires_auth": template.auth_required,
                    "requires_hub": template.requires_hub
                })
        
        # Sort by score
        possible_integrations.sort(key=lambda x: x["score"], reverse=True)
        return possible_integrations[:5]  # Top 5 matches
    
    def _calculate_integration_match_score(
        self, 
        device: Dict[str, Any], 
        template: IntegrationTemplate
    ) -> float:
        """Calculate how well a device matches an integration template."""
        
        score = 0.0
        
        # Brand matching
        if device.get("brand"):
            brand_lower = device["brand"].lower()
            if any(keyword in brand_lower for keyword in template.brand_keywords):
                score += 0.5
        
        # Function matching
        if device.get("function"):
            function_lower = device["function"].lower()
            if any(keyword in function_lower for keyword in template.function_keywords):
                score += 0.3
        
        # Keyword matching
        device_keywords = device.get("keywords", [])
        keyword_matches = 0
        for keyword in device_keywords:
            if (keyword.lower() in template.brand_keywords or 
                keyword.lower() in template.function_keywords):
                keyword_matches += 1
        
        if device_keywords:
            score += (keyword_matches / len(device_keywords)) * 0.2
        
        return min(score, 1.0)
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM API with proper error handling."""
        try:
            # Example for OpenAI - adjust for your LLM provider
            response = await self.llm_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return "[]"  # Return empty JSON array on failure
```

### 1.3 Question Generation System

```python
# consciousness/interview/question_generator.py
from typing import Dict, List, Any
from consciousness.models.interview import DeviceCandidate, IntegrationTemplate

class QuestionGenerator:
    """Generates contextual questions for device discovery."""
    
    def generate_questions_for_candidate(
        self, 
        candidate: DeviceCandidate,
        integration_template: IntegrationTemplate
    ) -> List[str]:
        """Generate specific questions for a device candidate."""
        
        questions = []
        
        # Integration-specific questions
        if integration_template.integration_name == "hue":
            questions.extend([
                "Do you have a Philips Hue Bridge? It's usually a white device connected to your router.",
                "What types of Hue devices do you have? (bulbs, light strips, motion sensors, etc.)",
                "Are they all connected through the Hue app?"
            ])
        
        elif integration_template.integration_name == "nest":
            questions.extend([
                "Do you use the Nest app or Google Home to control your thermostat?",
                "What's the model of your Nest device?",
                "Is it connected to your Google account?"
            ])
        
        elif integration_template.integration_name == "ring":
            questions.extend([
                "What Ring devices do you have? (doorbell, cameras, alarm, etc.)",
                "Do you use the Ring app to view them?",
                "Are they all on the same Ring account?"
            ])
        
        # Add authentication questions if needed
        if integration_template.auth_required:
            questions.append(
                f"Do you currently use an app to control your {candidate.detected_brand or 'devices'}?"
            )
        
        # Add hub questions if needed
        if integration_template.requires_hub:
            questions.append(
                f"Do you have a hub or bridge device for your {candidate.detected_brand or 'devices'}?"
            )
        
        return questions
    
    def generate_room_based_questions(self) -> List[str]:
        """Generate questions to discover devices by room."""
        return [
            "Let's go room by room. Starting with your living room - what smart devices do you have there?",
            "In your bedroom, do you have any smart lights, fans, or other connected devices?",
            "What about your kitchen? Any smart appliances, lights, or sensors?",
            "Do you have any devices in your bathroom? Smart switches, fans, or sensors?",
            "What smart devices do you have outdoors? Lights, cameras, or irrigation?"
        ]
    
    def generate_function_based_questions(self) -> List[str]:
        """Generate questions to discover devices by function."""
        return [
            "Tell me about how you control your home's temperature. Do you have a smart thermostat?",
            "For lighting, do you have any smart bulbs, switches, or dimmers?",
            "What about security? Any cameras, doorbells, or alarm systems?",
            "Do you have any entertainment devices? Smart TVs, speakers, or streaming devices?",
            "What about energy management? Solar panels, battery systems, or smart plugs?"
        ]
```

## Phase 2: Automatic Discovery Integration

### 2.1 Multi-Protocol Discovery Service

```python
# consciousness/discovery/auto_discovery.py
import asyncio
from typing import Dict, List, Any
from consciousness.discovery.protocols import (
    DHCPDiscovery, MDNSDiscovery, UPnPDiscovery, 
    BluetoothDiscovery, ZigbeeDiscovery
)

class AutoDiscoveryService:
    """Coordinates automatic device discovery across all protocols."""
    
    def __init__(self):
        self.dhcp = DHCPDiscovery()
        self.mdns = MDNSDiscovery()
        self.upnp = UPnPDiscovery()
        self.bluetooth = BluetoothDiscovery()
        self.zigbee = ZigbeeDiscovery()
    
    async def discover_all_protocols(self) -> Dict[str, List[Dict[str, Any]]]:
        """Run discovery across all protocols in parallel."""
        
        results = await asyncio.gather(
            self.dhcp.discover(),
            self.mdns.discover(),
            self.upnp.discover(),
            self.bluetooth.discover(),
            self.zigbee.discover(),
            return_exceptions=True
        )
        
        return {
            "dhcp": results[0] if not isinstance(results[0], Exception) else [],
            "mdns": results[1] if not isinstance(results[1], Exception) else [],
            "upnp": results[2] if not isinstance(results[2], Exception) else [],
            "bluetooth": results[3] if not isinstance(results[3], Exception) else [],
            "zigbee": results[4] if not isinstance(results[4], Exception) else []
        }
    
    async def discover_for_integration(self, integration_type: str) -> List[Dict[str, Any]]:
        """Run targeted discovery for a specific integration type."""
        
        # Map integration types to discovery methods
        discovery_map = {
            "hue": [self.mdns.discover_hue_bridges, self.upnp.discover_hue],
            "ring": [self.upnp.discover_ring],
            "sonos": [self.mdns.discover_sonos, self.upnp.discover_sonos],
            "roku": [self.mdns.discover_roku],
            "chromecast": [self.mdns.discover_chromecast],
            "homekit": [self.mdns.discover_homekit]
        }
        
        methods = discovery_map.get(integration_type, [])
        if not methods:
            return []
        
        results = await asyncio.gather(*[method() for method in methods], return_exceptions=True)
        
        # Combine and deduplicate results
        combined = []
        for result in results:
            if not isinstance(result, Exception):
                combined.extend(result)
        
        return combined
```

### 2.2 Protocol-Specific Discovery

```python
# consciousness/discovery/protocols/mdns_discovery.py
import asyncio
from zeroconf import ServiceBrowser, Zeroconf, ServiceListener
from typing import List, Dict, Any

class MDNSDiscovery:
    """mDNS/Zeroconf device discovery."""
    
    def __init__(self):
        self.zeroconf = Zeroconf()
        self.discovered_devices = []
    
    async def discover(self) -> List[Dict[str, Any]]:
        """Discover all mDNS services."""
        
        service_types = [
            "_hap._tcp.local.",  # HomeKit
            "_googlecast._tcp.local.",  # Chromecast
            "_roku-rcp._tcp.local.",  # Roku
            "_sonos._tcp.local.",  # Sonos
            "_philips-hue._tcp.local.",  # Hue Bridge
            "_airplay._tcp.local.",  # AirPlay
        ]
        
        listeners = []
        for service_type in service_types:
            listener = DeviceServiceListener(self.discovered_devices)
            browser = ServiceBrowser(self.zeroconf, service_type, listener)
            listeners.append((browser, listener))
        
        # Wait for discovery
        await asyncio.sleep(10)  # Discovery timeout
        
        # Clean up
        for browser, listener in listeners:
            browser.cancel()
        
        return self.discovered_devices.copy()
    
    async def discover_hue_bridges(self) -> List[Dict[str, Any]]:
        """Specifically discover Philips Hue bridges."""
        
        devices = []
        listener = DeviceServiceListener(devices)
        browser = ServiceBrowser(self.zeroconf, "_hue._tcp.local.", listener)
        
        await asyncio.sleep(5)
        browser.cancel()
        
        return devices

class DeviceServiceListener:
    """Listener for mDNS service discovery."""
    
    def __init__(self, device_list: List[Dict[str, Any]]):
        self.devices = device_list
    
    def add_service(self, zeroconf: Zeroconf, type_: str, name: str):
        """Called when a service is discovered."""
        
        info = zeroconf.get_service_info(type_, name)
        if info:
            device = {
                "name": name,
                "type": type_,
                "address": str(info.parsed_addresses()[0]) if info.parsed_addresses() else None,
                "port": info.port,
                "properties": {k.decode(): v.decode() for k, v in info.properties.items()},
                "discovery_method": "mdns"
            }
            self.devices.append(device)
```

## Phase 3: Dynamic Integration Factory

### 3.1 Integration Factory Pattern

```python
# consciousness/integrations/factory.py
from typing import Dict, Type, Any
from consciousness.integrations.base import BaseIntegration
from consciousness.integrations import (
    HueIntegration, NestIntegration, RingIntegration,
    TeslaIntegration, SonosIntegration, RokuIntegration
)

class IntegrationFactory:
    """Factory for creating device integrations dynamically."""
    
    _integrations: Dict[str, Type[BaseIntegration]] = {
        "hue": HueIntegration,
        "nest": NestIntegration,
        "ring": RingIntegration,
        "tesla": TeslaIntegration,
        "sonos": SonosIntegration,
        "roku": RokuIntegration,
        # Add more integrations here
    }
    
    @classmethod
    def create_integration(
        self, 
        integration_type: str, 
        config: Dict[str, Any]
    ) -> BaseIntegration:
        """Create an integration instance."""
        
        integration_class = self._integrations.get(integration_type)
        if not integration_class:
            raise ValueError(f"Unknown integration type: {integration_type}")
        
        return integration_class(config)
    
    @classmethod
    def get_supported_integrations(cls) -> List[str]:
        """Get list of supported integration types."""
        return list(cls._integrations.keys())
    
    @classmethod
    def register_integration(
        cls, 
        integration_type: str, 
        integration_class: Type[BaseIntegration]
    ):
        """Register a new integration type."""
        cls._integrations[integration_type] = integration_class
```

### 3.2 Base Integration Interface

```python
# consciousness/integrations/base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from consciousness.models.entities import Device, DeviceEntity

class BaseIntegration(ABC):
    """Base class for all device integrations."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_authenticated = False
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the device/service."""
        pass
    
    @abstractmethod
    async def discover_devices(self) -> List[Device]:
        """Discover devices through this integration."""
        pass
    
    @abstractmethod
    async def get_device_state(self, device_id: str) -> Dict[str, Any]:
        """Get current state of a device."""
        pass
    
    @abstractmethod
    async def send_command(
        self, 
        device_id: str, 
        command: str, 
        parameters: Dict[str, Any]
    ) -> bool:
        """Send command to device."""
        pass
    
    @abstractmethod
    async def subscribe_to_updates(self, device_id: str, callback: callable):
        """Subscribe to device state updates."""
        pass
    
    def get_required_config_fields(self) -> List[Dict[str, Any]]:
        """Get configuration fields required for this integration."""
        return []
    
    def get_supported_device_classes(self) -> List[str]:
        """Get device classes supported by this integration."""
        return []
```

## Phase 4: Integration Examples

### 4.1 Philips Hue Integration

```python
# consciousness/integrations/hue.py
import aiohttp
from typing import Dict, List, Any
from consciousness.integrations.base import BaseIntegration

class HueIntegration(BaseIntegration):
    """Philips Hue integration using local bridge API."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.bridge_ip = config.get("bridge_ip")
        self.username = config.get("username")
        self.session = None
    
    async def authenticate(self) -> bool:
        """Authenticate with Hue bridge."""
        
        if not self.bridge_ip:
            # Auto-discover bridge
            self.bridge_ip = await self._discover_bridge()
            if not self.bridge_ip:
                return False
        
        if not self.username:
            # Request authentication
            self.username = await self._request_auth()
            if not self.username:
                return False
        
        # Test authentication
        self.session = aiohttp.ClientSession()
        success = await self._test_connection()
        self.is_authenticated = success
        return success
    
    async def discover_devices(self) -> List[Device]:
        """Discover Hue devices."""
        
        if not self.is_authenticated:
            await self.authenticate()
        
        async with self.session.get(
            f"http://{self.bridge_ip}/api/{self.username}/lights"
        ) as resp:
            lights_data = await resp.json()
        
        devices = []
        for light_id, light_info in lights_data.items():
            device = Device(
                user_name=light_info["name"],
                detected_brand="Philips",
                detected_model=light_info["modelid"],
                integration_type="hue",
                device_class="light",
                supported_features=self._extract_features(light_info),
                config_data={
                    "bridge_ip": self.bridge_ip,
                    "light_id": light_id
                },
                discovery_method="hue_api"
            )
            devices.append(device)
        
        return devices
    
    async def send_command(
        self, 
        device_id: str, 
        command: str, 
        parameters: Dict[str, Any]
    ) -> bool:
        """Send command to Hue device."""
        
        light_id = parameters.get("light_id")
        if not light_id:
            return False
        
        payload = {}
        
        if command == "turn_on":
            payload["on"] = True
        elif command == "turn_off":
            payload["on"] = False
        elif command == "set_brightness":
            payload["bri"] = int(parameters["brightness"] * 254)
        elif command == "set_color":
            payload["xy"] = self._rgb_to_xy(parameters["rgb"])
        
        async with self.session.put(
            f"http://{self.bridge_ip}/api/{self.username}/lights/{light_id}/state",
            json=payload
        ) as resp:
            return resp.status == 200
```

This dynamic device integration guide provides a complete framework for conversational device discovery that can adapt to any smart home setup while leveraging the extensive Home Assistant integration ecosystem.