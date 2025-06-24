"""
DHCP-based device discovery.

This module implements network scanning to discover devices by examining
DHCP leases and scanning common smart home device ports.
"""

import asyncio
import logging
import socket
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DHCPDiscovery:
    """DHCP and network-based device discovery."""

    def __init__(self, scan_timeout: int = 30):
        self.scan_timeout = scan_timeout

        # Common smart home device ports
        self.smart_device_ports = {
            80: "http",
            443: "https",
            1400: "sonos",
            8060: "roku",
            8080: "http_alt",
            1900: "upnp",
            5353: "mdns",
            8443: "https_alt",
            9443: "hue_secure",
        }

    async def discover(self) -> List[Dict[str, Any]]:
        """Discover devices via network scanning."""

        logger.info("Starting DHCP/network discovery")

        devices = []

        try:
            # Get network range
            network_range = await self._get_network_range()
            if not network_range:
                logger.warning("Could not determine network range")
                return []

            # Scan for active hosts
            active_hosts = await self._scan_network(network_range)

            # Port scan active hosts for smart device signatures
            for host in active_hosts:
                device_info = await self._identify_device(host)
                if device_info:
                    devices.append(device_info)

            logger.info(f"DHCP/network discovery found {len(devices)} devices")
            return devices

        except Exception as e:
            logger.error(f"DHCP discovery failed: {e}")
            return []

    async def _get_network_range(self) -> Optional[str]:
        """Get the local network range."""

        try:
            # Get default gateway
            result = subprocess.run(
                ["ip", "route", "show", "default"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if "default via" in line:
                        parts = line.split()
                        gateway = parts[2]
                        # Assume /24 network
                        network_base = ".".join(gateway.split(".")[:-1])
                        return f"{network_base}.0/24"

        except Exception as e:
            logger.debug(f"Failed to get network range: {e}")

        # Fallback to common ranges
        return "192.168.1.0/24"

    async def _scan_network(self, network_range: str) -> List[str]:
        """Scan network for active hosts."""

        logger.info(f"Scanning network range: {network_range}")

        try:
            # Use nmap if available, otherwise ping sweep
            result = subprocess.run(
                ["nmap", "-sn", network_range],
                capture_output=True,
                text=True,
                timeout=self.scan_timeout,
            )

            if result.returncode == 0:
                return self._parse_nmap_output(result.stdout)

        except FileNotFoundError:
            logger.debug("nmap not available, using ping sweep")
            return await self._ping_sweep(network_range)
        except Exception as e:
            logger.debug(f"nmap scan failed: {e}")
            return await self._ping_sweep(network_range)

    def _parse_nmap_output(self, output: str) -> List[str]:
        """Parse nmap output to extract IP addresses."""

        hosts = []
        lines = output.split("\n")

        for line in lines:
            if "Nmap scan report for" in line:
                # Extract IP address
                parts = line.split()
                if len(parts) >= 5:
                    ip = parts[4]
                    if self._is_valid_ip(ip):
                        hosts.append(ip)

        return hosts

    async def _ping_sweep(self, network_range: str) -> List[str]:
        """Perform ping sweep if nmap is not available."""

        # Extract base network (simplified for /24)
        base = network_range.split("/")[0].rsplit(".", 1)[0]
        hosts = []

        # Test limited range for performance
        tasks = []
        for i in range(1, 255, 10):  # Sample every 10th address
            ip = f"{base}.{i}"
            tasks.append(self._ping_host(ip))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if result is True:
                ip = f"{base}.{1 + i * 10}"
                hosts.append(ip)

        return hosts

    async def _ping_host(self, ip: str) -> bool:
        """Ping a single host."""

        try:
            process = await asyncio.create_subprocess_exec(
                "ping",
                "-c",
                "1",
                "-W",
                "1",
                ip,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )

            await asyncio.wait_for(process.wait(), timeout=2)
            return process.returncode == 0

        except Exception:
            return False

    def _is_valid_ip(self, ip: str) -> bool:
        """Check if string is a valid IP address."""

        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

    async def _identify_device(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Identify device type by scanning ports and services."""

        device_info = {
            "device_id": f"dhcp_{ip_address.replace('.', '_')}",
            "name": f"Device at {ip_address}",
            "ip_address": ip_address,
            "discovery_method": "dhcp",
            "discovered_at": datetime.utcnow().isoformat(),
            "open_ports": [],
            "properties": {},
        }

        # Scan smart device ports
        open_ports = await self._scan_ports(
            ip_address, list(self.smart_device_ports.keys())
        )
        device_info["open_ports"] = open_ports

        # Try to identify device based on open ports and HTTP responses
        device_type, manufacturer, model = await self._classify_device_by_ports(
            ip_address, open_ports
        )

        device_info["device_type"] = device_type
        device_info["manufacturer"] = manufacturer
        device_info["model"] = model

        # Only return if we found something interesting
        if open_ports or device_type != "unknown":
            return device_info

        return None

    async def _scan_ports(self, ip_address: str, ports: List[int]) -> List[int]:
        """Scan specific ports on a host."""

        open_ports = []

        for port in ports:
            if await self._check_port(ip_address, port):
                open_ports.append(port)

        return open_ports

    async def _check_port(self, ip_address: str, port: int) -> bool:
        """Check if a port is open."""

        try:
            future = asyncio.open_connection(ip_address, port)
            reader, writer = await asyncio.wait_for(future, timeout=2)
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False

    async def _classify_device_by_ports(
        self, ip_address: str, open_ports: List[int]
    ) -> tuple:
        """Classify device based on open ports and HTTP responses."""

        device_type = "unknown"
        manufacturer = None
        model = None

        # Port-based classification
        if 1400 in open_ports:
            device_type = "speaker"
            manufacturer = "Sonos"
        elif 8060 in open_ports:
            device_type = "media_player"
            manufacturer = "Roku"
        elif 80 in open_ports or 443 in open_ports:
            # Check HTTP response for device identification
            http_info = await self._get_http_device_info(ip_address, open_ports)
            if http_info:
                device_type = http_info.get("device_type", device_type)
                manufacturer = http_info.get("manufacturer", manufacturer)
                model = http_info.get("model", model)

        return device_type, manufacturer, model

    async def _get_http_device_info(
        self, ip_address: str, open_ports: List[int]
    ) -> Optional[Dict[str, Any]]:
        """Get device info via HTTP."""

        try:
            import aiohttp

            # Try HTTP and HTTPS
            schemes = []
            if 80 in open_ports:
                schemes.append("http")
            if 443 in open_ports:
                schemes.append("https")

            for scheme in schemes:
                try:
                    async with aiohttp.ClientSession(
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as session:
                        async with session.get(f"{scheme}://{ip_address}/") as response:
                            if response.status == 200:
                                # Check headers for device info
                                server = response.headers.get("Server", "").lower()
                                content = await response.text()

                                return self._parse_http_device_info(server, content)

                except Exception:
                    continue

        except Exception as e:
            logger.debug(f"Failed to get HTTP info for {ip_address}: {e}")

        return None

    def _parse_http_device_info(
        self, server_header: str, content: str
    ) -> Dict[str, Any]:
        """Parse HTTP response to identify device."""

        info = {}

        server_lower = server_header.lower()
        content_lower = content.lower()

        # Check server header
        if "hue" in server_lower or "philips" in server_lower:
            info["manufacturer"] = "Philips"
            info["device_type"] = "hub"
            info["model"] = "Hue Bridge"
        elif "sonos" in server_lower:
            info["manufacturer"] = "Sonos"
            info["device_type"] = "speaker"
        elif "roku" in server_lower:
            info["manufacturer"] = "Roku"
            info["device_type"] = "media_player"
        elif "nest" in server_lower:
            info["manufacturer"] = "Google Nest"
            info["device_type"] = "thermostat"

        # Check content for additional clues
        if "hue" in content_lower and "bridge" in content_lower:
            info["manufacturer"] = "Philips"
            info["device_type"] = "hub"
            info["model"] = "Hue Bridge"

        return info

    async def scan_ports(self, ports: List[int]) -> List[Dict[str, Any]]:
        """Scan specific ports across the network."""

        logger.info(f"Scanning ports: {ports}")

        devices = []
        network_range = await self._get_network_range()

        if not network_range:
            return devices

        # Get active hosts first
        active_hosts = await self._scan_network(network_range)

        # Scan target ports on active hosts
        for host in active_hosts:
            open_ports = await self._scan_ports(host, ports)
            if open_ports:
                device = {
                    "device_id": f"port_scan_{host.replace('.', '_')}",
                    "name": f"Device at {host}",
                    "ip_address": host,
                    "open_ports": open_ports,
                    "discovery_method": "port_scan",
                    "discovered_at": datetime.utcnow().isoformat(),
                }
                devices.append(device)

        return devices
