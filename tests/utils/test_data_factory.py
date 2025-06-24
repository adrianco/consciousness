"""
Test data factory for creating realistic test data.
Provides builders and factories for consciousness system entities.
"""
import json
import random
from datetime import datetime, timedelta

import factory
import factory.fuzzy
from faker import Faker

from consciousness.models.consciousness import EmotionalState, Memory
from consciousness.models.entities import Device, House
from consciousness.models.interview import DeviceCandidate, InterviewSession

fake = Faker()


class HouseFactory(factory.Factory):
    """Factory for creating test houses."""

    class Meta:
        model = House

    id = factory.Sequence(lambda n: f"house_{n:03d}")
    name = factory.LazyAttribute(lambda obj: f"{fake.first_name()}'s Smart Home")
    timezone = factory.fuzzy.FuzzyChoice(
        [
            "America/New_York",
            "America/Chicago",
            "America/Denver",
            "America/Los_Angeles",
            "Europe/London",
            "Europe/Berlin",
        ]
    )
    location = factory.LazyFunction(
        lambda: {
            "latitude": fake.latitude(),
            "longitude": fake.longitude(),
            "address": fake.address(),
        }
    )
    created_at = factory.LazyFunction(datetime.now)


class DeviceFactory(factory.Factory):
    """Factory for creating test devices."""

    class Meta:
        model = Device

    id = factory.Sequence(lambda n: f"device_{n:03d}")
    name = factory.LazyAttribute(
        lambda obj: f"{fake.word().title()} {obj.device_type.title()}"
    )
    device_type = factory.fuzzy.FuzzyChoice(
        [
            "smart_light",
            "thermostat",
            "smart_plug",
            "motion_sensor",
            "temperature_sensor",
            "smart_lock",
            "security_camera",
            "smart_blinds",
        ]
    )
    location = factory.fuzzy.FuzzyChoice(
        [
            "living_room",
            "bedroom",
            "kitchen",
            "bathroom",
            "hallway",
            "dining_room",
            "office",
            "garage",
            "basement",
            "attic",
        ]
    )
    capabilities = factory.LazyAttribute(
        lambda obj: _get_device_capabilities(obj.device_type)
    )
    status = factory.fuzzy.FuzzyChoice(["online", "offline", "error", "maintenance"])
    metadata = factory.LazyFunction(
        lambda: {
            "manufacturer": fake.company(),
            "model": f"{fake.word().upper()}-{fake.random_int(100, 999)}",
            "firmware_version": f"{fake.random_int(1, 5)}.{fake.random_int(0, 9)}.{fake.random_int(0, 9)}",
            "installation_date": fake.date_this_year().isoformat(),
        }
    )
    created_at = factory.LazyFunction(datetime.now)


class EmotionalStateFactory(factory.Factory):
    """Factory for creating test emotional states."""

    class Meta:
        model = EmotionalState

    id = factory.Sequence(lambda n: n)
    happiness = factory.fuzzy.FuzzyFloat(0.0, 1.0)
    worry = factory.fuzzy.FuzzyFloat(0.0, 1.0)
    boredom = factory.fuzzy.FuzzyFloat(0.0, 1.0)
    excitement = factory.fuzzy.FuzzyFloat(0.0, 1.0)
    primary_emotion = factory.LazyAttribute(lambda obj: _determine_primary_emotion(obj))
    intensity = factory.LazyAttribute(
        lambda obj: max(obj.happiness, obj.worry, obj.boredom, obj.excitement)
    )
    confidence = factory.fuzzy.FuzzyFloat(0.6, 1.0)
    trigger_event = factory.fuzzy.FuzzyChoice(
        [
            "user_interaction",
            "device_success",
            "device_failure",
            "optimization_complete",
            "environmental_change",
            "routine_completion",
            "error_detected",
            "learning_update",
        ]
    )
    timestamp = factory.LazyFunction(datetime.now)


class MemoryFactory(factory.Factory):
    """Factory for creating test memories."""

    class Meta:
        model = Memory

    id = factory.Sequence(lambda n: n)
    type = factory.fuzzy.FuzzyChoice(
        ["pattern", "preference", "event", "learning", "optimization", "interaction"]
    )
    content = factory.LazyFunction(lambda: fake.sentence(nb_words=10))
    confidence = factory.fuzzy.FuzzyFloat(0.5, 1.0)
    importance = factory.fuzzy.FuzzyFloat(0.1, 1.0)
    context = factory.LazyFunction(
        lambda: {
            "location": fake.random_element(["living_room", "bedroom", "kitchen"]),
            "time_of_day": fake.random_element(
                ["morning", "afternoon", "evening", "night"]
            ),
            "user_present": fake.boolean(),
            "activity": fake.random_element(
                ["watching_tv", "cooking", "sleeping", "working"]
            ),
        }
    )
    created_at = factory.LazyFunction(datetime.now)
    last_accessed = factory.LazyFunction(
        lambda: datetime.now() - timedelta(days=fake.random_int(0, 30))
    )
    access_count = factory.fuzzy.FuzzyInteger(1, 100)


