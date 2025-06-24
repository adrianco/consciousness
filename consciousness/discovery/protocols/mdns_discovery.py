"""
mDNS/Zeroconf device discovery.

This module implements mDNS (Multicast DNS) and Zeroconf service discovery
to find smart home devices that advertise their services on the local network.
Many devices including Philips Hue, Sonos, Roku, and HomeKit devices use mDNS.
"""

import asyncio
import logging
import socket
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from zeroconf import ServiceBrowser, ServiceInfo, ServiceListener, Zeroconf
    from zeroconf.asyncio import AsyncServiceBrowser, AsyncZeroconf

    ZEROCONF_AVAILABLE = True
except ImportError:
    ZEROCONF_AVAILABLE = False
    ServiceListener = object  # Fallback for inheritance

logger = logging.getLogger(__name__)


class DeviceServiceListener(ServiceListener):
    """Listener for mDNS service discovery events."""

    def __init__(self):
        self.discovered_devices: List[Dict[str, Any]] = []
        self._processed_services: set = set()

    def add_service(self, zeroconf: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is discovered."""
        if name in self._processed_services:
            return

        try:
            info = zeroconf.get_service_info(type_, name)
            if info:
                device = self._create_device_from_service_info(info, type_, name)
                if device:
                    self.discovered_devices.append(device)
                    self._processed_services.add(name)
                    logger.debug(f"Discovered mDNS service: {name}")
        except Exception as e:
            logger.error(f"Error processing mDNS service {name}: {e}")

    def remove_service(self, zeroconf: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is removed."""
        logger.debug(f"mDNS service removed: {name}")

    def update_service(self, zeroconf: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is updated."""
        logger.debug(f"mDNS service updated: {name}")

    def _create_device_from_service_info(
        self, info: ServiceInfo, service_type: str, service_name: str
    ) -> Optional[Dict[str, Any]]:
        """Create device information from mDNS service info."""

        if not info.parsed_addresses():
            return None

        # Extract device properties
        properties = {}
        if info.properties:
            for key, value in info.properties.items():
                try:
                    key_str = (
                        key.decode("utf-8") if isinstance(key, bytes) else str(key)
                    )
                    value_str = (
                        value.decode("utf-8")
                        if isinstance(value, bytes)
                        else str(value)
                    )
                    properties[key_str] = value_str
                except UnicodeDecodeError:
                    # Skip properties that can't be decoded
                    continue

        # Try to extract manufacturer and model from properties
        manufacturer = self._extract_manufacturer(properties, service_name)
        model = self._extract_model(properties, service_name)
        device_type = self._infer_device_type(service_type, service_name, properties)

        device = {
            "device_id": f"mdns_{service_name.replace('.', '_')}",
            "name": self._extract_device_name(service_name, properties),
            "service_name": service_name,
            "service_type": service_type,
            "ip_address": str(info.parsed_addresses()[0]),
            "port": info.port,
            "manufacturer": manufacturer,
            "model": model,
            "device_type": device_type,
            "properties": properties,
            "discovery_method": "mdns",
            "discovered_at": datetime.utcnow().isoformat(),
            "server": info.server.decode("utf-8") if info.server else None,
        }

        return device

    def _extract_device_name(
        self, service_name: str, properties: Dict[str, str]
    ) -> str:
        """Extract a friendly device name."""

        # Look for common name properties
        name_keys = ["fn", "name", "friendlyname", "device_name", "model_name"]
        for key in name_keys:
            if key in properties:
                return properties[key]

        # Fall back to service name cleanup
        name = service_name.split(".")[0]  # Remove domain parts
        return name.replace("_", " ").title()

    def _extract_manufacturer(
        self, properties: Dict[str, str], service_name: str
    ) -> Optional[str]:
        """Extract manufacturer from properties or service name."""

        # Look for manufacturer in properties
        mfg_keys = ["manufacturer", "vendor", "brand", "mf"]
        for key in mfg_keys:
            if key in properties:
                return properties[key]

        # Try to infer from service name
        service_lower = service_name.lower()

        manufacturers = {
            "philips": "Philips",
            "hue": "Philips",
            "sonos": "Sonos",
            "roku": "Roku",
            "apple": "Apple",
            "google": "Google",
            "nest": "Google Nest",
            "samsung": "Samsung",
            "lg": "LG",
            "sony": "Sony",
        }

        for keyword, manufacturer in manufacturers.items():
            if keyword in service_lower:
                return manufacturer

        return None

    def _extract_model(
        self, properties: Dict[str, str], service_name: str
    ) -> Optional[str]:
        """Extract model from properties or service name."""

        # Look for model in properties
        model_keys = ["model", "model_name", "device_model", "md"]
        for key in model_keys:
            if key in properties:
                return properties[key]

        return None

    def _infer_device_type(
        self, service_type: str, service_name: str, properties: Dict[str, str]
    ) -> Optional[str]:
        """Infer device type from service information."""

        service_type_lower = service_type.lower()
        service_name_lower = service_name.lower()

        # Service type mappings
        type_mappings = {
            "_hue._tcp.": "hub",
            "_philips-hue._tcp.": "hub",
            "_sonos._tcp.": "speaker",
            "_roku-rcp._tcp.": "media_player",
            "_googlecast._tcp.": "media_player",
            "_airplay._tcp.": "media_player",
            "_hap._tcp.": "homekit_device",
            "_http._tcp.": "web_device",
            "_ipp._tcp.": "printer",
            "_ssh._tcp.": "computer",
        }

        for service_pattern, device_type in type_mappings.items():
            if service_pattern in service_type_lower:
                return device_type

        # Check device type from properties
        if "device_type" in properties:
            return properties["device_type"]

        # Infer from service name
        if "bridge" in service_name_lower or "hub" in service_name_lower:
            return "hub"
        elif "speaker" in service_name_lower or "audio" in service_name_lower:
            return "speaker"
        elif "camera" in service_name_lower:
            return "camera"
        elif "light" in service_name_lower or "bulb" in service_name_lower:
            return "light"

        return "unknown"


class MDNSDiscovery:
    """mDNS/Zeroconf device discovery implementation."""

    def __init__(self, discovery_timeout: int = 10):
        self.discovery_timeout = discovery_timeout

        # Common smart home service types
        self.service_types = [
            "_hue._tcp.local.",  # Philips Hue Bridge
            "_philips-hue._tcp.local.",  # Alternative Hue service
            "_sonos._tcp.local.",  # Sonos speakers
            "_roku-rcp._tcp.local.",  # Roku devices
            "_googlecast._tcp.local.",  # Chromecast/Google Cast
            "_airplay._tcp.local.",  # Apple AirPlay
            "_hap._tcp.local.",  # HomeKit Accessory Protocol
            "_spotify-connect._tcp.local.",  # Spotify Connect
            "_http._tcp.local.",  # Generic HTTP services
            "_homekit._tcp.local.",  # HomeKit devices
            "_matter._tcp.local.",  # Matter devices
            "_thread._tcp.local.",  # Thread devices
            "_ipp._tcp.local.",  # Internet Printing Protocol
            "_printer._tcp.local.",  # Printers
            "_smb._tcp.local.",  # SMB/CIFS shares
            "_ssh._tcp.local.",  # SSH services
        ]

    async def discover(self) -> List[Dict[str, Any]]:
        """Discover all mDNS services."""

        if not ZEROCONF_AVAILABLE:
            logger.warning("Zeroconf library not available, skipping mDNS discovery")
            return []

        logger.info("Starting mDNS discovery")

        try:
            # Use async zeroconf for better performance
            azeroconf = AsyncZeroconf()

            # Create listener for all service types
            listener = DeviceServiceListener()
            browsers = []

            # Browse for each service type
            for service_type in self.service_types:
                try:
                    browser = AsyncServiceBrowser(
                        azeroconf.zeroconf, service_type, listener=listener
                    )
                    browsers.append(browser)
                except Exception as e:
                    logger.error(f"Failed to create browser for {service_type}: {e}")

            # Wait for discovery
            await asyncio.sleep(self.discovery_timeout)

            # Clean up browsers
            for browser in browsers:
                try:
                    await browser.async_cancel()
                except Exception as e:
                    logger.error(f"Error canceling browser: {e}")

            # Clean up zeroconf
            await azeroconf.async_close()

            devices = listener.discovered_devices
            logger.info(f"mDNS discovery found {len(devices)} devices")

            return devices

        except Exception as e:
            logger.error(f"mDNS discovery failed: {e}")
            return []

    async def discover_service(self, service_type: str) -> List[Dict[str, Any]]:
        """Discover devices for a specific service type."""

        if not ZEROCONF_AVAILABLE:
            logger.warning("Zeroconf library not available")
            return []

        logger.info(f"Discovering mDNS service: {service_type}")

        try:
            azeroconf = AsyncZeroconf()
            listener = DeviceServiceListener()

            browser = AsyncServiceBrowser(
                azeroconf.zeroconf, service_type, listener=listener
            )

            # Wait for discovery
            await asyncio.sleep(self.discovery_timeout)

            # Clean up
            await browser.async_cancel()
            await azeroconf.async_close()

            devices = listener.discovered_devices
            logger.info(f"Found {len(devices)} devices for service {service_type}")

            return devices

        except Exception as e:
            logger.error(f"Service discovery failed for {service_type}: {e}")
            return []

    async def discover_hue_bridges(self) -> List[Dict[str, Any]]:
        """Specifically discover Philips Hue bridges."""

        hue_services = ["_hue._tcp.local.", "_philips-hue._tcp.local."]
        all_devices = []

        for service in hue_services:
            devices = await self.discover_service(service)
            all_devices.extend(devices)

        # Filter and enhance Hue-specific information
        hue_bridges = []
        for device in all_devices:
            if self._is_hue_bridge(device):
                enhanced_device = await self._enhance_hue_device(device)
                hue_bridges.append(enhanced_device)

        return hue_bridges

    def _is_hue_bridge(self, device: Dict[str, Any]) -> bool:
        """Check if device is a Hue bridge."""

        name = device.get("name", "").lower()
        service_type = device.get("service_type", "").lower()
        manufacturer = device.get("manufacturer", "").lower()

        hue_indicators = [
            "hue" in name,
            "philips" in name,
            "_hue._tcp" in service_type,
            "philips" in manufacturer,
        ]

        return any(hue_indicators)

    async def _enhance_hue_device(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance Hue device with additional information."""

        enhanced = device.copy()

        # Try to get bridge info via HTTP
        ip_address = device.get("ip_address")
        if ip_address:
            try:
                bridge_info = await self._get_hue_bridge_info(ip_address)
                if bridge_info:
                    enhanced["hue_bridge_info"] = bridge_info
            except Exception as e:
                logger.debug(f"Failed to get Hue bridge info: {e}")

        # Set device type
        enhanced["device_type"] = "hue_bridge"
        enhanced["manufacturer"] = "Philips"

        return enhanced

    async def _get_hue_bridge_info(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get Hue bridge information via HTTP API."""

        try:
            import aiohttp

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=5)
            ) as session:
                async with session.get(f"http://{ip_address}/api/config") as response:
                    if response.status == 200:
                        return await response.json()
        except Exception:
            pass

        return None

    async def discover_sonos_devices(self) -> List[Dict[str, Any]]:
        """Specifically discover Sonos speakers."""

        devices = await self.discover_service("_sonos._tcp.local.")

        # Enhance Sonos-specific information
        sonos_devices = []
        for device in devices:
            if self._is_sonos_device(device):
                enhanced_device = await self._enhance_sonos_device(device)
                sonos_devices.append(enhanced_device)

        return sonos_devices

    def _is_sonos_device(self, device: Dict[str, Any]) -> bool:
        """Check if device is a Sonos speaker."""

        name = device.get("name", "").lower()
        manufacturer = device.get("manufacturer", "").lower()
        service_type = device.get("service_type", "").lower()

        return (
            "sonos" in name or "sonos" in manufacturer or "_sonos._tcp" in service_type
        )

    async def _enhance_sonos_device(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance Sonos device with additional information."""

        enhanced = device.copy()
        enhanced["device_type"] = "speaker"
        enhanced["manufacturer"] = "Sonos"

        # Try to get additional Sonos info
        ip_address = device.get("ip_address")
        if ip_address:
            try:
                sonos_info = await self._get_sonos_device_info(ip_address)
                if sonos_info:
                    enhanced["sonos_device_info"] = sonos_info
            except Exception as e:
                logger.debug(f"Failed to get Sonos device info: {e}")

        return enhanced

    async def _get_sonos_device_info(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get Sonos device information via HTTP."""

        try:
            import aiohttp

            # Sonos uses port 1400 for HTTP API
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=5)
            ) as session:
                async with session.get(
                    f"http://{ip_address}:1400/xml/device_description.xml"
                ) as response:
                    if response.status == 200:
                        xml_data = await response.text()
                        # Parse basic info from XML (simplified)
                        return {
                            "xml_description": xml_data[:500]
                        }  # Truncated for brevity
        except Exception:
            pass

        return None

    async def discover_roku_devices(self) -> List[Dict[str, Any]]:
        """Specifically discover Roku devices."""

        devices = await self.discover_service("_roku-rcp._tcp.local.")

        # Enhance Roku-specific information
        roku_devices = []
        for device in devices:
            enhanced_device = await self._enhance_roku_device(device)
            roku_devices.append(enhanced_device)

        return roku_devices

    async def _enhance_roku_device(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance Roku device with additional information."""

        enhanced = device.copy()
        enhanced["device_type"] = "media_player"
        enhanced["manufacturer"] = "Roku"

        return enhanced

    async def discover_chromecast_devices(self) -> List[Dict[str, Any]]:
        """Specifically discover Chromecast devices."""

        devices = await self.discover_service("_googlecast._tcp.local.")

        # Enhance Chromecast-specific information
        chromecast_devices = []
        for device in devices:
            enhanced_device = await self._enhance_chromecast_device(device)
            chromecast_devices.append(enhanced_device)

        return chromecast_devices

    async def _enhance_chromecast_device(
        self, device: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance Chromecast device with additional information."""

        enhanced = device.copy()
        enhanced["device_type"] = "media_player"
        enhanced["manufacturer"] = "Google"

        # Extract model from properties
        properties = device.get("properties", {})
        if "md" in properties:
            enhanced["model"] = properties["md"]

        return enhanced

    async def discover_homekit_devices(self) -> List[Dict[str, Any]]:
        """Specifically discover HomeKit devices."""

        devices = await self.discover_service("_hap._tcp.local.")

        # Enhance HomeKit-specific information
        homekit_devices = []
        for device in devices:
            enhanced_device = await self._enhance_homekit_device(device)
            homekit_devices.append(enhanced_device)

        return homekit_devices

    async def _enhance_homekit_device(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance HomeKit device with additional information."""

        enhanced = device.copy()
        enhanced["device_type"] = "homekit_accessory"
        enhanced["protocol"] = "homekit"

        # Extract HomeKit-specific properties
        properties = device.get("properties", {})

        # Category ID mapping (simplified)
        category_map = {
            "1": "other",
            "2": "bridge",
            "3": "fan",
            "4": "garage_door_opener",
            "5": "lightbulb",
            "6": "door_lock",
            "7": "outlet",
            "8": "switch",
            "9": "thermostat",
            "10": "sensor",
            "11": "security_system",
            "12": "door",
            "13": "window",
            "14": "window_covering",
            "15": "programmable_switch",
            "16": "range_extender",
            "17": "ip_camera",
            "18": "video_doorbell",
            "19": "air_purifier",
            "20": "heater",
            "21": "air_conditioner",
            "22": "humidifier",
            "23": "dehumidifier",
            "28": "sprinkler",
            "29": "faucet",
            "30": "shower_head",
        }

        if "ci" in properties:
            category_id = properties["ci"]
            enhanced["homekit_category"] = category_map.get(category_id, "unknown")

        return enhanced

    async def get_device_info(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get additional device information via HTTP."""

        try:
            import aiohttp

            # Try common HTTP endpoints
            endpoints = [
                f"http://{ip_address}/",
                f"http://{ip_address}/description.xml",
                f"http://{ip_address}/device.xml",
                f"http://{ip_address}/api/",
                f"http://{ip_address}/info",
            ]

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=5)
            ) as session:
                for endpoint in endpoints:
                    try:
                        async with session.get(endpoint) as response:
                            if response.status == 200:
                                content_type = response.headers.get(
                                    "content-type", ""
                                ).lower()

                                if "json" in content_type:
                                    return {
                                        "endpoint": endpoint,
                                        "data": await response.json(),
                                    }
                                elif "xml" in content_type:
                                    xml_data = await response.text()
                                    return {
                                        "endpoint": endpoint,
                                        "xml": xml_data[:1000],
                                    }  # Truncated
                                else:
                                    text_data = await response.text()
                                    return {
                                        "endpoint": endpoint,
                                        "text": text_data[:500],
                                    }  # Truncated
                    except Exception:
                        continue

        except Exception as e:
            logger.debug(f"Failed to get device info for {ip_address}: {e}")

        return None
