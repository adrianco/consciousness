#!/usr/bin/env python3
"""
Demonstration of consciousness UI features with device control
"""

import json
import time

import requests

BASE_URL = "http://localhost:8000"


def get_auth_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"username": "admin", "password": "consciousness123"},
    )
    return response.json()["access_token"]


def test_device_control():
    """Test device control functionality"""
    print("🔌 Testing Device Control...")
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Get devices first
    devices_response = requests.get(f"{BASE_URL}/api/v1/devices", headers=headers)
    devices = devices_response.json()["devices"]

    if devices:
        test_device = devices[0]  # Use first device
        device_id = test_device["id"]
        print(f"Testing control of device: {test_device['name']}")

        # Try turning device on
        control_data = {"action": "turn_on"}
        response = requests.put(
            f"{BASE_URL}/api/v1/devices/{device_id}/control",
            headers=headers,
            json=control_data,
        )

        if response.status_code == 200:
            print(f"✅ Device control successful!")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Device control failed: {response.status_code}")
            return False
    else:
        print("❌ No devices found for testing")
        return False


def test_memory_storage():
    """Test memory storage functionality"""
    print("\n🧠 Testing Memory Storage...")
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    memory_data = {
        "type": "user_action",
        "content": "User tested the consciousness UI system successfully",
        "context": {"timestamp": time.time(), "test": True},
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/memory", headers=headers, json=memory_data
    )

    if response.status_code == 200:
        print(f"✅ Memory stored successfully!")
        print(f"   Memory ID: {response.json()['memory_id']}")
        return True
    else:
        print(f"❌ Memory storage failed: {response.status_code}")
        return False


def simulate_consciousness_interaction():
    """Simulate a full consciousness interaction"""
    print("\n🤖 Simulating Full Consciousness Interaction...")
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Series of queries to test conversation flow
    queries = [
        "Hello! How are you feeling today?",
        "What devices are currently online in my house?",
        "Can you tell me about the security status?",
        "What was the last thing you remember?",
        "Thank you for helping me today!",
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n  Query {i}: {query}")
        response = requests.post(
            f"{BASE_URL}/api/v1/consciousness/query",
            headers=headers,
            json={"query": query},
        )

        if response.status_code == 200:
            data = response.json()
            print(f"  Response: {data['response']}")
        else:
            print(f"  ❌ Query failed: {response.status_code}")

        time.sleep(1)  # Small delay between queries

    return True


def show_system_overview():
    """Show complete system overview"""
    print("\n📊 System Overview")
    print("=" * 30)

    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Consciousness status
    status_response = requests.get(
        f"{BASE_URL}/api/v1/consciousness/status", headers=headers
    )
    status = status_response.json()

    print(f"Consciousness Status: {status['status']}")
    print(f"Awareness Level: {status['awareness_level']}")
    print(
        f"Emotional State: {status['emotional_state']['primary']} (arousal: {status['emotional_state']['arousal']}, valence: {status['emotional_state']['valence']})"
    )
    print(f"Active Devices: {status['active_devices']}")
    print(f"SAFLA Loops: {status['safla_loops']}")

    # Device summary
    devices_response = requests.get(f"{BASE_URL}/api/v1/devices", headers=headers)
    devices = devices_response.json()["devices"]

    online_devices = [d for d in devices if d.get("status") in ["online", "active"]]
    print(f"Online Devices: {len(online_devices)}/{len(devices)}")

    # Memory summary
    memory_response = requests.get(f"{BASE_URL}/api/v1/memory", headers=headers)
    memories = memory_response.json()["memories"]
    print(f"Memory Entries: {len(memories)}")


def main():
    """Run consciousness UI demonstration"""
    print("🏠 House Consciousness UI Demonstration")
    print("=" * 50)

    # Show system overview
    show_system_overview()

    # Test device control
    test_device_control()

    # Test memory storage
    test_memory_storage()

    # Simulate consciousness interaction
    simulate_consciousness_interaction()

    print("\n✨ Consciousness UI demonstration complete!")
    print("\n📝 To access the web interface:")
    print(f"   1. Open your browser to: http://localhost:8000/")
    print(f"   2. Login with: admin / consciousness123")
    print(f"   3. Explore the consciousness features:")
    print(f"      - Overview: System status and health")
    print(f"      - Devices: Control and monitor smart devices")
    print(f"      - Chat: Interact with consciousness")
    print(f"      - Memory: View stored experiences")
    print(f"      - API Testing: Test individual endpoints")


if __name__ == "__main__":
    main()