class InterviewSessionFactory(factory.Factory):
    """Factory for creating test interview sessions."""

    class Meta:
        model = InterviewSession

    id = factory.Sequence(lambda n: n)
    house_id = factory.SubFactory(HouseFactory)
    status = factory.fuzzy.FuzzyChoice(["active", "paused", "completed", "cancelled"])
    current_phase = factory.fuzzy.FuzzyChoice(
        [
            "introduction",
            "discovery",
            "classification",
            "configuration",
            "verification",
            "completed",
        ]
    )
    progress = factory.LazyFunction(
        lambda: {
            "devices_mentioned": fake.random_int(0, 10),
            "devices_confirmed": fake.random_int(0, 8),
            "integrations_configured": fake.random_int(0, 5),
        }
    )
    created_at = factory.LazyFunction(
        lambda: datetime.now() - timedelta(hours=fake.random_int(0, 48))
    )
    updated_at = factory.LazyFunction(datetime.now)


class DeviceCandidateFactory(factory.Factory):
    """Factory for creating test device candidates."""

    class Meta:
        model = DeviceCandidate

    id = factory.Sequence(lambda n: n)
    interview_session_id = factory.SubFactory(InterviewSessionFactory)
    detected_brand = factory.fuzzy.FuzzyChoice(
        [
            "Philips",
            "Google/Nest",
            "TP-Link",
            "Samsung",
            "Amazon",
            "Apple",
            "LIFX",
            "Wyze",
            "Ring",
            "Arlo",
            "Ecobee",
            "Honeywell",
        ]
    )
    detected_function = factory.fuzzy.FuzzyChoice(
        [
            "lighting",
            "climate_control",
            "security",
            "energy_management",
            "entertainment",
            "monitoring",
            "automation",
        ]
    )
    confidence = factory.fuzzy.FuzzyFloat(0.5, 0.99)
    auto_discovery_successful = factory.fuzzy.FuzzyChoice([True, False])
    auto_discovery_results = factory.LazyFunction(lambda: _generate_discovery_results())
    status = factory.fuzzy.FuzzyChoice(
        ["pending_confirmation", "confirmed", "rejected", "configured"]
    )
    created_at = factory.LazyFunction(datetime.now)


def _get_device_capabilities(device_type):
    """Get realistic capabilities for device type."""
    capability_map = {
        "smart_light": ["on_off", "dimming", "color_temperature", "color_changing"],
        "thermostat": [
            "temperature_control",
            "scheduling",
            "mode_control",
            "energy_monitoring",
        ],
        "smart_plug": ["on_off", "energy_monitoring", "scheduling"],
        "motion_sensor": [
            "motion_detection",
            "occupancy_sensing",
            "battery_monitoring",
        ],
        "temperature_sensor": ["temperature_reading", "humidity_reading"],
        "smart_lock": ["lock_control", "access_monitoring", "battery_monitoring"],
        "security_camera": ["video_recording", "motion_detection", "night_vision"],
        "smart_blinds": ["position_control", "scheduling", "light_sensing"],
    }

    base_capabilities = capability_map.get(device_type, ["basic_control"])
    # Randomly include some optional capabilities
    optional_capabilities = ["remote_access", "voice_control", "app_control"]

    capabilities = base_capabilities.copy()
    for cap in optional_capabilities:
        if random.random() > 0.5:
            capabilities.append(cap)

    return capabilities


def _determine_primary_emotion(emotional_state):
    """Determine primary emotion from emotional values."""
    emotions = {
        "happy": emotional_state.happiness,
        "worried": emotional_state.worry,
        "bored": emotional_state.boredom,
        "excited": emotional_state.excitement,
    }

    return max(emotions, key=emotions.get)


def _generate_discovery_results():
    """Generate realistic auto-discovery results."""
    if random.random() > 0.3:  # 70% chance of successful discovery
        protocols = ["mdns", "upnp", "bluetooth", "zigbee"]
        selected_protocol = random.choice(protocols)

        return {
            selected_protocol: [
                {
                    "name": f"{fake.company()} Device",
                    "address": fake.ipv4()
                    if selected_protocol in ["mdns", "upnp"]
                    else fake.mac_address(),
                    "model": f"{fake.word().upper()}-{fake.random_int(100, 999)}",
                    "discovered_at": datetime.now().isoformat(),
                }
            ]
        }
    else:
        return {}


