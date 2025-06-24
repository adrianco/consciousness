"""
UPnP (Universal Plug and Play) device discovery.

This module implements UPnP discovery to find devices that advertise themselves
using the UPnP protocol, commonly used by media devices, routers, and some
smart home devices.
"""

import asyncio
import logging
import socket
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class UPnPDiscovery:
    """UPnP device discovery implementation."""

    def __init__(self, discovery_timeout: int = 10):
        self.discovery_timeout = discovery_timeout
        self.upnp_port = 1900
        self.upnp_addr = "239.255.255.250"

        # UPnP device types to search for
        self.search_targets = [
            "ssdp:all",
            "urn:schemas-upnp-org:device:MediaRenderer:1",
            "urn:schemas-upnp-org:device:MediaServer:1",
            "urn:schemas-upnp-org:device:InternetGatewayDevice:1",
            "urn:philips-com:device:bridge:1",
            "urn:smartspeaker-audio:device:SpeakerDevice:1",
            "urn:ring-com:device:Doorbell:1",
        ]

    async def discover(self) -> List[Dict[str, Any]]:
        """Discover UPnP devices."""

        logger.info("Starting UPnP discovery")

        discovered_devices = []

        try:
            # Create UDP socket for SSDP
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(self.discovery_timeout)

            # Send M-SEARCH requests for different device types
            for search_target in self.search_targets:
                devices = await self._search_devices(sock, search_target)
                discovered_devices.extend(devices)

            sock.close()

            # Remove duplicates
            unique_devices = self._remove_duplicates(discovered_devices)

            logger.info(f"UPnP discovery found {len(unique_devices)} devices")
            return unique_devices

        except Exception as e:
            logger.error(f"UPnP discovery failed: {e}")
            return []

    async def _search_devices(
        self, sock: socket.socket, search_target: str
    ) -> List[Dict[str, Any]]:
        """Search for devices of a specific type."""

        # Create M-SEARCH request
        msearch_request = (
            f"M-SEARCH * HTTP/1.1\r\n"
            f"HOST: {self.upnp_addr}:{self.upnp_port}\r\n"
            f'MAN: "ssdp:discover"\r\n'
            f"ST: {search_target}\r\n"
            f"MX: 3\r\n\r\n"
        ).encode()

        devices = []

        try:
            # Send search request
            sock.sendto(msearch_request, (self.upnp_addr, self.upnp_port))

            # Collect responses
            end_time = asyncio.get_event_loop().time() + self.discovery_timeout

            while asyncio.get_event_loop().time() < end_time:
                try:
                    data, addr = sock.recvfrom(4096)
                    response = data.decode("utf-8", errors="ignore")

                    device = self._parse_upnp_response(response, addr[0])
                    if device:
                        devices.append(device)

                except socket.timeout:
                    break
                except Exception as e:
                    logger.debug(f"Error parsing UPnP response: {e}")
                    continue

        except Exception as e:
            logger.error(f"UPnP search failed for {search_target}: {e}")

        return devices

    def _parse_upnp_response(
        self, response: str, ip_address: str
    ) -> Optional[Dict[str, Any]]:
        """Parse UPnP M-SEARCH response."""

        if "HTTP/1.1 200 OK" not in response:
            return None

        headers = {}
        lines = response.split("\r\n")

        for line in lines[1:]:  # Skip status line
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip().upper()] = value.strip()

        # Extract device information
        location = headers.get("LOCATION", "")
        usn = headers.get("USN", "")
        st = headers.get("ST", "")
        server = headers.get("SERVER", "")

        # Create device info
        device = {
            "device_id": f"upnp_{usn.replace(':', '_').replace('::', '_')}",
            "name": self._extract_device_name(usn, st),
            "ip_address": ip_address,
            "location": location,
            "usn": usn,
            "search_target": st,
            "server": server,
            "device_type": self._infer_device_type(st, usn),
            "manufacturer": self._extract_manufacturer(server, usn),
            "discovery_method": "upnp",
            "discovered_at": datetime.utcnow().isoformat(),
            "properties": {"upnp_headers": headers},
        }

        return device

    def _extract_device_name(self, usn: str, st: str) -> str:
        """Extract device name from USN or ST."""

        # Try to extract from USN
        if "::" in usn:
            parts = usn.split("::")
            if len(parts) > 1:
                name_part = parts[0].replace("uuid:", "")
                return name_part[:30]  # Truncate long UUIDs

        # Fall back to search target
        if "device:" in st:
            device_type = st.split("device:")[1].split(":")[0]
            return device_type.replace("-", " ").title()

        return "UPnP Device"

    def _extract_manufacturer(self, server: str, usn: str) -> Optional[str]:
        """Extract manufacturer from server string or USN."""

        server_lower = server.lower()

        manufacturers = {
            "philips": "Philips",
            "sonos": "Sonos",
            "roku": "Roku",
            "samsung": "Samsung",
            "lg": "LG",
            "sony": "Sony",
            "panasonic": "Panasonic",
            "linux": "Linux",
            "windows": "Microsoft",
        }

        for keyword, manufacturer in manufacturers.items():
            if keyword in server_lower:
                return manufacturer

        return None

    def _infer_device_type(self, st: str, usn: str) -> Optional[str]:
        """Infer device type from search target."""

        st_lower = st.lower()

        if "mediarenderer" in st_lower:
            return "media_player"
        elif "mediaserver" in st_lower:
            return "media_server"
        elif "bridge" in st_lower:
            return "hub"
        elif "speaker" in st_lower:
            return "speaker"
        elif "doorbell" in st_lower:
            return "doorbell"
        elif "camera" in st_lower:
            return "camera"
        elif "gateway" in st_lower:
            return "router"

        return "unknown"

    def _remove_duplicates(self, devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate devices based on IP and USN."""

        seen = set()
        unique_devices = []

        for device in devices:
            key = (device.get("ip_address"), device.get("usn"))
            if key not in seen:
                seen.add(key)
                unique_devices.append(device)

        return unique_devices

    async def discover_device_type(self, device_type: str) -> List[Dict[str, Any]]:
        """Discover devices of a specific UPnP type."""

        logger.info(f"Discovering UPnP devices of type: {device_type}")

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(self.discovery_timeout)

            devices = await self._search_devices(sock, device_type)
            sock.close()

            logger.info(f"Found {len(devices)} devices of type {device_type}")
            return devices

        except Exception as e:
            logger.error(f"UPnP discovery failed for type {device_type}: {e}")
            return []

    async def get_device_description(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get device description from UPnP location URL."""

        try:
            import aiohttp

            # Try to find the device description URL
            # This is a simplified implementation
            description_urls = [
                f"http://{ip_address}/description.xml",
                f"http://{ip_address}/device.xml",
                f"http://{ip_address}/upnp/desc.xml",
            ]

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=5)
            ) as session:
                for url in description_urls:
                    try:
                        async with session.get(url) as response:
                            if response.status == 200:
                                xml_data = await response.text()
                                return {"description_url": url, "xml": xml_data[:1000]}
                    except Exception:
                        continue

        except Exception as e:
            logger.debug(f"Failed to get UPnP description for {ip_address}: {e}")

        return None
