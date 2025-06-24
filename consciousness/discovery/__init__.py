"""
Automatic device discovery package.

This package implements multi-protocol automatic device discovery to complement
the conversational interview system, providing network-based device detection
across various smart home protocols.
"""

from .auto_discovery import AutoDiscoveryService
from .protocols import (
    BluetoothDiscovery,
    DHCPDiscovery,
    MDNSDiscovery,
    UPnPDiscovery,
    ZigbeeDiscovery,
)

__all__ = [
    "AutoDiscoveryService",
    "DHCPDiscovery",
    "MDNSDiscovery",
    "UPnPDiscovery",
    "BluetoothDiscovery",
    "ZigbeeDiscovery",
]