class ScenarioDataBuilder:
    """Builder for creating complex scenario test data."""

    def __init__(self):
        self.houses = []
        self.devices = []
        self.emotional_states = []
        self.memories = []

    def with_house(self, **kwargs):
        """Add a house to the scenario."""
        house = HouseFactory(**kwargs)
        self.houses.append(house)
        return self

    def with_devices(self, count=5, house_id=None, **kwargs):
        """Add devices to the scenario."""
        if house_id is None and self.houses:
            house_id = self.houses[0].id

        for _ in range(count):
            device = DeviceFactory(house_id=house_id, **kwargs)
            self.devices.append(device)
        return self

    def with_smart_home_setup(self, house_name="Test Smart Home"):
        """Create a complete smart home setup."""
        house = HouseFactory(name=house_name)
        self.houses.append(house)

        # Common smart home devices
        device_configs = [
            {
                "device_type": "thermostat",
                "location": "living_room",
                "name": "Main Thermostat",
            },
            {
                "device_type": "smart_light",
                "location": "living_room",
                "name": "Living Room Lights",
            },
            {
                "device_type": "smart_light",
                "location": "bedroom",
                "name": "Bedroom Lights",
            },
            {
                "device_type": "smart_plug",
                "location": "kitchen",
                "name": "Coffee Maker Plug",
            },
            {
                "device_type": "motion_sensor",
                "location": "hallway",
                "name": "Hallway Motion",
            },
            {
                "device_type": "smart_lock",
                "location": "front_door",
                "name": "Front Door Lock",
            },
            {
                "device_type": "security_camera",
                "location": "front_door",
                "name": "Doorbell Camera",
            },
        ]

        for config in device_configs:
            device = DeviceFactory(house_id=house.id, **config)
            self.devices.append(device)

        return self

    def with_emotional_history(self, count=10, days_back=30):
        """Add emotional state history."""
        for i in range(count):
            timestamp = datetime.now() - timedelta(
                days=random.randint(0, days_back),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )

            emotional_state = EmotionalStateFactory(timestamp=timestamp)
            self.emotional_states.append(emotional_state)

        return self

    def with_learned_patterns(self, count=5):
        """Add learned patterns and memories."""
        pattern_types = [
            "user_prefers_dim_lighting_evening",
            "temperature_adjustment_pattern",
            "energy_optimization_routine",
            "security_activation_pattern",
            "weekend_routine_pattern",
        ]

        for i in range(min(count, len(pattern_types))):
            memory = MemoryFactory(
                type="pattern",
                content=f"Learned pattern: {pattern_types[i]}",
                confidence=random.uniform(0.7, 0.95),
                importance=random.uniform(0.6, 1.0),
            )
            self.memories.append(memory)

        return self

    def build(self):
        """Build and return the complete scenario data."""
        return {
            "houses": self.houses,
            "devices": self.devices,
            "emotional_states": self.emotional_states,
            "memories": self.memories,
        }


class PerformanceDataGenerator:
    """Generator for performance testing data."""

    @staticmethod
    def generate_query_dataset(size=1000):
        """Generate a dataset of queries for performance testing."""
        query_templates = [
            "How are you feeling?",
            "What's the temperature in the {location}?",
            "Turn {state} the {device_type} in the {location}",
            "Is everything working properly?",
            "Optimize energy usage for the next {hours} hours",
            "What devices are connected?",
            "How comfortable is the {location}?",
            "Set the temperature to {temperature} degrees",
            "Are there any issues with the {device_type}?",
            "What's your current emotional state?",
        ]

        locations = ["living room", "bedroom", "kitchen", "bathroom"]
        device_types = ["lights", "thermostat", "security system", "smart plugs"]
        states = ["on", "off"]

        queries = []
        for _ in range(size):
            template = random.choice(query_templates)
            query = template.format(
                location=random.choice(locations),
                device_type=random.choice(device_types),
                state=random.choice(states),
                hours=random.randint(1, 24),
                temperature=random.randint(18, 25),
            )
            queries.append(query)

        return queries

    @staticmethod
    def generate_device_state_changes(device_count=50, changes_per_device=100):
        """Generate device state changes for load testing."""
        changes = []

        for device_id in range(device_count):
            for change_num in range(changes_per_device):
                change = {
                    "device_id": f"device_{device_id:03d}",
                    "timestamp": datetime.now() + timedelta(seconds=change_num),
                    "state_changes": _generate_realistic_state_change(),
                }
                changes.append(change)

        return changes


def _generate_realistic_state_change():
    """Generate realistic device state changes."""
    change_types = [
        {"brightness": random.randint(0, 100)},
        {"temperature": random.uniform(18.0, 25.0)},
        {"power_state": random.choice(["on", "off"])},
        {"mode": random.choice(["auto", "manual", "eco"])},
        {"position": random.randint(0, 100)},
    ]

    return random.choice(change_types)
