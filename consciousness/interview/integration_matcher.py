"""
Integration matcher for Home Assistant compatibility.

This module matches discovered devices to appropriate Home Assistant integration
patterns, leveraging the extensive ecosystem of 2000+ integrations to provide
seamless device connectivity.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class IntegrationMatcher:
    """Matches devices to Home Assistant integration patterns."""

    def __init__(self):
        self._initialize_integration_database()

    def _initialize_integration_database(self) -> None:
        """Initialize the database of Home Assistant integration patterns."""

        # Core integration patterns based on Home Assistant's integration library
        self.integration_patterns = {
            # Lighting Integrations
            "hue": {
                "display_name": "Philips Hue",
                "brand_keywords": ["philips", "hue"],
                "function_keywords": ["light", "bulb", "strip", "lamp", "lighting"],
                "model_patterns": ["hue", "color", "white", "ambiance"],
                "device_classes": ["light", "sensor"],
                "supported_features": {
                    "light": [
                        "brightness",
                        "color_temp",
                        "rgb_color",
                        "effects",
                        "transition",
                    ]
                },
                "discovery_methods": ["mdns", "upnp"],
                "requires_hub": True,
                "auth_required": False,
                "auth_methods": ["local_token"],
                "config_fields": ["bridge_ip", "bridge_id"],
                "ha_domain": "hue",
                "ha_config_flow": True,
                "priority": 90,
            },
            "lifx": {
                "display_name": "LIFX",
                "brand_keywords": ["lifx"],
                "function_keywords": ["light", "bulb", "strip", "lamp", "lighting"],
                "model_patterns": ["color", "white", "mini", "beam", "tile"],
                "device_classes": ["light"],
                "supported_features": {
                    "light": ["brightness", "color_temp", "rgb_color", "effects"]
                },
                "discovery_methods": ["lan_scan"],
                "requires_hub": False,
                "auth_required": False,
                "auth_methods": [],
                "config_fields": [],
                "ha_domain": "lifx",
                "ha_config_flow": True,
                "priority": 85,
            },
            "kasa": {
                "display_name": "TP-Link Kasa",
                "brand_keywords": ["tp-link", "kasa", "tplink"],
                "function_keywords": [
                    "switch",
                    "plug",
                    "outlet",
                    "bulb",
                    "light",
                    "dimmer",
                ],
                "model_patterns": ["hs", "kp", "kl", "ep"],
                "device_classes": ["switch", "light"],
                "supported_features": {
                    "switch": ["on_off", "power_monitoring"],
                    "light": ["brightness", "color_temp", "rgb_color"],
                },
                "discovery_methods": ["dhcp", "lan_scan"],
                "requires_hub": False,
                "auth_required": False,
                "auth_methods": [],
                "config_fields": [],
                "ha_domain": "tplink",
                "ha_config_flow": True,
                "priority": 80,
            },
            # Climate Integrations
            "nest": {
                "display_name": "Google Nest",
                "brand_keywords": ["nest", "google"],
                "function_keywords": ["thermostat", "temperature", "climate", "hvac"],
                "model_patterns": ["nest", "learning", "e"],
                "device_classes": ["climate", "sensor"],
                "supported_features": {
                    "climate": [
                        "temperature",
                        "humidity",
                        "mode",
                        "fan_mode",
                        "preset_mode",
                    ]
                },
                "discovery_methods": ["cloud"],
                "requires_hub": False,
                "auth_required": True,
                "auth_methods": ["oauth"],
                "config_fields": ["project_id", "client_id", "client_secret"],
                "ha_domain": "nest",
                "ha_config_flow": True,
                "priority": 95,
            },
            "ecobee": {
                "display_name": "Ecobee",
                "brand_keywords": ["ecobee"],
                "function_keywords": ["thermostat", "temperature", "climate"],
                "model_patterns": ["ecobee", "smartthermostat", "thermostat"],
                "device_classes": ["climate", "sensor"],
                "supported_features": {
                    "climate": [
                        "temperature",
                        "humidity",
                        "mode",
                        "fan_mode",
                        "preset_mode",
                    ]
                },
                "discovery_methods": ["cloud"],
                "requires_hub": False,
                "auth_required": True,
                "auth_methods": ["api_key"],
                "config_fields": ["api_key"],
                "ha_domain": "ecobee",
                "ha_config_flow": True,
                "priority": 85,
            },
            # Security Integrations
            "ring": {
                "display_name": "Ring",
                "brand_keywords": ["ring"],
                "function_keywords": ["doorbell", "camera", "security", "alarm"],
                "model_patterns": ["doorbell", "pro", "elite", "cam", "alarm"],
                "device_classes": [
                    "camera",
                    "binary_sensor",
                    "sensor",
                    "alarm_control_panel",
                ],
                "supported_features": {
                    "camera": ["streaming", "motion_detection", "two_way_audio"],
                    "binary_sensor": ["motion", "ding"],
                },
                "discovery_methods": ["cloud"],
                "requires_hub": False,
                "auth_required": True,
                "auth_methods": ["username_password"],
                "config_fields": ["username", "password"],
                "ha_domain": "ring",
                "ha_config_flow": True,
                "priority": 90,
            },
            "arlo": {
                "display_name": "Arlo",
                "brand_keywords": ["arlo", "netgear"],
                "function_keywords": ["camera", "security", "surveillance"],
                "model_patterns": ["pro", "ultra", "essential", "go"],
                "device_classes": ["camera", "binary_sensor", "sensor"],
                "supported_features": {
                    "camera": ["streaming", "motion_detection", "night_vision"]
                },
                "discovery_methods": ["cloud"],
                "requires_hub": True,
                "auth_required": True,
                "auth_methods": ["username_password"],
                "config_fields": ["username", "password"],
                "ha_domain": "arlo",
                "ha_config_flow": True,
                "priority": 85,
            },
            # Media Integrations
            "sonos": {
                "display_name": "Sonos",
                "brand_keywords": ["sonos"],
                "function_keywords": ["speaker", "audio", "music", "sound"],
                "model_patterns": ["play", "beam", "arc", "sub", "one", "five"],
                "device_classes": ["media_player"],
                "supported_features": {
                    "media_player": [
                        "play",
                        "pause",
                        "volume",
                        "grouping",
                        "browse_media",
                    ]
                },
                "discovery_methods": ["mdns", "upnp"],
                "requires_hub": False,
                "auth_required": False,
                "auth_methods": [],
                "config_fields": [],
                "ha_domain": "sonos",
                "ha_config_flow": True,
                "priority": 90,
            },
            "roku": {
                "display_name": "Roku",
                "brand_keywords": ["roku"],
                "function_keywords": ["tv", "streaming", "media", "entertainment"],
                "model_patterns": ["ultra", "express", "premiere", "streaming stick"],
                "device_classes": ["media_player"],
                "supported_features": {
                    "media_player": [
                        "play",
                        "pause",
                        "volume",
                        "source_select",
                        "remote_control",
                    ]
                },
                "discovery_methods": ["mdns"],
                "requires_hub": False,
                "auth_required": False,
                "auth_methods": [],
                "config_fields": [],
                "ha_domain": "roku",
                "ha_config_flow": True,
                "priority": 85,
            },
            # Energy Integrations
            "tesla": {
                "display_name": "Tesla",
                "brand_keywords": ["tesla"],
                "function_keywords": [
                    "powerwall",
                    "solar",
                    "energy",
                    "charging",
                    "vehicle",
                ],
                "model_patterns": ["powerwall", "solar", "model"],
                "device_classes": ["sensor", "switch", "climate"],
                "supported_features": {
                    "sensor": [
                        "battery_level",
                        "energy_production",
                        "energy_consumption",
                    ],
                    "switch": ["charging"],
                },
                "discovery_methods": ["cloud"],
                "requires_hub": False,
                "auth_required": True,
                "auth_methods": ["oauth"],
                "config_fields": ["username", "password"],
                "ha_domain": "tesla",
                "ha_config_flow": True,
                "priority": 95,
            },
            # Hub Integrations
            "smartthings": {
                "display_name": "Samsung SmartThings",
                "brand_keywords": ["samsung", "smartthings"],
                "function_keywords": ["hub", "automation", "control"],
                "model_patterns": ["hub", "station"],
                "device_classes": ["hub"],
                "supported_features": {
                    "hub": ["device_management", "automation", "scenes"]
                },
                "discovery_methods": ["cloud"],
                "requires_hub": True,
                "auth_required": True,
                "auth_methods": ["api_key"],
                "config_fields": ["api_key"],
                "ha_domain": "smartthings",
                "ha_config_flow": True,
                "priority": 85,
            },
            # Lock Integrations
            "august": {
                "display_name": "August",
                "brand_keywords": ["august"],
                "function_keywords": ["lock", "door", "smart lock"],
                "model_patterns": ["smart lock", "pro", "wifi"],
                "device_classes": ["lock"],
                "supported_features": {
                    "lock": ["lock", "unlock", "auto_lock", "remote_control"]
                },
                "discovery_methods": ["cloud"],
                "requires_hub": False,
                "auth_required": True,
                "auth_methods": ["username_password"],
                "config_fields": ["username", "password"],
                "ha_domain": "august",
                "ha_config_flow": True,
                "priority": 85,
            },
            "yale": {
                "display_name": "Yale",
                "brand_keywords": ["yale"],
                "function_keywords": ["lock", "door", "smart lock"],
                "model_patterns": ["assure", "conexis", "linus"],
                "device_classes": ["lock"],
                "supported_features": {
                    "lock": ["lock", "unlock", "keypad", "remote_control"]
                },
                "discovery_methods": ["cloud", "bluetooth"],
                "requires_hub": False,
                "auth_required": True,
                "auth_methods": ["username_password"],
                "config_fields": ["username", "password"],
                "ha_domain": "yale_smart_alarm",
                "ha_config_flow": True,
                "priority": 80,
            },
        }

        # Generic integration patterns for unknown devices
        self.generic_patterns = {
            "lighting": {
                "display_name": "Generic Lighting",
                "device_classes": ["light"],
                "supported_features": {"light": ["brightness", "on_off"]},
                "priority": 30,
            },
            "climate": {
                "display_name": "Generic Climate",
                "device_classes": ["climate"],
                "supported_features": {"climate": ["temperature", "mode"]},
                "priority": 30,
            },
            "security": {
                "display_name": "Generic Security",
                "device_classes": ["camera", "binary_sensor"],
                "supported_features": {
                    "camera": ["streaming"],
                    "binary_sensor": ["motion"],
                },
                "priority": 30,
            },
            "media": {
                "display_name": "Generic Media",
                "device_classes": ["media_player"],
                "supported_features": {"media_player": ["play", "pause", "volume"]},
                "priority": 30,
            },
            "switch": {
                "display_name": "Generic Switch",
                "device_classes": ["switch"],
                "supported_features": {"switch": ["on_off"]},
                "priority": 30,
            },
        }

    async def match_integrations(
        self, brand: Optional[str], function: Optional[str], keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """Match device information to Home Assistant integrations."""

        logger.info(
            f"Matching integrations for brand='{brand}', function='{function}', keywords={keywords}"
        )

        matches = []

        # First, try exact integration matching
        for integration_id, integration in self.integration_patterns.items():
            score = self._calculate_integration_match_score(
                brand, function, keywords, integration
            )

            if score > 0.3:  # Threshold for consideration
                match = {
                    "integration_id": integration_id,
                    "display_name": integration["display_name"],
                    "score": score,
                    "requires_auth": integration.get("auth_required", False),
                    "requires_hub": integration.get("requires_hub", False),
                    "auth_methods": integration.get("auth_methods", []),
                    "config_fields": integration.get("config_fields", []),
                    "device_classes": integration.get("device_classes", []),
                    "supported_features": integration.get("supported_features", {}),
                    "discovery_methods": integration.get("discovery_methods", []),
                    "ha_domain": integration.get("ha_domain", integration_id),
                    "priority": integration.get("priority", 50),
                }
                matches.append(match)

        # Sort by score and priority
        matches.sort(key=lambda x: (x["score"], x["priority"]), reverse=True)

        # If no good matches, try generic patterns
        if not matches or matches[0]["score"] < 0.5:
            generic_matches = self._match_generic_patterns(function, keywords)
            matches.extend(generic_matches)

        logger.info(f"Found {len(matches)} integration matches")
        return matches[:5]  # Return top 5 matches

    def _calculate_integration_match_score(
        self,
        brand: Optional[str],
        function: Optional[str],
        keywords: List[str],
        integration: Dict[str, Any],
    ) -> float:
        """Calculate how well device information matches an integration."""

        score = 0.0

        # Brand matching (highest weight)
        if brand:
            brand_lower = brand.lower()
            brand_keywords = integration.get("brand_keywords", [])

            for brand_keyword in brand_keywords:
                if (
                    brand_keyword.lower() in brand_lower
                    or brand_lower in brand_keyword.lower()
                ):
                    score += 0.5
                    break

        # Function matching (second highest weight)
        if function:
            function_lower = function.lower()
            function_keywords = integration.get("function_keywords", [])

            for func_keyword in function_keywords:
                if (
                    func_keyword.lower() in function_lower
                    or function_lower in func_keyword.lower()
                ):
                    score += 0.3
                    break

        # Model pattern matching
        model_patterns = integration.get("model_patterns", [])
        for keyword in keywords:
            keyword_lower = keyword.lower()
            for pattern in model_patterns:
                if pattern.lower() in keyword_lower:
                    score += 0.1
                    break

        # General keyword matching
        all_integration_keywords = (
            integration.get("brand_keywords", [])
            + integration.get("function_keywords", [])
            + integration.get("model_patterns", [])
        )

        keyword_matches = 0
        for keyword in keywords:
            keyword_lower = keyword.lower()
            for integration_keyword in all_integration_keywords:
                if keyword_lower == integration_keyword.lower():
                    keyword_matches += 1
                    break

        if keywords:
            keyword_score = (keyword_matches / len(keywords)) * 0.2
            score += keyword_score

        return min(score, 1.0)

    def _match_generic_patterns(
        self, function: Optional[str], keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """Match to generic patterns when no specific integration is found."""

        matches = []

        if function:
            function_lower = function.lower()

            # Map functions to generic patterns
            function_mapping = {
                "lighting": ["light", "bulb", "lamp", "lighting"],
                "climate": ["thermostat", "temperature", "climate", "hvac"],
                "security": ["camera", "security", "alarm", "surveillance"],
                "media": ["speaker", "tv", "audio", "music", "streaming"],
                "switch": ["switch", "plug", "outlet", "socket"],
            }

            for pattern_id, function_keywords in function_mapping.items():
                if any(fk in function_lower for fk in function_keywords):
                    pattern = self.generic_patterns[pattern_id]
                    match = {
                        "integration_id": f"generic_{pattern_id}",
                        "display_name": pattern["display_name"],
                        "score": 0.4,  # Lower score for generic
                        "requires_auth": False,
                        "requires_hub": False,
                        "auth_methods": [],
                        "config_fields": [],
                        "device_classes": pattern["device_classes"],
                        "supported_features": pattern["supported_features"],
                        "discovery_methods": ["manual"],
                        "ha_domain": pattern_id,
                        "priority": pattern["priority"],
                    }
                    matches.append(match)

        return matches

    def get_integration_requirements(self, integration_id: str) -> Dict[str, Any]:
        """Get detailed requirements for a specific integration."""

        integration = self.integration_patterns.get(integration_id)
        if not integration:
            return {}

        return {
            "requires_hub": integration.get("requires_hub", False),
            "auth_required": integration.get("auth_required", False),
            "auth_methods": integration.get("auth_methods", []),
            "config_fields": integration.get("config_fields", []),
            "discovery_methods": integration.get("discovery_methods", []),
            "supported_protocols": self._get_supported_protocols(integration),
            "setup_complexity": self._assess_setup_complexity(integration),
        }

    def _get_supported_protocols(self, integration: Dict[str, Any]) -> List[str]:
        """Determine supported protocols for an integration."""

        protocols = []
        discovery_methods = integration.get("discovery_methods", [])

        if "mdns" in discovery_methods:
            protocols.append("mdns")
        if "upnp" in discovery_methods:
            protocols.append("upnp")
        if "dhcp" in discovery_methods:
            protocols.append("dhcp")
        if "cloud" in discovery_methods:
            protocols.append("internet")
        if "bluetooth" in discovery_methods:
            protocols.append("bluetooth")
        if "lan_scan" in discovery_methods:
            protocols.append("wifi")

        return protocols

    def _assess_setup_complexity(self, integration: Dict[str, Any]) -> str:
        """Assess the setup complexity of an integration."""

        complexity_score = 0

        if integration.get("requires_hub", False):
            complexity_score += 2
        if integration.get("auth_required", False):
            complexity_score += 2
        if len(integration.get("config_fields", [])) > 2:
            complexity_score += 1
        if "cloud" in integration.get("discovery_methods", []):
            complexity_score += 1

        if complexity_score <= 1:
            return "simple"
        elif complexity_score <= 3:
            return "moderate"
        else:
            return "complex"

    def suggest_setup_order(
        self, matched_integrations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Suggest the optimal order for setting up integrations."""

        # Sort by complexity (simple first) and then by score
        def sort_key(integration):
            requirements = self.get_integration_requirements(
                integration["integration_id"]
            )
            complexity_scores = {"simple": 1, "moderate": 2, "complex": 3}
            complexity = complexity_scores.get(
                requirements.get("setup_complexity", "moderate"), 2
            )
            return (
                complexity,
                -integration["score"],
            )  # Negative score for descending order

        return sorted(matched_integrations, key=sort_key)

    def get_integration_documentation(self, integration_id: str) -> Dict[str, Any]:
        """Get documentation and setup instructions for an integration."""

        integration = self.integration_patterns.get(integration_id)
        if not integration:
            return {}

        # This would typically fetch from Home Assistant documentation
        # For now, return basic information
        return {
            "integration_id": integration_id,
            "display_name": integration["display_name"],
            "description": f"Integration for {integration['display_name']} devices",
            "setup_url": f"https://www.home-assistant.io/integrations/{integration.get('ha_domain', integration_id)}/",
            "requirements": self.get_integration_requirements(integration_id),
            "device_classes": integration.get("device_classes", []),
            "supported_features": integration.get("supported_features", {}),
        }

    def validate_integration_compatibility(
        self,
        integration_id: str,
        device_info: Dict[str, Any],
        environment_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Validate if an integration is compatible with the device and environment."""

        integration = self.integration_patterns.get(integration_id)
        if not integration:
            return {"compatible": False, "reason": "Integration not found"}

        compatibility_issues = []

        # Check hub requirements
        if integration.get("requires_hub", False):
            if not environment_info.get("has_required_hub", False):
                compatibility_issues.append("Requires hub device that wasn't detected")

        # Check network requirements
        discovery_methods = integration.get("discovery_methods", [])
        if "cloud" in discovery_methods:
            if not environment_info.get("internet_access", True):
                compatibility_issues.append("Requires internet access")

        # Check authentication requirements
        if integration.get("auth_required", False):
            if not environment_info.get("user_can_authenticate", True):
                compatibility_issues.append("Requires user authentication")

        return {
            "compatible": len(compatibility_issues) == 0,
            "issues": compatibility_issues,
            "confidence": 1.0 - (len(compatibility_issues) * 0.3),
        }

    def get_all_supported_brands(self) -> List[str]:
        """Get list of all supported brands."""

        brands = set()
        for integration in self.integration_patterns.values():
            brands.update(integration.get("brand_keywords", []))

        return sorted(list(brands))

    def get_integrations_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get integrations filtered by device category."""

        category_mapping = {
            "lighting": ["light"],
            "climate": ["climate"],
            "security": ["camera", "binary_sensor", "alarm_control_panel"],
            "media": ["media_player"],
            "energy": ["sensor"],
            "locks": ["lock"],
            "switches": ["switch"],
        }

        target_classes = category_mapping.get(category.lower(), [])
        if not target_classes:
            return []

        matching_integrations = []
        for integration_id, integration in self.integration_patterns.items():
            device_classes = integration.get("device_classes", [])
            if any(tc in device_classes for tc in target_classes):
                matching_integrations.append(
                    {
                        "integration_id": integration_id,
                        "display_name": integration["display_name"],
                        "device_classes": device_classes,
                        "priority": integration.get("priority", 50),
                    }
                )

        # Sort by priority
        matching_integrations.sort(key=lambda x: x["priority"], reverse=True)
        return matching_integrations
