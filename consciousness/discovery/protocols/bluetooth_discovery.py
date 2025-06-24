"""
Bluetooth device discovery.

This module implements Bluetooth device discovery for smart home devices
that use Bluetooth or Bluetooth Low Energy (BLE) for connectivity.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import bluetooth

    BLUETOOTH_AVAILABLE = True
except ImportError:
    BLUETOOTH_AVAILABLE = False


class BluetoothDiscovery:
    """Bluetooth device discovery implementation."""

    def __init__(self, scan_timeout: int = 10):
        self.scan_timeout = scan_timeout

        # Known smart home device name patterns
        self.device_patterns = {
            "yale": ("Yale", "lock"),
            "august": ("August", "lock"),
            "schlage": ("Schlage", "lock"),
            "lockitron": ("Lockitron", "lock"),
            "tile": ("Tile", "tracker"),
            "fitbit": ("Fitbit", "fitness"),
            "apple watch": ("Apple", "wearable"),
            "bose": ("Bose", "speaker"),
            "beats": ("Apple", "speaker"),
            "jbl": ("JBL", "speaker"),
            "sony": ("Sony", "speaker"),
            "amazon echo": ("Amazon", "speaker"),
            "google home": ("Google", "speaker"),
            "nest": ("Google Nest", "sensor"),
        }

    async def discover(self) -> List[Dict[str, Any]]:
        """Discover Bluetooth devices."""

        if not BLUETOOTH_AVAILABLE:
            logger.warning(
                "Bluetooth library not available, skipping Bluetooth discovery"
            )
            return []

        logger.info("Starting Bluetooth discovery")

        try:
            # Run Bluetooth discovery in executor to avoid blocking
            loop = asyncio.get_event_loop()
            devices = await loop.run_in_executor(None, self._discover_bluetooth_devices)

            # Process and enhance device information
            enhanced_devices = []
            for device in devices:
                enhanced_device = self._enhance_device_info(device)
                if enhanced_device:
                    enhanced_devices.append(enhanced_device)

            logger.info(f"Bluetooth discovery found {len(enhanced_devices)} devices")
            return enhanced_devices

        except Exception as e:
            logger.error(f"Bluetooth discovery failed: {e}")
            return []

    def _discover_bluetooth_devices(self) -> List[Dict[str, Any]]:
        """Discover Bluetooth devices (blocking operation)."""

        devices = []

        try:
            # Discover nearby Bluetooth devices
            nearby_devices = bluetooth.discover_devices(
                duration=self.scan_timeout, lookup_names=True, flush_cache=True
            )

            for addr, name in nearby_devices:
                device = {
                    "address": addr,
                    "name": name or "Unknown Device",
                    "device_class": None,
                    "rssi": None,
                }

                # Try to get device class
                try:
                    device_class = bluetooth.lookup_device_class(addr)
                    device["device_class"] = device_class
                except Exception:
                    pass

                devices.append(device)

        except Exception as e:
            logger.error(f"Bluetooth device discovery failed: {e}")

        return devices

    def _enhance_device_info(self, device: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Enhance device information with smart home device identification."""

        name = device.get("name", "").lower()
        address = device.get("address", "")

        # Skip non-smart home devices
        if not self._is_potential_smart_device(name, device.get("device_class")):
            return None

        # Identify manufacturer and device type
        manufacturer, device_type = self._identify_device(name)

        enhanced_device = {
            "device_id": f"bluetooth_{address.replace(':', '_')}",
            "name": device.get("name", "Unknown Device"),
            "mac_address": address,
            "manufacturer": manufacturer,
            "device_type": device_type,
            "device_class": device.get("device_class"),
            "connection_method": "bluetooth",
            "discovery_method": "bluetooth",
            "discovered_at": datetime.utcnow().isoformat(),
            "properties": {
                "bluetooth_class": device.get("device_class"),
                "rssi": device.get("rssi"),
            },
        }

        return enhanced_device

    def _is_potential_smart_device(
        self, name: str, device_class: Optional[int]
    ) -> bool:
        """Check if device might be a smart home device."""

        # Check name patterns
        smart_keywords = [
            "lock",
            "smart",
            "home",
            "sensor",
            "bulb",
            "light",
            "switch",
            "plug",
            "thermostat",
            "camera",
            "doorbell",
            "yale",
            "august",
            "nest",
            "hue",
            "echo",
            "google",
            "tile",
            "tracker",
        ]

        for keyword in smart_keywords:
            if keyword in name:
                return True

        # Check device class for relevant categories
        if device_class:
            # Major device classes
            major_class = (device_class >> 8) & 0x1F

            # Audio/Video (speakers, headphones)
            if major_class == 0x04:
                return True
            # Peripheral (keyboards, mice, sensors)
            elif major_class == 0x05:
                return True
            # Uncategorized (many IoT devices)
            elif major_class == 0x00:
                return True

        return False

    def _identify_device(self, name: str) -> tuple:
        """Identify device manufacturer and type from name."""

        name_lower = name.lower()

        for pattern, (manufacturer, device_type) in self.device_patterns.items():
            if pattern in name_lower:
                return manufacturer, device_type

        # Generic classification based on keywords
        if any(keyword in name_lower for keyword in ["lock", "door"]):
            return None, "lock"
        elif any(keyword in name_lower for keyword in ["speaker", "audio", "sound"]):
            return None, "speaker"
        elif any(
            keyword in name_lower for keyword in ["sensor", "motion", "temperature"]
        ):
            return None, "sensor"
        elif any(keyword in name_lower for keyword in ["light", "bulb", "lamp"]):
            return None, "light"
        elif any(keyword in name_lower for keyword in ["tracker", "tag"]):
            return None, "tracker"

        return None, "unknown"

    async def discover_ble_devices(self) -> List[Dict[str, Any]]:
        """Discover Bluetooth Low Energy (BLE) devices."""

        logger.info("Starting BLE discovery")

        # Note: This would require additional BLE libraries like bleak
        # For now, return empty list
        logger.warning(
            "BLE discovery not implemented - would require additional libraries"
        )
        return []

    async def get_device_services(self, mac_address: str) -> Optional[List[str]]:
        """Get services offered by a Bluetooth device."""

        if not BLUETOOTH_AVAILABLE:
            return None

        try:
            loop = asyncio.get_event_loop()
            services = await loop.run_in_executor(
                None, self._get_bluetooth_services, mac_address
            )
            return services
        except Exception as e:
            logger.error(f"Failed to get services for {mac_address}: {e}")
            return None

    def _get_bluetooth_services(self, mac_address: str) -> List[str]:
        """Get Bluetooth services (blocking operation)."""

        try:
            services = bluetooth.find_service(address=mac_address)
            service_names = []

            for service in services:
                name = service.get("name")
                if name:
                    service_names.append(name)

            return service_names

        except Exception as e:
            logger.error(f"Failed to find services for {mac_address}: {e}")
            return []
