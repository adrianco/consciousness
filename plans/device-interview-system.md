# Dynamic Device Interview System Design

## Overview

Replace fixed device types with a conversational interview system that dynamically discovers and configures devices based on natural language descriptions from homeowners. Leverages Home Assistant's 2000+ integration patterns as a reference for device support.

## Interview Flow Architecture

### Phase 1: Natural Discovery
**Goal**: Let users describe their devices naturally

```
AI: "Tell me about the smart devices in your home. You can describe them however feels natural - by room, by what they do, or just list what comes to mind."

User: "I have a Nest thermostat, some Philips Hue lights, a Ring doorbell, and my Tesla is connected to the house for charging."

AI: "That's a great start! Let me ask about each one to make sure I understand how to connect to them..."
```

### Phase 2: Device Classification & Technical Mapping
**Goal**: Map natural descriptions to technical integration patterns

#### Device Classification Engine
```python
class DeviceClassifier:
    def classify_device(self, description: str) -> DeviceCandidate:
        """
        Map natural language to Home Assistant integration patterns
        """
        # Extract key identifiers
        brand = extract_brand(description)  # "Nest", "Philips Hue", "Ring"
        function = extract_function(description)  # "thermostat", "lights", "doorbell"
        
        # Match to Home Assistant integrations
        possible_integrations = match_ha_integrations(brand, function)
        
        return DeviceCandidate(
            user_description=description,
            detected_brand=brand,
            detected_function=function,
            possible_integrations=possible_integrations,
            confidence_score=calculate_confidence()
        )
```

### Phase 3: Integration-Specific Interviews
**Goal**: Gather technical details needed for each integration type

#### Dynamic Question Generation
Based on Home Assistant's config_flow patterns, generate questions for each device:

```python
class IntegrationInterviewer:
    def generate_questions(self, integration_type: str) -> List[Question]:
        """
        Generate device-specific questions based on HA integration requirements
        """
        questions = []
        
        if integration_type == "nest":
            questions.extend([
                "Do you have a Nest account that you use to control your thermostat?",
                "What's the model of your Nest device? (You can usually find this in the Nest app)"
            ])
        
        elif integration_type == "hue":
            questions.extend([
                "Can you see your Hue Bridge? It's usually a white device connected to your router.",
                "Are your Hue lights all connected through the Philips Hue app?",
                "What types of Hue devices do you have? (bulbs, light strips, motion sensors, etc.)"
            ])
        
        elif integration_type == "ring":
            questions.extend([
                "Do you use the Ring app to view your doorbell?",
                "What Ring devices do you have? (doorbell, cameras, alarm system, etc.)"
            ])
        
        return questions
```

## Device Discovery Strategies

### 1. Network Discovery Integration
Combine interview with automatic discovery:

```python
async def enhanced_discovery(interview_data: InterviewSession):
    """
    Use interview context to guide automatic discovery
    """
    # User mentioned Hue - scan for Hue Bridge
    if "hue" in interview_data.mentioned_brands:
        hue_bridges = await discover_hue_bridges()
        await correlate_with_interview(hue_bridges, interview_data)
    
    # User mentioned Ring - check for Ring devices
    if "ring" in interview_data.mentioned_brands:
        ring_devices = await discover_ring_devices()
        await correlate_with_interview(ring_devices, interview_data)
```

### 2. Protocol-Aware Discovery
Based on Home Assistant's discovery mechanisms:

```python
class ProtocolDiscovery:
    discovery_methods = {
        "matter": discover_matter_devices,
        "homekit": discover_homekit_devices,  
        "zigbee": discover_zigbee_devices,
        "zwave": discover_zwave_devices,
        "bluetooth": discover_bluetooth_devices,
        "upnp": discover_upnp_devices,
        "dhcp": discover_dhcp_devices
    }
    
    async def discover_by_protocol(self, mentioned_devices: List[str]):
        """
        Run targeted discovery based on interview context
        """
        for device in mentioned_devices:
            likely_protocols = infer_protocols(device)
            for protocol in likely_protocols:
                if protocol in self.discovery_methods:
                    await self.discovery_methods[protocol]()
```

## Interview Question Patterns

### Room-Based Discovery
```
"Let's go room by room. Starting with your living room - what smart devices do you have there?"

"In your bedroom, do you have any smart lights, fans, or other connected devices?"

"What about your kitchen? Any smart appliances, lights, or sensors?"
```

### Function-Based Discovery  
```
"Tell me about how you control your home's temperature. Do you have a smart thermostat?"

"For lighting, do you have any smart bulbs, switches, or dimmers?"

"What about security? Any cameras, doorbells, or alarm systems?"

"Do you have any entertainment devices? Smart TVs, speakers, streaming devices?"
```

### App-Based Discovery
```
"What apps do you use to control things in your home?"
- "I use the Nest app" → Nest integration
- "I have the SmartThings app" → Samsung SmartThings integration  
- "I use Apple Home" → HomeKit integration
- "I have the Ring app" → Ring integration
```

