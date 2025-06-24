"""
Multi-protocol automatic device discovery service.

This service coordinates device discovery across multiple protocols including
mDNS/Zeroconf, UPnP, DHCP, Bluetooth, and Zigbee to automatically detect
smart home devices on the network.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from consciousness.discovery.protocols.bluetooth_discovery import BluetoothDiscovery
from consciousness.discovery.protocols.dhcp_discovery import DHCPDiscovery
from consciousness.discovery.protocols.mdns_discovery import MDNSDiscovery
from consciousness.discovery.protocols.upnp_discovery import UPnPDiscovery
from consciousness.discovery.protocols.zigbee_discovery import ZigbeeDiscovery

logger = logging.getLogger(__name__)


class DiscoveryResult:
    """Represents a discovered device with metadata."""

    def __init__(
        self,
        device_id: str,
        name: str,
        discovery_method: str,
        device_type: Optional[str] = None,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        ip_address: Optional[str] = None,
        mac_address: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ):
        self.device_id = device_id
        self.name = name
        self.discovery_method = discovery_method
        self.device_type = device_type
        self.manufacturer = manufacturer
        self.model = model
        self.ip_address = ip_address
        self.mac_address = mac_address
        self.properties = properties or {}
        self.discovered_at = datetime.utcnow()
        self.last_seen = datetime.utcnow()
        self.confidence_score = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "device_id": self.device_id,
            "name": self.name,
            "discovery_method": self.discovery_method,
            "device_type": self.device_type,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "ip_address": self.ip_address,
            "mac_address": self.mac_address,
            "properties": self.properties,
            "discovered_at": self.discovered_at.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "confidence_score": self.confidence_score,
        }


class AutoDiscoveryService:
    """Coordinates automatic device discovery across all protocols."""

    def __init__(
        self,
        discovery_timeout: int = 30,
        enable_parallel_discovery: bool = True,
        cache_duration: int = 300,  # 5 minutes
    ):
        self.discovery_timeout = discovery_timeout
        self.enable_parallel_discovery = enable_parallel_discovery
        self.cache_duration = cache_duration

        # Initialize discovery protocol handlers
        self.mdns = MDNSDiscovery()
        self.upnp = UPnPDiscovery()
        self.dhcp = DHCPDiscovery()
        self.bluetooth = BluetoothDiscovery()
        self.zigbee = ZigbeeDiscovery()

        # Discovery cache
        self._discovery_cache: Dict[str, DiscoveryResult] = {}
        self._last_discovery: Optional[datetime] = None

        # Device correlation patterns
        self._initialize_device_patterns()

    def _initialize_device_patterns(self) -> None:
        """Initialize patterns for identifying and correlating devices."""

        # Device identification patterns
        self.device_patterns = {
            "hue": {
                "mdns_service": "_hue._tcp.local.",
                "upnp_device_type": "urn:philips-com:device:bridge",
                "manufacturer_keywords": ["philips", "hue"],
                "model_keywords": ["bridge", "hue"],
                "default_ports": [80, 443, 1900],
            },
            "nest": {
                "manufacturer_keywords": ["nest", "google"],
                "model_keywords": ["thermostat", "protect", "cam"],
                "cloud_discovery": True,
            },
            "ring": {
                "upnp_device_type": "urn:ring-com:device",
                "manufacturer_keywords": ["ring"],
                "model_keywords": ["doorbell", "camera", "chime"],
                "cloud_discovery": True,
            },
            "sonos": {
                "mdns_service": "_sonos._tcp.local.",
                "upnp_device_type": "urn:smartspeaker-audio:device",
                "manufacturer_keywords": ["sonos"],
                "model_keywords": ["play", "beam", "arc", "sub", "one", "five"],
                "default_ports": [1400, 1443],
            },
            "roku": {
                "mdns_service": "_roku-rcp._tcp.local.",
                "manufacturer_keywords": ["roku"],
                "model_keywords": ["ultra", "express", "premiere", "stick"],
                "default_ports": [8060, 8443],
            },
            "tesla": {
                "manufacturer_keywords": ["tesla"],
                "model_keywords": ["powerwall", "solar", "gateway"],
                "cloud_discovery": True,
                "local_discovery": True,
                "default_ports": [443],
            },
        }

    async def discover_all_protocols(
        self, target_protocols: Optional[List[str]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Run discovery across all protocols in parallel."""

        logger.info("Starting multi-protocol device discovery")

        # Check cache first
        if self._is_cache_valid():
            logger.info("Using cached discovery results")
            return self._get_cached_results()

        protocols = target_protocols or ["mdns", "upnp", "dhcp", "bluetooth", "zigbee"]

        if self.enable_parallel_discovery:
            results = await self._run_parallel_discovery(protocols)
        else:
            results = await self._run_sequential_discovery(protocols)

        # Process and correlate results
        processed_results = await self._process_discovery_results(results)

        # Update cache
        self._update_cache(processed_results)
        self._last_discovery = datetime.utcnow()

        logger.info(
            f"Discovery completed. Found {sum(len(devices) for devices in processed_results.values())} devices"
        )

        return processed_results

    async def _run_parallel_discovery(
        self, protocols: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Run discovery protocols in parallel."""

        tasks = []

        for protocol in protocols:
            if protocol == "mdns":
                task = asyncio.create_task(
                    self._safe_discovery(self.mdns.discover(), "mdns")
                )
            elif protocol == "upnp":
                task = asyncio.create_task(
                    self._safe_discovery(self.upnp.discover(), "upnp")
                )
            elif protocol == "dhcp":
                task = asyncio.create_task(
                    self._safe_discovery(self.dhcp.discover(), "dhcp")
                )
            elif protocol == "bluetooth":
                task = asyncio.create_task(
                    self._safe_discovery(self.bluetooth.discover(), "bluetooth")
                )
            elif protocol == "zigbee":
                task = asyncio.create_task(
                    self._safe_discovery(self.zigbee.discover(), "zigbee")
                )
            else:
                logger.warning(f"Unknown protocol: {protocol}")
                continue

            tasks.append(task)

        # Wait for all discoveries to complete with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.discovery_timeout,
            )
        except asyncio.TimeoutError:
            logger.warning(f"Discovery timeout after {self.discovery_timeout} seconds")
            # Cancel remaining tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
            results = [task.result() if task.done() else [] for task in tasks]

        # Combine results
        combined_results = {}
        for i, protocol in enumerate(protocols):
            if i < len(results) and not isinstance(results[i], Exception):
                combined_results[protocol] = results[i]
            else:
                combined_results[protocol] = []
                if i < len(results) and isinstance(results[i], Exception):
                    logger.error(f"Discovery error for {protocol}: {results[i]}")

        return combined_results

    async def _run_sequential_discovery(
        self, protocols: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Run discovery protocols sequentially."""

        results = {}

        for protocol in protocols:
            try:
                if protocol == "mdns":
                    results[protocol] = await self.mdns.discover()
                elif protocol == "upnp":
                    results[protocol] = await self.upnp.discover()
                elif protocol == "dhcp":
                    results[protocol] = await self.dhcp.discover()
                elif protocol == "bluetooth":
                    results[protocol] = await self.bluetooth.discover()
                elif protocol == "zigbee":
                    results[protocol] = await self.zigbee.discover()
                else:
                    logger.warning(f"Unknown protocol: {protocol}")
                    results[protocol] = []

            except Exception as e:
                logger.error(f"Discovery error for {protocol}: {e}")
                results[protocol] = []

        return results

    async def _safe_discovery(
        self, discovery_coro, protocol_name: str
    ) -> List[Dict[str, Any]]:
        """Safely run a discovery coroutine with error handling."""

        try:
            return await discovery_coro
        except Exception as e:
            logger.error(f"Error in {protocol_name} discovery: {e}")
            return []

    async def _process_discovery_results(
        self, raw_results: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Process and enhance discovery results."""

        processed_results = {}
        all_devices = []

        # First pass: convert to DiscoveryResult objects
        for protocol, devices in raw_results.items():
            processed_devices = []

            for device_data in devices:
                discovery_result = self._create_discovery_result(device_data, protocol)
                processed_devices.append(discovery_result)
                all_devices.append(discovery_result)

            processed_results[protocol] = [d.to_dict() for d in processed_devices]

        # Second pass: correlate devices across protocols
        correlated_devices = await self._correlate_devices(all_devices)

        # Third pass: enhance with device identification
        enhanced_results = {}
        for protocol, devices in processed_results.items():
            enhanced_devices = []
            for device in devices:
                enhanced_device = await self._enhance_device_info(
                    device, correlated_devices
                )
                enhanced_devices.append(enhanced_device)
            enhanced_results[protocol] = enhanced_devices

        return enhanced_results

    def _create_discovery_result(
        self, device_data: Dict[str, Any], discovery_method: str
    ) -> DiscoveryResult:
        """Create a DiscoveryResult from raw device data."""

        # Extract common fields
        device_id = device_data.get("id", device_data.get("device_id", "unknown"))
        name = device_data.get("name", device_data.get("device_name", "Unknown Device"))
        device_type = device_data.get("type", device_data.get("device_type"))
        manufacturer = device_data.get("manufacturer", device_data.get("vendor"))
        model = device_data.get("model", device_data.get("model_name"))
        ip_address = device_data.get("ip", device_data.get("ip_address"))
        mac_address = device_data.get("mac", device_data.get("mac_address"))

        # Create properties from remaining fields
        properties = {
            k: v
            for k, v in device_data.items()
            if k
            not in [
                "id",
                "device_id",
                "name",
                "device_name",
                "type",
                "device_type",
                "manufacturer",
                "vendor",
                "model",
                "model_name",
                "ip",
                "ip_address",
                "mac",
                "mac_address",
            ]
        }

        return DiscoveryResult(
            device_id=device_id,
            name=name,
            discovery_method=discovery_method,
            device_type=device_type,
            manufacturer=manufacturer,
            model=model,
            ip_address=ip_address,
            mac_address=mac_address,
            properties=properties,
        )

    async def _correlate_devices(
        self, devices: List[DiscoveryResult]
    ) -> Dict[str, List[DiscoveryResult]]:
        """Correlate devices found across different protocols."""

        correlated = {}
        processed_devices = set()

        for device in devices:
            if id(device) in processed_devices:
                continue

            # Find related devices
            related_devices = [device]

            for other_device in devices:
                if id(other_device) in processed_devices or device == other_device:
                    continue

                if self._are_devices_related(device, other_device):
                    related_devices.append(other_device)
                    processed_devices.add(id(other_device))

            # Create correlation key
            correlation_key = self._generate_correlation_key(device)
            correlated[correlation_key] = related_devices
            processed_devices.add(id(device))

        return correlated

    def _are_devices_related(
        self, device1: DiscoveryResult, device2: DiscoveryResult
    ) -> bool:
        """Check if two devices are the same device discovered via different protocols."""

        # Check IP address match
        if (
            device1.ip_address
            and device2.ip_address
            and device1.ip_address == device2.ip_address
        ):
            return True

        # Check MAC address match
        if (
            device1.mac_address
            and device2.mac_address
            and device1.mac_address.lower() == device2.mac_address.lower()
        ):
            return True

        # Check name similarity
        if (
            device1.name
            and device2.name
            and self._calculate_name_similarity(device1.name, device2.name) > 0.8
        ):
            return True

        # Check manufacturer and model match
        if (
            device1.manufacturer
            and device2.manufacturer
            and device1.manufacturer.lower() == device2.manufacturer.lower()
            and device1.model
            and device2.model
            and device1.model.lower() == device2.model.lower()
        ):
            return True

        return False

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two device names."""

        # Simple similarity based on common words
        words1 = set(name1.lower().split())
        words2 = set(name2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)

    def _generate_correlation_key(self, device: DiscoveryResult) -> str:
        """Generate a correlation key for a device."""

        # Use IP address if available
        if device.ip_address:
            return f"ip_{device.ip_address}"

        # Use MAC address if available
        if device.mac_address:
            return f"mac_{device.mac_address.lower()}"

        # Use name and manufacturer
        name_part = device.name.lower().replace(" ", "_") if device.name else "unknown"
        mfg_part = (
            device.manufacturer.lower().replace(" ", "_")
            if device.manufacturer
            else "unknown"
        )

        return f"name_{name_part}_{mfg_part}"

    async def _enhance_device_info(
        self,
        device: Dict[str, Any],
        correlated_devices: Dict[str, List[DiscoveryResult]],
    ) -> Dict[str, Any]:
        """Enhance device information with additional details."""

        enhanced_device = device.copy()

        # Find correlation group for this device
        correlation_group = None
        for group in correlated_devices.values():
            for corr_device in group:
                if (
                    corr_device.device_id == device["device_id"]
                    and corr_device.discovery_method == device["discovery_method"]
                ):
                    correlation_group = group
                    break
            if correlation_group:
                break

        if correlation_group and len(correlation_group) > 1:
            # Merge information from related devices
            enhanced_device = self._merge_device_information(device, correlation_group)

        # Add device pattern matching
        pattern_match = self._match_device_pattern(enhanced_device)
        if pattern_match:
            enhanced_device["pattern_match"] = pattern_match
            enhanced_device["confidence_score"] = pattern_match.get("confidence", 0.5)

        return enhanced_device

    def _merge_device_information(
        self, primary_device: Dict[str, Any], related_devices: List[DiscoveryResult]
    ) -> Dict[str, Any]:
        """Merge information from related devices discovered via different protocols."""

        merged = primary_device.copy()

        # Collect all available information
        all_names = set()
        all_manufacturers = set()
        all_models = set()
        all_ips = set()
        all_macs = set()
        all_properties = {}

        for device in related_devices:
            if device.name:
                all_names.add(device.name)
            if device.manufacturer:
                all_manufacturers.add(device.manufacturer)
            if device.model:
                all_models.add(device.model)
            if device.ip_address:
                all_ips.add(device.ip_address)
            if device.mac_address:
                all_macs.add(device.mac_address)

            # Merge properties
            for key, value in device.properties.items():
                if key not in all_properties:
                    all_properties[key] = value

        # Choose best values
        if not merged.get("name") and all_names:
            merged["name"] = max(all_names, key=len)  # Choose longest name

        if not merged.get("manufacturer") and all_manufacturers:
            merged["manufacturer"] = list(all_manufacturers)[0]

        if not merged.get("model") and all_models:
            merged["model"] = list(all_models)[0]

        if not merged.get("ip_address") and all_ips:
            merged["ip_address"] = list(all_ips)[0]

        if not merged.get("mac_address") and all_macs:
            merged["mac_address"] = list(all_macs)[0]

        # Add correlation info
        merged["correlated_protocols"] = [d.discovery_method for d in related_devices]
        merged["correlation_confidence"] = min(1.0, len(related_devices) * 0.3)

        # Merge properties
        merged["properties"].update(all_properties)

        return merged

    def _match_device_pattern(self, device: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Match device against known device patterns."""

        device_name = device.get("name", "").lower()
        manufacturer = device.get("manufacturer", "").lower()
        model = device.get("model", "").lower()
        device_type = device.get("device_type", "").lower()

        best_match = None
        best_score = 0.0

        for pattern_id, pattern in self.device_patterns.items():
            score = 0.0

            # Check manufacturer keywords
            manufacturer_keywords = pattern.get("manufacturer_keywords", [])
            for keyword in manufacturer_keywords:
                if keyword in manufacturer or keyword in device_name:
                    score += 0.4
                    break

            # Check model keywords
            model_keywords = pattern.get("model_keywords", [])
            for keyword in model_keywords:
                if keyword in model or keyword in device_name:
                    score += 0.3
                    break

            # Check service/device type matching
            if pattern.get("mdns_service") in device.get("properties", {}):
                score += 0.3

            if pattern.get("upnp_device_type") in device.get("properties", {}):
                score += 0.3

            if score > best_score:
                best_score = score
                best_match = {
                    "pattern_id": pattern_id,
                    "confidence": score,
                    "matched_pattern": pattern,
                }

        return best_match if best_score > 0.3 else None

    async def discover_for_integration(
        self, integration_type: str, timeout: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Run targeted discovery for a specific integration type."""

        logger.info(f"Running targeted discovery for {integration_type}")

        pattern = self.device_patterns.get(integration_type)
        if not pattern:
            logger.warning(f"No discovery pattern for {integration_type}")
            return []

        timeout = timeout or self.discovery_timeout
        tasks = []

        # Run targeted discovery methods
        if pattern.get("mdns_service"):
            tasks.append(self.mdns.discover_service(pattern["mdns_service"]))

        if pattern.get("upnp_device_type"):
            tasks.append(self.upnp.discover_device_type(pattern["upnp_device_type"]))

        if pattern.get("default_ports"):
            tasks.append(self.dhcp.scan_ports(pattern["default_ports"]))

        if not tasks:
            return []

        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True), timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Targeted discovery timeout for {integration_type}")
            return []

        # Combine and filter results
        combined_devices = []
        for result in results:
            if isinstance(result, list):
                combined_devices.extend(result)

        # Filter to only include devices matching the pattern
        filtered_devices = []
        for device in combined_devices:
            if self._device_matches_pattern(device, pattern):
                filtered_devices.append(device)

        logger.info(f"Found {len(filtered_devices)} devices for {integration_type}")
        return filtered_devices

    def _device_matches_pattern(
        self, device: Dict[str, Any], pattern: Dict[str, Any]
    ) -> bool:
        """Check if a device matches a specific pattern."""

        device_text = str(device).lower()

        # Check manufacturer keywords
        manufacturer_keywords = pattern.get("manufacturer_keywords", [])
        if manufacturer_keywords:
            if not any(keyword in device_text for keyword in manufacturer_keywords):
                return False

        # Check model keywords (optional)
        model_keywords = pattern.get("model_keywords", [])
        if model_keywords:
            if any(keyword in device_text for keyword in model_keywords):
                return True

        return True

    def _is_cache_valid(self) -> bool:
        """Check if discovery cache is still valid."""

        if not self._last_discovery:
            return False

        age = (datetime.utcnow() - self._last_discovery).total_seconds()
        return age < self.cache_duration

    def _get_cached_results(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get results from cache."""

        # Group cached devices by discovery method
        results = {}
        for device in self._discovery_cache.values():
            method = device.discovery_method
            if method not in results:
                results[method] = []
            results[method].append(device.to_dict())

        return results

    def _update_cache(self, results: Dict[str, List[Dict[str, Any]]]) -> None:
        """Update discovery cache with new results."""

        self._discovery_cache.clear()

        for protocol, devices in results.items():
            for device_data in devices:
                device_id = device_data["device_id"]
                device = DiscoveryResult(
                    device_id=device_id,
                    name=device_data["name"],
                    discovery_method=device_data["discovery_method"],
                    device_type=device_data.get("device_type"),
                    manufacturer=device_data.get("manufacturer"),
                    model=device_data.get("model"),
                    ip_address=device_data.get("ip_address"),
                    mac_address=device_data.get("mac_address"),
                    properties=device_data.get("properties", {}),
                )
                self._discovery_cache[device_id] = device

    async def get_device_details(
        self, device_id: str, discovery_method: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific discovered device."""

        device = self._discovery_cache.get(device_id)
        if not device:
            return None

        details = device.to_dict()

        # Try to get additional details based on discovery method
        if discovery_method == "mdns" and device.ip_address:
            additional_info = await self.mdns.get_device_info(device.ip_address)
            details["additional_info"] = additional_info

        elif discovery_method == "upnp" and device.ip_address:
            additional_info = await self.upnp.get_device_description(device.ip_address)
            details["additional_info"] = additional_info

        return details

    def clear_cache(self) -> None:
        """Clear the discovery cache."""
        self._discovery_cache.clear()
        self._last_discovery = None
        logger.info("Discovery cache cleared")

    def get_discovery_statistics(self) -> Dict[str, Any]:
        """Get statistics about the discovery process."""

        stats = {
            "cached_devices": len(self._discovery_cache),
            "last_discovery": self._last_discovery.isoformat()
            if self._last_discovery
            else None,
            "cache_age_seconds": (
                (datetime.utcnow() - self._last_discovery).total_seconds()
                if self._last_discovery
                else None
            ),
            "discovery_methods": {},
            "device_types": {},
            "manufacturers": {},
        }

        # Count by discovery method
        for device in self._discovery_cache.values():
            method = device.discovery_method
            stats["discovery_methods"][method] = (
                stats["discovery_methods"].get(method, 0) + 1
            )

            if device.device_type:
                stats["device_types"][device.device_type] = (
                    stats["device_types"].get(device.device_type, 0) + 1
                )

            if device.manufacturer:
                stats["manufacturers"][device.manufacturer] = (
                    stats["manufacturers"].get(device.manufacturer, 0) + 1
                )

        return stats