## Device Metadata Capture

### Core Device Information
```python
@dataclass
class DiscoveredDevice:
    # User-provided information
    user_name: str                    # "Living room lights"
    user_description: str             # "Philips Hue color bulbs above the couch"
    location: str                     # "Living room"
    
    # Technical identification
    detected_brand: str               # "Philips"
    detected_model: Optional[str]     # "Hue Color Bulb"
    integration_type: str             # "hue"
    
    # Connection details
    connection_method: str            # "wifi", "zigbee", "cloud"
    api_endpoint: Optional[str]       # For direct device APIs
    requires_hub: bool                # Needs Hue Bridge, SmartThings Hub, etc.
    
    # Capabilities (from Home Assistant patterns)
    device_class: str                 # "light", "sensor", "switch"
    supported_features: List[str]     # ["brightness", "color", "effects"]
    
    # Authentication/Configuration
    requires_auth: bool
    auth_method: str                  # "oauth", "api_key", "local_token"
    config_data: Dict[str, Any]       # Integration-specific configuration
```

### Integration-Specific Metadata
Drawing from Home Assistant's device registry patterns:

```python
# Example: Hue devices
hue_device = DiscoveredDevice(
    user_name="Living room lights",
    detected_brand="Philips",
    integration_type="hue",
    connection_method="wifi",
    requires_hub=True,
    device_class="light",
    supported_features=["brightness", "color_temp", "rgb_color", "effects"],
    config_data={
        "bridge_id": "discovered_bridge_id",
        "light_ids": [1, 2, 3],
        "bridge_ip": "192.168.1.100"
    }
)

# Example: Ring devices
ring_device = DiscoveredDevice(
    user_name="Front door camera",
    detected_brand="Ring",
    integration_type="ring",
    connection_method="cloud",
    device_class="camera",
    supported_features=["streaming", "motion_detection", "two_way_audio"],
    requires_auth=True,
    auth_method="oauth",
    config_data={
        "username": "user_email",
        "device_id": "ring_device_id"
    }
)
```

## Conversational Flow Examples

### Example 1: Comprehensive Home
```
AI: What smart devices do you have in your home?

User: We have quite a bit - Nest thermostat, Ring doorbell, lots of Hue lights, a Tesla Powerwall, and everything connects through our Samsung SmartThings hub.

AI: That's an impressive setup! Let me make sure I understand each system:

For your Nest thermostat - do you control it through the Nest app or Google Home?
User: Both actually, it's connected to our Google account.

Great! For the Ring doorbell - what model is it, and do you have any other Ring devices?
User: It's a Ring Video Doorbell Pro, and we also have two Ring cameras in the backyard.

Perfect. With your Hue lights - how many do you have, and what types?
User: Maybe 15 bulbs throughout the house, mostly color bulbs but some just white ones. Plus we have some Hue motion sensors.

Excellent. Your Tesla Powerwall - do you monitor it through the Tesla app?
User: Yes, and we can see the energy data there.

And SmartThings - what devices do you have connected through that hub?
User: Some Samsung appliances, a few sensors, and some outlets that aren't Hue.

AI: Perfect! I can connect to all of these. Let me set up the integrations...
```

### Example 2: Simple Setup
```
AI: Tell me about any smart devices you have.

User: I just have some smart plugs and a Roku TV.

AI: Nice and simple! What brand are the smart plugs?

User: I think they're TP-Link Kasa plugs. I control them with an app on my phone.

AI: Perfect - those work great. How many do you have and what do you use them for?

User: Three plugs. One for a lamp, one for a fan, and one for some holiday lights.

AI: Great! And your Roku - do you ever want to control it from other devices or just use the remote?

User: Just the remote is fine for now.

AI: Understood. I'll set up the TP-Link plugs so your house can monitor and control them, and I'll connect to your Roku for basic monitoring. Setting this up now...
```

## Integration with Home Assistant Knowledge Base

### Device Database
Maintain a curated database of device patterns from Home Assistant:

```python
class HADeviceKnowledge:
    """
    Knowledge base of Home Assistant integration patterns
    """
    
    def get_integration_info(self, brand: str, device_type: str) -> IntegrationInfo:
        """
        Return integration requirements based on HA documentation
        """
        key = f"{brand.lower()}_{device_type.lower()}"
        return self.device_patterns.get(key, self.generic_patterns.get(device_type))
    
    def get_required_config(self, integration_type: str) -> List[ConfigField]:
        """
        Return required configuration fields for an integration
        """
        return self.config_requirements.get(integration_type, [])
    
    def get_discovery_hints(self, integration_type: str) -> DiscoveryHints:
        """
        Return how this integration typically gets discovered
        """
        return self.discovery_patterns.get(integration_type)
```

This approach transforms device discovery from a fixed list to a dynamic, conversational process that can adapt to any home's unique combination of smart devices while leveraging Home Assistant's extensive integration knowledge.